# Local YT-DLP Downloader

Aplicación web local para descargar contenido multimedia con **yt-dlp** y **FFmpeg** ejecutados en tu propio ordenador. No hay servidores remotos: el vídeo o el audio nunca salen de tu equipo.

Una sola pantalla, una sola tarea: pegar una URL, elegir formato y calidad, descargar.

## Características

- Análisis real de la URL con yt-dlp y detección de título, miniatura, duración y plataforma.
- Listas de reproducción: título, número de elementos y vista previa de las canciones antes de descargar.
- Descarga completa de listas: añade todas las canciones a la cola con el formato y la calidad elegidos.
- Descarga individual desde una lista: el icono de cada canción abre un diálogo para elegir formato y calidad, y la añade a la cola.
- Vídeos o audios individuales: al analizar el enlace se abre el mismo diálogo automáticamente y la descarga se añade a la cola.
- Cola secuencial: puedes seguir añadiendo canciones mientras otra se descarga.
- Icono de cola en la cabecera con el número de canciones; su popup permite ver la lista, eliminar canciones y vaciar toda la cola con confirmación.
- El logo superior izquierdo vuelve al inicio sin detener la cola.
- Progreso de la cola en un toast en la parte superior central, sin abandonar la pantalla de la lista.
- Interfaz en español e inglés: detecta automáticamente el idioma del sistema (cualquier otro idioma usa inglés).
- Formatos: MP4, WebM, MP3, M4A y mejor formato disponible.
- Calidades reales: mejor, 2160p, 1440p, 1080p, 720p, 480p y 360p, solo si existen.
- Conversión de audio MP3 con FFmpeg (320, 256, 192 y 128 kbps).
- Progreso en tiempo real por WebSocket: porcentaje, velocidad, bytes y tiempo restante, con el elemento actual en las listas.
- Cancelación real del proceso de yt-dlp y de sus procesos hijos, también en listas.
- Nombres de archivo numerados (`001 - Título [id].ext`) para conservar el orden de la lista.
- Selección de carpeta de destino con sandbox de ubicaciones permitidas.
- Interfaz minimalista, modo oscuro por defecto y modo claro opcional.
- Comprobación de versiones y actualizaciones de yt-dlp y FFmpeg.
- Seguridad local: token de sesión, validación de Host/Origin, CSP, protección CSRF y DNS rebinding.

## Requisitos

| Componente | Versión | Uso |
| --- | --- | --- |
| Python | 3.10 o superior | Backend FastAPI |
| Node.js + npm | 20 o superior | Compilar la interfaz |
| FFmpeg | Versión reciente | Combinar pistas y convertir audio |
| yt-dlp | Se instala en el entorno virtual | Análisis y descargas |

El instalador comprueba estas dependencias, crea el entorno de Python, instala yt-dlp y compila el frontend.

## Instalación

### Linux

```bash
git clone <repositorio> local-yt-dlp
cd local-yt-dlp
./installer/linux/install.sh
```

El instalador crea un lanzador en el menú de aplicaciones y el comando `local-ytdlp`.

### macOS

```bash
cd local-yt-dlp
./installer/macos/install.sh
```

Crea `~/Applications/Local YT-DLP.command`. Si macOS bloquea la primera apertura, haz clic derecho sobre el archivo y elige **Abrir**.

### Windows

```powershell
cd local-yt-dlp
.\installer\windows\install.ps1
```

También puedes hacer doble clic en `installer\windows\install.bat`. El instalador crea el acceso directo **Local YT-DLP** en el escritorio.

## Uso

1. Abre la aplicación (se abre el navegador automáticamente en `http://127.0.0.1:8765`).
2. Pega la URL de un vídeo, audio o lista de reproducción.
3. Pulsa **Analizar**.
   - Si es un vídeo o audio individual, se abre el diálogo de formato y calidad; al confirmar, la descarga se añade a la cola.
   - Si es una lista, elige formato y calidad y pulsa **Añadir lista a la cola (N)** para encolar todas las canciones, o usa el icono de una canción para añadir solo esa.
4. Elige la carpeta de destino y confirma.
5. El progreso aparece en el toast superior. El icono de cola, a la izquierda del botón de tema, muestra cuántas canciones quedan; al pulsarlo puedes verlas, eliminar canciones o vaciar la cola con confirmación.
6. Al terminar, usa **Abrir carpeta** en el toast o inicia otra descarga. El logo superior izquierdo vuelve al inicio sin detener la cola.

En una lista, la aplicación descarga todos sus elementos y muestra el progreso del elemento actual y el porcentaje total. Los archivos se guardan con un prefijo numérico para mantener el orden. Cada fila de la vista previa tiene un icono de descarga que abre un diálogo para elegir formato y calidad; al confirmar, la canción se añade a una cola y su progreso aparece en un toast superior. Puedes añadir más canciones mientras otra se descarga. Las listas vacías, privadas o con elementos no disponibles se rechazan con un mensaje claro.

