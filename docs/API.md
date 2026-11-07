# Referencia de la API

La API se sirve en `http://127.0.0.1:8765/api` (configurable con `LOCAL_YTDLP_PORT`). El frontend de producción se sirve desde el mismo origen; en desarrollo, Next.js usa `http://127.0.0.1:3000`.

La documentación interactiva de FastAPI está desactivada. El esquema OpenAPI está disponible en `GET /api/openapi.json` (requiere token).

## Autenticación

1. `GET /api/session` devuelve `{ "token": "..." }`. Solo se permite desde loopback (`127.0.0.1`, `::1`, `localhost`) y con un `Origin` permitido.
2. Todas las rutas de `/api` excepto `/api/health` y `/api/session` requieren la cabecera:

```
X-API-Token: <token>
```

3. El WebSocket envía el token como subprotocolo:

```
Sec-WebSocket-Protocol: local-ytdlp, <token>
```

El token se guarda en memoria y, en el frontend, en `sessionStorage`. En modo red se puede pasar una vez mediante `#token=...` en la URL.

### Validaciones adicionales

- `Host` debe estar entre los hosts permitidos (`127.0.0.1`, `localhost`, `::1` por defecto).
- `Origin`, si está presente, debe ser local (o coincidir con el `Host` en modo red).
- Si no hay `Origin`, `Sec-Fetch-Site` no puede ser `cross-site`.
- Las respuestas incluyen CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y `Cross-Origin-Opener-Policy`.

## Formato de errores

```json
{
  "detail": {
    "message": "Mensaje comprensible para el usuario.",
    "hint": "Explicación o acción recomendada."
  }
}
```

`hint` puede ser `null`. Los errores de validación de Pydantic usan el mismo formato.

> Los mensajes de la API se generan en español. La interfaz los traduce al inglés para los mensajes conocidos; los detalles dinámicos no reconocidos se muestran tal cual.

| Código | Significado |
| --- | --- |
| 400 | Solicitud o URL no válida |
| 401 | Token ausente o incorrecto |
| 403 | Origen, host o carpeta no permitidos |
| 404 | Descarga o ruta inexistente |
| 409 | Conflicto (carpeta ya existente) |
| 422 | yt-dlp no pudo procesar el contenido |
| 503 | yt-dlp o FFmpeg no disponibles |
| 504 | Tiempo de espera agotado |

## Servicio

### `GET /api/health`

Público.

```json
{ "status": "ok", "version": "1.0.0" }
```

### `GET /api/session`

Público solo para loopback. Devuelve el token local. `Cache-Control: no-store`.

```json
{ "token": "..." }
```

### `GET /api/config`

```json
{
  "app_version": "1.0.0",
  "default_destination": "/home/usuario/Downloads",
  "roots": [{ "path": "/home/usuario/Downloads", "label": "Downloads" }],
  "allow_network": false
}
```

## Dependencias

### `GET /api/dependencies`

```json
{
  "ok": true,
  "ytdlp": { "installed": true, "version": "2026.10.26", "path": "..." },
  "ffmpeg": { "installed": true, "version": "9.0.2", "path": "/usr/bin/ffmpeg" }
}
```

### `POST /api/dependencies/check-updates`

Consulta PyPI y el repositorio de FFmpeg. Sin cuerpo.

```json
{
  "ytdlp": {
    "installed": "2026.10.26",
    "latest": "2026.10.26",
    "update_available": false,
    "error": null
  },
  "ffmpeg": {
    "installed": "9.0.2",
    "latest": "9.0.2",
    "update_available": false,
    "error": null
  },
  "checked_at": "2026-11-07T16:58:03+00:00"
}
```

`update_available` puede ser `null` si no se pueden comparar las versiones.

## Análisis

### `POST /api/analyze`

```json
{ "url": "https://www.youtube.com/watch?v=..." }
```

Respuesta para un vídeo o audio individual:

