# Instalación y solución de problemas

## Requisitos

- Python 3.10 o superior.
- Node.js 20 o superior y npm (solo para compilar la interfaz).
- FFmpeg disponible en el `PATH`.
- Conexión a Internet para descargar el contenido y comprobar actualizaciones.

yt-dlp se instala dentro de `backend/.venv`, por lo que no es necesario instalarlo globalmente.

## Instalación manual

```bash
# 1. Entorno de Python
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Interfaz
cd ../frontend
npm install
npm run build

# 3. Inicio
cd ..
./scripts/run.sh
```

En Windows:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..\frontend
npm install
npm run build

cd ..
.\run.ps1
```

## Instaladores

### Linux

`installer/linux/install.sh`:

- Comprueba Python 3.10+ y Node.js 20+.
- Crea `backend/.venv` e instala FastAPI y yt-dlp.
- Ejecuta `npm ci` y `npm run build`.
- Detecta FFmpeg y muestra el comando de instalación si falta.
- Crea `~/.local/bin/local-ytdlp` y `~/.local/share/applications/local-ytdlp.desktop`.

### macOS

`installer/macos/install.sh`:

- Comprueba Python 3.10+ y Node.js 20+.
- Crea el entorno e instala dependencias.
- Compila la interfaz.
- Instala FFmpeg con Homebrew si está disponible; si no, muestra instrucciones.
- Crea `~/Applications/Local YT-DLP.command`.

### Windows

`installer/windows/install.ps1` (o `install.bat`):

- Busca `py -3` o `python`.
- Crea `backend\.venv` e instala dependencias.
- Compila la interfaz con npm.
- Instala FFmpeg con winget si falta y winget está disponible.
- Crea `Start Local YT-DLP.bat` y un acceso directo en el escritorio.

## Solución de problemas

### «El frontend no está compilado»

Ejecuta:

```bash
cd frontend
npm install
npm run build
```

### «El puerto 8765 está ocupado»

Cierra el programa que lo usa o inicia en otro puerto:

```bash
LOCAL_YTDLP_PORT=9000 ./scripts/run.sh
```

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

Recarga la página. El frontend solicita un token nuevo a `GET /api/session`. En modo red, comprueba que la URL incluye `#token=...` con el token configurado.

### No se puede abrir la carpeta

La aplicación usa `xdg-open`/`gio` en Linux, `open` en macOS y el explorador de Windows. Si no hay gestor de archivos disponible, abre la ruta manualmente.

### La descarga se cancela o falla al procesar

Revisa `<DATA_DIR>/logs/app.log`. Las causas habituales son falta de espacio, permisos de escritura o FFmpeg ausente.

## Actualizar

```bash
# Dependencias de Python (incluye yt-dlp)
backend/.venv/bin/pip install --upgrade -r backend/requirements.txt

# Interfaz
cd frontend
npm install
npm run build
```

También puedes usar el botón **Comprobar** del pie de la aplicación para consultar las últimas versiones publicadas.

## Desinstalar

- Linux: elimina `~/.local/bin/local-ytdlp`, `~/.local/share/applications/local-ytdlp.desktop` y la carpeta del proyecto.
- macOS: elimina `~/Applications/Local YT-DLP.command` y la carpeta del proyecto.
- Windows: elimina el acceso directo del escritorio, `Start Local YT-DLP.bat` y la carpeta del proyecto.

Los datos locales (token, logs y temporales) están en:

| Sistema | Ruta |
| --- | --- |
| Linux | `~/.local/state/local-ytdlp` |
| macOS | `~/Library/Application Support/LocalYTDLP` |
| Windows | `%LOCALAPPDATA%\LocalYTDLP` |
