"""Detection of yt-dlp and FFmpeg installations."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from ..core.errors import CommandTimeoutError
from ..core.process import clean_output, last_error_line, run_capture, subprocess_env

_VERSION_TTL = 300.0
_UPDATE_TIMEOUT = 240.0
_FFMPEG_UPDATE_TIMEOUT = 300.0


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    command: tuple[str, ...]
    path: str | None
    installed: bool


@dataclass(frozen=True, slots=True)
class ToolUpdateResult:
    updated: bool
    error: str | None = None
    hint: str | None = None


def _find_command(name: str, extra: tuple[str, ...] = ()) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for candidate in extra:
        path = Path(candidate)
        if path.is_file():
            return str(path)
    return None


def _decode_update_output(stdout: bytes, stderr: bytes) -> str:
    return (
        stderr.decode("utf-8", "replace").strip()
        or stdout.decode("utf-8", "replace").strip()
    )


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
        self.project_root = project_root
        self.ytdlp = locate_ytdlp(project_root)
        self.ffmpeg = locate_ffmpeg(project_root)
        self._ytdlp_version: str | None = None
        self._ffmpeg_version: str | None = None
        self._ytdlp_checked_at = 0.0
        self._ffmpeg_checked_at = 0.0
        self._update_lock = asyncio.Lock()

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

    async def update(self, name: str) -> ToolUpdateResult:
        """Update yt-dlp or FFmpeg using the mechanism available on this system."""

        async with self._update_lock:
            if name == "ytdlp":
                return await self._update_ytdlp()
            if name == "ffmpeg":
                return await self._update_ffmpeg()
            return ToolUpdateResult(False, error="Herramienta desconocida.")

    def _ytdlp_update_command(self) -> list[str]:
        command = tuple(self.ytdlp.command)
        # The application installs yt-dlp inside its virtual environment, so a
        # pip upgrade is the reliable path. Standalone binaries support -U.
        if len(command) >= 3 and command[1:3] == ("-m", "yt_dlp"):
            return [
                command[0],
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--disable-pip-version-check",
                "yt-dlp",
            ]
        return [*command, "-U"]

    async def _update_ytdlp(self) -> ToolUpdateResult:
        if not self.ytdlp.installed:
            return ToolUpdateResult(
                False,
                error="yt-dlp no está instalado.",
                hint="Ejecuta el instalador de la aplicación.",
            )

        command = self._ytdlp_update_command()
        try:
            code, stdout, stderr = await run_capture(
                command,
                timeout=_UPDATE_TIMEOUT,
                env=subprocess_env(),
            )
        except CommandTimeoutError:
            return ToolUpdateResult(
                False,
                error="La actualización de yt-dlp tardó demasiado.",
                hint="Comprueba tu conexión a Internet e inténtalo de nuevo.",
            )
        except OSError as exc:
            return ToolUpdateResult(
                False,
                error=clean_output(str(exc), 300),
                hint="Vuelve a ejecutar el instalador de la aplicación.",
            )

        output = _decode_update_output(stdout, stderr)
        if code != 0:
            return ToolUpdateResult(
                False,
                error=clean_output(last_error_line(output) or output, 300) or None,
                hint=self._update_failure_hint(
                    output,
                    "Vuelve a ejecutar el instalador o actualiza yt-dlp manualmente.",
                ),
            )

        self._ytdlp_checked_at = 0.0
        return ToolUpdateResult(True)

    def _ffmpeg_update_command(self) -> tuple[list[str] | None, str]:
        """Return the upgrade command and the manual fallback hint."""

        if self.ffmpeg.path:
            try:
                Path(self.ffmpeg.path).resolve().relative_to(
                    (self.project_root / "tools").resolve()
                )
            except (OSError, ValueError):
                pass
            else:
                return (
                    None,
                    "Esta instalación usa una copia propia de FFmpeg. Vuelve a ejecutar el instalador para actualizarla.",
                )

        if sys.platform == "win32":
            winget = _find_command("winget")
            if winget:
                return (
                    [
                        winget,
                        "upgrade",
                        "--id",
                        "Gyan.FFmpeg",
                        "-e",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                        "--silent",
                    ],
                    "Ejecuta «winget upgrade --id Gyan.FFmpeg -e» desde una terminal.",
                )
            return (
                None,
                "Descarga la nueva versión desde https://www.gyan.dev/ffmpeg/builds/.",
            )

        if sys.platform == "darwin":
            brew = _find_command(
                "brew", ("/opt/homebrew/bin/brew", "/usr/local/bin/brew")
            )
            if brew:
                return (
                    [brew, "upgrade", "ffmpeg"],
                    "Ejecuta «brew upgrade ffmpeg» desde una terminal.",
                )
            return (
                None,
                "Instala Homebrew y ejecuta «brew upgrade ffmpeg» desde una terminal.",
            )

        managers: tuple[tuple[str, list[str], str], ...] = (
            (
                "apt-get",
                ["apt-get", "install", "--only-upgrade", "-y", "ffmpeg"],
                "sudo apt-get install --only-upgrade -y ffmpeg",
            ),
            ("dnf", ["dnf", "upgrade", "-y", "ffmpeg"], "sudo dnf upgrade -y ffmpeg"),
            (
                "pacman",
                ["pacman", "-S", "--noconfirm", "ffmpeg"],
                "sudo pacman -S --noconfirm ffmpeg",
            ),
            (
                "zypper",
                ["zypper", "--non-interactive", "update", "ffmpeg"],
                "sudo zypper update ffmpeg",
            ),
        )
        for manager, command, manual in managers:
            if not _find_command(manager):
                continue
            if getattr(os, "geteuid", lambda: -1)() == 0:
                return command, f"Ejecuta «{manual}» desde una terminal."
            pkexec = _find_command("pkexec")
            if pkexec:
                return [pkexec, *command], f"Ejecuta «{manual}» desde una terminal."
            sudo = _find_command("sudo")
            if sudo:
                return (
                    [sudo, "-n", *command],
                    f"Ejecuta «{manual}» desde una terminal.",
                )
            return None, f"Ejecuta «{manual}» desde una terminal."

        return (
            None,
            "Actualiza FFmpeg con el gestor de paquetes de tu distribución.",
        )

    async def _update_ffmpeg(self) -> ToolUpdateResult:
        if not self.ffmpeg.installed:
            return ToolUpdateResult(
                False,
                error="FFmpeg no está instalado.",
                hint="Ejecuta el instalador de la aplicación.",
            )

        command, manual_hint = self._ffmpeg_update_command()
        if command is None:
            return ToolUpdateResult(False, hint=manual_hint)

        try:
            code, stdout, stderr = await run_capture(
                command,
                timeout=_FFMPEG_UPDATE_TIMEOUT,
                env=subprocess_env(),
            )
        except CommandTimeoutError:
            return ToolUpdateResult(
                False,
                error="La actualización de FFmpeg tardó demasiado.",
                hint=manual_hint,
            )
        except OSError as exc:
            return ToolUpdateResult(
                False,
                error=clean_output(str(exc), 300),
                hint=manual_hint,
            )

        output = _decode_update_output(stdout, stderr)
        if code != 0:
            return ToolUpdateResult(
                False,
                error=clean_output(last_error_line(output) or output, 300) or None,
                hint=self._update_failure_hint(output, manual_hint),
            )

        self._ffmpeg_checked_at = 0.0
        return ToolUpdateResult(True)

    @staticmethod
    def _update_failure_hint(output: str, fallback: str) -> str:
        lower = output.lower()
        if any(
            marker in lower
            for marker in (
                "permission denied",
                "access is denied",
                "operation not permitted",
                "requires administrator",
                "are you root",
            )
        ):
            return f"La actualización necesita permisos de administrador. {fallback}"
        if any(
            marker in lower
            for marker in (
                "connection",
                "network",
                "timed out",
                "timeout",
                "certificate",
                "could not resolve",
                "name or service not known",
            )
        ):
            return "Comprueba tu conexión a Internet e inténtalo de nuevo."
        return fallback

    async def _versions(self, refresh: bool = False) -> tuple[str | None, str | None]:
        import asyncio

        return await asyncio.gather(
            self.ytdlp_version(refresh=refresh),
            self.ffmpeg_version(refresh=refresh),
        )
