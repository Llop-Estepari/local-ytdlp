# Arquitectura de Vidora

## Visión general

```
┌─────────────────────────────────────┐        ┌──────────────────────────────────┐
│  Ventana nativa (pywebview)         │        │  FastAPI (127.0.0.1:8765)        │
│  WebKitGTK / WebView2 / WKWebView   │        │                                  │
│                                     │  REST  │  /api/*        rutas y modelos   │
│  Next.js (export estático)          │◄──────►│  /ws/downloads WebSocket         │
│  React + TypeScript                 │        │                                  │
│  Tailwind + shadcn/ui               │        │  DownloadManager                 │
└─────────────────────────────────────┘        │    ├─ YtDlpService               │
                                               │    ├─ FileSystemService          │
                                               │    ├─ ToolsService               │
                                               │    └─ UpdateChecker              │
                                               └──────────────┬───────────────────┘
                                                              │ subprocess (sin shell)
                                                              ▼
                                               ┌──────────────────────────────────┐
                                               │  yt-dlp  ──►  FFmpeg             │
                                               │  (proceso aislado por descarga)  │
                                               └──────────────────────────────────┘
```

En la aplicación de escritorio, `app/desktop.py` inicia uvicorn en un hilo y abre una ventana nativa que carga `http://127.0.0.1:8765`. FastAPI sirve `frontend/out` en el mismo origen que la API, así que no hay CORS y se mantienen las validaciones de origen y token. En desarrollo, Next.js corre en `:3000` y la API en `:8765`; el modo `--browser` conserva el comportamiento de navegador.

## Estructura del repositorio

```
install.sh             Instalador de un solo comando (Linux/macOS)
install.ps1            Instalador de un solo comando (Windows)
backend/
  app/
    main.py            Punto de entrada ASGI
    __main__.py        python -m app (ventana, navegador o solo servidor)
    desktop.py         Ventana nativa, servidor en segundo plano y fallback
    factory.py         Creación de la app, middleware, estáticos, errores
    api/routes.py      Endpoints REST y WebSocket
    core/
      config.py        Settings, rutas, token, hosts y orígenes
      context.py       Contenedor de servicios
      errors.py        Errores de aplicación con mensajes seguros
      logging.py       Log rotativo local
      process.py       Subprocess, grupos de procesos y terminación
      security.py      Token, Origin, Host y subprotocolo WebSocket
      urls.py          Validación de URLs públicas (anti-SSRF)
    models/schemas.py  Modelos Pydantic de entrada y salida
    services/
      downloader.py    Ciclo de vida, progreso, cancelación y limpieza
      formats.py       Detección de formatos y calidades reales
      fs.py            Sandbox de carpetas y apertura del explorador
      progress.py      Parser de la plantilla de progreso de yt-dlp
      tools.py         Detección y actualización de yt-dlp y FFmpeg
      updates.py       Comprobación de versiones publicadas
      ytdlp.py         Comandos de análisis y descarga
  tests/               Unitarias + integración real
assets/                Iconos de la aplicación (PNG, ICO e ICNS)
frontend/
  out/                 Interfaz compilada versionada (instalación sin Node.js)
  app/                 Layout, página, estilos y metadatos
  components/          Pantalla única y estados progresivos
                       (playlist-panel, download-toast, download-options-dialog,
                       queue-dialog, i18n-provider…)
  components/ui/       Primitivas shadcn/ui (button, select, progress, dialog)
  hooks/               Progreso por WebSocket con polling de respaldo
  lib/                 Cliente API, i18n (es/en), etiquetas, formateadores y errores
  types/               Contratos TypeScript de la API
scripts/               Lanzador, desarrollo y utilidades
installer/             Instaladores por plataforma
docs/                  API, arquitectura e instalación
```

## Flujo de una descarga

