# 安全设计与公开仓库检查

## 身份与秘密

- 密码使用 Argon2 单向哈希，数据库不保存明文密码。
- 浏览器 Session Token 和 Agent Token 都由安全随机数生成，数据库只保存 SHA-256 哈希。
- Session Cookie 使用 `HttpOnly`、`SameSite=Lax`；生产环境必须设置 `SESSION_COOKIE_SECURE=true`。
- Agent Token 只在生成时完整显示一次，首次 bootstrap 后与本地随机实例 UUID 绑定。
- 登录失败使用统一提示并写审计日志，避免泄露用户名是否存在。
- 日志只允许输出 Token 短前缀，不得输出密码、Cookie、完整 Token、数据库连接串或私钥。

## 网络与容器

- Nginx 是唯一公网 Web 入口，HTTP 跳转到 HTTPS。
- App 只映射宿主机 `127.0.0.1:8000`；PostgreSQL 不映射宿主机端口。
- 生产环境使用 Host 白名单；容器内健康检查额外允许 `localhost` 和 `127.0.0.1`。
- App 镜像使用非 root 用户、只读根文件系统和资源限制。
- 当前使用受信任的短期公网 IP 证书，依赖 Certbot 定时续期；续期钩子通过 `nginx -t` 后才 reload。

## 数据最小化

Agent 只采集系统版本、CPU、内存、磁盘、网络速率和 uptime，不采集键盘、浏览历史、截屏、文件内容或完整进程列表。项目不提供远程命令、关机或桌面控制。

原始指标默认保留 30 天；Agent 本地缓存默认保留 7 天、最多 10000 条。备份文件权限为 `600`，至少保留一份服务器外副本并定期执行恢复演练。

## 演示数据防护

演示 seed 使用固定 UUID 和 `[演示]` 前缀，只重建自身数据；若 UUID 被其他设备占用会中止。命令检测到 `APP_ENV=production` 时拒绝执行，不能通过 seed 向生产库写入假监控指标。

## 仓库内的安全边界

以下文件只允许出现在本机或服务器，不得提交：

- `.env`、`config.toml`、Agent `identity.json` 和 `metrics.db`
- SSH、TLS、GHCR Token、Agent Token 和数据库密码
- 数据库备份、生产日志、带真实 IP/主机名/用户名的截图

`.env.example` 和 `production.env.example` 只能使用明显占位值。

## 公开仓库前检查清单

1. 检查当前文件：

```powershell
git status --short
git ls-files | Select-String -Pattern '\.env$|config\.toml$|identity\.json$|metrics\.db$|\.sql|\.pem$|id_rsa'
rg -n --hidden -g '!\.git/**' 'nwa_[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|postgresql\+psycopg://[^:]+:[^@]+'
```

2. 检查 Git 历史，而不只检查当前目录：

```powershell
git log --all --oneline
git log -p --all | Select-String -Pattern 'nwa_|PRIVATE KEY|BOOTSTRAP_ADMIN_PASSWORD|DATABASE_URL'
```

3. 人工检查 README、部署记录和三张截图，遮挡公网 IP、Token、用户名、真实主机名和浏览器个人信息。
4. 若秘密曾进入提交历史，立即轮换秘密；仅删除当前文件不够。确认后再用专门的历史清理工具，并强制所有协作者重新拉取。
5. 把仓库设为公开后，再从无登录浏览器打开仓库，确认 README、Actions 和 Release 可见且没有敏感附件。

## 已知安全限制

- 当前没有 MFA、OAuth、登录速率限制或独立 WAF。
- 单机数据库、应用和反向代理共享故障域，不属于高可用方案。
- Agent Token 是长期凭据；发现泄露后必须在网页撤销并生成新 Token。
- 公网 IP 证书有效期短，必须持续监控 Certbot 定时器和到期时间。
