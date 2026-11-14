Set-Location (Join-Path $PSScriptRoot "..")
docker compose down
Write-Host "Kanban backend stopped."
