$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location -LiteralPath $root

$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path -LiteralPath $activate)) {
    Write-Error "Virtual environment not found. Run setup_portable.ps1 first."
    exit 1
}

. $activate

$app = Join-Path $root "app.py"

if (-not (Test-Path -LiteralPath $app)) {
    Write-Error "app.py not found."
    exit 1
}

Write-Host "Starting OT Local Agent on http://127.0.0.1:8501"
python -m streamlit run $app --server.address 127.0.0.1 --server.port 8501 --server.headless true