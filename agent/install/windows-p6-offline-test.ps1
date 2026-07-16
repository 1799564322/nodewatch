param(
    [int]$OfflineSeconds = 300,
    [string]$ProjectRoot = "D:\Claude\全栈项目"
)

$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "请右键 PowerShell，选择‘以管理员身份运行’"
}

$taskName = "NodeWatch Agent"
$agentLog = "C:\ProgramData\NodeWatch\logs\agent.log"
$backendDir = Join-Path $ProjectRoot "backend"
$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$composeFile = Join-Path $ProjectRoot "deploy\docker-compose.local.yml"
$testLogDir = Join-Path $ProjectRoot "logs"

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "找不到后端 Python：$backendPython"
}
if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "找不到 Docker Compose 文件：$composeFile"
}
if (-not (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
    throw "找不到计划任务：$taskName"
}

Write-Host "[1/6] 保持后端离线 $OfflineSeconds 秒，让 Agent 自动积累缓存。"
for ($remaining = $OfflineSeconds; $remaining -gt 0; $remaining -= 30) {
    Write-Host "      剩余 $remaining 秒"
    Start-Sleep -Seconds ([Math]::Min(30, $remaining))
}

Write-Host "[2/6] 检查开机计划任务。"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State | Format-Table
Get-ScheduledTaskInfo -TaskName $taskName |
    Select-Object LastRunTime, LastTaskResult |
    Format-Table

Write-Host "[3/6] 等待 Docker Desktop 引擎可用。"
$dockerReady = $false
for ($attempt = 1; $attempt -le 36; $attempt++) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    docker info *> $null
    $dockerExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($dockerExitCode -eq 0) {
        $dockerReady = $true
        break
    }
    if ($attempt -eq 1) {
        $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
        if (Test-Path -LiteralPath $dockerDesktop) {
            Write-Host "      Docker 尚未就绪，正在启动 Docker Desktop。"
            Start-Process -FilePath $dockerDesktop
        } else {
            Write-Host "      Docker 尚未就绪；请现在打开 Docker Desktop。"
        }
    }
    Start-Sleep -Seconds 5
}
if (-not $dockerReady) {
    throw "等待 3 分钟后 Docker 仍未就绪"
}

Write-Host "[4/6] 启动 PostgreSQL 和后端。"
docker compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL 启动失败"
}
New-Item -ItemType Directory -Force -Path $testLogDir | Out-Null
$backendProcess = Start-Process `
    -FilePath $backendPython `
    -ArgumentList @("-m", "uvicorn", "app.main:app") `
    -WorkingDirectory $backendDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $testLogDir "p6-backend.out.log") `
    -RedirectStandardError (Join-Path $testLogDir "p6-backend.err.log") `
    -PassThru
Write-Host "      后端进程 ID：$($backendProcess.Id)"

Write-Host "[5/6] 等待后端就绪，然后重启 Agent 立即触发补传。"
$backendReady = $false
for ($attempt = 1; $attempt -le 60; $attempt++) {
    try {
        $response = Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health/ready" -TimeoutSec 2
        if ($response.status -eq "ready") {
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $backendReady) {
    throw "后端在 2 分钟内没有就绪，请查看 $testLogDir\p6-backend.err.log"
}
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 20

Write-Host "[6/6] 显示补传结果。"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State | Format-Table
if (Test-Path -LiteralPath $agentLog) {
    Get-Content -LiteralPath $agentLog -Encoding utf8 -Tail 60
} else {
    throw "Agent 日志不存在：$agentLog"
}
Write-Host "测试结束：请确认日志中 queued 曾增加，最后出现批量上报且 remaining=0。"
