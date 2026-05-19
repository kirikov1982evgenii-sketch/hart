# Публикация API и бота на Render (один раз)
$ErrorActionPreference = "Stop"
$repo = "https://github.com/kirikov1982evgenii-sketch/klub-znaniy-hart"
$blueprint = "https://dashboard.render.com/blueprint/new?repo=$([uri]::EscapeDataString($repo))"
$secretsFile = Join-Path $env:USERPROFILE "Desktop\DEPLOY-HART-Render.txt"
if (-not (Test-Path $secretsFile)) {
    $alt = Get-ChildItem (Join-Path $env:USERPROFILE "Desktop") -Filter "*Render*.txt" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($alt) { $secretsFile = $alt.FullName }
}

Write-Host ""
Write-Host "=== Публикация API (Render) ===" -ForegroundColor Cyan
Write-Host "1. Откроется Render Blueprint — нажмите Apply"
Write-Host "2. Вставьте переменные из файла на рабочем столе"
Write-Host "3. Дождитесь статуса Live у hart-payments и hart-telegram-bot"
Write-Host ""

if (Test-Path $secretsFile) { Start-Process notepad.exe $secretsFile }
$yb = "$env:LOCALAPPDATA\Yandex\YandexBrowser\Application\browser.exe"
if (Test-Path $yb) { Start-Process $yb $blueprint } else { Start-Process $blueprint }

Write-Host "Blueprint:" $blueprint
