# 故障排查

先判断问题属于哪一层：数据库 → 后端健康检查 → Nginx/HTTPS → Agent。按层检查比反复重装更容易定位原因。

## Docker 无法连接

典型错误包含 `dockerDesktopLinuxEngine`、`daemon is running` 或 `no configuration file provided`。

- Windows：先打开 Docker Desktop，等待状态显示 Engine running，再执行 `docker version`。
- 命令必须在项目根目录执行，并显式指定本地文件：

```powershell
docker compose -f deploy/docker-compose.local.yml up -d
docker compose -f deploy/docker-compose.local.yml ps
```

`docker compose pull` 在没有 Compose 文件的目录执行会报错，并不表示 Docker 损坏。

## PowerShell 禁止执行脚本

只为当前窗口临时放行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

也可以不激活虚拟环境，直接调用 `.\.venv\Scripts\python.exe`。npm 被 `npm.ps1` 拦截时使用 `npm.cmd`。

## 就绪检查 502，但存活检查正常

`/health/live` 只证明 Python 进程存活；`/health/ready` 还会检查 PostgreSQL 和迁移版本。依次执行：

```powershell
docker compose -f deploy/docker-compose.local.yml ps
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/ready
```

确认 `.env` 的数据库地址、用户名、密码和 Docker Compose 一致。

## Agent 返回 401、403 或 409

- 401：Token 缺失或格式错误，重新复制完整的 `nwa_...`。
- 403：Token 已撤销或设备被禁用，在网页生成新 Token。
- 409：Token 已绑定另一 Agent 实例，不要复制旧身份文件；为目标设备重新生成 Token。

日志只应出现 Token 短前缀。如果完整 Token 出现在截图或聊天中，应立即撤销并轮换。

## Agent 一直显示“无法连接服务端”

先从 Agent 机器测试健康接口：

```powershell
curl.exe --noproxy "*" https://你的地址/api/v1/health/ready
```

若健康接口可达，检查 Agent 配置中的 `server_url` 是否为 HTTPS、系统时间是否准确、证书是否仍有效。恢复连接后，日志会先批量补传并让 `remaining` 逐步变为 0。

## Windows 覆盖安装提示文件被占用

使用仓库当前的 `windows-install.ps1`。它会停止并注销旧计划任务、结束仍占用安装目录可执行文件的旧进程，再复制新版本。不要手工删除 SQLite `state` 目录，否则会丢失身份和待传队列。

检查：

```powershell
Get-ScheduledTask -TaskName "NodeWatch Agent"
Get-Content "C:\ProgramData\NodeWatch\logs\agent.log" -Encoding utf8 -Tail 30
```

计划任务长期为 `Ready` 且没有新日志时，用 `Get-ScheduledTaskInfo` 查看 `LastTaskResult`，再以前台 `--once` 运行定位配置错误。

## Nginx 返回 502

502 通常表示 Nginx 正常，但它无法连接后端：

```bash
cd /opt/nodewatch/deploy
docker compose ps
docker compose logs --tail 100 app
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
sudo nginx -t
```

App 必须监听容器内 `0.0.0.0:8000`，宿主机映射保持 `127.0.0.1:8000`。不要为修复 502 把 8000 或 5432 开到公网。

## HTTPS 证书或续期异常

公网 IP 证书是短期证书，自动续期比域名证书更重要：

```bash
sudo certbot certificates
systemctl list-timers --all | grep certbot
sudo certbot renew --dry-run --run-deploy-hooks
```

ACME HTTP-01 验证要求公网 80 端口可访问 `/.well-known/acme-challenge/`。续期钩子应先执行 `nginx -t`，成功后再 reload。

## 数据库或磁盘空间不足

```bash
df -h /
docker system df
cd /opt/nodewatch/deploy
docker compose exec -T db pg_isready -U nodewatch
ls -lh /opt/nodewatch/backups
```

先确认备份有效再清理。不要执行 `docker compose down -v`，它会删除 PostgreSQL 命名卷；不要用 `docker system prune --volumes` 处理不明原因的空间问题。

## 备份恢复失败

```bash
cd /opt/nodewatch/deploy
./scripts/backup.sh
./scripts/restore-test.sh /opt/nodewatch/backups/具体备份.sql.gz
```

“有备份文件”不等于“可恢复”。发布前至少完成一次临时数据库恢复演练，并把备份复制到服务器之外。

## 图表没有数据

确认 Agent 已连续上报至少两个周期、设备时间正确，并选择覆盖样本时间的范围。1 小时使用 raw，24 小时自动使用 5m，7 天自动使用 1h；聚合点少于原始点属于正常现象。
