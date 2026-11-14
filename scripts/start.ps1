Set-Location (Join-Path $PSScriptRoot "..")
docker compose up --build -d
Write-Host "Kanban backend is starting on http://localhost:8000"
