# One-command installer for Windows.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/Llop-Estepari/local-ytdlp/main/install.ps1 | iex"
#
# It downloads or updates the repository in %LOCALAPPDATA%\LocalYTDLP\app and
# runs installer\windows\install.ps1.

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoUrl = "https://github.com/Llop-Estepari/local-ytdlp.git"
$ArchiveUrl = "https://github.com/Llop-Estepari/local-ytdlp/archive/refs/heads/main.zip"
$Branch = "main"

function Write-Step($Message) {
    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
}

function Fail($Message) {
    Write-Host ""
    Write-Host "Error: $Message" -ForegroundColor Red
    exit 1
}

$InstallDir = if ($env:LOCAL_YTDLP_INSTALL_DIR) {
    $env:LOCAL_YTDLP_INSTALL_DIR
} else {
    Join-Path $env:LOCALAPPDATA "LocalYTDLP\app"
}

# Allow .\install.ps1 from a local checkout without cloning again.
$AppDir = $InstallDir
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "installer\windows\install.ps1"))) {
    $AppDir = $PSScriptRoot
}

function Install-Archive {
    $Temp = Join-Path ([IO.Path]::GetTempPath()) ("local-ytdlp-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $Temp -Force | Out-Null
    try {
        Write-Step "Descargando Local YT-DLP…"
        $Zip = Join-Path $Temp "repo.zip"
        Invoke-WebRequest -Uri $ArchiveUrl -OutFile $Zip -UseBasicParsing
        Expand-Archive -Path $Zip -DestinationPath $Temp -Force

        $Source = Get-ChildItem -Path $Temp -Directory |
            Where-Object { $_.Name -like "local-ytdlp-*" } |
            Select-Object -First 1
        if (-not $Source) {
            Fail "El archivo descargado no contiene el proyecto."
        }

        New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
        foreach ($Item in Get-ChildItem -Path $Source.FullName -Force) {
            Copy-Item -Path $Item.FullName -Destination $AppDir -Recurse -Force
        }
    } finally {
        Remove-Item -Path $Temp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($AppDir -eq $InstallDir) {
    if (Test-Path (Join-Path $AppDir ".git")) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Fail "La instalación existente usa git, pero git no está disponible."
        }
        Write-Step "Actualizando Local YT-DLP…"
        & git -C $AppDir pull --ff-only
        if ($LASTEXITCODE -ne 0) {
            Fail "No se pudo actualizar. Revisa los cambios locales en $AppDir."
        }
    } elseif ((Test-Path $AppDir) -and (Test-Path (Join-Path $AppDir "installer\windows\install.ps1"))) {
        Write-Step "Usando la instalación existente en $AppDir"
    } else {
        if ((Test-Path $AppDir) -and (Get-ChildItem -Path $AppDir -Force | Select-Object -First 1)) {
            Fail "La carpeta $AppDir existe pero no parece una instalación de Local YT-DLP."
        }

        if (Get-Command git -ErrorAction SilentlyContinue) {
            Write-Step "Descargando Local YT-DLP…"
            & git clone --depth 1 --branch $Branch $RepoUrl $AppDir
            if ($LASTEXITCODE -ne 0) {
                Remove-Item -Path $AppDir -Recurse -Force -ErrorAction SilentlyContinue
                Write-Step "git no pudo clonar el repositorio; usando la descarga directa…"
                Install-Archive
            }
        } else {
            Install-Archive
        }
    }
}

$Installer = Join-Path $AppDir "installer\windows\install.ps1"
if (-not (Test-Path $Installer)) {
    Fail "No se encontró el instalador de Windows en $Installer."
}

Write-Step "Iniciando la instalación para Windows…"
$env:LOCAL_YTDLP_NO_PAUSE = "1"
& powershell -NoProfile -ExecutionPolicy Bypass -File $Installer
$Code = $LASTEXITCODE
Remove-Item Env:\LOCAL_YTDLP_NO_PAUSE -ErrorAction SilentlyContinue
exit $Code
