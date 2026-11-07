"""Download orchestration with real subprocesses and live progress."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import Settings
from ..core.errors import ToolUnavailableError
from ..core.process import (
    popen_kwargs,
    subprocess_env,
    terminate_process,
)
from ..core.urls import validate_media_url
from ..models.schemas import DownloadRequest, DownloadState
from .formats import validate_selection
from .fs import FileSystemService
from .progress import parse_item_line, parse_progress_line
from .tools import Tool
from .ytdlp import FILE_MARKER, YtDlpService, humanize_ytdlp_error

FINAL_STATUSES = {"completed", "cancelled", "error"}
_PROCESSING_PREFIXES = (
    "[Merger]",
    "[ExtractAudio]",
    "[VideoConvertor]",
    "[FixupM3u8]",
    "[MoveFiles]",
    "[Metadata]",
    "[EmbedThumbnail]",
    "[ThumbnailsConvertor]",
)

_DESTINATION_RE = re.compile(r"^\[download\] Destination: (.+)$")
_MERGE_RE = re.compile(r'^\[Merger\] Merging formats into "(.+)"$')
_EXTRACT_RE = re.compile(r"^\[ExtractAudio\] Destination: (.+)$")
_EXISTING_RE = re.compile(r"^\[download\] (.+) has already been downloaded$")

logger = logging.getLogger("local_ytdlp.downloads")


def _iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


@dataclass
class _Record:
    id: str
    url: str
    format_id: str
    quality: str
    destination: Path
    playlist: bool = False
    playlist_item: int | None = None
    numbered: bool = False
    status: str = "starting"
    percent: float | None = None
    item_percent: float | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    playlist_index: int | None = None
    playlist_count: int | None = None
    current_title: str | None = None
    filepath: Path | None = None
    output_path_hint: Path | None = None
    files: set[Path] = field(default_factory=set)
    error: str | None = None
    error_hint: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_emit: float = 0.0
    cancel_requested: bool = False
    temp_dir: Path | None = None
    process: asyncio.subprocess.Process | None = None
    task: asyncio.Task[None] | None = None
    subscribers: set[asyncio.Queue[dict]] = field(default_factory=set)
    output_tail: deque[str] = field(default_factory=lambda: deque(maxlen=60))

    def to_state(self) -> DownloadState:
        return DownloadState(
            id=self.id,
            url=self.url,
            format=self.format_id,
            quality=self.quality,
            destination=str(self.destination),
            status=self.status,
            percent=round(self.percent, 1) if self.percent is not None else None,
            item_percent=(
                round(self.item_percent, 1) if self.item_percent is not None else None
            ),
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            speed=self.speed,
            eta=self.eta,
            filename=self.filepath.name if self.filepath else None,
            filepath=str(self.filepath) if self.filepath else None,
            playlist=self.playlist,
            playlist_index=self.playlist_index,
            playlist_count=self.playlist_count,
            current_title=self.current_title,
            file_count=len(self.files),
            error=self.error,
            error_hint=self.error_hint,
            created_at=_iso(self.created_at),
            updated_at=_iso(self.updated_at),
        )


class DownloadManager:
    def __init__(
        self,
        settings: Settings,
        ytdlp: YtDlpService,
        ffmpeg: Tool,
        filesystem: FileSystemService,
    ) -> None:
        self.settings = settings
        self.ytdlp = ytdlp
        self.ffmpeg = ffmpeg
        self.filesystem = filesystem
        self._records: dict[str, _Record] = {}

    async def start(self, request: DownloadRequest) -> DownloadState:
        if not self.ytdlp.tool.installed:
            raise ToolUnavailableError(
                "yt-dlp no está instalado.",
                "Ejecuta el instalador de la aplicación para instalar las dependencias.",
            )
        if request.format in {"mp4", "webm", "mp3", "m4a"} and not self.ffmpeg.installed:
            raise ToolUnavailableError(
                "FFmpeg no está instalado.",
                "Es necesario para combinar pistas y convertir audio.",
            )

        validate_selection(request.format, request.quality)
        destination = self.filesystem.resolve_destination(request.destination)
        url = await validate_media_url(request.url)

        self._cleanup_old_records()

        download_id = uuid.uuid4().hex
        temp_dir = self.settings.temp_dir / download_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        record = _Record(
            id=download_id,
            url=url,
            format_id=request.format,
            quality=request.quality,
            destination=destination,
            playlist=request.playlist,
            playlist_count=request.playlist_count,
            playlist_item=request.playlist_item,
            numbered=request.numbered,
            temp_dir=temp_dir,
        )
        self._records[download_id] = record
        record.task = asyncio.create_task(self._run(record), name=f"download-{download_id}")
        logger.info(
            "Descarga %s iniciada: %s (%s/%s, lista=%s, elemento=%s) en %s",
            download_id,
            url,
            request.format,
            request.quality,
            request.playlist,
            request.playlist_item,
            destination,
        )
        return record.to_state()

    def get_state(self, download_id: str) -> DownloadState | None:
        record = self._records.get(download_id)
        return record.to_state() if record else None

    def subscribe(self, download_id: str) -> asyncio.Queue[dict] | None:
        record = self._records.get(download_id)
        if record is None:
            return None
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=1)
        queue.put_nowait(record.to_state().model_dump())
        record.subscribers.add(queue)
        return queue

    def unsubscribe(self, download_id: str, queue: asyncio.Queue[dict]) -> None:
        record = self._records.get(download_id)
        if record is not None:
            record.subscribers.discard(queue)

    async def cancel(self, download_id: str) -> DownloadState | None:
        record = self._records.get(download_id)
        if record is None:
            return None
        if record.status in FINAL_STATUSES:
            return record.to_state()

        record.cancel_requested = True
        logger.info("Cancelando descarga %s", download_id)

        process = record.process
        if process is not None and process.returncode is None:
            await terminate_process(process)

        if record.task is not None and not record.task.done():
            try:
                await asyncio.wait_for(asyncio.shield(record.task), timeout=15)
            except TimeoutError:
                logger.warning("La descarga %s no terminó a tiempo", download_id)

        if record.status not in FINAL_STATUSES:
            record.status = "cancelled"
            record.updated_at = time.time()
            self._publish(record, force=True)
        return record.to_state()

    async def shutdown(self) -> None:
        records = [record for record in self._records.values() if record.process]
        if records:
            await asyncio.gather(
                *(terminate_process(record.process) for record in records if record.process),
                return_exceptions=True,
            )
        tasks = [record.task for record in self._records.values() if record.task and not record.task.done()]
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=10,
                )
            except TimeoutError:
                for task in tasks:
                    task.cancel()
        for record in self._records.values():
            if record.temp_dir and record.temp_dir.exists():
                shutil.rmtree(record.temp_dir, ignore_errors=True)

    async def _run(self, record: _Record) -> None:
        command: list[str] = []
        try:
            if record.cancel_requested:
                record.status = "cancelled"
                record.updated_at = time.time()
                return

            command = self.ytdlp.build_download_command(
                url=record.url,
                format_id=record.format_id,
                quality=record.quality,
                destination=record.destination,
                temp_dir=record.temp_dir or self.settings.temp_dir,
                playlist=record.playlist,
                playlist_item=record.playlist_item,
                numbered=record.numbered,
            )
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(record.destination),
                env=subprocess_env(),
                **popen_kwargs(),
            )
            record.process = process
            record.status = "downloading"
            record.updated_at = time.time()
            self._publish(record, force=True)

            if record.cancel_requested:
                await terminate_process(process)

            assert process.stdout is not None
            while True:
                raw_line = await process.stdout.readline()
                if not raw_line:
                    break
                self._handle_line(record, raw_line.decode("utf-8", "replace").rstrip("\r\n"))

            returncode = await process.wait()
            self._finish(record, returncode)
        except asyncio.CancelledError:
            record.cancel_requested = True
            record.status = "cancelled"
            record.updated_at = time.time()
            self._publish(record, force=True)
            raise
        except Exception as exc:
            logger.exception("Error inesperado en la descarga %s", record.id)
            record.status = "error"
            record.error = "La descarga ha fallado de forma inesperada."
            record.error_hint = str(exc)[:300]
            record.updated_at = time.time()
        finally:
            record.process = None
            if record.temp_dir and record.temp_dir.exists():
                shutil.rmtree(record.temp_dir, ignore_errors=True)
            self._publish(record, force=True)

    def _handle_line(self, record: _Record, line: str) -> None:
        line = line.strip()
        if not line:
            return

        item = parse_item_line(line)
        if item is not None:
            record.playlist_index = item.index
            if item.count is not None:
                record.playlist_count = item.count
            record.current_title = item.title
            record.item_percent = None
            record.downloaded_bytes = None
            record.total_bytes = None
            record.speed = None
            record.eta = None
            record.percent = self._overall_percent(record, None)
            record.status = "downloading"
            record.updated_at = time.time()
            self._publish(record, force=True)
            return

        progress = parse_progress_line(line)
        if progress is not None:
            record.item_percent = progress.percent
            record.downloaded_bytes = progress.downloaded_bytes
            record.total_bytes = progress.total_bytes
            record.speed = progress.speed
            record.eta = progress.eta
            record.percent = self._overall_percent(record, progress.percent)
            if record.status != "processing":
                record.status = "downloading"
            record.updated_at = time.time()
            self._publish(record)
            return

        record.output_tail.append(line)

        if line.startswith(FILE_MARKER):
            path = self._path_from_output(record, line[len(FILE_MARKER) :])
            if path is not None:
                record.files.add(path)
                record.filepath = path
                record.status = "processing"
                if (
                    record.playlist
                    and record.playlist_index is not None
                    and record.playlist_count is not None
                ):
                    record.percent = min(
                        100.0,
                        record.playlist_index / record.playlist_count * 100.0,
                    )
                elif record.percent is None:
                    record.percent = 100.0
                record.updated_at = time.time()
                self._publish(record, force=True)
            return

        match = _EXISTING_RE.match(line)
        if match:
            path = self._path_from_output(record, match.group(1))
            if path is not None:
                record.files.add(path)
                record.filepath = path
                record.output_path_hint = path
            return

        match = _DESTINATION_RE.match(line)
        if match:
            path = self._path_from_output(record, match.group(1))
            if path is not None:
                record.output_path_hint = path
            return

        match = _MERGE_RE.match(line)
        if match:
            path = self._path_from_output(record, match.group(1))
            if path is not None:
                record.output_path_hint = path
            self._mark_processing(record)
            return

        match = _EXTRACT_RE.match(line)
        if match:
            path = self._path_from_output(record, match.group(1))
            if path is not None:
                record.output_path_hint = path
            self._mark_processing(record)
            return

        if line.startswith(_PROCESSING_PREFIXES):
            self._mark_processing(record)

    @staticmethod
    def _overall_percent(record: _Record, item_percent: float | None) -> float | None:
        if (
            record.playlist
            and record.playlist_index is not None
            and record.playlist_count is not None
            and record.playlist_count > 0
        ):
            base = (record.playlist_index - 1) / record.playlist_count * 100.0
            if item_percent is None:
                return max(0.0, min(100.0, base))
            return max(0.0, min(100.0, base + item_percent / record.playlist_count))
        return item_percent

    def _mark_processing(self, record: _Record) -> None:
        if record.status != "processing":
            record.status = "processing"
            record.updated_at = time.time()
            self._publish(record, force=True)

    def _path_from_output(self, record: _Record, raw_path: str) -> Path | None:
        value = raw_path.strip().strip('"').strip("'")
        if not value:
            return None
        try:
            path = Path(value)
            if not path.is_absolute():
                path = record.destination / path
            path = path.resolve()
        except (OSError, RuntimeError):
            return None
        if path != record.destination and record.destination not in path.parents:
            return None
        return path

    def _finish(self, record: _Record, returncode: int) -> None:
        record.updated_at = time.time()

        if record.cancel_requested:
            record.status = "cancelled"
            record.error = None
            record.error_hint = None
            logger.info("Descarga %s cancelada", record.id)
            return

        if returncode == 0:
            path = record.filepath or record.output_path_hint or self._find_new_file(record)
            if path is not None and path.is_file():
                record.files.add(path)
                record.filepath = path
                record.percent = 100.0
                record.status = "completed"
                logger.info("Descarga %s completada: %s", record.id, path)
                return
            if record.playlist:
                existing = next(
                    (item for item in record.files if item.is_file()), None
                )
                if existing is not None:
                    record.filepath = existing
                    record.percent = 100.0
                    record.status = "completed"
                    logger.info(
                        "Descarga %s completada (%s archivos): %s",
                        record.id,
                        len(record.files),
                        existing,
                    )
                    return
            record.status = "error"
            record.error = "No se pudo localizar el archivo descargado."
            record.error_hint = (
                "yt-dlp terminó correctamente pero el archivo no aparece en la "
                "carpeta de destino."
            )
            return

        message, hint = humanize_ytdlp_error("\n".join(record.output_tail), returncode)
        if record.playlist and record.files:
            partial = (
                f"Se descargaron {len(record.files)} archivo(s) antes del error."
            )
            hint = f"{hint} {partial}" if hint else partial
        record.status = "error"
        record.error = message
        record.error_hint = hint
        logger.warning(
            "Descarga %s falló (código %s): %s", record.id, returncode, message
        )

    def _find_new_file(self, record: _Record) -> Path | None:
        threshold = record.created_at - 5
        candidates: list[tuple[float, Path]] = []
        try:
            for item in record.destination.iterdir():
                if not item.is_file():
                    continue
                if item.name.endswith((".part", ".ytdl", ".temp")):
                    continue
                try:
                    stat = item.stat()
                except OSError:
                    continue
                if stat.st_mtime >= threshold:
                    candidates.append((stat.st_mtime, item))
        except OSError:
            return None
        if not candidates:
            return None
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        logger.warning(
            "Descarga %s: usando archivo detectado por fecha: %s",
            record.id,
            candidates[0][1],
        )
        return candidates[0][1]

    def _publish(self, record: _Record, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - record.last_emit < 0.1:
            return
        record.last_emit = now
        snapshot = record.to_state().model_dump()
        for queue in list(record.subscribers):
            try:
                queue.put_nowait(snapshot)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(snapshot)
                except asyncio.QueueFull:
                    pass

    def _cleanup_old_records(self) -> None:
        if len(self._records) < 100:
            return
        finished = [
            record
            for record in self._records.values()
            if record.status in FINAL_STATUSES
        ]
        finished.sort(key=lambda record: record.created_at)
        for record in finished[: max(0, len(self._records) - 80)]:
            self._records.pop(record.id, None)