```json
{
  "kind": "media",
  "url": "https://www.youtube.com/watch?v=...",
  "title": "Título",
  "duration": 213,
  "thumbnail": "https://...",
  "extractor": "YouTube",
  "formats": [
    {
      "id": "mp4",
      "label": "MP4 · Vídeo",
      "kind": "video",
      "qualities": [
        { "id": "best", "label": "Mejor disponible" },
        { "id": "1080", "label": "1080p · Full HD" }
      ]
    },
    {
      "id": "mp3",
      "label": "MP3 · Audio",
      "kind": "audio",
      "qualities": [
        { "id": "320", "label": "320 kbps" },
        { "id": "256", "label": "256 kbps" },
        { "id": "192", "label": "192 kbps" },
        { "id": "128", "label": "128 kbps" }
      ]
    }
  ]
}
```

Solo se devuelven formatos y calidades que existen realmente.

### Respuesta para una lista de reproducción

Si la URL apunta a una lista (o a una pestaña de vídeos de un canal), la respuesta cambia a `kind: "playlist"`:

```json
{
  "kind": "playlist",
  "url": "https://www.youtube.com/playlist?list=...",
  "title": "Mi lista",
  "entry_count": 12,
  "thumbnail": "https://...",
  "extractor": "YouTube",
  "formats": [
    {
      "id": "mp3",
      "label": "MP3 · Audio",
      "kind": "audio",
      "qualities": [
        { "id": "320", "label": "320 kbps" },
        { "id": "256", "label": "256 kbps" },
        { "id": "192", "label": "192 kbps" },
        { "id": "128", "label": "128 kbps" }
      ]
    }
  ],
  "entries": [
    { "index": 1, "title": "Primera canción", "duration": 214, "thumbnail": null },
    { "index": 2, "title": "Segunda canción", "duration": 187, "thumbnail": null }
  ]
}
```

- `entry_count` es el número total de elementos; `entries` incluye todos los elementos disponibles (hasta 1000). La interfaz muestra los primeros 50 en la vista previa, pero usa la lista completa para encolar.
- Los formatos y calidades se detectan analizando hasta los tres primeros elementos disponibles, por lo que siguen siendo opciones reales.
- Las listas vacías, privadas o sin elementos descargables devuelven un error con mensaje y sugerencia.

## Descargas

### `POST /api/downloads`

Vídeo individual:

```json
{
  "url": "https://...",
  "format": "mp4",
  "quality": "1080",
  "destination": "/home/usuario/Downloads"
}
```

Lista de reproducción:

```json
{
  "url": "https://www.youtube.com/playlist?list=...",
  "format": "mp3",
  "quality": "192",
  "destination": "/home/usuario/Music",
  "playlist": true,
  "playlist_count": 12
}
```

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `playlist` | `bool` (por defecto `false`) | Con `false` se usa `--no-playlist` (solo el vídeo). Con `true` se descarga toda la lista con `--yes-playlist`. |
| `playlist_count` | `int \| null` | Número de elementos detectado en el análisis; se usa para calcular el progreso total si yt-dlp no informa del total. |
| `playlist_item` | `int \| null` | Índice 1-based de una sola canción de la lista. Usa `--playlist-items N`, descarga solo ese elemento y no añade prefijo numérico al archivo. |
| `numbered` | `bool` (por defecto `false`) | Usa la plantilla `001 - Título [id].ext` también en descargas de un solo elemento. El frontend lo activa al encolar una lista completa. |

Ejemplo para una sola canción de la lista:

```json
{
  "url": "https://www.youtube.com/playlist?list=...",
  "format": "mp3",
  "quality": "320",
  "destination": "/home/usuario/Music",
  "playlist_item": 3,
  "numbered": true
}
```

En este caso el estado se comporta como una descarga individual (`playlist: false`), aunque yt-dlp extraiga el elemento de la lista. Al encolar una lista completa, el frontend crea una petición por canción con `playlist_item` y `numbered: true`, y las descarga secuencialmente.

`format`: `mp4`, `webm`, `mp3`, `m4a` o `best`.

