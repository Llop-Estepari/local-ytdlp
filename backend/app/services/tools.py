"""Detection of yt-dlp and FFmpeg installations."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from ..core.process import clean_output, run_capture, subprocess_env

_VERSION_TTL = 300.0


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    command: tuple[str, ...]
    path: str | None
    installed: bool


def _env_path(*names: str) -> Path | None:
    for name in names:
        raw = os.environ.get(name, "").strip()
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        if candidate.is_dir():
            for filename in ("yt-dlp.exe", "yt-dlp", "ffmpeg.exe", "ffmpeg"):
                nested = candidate / filename
                if nested.is_file():
                    return nested.resolve()
    return None


def locate_ytdlp(project_root: Path) -> Tool:
    env_tool = _env_path("LOCAL_YTDLP_YTDLP_PATH", "YTDLP_PATH")
    if env_tool:
        return Tool("yt-dlp", (str(env_tool),), str(env_tool), True)

    bundled = project_root / "tools" / ("yt-dlp.exe" if os.name == "nt" else "yt-dlp")
    if bundled.is_file():
        return Tool("yt-dlp", (str(bundled),), str(bundled), True)

    if importlib.util.find_spec("yt_dlp") is not None:
        return Tool(
            "yt-dlp",
            (sys.executable, "-m", "yt_dlp"),
            sys.executable,
            True,
        )

    system = shutil.which("yt-dlp")
    if system:
        resolved = str(Path(system).resolve())
        return Tool("yt-dlp", (resolved,), resolved, True)

    return Tool("yt-dlp", (), None, False)


def locate_ffmpeg(project_root: Path) -> Tool:
    env_tool = _env_path("LOCAL_YTDLP_FFMPEG_PATH", "FFMPEG_PATH")
    if env_tool:
        return Tool("ffmpeg", (str(env_tool),), str(env_tool), True)

    candidates = [
        project_root / "tools" / "ffmpeg" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
        project_root / "tools" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            resolved = str(candidate.resolve())
            return Tool("ffmpeg", (resolved,), resolved, True)

    system = shutil.which("ffmpeg")
    if system:
        resolved = str(Path(system).resolve())
        return Tool("ffmpeg", (resolved,), resolved, True)

    return Tool("ffmpeg", (), None, False)


def _parse_ffmpeg_version(output: str) -> str | None:
    match = re.search(r"ffmpeg version\s+(\S+)", output, re.IGNORECASE)
    if not match:
        return None
    version = match.group(1)
    if re.match(r"^n\d", version):
        version = version[1:]
    return clean_output(version, 40) or None


class ToolsService:
    def __init__(self, project_root: Path) -> None:
        self.ytdlp = locate_ytdlp(project_root)
        self.ffmpeg = locate_ffmpeg(project_root)
        self._ytdlp_version: str | None = None
        self._ffmpeg_version: str | None = None
        self._ytdlp_checked_at = 0.0
        self._ffmpeg_checked_at = 0.0

    async def ytdlp_version(self, refresh: bool = False) -> str | None:
        now = time.monotonic()
        if not refresh and now - self._ytdlp_checked_at < _VERSION_TTL:
            return self._ytdlp_version
        if not self.ytdlp.installed:
            return None
        try:
            code, stdout, _ = await run_capture(
                [*self.ytdlp.command, "--version"],
                timeout=10,
                env=subprocess_env(),
            )
            if code == 0:
                self._ytdlp_version = clean_output(
                    stdout.decode("utf-8", "replace"), 80
                ) or None
        except Exception:
            self._ytdlp_version = None
        self._ytdlp_checked_at = now
        return self._ytdlp_version

    async def ffmpeg_version(self, refresh: bool = False) -> str | None:
        now = time.monotonic()
        if not refresh and now - self._ffmpeg_checked_at < _VERSION_TTL:
            return self._ffmpeg_version
        if not self.ffmpeg.installed:
            return None
        try:
            code, stdout, stderr = await run_capture(
                [*self.ffmpeg.command, "-version"],
                timeout=10,
                env=subprocess_env(),
            )
            if code == 0:
                text = stdout.decode("utf-8", "replace") or stderr.decode(
                    "utf-8", "replace"
                )
                self._ffmpeg_version = _parse_ffmpeg_version(text)
        except Exception:
            self._ffmpeg_version = None
        self._ffmpeg_checked_at = now
        return self._ffmpeg_version

    async def dependencies(self, refresh: bool = False) -> dict:
        ytdlp_version, ffmpeg_version = await self._versions(refresh=refresh)
        return {
            "ok": self.ytdlp.installed and self.ffmpeg.installed,
            "ytdlp": {
                "installed": self.ytdlp.installed,
                "version": ytdlp_version,
                "path": self.ytdlp.path,
            },
            "ffmpeg": {
                "installed": self.ffmpeg.installed,
                "version": ffmpeg_version,
                "path": self.ffmpeg.path,
            },
        }

    async def _versions(self, refresh: bool = False) -> tuple[str | None, str | None]:
        import asyncio

        return await asyncio.gather(
            self.ytdlp_version(refresh=refresh),
            self.ffmpeg_version(refresh=refresh),
        )
