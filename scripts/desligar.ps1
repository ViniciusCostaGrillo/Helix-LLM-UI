$target = $args[0]
if ($target -ne "Helix") {
    Write-Host "Uso incorreto. Digite: Desligar Helix" -ForegroundColor Red
    Exit 1
}

Write-Host "[Helix] Desligando os servicos do ecossistema..." -ForegroundColor Yellow

$ports = @(8000, 3000)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            Write-Host "[Helix] Parando processo na porta $port (PID: $procId)..."
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

$processes = Get-CimInstance Win32_Process -Filter "CommandLine like '%backend.knowledge.watchdog%' or CommandLine like '%backend.api.main%'" -ErrorAction SilentlyContinue
if ($processes) {
    foreach ($proc in $processes) {
        Write-Host "[Helix] Parando processo extra (PID: $($proc.ProcessId))..."
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Helix UI foi desligado completamente!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
