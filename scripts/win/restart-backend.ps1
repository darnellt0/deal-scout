param(
    [switch]$Logs = $true,
    [int]$TailLines = 50
)

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan
Write-Host "Restarting Backend Service" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

try {
    Write-Host "Restarting container 'backend'..." -ForegroundColor Gray
    docker compose restart backend

    Write-Host "✓ Backend container restarted." -ForegroundColor Green
    Write-Host ""

    if ($Logs) {
        Write-Host "Fetching last $TailLines lines of logs..." -ForegroundColor Gray
        Write-Host ""
        docker compose logs --tail=$TailLines backend
    }

    Write-Host ""
    Write-Host "Checking health status..." -ForegroundColor Gray
    Start-Sleep -Seconds 2

    try {
        $response = curl.exe -s http://localhost:8000/health | ConvertFrom-Json
        if ($response.ok) {
            Write-Host "✓ Backend is healthy" -ForegroundColor Green
            Write-Host "  DB:    $($response.db)" -ForegroundColor Gray
            Write-Host "  Redis: $($response.redis)" -ForegroundColor Gray
            Write-Host "  Queue: $($response.queue_depth) pending tasks" -ForegroundColor Gray
        } else {
            Write-Host "⚠ Backend is running but reports degraded status" -ForegroundColor Yellow
            $response | ConvertTo-Json | Write-Host
        }
    } catch {
        Write-Host "⚠ Health check endpoint not yet ready; backend still starting" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Done. Backend is being restarted." -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "✗ Error restarting backend" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    exit 1
}
