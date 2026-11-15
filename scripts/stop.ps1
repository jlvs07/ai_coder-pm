$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose --profile e2e down --remove-orphans
Write-Host "Kanban backend stopped."
