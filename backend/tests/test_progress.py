from __future__ import annotations

import pytest

from app.services.progress import parse_item_line, parse_progress_line


def test_parse_download_progress() -> None:
    update = parse_progress_line(
        "PROGRESS|downloading|1047552|2848208|NA|5968149.339592502|1| 36.8%"
    )
    assert update is not None
    assert update.status == "downloading"
    assert update.downloaded_bytes == 1047552
    assert update.total_bytes == 2848208
    assert update.speed == pytest.approx(5968149.339592502)
    assert update.eta == 1
    assert update.percent == pytest.approx(36.78, abs=0.01)


def test_parse_total_estimate_fallback() -> None:
    update = parse_progress_line(
        "PROGRESS|downloading|500|NA|1000|NA|NA| 50.0%"
    )
    assert update is not None
    assert update.total_bytes == 1000
    assert update.percent == pytest.approx(50.0)


def test_parse_finished_without_bytes() -> None:
    update = parse_progress_line("PROGRESS|finished|NA|NA|NA|NA|NA|100.0%")
    assert update is not None
    assert update.status == "finished"
    assert update.percent == 100.0


def test_parse_clamps_percent() -> None:
    update = parse_progress_line("PROGRESS|downloading|200|100|NA|NA|NA|200.0%")
    assert update is not None
    assert update.percent == 100.0


def test_non_progress_line() -> None:
    assert parse_progress_line("[download] Destination: /tmp/video.mp4") is None


def test_malformed_progress_line() -> None:
    assert parse_progress_line("PROGRESS|downloading|1|2") is None


def test_parse_playlist_item() -> None:
    item = parse_item_line("ITEM|3|12|Canción con | barra")
    assert item is not None
    assert item.index == 3
    assert item.count == 12
    assert item.title == "Canción con | barra"


def test_parse_playlist_item_with_missing_values() -> None:
    item = parse_item_line("ITEM|NA|NA|Título")
    assert item is not None
    assert item.index is None
    assert item.count is None
    assert item.title == "Título"


def test_non_item_line() -> None:
    assert parse_item_line("PROGRESS|downloading|1|2|NA|NA|NA|50%") is None
    assert parse_item_line("ITEM|1|2") is None