1. El frontend obtiene el token con `GET /api/session` y carga `/api/config` y `/api/dependencies`.
2. `POST /api/analyze` valida la URL y ejecuta `yt-dlp -J --flat-playlist`. Si el resultado es una lista, se realiza una segunda extracción completa de hasta tres elementos (`--playlist-items 1-3`) para detectar formatos reales. `formats.py` construye `MediaInfo` o `PlaylistInfo`.
3. El usuario elige formato, calidad y carpeta. Un vídeo o audio individual abre automáticamente el diálogo de opciones al analizarlo y se añade a la cola (`playlist_item` nulo). Las canciones de una lista usan el mismo diálogo desde su icono (`playlist_item: N`). El botón **Añadir lista a la cola** encola todos los elementos de la lista (`playlist_item: N` y `numbered: true` para conservar el orden en el nombre del archivo).
4. El backend valida la selección, resuelve la carpeta dentro del sandbox y crea un `_Record` con un id UUID.
5. `DownloadManager` lanza `asyncio.create_subprocess_exec` con un grupo de procesos propio. Las descargas de lista usan `--yes-playlist`; las individuales, `--no-playlist`; una canción concreta usa `--yes-playlist --playlist-items N` y la plantilla de archivo individual.
6. yt-dlp escribe líneas `PROGRESS|...`, líneas `ITEM|índice|total|título` antes de cada elemento de una lista y una marca `__FILE__...` al mover cada archivo final. El parser actualiza el estado y lo publica a los suscriptores.
7. El frontend recibe el estado por WebSocket; si el socket falla, consulta el endpoint REST cada 1,5 s.
8. Al terminar, `_finish` localiza los archivos, marca `completed` y elimina la carpeta temporal. Si se cancela, se termina el grupo de procesos y se limpian los parciales de todos los elementos.

### Cola de canciones

Todas las descargas (un vídeo/audio suelto, una canción de una lista o una lista completa) pasan por una cola en memoria con concurrencia 1:

- El diálogo de opciones elige formato y calidad y añade un elemento a la cola. En un enlace individual se abre automáticamente al terminar el análisis; en una lista se abre desde el icono de cada fila.
- **Añadir lista a la cola** crea un elemento por cada canción, con su índice y el formato/calidad seleccionados. Las claves son deterministas (`playlist:<url>:<índice>`), así que volver a pulsar no duplica canciones ya encoladas.
- Un efecto inicia el primer elemento con `POST /api/downloads` (`playlist_item` nulo para un enlace individual o `N` para una canción de lista).
- El progreso se muestra en `DownloadToast`, fijo arriba en el centro, con porcentaje, velocidad, bytes, ETA y número de canciones en cola.
- Al terminar o fallar, se muestra un aviso temporal y se inicia el siguiente elemento.
- Cancelar detiene la descarga activa; la siguiente de la cola comienza automáticamente.
- El icono de cola de la cabecera (a la izquierda del tema) muestra el número total de canciones. `QueueDialog` permite ver la activa y las pendientes, quitar canciones y vaciar la cola con confirmación; vaciar cancela también la descarga activa.
- El logo de la cabecera vuelve al inicio sin detener la cola; se puede pegar otro enlace mientras el toast sigue activo.

## Modo escritorio

- `scripts/launch.py` carga `Settings`, comprueba que `frontend/out/index.html` exista y llama a `app.desktop.run_desktop`.
- `run_desktop` reutiliza una instancia ya en ejecución (`GET /api/health`); si no la hay, inicia uvicorn en un hilo daemon y espera a que `server.started` sea verdadero.
- `pywebview` crea una ventana nativa con `private_mode=False` y `storage_path=<DATA_DIR>/webview`, de modo que el tema y las preferencias persisten entre sesiones.
- Al cerrar la ventana, el hilo del servidor recibe `should_exit`, se ejecuta el apagado ordenado de `DownloadManager` y se eliminan los temporales.
- Si `pywebview` no está instalado, falla la WebView del sistema o el usuario pasa `--browser`, se sirve la misma interfaz y se abre el navegador por defecto.
- `python -m app --server` permite ejecutar solo el servicio HTTP para depuración o despliegues headless.

## Selección de formatos

