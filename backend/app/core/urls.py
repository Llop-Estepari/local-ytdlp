"""URL validation with SSRF and local-network protections."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from .errors import ValidationError

MAX_URL_LENGTH = 2048
_BLOCKED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".home.arpa",
    ".lan",
)


def _is_global_address(raw: str) -> bool:
    try:
        address = ipaddress.ip_address(raw)
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global


async def validate_media_url(raw_url: str) -> str:
    """Validate an HTTP(S) URL that yt-dlp is allowed to fetch.

    Private, loopback and link-local destinations are rejected to avoid using
    the local service as a bridge to the user's network.
    """

    url = (raw_url or "").strip()
    if not url:
        raise ValidationError("Introduce una URL.")
    if len(url) > MAX_URL_LENGTH:
        raise ValidationError(
            "La URL es demasiado larga.",
            f"El límite es de {MAX_URL_LENGTH} caracteres.",
        )
    if any(ord(char) < 32 for char in url):
        raise ValidationError("La URL contiene caracteres no válidos.")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValidationError(
            "Solo se admiten enlaces HTTP o HTTPS.",
            "Los enlaces locales (file://) no están permitidos.",
        )
    if not parsed.hostname:
        raise ValidationError("La URL no contiene un dominio válido.")
    if parsed.username or parsed.password:
        raise ValidationError("La URL no puede incluir credenciales.")
    if parsed.port == 0:
        raise ValidationError("El puerto de la URL no es válido.")

    host = parsed.hostname.rstrip(".").lower()
    if not host:
        raise ValidationError("La URL no contiene un dominio válido.")
    if host == "localhost" or host.endswith(_BLOCKED_HOST_SUFFIXES):
        raise ValidationError(
            "No se permiten direcciones locales o privadas.",
            "Introduce el enlace público del contenido.",
        )
    if "%" in host:
        raise ValidationError("La URL no es válida.")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not _is_global_address(str(literal)):
            raise ValidationError(
                "No se permiten direcciones locales o privadas.",
                "Introduce el enlace público del contenido.",
            )
        return url

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValidationError("El dominio de la URL no es válido.") from exc

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        infos = await asyncio.wait_for(
            asyncio.to_thread(
                socket.getaddrinfo,
                ascii_host,
                port,
                type=socket.SOCK_STREAM,
            ),
            timeout=6,
        )
    except (socket.gaierror, OSError, TimeoutError) as exc:
        raise ValidationError(
            "No se pudo resolver el dominio.",
            "Comprueba la URL y tu conexión a Internet.",
        ) from exc

    addresses = {info[4][0] for info in infos if info[4]}
    if not addresses:
        raise ValidationError("No se pudo resolver el dominio.")
    if any(not _is_global_address(address) for address in addresses):
        raise ValidationError(
            "La URL apunta a una dirección local o privada.",
            "Introduce el enlace público del contenido.",
        )

    return url
