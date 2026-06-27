$target = $args[0]
if ($target -ne "Helix") {
    Write-Host "Uso incorreto. Digite: Ligar Helix" -ForegroundColor Red
    Exit 1
}

# Garante que o script roda no diretorio raiz do projeto
Set-Location -Path "c:\Users\Vinic\UI IA BUILDER"

Write-Host "[Helix] Iniciando o backend da API..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"c:\Users\Vinic\UI IA BUILDER`" && set DATABASE_URL=sqlite:///./test.db&& set PYTHONPATH=.&& .venv\Scripts\python.exe -m uvicorn backend.api.main:app --port 8000" -WindowStyle Minimized

Write-Host "[Helix] Iniciando o Watchdog de conhecimento..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"c:\Users\Vinic\UI IA BUILDER`" && set DATABASE_URL=sqlite:///./test.db&& set PYTHONPATH=.&& .venv\Scripts\python.exe scripts\run_watchdog.py" -WindowStyle Minimized

Write-Host "[Helix] Aguardando o backend estar totalmente pronto..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe scripts\wait_for_port.py 8000

Write-Host "[Helix] Iniciando o frontend Next.js..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"c:\Users\Vinic\UI IA BUILDER\frontend`" && npm run dev" -WindowStyle Minimized

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Helix UI foi iniciado em segundo plano!" -ForegroundColor Green
Write-Host "API rodando em: http://localhost:8000" -ForegroundColor Green
Write-Host "Interface rodando em: http://localhost:3000" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
