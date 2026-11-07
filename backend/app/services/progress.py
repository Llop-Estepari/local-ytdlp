"""Parsing of yt-dlp progress output."""

from __future__ import annotations

from dataclasses import dataclass

PROGRESS_PREFIX = "PROGRESS|"
ITEM_PREFIX = "ITEM|"


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    status: str
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    percent: float | None


@dataclass(frozen=True, slots=True)
class ItemUpdate:
    index: int | None
    count: int | None
    title: str | None


def _number(raw: str) -> float | None:
    raw = raw.strip()
    if not raw or raw in {"NA", "None", "none", "N/A"}:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value != value:  # NaN
        return None
    return value


def _integer(raw: str) -> int | None:
    value = _number(raw)
    if value is None or value < 0:
        return None
    return int(value)


def parse_progress_line(line: str) -> ProgressUpdate | None:
    line = line.strip()
    if not line.startswith(PROGRESS_PREFIX):
        return None
    parts = line.split("|", 7)
    if len(parts) != 8:
        return None

    status = parts[1].strip() or "downloading"
    downloaded = _integer(parts[2])
    total = _integer(parts[3])
    estimate = _integer(parts[4])
    speed = _number(parts[5])
    eta = _number(parts[6])
    raw_percent = parts[7].strip().removesuffix("%").strip()

    if total is None:
        total = estimate
    if total is not None and total <= 0:
        total = None

    percent: float | None = None
    if downloaded is not None and total:
        percent = (downloaded / total) * 100.0
    else:
        parsed_percent = _number(raw_percent)
        if parsed_percent is not None:
            percent = parsed_percent

    if percent is not None:
        percent = max(0.0, min(100.0, percent))
    elif status == "finished":
        percent = 100.0

    if speed is not None and speed <= 0:
        speed = None
    if eta is not None and eta < 0:
        eta = None

    return ProgressUpdate(
        status=status,
        downloaded_bytes=downloaded,
        total_bytes=total,
        speed=speed,
        eta=int(round(eta)) if eta is not None else None,
        percent=percent,
    )


def parse_item_line(line: str) -> ItemUpdate | None:
    line = line.strip()
    if not line.startswith(ITEM_PREFIX):
        return None
    parts = line.split("|", 3)
    if len(parts) != 4:
        return None

    index = _integer(parts[1])
    count = _integer(parts[2])
    title = parts[3].strip()
    if index is not None and index <= 0:
        index = None
    if count is not None and count <= 0:
        count = None
    if title in {"NA", "None", "none", "N/A"}:
        title = ""
    return ItemUpdate(index=index, count=count, title=title or None)
