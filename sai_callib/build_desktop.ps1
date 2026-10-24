# Builds dist\SAI_Calibration.exe (single file, no console, no .py source files shipped).
#
# Usage (from the sai_callib folder):
#   .\build_desktop.ps1
#   .\build_desktop.ps1 -Python C:\Users\user\OneDrive\Desktop\myenv\Scripts\python.exe

param(
    [string]$Python = "C:\Users\user\OneDrive\Desktop\myenv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Build against the local SQLite settings, never the online database
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:DEBUG -ErrorAction SilentlyContinue
$env:DJANGO_SETTINGS_MODULE = "sai_calibrations.settings"

if (Select-String -Path licensing.py -Pattern "^PUBLIC_KEY = ''" -Quiet) {
    throw "No licence key set up yet. Run once: $Python license_tool.py init"
}

Write-Host "Collecting static files..."
& $Python manage.py collectstatic --noinput --clear | Out-Null
if ($LASTEXITCODE -ne 0) { throw "collectstatic failed" }

Write-Host "Building exe..."
# PyInstaller logs progress on stderr; rely on its exit code instead
$ErrorActionPreference = "Continue"
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name SAI_Calibration `
    --icon app/static/images/sai.ico `
    --add-data "app/templates;app/templates" `
    --add-data "staticfiles;staticfiles" `
    --collect-submodules app `
    --collect-submodules sai_calibrations `
    --collect-submodules whitenoise `
    --exclude-module tkinter `
    desktop_app.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
$ErrorActionPreference = "Stop"

$exe = Get-Item dist\SAI_Calibration.exe
Write-Host ("Done: {0} ({1:N0} MB)" -f $exe.FullName, ($exe.Length / 1MB))
