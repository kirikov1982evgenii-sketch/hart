# Временный публичный API (пока Render не Live). ПК должен быть включён.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    $cfPath = "$env:ProgramFiles\cloudflared\cloudflared.exe"
    if (Test-Path $cfPath) { $cf = $cfPath } else { throw "Установите cloudflared: winget install Cloudflare.cloudflared" }
}

$env:PYTHONIOENCODING = "utf-8"
Remove-Item Env:DEV_LOCAL -ErrorAction SilentlyContinue
$env:BIND_HOST = "127.0.0.1"
$env:PAYMENT_API_PORT = "8766"

Write-Host "Запуск API на :8766..." -ForegroundColor Cyan
$api = Start-Process python -ArgumentList "payment_server.py" -PassThru -WindowStyle Hidden -WorkingDirectory $root

Start-Sleep -Seconds 2
Write-Host "Туннель Cloudflare..." -ForegroundColor Cyan
$log = Join-Path $env:TEMP "hart-cloudflared.log"
Remove-Item $log -ErrorAction SilentlyContinue
$tunnel = Start-Process cmd.exe -ArgumentList "/c","`"$($cf.Source)`" tunnel --url http://127.0.0.1:8766 > `"$log`" 2>&1" -PassThru -WindowStyle Hidden

$url = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $log) {
        $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
        if ($m) { $url = $m.Matches[0].Value; break }
    }
}

Write-Host ""
if ($url) {
    Write-Host "Публичный API:" $url -ForegroundColor Green
    Write-Host "Health:" "$url/api/health"
    $url | Set-Content (Join-Path $root "data\public_api_url.txt")
} else {
    Write-Host "URL туннеля не найден. Смотрите $log"
}
Write-Host "Остановка: закройте окна или Stop-Process -Id $($api.Id),$($tunnel.Id)"