La detección se basa en los metadatos reales de yt-dlp:

- Solo se consideran formatos de vídeo con `vcodec` distinto de `none`, `height > 0` y extensión válida.
- Las alturas se agrupan en 2160, 1440, 1080, 720, 480 y 360 con una tolerancia del 5 % (mínimo 24 px).
- MP4 y WebM solo aparecen si existe al menos un formato de vídeo de esa extensión.
- MP3 y M4A aparecen si hay audio o vídeo del que extraerlo.
- «Mejor formato» usa `bv*+ba/b`.
- MP3 usa `-x --audio-format mp3 --audio-quality <bitrate>K`; M4A usa `-x --audio-format m4a`.
- En listas, las opciones se derivan de los tres primeros elementos disponibles y se aplican a todos. Si un vídeo no alcanza la calidad elegida, el selector `height<=H` toma la mejor disponible.

Comandos de descarga:

| Formato | Selector | Postproceso |
| --- | --- | --- |
| MP4 | `bv*[height<=H][ext=mp4]+ba[ext=m4a]/bv*[height<=H]+ba/b[height<=H]` | `--merge-output-format mp4 --remux-video mp4` |
| WebM | `bv*[height<=H][ext=webm]+ba[ext=webm]/bv*[height<=H][ext=webm]+ba` | `--merge-output-format webm` |
| MP3 | `ba/b` | `-x --audio-format mp3` |
| M4A | `ba[ext=m4a]/ba/b` | `-x --audio-format m4a` |
| Best | `bv*+ba/b` | — |

Todas las descargas usan `--ignore-config`, `--windows-filenames`, `--trim-filenames 180`, `--paths home:<destino> --paths temp:<id>` y una plantilla de salida controlada. Las individuales añaden `--no-playlist`; las listas añaden `--yes-playlist`, `--print before_dl:ITEM|...` y la plantilla `%(playlist_index)03d - %(title).160B [%(id)s].%(ext)s`; una canción concreta añade `--yes-playlist --playlist-items N` y usa la plantilla individual sin prefijo. Los archivos parciales se escriben en la carpeta temporal, no en la carpeta final.

## Progreso y cancelación

- La plantilla `PROGRESS|status|downloaded|total|estimate|speed|eta|percent` se parsea en `progress.py`.
- Las líneas `ITEM|índice|total|título` marcan el inicio de cada elemento de una lista.
- El total usa `total_bytes` y, si falta, `total_bytes_estimate`.
- El porcentaje se calcula con los bytes; si no hay total, se usa el porcentaje de yt-dlp.
- En listas, `percent` es el progreso global `((índice-1) + item_percent/100) / total * 100`; `item_percent`, bytes, velocidad y ETA se refieren al elemento actual. Si yt-dlp no informa del total, se usa `playlist_count` del análisis.
- Cada `__FILE__...` añade un archivo al conjunto de resultados (`file_count`).
- Los eventos se emiten como máximo cada 100 ms por descarga (`_publish`), con una cola de tamaño 1 por suscriptor para no acumular estados obsoletos.
- `cancel()` marca `cancel_requested`, termina el grupo de procesos (`killpg` en POSIX, `taskkill /T /F` en Windows), espera y limpia.
- En el apagado, `shutdown()` termina procesos y elimina temporales.

## Seguridad

### Red

- `127.0.0.1` por defecto; el modo red es explícito y exige token.
- `TrustedHostMiddleware` + comprobación de `Origin`/`Sec-Fetch-Site`.
- El bootstrap del token solo se entrega a clientes loopback.
- CSP con `connect-src` limitado a los orígenes locales (o `ws:`/`wss:` en modo red).
- Sin `allow_credentials` en CORS; solo se permiten métodos y cabeceras necesarios.

### Procesos

- `asyncio.create_subprocess_exec` con listas de argumentos; nunca `shell=True`.
- Grupo de procesos propio para poder cancelar también los hijos de FFmpeg.
- Entorno con `NO_COLOR=1` y UTF-8.
- Timeouts en análisis, comprobación de versiones y terminación.

