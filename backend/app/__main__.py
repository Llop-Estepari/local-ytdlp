"""Allow ``python -m app`` for a simple local start."""

from __future__ import annotations

import uvicorn

from .core.config import Settings
from .factory import create_app


def main() -> None:
    settings = Settings.load()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