`quality`:

- `mp4`/`webm`: `best`, `2160`, `1440`, `1080`, `720`, `480`, `360`.
- `mp3`: `320`, `256`, `192`, `128`.
- `m4a`/`best`: `best`.

Responde `201` con el estado inicial. La descarga continúa en segundo plano.

```json
{
  "id": "4b695bdeb272402bbc02bd9ce13487ca",
  "url": "https://...",
  "format": "mp4",
  "quality": "1080",
  "destination": "/home/usuario/Downloads",
  "status": "starting",
  "percent": null,
  "downloaded_bytes": null,
  "total_bytes": null,
  "speed": null,
  "eta": null,
  "filename": null,
  "filepath": null,
  "playlist": false,
  "playlist_index": null,
  "playlist_count": null,
  "current_title": null,
  "item_percent": null,
  "file_count": 0,
  "error": null,
  "error_hint": null,
  "created_at": "2026-11-07T16:44:55+00:00",
  "updated_at": "2026-11-07T16:44:55+00:00"
}
```

Estados: `starting`, `downloading`, `processing`, `completed`, `cancelled`, `error`.

Campos adicionales del estado:

| Campo | Descripción |
| --- | --- |
| `playlist` | `true` si la descarga es una lista completa. |
| `playlist_index` / `playlist_count` | Elemento actual y total de elementos. |
| `current_title` | Título del elemento que se está descargando. |
| `item_percent` | Progreso del elemento actual (0–100). |
| `percent` | Progreso total. En listas se calcula combinando los elementos completados y `item_percent`. |
| `file_count` | Número de archivos finales localizados en la carpeta de destino. |
| `downloaded_bytes`, `total_bytes`, `speed`, `eta` | Se refieren al elemento actual cuando `playlist` es `true`. |

En una lista, yt-dlp emite una línea `ITEM|índice|total|título` antes de cada elemento y un `__FILE__...` por cada archivo terminado. Los archivos se nombran `001 - Título [id].ext`. La cancelación detiene todo el grupo de procesos y elimina los temporales de todos los elementos.

### `GET /api/downloads/{id}`

Devuelve el estado actual. Útil como respaldo del WebSocket.

### `POST /api/downloads/{id}/cancel`

Solicita la cancelación. Termina el grupo de procesos de yt-dlp, espera su cierre y elimina los archivos temporales. Devuelve el estado final (`cancelled`, o el que ya hubiera alcanzado).

### `WS /ws/downloads/{id}`

Requiere subprotocolos `["local-ytdlp", "<token>"]`. El servidor acepta con el subprotocolo `local-ytdlp` y envía un objeto JSON con el mismo esquema que `GET /api/downloads/{id}` cada vez que cambia el estado (máximo ~10 mensajes/s). El socket se cierra al alcanzar un estado final. Si el cliente no recibe mensajes durante 20 s, el servidor envía un estado actual.

## Sistema de archivos

### `GET /api/fs/roots`

Lista las raíces permitidas.

### `GET /api/fs/list?path=/ruta`

```json
{
  "path": "/home/usuario/Downloads",
  "parent": null,
  "directories": [{ "name": "Vídeos", "path": "/home/usuario/Downloads/Vídeos" }],
  "writable": true
}
```

Solo devuelve subcarpetas dentro de las raíces permitidas. Los symlinks que escapan del sandbox se ignoran.

### `POST /api/fs/mkdir`

```json
{ "path": "/home/usuario/Downloads", "name": "Nueva carpeta" }
```

Responde `201` con `{ "path": "...", "label": "Nueva carpeta" }`.

### `POST /api/open-folder`

```json
{ "path": "/home/usuario/Downloads" }
```

Abre la carpeta con el gestor de archivos del sistema. Respuesta: `{ "ok": true }`.

## Ejemplo con curl

```bash
TOKEN=$(curl -s http://127.0.0.1:8765/api/session | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

curl -s -H "X-API-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  http://127.0.0.1:8765/api/analyze
```
