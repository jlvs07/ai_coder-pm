$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose up --build -d --wait
Write-Host "Kanban backend is running on http://localhost:8000"
