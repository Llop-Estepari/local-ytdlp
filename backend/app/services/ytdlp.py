"""yt-dlp integration using argument lists and isolated subprocesses."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.errors import YtDlpError
from ..core.process import clean_output, last_error_line, run_capture, subprocess_env
from .progress import PROGRESS_PREFIX
from .tools import Tool

PROGRESS_TEMPLATE = (
    f"download:{PROGRESS_PREFIX}"
    "%(progress.status)s|"
    "%(progress.downloaded_bytes)s|"
    "%(progress.total_bytes)s|"
    "%(progress.total_bytes_estimate)s|"
    "%(progress.speed)s|"
    "%(progress.eta)s|"
    "%(progress._percent_str)s"
)

ITEM_TEMPLATE = (
    "before_dl:ITEM|%(playlist_index)s|%(playlist_count)s|%(title)s"
)

OUTPUT_TEMPLATE = "%(title).160B [%(id)s].%(ext)s"
PLAYLIST_OUTPUT_TEMPLATE = (
    "%(playlist_index)03d - %(title).160B [%(id)s].%(ext)s"
)
FILE_MARKER = "__FILE__"

_ANALYZE_TIMEOUT = 90.0
_PLAYLIST_SAMPLE_TIMEOUT = 120.0

_ERROR_MESSAGES: tuple[tuple[tuple[str, ...], str, str | None], ...] = (
    (
        ("unsupported url",),
        "La URL no es compatible con yt-dlp.",
        "Comprueba que el enlace apunte a un vídeo o audio.",
    ),
    (
        ("private video", "this video is private"),
        "El contenido es privado.",
        "No se puede descargar sin autorización del propietario.",
    ),
    (
        ("video unavailable", "this video is unavailable", "content is not available"),
        "El contenido no está disponible.",
        "Puede haber sido eliminado o restringido.",
    ),
    (
        ("sign in to confirm", "confirm you're not a bot", "confirm you are not a bot"),
        "La plataforma requiere verificación o inicio de sesión.",
        "Prueba más tarde o utiliza otro enlace público.",
    ),
    (
        ("cookies", "login required", "authentication"),
        "El contenido requiere iniciar sesión.",
        "La aplicación solo admite contenido público.",
    ),
    (
        ("http error 404", "not found"),
        "El contenido no existe (404).",
        "Comprueba que el enlace sea correcto.",
    ),
    (
        ("http error 403", "forbidden"),
        "Acceso denegado (403).",
        "La plataforma ha rechazado la petición.",
    ),
    (
        ("not available in your country", "geo restriction", "geo-restricted"),
        "El contenido no está disponible en tu región.",
        None,
    ),
    (
        ("requested format is not available", "format is not available"),
        "El formato seleccionado no está disponible.",
        "Prueba con otra calidad o formato.",
    ),
    (
        ("ffmpeg not found", "ffmpeg is not installed", "ffprobe not found"),
        "FFmpeg no está instalado.",
        "Instala FFmpeg para combinar pistas y convertir audio.",
    ),
    (
        ("no space left", "disk full"),
        "No hay espacio suficiente en el disco.",
        "Libera espacio o elige otra carpeta de destino.",
    ),
    (
        ("permission denied", "access is denied"),
        "No hay permisos para escribir en la carpeta.",
        "Elige otra carpeta de destino.",
    ),
    (
        ("timed out", "timeout"),
        "La conexión ha caducado.",
        "Comprueba tu conexión a Internet e inténtalo de nuevo.",
    ),
    (
        ("unable to download webpage", "failed to resolve", "name or service not known", "getaddrinfo"),
        "No se pudo conectar con el servidor.",
        "Comprueba la URL y tu conexión a Internet.",
    ),
    (
        ("postprocessing", "post-processing", "conversion failed", "merge failed"),
        "Error al procesar el archivo con FFmpeg.",
        "Comprueba que FFmpeg esté instalado correctamente.",
    ),
)


def humanize_ytdlp_error(output: str, returncode: int = 1) -> tuple[str, str | None]:
    cleaned = clean_output(output, 5000)
    lower = cleaned.lower()

    for needles, message, hint in _ERROR_MESSAGES:
        if any(needle in lower for needle in needles):
            return message, hint

    detail = last_error_line(cleaned)
    if detail:
        detail = detail.removeprefix("ERROR:").strip()
        return "No se pudo completar la operación.", clean_output(detail, 320)
    if returncode != 0:
        return "yt-dlp terminó con un error.", None
    return "No se pudo completar la operación.", None


class YtDlpService:
    def __init__(self, tool: Tool, ffmpeg: Tool) -> None:
        self.tool = tool
        self.ffmpeg = ffmpeg

    async def analyze(self, url: str) -> dict:
        if not self.tool.installed:
            raise YtDlpError(
                "yt-dlp no está instalado.",
                "Ejecuta el instalador de la aplicación para instalar las dependencias.",
            )

        command = [
            *self.tool.command,
            "--ignore-config",
            "--no-warnings",
            "--flat-playlist",
            "--color",
            "never",
            "--socket-timeout",
            "20",
            "--retries",
            "2",
            "-J",
            url,
        ]
        return await self._run_json(command, _ANALYZE_TIMEOUT)

    async def analyze_playlist_sample(self, url: str) -> dict:
        """Fetch full metadata for the first available playlist items.

        The flat playlist listing has no format information, so a small sample
        is extracted to offer only real formats and qualities.
        """
        command = [
            *self.tool.command,
            "--ignore-config",
            "--no-warnings",
            "--playlist-items",
            "1-3",
            "--color",
            "never",
            "--socket-timeout",
            "20",
            "--retries",
            "2",
            "-J",
            url,
        ]
        info = await self._run_json(command, _PLAYLIST_SAMPLE_TIMEOUT)
        entries = [item for item in info.get("entries") or [] if isinstance(item, dict)]
        for entry in entries:
            if entry.get("formats"):
                return entry
        if not entries:
            raise YtDlpError(
                "La lista de reproducción está vacía.",
                "Comprueba que el enlace apunte a una lista con contenido público.",
            )
        raise YtDlpError(
            "No se pudieron detectar los formatos de la lista.",
            "Comprueba que sus elementos sean públicos y estén disponibles.",
        )

    async def _run_json(self, command: list[str], timeout: float) -> dict:
        code, stdout, stderr = await run_capture(
            command,
            timeout=timeout,
            env=subprocess_env(),
        )
        if code != 0:
            message, hint = humanize_ytdlp_error(
                stderr.decode("utf-8", "replace") or stdout.decode("utf-8", "replace"),
                code,
            )
            raise YtDlpError(message, hint)

        try:
            info = json.loads(stdout.decode("utf-8", "replace"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise YtDlpError(
                "yt-dlp devolvió una respuesta inesperada.",
                "No se pudo interpretar la información del contenido.",
            ) from exc

        if not isinstance(info, dict):
            raise YtDlpError("yt-dlp devolvió una respuesta inesperada.")
        return info

    def build_download_command(
        self,
        *,
        url: str,
        format_id: str,
        quality: str,
        destination: Path,
        temp_dir: Path,
        playlist: bool = False,
        playlist_item: int | None = None,
        numbered: bool = False,
    ) -> list[str]:
        command = [
            *self.tool.command,
            "--ignore-config",
            "--color",
            "never",
            "--newline",
            "--progress",
            "--progress-template",
            PROGRESS_TEMPLATE,
            "--print",
            f"after_move:{FILE_MARKER}%(filepath)s",
            "--no-simulate",
            "--socket-timeout",
            "30",
            "--retries",
            "10",
            "--fragment-retries",
            "10",
            "--windows-filenames",
            "--trim-filenames",
            "180",
            "--paths",
            f"home:{destination}",
            "--paths",
            f"temp:{temp_dir}",
            "-o",
            (
                PLAYLIST_OUTPUT_TEMPLATE
                if numbered or (playlist and playlist_item is None)
                else OUTPUT_TEMPLATE
            ),
        ]

        if playlist_item is not None:
            command.extend(
                ["--yes-playlist", "--playlist-items", str(playlist_item)]
            )
        elif playlist:
            command.extend(["--yes-playlist", "--print", ITEM_TEMPLATE])
        else:
            command.append("--no-playlist")

        if self.ffmpeg.installed and self.ffmpeg.path:
            command.extend(["--ffmpeg-location", self.ffmpeg.path])

        command.extend(self._format_arguments(format_id, quality))
        command.append(url)
        return command

    @staticmethod
    def _format_arguments(format_id: str, quality: str) -> list[str]:
        height = None if quality == "best" else int(quality)

        if format_id == "mp4":
            if height is None:
                selector = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b"
            else:
                selector = (
                    f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/"
                    f"bv*[height<={height}]+ba/b[height<={height}]"
                )
            return [
                "-f",
                selector,
                "--merge-output-format",
                "mp4",
                "--remux-video",
                "mp4",
            ]

        if format_id == "webm":
            if height is None:
                selector = "bv*[ext=webm]+ba[ext=webm]/bv*[ext=webm]+ba"
            else:
                selector = (
                    f"bv*[height<={height}][ext=webm]+ba[ext=webm]/"
                    f"bv*[height<={height}][ext=webm]+ba"
                )
            return [
                "-f",
                selector,
                "--merge-output-format",
                "webm",
            ]

        if format_id == "mp3":
            return [
                "-f",
                "ba/b",
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                f"{quality}K",
            ]

        if format_id == "m4a":
            return [
                "-f",
                "ba[ext=m4a]/ba/b",
                "-x",
                "--audio-format",
                "m4a",
                "--audio-quality",
                "0",
            ]

        return ["-f", "bv*+ba/b"]
