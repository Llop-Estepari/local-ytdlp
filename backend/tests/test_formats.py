from __future__ import annotations

import pytest

from app.core.errors import SelectionError, YtDlpError
from app.services.formats import (
    build_media_info,
    build_playlist_info,
    is_playlist_info,
    validate_selection,
)


def sample_info() -> dict:
    return {
        "title": "Vídeo de prueba",
        "duration": 125,
        "thumbnail": "https://example.com/thumb.jpg",
        "extractor_key": "Youtube",
        "formats": [
            {"ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "none"},
            {"ext": "mp4", "height": 720, "vcodec": "avc1", "acodec": "none"},
            {"ext": "mp4", "height": 360, "vcodec": "avc1", "acodec": "mp4a"},
            {"ext": "webm", "height": 1080, "vcodec": "vp9", "acodec": "none"},
            {"ext": "webm", "height": 480, "vcodec": "vp9", "acodec": "none"},
            {"ext": "m4a", "height": None, "vcodec": "none", "acodec": "mp4a"},
            {"ext": "mhtml", "height": 90, "vcodec": "none", "acodec": "none"},
        ],
    }


def test_build_media_info_video_and_audio_formats() -> None:
    media = build_media_info(sample_info(), "https://example.com/video")

    assert media.title == "Vídeo de prueba"
    assert media.duration == 125
    assert media.extractor == "YouTube"
    assert [option.id for option in media.formats] == [
        "mp4",
        "webm",
        "mp3",
        "m4a",
        "best",
    ]

    mp4 = next(option for option in media.formats if option.id == "mp4")
    assert [quality.id for quality in mp4.qualities] == ["best", "1080", "720", "360"]

    webm = next(option for option in media.formats if option.id == "webm")
    assert [quality.id for quality in webm.qualities] == ["best", "1080", "480"]

    mp3 = next(option for option in media.formats if option.id == "mp3")
    assert [quality.id for quality in mp3.qualities] == ["320", "256", "192", "128"]

    best = next(option for option in media.formats if option.id == "best")
    assert [quality.id for quality in best.qualities] == ["best"]


def test_only_webm_does_not_offer_mp4() -> None:
    info = {
        "title": "WebM",
        "formats": [
            {"ext": "webm", "height": 720, "vcodec": "vp9", "acodec": "none"},
            {"ext": "webm", "height": None, "vcodec": "none", "acodec": "opus"},
        ],
    }
    media = build_media_info(info, "https://example.com/webm")
    assert [option.id for option in media.formats] == ["webm", "mp3", "m4a", "best"]


def test_audio_only_content() -> None:
    info = {
        "title": "Audio",
        "formats": [
            {"ext": "m4a", "height": None, "vcodec": "none", "acodec": "mp4a"},
        ],
    }
    media = build_media_info(info, "https://example.com/audio")
    assert [option.id for option in media.formats] == ["mp3", "m4a", "best"]
    assert media.formats[-1].kind == "audio"


def test_playlist_is_detected() -> None:
    assert is_playlist_info({"_type": "playlist", "entries": []})
    assert is_playlist_info({"_type": "multi_video", "entries": []})
    assert is_playlist_info({"entries": []})
    assert not is_playlist_info({"_type": "video", "formats": []})
    assert not is_playlist_info({"formats": []})


def playlist_info() -> dict:
    return {
        "_type": "playlist",
        "title": "Lista de prueba",
        "playlist_count": 3,
        "thumbnail": "https://example.com/list.jpg",
        "extractor_key": "Youtube",
        "entries": [
            {
                "title": "Primera canción",
                "duration": 10,
                "thumbnail": "https://example.com/1.jpg",
            },
            {"title": "Segunda canción", "duration": 20},
            {"title": "Tercera canción", "duration": None},
        ],
    }


def test_build_playlist_info() -> None:
    playlist = build_playlist_info(
        playlist_info(), sample_info(), "https://example.com/lista"
    )

    assert playlist.kind == "playlist"
    assert playlist.title == "Lista de prueba"
    assert playlist.entry_count == 3
    assert playlist.extractor == "YouTube"
    assert playlist.thumbnail == "https://example.com/list.jpg"
    assert [entry.index for entry in playlist.entries] == [1, 2, 3]
    assert [entry.title for entry in playlist.entries] == [
        "Primera canción",
        "Segunda canción",
        "Tercera canción",
    ]
    assert playlist.entries[0].duration == 10
    assert playlist.entries[2].duration is None
    assert [option.id for option in playlist.formats] == [
        "mp4",
        "webm",
        "mp3",
        "m4a",
        "best",
    ]


def test_playlist_count_falls_back_to_entries() -> None:
    info = playlist_info()
    info["playlist_count"] = None
    playlist = build_playlist_info(info, sample_info(), "https://example.com/lista")
    assert playlist.entry_count == 3


def test_playlist_entries_are_included() -> None:
    info = playlist_info()
    info["entries"] = [
        {"title": f"Elemento {index}", "duration": 1} for index in range(80)
    ]
    info["playlist_count"] = 80
    playlist = build_playlist_info(info, sample_info(), "https://example.com/lista")
    assert playlist.entry_count == 80
    assert len(playlist.entries) == 80


def test_empty_playlist_is_rejected() -> None:
    with pytest.raises(YtDlpError):
        build_playlist_info(
            {"_type": "playlist", "title": "Vacía", "entries": []},
            sample_info(),
            "https://example.com/vacia",
        )


def test_playlist_without_sample_formats_is_rejected() -> None:
    with pytest.raises(YtDlpError):
        build_playlist_info(
            playlist_info(), {}, "https://example.com/lista"
        )


def test_no_formats_is_rejected() -> None:
    with pytest.raises(YtDlpError):
        build_media_info({"title": "Nada", "formats": []}, "https://example.com/n")


def test_non_standard_height_still_allows_best() -> None:
    info = {
        "title": "540p",
        "formats": [
            {"ext": "mp4", "height": 540, "vcodec": "avc1", "acodec": "none"},
            {"ext": "mp4", "height": None, "vcodec": "none", "acodec": "mp4a"},
        ],
    }
    media = build_media_info(info, "https://example.com/540")
    mp4 = next(option for option in media.formats if option.id == "mp4")
    assert [quality.id for quality in mp4.qualities] == ["best"]


@pytest.mark.parametrize(
    ("format_id", "quality"),
    [
        ("mp4", "best"),
        ("mp4", "1080"),
        ("webm", "360"),
        ("mp3", "320"),
        ("mp3", "128"),
        ("m4a", "best"),
        ("best", "best"),
    ],
)
def test_valid_selection(format_id: str, quality: str) -> None:
    validate_selection(format_id, quality)


@pytest.mark.parametrize(
    ("format_id", "quality"),
    [
        ("mp4", "320"),
        ("mp3", "1080"),
        ("m4a", "128"),
        ("best", "720"),
        ("avi", "best"),
    ],
)
def test_invalid_selection(format_id: str, quality: str) -> None:
    with pytest.raises(SelectionError):
        validate_selection(format_id, quality)
