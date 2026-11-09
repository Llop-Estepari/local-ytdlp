from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.services import tools as tools_module
from app.services.tools import Tool, ToolsService


def _service(
    tmp_path: Path,
    *,
    ytdlp: Tool | None = None,
    ffmpeg: Tool | None = None,
) -> ToolsService:
    service = ToolsService(tmp_path)
    if ytdlp is not None:
        service.ytdlp = ytdlp
    if ffmpeg is not None:
        service.ffmpeg = ffmpeg
    return service


def test_ytdlp_module_update_uses_pip(tmp_path: Path) -> None:
    service = _service(
        tmp_path,
        ytdlp=Tool(
            "yt-dlp",
            (sys.executable, "-m", "yt_dlp"),
            sys.executable,
            True,
        ),
    )

    assert service._ytdlp_update_command() == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--disable-pip-version-check",
        "yt-dlp",
    ]


def test_standalone_ytdlp_update_uses_self_update(tmp_path: Path) -> None:
    service = _service(
        tmp_path,
        ytdlp=Tool("yt-dlp", ("/opt/yt-dlp",), "/opt/yt-dlp", True),
    )

    assert service._ytdlp_update_command() == ["/opt/yt-dlp", "-U"]


def test_ffmpeg_update_uses_winget_on_windows(
    tmp_path: Path, monkeypatch
) -> None:
    service = _service(
        tmp_path,
        ffmpeg=Tool("ffmpeg", ("C:\\ffmpeg.exe",), "C:\\ffmpeg.exe", True),
    )
    monkeypatch.setattr(tools_module.sys, "platform", "win32")
    monkeypatch.setattr(
        tools_module,
        "_find_command",
        lambda name, extra=(): "C:\\winget.exe" if name == "winget" else None,
    )

    command, hint = service._ffmpeg_update_command()

    assert command is not None
    assert command[:4] == ["C:\\winget.exe", "upgrade", "--id", "Gyan.FFmpeg"]
    assert "winget upgrade" in hint


def test_ffmpeg_update_uses_pkexec_on_linux(
    tmp_path: Path, monkeypatch
) -> None:
    service = _service(
        tmp_path,
        ffmpeg=Tool("ffmpeg", ("/usr/bin/ffmpeg",), "/usr/bin/ffmpeg", True),
    )
    monkeypatch.setattr(tools_module.sys, "platform", "linux")
    monkeypatch.setattr(tools_module.os, "geteuid", lambda: 1000)

    def fake_find(name: str, extra: tuple[str, ...] = ()) -> str | None:
        return {
            "apt-get": "/usr/bin/apt-get",
            "pkexec": "/usr/bin/pkexec",
            "sudo": "/usr/bin/sudo",
        }.get(name)

    monkeypatch.setattr(tools_module, "_find_command", fake_find)

    command, hint = service._ffmpeg_update_command()

    assert command == [
        "/usr/bin/pkexec",
        "apt-get",
        "install",
        "--only-upgrade",
        "-y",
        "ffmpeg",
    ]
    assert "apt-get" in hint


@pytest.mark.asyncio
async def test_update_reports_permission_hint(
    tmp_path: Path, monkeypatch
) -> None:
    service = _service(
        tmp_path,
        ytdlp=Tool("yt-dlp", ("/opt/yt-dlp",), "/opt/yt-dlp", True),
    )

    async def fake_run(*_args, **_kwargs):
        return 1, b"", b"ERROR: Permission denied"

    monkeypatch.setattr(tools_module, "run_capture", fake_run)

    result = await service.update("ytdlp")

    assert result.updated is False
    assert result.error == "ERROR: Permission denied"
    assert result.hint is not None
    assert "permisos" in result.hint


@pytest.mark.asyncio
async def test_update_returns_success(tmp_path: Path, monkeypatch) -> None:
    service = _service(
        tmp_path,
        ytdlp=Tool("yt-dlp", ("/opt/yt-dlp",), "/opt/yt-dlp", True),
    )

    async def fake_run(*_args, **_kwargs):
        return 0, b"Successfully installed yt-dlp", b""

    monkeypatch.setattr(tools_module, "run_capture", fake_run)

    result = await service.update("ytdlp")

    assert result.updated is True
    assert result.error is None
    assert result.hint is None
