[CmdletBinding()]
param(
    [string]$TargetDir = ""
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location -LiteralPath $root

if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    $TargetDir = Join-Path $root "00_SYS\backups"
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$db = Join-Path $root "00_SYS\ot_local_agent.sqlite"

if (-not (Test-Path -LiteralPath $db)) {
    Write-Error "Database not found: $db"
    exit 1
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$target = Join-Path $TargetDir "ot_local_agent_$stamp.sqlite"

Copy-Item -LiteralPath $db -Destination $target

Write-Host "Database backup created:"
Write-Host $target