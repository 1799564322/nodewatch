# 安全

- `.env` 和真实秘密不得提交到仓库；仓库只保留 `.env.example`。
- 密码使用 Argon2 单向哈希，数据库不保存明文密码。
- 登录成功后生成随机 Session Token；浏览器保存原始 Token，数据库只保存其 SHA-256 哈希。
- Session Cookie 使用 `HttpOnly` 和 `SameSite=Lax`。生产环境必须设置 `SESSION_COOKIE_SECURE=true`，使 Cookie 仅通过 HTTPS 发送。
- 登录失败返回统一提示，避免泄露用户名是否存在；失败事件写入审计日志。
- `admin` 和 `viewer` 权限由后端依赖校验，前端隐藏按钮不能替代后端鉴权。
- 健康检查不得返回环境变量、密码、Session Token 或数据库地址。
- Agent Token 使用 `nwa_` 前缀和安全随机数，只在生成时返回一次；数据库仅保存 SHA-256 哈希与短前缀。
- Token 首次 bootstrap 后与本地随机 `agent_instance_id` 绑定，其他实例使用同一 Token 返回 409。
- Token 被撤销或设备被禁用后，Agent 请求返回 403；日志只记录 Token 前缀。
- 生产环境使用 `TrustedHostMiddleware` 校验域名；容器内部健康检查额外允许 `127.0.0.1` 和 `localhost`。
- App 宿主机端口只绑定 `127.0.0.1:8000`，PostgreSQL 不映射端口；公网入口仅为 Nginx 80/443。
- 生产镜像使用非 root 用户和只读根文件系统，`.dockerignore` 排除环境变量、私钥、Token 和备份。
- 首次管理员创建后使用容器内 CLI 修改密码并撤销旧会话，再从 `.env` 删除 bootstrap 凭据。
