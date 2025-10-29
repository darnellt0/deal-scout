param(
    [string]$Service = "backend",
    [string]$Match = "scan|health|error"
)

# Tail logs from Docker Compose service, filtering for keywords (case-insensitive)
Write-Host "Tailing $Service logs (filtering for: $Match)" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

docker compose logs -f $Service | Select-String -Pattern "(?i)$Match"
