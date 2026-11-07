from __future__ import annotations

import os

import pytest

from app.core.config import Settings
from app.core.errors import AppError, PathExistsError, PathNotAllowedError
from app.services.fs import FileSystemService


@pytest.fixture
def service(settings: Settings) -> FileSystemService:
    return FileSystemService(settings)


def test_default_destination_is_downloads(settings: Settings, service: FileSystemService) -> None:
    assert service.default_destination == settings.allowed_roots[0]
    assert service.default_destination.name == "downloads"


def test_list_and_create_directory(service: FileSystemService, settings: Settings) -> None:
    created = service.create_directory(str(settings.allowed_roots[0]), "Mi carpeta")
    listing = service.list_directory(str(settings.allowed_roots[0]))

    assert listing.path == str(settings.allowed_roots[0])
    assert any(item.name == "Mi carpeta" for item in listing.directories)
    assert listing.parent is None
    assert listing.writable is True
    assert created == str(settings.allowed_roots[0] / "Mi carpeta")


def test_duplicate_directory(service: FileSystemService, settings: Settings) -> None:
    root = str(settings.allowed_roots[0])
    service.create_directory(root, "Repetida")
    with pytest.raises(PathExistsError):
        service.create_directory(root, "Repetida")


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a\\b", "a:b", "CON", "nombre."])
def test_invalid_directory_names(
    service: FileSystemService, settings: Settings, name: str
) -> None:
    with pytest.raises(AppError):
        service.create_directory(str(settings.allowed_roots[0]), name)


def test_traversal_is_rejected(service: FileSystemService, settings: Settings) -> None:
    with pytest.raises(PathNotAllowedError):
        service.list_directory(str(settings.allowed_roots[0] / ".."))


def test_outside_destination_is_rejected(service: FileSystemService) -> None:
    with pytest.raises(PathNotAllowedError):
        service.resolve_destination("/tmp")


def test_symlink_escape_is_rejected(
    service: FileSystemService, settings: Settings, tmp_path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = settings.allowed_roots[0] / "escape"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("El sistema no permite crear symlinks")

    with pytest.raises(PathNotAllowedError):
        service.resolve_destination(str(link))

    listing = service.list_directory(str(settings.allowed_roots[0]))
    assert all(item.name != "escape" for item in listing.directories)
