# Instalación y solución de problemas

## Requisitos

- Python 3.10 o superior.
- FFmpeg disponible en el `PATH`.
- Una WebView del sistema para la ventana nativa:
  - Linux: PyGObject y WebKitGTK 4.1.
  - Windows: Microsoft Edge WebView2.
  - macOS: WKWebView (incluido en el sistema).
- Conexión a Internet para descargar el contenido y comprobar actualizaciones.

**Node.js y npm no son necesarios para instalar ni usar la aplicación.** La interfaz compilada se distribuye en `frontend/out`. Solo se necesitan para modificar el frontend.

Los instaladores intentan instalar automáticamente Python, FFmpeg y la WebView del sistema cuando faltan. Pueden pedir la contraseña de administrador o permisos de winget.

yt-dlp y pywebview se instalan dentro de `backend/.venv`, por lo que no es necesario instalarlos globalmente.

## Instalación con un solo comando

El instalador descarga o actualiza el proyecto en una carpeta estándar y ejecuta el instalador de la plataforma.

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

Carpetas por defecto:

| Sistema | Ruta |
| --- | --- |
| Linux | `~/.local/share/local-ytdlp` |
| macOS | `~/Library/Application Support/local-ytdlp` |
| Windows | `%LOCALAPPDATA%\LocalYTDLP\app` |

Para cambiar la carpeta en Linux o macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.sh | LOCAL_YTDLP_INSTALL_DIR="$HOME/apps/local-ytdlp" bash
```

En Windows:

```powershell
$env:LOCAL_YTDLP_INSTALL_DIR="$env:USERPROFILE\apps\local-ytdlp"; irm https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.ps1 | iex
```

## Instalación manual

```bash
# 1. Entorno de Python
cd backend
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

# 2. Inicio en ventana nativa
cd ..
./scripts/run.sh
```

`--system-site-packages` permite que la ventana nativa use PyGObject y WebKitGTK instalados por el sistema. En macOS y Windows no es necesario, pero tampoco molesta.

En Windows:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..
.\run.ps1
```

Para usar el navegador en lugar de la ventana nativa, añade `--browser` al lanzador.

## Instaladores

### Linux

`installer/linux/install.sh`:

- Detecta `apt`, `dnf`, `pacman` o `zypper` e instala Python 3.10+, `venv`, PyGObject, WebKitGTK 4.1 y FFmpeg si faltan.
- Crea `backend/.venv` con acceso a los paquetes del sistema e instala FastAPI, pywebview y yt-dlp.
- Usa la interfaz precompilada de `frontend/out`; no necesita Node.js ni npm.
- Crea `~/.local/bin/local-ytdlp` y `~/.local/share/applications/local-ytdlp.desktop`.

### macOS

`installer/macos/install.sh`:

- Comprueba Python 3.10+; si falta, instala Homebrew y Python automáticamente.
- Crea el entorno e instala las dependencias de Python.
- Usa la interfaz precompilada de `frontend/out`; no necesita Node.js ni npm.
- Instala FFmpeg con Homebrew si falta.
- Crea la aplicación `~/Applications/Local YT-DLP.app` con su `Info.plist` y su lanzador.

### Windows

`installer/windows/install.ps1` (o `install.bat`):

- Busca `py -3` o `python`; si falta o es anterior a 3.10, instala Python con winget.
- Crea `backend\.venv` e instala las dependencias de Python.
- Usa la interfaz precompilada de `frontend\out`; no necesita Node.js ni npm.
- Instala FFmpeg y Microsoft Edge WebView2 con winget si faltan.
- Crea `Start Local YT-DLP.bat` para diagnóstico y un acceso directo en el escritorio que abre la ventana sin consola.

## Solución de problemas

### La aplicación se abre en el navegador en lugar de la ventana

Falta la WebView del sistema o pywebview no puede cargarla.

- Linux: instala PyGObject y WebKitGTK:

  ```bash
  # Debian / Ubuntu
  sudo apt install python3-gi gir1.2-webkit2-4.1

  # Fedora
  sudo dnf install python3-gobject webkit2gtk4.1

  # Arch Linux
  sudo pacman -S python-gobject webkit2gtk-4.1

  # openSUSE
  sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1
  ```

  Vuelve a ejecutar el instalador para recrear el entorno con acceso a los paquetes del sistema.

