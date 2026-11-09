"""Pydantic models shared by the API and the frontend."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DownloadFormat = Literal["mp4", "webm", "mp3", "m4a", "best"]
DownloadStatus = Literal[
    "starting",
    "downloading",
    "processing",
    "completed",
    "cancelled",
    "error",
]


class QualityOption(BaseModel):
    id: str
    label: str


class FormatOption(BaseModel):
    id: DownloadFormat
    label: str
    kind: Literal["video", "audio"]
    qualities: list[QualityOption]


class MediaInfo(BaseModel):
    kind: Literal["media"] = "media"
    url: str
    title: str
    duration: float | None = None
    thumbnail: str | None = None
    extractor: str | None = None
    formats: list[FormatOption]


class PlaylistEntry(BaseModel):
    index: int
    title: str
    duration: float | None = None
    thumbnail: str | None = None


class PlaylistInfo(BaseModel):
    kind: Literal["playlist"] = "playlist"
    url: str
    title: str
    entry_count: int
    thumbnail: str | None = None
    extractor: str | None = None
    formats: list[FormatOption]
    entries: list[PlaylistEntry]


AnalyzeResponse = MediaInfo | PlaylistInfo


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=4, max_length=2048)


class DownloadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=4, max_length=2048)
    format: DownloadFormat
    quality: str = Field(min_length=1, max_length=8)
    destination: str = Field(min_length=1, max_length=4096)
    playlist: bool = False
    playlist_count: int | None = Field(default=None, ge=1, le=100_000)
    playlist_item: int | None = Field(default=None, ge=1, le=100_000)
    numbered: bool = False


class DownloadState(BaseModel):
    id: str
    url: str
    format: DownloadFormat
    quality: str
    destination: str
    status: DownloadStatus
    percent: float | None = None
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    filename: str | None = None
    filepath: str | None = None
    playlist: bool = False
    playlist_index: int | None = None
    playlist_count: int | None = None
    current_title: str | None = None
    item_percent: float | None = None
    file_count: int = 0
    error: str | None = None
    error_hint: str | None = None
    created_at: str
    updated_at: str


class RootEntry(BaseModel):
    path: str
    label: str


class ConfigResponse(BaseModel):
    app_version: str
    default_destination: str
    roots: list[RootEntry]
    allow_network: bool


class DirectoryEntry(BaseModel):
    name: str
    path: str


class DirectoryListing(BaseModel):
    path: str
    parent: str | None = None
    directories: list[DirectoryEntry]
    writable: bool


class MkdirRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=4096)
    name: str = Field(min_length=1, max_length=120)


class OpenFolderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=4096)


class ToolStatus(BaseModel):
    installed: bool
    version: str | None = None
    path: str | None = None


class DependenciesResponse(BaseModel):
    ok: bool
    ytdlp: ToolStatus
    ffmpeg: ToolStatus


class ToolUpdateStatus(BaseModel):
    installed: str | None = None
    latest: str | None = None
    update_available: bool | None = None
    error: str | None = None


class AppUpdateStatus(BaseModel):
    installed: str
    latest: str | None = None
    update_available: bool | None = None
    error: str | None = None


class UpdateCheckResponse(BaseModel):
    app: AppUpdateStatus
    ytdlp: ToolUpdateStatus
    ffmpeg: ToolUpdateStatus
    checked_at: str


ToolName = Literal["ytdlp", "ffmpeg"]


class UpdateToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName


class DependencyUpdateResponse(BaseModel):
    tool: ToolName
    updated: bool
    version: str | None = None
    error: str | None = None
    hint: str | None = None
    dependencies: DependenciesResponse
    check: UpdateCheckResponse | None = None


class SessionResponse(BaseModel):
    token: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
