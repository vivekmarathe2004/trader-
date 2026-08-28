# ==============================================================================
#   VALEXIS QUANT - UNIFIED PLATFORM CONTROLLER (Single Window)
#   Autonomous Quantitative Scanner & Multi-Broker Trading Matrix
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "VALEXIS QUANT - Unified Terminal Controller"

$scriptDir = $PSScriptRoot

function Clean-LingeringPorts {
    foreach ($port in @(8000, 3000)) {
        try {
            $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if ($connections) {
                foreach ($conn in $connections) {
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {}
    }
}

Clean-LingeringPorts

Clear-Host
Write-Host ""
Write-Host "   ================================================================" -ForegroundColor DarkYellow
Write-Host "             VALEXIS QUANT - AUTONOMOUS TRADING TERMINAL           " -ForegroundColor Yellow
Write-Host "       Deterministic Math | Hardened Risk | Multi-Broker Engine    " -ForegroundColor White
Write-Host "   ================================================================" -ForegroundColor DarkYellow
Write-Host ""

$nowIst = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + " IST"
Write-Host "  [+] System Time:      $nowIst" -ForegroundColor Cyan
Write-Host "  [+] Core Engine:      FastAPI v1 Gateway (Port 8000)" -ForegroundColor Gray
Write-Host "  [+] Web Terminal:     Next.js 14 Cockpit (Port 3000)" -ForegroundColor Gray
Write-Host "  [+] Window Mode:      100% Unified (Single Window Console)" -ForegroundColor Green
Write-Host ""
Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  [1/2] Launching Backend Daemon (Port 8000)..." -ForegroundColor Cyan

# Start Backend quietly in background (hidden window)
$backendProc = Start-Process python -ArgumentList "-m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WorkingDirectory "$scriptDir/backend" -WindowStyle Hidden -PassThru

Write-Host "        -> Backend PID: $($backendProc.Id) (Starting...)" -ForegroundColor Green

# Wait for backend readiness
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($resp -and $resp.status -eq "ONLINE") {
            $ready = $true
            break
        }
    } catch {}
    Start-Sleep -Milliseconds 400
}

if ($ready) {
    Write-Host "        -> Backend API Gateway: ONLINE (http://127.0.0.1:8000)" -ForegroundColor Green
} else {
    Write-Host "        -> Backend starting in background..." -ForegroundColor Yellow
}

Write-Host "  [2/2] Launching Frontend Web Terminal (Port 3000)..." -ForegroundColor Cyan

# Start Frontend quietly in background (hidden window)
$frontendProc = Start-Process cmd -ArgumentList "/c npm run dev" -WorkingDirectory "$scriptDir/frontend" -WindowStyle Hidden -PassThru

Write-Host "        -> Frontend PID: $($frontendProc.Id) (Online)" -ForegroundColor Green
Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

Start-Sleep -Seconds 1
# Auto open browser
Start-Process "http://localhost:3000"

Write-Host "  ================================================================" -ForegroundColor DarkYellow
Write-Host "   LIVE PLATFORM ACCESS & SERVICES:                               " -ForegroundColor Yellow
Write-Host "   - Web Cockpit:        http://localhost:3000                    " -ForegroundColor White
Write-Host "   - AutoTrader Matrix:  http://localhost:3000/operations/auto-trade" -ForegroundColor Cyan
Write-Host "   - Swagger API Docs:   http://localhost:8000/docs               " -ForegroundColor Gray
Write-Host "   - WebSocket Stream:   ws://localhost:8000/ws/events            " -ForegroundColor Green
Write-Host "  ================================================================" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  [i] All services are running inside this single controller window." -ForegroundColor Yellow
Write-Host "  [!] Press [Q] or [Ctrl+C] to stop all services and exit..." -ForegroundColor Magenta
Write-Host ""

try {
    while ($true) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq [ConsoleKey]::Q -or $key.Key -eq [ConsoleKey]::Escape) {
                break
            }
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "`n  [*] Shutting down platform services..." -ForegroundColor Yellow
    if ($backendProc -and !$backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProc -and !$frontendProc.HasExited) {
        Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
    }
    Clean-LingeringPorts
    Write-Host "  [+] All background services stopped cleanly. Goodbye!`n" -ForegroundColor Green
}
