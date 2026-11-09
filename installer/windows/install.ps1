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
    if (-not $env:LOCAL_YTDLP_NO_PAUSE) {
        Read-Host "Pulsa Enter para cerrar"
    }
    exit 1
}

Write-Step "Vidora · instalación para Windows"

# --- Python -----------------------------------------------------------------
function Update-Path {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$MachinePath;$UserPath"
}

function Resolve-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Exe = "py"; Args = @("-3") }
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Exe = "python"; Args = @() }
        }
    }

    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"),
        (Join-Path $env:ProgramFiles "Python312\python.exe"),
        (Join-Path $env:ProgramFiles "Python313\python.exe"),
        (Join-Path $env:ProgramFiles "Python314\python.exe")
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path $Candidate) {
            return @{ Exe = $Candidate; Args = @() }
        }
    }
    return $null
}

$Python = Resolve-Python
if (-not $Python) {
    Update-Path
    $Python = Resolve-Python
}

if (-not $Python) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step "Instalando Python con winget (puede pedir permisos)…"
        & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Fail "No se pudo instalar Python automáticamente. Descárgalo desde https://www.python.org/downloads/ y marca «Add python.exe to PATH»."
        }
        Update-Path
        $Python = Resolve-Python
    }
}

if (-not $Python) {
    Fail "Python 3 no está disponible. Instálalo desde https://www.python.org/downloads/ y vuelve a ejecutar este instalador."
}

$PythonExe = $Python.Exe
$PythonArgs = @($Python.Args)

& $PythonExe @PythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Fail "Se requiere Python 3.10 o superior. Instala una versión reciente desde https://www.python.org/downloads/."
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

# --- Interfaz precompilada --------------------------------------------------
if (-not (Test-Path (Join-Path $Root "frontend\out\index.html"))) {
    Fail "Falta frontend\out\index.html. Ejecuta scripts/build-frontend.sh en el repositorio o vuelve a descargar la aplicación."
}

# --- FFmpeg -----------------------------------------------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step "Instalando FFmpeg con winget…"
        & winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Aviso: no se pudo instalar FFmpeg automáticamente." -ForegroundColor Yellow
        }
        Update-Path
    } else {
        Write-Host ""
        Write-Host "Aviso: FFmpeg no está instalado." -ForegroundColor Yellow
        Write-Host "Instálalo desde https://www.gyan.dev/ffmpeg/builds/ y añade la carpeta bin al PATH."
    }
}

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "FFmpeg detectado."
} else {
    Write-Host "Aviso: FFmpeg sigue sin estar disponible en el PATH." -ForegroundColor Yellow
}

# --- Ventana nativa (WebView2) ---------------------------------------------
$WebView2Keys = @(
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
)
$HasWebView2 = $false
foreach ($Key in $WebView2Keys) {
    if (Test-Path $Key) {
        $HasWebView2 = $true
        break
    }
}
if (-not $HasWebView2) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Step "Instalando Microsoft Edge WebView2 Runtime…"
        & winget install --id Microsoft.EdgeWebView2Runtime -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "Aviso: no se pudo instalar WebView2 automáticamente." -ForegroundColor Yellow
            Write-Host "Instálalo desde https://developer.microsoft.com/microsoft-edge/webview2/"
            Write-Host "Si no está disponible, la aplicación se abrirá en el navegador."
        }
    } else {
        Write-Host ""
        Write-Host "Aviso: no se detectó Microsoft Edge WebView2." -ForegroundColor Yellow
        Write-Host "La ventana nativa lo necesita. Instálalo desde:"
        Write-Host "  https://developer.microsoft.com/microsoft-edge/webview2/"
        Write-Host "Si no está disponible, la aplicación se abrirá en el navegador."
    }
}

# --- Lanzador ---------------------------------------------------------------
$StartBat = Join-Path $Root "Start Vidora.bat"
@"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
"@ | Set-Content -Path $StartBat -Encoding ASCII
Remove-Item -Path (Join-Path $Root "Start Local YT-DLP.bat") -Force -ErrorAction SilentlyContinue

$VenvPythonw = Join-Path $Root "backend\.venv\Scripts\pythonw.exe"
try {
    $Desktop = [Environment]::GetFolderPath("Desktop")
    if ($Desktop) {
        $Shell = New-Object -ComObject WScript.Shell
        $ShortcutPath = Join-Path $Desktop "Vidora.lnk"
        $Shortcut = $Shell.CreateShortcut($ShortcutPath)
        if (Test-Path $VenvPythonw) {
            $Shortcut.TargetPath = $VenvPythonw
            $Shortcut.Arguments = '"' + (Join-Path $Root "scripts\launch.py") + '"'
            $Shortcut.WindowStyle = 7
        } else {
            $Shortcut.TargetPath = $StartBat
        }
        $Shortcut.WorkingDirectory = $Root
        $IconPath = Join-Path $Root "assets\icon.ico"
        if (Test-Path $IconPath) {
            $Shortcut.IconLocation = $IconPath
        } else {
            $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,137"
        }
        $Shortcut.Description = "Vidora"
        $Shortcut.Save()
        Remove-Item -Path (Join-Path $Desktop "Local YT-DLP.lnk") -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "Aviso: no se pudo crear el acceso directo del escritorio." -ForegroundColor Yellow
}

Write-Step "Instalación completada"
Write-Host "Inicia la aplicación con el acceso directo «Vidora» del escritorio."
Write-Host "Para ver la consola de diagnóstico ejecuta:"
Write-Host "  $StartBat"
Write-Host ""
Write-Host "Si FFmpeg se acaba de instalar, cierra y vuelve a abrir la aplicación."
if (-not $env:LOCAL_YTDLP_NO_PAUSE) {
    Read-Host "Pulsa Enter para cerrar"
}
