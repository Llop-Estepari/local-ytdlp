"""Format and quality detection from yt-dlp metadata."""

from __future__ import annotations

from typing import Any

from ..core.errors import SelectionError, YtDlpError
from ..models.schemas import (
    FormatOption,
    MediaInfo,
    PlaylistEntry,
    PlaylistInfo,
    QualityOption,
)

STANDARD_HEIGHTS = (2160, 1440, 1080, 720, 480, 360)
VIDEO_QUALITIES = {"best", *(str(height) for height in STANDARD_HEIGHTS)}
AUDIO_BITRATES = {"320", "256", "192", "128"}
FORMATS = {"mp4", "webm", "mp3", "m4a", "best"}
PLAYLIST_PREVIEW_LIMIT = 1000

_HEIGHT_LABELS = {
    2160: "2160p · 4K",
    1440: "1440p · 2K",
    1080: "1080p · Full HD",
    720: "720p · HD",
    480: "480p",
    360: "360p",
}

_EXTRACTOR_LABELS = {
    "youtube": "YouTube",
    "youtube:tab": "YouTube",
    "youtubetab": "YouTube",
    "youtube:playlist": "YouTube",
    "youtubeplaylist": "YouTube",
    "vimeo": "Vimeo",
    "dailymotion": "Dailymotion",
    "soundcloud": "SoundCloud",
    "twitch": "Twitch",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "x": "X",
    "twitter": "X",
    "facebook": "Facebook",
    "reddit": "Reddit",
    "bilibili": "Bilibili",
    "generic": "Enlace directo",
}


def _bucket_height(height: Any) -> int | None:
    if not isinstance(height, (int, float)) or height <= 0:
        return None
    for standard in STANDARD_HEIGHTS:
        tolerance = max(24, standard * 0.05)
        if abs(float(height) - standard) <= tolerance:
            return standard
    return None


def _video_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in info.get("formats") or []:
        if not isinstance(item, dict):
            continue
        if item.get("vcodec") in (None, "none"):
            continue
        if item.get("ext") in (None, "mhtml"):
            continue
        height = item.get("height")
        if not isinstance(height, (int, float)) or height <= 0:
            continue
        result.append(item)
    return result


def _heights_for(formats: list[dict[str, Any]], extension: str) -> set[int]:
    heights: set[int] = set()
    for item in formats:
        if item.get("ext") != extension:
            continue
        bucket = _bucket_height(item.get("height"))
        if bucket is not None:
            heights.add(bucket)
    return heights


def _quality_options(heights: set[int]) -> list[QualityOption]:
    options = [QualityOption(id="best", label="Mejor disponible")]
    for height in STANDARD_HEIGHTS:
        if height in heights:
            options.append(
                QualityOption(id=str(height), label=_HEIGHT_LABELS[height])
            )
    return options


def _audio_bitrate_options() -> list[QualityOption]:
    return [
        QualityOption(id=str(bitrate), label=f"{bitrate} kbps")
        for bitrate in (320, 256, 192, 128)
    ]


def _pretty_extractor(info: dict[str, Any]) -> str | None:
    raw = info.get("extractor_key") or info.get("extractor")
    if not isinstance(raw, str) or not raw:
        return None
    key = raw.strip().lower()
    return _EXTRACTOR_LABELS.get(key, raw.strip())


def _thumbnail(info: dict[str, Any]) -> str | None:
    direct = info.get("thumbnail")
    if isinstance(direct, str) and direct.startswith(("http://", "https://")):
        return direct
    thumbnails = info.get("thumbnails")
    if isinstance(thumbnails, list):
        for item in reversed(thumbnails):
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                return url
    return None


def is_playlist_info(info: dict[str, Any]) -> bool:
    if not isinstance(info, dict):
        return False
    if info.get("_type") in {"playlist", "multi_video"}:
        return True
    return isinstance(info.get("entries"), list)


