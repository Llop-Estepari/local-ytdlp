from __future__ import annotations

from pathlib import Path

import pytest

from app.services.downloader import DownloadManager, _Record
from app.services.tools import Tool
from app.services.ytdlp import PLAYLIST_OUTPUT_TEMPLATE, YtDlpService


def make_manager() -> DownloadManager:
    return DownloadManager(
        settings=None,  # type: ignore[arg-type]
        ytdlp=None,  # type: ignore[arg-type]
        ffmpeg=None,  # type: ignore[arg-type]
        filesystem=None,  # type: ignore[arg-type]
    )


def make_record(tmp_path: Path, playlist: bool = True) -> _Record:
    return _Record(
        id="test",
        url="https://example.com/lista",
        format_id="mp3",
        quality="128",
        destination=tmp_path,
        playlist=playlist,
        playlist_count=10,
    )


def test_item_line_updates_playlist_position(tmp_path: Path) -> None:
    manager = make_manager()
    record = make_record(tmp_path)

    manager._handle_line(record, "ITEM|3|10|Tercera canción")

    assert record.playlist_index == 3
    assert record.playlist_count == 10
    assert record.current_title == "Tercera canción"
    assert record.percent == pytest.approx(20.0)
    assert record.status == "downloading"


def test_playlist_progress_is_overall(tmp_path: Path) -> None:
    manager = make_manager()
    record = make_record(tmp_path)
    manager._handle_line(record, "ITEM|3|10|Tercera canción")

    manager._handle_line(
        record, "PROGRESS|downloading|50|100|NA|NA|NA| 50.0%"
    )

    assert record.item_percent == pytest.approx(50.0)
    assert record.percent == pytest.approx(25.0)


def test_playlist_progress_without_count_falls_back(tmp_path: Path) -> None:
    manager = make_manager()
    record = make_record(tmp_path)
    record.playlist_count = None
    manager._handle_line(record, "ITEM|3|NA|Tercera canción")

    manager._handle_line(
        record, "PROGRESS|downloading|50|100|NA|NA|NA| 50.0%"
    )

    assert record.percent == pytest.approx(50.0)


def test_single_download_progress_is_not_rewritten(tmp_path: Path) -> None:
    manager = make_manager()
    record = make_record(tmp_path, playlist=False)
    record.playlist_count = None

    manager._handle_line(
        record, "PROGRESS|downloading|50|100|NA|NA|NA| 50.0%"
    )

    assert record.percent == pytest.approx(50.0)
    assert record.item_percent == pytest.approx(50.0)


def test_file_marker_tracks_playlist_files(tmp_path: Path) -> None:
    manager = make_manager()
    record = make_record(tmp_path)
    record.playlist_index = 4
    file = tmp_path / "004 - Canción.mp3"
    file.write_bytes(b"audio")

    manager._handle_line(record, f"__FILE__{file}")

    assert record.files == {file.resolve()}
    assert record.filepath == file.resolve()
    assert record.percent == pytest.approx(40.0)
    assert record.to_state().file_count == 1


def test_playlist_download_command() -> None:
    service = YtDlpService(
        Tool("yt-dlp", ("yt-dlp",), "/usr/bin/yt-dlp", True),
        Tool("ffmpeg", ("ffmpeg",), "/usr/bin/ffmpeg", True),
    )
    command = service.build_download_command(
        url="https://example.com/lista",
        format_id="mp3",
        quality="128",
        destination=Path("/tmp/dest"),
        temp_dir=Path("/tmp/temp"),
        playlist=True,
    )

    assert "--yes-playlist" in command
    assert "--no-playlist" not in command
    assert PLAYLIST_OUTPUT_TEMPLATE in command
    assert any(arg.startswith("before_dl:ITEM|") for arg in command)


def test_single_playlist_item_download_command() -> None:
    service = YtDlpService(
        Tool("yt-dlp", ("yt-dlp",), "/usr/bin/yt-dlp", True),
        Tool("ffmpeg", ("ffmpeg",), "/usr/bin/ffmpeg", True),
    )
    command = service.build_download_command(
        url="https://example.com/lista",
        format_id="mp3",
        quality="320",
        destination=Path("/tmp/dest"),
        temp_dir=Path("/tmp/temp"),
        playlist_item=3,
    )

    assert "--yes-playlist" in command
    assert "--no-playlist" not in command
    index = command.index("--playlist-items")
    assert command[index + 1] == "3"
    assert PLAYLIST_OUTPUT_TEMPLATE not in command
    assert not any(arg.startswith("before_dl:ITEM|") for arg in command)


def test_numbered_playlist_item_command() -> None:
    service = YtDlpService(
        Tool("yt-dlp", ("yt-dlp",), "/usr/bin/yt-dlp", True),
        Tool("ffmpeg", ("ffmpeg",), "/usr/bin/ffmpeg", True),
    )
    command = service.build_download_command(
        url="https://example.com/lista",
        format_id="mp3",
        quality="320",
        destination=Path("/tmp/dest"),
        temp_dir=Path("/tmp/temp"),
        playlist_item=3,
        numbered=True,
    )

    assert PLAYLIST_OUTPUT_TEMPLATE in command
    index = command.index("--playlist-items")
    assert command[index + 1] == "3"


def test_single_download_command_keeps_no_playlist() -> None:
    service = YtDlpService(
        Tool("yt-dlp", ("yt-dlp",), "/usr/bin/yt-dlp", True),
        Tool("ffmpeg", ("ffmpeg",), "/usr/bin/ffmpeg", True),
    )
    command = service.build_download_command(
        url="https://example.com/video",
        format_id="mp4",
        quality="1080",
        destination=Path("/tmp/dest"),
        temp_dir=Path("/tmp/temp"),
    )

    assert "--no-playlist" in command
    assert "--yes-playlist" not in command
    assert PLAYLIST_OUTPUT_TEMPLATE not in command
    assert not any(arg.startswith("before_dl:ITEM|") for arg in command)
