"""Subprocess helpers with process-tree termination and output cleanup."""

from __future__ import annotations

import asyncio
import os
import re
import signal
import subprocess
import sys
from typing import Any

from .errors import CommandTimeoutError

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def popen_kwargs() -> dict[str, Any]:
    """Start every child in its own process group/session.

    This lets us terminate yt-dlp together with the ffmpeg children it spawns.
    """

    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def clean_output(text: str, limit: int = 600) -> str:
    text = _ANSI_RE.sub("", text).replace("\r", "")
    text = _CONTROL_RE.sub("", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def last_error_line(output: str) -> str | None:
    lines = [clean_output(line, 500) for line in output.splitlines()]
    for line in reversed(lines):
        if line:
            return line
    return None


async def terminate_process(process: asyncio.subprocess.Process, grace: float = 5.0) -> None:
    """Terminate a process and all of its children."""

    if process.returncode is not None:
        return

    if os.name == "nt":
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            try:
                process.terminate()
            except ProcessLookupError:
                pass
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                process.terminate()
            except ProcessLookupError:
                pass

    try:
        await asyncio.wait_for(process.wait(), timeout=grace)
        return
    except TimeoutError:
        pass

    if os.name == "nt":
        try:
            process.kill()
        except ProcessLookupError:
            pass
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                process.kill()
            except ProcessLookupError:
                pass

    try:
        await asyncio.wait_for(process.wait(), timeout=grace)
    except TimeoutError:
        pass


async def run_capture(
    command: list[str],
    *,
    timeout: float,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, bytes, bytes]:
    """Run a command without a shell and return its exit code and output."""

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
        **popen_kwargs(),
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError as exc:
        await terminate_process(process)
        raise CommandTimeoutError(
            "La operación tardó demasiado.",
            "Comprueba tu conexión a Internet e inténtalo de nuevo.",
        ) from exc
    return process.returncode or 0, stdout, stderr


def subprocess_env(extra_path: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env["NO_COLOR"] = "1"
    if extra_path:
        current = env.get("PATH", "")
        env["PATH"] = extra_path + (os.pathsep + current if current else "")
    return env


def python_executable() -> str:
    return sys.executable
