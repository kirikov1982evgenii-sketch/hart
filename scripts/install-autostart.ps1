# Автозапуск API + бота при входе в Windows (без Render)
$root = Split-Path $PSScriptRoot -Parent
$bat = Join-Path $root "start-site.bat"
$taskName = "HartKnowledgeClub"

$action = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Автозапуск: $taskName -> $bat" -ForegroundColor Green
