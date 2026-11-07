"""HTTP and WebSocket endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect

from .. import __version__
from ..core.context import AppContext
from ..core.errors import ToolUnavailableError
from ..core.security import authorize_websocket
from ..core.urls import validate_media_url
from ..models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ConfigResponse,
    DependenciesResponse,
    DirectoryListing,
    DownloadRequest,
    DownloadState,
    HealthResponse,
    MkdirRequest,
    OpenFolderRequest,
    RootEntry,
    SessionResponse,
    UpdateCheckResponse,
)
from ..services.downloader import FINAL_STATUSES
from ..services.formats import build_media_info, build_playlist_info, is_playlist_info

router = APIRouter()
ws_router = APIRouter()


def _ctx(request: Request) -> AppContext:
    return request.app.state.ctx


@router.get("/health", response_model=HealthResponse, tags=["service"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/session", response_model=SessionResponse, tags=["security"])
async def session(request: Request, response: Response) -> SessionResponse:
    response.headers["Cache-Control"] = "no-store"
    return SessionResponse(token=_ctx(request).settings.token)


@router.get("/config", response_model=ConfigResponse, tags=["service"])
async def config(request: Request) -> ConfigResponse:
    ctx = _ctx(request)
    return ConfigResponse(
        app_version=__version__,
        default_destination=str(ctx.filesystem.default_destination),
        roots=ctx.filesystem.roots_payload(),
        allow_network=ctx.settings.allow_network,
    )


@router.get("/dependencies", response_model=DependenciesResponse, tags=["tools"])
async def dependencies(request: Request) -> DependenciesResponse:
    payload = await _ctx(request).tools.dependencies()
    return DependenciesResponse(**payload)


@router.post("/dependencies/check-updates", response_model=UpdateCheckResponse, tags=["tools"])
async def check_updates(request: Request) -> UpdateCheckResponse:
    ctx = _ctx(request)
    ytdlp_version = await ctx.tools.ytdlp_version()
    ffmpeg_version = await ctx.tools.ffmpeg_version()
    payload = await ctx.updates.check(
        ytdlp_installed=ytdlp_version,
        ffmpeg_installed=ffmpeg_version,
        refresh=True,
    )
    return UpdateCheckResponse(**payload)


@router.post("/analyze", response_model=AnalyzeResponse, tags=["media"])
async def analyze(payload: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    ctx = _ctx(request)
    if not ctx.ytdlp.tool.installed:
        raise ToolUnavailableError(
            "yt-dlp no está instalado.",
            "Ejecuta el instalador de la aplicación para instalar las dependencias.",
        )
    url = await validate_media_url(payload.url)
    info = await ctx.ytdlp.analyze(url)
    if is_playlist_info(info):
        sample = await ctx.ytdlp.analyze_playlist_sample(url)
        return build_playlist_info(info, sample, url)
    return build_media_info(info, url)


@router.post("/downloads", response_model=DownloadState, status_code=201, tags=["downloads"])
async def start_download(payload: DownloadRequest, request: Request) -> DownloadState:
    return await _ctx(request).downloads.start(payload)


@router.get("/downloads/{download_id}", response_model=DownloadState, tags=["downloads"])
async def get_download(download_id: str, request: Request) -> DownloadState:
    state = _ctx(request).downloads.get_state(download_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "La descarga no existe.", "hint": None},
        )
    return state


@router.post(
    "/downloads/{download_id}/cancel",
    response_model=DownloadState,
    tags=["downloads"],
)
async def cancel_download(download_id: str, request: Request) -> DownloadState:
    state = await _ctx(request).downloads.cancel(download_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail={"message": "La descarga no existe.", "hint": None},
        )
    return state


@router.get("/fs/roots", response_model=list[RootEntry], tags=["filesystem"])
async def fs_roots(request: Request) -> list[RootEntry]:
    return _ctx(request).filesystem.roots_payload()


@router.get("/fs/list", response_model=DirectoryListing, tags=["filesystem"])
async def fs_list(
    request: Request,
    path: str | None = Query(default=None, max_length=4096),
) -> DirectoryListing:
    return _ctx(request).filesystem.list_directory(path)


@router.post("/fs/mkdir", response_model=RootEntry, status_code=201, tags=["filesystem"])
async def fs_mkdir(payload: MkdirRequest, request: Request) -> RootEntry:
    path = _ctx(request).filesystem.create_directory(payload.path, payload.name)
    return RootEntry(path=path, label=payload.name.strip())


@router.post("/open-folder", tags=["filesystem"])
async def open_folder(payload: OpenFolderRequest, request: Request) -> dict[str, bool]:
    _ctx(request).filesystem.open_folder(payload.path)
    return {"ok": True}


@ws_router.websocket("/ws/downloads/{download_id}")
async def download_progress(websocket: WebSocket, download_id: str) -> None:
    ctx: AppContext = websocket.app.state.ctx
    if not await authorize_websocket(websocket, ctx.settings):
        return

    queue = ctx.downloads.subscribe(download_id)
    if queue is None:
        await websocket.close(code=1008)
        return

    await websocket.accept(subprotocol="local-ytdlp")
    try:
        while True:
            try:
                snapshot: dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=20)
            except TimeoutError:
                state = ctx.downloads.get_state(download_id)
                if state is None:
                    break
                snapshot = state.model_dump()

            await websocket.send_json(snapshot)
            if snapshot.get("status") in FINAL_STATUSES:
                break
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        ctx.downloads.unsubscribe(download_id, queue)
        try:
            await websocket.close()
        except RuntimeError:
            pass
