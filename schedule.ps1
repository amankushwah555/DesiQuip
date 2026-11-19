# Registers the daily DesiQuip schedule in Windows Task Scheduler (spec section 9).
#   09:00          growth      yesterday's analytics, comment replies, new learnings
#   14:00          run-daily   Trend finder -> 2 jobs -> produce -> approval request -> summary
#   every 10 min   approvals   publish what was approved (Telegram buttons or CLI)
#
# Run once from the repo root:   powershell -ExecutionPolicy Bypass -File .\schedule.ps1
# Remove the tasks again:        powershell -ExecutionPolicy Bypass -File .\schedule.ps1 -Remove
# The laptop must be on (and logged in) at these times. Logs go to logs\desiquip.log.

param([switch]$Remove)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Tasks = @(
    @{ Name = "DesiQuip Growth";    Args = "-m desiquip growth";    Trigger = New-ScheduledTaskTrigger -Daily -At "09:00" },
    @{ Name = "DesiQuip Daily Run"; Args = "-m desiquip run-daily"; Trigger = New-ScheduledTaskTrigger -Daily -At "14:00" },
    @{ Name = "DesiQuip Approvals"; Args = "-m desiquip approvals"
       Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 10) }
)

foreach ($t in $Tasks) {
    Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue
    if ($Remove) { Write-Host "Removed $($t.Name)"; continue }
    $action = New-ScheduledTaskAction -Execute $Py -Argument $t.Args -WorkingDirectory $Root
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger $t.Trigger -Settings $settings `
        -Description "DesiQuip: python $($t.Args)" | Out-Null
    Write-Host "Scheduled $($t.Name): python $($t.Args)" -ForegroundColor Green
}
if (-not $Remove) { Write-Host "`n'StartWhenAvailable' runs a missed task as soon as the laptop wakes up." }
