from __future__ import annotations

import pytest

from app.core.errors import ValidationError
from app.core.urls import validate_media_url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/video.mp4",
        "http://localhost:8765/video.mp4",
        "http://127.0.0.1/video.mp4",
        "http://10.0.0.1/video.mp4",
        "http://192.168.1.5/video.mp4",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/video.mp4",
        "http://example.local/video.mp4",
        "http://user:password@1.1.1.1/video.mp4",
        "not a url",
        "",
    ],
)
async def test_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        await validate_media_url(url)


async def test_accepts_public_ip_literals() -> None:
    assert await validate_media_url("https://1.1.1.1/video.mp4") == "https://1.1.1.1/video.mp4"
    assert (
        await validate_media_url("https://[2606:4700:4700::1111]/video.mp4")
        == "https://[2606:4700:4700::1111]/video.mp4"
    )


async def test_rejects_control_characters() -> None:
    with pytest.raises(ValidationError):
        await validate_media_url("https://1.1.1.1/\x00video")
