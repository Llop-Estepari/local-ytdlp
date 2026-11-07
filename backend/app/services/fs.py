"""Restricted filesystem access for destination folders."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from ..core.config import Settings
from ..core.errors import AppError, PathExistsError, PathNotAllowedError, PathNotFoundError
from ..core.process import popen_kwargs
from ..models.schemas import DirectoryEntry, DirectoryListing, RootEntry

_INVALID_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class FileSystemService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.roots = tuple(settings.allowed_roots)
        self.default_destination = self._pick_default()

    def _pick_default(self) -> Path:
        for root in self.roots:
            if root.name.lower() == "downloads" and os.access(root, os.W_OK):
                return root
        for root in self.roots:
            if os.access(root, os.W_OK):
                return root
        return self.roots[0]

    def _inside(self, path: Path) -> bool:
        return any(path == root or root in path.parents for root in self.roots)

    def _resolve_within(self, raw_path: str | Path) -> Path:
        try:
            path = Path(raw_path).expanduser().resolve()
        except (OSError, RuntimeError) as exc:
            raise PathNotAllowedError(
                "La ruta no es válida.",
                "Elige una carpeta dentro de las ubicaciones permitidas.",
            ) from exc
        if not self._inside(path):
            raise PathNotAllowedError(
                "La carpeta está fuera de las ubicaciones permitidas.",
                "Elige una carpeta dentro de Descargas, Vídeos, Música o Escritorio.",
            )
        return path

    def resolve_destination(self, raw_path: str | Path) -> Path:
        path = self._resolve_within(raw_path)
        if not path.exists():
            raise PathNotFoundError(
                "La carpeta de destino no existe.",
                "Elige otra carpeta.",
            )
        if not path.is_dir():
            raise PathNotFoundError(
                "La ruta de destino no es una carpeta.",
                "Elige una carpeta válida.",
            )
        if not os.access(path, os.W_OK):
            raise AppError(
                "No hay permisos para escribir en la carpeta.",
                "Elige otra carpeta de destino.",
            )
        return path

    def roots_payload(self) -> list[RootEntry]:
        return [
            RootEntry(path=str(root), label=root.name or str(root))
            for root in self.roots
        ]

    def list_directory(self, raw_path: str | None = None) -> DirectoryListing:
        path = self.resolve_destination(raw_path or self.default_destination)
        directories: list[DirectoryEntry] = []
        try:
            children = sorted(path.iterdir(), key=lambda item: item.name.casefold())
        except OSError as exc:
            raise AppError(
                "No se pudo leer la carpeta.",
                "Comprueba los permisos de la carpeta.",
            ) from exc

        for child in children:
            if child.name.startswith("."):
                continue
            try:
                if not child.is_dir():
                    continue
                resolved = child.resolve()
            except OSError:
                continue
            if not self._inside(resolved):
                continue
            directories.append(DirectoryEntry(name=child.name, path=str(resolved)))
            if len(directories) >= 500:
                break

        parent = path.parent
        parent_value = (
            str(parent)
            if parent != path and self._inside(parent) and parent.exists()
            else None
        )
        return DirectoryListing(
            path=str(path),
            parent=parent_value,
            directories=directories,
            writable=os.access(path, os.W_OK),
        )

    def create_directory(self, raw_parent: str, name: str) -> str:
        clean_name = name.strip()
        if not clean_name or clean_name in {".", ".."}:
            raise AppError("El nombre de la carpeta no es válido.")
        if len(clean_name) > 120:
            raise AppError("El nombre de la carpeta es demasiado largo.")
        if _INVALID_NAME_RE.search(clean_name):
            raise AppError(
                "El nombre de la carpeta contiene caracteres no válidos.",
                "Evita los caracteres < > : \" / \\ | ? *.",
            )
        if clean_name.rstrip(". ").lower() in _WINDOWS_RESERVED:
            raise AppError("Ese nombre de carpeta está reservado por el sistema.")
        if clean_name.endswith((".", " ")):
            raise AppError("El nombre de la carpeta no puede terminar en punto o espacio.")

        parent = self.resolve_destination(raw_parent)
        target = self._resolve_within(parent / clean_name)
        if target.exists():
            raise PathExistsError("Ya existe una carpeta con ese nombre.")
        try:
            target.mkdir()
        except OSError as exc:
            raise AppError(
                "No se pudo crear la carpeta.",
                "Comprueba los permisos de la carpeta de destino.",
            ) from exc
        return str(target)

    def open_folder(self, raw_path: str) -> None:
        path = self.resolve_destination(raw_path)
        try:
            if sys.platform == "win32":
                startfile = getattr(os, "startfile", None)
                if startfile is None:
                    raise OSError("startfile no está disponible")
                startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **popen_kwargs(),
                )
            else:
                opener = shutil.which("xdg-open")
                if opener:
                    subprocess.Popen(
                        [opener, str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **popen_kwargs(),
                    )
                else:
                    gio = shutil.which("gio")
                    if not gio:
                        raise OSError("No hay un gestor de archivos disponible")
                    subprocess.Popen(
                        [gio, "open", str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **popen_kwargs(),
                    )
        except OSError as exc:
            raise AppError(
                "No se pudo abrir la carpeta.",
                "Ábrela manualmente desde tu explorador de archivos.",
            ) from exc
