$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "No se encontró el entorno de Python de la aplicación." -ForegroundColor Red
    Write-Host "Ejecuta primero el instalador: installer\windows\install.ps1"
    Read-Host "Pulsa Enter para cerrar"
    exit 1
}

& $Python (Join-Path $Root "scripts\launch.py") @args
if ($LASTEXITCODE -ne 0) {
    Read-Host "Pulsa Enter para cerrar"
    exit $LASTEXITCODE
}