- Windows: instala Microsoft Edge WebView2 desde <https://developer.microsoft.com/microsoft-edge/webview2/>.
- macOS: usa una versión reciente de macOS; WKWebView viene incluido.

También puedes revisar el motivo con:

```bash
./scripts/run.sh --debug
```

### La ventana nativa aparece en blanco o congelada (Linux)

Algunos controladores gráficos tienen problemas con la composición de WebKitGTK. Prueba a desactivarla:

```bash
WEBKIT_DISABLE_COMPOSITING_MODE=1 ./scripts/run.sh
```

Si el problema continúa, usa temporalmente el modo navegador con `--browser`.

### La ventana no se abre en Windows

El acceso directo usa `pythonw.exe` y no muestra errores. Ejecuta `Start Local YT-DLP.bat` para ver la consola de diagnóstico o revisa `<DATA_DIR>\logs\app.log`. Comprueba también que Microsoft Edge WebView2 esté instalado.

### «El frontend no está compilado»

`frontend/out` debería venir incluido en el repositorio. Si falta, vuelve a descargar la aplicación o, si eres mantenedor y tienes Node.js instalado:

```bash
./scripts/build-frontend.sh
```

### «El puerto 8765 está ocupado»

Cierra el programa que lo usa o inicia en otro puerto:

```bash
LOCAL_YTDLP_PORT=9000 ./scripts/run.sh
```

En modo escritorio el puerto solo se usa internamente.

### FFmpeg no está instalado

- Debian/Ubuntu: `sudo apt install ffmpeg`
- Fedora: `sudo dnf install ffmpeg`
- Arch: `sudo pacman -S ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: `winget install Gyan.FFmpeg` o descarga desde <https://www.gyan.dev/ffmpeg/builds/>

Después de instalarlo, cierra y vuelve a abrir la aplicación.

### yt-dlp no está instalado

```bash
cd backend
.venv/bin/pip install -r requirements.txt
```

En Windows, usa `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### YouTube pide verificación o inicio de sesión

La aplicación solo admite contenido público. Si YouTube muestra un control anti-bots, prueba más tarde, usa otra URL pública o actualiza yt-dlp:

```bash
backend/.venv/bin/pip install --upgrade yt-dlp
```

### La lista de reproducción aparece vacía o sin formatos

La aplicación solo admite listas públicas. Comprueba que el enlace sea el de la lista completa y que sus primeros elementos estén disponibles: se analizan hasta tres para detectar formatos reales. Si un elemento falla a mitad de la descarga, los archivos ya completados se conservan en la carpeta de destino y se muestra el error con el número de archivos descargados.

### El token no es válido o la sesión caduca

Cierra y vuelve a abrir la aplicación. El frontend solicita un token nuevo a `GET /api/session`. En modo red, comprueba que la URL incluye `#token=...` con el token configurado.

### No se puede abrir la carpeta

La aplicación usa `xdg-open`/`gio` en Linux, `open` en macOS y el explorador de Windows. Si no hay gestor de archivos disponible, abre la ruta manualmente.

### La descarga se cancela o falla al procesar

Revisa `<DATA_DIR>/logs/app.log`. Las causas habituales son falta de espacio, permisos de escritura o FFmpeg ausente.

## Actualizar

```bash
git pull

# Dependencias de Python (incluye yt-dlp y pywebview)
backend/.venv/bin/pip install --upgrade -r backend/requirements.txt
```

La interfaz compilada se actualiza con `git pull`; no hace falta Node.js. Solo los mantenedores deben regenerar `frontend/out` con `./scripts/build-frontend.sh` después de cambiar el frontend.

También puedes usar el botón **Comprobar** del pie de la aplicación para consultar las últimas versiones publicadas.

## Desinstalar

- Linux: elimina `~/.local/bin/local-ytdlp`, `~/.local/share/applications/local-ytdlp.desktop` y la carpeta del proyecto.
- macOS: elimina `~/Applications/Local YT-DLP.app` y la carpeta del proyecto.
- Windows: elimina el acceso directo del escritorio, `Start Local YT-DLP.bat` y la carpeta del proyecto.

Los datos locales (token, logs, temporales y almacenamiento de la ventana) están en:

| Sistema | Ruta |
| --- | --- |
| Linux | `~/.local/state/local-ytdlp` |
| macOS | `~/Library/Application Support/LocalYTDLP` |
| Windows | `%LOCALAPPDATA%\LocalYTDLP` |
