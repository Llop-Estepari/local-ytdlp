"""Application service container."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings
from ..services.downloader import DownloadManager
from ..services.fs import FileSystemService
from ..services.tools import ToolsService
from ..services.updates import UpdateChecker
from ..services.ytdlp import YtDlpService


@dataclass(slots=True)
class AppContext:
    settings: Settings
    tools: ToolsService
    ytdlp: YtDlpService
    filesystem: FileSystemService
    downloads: DownloadManager
    updates: UpdateChecker
    logger: logging.Logger
