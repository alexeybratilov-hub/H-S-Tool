[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [ValidateSet("minimal", "lock")]
    [string]$RequirementsMode = "minimal"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location -LiteralPath $root

Write-Host "Portable setup started."
Write-Host "Root: $root"

try {
    & $PythonExe --version
} catch {
    Write-Error "Python interpreter not found: $PythonExe. Install Python or pass -PythonExe to a portable Python executable."
    exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $root ".venv"))) {
    Write-Host "Creating virtual environment..."
    & $PythonExe -m venv (Join-Path $root ".venv")
}

$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path -LiteralPath $activate)) {
    Write-Error "Virtual environment activation script not found: $activate"
    exit 1
}

. $activate

python -m pip install --upgrade pip setuptools wheel

$reqFile = if ($RequirementsMode -eq "lock") {
    Join-Path $root "07_PROJECT_DOCS\requirements-lock.txt"
} else {
    Join-Path $root "07_PROJECT_DOCS\requirements-minimal.txt"
}

if (-not (Test-Path -LiteralPath $reqFile)) {
    Write-Error "Requirements file not found: $reqFile"
    exit 1
}

Write-Host "Installing requirements from: $reqFile"
python -m pip install -r $reqFile

Write-Host ""
Write-Host "Portable setup completed."
Write-Host "Run application with:"
Write-Host "powershell -ExecutionPolicy Bypass -File .\run_portable.ps1"