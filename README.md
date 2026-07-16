# NodeWatch

NodeWatch 是一个面向个人学习和简历展示的轻量级跨平台主机监控平台。它包含 Vue 管理界面、FastAPI API、PostgreSQL 时序数据、告警状态机，以及支持 Windows/Linux 的可靠采集 Agent。当前正在完成 P7 的阿里云生产部署。

## 功能与技术栈

- Vue 3、TypeScript、Pinia、Vue Router、Element Plus、ECharts
- FastAPI、SQLAlchemy、Alembic、PostgreSQL 17、APScheduler
- Python Agent、psutil、SQLite WAL、httpx、PyInstaller
- Docker Compose、Nginx、GitHub Actions、systemd、Windows 计划任务

核心功能包括设备管理、一次性 Agent Token、实时指标、历史聚合、多磁盘、告警与维护模式、离线缓存、批量幂等补传和跨平台安装。

## 数据流

```text
Agent → SQLite 待传队列 → HTTPS 批量 API → PostgreSQL 历史/latest 表
                                                ↓
浏览器 ← Nginx ← FastAPI + Vue 静态文件 ← 告警状态机与历史查询
```

## 第一次启动

在项目根目录执行：

```powershell
docker compose -f deploy/docker-compose.local.yml up -d
Copy-Item .env.example .env
```

然后编辑 `.env`，至少替换 `SECRET_KEY` 和 `BOOTSTRAP_ADMIN_PASSWORD`。本地已有 `.env` 时不要再次复制覆盖。

初始化数据库并启动后端：

```powershell
cd backend
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

保留后端终端，再打开一个终端启动前端：

```powershell
cd frontend
npm install
npm run dev
```

访问终端显示的前端地址（通常是 `http://localhost:5173`），使用 `.env` 中的 `BOOTSTRAP_ADMIN_USERNAME` 和 `BOOTSTRAP_ADMIN_PASSWORD` 登录。

> 首个管理员仅在 `users` 表为空时自动创建。之后修改 `.env` 中的初始密码不会修改数据库里已有账号。

## 连接本机 Agent

1. 在网页“设备”页创建设备并立即复制一次性 Token。
2. 将 `agent/config.example.toml` 复制为 `agent/config.toml`，替换其中的 `agent_token`。
3. 保持后端运行，再打开一个终端执行：

```powershell
cd agent
.\.venv\Scripts\Activate.ps1
nodewatch-agent --config config.toml --once
```

P3 连续采集时去掉 `--once`，Agent 会按服务端返回的 60 秒周期持续上报；按 `Ctrl+C` 停止：

```powershell
nodewatch-agent --config config.toml
```

刷新设备页后应看到本机主机名、操作系统和 Agent 版本。`config.toml` 与本地身份文件已被 Git 忽略，不得提交真实 Token。

## 常用检查

- 存活检查：`http://127.0.0.1:8000/api/v1/health/live`
- 就绪检查：`http://127.0.0.1:8000/api/v1/health/ready`
- 停止数据库：`docker compose -f deploy/docker-compose.local.yml down`
- 停止数据库但保留数据：上述 `down` 命令默认会保留 Volume。

## 自动化验证

```powershell
cd backend
ruff check .
pytest

cd ../frontend
npm run typecheck
npm run test
npm run build
```

## 生产部署

生产镜像使用多阶段构建，将 Vue 产物和 FastAPI 合并为同源服务。Compose 中 App 只映射 `127.0.0.1:8000`，PostgreSQL 不映射宿主机端口，公网仅由 Nginx 提供 80/443。

完整的阿里云轻量应用服务器指南见 [docs/ALIYUN_DEPLOY.md](docs/ALIYUN_DEPLOY.md)，Agent 安装见 [docs/AGENT_INSTALL.md](docs/AGENT_INSTALL.md)。

## 安全与数据保留

- 密码使用 Argon2，Session 和 Agent Token 在数据库只保存 SHA-256 哈希。
- 生产 Cookie 仅通过 HTTPS 发送，Host 头按域名白名单校验。
- 原始指标默认保留 30 天；Agent 离线缓存默认保留 7 天、最多 10000 条。
- PostgreSQL 使用命名卷，并提供 `pg_dump`、临时数据库恢复演练和 7 天备份轮转脚本。

## 已知限制

- MVP 仅支持单 App 副本和单 Uvicorn Worker，因为 APScheduler 尚未使用分布式锁。
- 2 核 2 GiB 单机适合个人项目和小规模设备，不等同于高可用架构。
- 中国内地服务器使用域名正式对外服务前需要完成 ICP 备案。

完整产品要求见 `NodeWatch_个人开发与Vibe_Coding交付文档_阿里云版.md`，阶段进度见 `PROGRESS.md`，技术取舍见 `DECISIONS.md`。

## 许可证

本项目使用 MIT License。
