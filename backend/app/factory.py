"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .api.routes import router, ws_router
from .core.config import Settings
from .core.context import AppContext
from .core.errors import AppError
from .core.logging import setup_logging
from .core.security import build_http_security_middleware
from .services.downloader import DownloadManager
from .services.fs import FileSystemService
from .services.tools import ToolsService
from .services.updates import UpdateChecker
from .services.ytdlp import YtDlpService


def _build_context(settings: Settings, logger: logging.Logger) -> AppContext:
    tools = ToolsService(settings.project_root)
    ytdlp = YtDlpService(tools.ytdlp, tools.ffmpeg)
    filesystem = FileSystemService(settings)
    downloads = DownloadManager(settings, ytdlp, tools.ffmpeg, filesystem)
    updates = UpdateChecker()
    return AppContext(
        settings=settings,
        tools=tools,
        ytdlp=ytdlp,
        filesystem=filesystem,
        downloads=downloads,
        updates=updates,
        logger=logger,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    logger = setup_logging(settings)
    ctx = _build_context(settings, logger)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info(
            "Vidora %s en http://%s:%s (datos: %s)",
            __version__,
            settings.host,
            settings.port,
            settings.app_data_dir,
        )
        dependencies = await ctx.tools.dependencies()
        ytdlp_version = dependencies["ytdlp"]["version"] or "no instalado"
        ffmpeg_version = dependencies["ffmpeg"]["version"] or "no instalado"
        logger.info("yt-dlp: %s | FFmpeg: %s", ytdlp_version, ffmpeg_version)
        if not dependencies["ytdlp"]["installed"]:
            logger.warning("yt-dlp no está instalado.")
        if not dependencies["ffmpeg"]["installed"]:
            logger.warning("FFmpeg no está instalado.")
        try:
            yield
        finally:
            await ctx.downloads.shutdown()
            logger.info("Servicio detenido.")

    app = FastAPI(
        title="Vidora API",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.ctx = ctx

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(settings.trusted_hosts),
        www_redirect=False,
    )
    app.middleware("http")(build_http_security_middleware(settings))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Token"],
        max_age=600,
    )

    app.include_router(router, prefix="/api")
    app.include_router(ws_router)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"message": exc.message, "hint": exc.hint}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        field = None
        if exc.errors():
            location = exc.errors()[0].get("loc", ())
            field = ".".join(str(part) for part in location if part not in {"body", "query", "path"})
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "message": "La solicitud no es válida.",
                    "hint": f"Revisa el campo «{field}»." if field else None,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "message" in detail:
            content = {"detail": detail}
        else:
            content = {"detail": {"message": str(detail), "hint": None}}
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado en %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "message": "Ha ocurrido un error inesperado.",
                    "hint": "Consulta el log local de la aplicación.",
                }
            },
        )

    index = settings.frontend_dir / "index.html"
    if index.is_file():
        app.mount(
            "/",
            StaticFiles(directory=settings.frontend_dir, html=True),
            name="frontend",
        )
    else:

        @app.get("/", include_in_schema=False)
        async def frontend_missing() -> HTMLResponse:
            return HTMLResponse(
                "<!doctype html><html lang='es'><meta charset='utf-8'>"
                "<title>Vidora</title>"
                "<body style='font-family:system-ui;padding:3rem;max-width:40rem;margin:auto'>"
                "<h1>Frontend no compilado</h1>"
                "<p>Ejecuta <code>npm install &amp;&amp; npm run build</code> dentro de "
                "<code>frontend/</code> y vuelve a iniciar la aplicación.</p>"
                "</body></html>",
                status_code=503,
            )

    return app
