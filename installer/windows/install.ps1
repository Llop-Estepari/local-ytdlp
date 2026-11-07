$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

function Write-Step($Message) {
    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
}

function Fail($Message) {
    Write-Host ""
    Write-Host "Error: $Message" -ForegroundColor Red
    Read-Host "Pulsa Enter para cerrar"
    exit 1
}

Write-Step "Local YT-DLP Downloader · instalación para Windows"

# --- Python -----------------------------------------------------------------
$PythonExe = $null
$PythonArgs = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonExe = "py"
        $PythonArgs = @("-3")
    }
}

if (-not $PythonExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonExe = "python"
    }
}

if (-not $PythonExe) {
    Fail "Python 3 no está instalado. Descárgalo desde https://www.python.org/downloads/ y marca «Add python.exe to PATH»."
}

& $PythonExe @PythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Fail "Se requiere Python 3.10 o superior."
}

$VenvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Step "Creando entorno virtual de Python…"
    & $PythonExe @PythonArgs -m venv (Join-Path $Root "backend\.venv")
    if ($LASTEXITCODE -ne 0) {
        Fail "No se pudo crear el entorno virtual."
    }
}

Write-Step "Instalando dependencias de Python (FastAPI, yt-dlp)…"
& $VenvPython -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { Fail "No se pudo actualizar pip." }
& $VenvPython -m pip install -r (Join-Path $Root "backend\requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { Fail "No se pudieron instalar las dependencias de Python." }

# --- Node / frontend --------------------------------------------------------
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Fail "Node.js y npm son necesarios para compilar la interfaz. Instala Node.js 20 o superior."
}

$NodeMajor = [int](& node -p "process.versions.node.split('.')[0]")
if ($NodeMajor -lt 20) {
    Fail "Se requiere Node.js 20 o superior (detectado $(& node --version))."
}

Write-Step "Compilando la interfaz web…"
Push-Location (Join-Path $Root "frontend")
try {
    if (Test-Path "package-lock.json") {
        & npm ci --no-audit --no-fund
    } else {
        & npm install --no-audit --no-fund
    }
    if ($LASTEXITCODE -ne 0) { Fail "No se pudieron instalar las dependencias del frontend." }
    & npm run build
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo compilar la interfaz." }
} finally {
    Pop-Location
}

# --- FFmpeg -----------------------------------------------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step "Instalando FFmpeg con winget…"
        & winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Aviso: no se pudo instalar FFmpeg automáticamente." -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "Aviso: FFmpeg no está instalado." -ForegroundColor Yellow
        Write-Host "Instálalo desde https://www.gyan.dev/ffmpeg/builds/ y añade la carpeta bin al PATH."
    }
} else {
    Write-Host "FFmpeg detectado."
}

# --- Lanzador ---------------------------------------------------------------
$StartBat = Join-Path $Root "Start Local YT-DLP.bat"
@"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
"@ | Set-Content -Path $StartBat -Encoding ASCII

try {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    if ($Desktop) {
        $Shell = New-Object -ComObject WScript.Shell
        $Shortcut = $Shell.CreateShortcut((Join-Path $Desktop "Local YT-DLP.lnk"))
        $Shortcut.TargetPath = $StartBat
        $Shortcut.WorkingDirectory = $Root
        $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,137"
        $Shortcut.Description = "Local YT-DLP Downloader"
        $Shortcut.Save()
    }
} catch {
    Write-Host "Aviso: no se pudo crear el acceso directo del escritorio." -ForegroundColor Yellow
}

Write-Step "Instalación completada"
Write-Host "Inicia la aplicación con el acceso directo «Local YT-DLP» o ejecutando:"
Write-Host "  $StartBat"
Write-Host ""
Write-Host "Si FFmpeg se acaba de instalar, cierra y vuelve a abrir la aplicación."
Read-Host "Pulsa Enter para cerrar"
