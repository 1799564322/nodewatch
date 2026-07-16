param(
    [string]$InstallDir = "$env:ProgramData\NodeWatch",
    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "请右键 PowerShell，选择‘以管理员身份运行’"
}
$existingTask = Get-ScheduledTask -TaskName "NodeWatch Agent" -ErrorAction SilentlyContinue
if ($existingTask) {
    Stop-ScheduledTask -TaskName "NodeWatch Agent" -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "NodeWatch Agent" -Confirm:$false
}
if ($RemoveData -and (Test-Path -LiteralPath $InstallDir)) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
    Write-Host "计划任务和本地数据已删除"
} else {
    Write-Host "计划任务已删除；配置、身份、缓存和日志保留在：$InstallDir"
}
