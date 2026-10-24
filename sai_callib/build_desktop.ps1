# Builds the desktop app (no console, no .py source files shipped) and its installer:
#   dist\SAI_Calibration\SAI_Calibration.exe   the app folder (opens in a few seconds)
#   dist\SAI_Calibration_Setup.exe             single file to give to customers
#
# Usage (from the sai_callib folder):
#   .\build_desktop.ps1
#   .\build_desktop.ps1 -Python C:\Users\user\OneDrive\Desktop\myenv\Scripts\python.exe

param(
    [string]$Python = "C:\Users\user\OneDrive\Desktop\myenv\Scripts\python.exe",
    [string]$InnoSetup = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
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
if (Get-Process SAI_Calibration -ErrorAction SilentlyContinue) {
    throw "Close the running SAI Calibration app first."
}

Write-Host "Collecting static files..."
& $Python manage.py collectstatic --noinput --clear | Out-Null
if ($LASTEXITCODE -ne 0) { throw "collectstatic failed" }

Write-Host "Building app..."
# The old single-file exe took 20-60 s to start because it unpacked itself on every launch
Remove-Item dist\SAI_Calibration.exe -ErrorAction SilentlyContinue
# PyInstaller logs progress on stderr; rely on its exit code instead
$ErrorActionPreference = "Continue"
& $Python -m PyInstaller --noconfirm --clean --onedir --windowed `
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

Write-Host "Building installer..."
if (-not (Test-Path $InnoSetup)) { throw "Inno Setup not found at $InnoSetup" }
& $InnoSetup /Q installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }
$ErrorActionPreference = "Stop"

$setup = Get-Item dist\SAI_Calibration_Setup.exe
Write-Host ("Done: {0} ({1:N0} MB) - give this file to customers" -f $setup.FullName, ($setup.Length / 1MB))