def build_formats(info: dict[str, Any]) -> list[FormatOption]:
    if not isinstance(info, dict):
        raise YtDlpError("yt-dlp devolvió una respuesta inesperada.")

    all_formats = [item for item in info.get("formats") or [] if isinstance(item, dict)]
    video_formats = _video_formats(info)
    has_audio = any(
        item.get("acodec") not in (None, "none") for item in all_formats
    )

    if not video_formats and not has_audio:
        raise YtDlpError(
            "No se encontraron formatos descargables.",
            "Comprueba que el enlace sea de un vídeo o audio compatible con yt-dlp.",
        )

    formats: list[FormatOption] = []

    mp4_formats = [item for item in video_formats if item.get("ext") == "mp4"]
    if mp4_formats:
        formats.append(
            FormatOption(
                id="mp4",
                label="MP4 · Vídeo",
                kind="video",
                qualities=_quality_options(_heights_for(video_formats, "mp4")),
            )
        )

    webm_formats = [item for item in video_formats if item.get("ext") == "webm"]
    if webm_formats:
        formats.append(
            FormatOption(
                id="webm",
                label="WebM · Vídeo",
                kind="video",
                qualities=_quality_options(_heights_for(video_formats, "webm")),
            )
        )

    if has_audio or video_formats:
        formats.append(
            FormatOption(
                id="mp3",
                label="MP3 · Audio",
                kind="audio",
                qualities=_audio_bitrate_options(),
            )
        )
        formats.append(
            FormatOption(
                id="m4a",
                label="M4A · Audio",
                kind="audio",
                qualities=[QualityOption(id="best", label="Mejor disponible")],
            )
        )
        formats.append(
            FormatOption(
                id="best",
                label="Mejor formato",
                kind="video" if video_formats else "audio",
                qualities=[QualityOption(id="best", label="Mejor disponible")],
            )
        )

    if not formats:
        raise YtDlpError("No se encontraron formatos descargables.")
    return formats


def _duration(value: Any) -> float | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return float(value)


def build_media_info(info: dict[str, Any], url: str) -> MediaInfo:
    if not isinstance(info, dict):
        raise YtDlpError("yt-dlp devolvió una respuesta inesperada.")

    formats = build_formats(info)

    title = info.get("title")
    if not isinstance(title, str) or not title.strip():
        title = "Contenido sin título"

    return MediaInfo(
        url=url,
        title=title.strip(),
        duration=_duration(info.get("duration")),
        thumbnail=_thumbnail(info),
        extractor=_pretty_extractor(info),
        formats=formats,
    )


def build_playlist_info(
    info: dict[str, Any], sample: dict[str, Any], url: str
) -> PlaylistInfo:
    if not isinstance(info, dict):
        raise YtDlpError("yt-dlp devolvió una respuesta inesperada.")

    raw_entries = info.get("entries") or []
    if not isinstance(raw_entries, list) or not any(
        isinstance(item, dict) for item in raw_entries
    ):
        raise YtDlpError(
            "La lista de reproducción está vacía.",
            "Comprueba que el enlace apunte a una lista con contenido público.",
        )
    entries: list[PlaylistEntry] = []
    for position, entry in enumerate(raw_entries, start=1):
        if not isinstance(entry, dict):
            continue
        raw_index = entry.get("playlist_index")
        index = (
            raw_index
            if isinstance(raw_index, int) and raw_index > 0
            else position
        )
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            title = f"Elemento {index}"
        entries.append(
            PlaylistEntry(
                index=index,
                title=title.strip(),
                duration=_duration(entry.get("duration")),
                thumbnail=_thumbnail(entry),
            )
        )

    count = info.get("playlist_count")
    if not isinstance(count, int) or count <= 0:
        count = len(entries)
    if count <= 0:
        raise YtDlpError(
            "La lista de reproducción está vacía.",
            "Comprueba que el enlace apunte a una lista con contenido público.",
        )

    if not isinstance(sample, dict):
        raise YtDlpError(
            "No se pudieron detectar los formatos de la lista.",
            "Comprueba que sus elementos sean públicos y estén disponibles.",
        )

    title = info.get("title")
    if not isinstance(title, str) or not title.strip():
        title = "Lista sin título"

    thumbnail = _thumbnail(info) or next(
        (entry.thumbnail for entry in entries if entry.thumbnail), None
    )

    return PlaylistInfo(
        url=url,
        title=title.strip(),
        entry_count=count,
        thumbnail=thumbnail,
        extractor=_pretty_extractor(info),
        formats=build_formats(sample),
        entries=entries[:PLAYLIST_PREVIEW_LIMIT],
    )


def validate_selection(format_id: str, quality: str) -> None:
    if format_id not in FORMATS:
        raise SelectionError("Formato de descarga no válido.")
    if format_id in {"mp4", "webm"}:
        if quality not in VIDEO_QUALITIES:
            raise SelectionError("Calidad de vídeo no válida.")
    elif format_id == "mp3":
        if quality not in AUDIO_BITRATES:
            raise SelectionError("Calidad de audio no válida.")
    elif format_id in {"m4a", "best"}:
        if quality != "best":
            raise SelectionError("Calidad no válida para este formato.")
