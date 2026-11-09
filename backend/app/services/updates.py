"""Best-effort update checks for Vidora, yt-dlp and FFmpeg."""

from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime, timezone

import httpx
from packaging.version import InvalidVersion, Version

from .. import __version__

_CACHE_TTL = 3600.0
_HEADERS = {"User-Agent": "Vidora/1.0"}
_APP_REPO = "Llop-Estepari/local-ytdlp"
_APP_VERSION_URL = (
    "https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/"
    "backend/app/__init__.py"
)
_APP_VERSION_RE = re.compile(
    r"^__version__\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE
)


def _parse_version(raw: str | None) -> Version | None:
    if not raw:
        return None
    cleaned = raw.strip().lstrip("nNvV")
    match = re.match(r"(\d+(?:\.\d+)*)", cleaned)
    if not match:
        return None
    try:
        return Version(match.group(1))
    except InvalidVersion:
        return None


def _normalized_version(raw: str | None) -> str | None:
    parsed = _parse_version(raw)
    return str(parsed) if parsed is not None else raw


def _update_available(installed: str | None, latest: str | None) -> bool | None:
    if not installed or not latest:
        return None
    current = _parse_version(installed)
    available = _parse_version(latest)
    if current is None or available is None:
        return None
    return available > current


def _extract_app_version(source: str) -> str | None:
    match = _APP_VERSION_RE.search(source)
    if not match:
        return None
    return match.group(1).strip() or None


class UpdateChecker:
    def __init__(self) -> None:
        self._cached: dict | None = None
        self._cached_at = 0.0

    async def check(
        self,
        *,
        ytdlp_installed: str | None,
        ffmpeg_installed: str | None,
        refresh: bool = False,
    ) -> dict:
        now = time.monotonic()
        if not refresh and self._cached and now - self._cached_at < _CACHE_TTL:
            return self._cached

        ytdlp_result, ffmpeg_result, app_result = await asyncio.gather(
            self._check_ytdlp(ytdlp_installed),
            self._check_ffmpeg(ffmpeg_installed),
            self._check_app(__version__),
        )
        payload = {
            "app": app_result,
            "ytdlp": ytdlp_result,
            "ffmpeg": ffmpeg_result,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        self._cached = payload
        self._cached_at = now
        return payload

    async def _check_app(self, installed: str) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=8.0, headers=_HEADERS, follow_redirects=True
            ) as client:
                latest = await self._latest_app_version(client)
            if not isinstance(latest, str) or not latest:
                raise ValueError("Respuesta sin versión")
            normalized = _normalized_version(latest)
            return {
                "installed": installed,
                "latest": normalized,
                "update_available": _update_available(installed, normalized),
                "error": None,
            }
        except Exception:
            return {
                "installed": installed,
                "latest": None,
                "update_available": None,
                "error": "No se pudo comprobar la última versión de Vidora.",
            }

    async def _latest_app_version(self, client: httpx.AsyncClient) -> str | None:
        response = await client.get(
            f"https://api.github.com/repos/{_APP_REPO}/releases/latest"
        )
        if response.status_code != 404:
            response.raise_for_status()
            tag = response.json().get("tag_name")
            if isinstance(tag, str) and _parse_version(tag) is not None:
                return tag

        response = await client.get(
            f"https://api.github.com/repos/{_APP_REPO}/tags?per_page=100"
        )
        if response.status_code == 200:
            tags = response.json()
            versions = [
                item.get("name")
                for item in tags
                if isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and not any(
                    marker in item["name"].lower()
                    for marker in ("dev", "rc", "beta", "alpha")
                )
                and _parse_version(item["name"]) is not None
            ]
            if versions:
                return max(versions, key=lambda value: _parse_version(value))

        response = await client.get(_APP_VERSION_URL)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return _extract_app_version(response.text)

    async def _check_ytdlp(self, installed: str | None) -> dict:
        if not installed:
            return {
                "installed": None,
                "latest": None,
                "update_available": None,
                "error": "yt-dlp no está instalado.",
            }
        try:
            async with httpx.AsyncClient(
                timeout=8.0, headers=_HEADERS, follow_redirects=True
            ) as client:
                response = await client.get("https://pypi.org/pypi/yt-dlp/json")
                response.raise_for_status()
                latest = response.json().get("info", {}).get("version")
            if not isinstance(latest, str) or not latest:
                raise ValueError("Respuesta sin versión")
            return {
                "installed": installed,
                "latest": latest,
                "update_available": _update_available(installed, latest),
                "error": None,
            }
        except Exception:
            return {
                "installed": installed,
                "latest": None,
                "update_available": None,
                "error": "No se pudo comprobar la última versión de yt-dlp.",
            }

    async def _check_ffmpeg(self, installed: str | None) -> dict:
        if not installed:
            return {
                "installed": None,
                "latest": None,
                "update_available": None,
                "error": "FFmpeg no está instalado.",
            }
        try:
            async with httpx.AsyncClient(
                timeout=8.0, headers=_HEADERS, follow_redirects=True
            ) as client:
                latest = await self._latest_ffmpeg_tag(client)
            if not isinstance(latest, str) or not latest:
                raise ValueError("Respuesta sin versión")
            normalized = _normalized_version(latest)
            return {
                "installed": installed,
                "latest": normalized,
                "update_available": _update_available(installed, normalized),
                "error": None,
            }
        except Exception:
            return {
                "installed": installed,
                "latest": None,
                "update_available": None,
                "error": "No se pudo comprobar la última versión de FFmpeg.",
            }

    async def _latest_ffmpeg_tag(self, client: httpx.AsyncClient) -> str | None:
        response = await client.get(
            "https://api.github.com/repos/FFmpeg/FFmpeg/releases/latest"
        )
        if response.status_code != 404:
            response.raise_for_status()
            tag = response.json().get("tag_name")
            if isinstance(tag, str) and tag:
                return tag

        response = await client.get(
            "https://api.github.com/repos/FFmpeg/FFmpeg/tags?per_page=100"
        )
        if response.status_code == 200:
            tags = response.json()
            versions = [
                item.get("name")
                for item in tags
                if isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and not any(
                    marker in item["name"].lower()
                    for marker in ("dev", "rc", "beta", "alpha")
                )
                and _parse_version(item["name"]) is not None
            ]
            if versions:
                return max(versions, key=lambda value: _parse_version(value))

        response = await client.get("https://ffmpeg.org/releases/")
        response.raise_for_status()
        matches = re.findall(
            r"ffmpeg-(\d+\.\d+(?:\.\d+)?)\.tar\.(?:xz|bz2|gz)",
            response.text,
        )
        if not matches:
            return None
        return max(matches, key=lambda value: _parse_version(value))
