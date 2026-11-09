from __future__ import annotations

from app.services.updates import (
    _extract_app_version,
    _normalized_version,
    _parse_version,
    _update_available,
)


def test_parse_versions_with_prefixes() -> None:
    assert str(_parse_version("n9.0.2")) == "9.0.2"
    assert str(_parse_version("v0.6.1")) == "0.6.1"
    assert str(_parse_version("2026.10.26")) == "2026.10.26"
    assert _parse_version("not-a-version") is None


def test_update_available() -> None:
    assert _update_available("2026.10.26", "2026.11.01") is True
    assert _update_available("2026.10.26", "2026.10.26") is False
    assert _update_available("9.0.2", "9.1.0") is True
    assert _update_available(None, "9.0.2") is None


def test_normalized_version() -> None:
    assert _normalized_version("n9.0.2") == "9.0.2"
    assert _normalized_version("v0.6.1") == "0.6.1"
    assert _normalized_version(None) is None


def test_extract_app_version_from_source() -> None:
    source = '"""Vidora backend."""\n\n__version__ = "1.2.3"\n'
    assert _extract_app_version(source) == "1.2.3"
    assert _extract_app_version('__version__ = "1.2.3"\n') == "1.2.3"
    assert _extract_app_version("no version here") is None
