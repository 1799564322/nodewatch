# 故障排查

## PowerShell 无法执行 npm

使用 `npm.cmd` 代替 `npm.ps1`，或在理解安全影响后调整当前用户的 PowerShell 执行策略。

## Docker 命令不存在

安装 Docker Desktop，启动后执行 `docker version` 和 `docker compose version` 验证。