Si pegas un enlace de vídeo que incluye el parámetro `list=` de YouTube, se analizará la lista completa; elimina ese parámetro si solo quieres descargar ese vídeo.

### Idioma

La interfaz detecta el idioma del sistema al abrirla: usa español si el navegador está configurado en español y, para cualquier otro idioma, usa inglés. No hace falta configurar nada; el atributo `lang` del documento se actualiza automáticamente.

### Lanzadores manuales

| Sistema | Comando |
| --- | --- |
| Linux / macOS | `./scripts/run.sh` |
| macOS (doble clic) | `run.command` |
| Windows (PowerShell) | `.\run.ps1` |
| Windows (doble clic) | `Start Local YT-DLP.bat` |

## Desarrollo

Requisitos: Python 3.10+, Node.js 20+ y FFmpeg en el `PATH`.

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q

# Frontend
cd ../frontend
npm install
npm run dev        # http://127.0.0.1:3000

# O ambos a la vez, desde la raíz
./scripts/dev.sh
```

Pruebas de integración reales (usan la red y descargan contenido):

```bash
cd backend
RUN_INTEGRATION=1 .venv/bin/pytest -q tests/test_integration.py -vv
```

Compilación de producción:

```bash
cd frontend
npm run typecheck
npm test
npm run build      # genera frontend/out
```

El backend sirve `frontend/out` en un único origen. En desarrollo, Next.js usa `http://127.0.0.1:8765` como API.

## Seguridad

- El servicio escucha en `127.0.0.1` por defecto.
- La API exige el token local en la cabecera `X-API-Token`. El token se obtiene en `GET /api/session`, solo para clientes loopback.
- Se validan `Host`, `Origin` y `Sec-Fetch-Site`; se aplica CSP y cabeceras de seguridad.
- Las carpetas de destino están limitadas a Descargas, Vídeos, Música y Escritorio (más `LOCAL_YTDLP_ALLOWED_ROOTS`). Se resuelven symlinks y se rechazan escapes.
- Solo se aceptan URLs HTTP(S) públicas: se rechazan `file://`, loopback, redes privadas y credenciales.
- yt-dlp se ejecuta con `asyncio.create_subprocess_exec` y argumentos separados. Nunca se usa una shell.
- Los archivos parciales se guardan en una carpeta temporal por descarga y se eliminan al terminar o cancelar.

### Acceso desde la red local (opcional)

Desactivado por defecto. Para habilitarlo de forma explícita:

```bash
export LOCAL_YTDLP_ALLOW_NETWORK=1
export LOCAL_YTDLP_TOKEN="un-token-largo-y-aleatorio-de-32-caracteres"
./scripts/run.sh
```

Abre en el otro dispositivo `http://IP-DEL-EQUIPO:8765/#token=TU_TOKEN`. El token se guarda en `sessionStorage` y se elimina de la barra de direcciones. No expongas el puerto a Internet.

## Configuración

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `LOCAL_YTDLP_HOST` | `127.0.0.1` | Interfaz de escucha |
| `LOCAL_YTDLP_PORT` | `8765` | Puerto local |
| `LOCAL_YTDLP_DATA_DIR` | Directorio de estado del sistema | Token, logs y temporales |
| `LOCAL_YTDLP_ALLOWED_ROOTS` | Descargas, Vídeos, Música, Escritorio | Carpetas de destino permitidas, separadas por `:` (`;` en Windows) |
| `LOCAL_YTDLP_TOKEN` | Generado y guardado | Token local (mínimo 24 caracteres) |
| `LOCAL_YTDLP_ALLOW_NETWORK` | `0` | Habilita el modo red |
| `LOCAL_YTDLP_ALLOWED_ORIGINS` | Orígenes locales | Orígenes adicionales permitidos, separados por comas |
| `LOCAL_YTDLP_TRUSTED_HOSTS` | Hosts locales | Hosts permitidos, separados por comas |
| `LOCAL_YTDLP_FRONTEND_DIR` | `frontend/out` | Carpeta del frontend compilado |
| `LOCAL_YTDLP_YTDLP_PATH` | Autodetectado | Ruta a un ejecutable de yt-dlp |
| `LOCAL_YTDLP_FFMPEG_PATH` | Autodetectado | Ruta a un ejecutable de FFmpeg |

Los logs se guardan en `<DATA_DIR>/logs/app.log`.

## Estructura

```
backend/            FastAPI, servicios, seguridad y pruebas
frontend/           Next.js, React, TypeScript y Tailwind
scripts/            Lanzadores y desarrollo
installer/          Instaladores de Linux, macOS y Windows
docs/               API, arquitectura e instalación
```

## Documentación

- [Instalación y solución de problemas](docs/INSTALL.md)
- [Referencia de la API](docs/API.md)
- [Arquitectura](docs/ARCHITECTURE.md)

## Licencia

Uso personal. Respeta los términos de servicio de las plataformas y los derechos de autor del contenido que descargues.
