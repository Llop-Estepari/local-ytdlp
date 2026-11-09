"""Runtime configuration for the local service."""

from __future__ import annotations

import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Vidora"
DEFAULT_PORT = 8765
MIN_TOKEN_LENGTH = 24


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _default_data_dir() -> Path:
    override = os.environ.get("LOCAL_YTDLP_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Vidora"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Vidora"

    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "vidora"


def _xdg_user_dir(key: str, fallback: Path) -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_file = config_home / "user-dirs.dirs"
    try:
        for line in config_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith(f"{key}="):
                continue
            value = line.split("=", 1)[1].strip().strip('"')
            value = value.replace("$HOME", str(Path.home()))
            if value:
                return Path(value).expanduser()
    except OSError:
        pass
    return fallback


def _default_roots() -> tuple[Path, ...]:
    home = Path.home()
    if sys.platform.startswith("linux"):
        candidates = [
            _xdg_user_dir("XDG_DOWNLOAD_DIR", home / "Downloads"),
            _xdg_user_dir("XDG_VIDEOS_DIR", home / "Videos"),
            _xdg_user_dir("XDG_MUSIC_DIR", home / "Music"),
            _xdg_user_dir("XDG_DESKTOP_DIR", home / "Desktop"),
        ]
    else:
        candidates = [
            home / "Downloads",
            home / "Videos",
            home / "Music",
            home / "Desktop",
        ]
    roots: list[Path] = []
    for candidate in candidates:
        try:
            if candidate.is_dir():
                roots.append(candidate.resolve())
        except OSError:
            continue

    if not roots:
        downloads = home / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        roots.append(downloads.resolve())

    return tuple(dict.fromkeys(roots))


def _configured_roots() -> tuple[Path, ...]:
    raw = os.environ.get("LOCAL_YTDLP_ALLOWED_ROOTS", "").strip()
    if not raw:
        return _default_roots()

    roots: list[Path] = []
    for part in raw.split(os.pathsep):
        part = part.strip()
        if not part:
            continue
        try:
            candidate = Path(part).expanduser().resolve()
        except OSError:
            continue
        if candidate.is_dir():
            roots.append(candidate)

    if not roots:
        raise RuntimeError(
            "LOCAL_YTDLP_ALLOWED_ROOTS no contiene ninguna carpeta existente."
        )
    return tuple(dict.fromkeys(roots))


def _load_token(data_dir: Path, allow_network: bool) -> str:
    env_token = os.environ.get("LOCAL_YTDLP_TOKEN", "").strip()
    if env_token:
        if len(env_token) < MIN_TOKEN_LENGTH:
            raise RuntimeError(
                f"LOCAL_YTDLP_TOKEN debe tener al menos {MIN_TOKEN_LENGTH} caracteres."
            )
        return env_token

    if allow_network:
        raise RuntimeError(
            "El acceso por red requiere definir LOCAL_YTDLP_TOKEN con un valor "
            f"de al menos {MIN_TOKEN_LENGTH} caracteres."
        )

    token_file = data_dir / "token"
    try:
        if token_file.is_file():
            existing = token_file.read_text(encoding="utf-8").strip()
            if len(existing) >= MIN_TOKEN_LENGTH:
                return existing
    except OSError:
        pass

    token = secrets.token_urlsafe(32)
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token)
        if os.name != "nt":
            os.chmod(token_file, 0o600)
    except OSError:
        # The app still works without a persistent token; a new one is created
        # on the next start.
        pass
    return token


def _allowed_origins(port: int) -> frozenset[str]:
    origins = {
        f"http://127.0.0.1:{port}",
        f"http://localhost:{port}",
        f"http://[::1]:{port}",
        # Next.js development server.
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://[::1]:3000",
    }
    extra = os.environ.get("LOCAL_YTDLP_ALLOWED_ORIGINS", "")
    for item in extra.split(","):
        item = item.strip()
        if item:
            origins.add(item)
    return frozenset(origins)


def _trusted_hosts(allow_network: bool) -> tuple[str, ...]:
    raw = os.environ.get("LOCAL_YTDLP_TRUSTED_HOSTS", "").strip()
    if raw:
        return tuple(item.strip() for item in raw.split(",") if item.strip())
    if allow_network:
        # Network mode is opt-in and protected by the API token.
        return ("*",)
    return ("127.0.0.1", "localhost", "::1", "[::1]")


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    app_data_dir: Path
    allowed_roots: tuple[Path, ...]
    token: str
    allow_network: bool
    trusted_hosts: tuple[str, ...]
    allowed_origins: frozenset[str]
    project_root: Path
    frontend_dir: Path
    test_mode: bool = False

    @property
    def temp_dir(self) -> Path:
        return self.app_data_dir / "tmp"

    @property
    def log_dir(self) -> Path:
        return self.app_data_dir / "logs"

    @classmethod
    def load(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[3]
        allow_network = _env_flag("LOCAL_YTDLP_ALLOW_NETWORK")
        host = os.environ.get(
            "LOCAL_YTDLP_HOST",
            "0.0.0.0" if allow_network else "127.0.0.1",
        ).strip()
        port = _env_int("LOCAL_YTDLP_PORT", DEFAULT_PORT)
        app_data_dir = _default_data_dir()
        app_data_dir.mkdir(parents=True, exist_ok=True)
        frontend_override = os.environ.get("LOCAL_YTDLP_FRONTEND_DIR")
        frontend_dir = (
            Path(frontend_override).expanduser().resolve()
            if frontend_override
            else project_root / "frontend" / "out"
        )

        return cls(
            host=host,
            port=port,
            app_data_dir=app_data_dir,
            allowed_roots=_configured_roots(),
            token=_load_token(app_data_dir, allow_network),
            allow_network=allow_network,
            trusted_hosts=_trusted_hosts(allow_network),
            allowed_origins=_allowed_origins(port),
            project_root=project_root,
            frontend_dir=frontend_dir,
        )

    @classmethod
    def for_testing(
        cls,
        base_dir: Path,
        *,
        token: str = "test-token-0123456789abcdef",
    ) -> "Settings":
        app_data_dir = base_dir / "data"
        downloads = base_dir / "downloads"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        downloads.mkdir(parents=True, exist_ok=True)
        return cls(
            host="127.0.0.1",
            port=8765,
            app_data_dir=app_data_dir,
            allowed_roots=(downloads.resolve(),),
            token=token,
            allow_network=False,
            trusted_hosts=("testserver", "127.0.0.1", "localhost"),
            allowed_origins=frozenset(
                {
                    "http://testserver",
                    "http://127.0.0.1:8765",
                    "http://localhost:8765",
                    "http://127.0.0.1:3000",
                    "http://localhost:3000",
                }
            ),
            project_root=Path(__file__).resolve().parents[3],
            frontend_dir=base_dir / "frontend",
            test_mode=True,
        )
