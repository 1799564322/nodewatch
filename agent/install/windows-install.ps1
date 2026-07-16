param(
    [Parameter(Mandatory = $true)][string]$BinaryPath,
    [Parameter(Mandatory = $true)][string]$ServerUrl,
    [Parameter(Mandatory = $true)][string]$AgentToken,
    [string]$InstallDir = "$env:ProgramData\NodeWatch"
)

$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "请右键 PowerShell，选择‘以管理员身份运行’"
}
if (-not (Test-Path -LiteralPath $BinaryPath)) {
    throw "找不到 Agent 文件：$BinaryPath"
}
if (-not $AgentToken.StartsWith("nwa_")) {
    throw "Agent Token 格式无效"
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$target = Join-Path $InstallDir "nodewatch-agent.exe"
$existingTask = Get-ScheduledTask -TaskName "NodeWatch Agent" -ErrorAction SilentlyContinue
if ($existingTask) {
    Stop-ScheduledTask -TaskName "NodeWatch Agent" -ErrorAction SilentlyContinue
}
Copy-Item -LiteralPath $BinaryPath -Destination $target -Force
$config = @"
server_url = "$ServerUrl"
agent_token = "$AgentToken"
collect_interval_seconds = 60
request_timeout_seconds = 10
verify_tls = true
log_level = "INFO"
cache_max_samples = 10000
cache_retention_days = 7
max_batch_samples = 500
retry_max_seconds = 300
log_max_bytes = 5242880
log_backup_count = 3
"@
$configPath = Join-Path $InstallDir "config.toml"
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($configPath, $config, $utf8WithoutBom)
$action = '"' + $target + '" --config "' + $configPath + '"'
schtasks.exe /Create /TN "NodeWatch Agent" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR $action /F | Out-Null
schtasks.exe /Run /TN "NodeWatch Agent" | Out-Null
Write-Host "NodeWatch Agent 已安装并启动。安装目录：$InstallDir"