### Archivos

- Raíces permitidas: Descargas, Vídeos, Música y Escritorio (XDG en Linux) más `LOCAL_YTDLP_ALLOWED_ROOTS`.
- `resolve()` antes de comparar; se rechazan symlinks que salen del sandbox.
- Nombres de carpeta validados (caracteres prohibidos y nombres reservados de Windows).
- La apertura de carpetas usa el gestor del sistema, nunca comandos construidos con entrada del usuario.

### URLs

- Solo HTTP(S), sin credenciales ni caracteres de control.
- Se rechazan hosts locales, `.local`, `.internal`, `.home.arpa`, `.lan`, loopback, link-local y rangos privados.
- Se resuelve DNS y se comprueban todas las direcciones antes de invocar yt-dlp.

## Frontend

- Next.js con `output: "export"`; la app es una sola página.
- `Downloader` mantiene la máquina de estados: `idle`, `analyzing`, `ready`, `downloading`, `completed`, `error`.
- El resultado del análisis se discrimina por `kind`: un vídeo o audio individual abre `DownloadOptionsDialog` automáticamente y, al confirmar, se añade a la cola; una lista muestra `PlaylistPanel` con vista previa, formato de audio por defecto, botón para encolar toda la lista e icono de descarga individual por fila.
- El icono de cada canción abre el mismo `DownloadOptionsDialog`; al confirmar, la canción entra en la cola y el progreso aparece en `DownloadToast`.
- `QueueDialog` muestra la descarga activa y las pendientes, permite eliminarlas y vaciar la cola mediante una vista de confirmación. El icono de la cabecera muestra el total y está a la izquierda del tema.
- El botón del logo en la cabecera vuelve al inicio (`idle`) sin detener la cola: las descargas pendientes siguen avanzando en el toast.
- `I18nProvider` detecta `navigator.languages` y elige español si el idioma preferido empieza por `es`; en cualquier otro caso usa inglés. Actualiza `document.documentElement.lang` y traduce todos los textos de la interfaz con `lib/i18n.ts`.
- Los mensajes conocidos del backend (español) se traducen en el cliente con `lib/api-messages.ts`; los detalles dinámicos no reconocidos se muestran tal cual.
- El estado se revela progresivamente; no hay sidebar, historial ni reproductor.
- El token se mantiene en memoria y `sessionStorage`; se elimina del hash de la URL.
- `useDownloadProgress` combina WebSocket y polling; cierra el socket en estados finales.
- Tailwind v4 con variables CSS y modo oscuro por clase; el tema se aplica antes de la hidratación.

## Pruebas

- Unitarias del backend: formatos, listas, progreso, comandos de descarga, URLs, sandbox, seguridad, API, versiones.
- Integración real: análisis de YouTube, descarga completa con WebSocket y cancelación de un subproceso en curso.
- Frontend: pruebas de formateadores, preferencia de formato en listas y validación local con Vitest.
- Verificación E2E automatizada del flujo completo en navegador, incluida una lista real, la cola de canciones y las interfaces en español e inglés.

## Decisiones y límites

- Se admiten listas de reproducción públicas; no se admite contenido privado ni que requiera inicio de sesión.
- La vista previa de una lista se limita a 50 elementos y los formatos se detectan con una muestra de hasta 3 elementos; el resto se procesa igual durante la descarga.
- La interfaz admite español e inglés y detecta el idioma del sistema; no hay selector manual.
- La cola de canciones vive en la interfaz con concurrencia 1 y no se conserva al cerrar la aplicación.
- No se usa una base de datos: el estado vive en memoria y los archivos en disco.
- Las descargas simultáneas están aisladas por id y carpeta temporal.
- El historial no se conserva al cerrar el servicio.
- El pie muestra la versión de Vidora y las de yt-dlp/FFmpeg. La comprobación de actualizaciones no modifica instalaciones por sí sola: el usuario decide qué herramienta actualizar desde el pie de la aplicación.
