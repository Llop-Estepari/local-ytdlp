"""Local API security: token, origin and DNS-rebinding checks."""

from __future__ import annotations

import hmac
import ipaddress
from urllib.parse import urlparse

from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

from .config import Settings

PUBLIC_API_PATHS = {"/api/health", "/api/session"}
LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost"}


def is_loopback_client(host: str | None, settings: Settings) -> bool:
    if settings.test_mode and host in {"testclient", "testserver"}:
        return True
    if not host:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host == "localhost"
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_loopback


def _origin_allowed(origin: str | None, request: Request | WebSocket, settings: Settings) -> bool:
    if not origin:
        return True
    if origin in settings.allowed_origins:
        return True
    if settings.allow_network:
        parsed = urlparse(origin)
        host_header = request.headers.get("host", "")
        if parsed.scheme in {"http", "https"} and parsed.netloc == host_header:
            return True
    return False


def _error_response(status_code: int, message: str, hint: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"message": message, "hint": hint}},
    )


def _security_headers(settings: Settings) -> dict[str, str]:
    port = settings.port
    connect_sources = [
        "'self'",
        f"ws://127.0.0.1:{port}",
        f"ws://localhost:{port}",
        f"http://127.0.0.1:{port}",
        f"http://localhost:{port}",
    ]
    if settings.allow_network:
        connect_sources.extend(["ws:", "wss:"])
    csp = "; ".join(
        [
            "default-src 'self'",
            "base-uri 'none'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' https: http: data:",
            "font-src 'self' data:",
            "media-src 'none'",
            f"connect-src {' '.join(connect_sources)}",
        ]
    )
    return {
        "Content-Security-Policy": csp,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Cross-Origin-Opener-Policy": "same-origin",
    }


def build_http_security_middleware(settings: Settings):
    headers = _security_headers(settings)

    async def middleware(request: Request, call_next):
        path = request.url.path

        if path.startswith("/api"):
            origin = request.headers.get("origin")
            if not _origin_allowed(origin, request, settings):
                return _error_response(
                    403,
                    "Origen de la petición no permitido.",
                    "La aplicación solo acepta peticiones desde su propia interfaz local.",
                )

            fetch_site = request.headers.get("sec-fetch-site")
            if not origin and fetch_site and fetch_site not in {"same-origin", "none"}:
                return _error_response(
                    403,
                    "Petición entre sitios bloqueada.",
                    "Abre la aplicación directamente en localhost.",
                )

            if path not in PUBLIC_API_PATHS:
                token = request.headers.get("x-api-token", "")
                if not token or not hmac.compare_digest(token, settings.token):
                    return _error_response(
                        401,
                        "Token local no válido.",
                        "Recarga la aplicación para obtener un token nuevo.",
                    )

            if path == "/api/session":
                client_host = request.client.host if request.client else None
                if not is_loopback_client(client_host, settings):
                    return _error_response(
                        403,
                        "El token solo se entrega a clientes locales.",
                        "El acceso por red requiere configurar el token manualmente.",
                    )

        response = await call_next(request)

        for key, value in headers.items():
            response.headers.setdefault(key, value)

        if path.startswith("/_next/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-store"

        return response

    return middleware


async def authorize_websocket(websocket: WebSocket, settings: Settings) -> bool:
    """Validate the WebSocket origin and the token sent as a subprotocol."""

    origin = websocket.headers.get("origin")
    if not _origin_allowed(origin, websocket, settings):
        await websocket.close(code=1008)
        return False

    client_host = websocket.client.host if websocket.client else None
    if not settings.allow_network and not is_loopback_client(client_host, settings):
        await websocket.close(code=1008)
        return False

    raw_protocols = websocket.headers.get("sec-websocket-protocol", "")
    protocols = [item.strip() for item in raw_protocols.split(",") if item.strip()]
    if len(protocols) < 2 or protocols[0] != "local-ytdlp":
        await websocket.close(code=1008)
        return False
    if not hmac.compare_digest(protocols[1], settings.token):
        await websocket.close(code=1008)
        return False
    return True
