param(
    [switch]$Live = $true,
    [switch]$Blocking = $true,
    [string]$BackendUrl = "http://localhost:8000"
)

# Build query parameters
$liveFlag = if ($Live) { 1 } else { 0 }
$blockingFlag = if ($Blocking) { 1 } else { 0 }

$url = "$BackendUrl/scan/run?live=$liveFlag&blocking=$blockingFlag"

Write-Host "Starting scan..." -ForegroundColor Cyan
Write-Host "  Mode: $(if ($Blocking) { 'Blocking (synchronous)' } else { 'Queued (async)' })" -ForegroundColor Gray
Write-Host "  Live: $(if ($Live) { 'Yes' } else { 'No (fixtures)' })" -ForegroundColor Gray
Write-Host "  URL: $url" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -Method POST -TimeoutSec 60 -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json

    Write-Host "✓ Scan initiated successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    $data | ConvertTo-Json | Write-Host

    if ($Blocking -and $data.total) {
        Write-Host ""
        Write-Host "Summary:" -ForegroundColor Yellow
        Write-Host "  Total scanned: $($data.total)" -ForegroundColor Gray
        Write-Host "  New listings:  $($data.new)" -ForegroundColor Gray
        Write-Host "  Updated:       $($data.updated)" -ForegroundColor Gray
        Write-Host "  Skipped:       $($data.skipped)" -ForegroundColor Gray
    }
    elseif ($data.task_id) {
        Write-Host ""
        Write-Host "Task queued with ID: $($data.task_id)" -ForegroundColor Yellow
        Write-Host "Monitor progress with: docker compose logs -f worker" -ForegroundColor Gray
    }

    Write-Host ""
    exit 0
}
catch {
    Write-Host "✗ Scan failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check backend is running: docker compose logs backend" -ForegroundColor Gray
    Write-Host "  2. Verify /health endpoint: curl http://localhost:8000/health" -ForegroundColor Gray
    Write-Host "  3. Check Celery worker: docker compose logs worker" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
