# Открыть мастер деплоя Render (Blueprint из GitHub)
$repo = "https://github.com/kirikov1982evgenii-sketch/-"
$url = "https://dashboard.render.com/blueprint/new?repo=$([uri]::EscapeDataString($repo))"
$yb = "$env:LOCALAPPDATA\Yandex\YandexBrowser\Application\browser.exe"
if (Test-Path $yb) { Start-Process $yb $url } else { Start-Process $url }
Write-Host "Render Blueprint:" $url
