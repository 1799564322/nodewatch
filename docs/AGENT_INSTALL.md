# Agent 安装、升级与卸载

NodeWatch Agent 支持 Windows x86-64 和 Linux x86-64。发布包是 PyInstaller 生成的独立可执行文件，目标机器不需要安装 Python。

## 1. 下载并校验

从 GitHub Actions 的 `agent-package` 任务下载与系统匹配的 Artifact 并解压。发布包中包含 Agent、安装与卸载脚本、示例配置及 `.sha256` 文件。

Windows PowerShell 校验：

```powershell
(Get-FileHash .\nodewatch-agent.exe -Algorithm SHA256).Hash.ToLower()
Get-Content .\nodewatch-agent.exe.sha256
```

Linux 校验：

```bash
sha256sum -c nodewatch-agent.sha256
```

两边显示的哈希必须一致。校验失败时不要运行文件，请重新下载。

## 2. 准备 Agent Token

登录 NodeWatch 网页，在“设备”页创建设备并复制只显示一次的 Token。Token 以 `nwa_` 开头，不要把它发给别人或提交到 Git。

## 3. Windows 安装

以管理员身份打开 PowerShell，进入解压目录：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\windows-install.ps1 `
  -BinaryPath ".\nodewatch-agent.exe" `
  -ServerUrl "https://你的公网IP" `
  -AgentToken "nwa_替换为真实Token"
```

脚本会把文件安装到 `C:\ProgramData\NodeWatch`，创建名为 `NodeWatch Agent` 的开机计划任务并立即启动。

重复运行安装脚本可以覆盖升级：脚本会停止并注销旧计划任务，结束仍占用程序文件的旧 Agent 进程，再替换可执行文件和重建任务。`state` 中的身份与离线缓存会保留，连接恢复后继续补传。

检查运行状态和日志：

```powershell
Get-ScheduledTask -TaskName "NodeWatch Agent"
Get-Content "C:\ProgramData\NodeWatch\logs\agent.log" -Encoding utf8 -Tail 30
```

重启电脑后再次执行以上命令。计划任务状态应为 `Running`，日志应出现成功上报记录。

## 4. Linux 安装

```bash
chmod +x linux-install.sh linux-uninstall.sh nodewatch-agent
sudo ./linux-install.sh ./nodewatch-agent "https://你的公网IP" "nwa_替换为真实Token"
```

检查服务和日志：

```bash
systemctl status nodewatch-agent --no-pager
journalctl -u nodewatch-agent -n 30 --no-pager
```

服务程序安装在 `/opt/nodewatch`，配置、身份、SQLite 缓存及轮转日志保存在 `/var/lib/nodewatch`。

## 5. 断网补传验证

1. 保持 Agent 正常运行，确认网页有最新指标。
2. 断开目标机器网络 5～10 分钟，不要停止 Agent。
3. 查看日志，应出现“无法连接服务端”和逐渐变长的重试间隔。
4. SQLite 缓存位于 `state/metrics.db`，断网期间样本数量会增加。
5. 恢复网络，日志应出现“批量上报”，`remaining` 最终变成 `0`。
6. 网页历史曲线应按原采集时间补齐；旧样本不会覆盖最新值或触发实时阈值告警。

Windows 本地开发环境也可以在重启后使用一键验收脚本。后端保持关闭，以管理员身份执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "D:\Claude\全栈项目\agent\install\windows-p6-offline-test.ps1"
```

脚本会等待 5 分钟、检查计划任务、启动本地 PostgreSQL 与后端、重启 Agent 并打印补传日志。

默认最多缓存 10000 条、保留 7 天，达到上限时删除最旧样本，因此不会无限增长。SQLite 使用 WAL 和完整同步；进程被强制结束后，重启时会由 SQLite 自动恢复未完成事务。

## 6. 常见错误

- `HTTP 401/403/409`：Token 无效、失效或绑定了其他 Agent。Agent 会等待 300 秒再请求，不会每秒刷服务端。
- TLS 校验失败：生产环境应修复公网 IP 证书。只有本地调试时才能把 `verify_tls` 改为 `false`。
- Windows 任务未运行：确认安装时使用了管理员 PowerShell，并查看 `logs/agent.log`。
- Linux 启动失败：执行 `journalctl -u nodewatch-agent -n 100 --no-pager` 查看原因。

## 7. 升级

先备份配置，再重新运行对应系统的安装脚本。脚本会替换程序并保留 `state` 中的身份和待补传指标。不要复制另一台机器的 `identity.json`。

## 8. 卸载

Windows 管理员 PowerShell：

```powershell
.\windows-uninstall.ps1
```

默认只删除计划任务，保留 `C:\ProgramData\NodeWatch` 中的配置、身份、缓存和日志。确认不再需要后彻底删除：

```powershell
.\windows-uninstall.ps1 -RemoveData
```

Linux：

```bash
sudo ./linux-uninstall.sh
```

默认保留 `/var/lib/nodewatch`。彻底删除：

```bash
sudo ./linux-uninstall.sh --remove-data
```
