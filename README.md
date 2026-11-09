# Vidora

Aplicación de escritorio local para descargar vídeo y audio con **yt-dlp** y **FFmpeg**. Todo se ejecuta en tu ordenador: no hay servidores remotos.

La interfaz se muestra en una ventana nativa en Linux, Windows y macOS. También incluye un modo navegador opcional con `--browser`.

## Características

- Análisis de vídeos, audios y listas de reproducción.
- Formatos MP4, WebM, MP3, M4A y mejor formato disponible.
- Calidades desde 360p hasta 2160p, solo si existen.
- Cola de descargas con progreso en tiempo real, cancelación y descarga de listas completas.
- Selección de carpeta de destino con ubicaciones permitidas.
- Interfaz en español e inglés, modo oscuro y modo claro.
- Iconos animados y marca SVG que se adapta al tema.
- Versión de la aplicación visible y comprobación de versiones de Vidora, yt-dlp y FFmpeg, con actualización de las herramientas desde la propia interfaz.

## Instalación con un solo comando

El instalador descarga o actualiza la aplicación, instala las dependencias que falten y crea el lanzador de escritorio. Puede pedir la contraseña de administrador.

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.sh | bash
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.sh | bash
```

### Windows

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.ps1 | iex"
```

Si no tienes `curl` en Linux:

```bash
wget -qO- https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.sh | bash
```

### Carpetas de instalación

| Sistema | Ruta por defecto |
| --- | --- |
| Linux | `~/.local/share/vidora` |
| macOS | `~/Library/Application Support/Vidora` |
| Windows | `%LOCALAPPDATA%\Vidora\app` |

Puedes usar otra carpeta con `LOCAL_YTDLP_INSTALL_DIR`.

## Uso

1. Abre **Vidora** desde el menú de aplicaciones, Launchpad o el acceso directo del escritorio.
2. Pega la URL de un vídeo, audio o lista de reproducción.
3. Pulsa **Analizar** y elige formato, calidad y carpeta.
4. La descarga se añade a la cola y muestra el progreso en la parte superior.

## Requisitos

- Python 3.10 o superior.
- FFmpeg.
- WebView del sistema:
  - Linux: PyGObject y WebKitGTK 4.1.
  - Windows: Microsoft Edge WebView2.
  - macOS: WKWebView, incluido en el sistema.

Los instaladores intentan instalar automáticamente lo que falte. **Node.js y npm no son necesarios para instalar ni usar Vidora**; solo para desarrollo.

## Desarrollo

Requisitos: Python 3.10+, Node.js 20+ y FFmpeg.

```bash
# Backend
cd backend
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q

# Interfaz
cd ../frontend
npm install
npm run dev        # http://127.0.0.1:3000

# Backend + interfaz
./scripts/dev.sh
```

Para probar la ventana nativa con el frontend compilado:

```bash
./scripts/build-frontend.sh
./scripts/run.sh --debug
```

`frontend/out` se versiona en el repositorio para que los usuarios finales no necesiten Node.js. Si cambias el frontend, regenera `frontend/out` y haz commit de los cambios.

## Documentación

- [Instalación y solución de problemas](docs/INSTALL.md)
- [Referencia de la API](docs/API.md)
- [Arquitectura](docs/ARCHITECTURE.md)

## Licencia

Uso personal. Respeta los términos de servicio de las plataformas y los derechos de autor del contenido que descargues.
