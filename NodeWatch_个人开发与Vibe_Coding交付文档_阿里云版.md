# NodeWatch 个人全栈开发与 Vibe Coding 交付文档

**文档版本：** v1.1  
**编写日期：** 2026-07-14  
**项目性质：** 个人学习项目 / 简历项目 / 可公开演示的全栈作品  
**默认项目名称：** NodeWatch（后续可以修改）  
**目标部署平台：** 阿里云轻量应用服务器（Ubuntu 24.04，2 核 2 GiB，40 GiB 系统盘，西南 1（成都））  
**目标开发者水平：** 已学习 Python，JavaScript/TypeScript 初学者  
**目标运行规模：** 10～50 台被监控设备，每台默认 60 秒上报一次

---

## 0. 文档用途

本文件同时服务于两类读者：

1. **项目所有者（我本人）**：明确自己每个阶段需要学习、测试和手动操作的内容。
2. **Vibe Coding 编程代理**：把本文件当作唯一的产品与工程需求基线，按阶段实现，不得擅自扩大范围。

本项目必须采用“阶段交付”的方式开发。编程代理完成一个阶段后必须停止，提交阶段报告，等待我明确回复“继续下一阶段”后再继续。

---

# 第一部分：项目决策摘要

## 1. 项目目标

开发一个轻量级、跨平台的主机资源上报与监控平台：

- 在 Windows 或 Linux 被监控设备上运行 Python Agent。
- Agent 定时采集 CPU、内存、磁盘、网络和系统信息。
- Agent 使用 HTTPS 和独立 Token 向服务端上报数据。
- 服务端保存最新状态和历史指标。
- 用户通过网页查看设备在线状态、历史曲线和告警。
- 系统支持 CPU、内存、磁盘和设备离线告警。
- 系统可以部署到低配云环境，并作为简历中的完整全栈项目展示。

## 2. MVP 必须完成的功能

1. 管理员登录、退出和会话保持。
2. 管理员创建设备，并生成只显示一次的 Agent Token。
3. Python Agent 获取配置后采集基础系统信息。
4. Agent 每 60 秒上报 CPU、内存、系统盘和网络速率。
5. 服务端保存设备最新状态和历史样本。
6. 总览页显示设备总数、在线数、离线数和告警数。
7. 设备列表显示最新指标和最后上报时间。
8. 设备详情页显示最近 1 小时、24 小时和 7 天曲线。
9. 支持 CPU、内存、磁盘、离线告警。
10. 告警支持“触发中”和“已恢复”状态。
11. Agent 支持请求失败重试和本地离线缓存。
12. 前后端和后端 API 构建为一个生产容器。
13. 使用 Docker Compose 在阿里云轻量应用服务器上部署应用与 PostgreSQL，并由宿主机 Nginx 提供反向代理和 HTTPS。
14. 完成 README、安装说明、架构图、演示账号说明和简历描述。

## 3. MVP 明确不做的功能

以下功能禁止在 MVP 阶段实现：

- 远程执行 Shell、PowerShell 或任意脚本。
- 远程关机、重启、控制桌面或截屏。
- 采集完整进程列表、键盘记录、浏览历史等敏感信息。
- Kubernetes 管理、Docker 容器监控和容器编排。
- Prometheus、Grafana、Redis、Celery、Kafka、Elasticsearch。
- 多租户计费系统。
- 手机 App。
- 本地大模型或复杂 AI 功能。
- 短信通知。
- 自动扩容、多副本高可用和分布式定时任务。

任何新增需求必须先写入 `docs/CHANGE_REQUESTS.md`，明确为什么需要、会增加多少复杂度，再决定是否进入后续版本。

## 4. 最终技术栈

### 4.1 Agent

- Python 3.12
- psutil
- httpx
- Pydantic / pydantic-settings
- SQLite（离线缓存）
- PyInstaller（Windows/Linux 分别构建）
- pytest

### 4.2 后端

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic
- APScheduler（MVP 单副本、单 Worker 条件下使用）
- pytest
- Ruff

### 4.3 前端

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Axios
- Element Plus
- Apache ECharts
- Vitest

### 4.4 部署

- 单一应用镜像：Vue 在构建阶段生成静态文件，FastAPI 在运行时同时提供 API 和前端文件。
- 阿里云轻量应用服务器：运行 Docker Engine、Docker Compose、Nginx、NodeWatch 应用容器和 PostgreSQL 容器。
- Docker Compose：管理 `app` 与 `db` 两个容器；应用固定单副本、单 Uvicorn Worker。
- 宿主机 Nginx：只对公网提供 80/443，将请求反向代理到 `127.0.0.1:8000`。
- PostgreSQL：只加入 Docker 内部网络，使用命名卷保存数据，不映射宿主机公网端口。
- GitHub Actions：测试、构建镜像并推送到镜像仓库。
- 生产发布使用固定镜像 tag；服务器通过 `docker compose pull && docker compose up -d` 更新。
- 正式公网访问优先使用已完成 ICP 备案的域名和 HTTPS；公网 IP 仅用于部署初期的短时 HTTP 验证。

## 5. 为什么使用单应用容器

MVP 不把 Vue 和 FastAPI 拆成两个公网服务，原因如下：

- 减少一套容器、域名和反向代理配置。
- 前后端同域，不需要额外处理 CORS。
- 登录 Cookie、静态页面和 API 使用同一个域名，理解成本更低。
- 公网只暴露 Nginx 的 80/443；应用端口 8000 只绑定 `127.0.0.1`。
- PostgreSQL 不发布任何宿主机端口，只允许应用容器通过 Docker 内部网络访问。
- 仍然保留清晰的 `frontend/` 与 `backend/` 源码边界，未来可以拆分。

生产运行逻辑：

```text
浏览器 / Python Agent
  |
  | HTTPS :443
  v
阿里云轻量应用服务器防火墙
  |
  v
宿主机 Nginx
  |
  | http://127.0.0.1:8000
  v
NodeWatch App 容器（单副本、单 Worker）
  |- /api/v1/*       REST API
  |- /assets/*       Vue 构建产物
  `- /*              返回 index.html，由 Vue Router 接管
  |
  | Docker 内部网络 :5432
  v
PostgreSQL 容器
  |
  v
Docker 命名卷 postgres_data
```

服务器基线：Ubuntu 24.04、2 vCPU、2 GiB 内存、40 GiB 系统盘。公网 IP、SSH 私钥、数据库密码和生产域名均不得写入仓库。

# 第二部分：给 Vibe Coding 的总执行规则

## 6. 编程代理必须遵守的规则

1. 开始编码前完整阅读本文件。
2. 只执行当前阶段，不得提前实现后续阶段。
3. 每个阶段开始前，先检查：
   - `README.md`
   - `PROGRESS.md`
   - `DECISIONS.md`
   - 当前代码和测试状态
4. 不得把密码、Token、数据库连接串或密钥写入源码、示例截图或 Git 历史。
5. 所有环境变量必须记录在 `.env.example`，真实 `.env` 必须加入 `.gitignore`。
6. 所有数据库结构变化必须通过 Alembic migration 完成。
7. 所有时间在数据库和 API 内使用 UTC；只在前端显示时转换为浏览器本地时间。
8. 所有字节数量在 API 中使用整数；前端负责转换成 MB、GB。
9. 所有公开 API 必须有输入校验和明确错误码。
10. 所有 Token、密码和 Session ID 在日志中必须脱敏。
11. 禁止使用 `except Exception: pass` 或吞掉异常。
12. 关键业务逻辑必须放入 service 层，不允许全部堆在路由函数中。
13. 前端不得在多个页面重复定义同一套 API 类型。
14. 不得为了“看起来完成”而使用无法替换的假数据。
15. 可以提供开发用 seed 数据，但必须与真实流程分开，并可以关闭。
16. 每个阶段至少添加与该阶段关键逻辑对应的测试。
17. 完成阶段后必须运行格式化、静态检查和测试。
18. 如果某项工作必须由我手动完成，立即停在清晰的检查点，给出逐步操作、需要复制的值和验证方式。
19. 遇到非关键不确定项时，优先采用本文档的最小实现，不要无限提问。
20. 每个阶段完成后更新 `PROGRESS.md` 和 `DECISIONS.md`。

## 7. 阶段完成报告格式

每个阶段结束时，编程代理必须按以下格式回复：

```markdown
# 阶段 Pn 完成报告

## 已完成
- ...

## 主要文件
- `path/to/file`: 作用

## 数据库变更
- migration 名称和内容；没有则写“无”

## 测试结果
- 执行命令
- 通过数量
- 未通过项

## 本地验证步骤
1. ...

## 需要我手动完成
- 没有则写“无”

## 已知限制
- ...

## 下一阶段建议
- 只说明 Pn+1，不开始编码
```

## 8. 推荐 Git 工作方式

- `main`：始终保持可以运行。
- 每个阶段使用一个分支，例如 `phase/p1-auth`。
- 阶段验收后合并到 `main`。
- Commit 使用清晰前缀：
  - `feat:` 新功能
  - `fix:` 修复
  - `test:` 测试
  - `docs:` 文档
  - `refactor:` 重构
  - `chore:` 工具和配置
- 每个阶段至少有一个可理解的提交，不允许把全部项目压成一个提交。

---

# 第三部分：功能需求

## 9. 用户角色

### 9.1 admin

可以：

- 登录系统。
- 创建、编辑、禁用和删除设备。
- 生成、撤销和轮换 Agent Token。
- 查看所有设备和指标。
- 创建、编辑和启停告警规则。
- 确认告警。
- 创建 viewer 用户。
- 查看审计记录。

### 9.2 viewer

可以：

- 登录系统。
- 查看总览、设备、历史指标和告警。
- 不可以创建或修改设备、Token、用户和告警规则。

MVP 不开放自主注册。用户只能由管理员创建。

## 10. 设备生命周期

```text
管理员创建设备
  -> 系统生成一次性可见 Token
  -> 用户在目标机器配置 Agent
  -> Agent 首次启动并上报系统信息
  -> 设备进入在线状态
  -> Agent 周期上报指标
  -> Token 可以撤销或轮换
  -> 设备可以进入维护、禁用或删除状态
```

设备状态分为：

- `online`：最近一次有效上报未超过离线阈值。
- `offline`：超过离线阈值没有有效上报。
- `warning`：在线但存在触发中的 warning/critical 告警。
- `disabled`：管理员禁用，不接收数据且不产生离线告警。
- `maintenance`：维护模式，不产生离线告警，但仍可接收数据。

数据库只保存 `is_enabled` 和 `maintenance_until` 等持久状态；`online/offline/warning` 优先根据 `last_seen_at` 和告警动态计算，避免状态不一致。

## 11. Agent 采集内容

### 11.1 首次启动或每天更新一次的系统信息

- Agent 实例 UUID（本地首次生成并持久化）。
- 主机名。
- 操作系统名称和版本。
- CPU 架构。
- CPU 型号。
- 物理核心数、逻辑核心数。
- 总内存。
- Agent 版本。
- Python 运行环境仅用于调试，不作为公开页面重点。

### 11.2 每个采样周期上报的指标

- 采集时间。
- CPU 总使用率。
- 内存总量、已使用、使用率。
- Swap 使用率（系统支持时）。
- 系统盘总量、已使用、使用率。
- 每个磁盘分区的最新状态。
- 网络发送和接收速率，单位 bytes/second。
- 系统运行时长，单位秒。

### 11.3 MVP 不采集

- 文件内容。
- 用户文档路径。
- 完整进程命令行。
- 浏览器数据。
- 屏幕内容。
- 键盘、鼠标、音频、摄像头信息。
- 精确硬件序列号。

## 12. 页面需求

### 12.1 登录页

- 用户名。
- 密码。
- 登录按钮。
- 登录失败提示。
- 已登录时访问登录页自动跳转总览。

### 12.2 总览页

展示：

- 设备总数。
- 在线设备数。
- 离线设备数。
- 存在告警设备数。
- 触发中告警数。
- CPU 使用率最高的 5 台在线设备。
- 内存使用率最高的 5 台在线设备。
- 最近 10 条告警。
- 设备状态分布。

### 12.3 设备列表页

列：

- 设备名称。
- 主机名。
- 操作系统。
- CPU。
- 内存。
- 系统盘。
- 当前网络速率。
- 状态。
- Agent 版本。
- 最后上报时间。

支持：

- 名称/主机名搜索。
- 状态筛选。
- 操作系统筛选。
- 按 CPU、内存、最后上报时间排序。
- 分页。

### 12.4 设备详情页

顶部：

- 设备名称、主机名、系统、状态。
- 最后上报时间。
- Agent 版本。
- Token 状态。
- 维护模式状态。

指标卡：

- CPU。
- 内存。
- 系统盘。
- 网络发送/接收。
- 运行时长。

图表：

- CPU 历史。
- 内存历史。
- 网络发送和接收历史。
- 系统盘使用率历史。
- 时间范围：1 小时、24 小时、7 天、自定义。

其他区域：

- 所有磁盘的最新状态。
- 当前告警。
- 历史告警。
- 系统信息。

### 12.5 告警页

- 触发中、已恢复、已确认筛选。
- 严重程度筛选。
- 设备筛选。
- 告警名称、设备、内容、开始时间、恢复时间、持续时间。
- 管理员可以确认告警。

### 12.6 设置页

管理员可见：

- 用户管理。
- 设备管理和 Token 轮换。
- 告警规则管理。
- 数据保留配置只读展示，MVP 通过环境变量修改。
- 系统版本和构建信息。

---

# 第四部分：非功能需求

## 13. 资源目标

MVP 目标：

- 10～50 台设备。
- 默认每台 60 秒一个样本。
- 单应用容器。
- 单 Uvicorn Worker。
- PostgreSQL 单实例容器。
- 原始指标默认保留 30 天，并监控磁盘增长。
- 低并发个人演示，不按企业级高可用设计。

当前阿里云服务器基线：

| 项目 | 当前配置 | 约束 |
|---|---:|---|
| 操作系统 | Ubuntu 24.04 | 只使用 LTS 系统包和 Docker 官方仓库 |
| CPU | 2 vCPU | App 与 PostgreSQL 共用，不运行本地大模型 |
| 内存 | 2 GiB | 建议额外创建 2 GiB Swap，防止瞬时 OOM |
| 系统盘 | 40 GiB | 需要限制 Docker 日志、备份数量和指标保留期 |
| 公网带宽 | 200 Mbps 峰值 | 监控上报数据量很小，不以峰值带宽作为性能目标 |

建议容器资源上限：

| 组件 | CPU 上限建议 | 内存上限建议 | 说明 |
|---|---:|---:|---|
| NodeWatch App | 0.75 Core | 512 MiB | 单副本、单 Worker |
| PostgreSQL | 0.75 Core | 768 MiB | 小连接池，关闭不需要的扩展 |
| Nginx | 宿主机进程 | 通常很小 | 负责 80/443 和 TLS |
| 系统与 Docker | 保留余量 | 至少保留约 500 MiB | 避免把 2 GiB 全部分配给容器 |

磁盘初始预算：

- PostgreSQL 数据与索引：先预留 10～15 GiB。
- Docker 镜像、构建缓存与容器日志：控制在 5～8 GiB。
- 逻辑备份：本机只保留最近 7 份，并计划复制到服务器外。
- 系统、软件包和安全余量：至少保留 10 GiB。

必须为 Docker 配置日志轮转，例如单文件 10 MiB、最多 3 个文件。磁盘使用率达到 70% 时开始检查，达到 80% 时必须清理或缩短原始指标保留期。不要因为资源有余量就增加副本；MVP 内部调度器要求应用保持单副本、单 Worker，否则离线检查和清理任务可能重复执行。

## 14. 性能目标

- Agent 单次上报 JSON 尽量小于 20 KiB。
- 批量补传单次最多 500 条样本，并设置请求体上限。
- 设备列表使用最新状态表，不扫描历史样本表。
- 历史查询必须包含设备 ID 和时间范围。
- 图表接口根据时间范围做聚合或限制点数，单个序列建议不超过 1,500 个点。
- 所有列表接口必须分页。

## 15. 可靠性目标

- Agent 上传失败不能阻塞下一次采集。
- Agent 使用 SQLite 保存待上传样本。
- 缓存默认最多保留 7 天或 10,000 条，以先达到的限制为准。
- HTTP 请求使用超时。
- 重试使用指数退避并添加随机抖动。
- 服务端重复收到同一设备、同一采集时间的样本时保持幂等。
- 服务端重启后数据和 Token 不丢失。

## 16. 可维护性目标

- Python 与 TypeScript 开启类型检查。
- API Schema 与数据库 Model 分离。
- 数据库查询集中在 repository/service 层。
- `README.md` 能让新用户在本地 30 分钟内跑通。
- `docs/` 记录架构、API、部署和故障排查。

---

# 第五部分：代码仓库设计

## 17. 目录结构

```text
nodewatch/
├── agent/
│   ├── nodewatch_agent/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── collector.py
│   │   ├── sender.py
│   │   ├── cache.py
│   │   ├── identity.py
│   │   ├── models.py
│   │   ├── logging_config.py
│   │   └── version.py
│   ├── scripts/
│   │   ├── install-linux.sh
│   │   ├── uninstall-linux.sh
│   │   ├── install-windows.ps1
│   │   └── uninstall-windows.ps1
│   ├── tests/
│   ├── config.example.toml
│   └── pyproject.toml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── jobs/
│   │   ├── static/
│   │   └── cli.py
│   ├── alembic/
│   ├── tests/
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── utils/
│   │   └── views/
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── deploy/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── docker-compose.local.yml
│   ├── production.env.example
│   ├── docker-compose.production.yml
│   └── nginx-nodewatch.conf.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── AGENT_INSTALL.md
│   ├── ALIYUN_DEPLOY.md
│   ├── SECURITY.md
│   ├── TROUBLESHOOTING.md
│   └── CHANGE_REQUESTS.md
├── .github/workflows/
│   ├── ci.yml
│   └── image.yml
├── .env.example
├── .gitignore
├── DECISIONS.md
├── PROGRESS.md
├── LICENSE
└── README.md
```

## 18. 编码规范

- Python：4 空格、类型标注、Ruff 格式化和检查。
- TypeScript：严格模式开启。
- 数据库表名使用复数 snake_case。
- Python 类使用 PascalCase，函数和字段使用 snake_case。
- TypeScript 变量和函数使用 camelCase，组件使用 PascalCase。
- API 路径使用复数名词和小写短横线。
- 错误响应统一格式。

统一错误响应：

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "设备不存在",
    "request_id": "req_...",
    "details": null
  }
}
```

---

# 第六部分：数据库设计

## 19. 通用约定

- 主业务 ID 使用 UUID。
- 高频时序表主键可使用 BIGINT 自增。
- 所有时间字段为 timezone-aware UTC。
- 所有表至少有 `created_at`；需要修改的表有 `updated_at`。
- 所有外键明确删除策略。
- 不在 PostgreSQL 中保存 Agent 原始 Token、用户明文密码或 Session 原始值。

## 20. users

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| username | VARCHAR(64) | 唯一、非空、小写规范化 |
| password_hash | TEXT | Argon2 或 bcrypt 哈希 |
| role | VARCHAR(16) | admin/viewer |
| is_active | BOOLEAN | 默认 true |
| last_login_at | TIMESTAMPTZ | 可空 |
| created_at | TIMESTAMPTZ | 非空 |
| updated_at | TIMESTAMPTZ | 非空 |

## 21. user_sessions

使用数据库 Session，避免 MVP 额外引入 Redis。

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| user_id | UUID | 外键 users，级联删除 |
| session_hash | CHAR(64) | SHA-256 哈希，唯一 |
| expires_at | TIMESTAMPTZ | 非空 |
| last_seen_at | TIMESTAMPTZ | 非空 |
| ip_address | INET/TEXT | 可空，按兼容实现 |
| user_agent | TEXT | 可空 |
| created_at | TIMESTAMPTZ | 非空 |

浏览器 Cookie：

- 名称：`nodewatch_session`
- HttpOnly=true
- Secure=true（生产）
- SameSite=Lax
- Path=/
- Max-Age 由配置决定

## 22. devices

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| name | VARCHAR(100) | 用户定义名称 |
| hostname | VARCHAR(255) | Agent 上报，可空 |
| agent_instance_id | UUID | Agent 本地生成，绑定后唯一 |
| os_name | VARCHAR(64) | 可空 |
| os_version | VARCHAR(255) | 可空 |
| architecture | VARCHAR(64) | 可空 |
| cpu_model | VARCHAR(255) | 可空 |
| cpu_physical_cores | INTEGER | 可空 |
| cpu_logical_cores | INTEGER | 可空 |
| memory_total_bytes | BIGINT | 可空 |
| agent_version | VARCHAR(32) | 可空 |
| last_seen_at | TIMESTAMPTZ | 可空 |
| last_ip | VARCHAR(64) | 可空 |
| is_enabled | BOOLEAN | 默认 true |
| maintenance_until | TIMESTAMPTZ | 可空 |
| created_at | TIMESTAMPTZ | 非空 |
| updated_at | TIMESTAMPTZ | 非空 |

## 23. agent_tokens

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| device_id | UUID | 外键 devices，级联删除 |
| token_prefix | VARCHAR(16) | 只用于识别和界面展示 |
| token_hash | CHAR(64) | SHA-256 哈希，唯一 |
| last_used_at | TIMESTAMPTZ | 可空 |
| expires_at | TIMESTAMPTZ | 可空 |
| revoked_at | TIMESTAMPTZ | 可空 |
| created_at | TIMESTAMPTZ | 非空 |

原始 Token 格式建议：

```text
nwa_<43个以上安全随机字符>
```

Token 只在生成时返回一次。之后任何 API 都不得返回完整 Token。

## 24. device_latest_metrics

每台设备最多一行，首页和设备列表直接读取。

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| device_id | UUID | 主键兼外键 |
| collected_at | TIMESTAMPTZ | 非空 |
| received_at | TIMESTAMPTZ | 非空 |
| cpu_percent | NUMERIC(5,2) | 0～100 |
| memory_percent | NUMERIC(5,2) | 0～100 |
| memory_used_bytes | BIGINT | 非负 |
| swap_percent | NUMERIC(5,2) | 可空 |
| root_disk_percent | NUMERIC(5,2) | 可空 |
| root_disk_used_bytes | BIGINT | 可空 |
| net_tx_bytes_per_sec | BIGINT | 非负 |
| net_rx_bytes_per_sec | BIGINT | 非负 |
| uptime_seconds | BIGINT | 非负 |
| updated_at | TIMESTAMPTZ | 非空 |

## 25. metric_samples

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | BIGINT | 主键自增 |
| device_id | UUID | 外键 devices |
| collected_at | TIMESTAMPTZ | 采集时间 |
| received_at | TIMESTAMPTZ | 服务端接收时间 |
| cpu_percent | NUMERIC(5,2) | 0～100 |
| memory_percent | NUMERIC(5,2) | 0～100 |
| memory_used_bytes | BIGINT | 非负 |
| swap_percent | NUMERIC(5,2) | 可空 |
| root_disk_percent | NUMERIC(5,2) | 可空 |
| root_disk_used_bytes | BIGINT | 可空 |
| net_tx_bytes_per_sec | BIGINT | 非负 |
| net_rx_bytes_per_sec | BIGINT | 非负 |
| uptime_seconds | BIGINT | 非负 |
| created_at | TIMESTAMPTZ | 非空 |

唯一约束：

```text
(device_id, collected_at)
```

关键索引：

```text
(device_id, collected_at DESC)
(collected_at)
```

## 26. disk_latest_metrics

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| device_id | UUID | 外键 devices |
| mountpoint | VARCHAR(255) | 例如 C:\ 或 / |
| filesystem | VARCHAR(64) | 可空 |
| total_bytes | BIGINT | 非负 |
| used_bytes | BIGINT | 非负 |
| percent | NUMERIC(5,2) | 0～100 |
| collected_at | TIMESTAMPTZ | 非空 |
| updated_at | TIMESTAMPTZ | 非空 |

唯一约束：

```text
(device_id, mountpoint)
```

## 27. alert_rules

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| name | VARCHAR(100) | 非空 |
| device_id | UUID | 可空；空表示全局规则 |
| metric | VARCHAR(32) | cpu/memory/root_disk/offline |
| operator | VARCHAR(8) | gt/gte/lt/lte |
| threshold | NUMERIC | 离线规则可为空 |
| duration_seconds | INTEGER | 持续时间 |
| severity | VARCHAR(16) | info/warning/critical |
| cooldown_seconds | INTEGER | 默认 600 |
| is_enabled | BOOLEAN | 默认 true |
| created_at | TIMESTAMPTZ | 非空 |
| updated_at | TIMESTAMPTZ | 非空 |

MVP 启动时自动创建默认规则，但用户可以修改：

- CPU > 90%，持续 300 秒，warning。
- 内存 > 90%，持续 300 秒，warning。
- 系统盘 > 85%，持续 120 秒，warning。
- 设备 180 秒未上报，critical。

## 28. alert_events

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键 |
| device_id | UUID | 外键 devices |
| rule_id | UUID | 外键 alert_rules |
| status | VARCHAR(16) | firing/resolved/acknowledged |
| severity | VARCHAR(16) | 事件发生时快照 |
| title | VARCHAR(200) | 非空 |
| message | TEXT | 非空 |
| observed_value | NUMERIC | 可空 |
| threshold_value | NUMERIC | 可空 |
| started_at | TIMESTAMPTZ | 非空 |
| last_evaluated_at | TIMESTAMPTZ | 非空 |
| resolved_at | TIMESTAMPTZ | 可空 |
| acknowledged_at | TIMESTAMPTZ | 可空 |
| acknowledged_by | UUID | 可空，外键 users |
| created_at | TIMESTAMPTZ | 非空 |
| updated_at | TIMESTAMPTZ | 非空 |

同一设备同一规则只允许存在一个未恢复事件。可以通过事务加应用逻辑实现；若使用 PostgreSQL partial unique index，也必须用 migration 明确创建。

## 29. audit_logs

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | BIGINT | 主键自增 |
| user_id | UUID | 可空 |
| action | VARCHAR(64) | 例如 device.create |
| resource_type | VARCHAR(64) | 可空 |
| resource_id | VARCHAR(64) | 可空 |
| details | JSONB | 已脱敏 |
| ip_address | VARCHAR(64) | 可空 |
| created_at | TIMESTAMPTZ | 非空 |

必须记录：

- 登录成功/失败（失败记录不保存密码）。
- 创建设备。
- 生成、撤销、轮换 Token。
- 修改告警规则。
- 进入或退出维护模式。
- 创建和禁用用户。

---

# 第七部分：API 设计

## 30. API 通用规则

- 前缀：`/api/v1`
- JSON Content-Type。
- 浏览器接口使用 Session Cookie。
- Agent 接口使用 `Authorization: Bearer <agent-token>`。
- Agent 接口不得接受浏览器 Session 替代 Agent Token。
- 返回时间使用 ISO 8601 UTC，例如 `2026-07-14T08:00:00Z`。
- 列表接口使用 `page`、`page_size`，`page_size` 最大 100。
- 每个响应带 `X-Request-ID`。

## 31. 健康检查

```text
GET /api/v1/health/live
GET /api/v1/health/ready
```

- `live`：只验证进程可以响应，不访问数据库。
- `ready`：验证数据库可连接、migration 版本可识别。
- 健康接口不得泄露数据库地址或环境变量。

## 32. 用户认证接口

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

登录请求：

```json
{
  "username": "admin",
  "password": "用户输入的密码"
}
```

登录成功：

```json
{
  "user": {
    "id": "uuid",
    "username": "admin",
    "role": "admin"
  }
}
```

服务端同时设置 HttpOnly Session Cookie。

## 33. 用户管理接口

```text
GET    /api/v1/users
POST   /api/v1/users
PATCH  /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
```

MVP 的 DELETE 实际执行禁用，除非用户从未产生审计关系。

## 34. 设备管理接口

```text
GET    /api/v1/devices
POST   /api/v1/devices
GET    /api/v1/devices/{device_id}
PATCH  /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}
POST   /api/v1/devices/{device_id}/tokens
POST   /api/v1/devices/{device_id}/tokens/{token_id}/revoke
POST   /api/v1/devices/{device_id}/maintenance
DELETE /api/v1/devices/{device_id}/maintenance
```

创建设备：

```json
{
  "name": "server-01"
}
```

生成 Token 的响应只出现一次：

```json
{
  "token": "nwa_xxxxxxxxx",
  "token_id": "uuid",
  "token_prefix": "nwa_abcd",
  "warning": "请立即复制保存，此 Token 之后无法再次查看"
}
```

## 35. 指标查询接口

```text
GET /api/v1/dashboard
GET /api/v1/devices/{device_id}/metrics/latest
GET /api/v1/devices/{device_id}/metrics/history
GET /api/v1/devices/{device_id}/disks
```

历史接口参数：

```text
from=ISO8601
to=ISO8601
resolution=raw|5m|1h
```

如果请求范围过大：

- 后端自动提高 resolution；或
- 返回明确的 422，提示允许的范围。

推荐自动规则：

| 时间范围 | 默认分辨率 |
|---|---|
| <= 6 小时 | raw |
| <= 48 小时 | 5m |
| > 48 小时 | 1h |

MVP 可以先在 SQL 中使用 `date_trunc` 和平均值聚合，不必建立小时汇总表。

## 36. 告警接口

```text
GET   /api/v1/alerts
GET   /api/v1/alerts/{alert_id}
POST  /api/v1/alerts/{alert_id}/acknowledge
GET   /api/v1/alert-rules
POST  /api/v1/alert-rules
PATCH /api/v1/alert-rules/{rule_id}
```

## 37. Agent 接口

```text
POST /api/v1/agent/bootstrap
POST /api/v1/agent/system-info
POST /api/v1/agent/metrics
POST /api/v1/agent/metrics/batch
```

### 37.1 bootstrap

用途：绑定 Agent 本地实例，并返回服务端配置。

请求：

```json
{
  "agent_instance_id": "uuid",
  "agent_version": "0.1.0",
  "hostname": "server-01"
}
```

响应：

```json
{
  "device_id": "uuid",
  "collect_interval_seconds": 60,
  "max_batch_samples": 500,
  "server_time": "2026-07-14T08:00:00Z"
}
```

Token 第一次绑定后，其他 Agent 实例 UUID 使用同一 Token 必须被拒绝，除非管理员执行“重置 Agent 绑定”。

### 37.2 metrics

```json
{
  "sample_id": "agent生成的uuid",
  "collected_at": "2026-07-14T08:10:00Z",
  "cpu_percent": 23.6,
  "memory_percent": 61.2,
  "memory_used_bytes": 10514046976,
  "swap_percent": 0.0,
  "root_disk_percent": 72.4,
  "root_disk_used_bytes": 358629220352,
  "net_tx_bytes_per_sec": 317440,
  "net_rx_bytes_per_sec": 1300234,
  "uptime_seconds": 1296000,
  "disks": [
    {
      "mountpoint": "C:\\",
      "filesystem": "NTFS",
      "total_bytes": 512000000000,
      "used_bytes": 380000000000,
      "percent": 74.2
    }
  ]
}
```

服务端处理顺序：

1. 验证 Token。
2. 验证设备可用且不处于禁用状态。
3. 校验请求体大小、数值范围和时间。
4. 在事务中插入历史样本。
5. Upsert 最新状态和磁盘最新状态。
6. 更新 `devices.last_seen_at`、IP 和 Agent 版本。
7. 对实时样本执行告警评估。
8. 返回接收结果。

响应：

```json
{
  "accepted": 1,
  "duplicate": 0,
  "server_time": "2026-07-14T08:10:01Z"
}
```

批量接口返回每条结果汇总，不因为单条重复而整体失败。

## 38. 状态码约定

- 200：查询或幂等操作成功。
- 201：创建成功。
- 204：无正文成功。
- 400：格式语义错误。
- 401：未登录或 Token 无效。
- 403：权限不足、设备禁用或 Token 已撤销。
- 404：资源不存在。
- 409：重复绑定、唯一冲突或状态冲突。
- 413：请求体过大。
- 422：字段校验失败。
- 429：请求频率过高。
- 500：未处理服务器错误，响应不得包含堆栈。
- 503：数据库不可用或服务未准备好。

---

# 第八部分：Agent 详细设计

## 39. 配置文件

使用 TOML，示例：

```toml
server_url = "https://your-nodewatch-domain.example"
agent_token = "nwa_xxxxxxxxx"
collect_interval_seconds = 60
request_timeout_seconds = 10
verify_tls = true
log_level = "INFO"
```

生产环境禁止将 `verify_tls` 设置为 false。该选项仅用于明确的本地开发环境。

建议路径：

- Windows：`%ProgramData%\NodeWatch\config.toml`
- Linux：`/etc/nodewatch-agent/config.toml`
- 本地状态和 SQLite：
  - Windows：`%ProgramData%\NodeWatch\state\`
  - Linux：`/var/lib/nodewatch-agent/`
- 日志：
  - Windows：`%ProgramData%\NodeWatch\logs\`
  - Linux：优先输出到 journald；开发模式可输出文件。

## 40. Agent 身份

第一次启动：

1. 检查本地状态是否存在 `agent_instance_id`。
2. 不存在则使用安全随机 UUID 生成。
3. 保存到本地状态文件或 SQLite。
4. 调用 bootstrap。
5. 服务端把 Token 与该实例绑定。

不要使用硬盘序列号或 MAC 地址作为唯一身份，避免更换网卡、虚拟化和隐私问题。

## 41. 采集循环

伪代码：

```python
initialize()
bootstrap_if_needed()

while not shutdown_requested:
    started_at = monotonic()
    sample = collector.collect()
    cache.save(sample)
    sender.flush_pending(limit=max_batch_samples)
    sleep(max(0, interval - elapsed(started_at)))
```

重要原则：先保存本地，再尝试上传。上传成功后再从缓存删除，可以减少进程崩溃时的数据丢失。

## 42. 网络速度计算

`psutil.net_io_counters()` 返回累计字节。Agent 保存上一次累计值和采样时间：

```text
速率 = max(0, 当前累计字节 - 上次累计字节) / 实际经过秒数
```

如果系统重启、网卡计数重置或差值为负：

- 当前速率记为 0。
- 更新基线。
- 不产生异常。

## 43. 磁盘采集

- 忽略不可访问、光驱未插入、伪文件系统和重复挂载点。
- 捕获单个分区异常，不因一个分区失败而丢弃整条样本。
- Windows 选择系统盘作为 root disk；Linux 使用 `/`。
- 所有分区只保存最新状态；MVP 历史图表只保存 root disk。

## 44. 离线缓存

SQLite 表建议：

```text
pending_samples
- id INTEGER PRIMARY KEY
- sample_id TEXT UNIQUE
- collected_at TEXT
- payload_json TEXT
- retry_count INTEGER
- next_retry_at TEXT
- created_at TEXT
```

清理规则：

- 成功上传后删除。
- 超过 7 天删除最旧数据并记录 warning 日志。
- 超过 10,000 条删除最旧数据并记录 warning 日志。
- 单条永久校验失败（4xx 且不是 401/429）移入 dead-letter 日志，不无限重试。

## 45. 重试策略

- 网络错误、超时、5xx：指数退避。
- 429：尊重 `Retry-After`，没有时使用退避。
- 401/403：停止持续高频请求，记录明确错误，每 10 分钟重试一次，等待用户修复 Token。
- 422：记录 payload 摘要，停止重试该条。
- 最大退避：5 分钟。
- 添加 0～20% 随机抖动，防止大量设备同时恢复造成尖峰。

## 46. 优雅退出

收到 SIGTERM、SIGINT 或 Windows 停止信号时：

- 停止开始新的采集。
- 等待当前 SQLite 写入完成。
- 最多尝试一次短时 flush。
- 关闭数据库和 HTTP 客户端。
- 在规定超时内退出。

## 47. 打包和安装

Windows 和 Linux 必须分别构建，不尝试跨平台生成同一个二进制。

MVP 输出：

```text
nodewatch-agent-windows-x64.zip
nodewatch-agent-linux-x64.tar.gz
```

包含：

- 可执行文件。
- 配置示例。
- 安装脚本。
- 卸载脚本。
- README。
- SHA-256 校验文件。

Linux 使用 systemd；Windows 第一版可以使用任务计划程序开机启动，后续再改为 Windows Service。

---

# 第九部分：告警系统

## 48. 告警状态机

```text
正常
  -> 条件持续满足
  -> firing
  -> 用户确认（可选）
  -> acknowledged（条件仍可能存在）
  -> 条件恢复
  -> resolved
```

确认告警不等于恢复告警。恢复只能由监控条件不再满足触发。

## 49. CPU 和内存持续告警

不要因为单个峰值触发。

实现方式：

1. 根据规则持续时间计算需要的采样窗口。
2. 查询设备最近窗口内的实时样本。
3. 样本数量不足时不触发。
4. 所有有效样本均超过阈值时触发。
5. 任意有效样本恢复到阈值以下时解决现有事件。

“实时样本”定义：`received_at - collected_at` 不超过允许延迟，例如两个采样周期。离线补传的旧样本只写历史，不触发当前告警。

## 50. 磁盘告警

磁盘变化通常较慢，默认要求连续两个样本超过阈值即可触发。

恢复可设置回差：

- 触发阈值：85%。
- 恢复阈值：82%。

这样可以防止使用率在 84.9% 和 85.1% 之间反复开关告警。MVP 可以把回差固定为 3 个百分点。

## 51. 离线告警

后台任务每 60 秒检查：

```text
当前时间 - last_seen_at > offline_after_seconds
```

以下设备不产生离线告警：

- `is_enabled = false`
- 当前仍在 `maintenance_until` 维护时间内
- 从未成功绑定 Agent，且创建时间不足一个宽限期

设备重新上报后，解决离线告警。

## 52. 防止重复告警

- 同一设备、同一规则只保留一个未恢复事件。
- 每次评估更新 `last_evaluated_at`，不新增重复记录。
- 创建和解决事件使用事务。
- 后端必须是单副本、单 Worker，直到调度任务迁移到独立执行器。

## 53. 定时任务

MVP 在 FastAPI 进程内使用 APScheduler：

- 每 60 秒：离线检查。
- 每天一次：清理过期 Session。
- 每天一次：清理超过保留期的原始样本。
- 每天一次：清理旧审计记录（可配置，默认暂不删除）。

生产启动参数必须固定一个 Worker。后续如果改为多副本，把定时任务迁移到独立 worker、systemd timer 或专门的调度容器，并增加分布式锁。

---

# 第十部分：安全要求

## 54. 密码与登录

- 使用 Argon2 优先，或 bcrypt。
- 登录失败返回统一提示，不暴露用户名是否存在。
- 登录接口限制频率。
- Session 原始值使用安全随机数生成，只存哈希。
- 修改密码后撤销该用户其他 Session。
- 管理员不能禁用系统中最后一个可用 admin。

## 55. Agent Token

- 每台设备独立 Token。
- Token 只显示一次。
- 数据库只存 SHA-256 哈希和前缀。
- Token 支持撤销、过期和轮换。
- 比较哈希使用常量时间比较。
- Agent 日志只显示 Token 前缀。

## 56. 传输和网络

- 正式生产环境只使用 HTTPS，Agent 默认校验证书。
- 阿里云轻量应用服务器防火墙只需要放行 22、80、443。
- SSH 22 端口尽量限制为管理员当前可信公网 IP，不长期对 `0.0.0.0/0` 开放。
- Nginx 对公网监听 80/443。
- App 容器端口必须映射为 `127.0.0.1:8000:8000`，不得映射为 `0.0.0.0:8000`。
- PostgreSQL 容器不配置 `ports`，不得向公网或宿主机直接暴露 5432。
- 不公开调试端口、Docker Remote API、数据库管理面板或其他管理端口。
- 同域部署时 CORS 默认关闭；开发环境只允许明确的 localhost 来源。
- Docker 发布端口可能绕过部分宿主机防火墙规则，因此安全边界不能只依赖 UFW；必须同时做到“云防火墙不放行 + Compose 不公开数据库 + App 只绑定回环地址”。
- 当前服务器位于中国内地地域，使用域名正式对外提供 Web 服务前需要完成 ICP 备案。

## 57. 输入与资源限制

- Agent 单样本请求体限制，例如 256 KiB。
- 批量请求限制，例如 2 MiB 和 500 条。
- 字符串字段限制长度。
- 数值范围校验。
- Agent 时间戳与服务器时间偏差过大时标记或拒绝。
- 不把用户输入直接拼接进 SQL。
- 不允许前端指定任意数据库排序字段，使用白名单映射。

## 58. 日志安全

日志中禁止出现：

- 明文密码。
- 完整 Session。
- 完整 Agent Token。
- 完整数据库连接串。
- Cookie Header。
- 请求体中的秘密字段。

日志应包含：

- request_id。
- 路径、方法、状态码、耗时。
- 设备 ID 或用户 ID（允许内部 UUID）。
- 异常类型和可定位信息。

---

# 第十一部分：环境变量

## 59. 应用环境变量

`deploy/production.env.example` 至少包含：

```dotenv
# Compose 镜像与数据库初始化
NODEWATCH_IMAGE=ghcr.io/your-account/nodewatch:v0.1.0
POSTGRES_DB=nodewatch
POSTGRES_USER=nodewatch
POSTGRES_PASSWORD=replace-with-url-safe-random-password

# 应用
APP_NAME=NodeWatch
APP_ENV=production
APP_VERSION=0.1.0
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://nodewatch:replace-with-url-safe-random-password@db:5432/nodewatch
SECRET_KEY=replace-with-long-random-value

SESSION_COOKIE_NAME=nodewatch_session
SESSION_TTL_SECONDS=604800
SESSION_COOKIE_SECURE=true

# 正式域名；初次仅通过 IP 验证时可临时填写公网 IP
ALLOWED_HOSTS=monitor.example.com

DEFAULT_COLLECT_INTERVAL_SECONDS=60
OFFLINE_AFTER_SECONDS=180
RAW_METRIC_RETENTION_DAYS=30
MAX_AGENT_BATCH_SAMPLES=500
MAX_AGENT_BODY_BYTES=2097152

RUN_SCHEDULER=true

BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=remove-after-first-login
```

要求：

- 生产文件实际路径为 `/opt/nodewatch/deploy/.env`，权限必须为 `600`，所有者为部署用户。
- `.env` 不得提交到 Git；仓库只保留 `production.env.example`。
- `SECRET_KEY` 至少使用 48 字节安全随机值。
- `POSTGRES_PASSWORD` 建议使用 URL-safe 随机字符串，减少数据库连接串转义错误。
- `DATABASE_URL` 中的密码必须与 `POSTGRES_PASSWORD` 一致；若包含特殊字符必须 URL 编码。
- 首次启动时，如果用户表为空，允许用 bootstrap 环境变量创建管理员。
- 管理员创建成功并完成首次登录后，必须从服务器 `.env` 删除 `BOOTSTRAP_ADMIN_PASSWORD`，再执行 `docker compose up -d app`。
- 如果用户表不为空，应用必须忽略 bootstrap 密码，不能覆盖现有管理员。
- 正式启用 HTTPS 后，`SESSION_COOKIE_SECURE` 必须为 `true`。
- 公网 IP、数据库密码、Secret 和一次性 Agent Token 不得进入截图或公开文档。

生成随机值：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

第一个可用于 `SECRET_KEY`，第二个可用于数据库密码。

# 第十二部分：分阶段开发计划

## 60. 阶段总览

| 阶段 | 名称 | 主要结果 | 需要我介入 |
|---|---|---|---|
| P0 | 项目初始化与工程约束 | 仓库、目录、CI 骨架、文档 | 确认名称和仓库 |
| P1 | 后端基础与登录 | 数据库迁移、用户、Session、登录页 | 创建本地 `.env` |
| P2 | 设备与 Agent 最小闭环 | 创建设备、Token、Agent bootstrap | 在一台电脑运行 Agent |
| P3 | 指标采集与总览 | 上报、最新状态、列表和总览 | 观察真实数据 |
| P4 | 历史曲线和磁盘 | 历史 API、ECharts、时间范围 | 验证时区和图表 |
| P5 | 告警系统 | 规则、触发、恢复、离线任务 | 人工制造告警 |
| P6 | Agent 可靠性与打包 | 缓存、重试、安装包 | Windows/Linux 安装测试 |
| P7 | 阿里云轻量服务器部署 | Docker、PostgreSQL、Nginx、HTTPS | 必须手动操作服务器与控制台 |
| P8 | 测试、文档与简历交付 | README、截图、演示和简历文案 | 录制/截图并公开仓库 |

---

## 61. P0：项目初始化与工程约束

### Vibe Coding 负责

1. 创建本文指定目录。
2. 初始化 Python 与 Vue 项目骨架。
3. 创建根目录 README、PROGRESS、DECISIONS。
4. 创建 `.gitignore` 和 `.env.example`。
5. 建立本地 PostgreSQL Docker Compose，仅用于开发。
6. 建立后端 `/health/live` 最小接口。
7. 建立前端空壳和路由。
8. 创建 CI 骨架：Python lint/test、前端 typecheck/test。
9. 创建 `docs/` 占位文档。
10. 不实现登录、设备和指标。

### 我需要手动完成

- 决定 GitHub 仓库名，默认 `nodewatch`。
- 决定仓库公开或私有；简历项目最终建议公开。
- 创建空 GitHub 仓库并把远程地址提供给编程代理，或自行添加 remote。
- 确认项目名称是否保留 NodeWatch。

### 验收标准

- `docker compose -f deploy/docker-compose.local.yml up -d` 可以启动 PostgreSQL。
- 后端可以本地运行并访问 `/api/v1/health/live`。
- 前端可以本地运行，显示 NodeWatch 占位页。
- CI 配置语法正确。
- 代码仓库没有任何真实秘密。

### 阶段停止点

完成后停止，不创建数据库业务表，不做登录。

---

## 62. P1：后端基础、数据库和登录

### Vibe Coding 负责

1. 实现配置加载和结构化日志。
2. 配置 SQLAlchemy、Alembic 和 PostgreSQL。
3. 创建 `users`、`user_sessions`、`audit_logs` migration。
4. 实现首次管理员 bootstrap 逻辑。
5. 实现登录、退出、当前用户接口。
6. 实现 Session Cookie 安全属性。
7. 实现 admin/viewer 权限依赖。
8. 实现 Vue 登录页、路由守卫和基础后台布局。
9. 添加登录成功、失败、退出测试。
10. 增加 `/health/ready` 数据库检查。

### 我需要手动完成

1. 复制 `.env.example` 为 `.env`。
2. 生成 `SECRET_KEY`。
3. 设置本地 bootstrap 管理员密码。
4. 启动数据库并运行 migration。
5. 首次登录后验证 Cookie 行为。

### 验收标准

- 未登录访问后台返回 401 或跳转登录页。
- 正确密码登录成功并设置 HttpOnly Cookie。
- 浏览器刷新后仍保持登录。
- viewer 不能访问管理员接口。
- 数据库中没有明文密码和明文 Session。
- 退出后原 Session 失效。

### 阶段停止点

完成后停止，不创建设备和 Agent Token。

---

## 63. P2：设备管理与 Agent 最小闭环

### Vibe Coding 负责

1. 创建 `devices` 和 `agent_tokens` migration。
2. 实现设备 CRUD。
3. 实现 Token 生成、哈希、只显示一次、撤销和轮换。
4. 实现 Agent bootstrap 和 system-info API。
5. 创建 Agent 配置、身份、基础采集模块。
6. Agent 暂时只采集系统信息和 CPU/内存，不做缓存。
7. 实现前端设备列表基础页和“创建设备”对话框。
8. 实现 Token 一次性展示并要求用户确认已复制。
9. 增加 Token 权限与绑定冲突测试。

### 我需要手动完成

1. 在网页创建设备。
2. 复制一次性 Token 到测试电脑配置文件。
3. 在测试电脑安装 Python 依赖并运行 Agent。
4. 确认网页出现主机名、系统和 Agent 版本。
5. 测试撤销 Token 后 Agent 得到 403。

### 验收标准

- Token 在数据库中只有哈希。
- 同一 Token 不能被不同 Agent 实例抢占。
- Agent 启动后设备 `last_seen_at` 更新。
- Agent 日志不打印完整 Token。
- 禁用设备后拒绝 Agent 上报。

### 阶段停止点

完成后停止，不做历史指标和图表。

---

## 64. P3：指标上报、最新状态和总览

### Vibe Coding 负责

1. 创建 `metric_samples`、`device_latest_metrics` migration。
2. 实现 Agent 单条指标上报。
3. 实现幂等唯一约束和重复样本处理。
4. 实现最新状态 Upsert。
5. Agent 增加 CPU、内存、系统盘、网络速率、uptime 采集。
6. 实现总览接口。
7. 实现设备列表最新指标、状态和筛选。
8. 实现前端总览卡片和设备表格。
9. 添加 10～50 台设备规模下的基础查询测试或数据生成脚本。

### 我需要手动完成

- 让测试 Agent 连续运行至少 10 分钟。
- 观察 CPU、内存、磁盘和网络数据是否合理。
- 在电脑上运行高 CPU 或大量下载，确认数值变化。
- 检查浏览器时间显示是否符合本地时区。

### 验收标准

- 每分钟能保存一个历史样本。
- 同一个 `device_id + collected_at` 不重复。
- 设备列表查询只依赖 latest 表和设备表。
- Agent 停止后页面最后上报时间持续增长。
- API 返回字节整数，前端正确格式化。

### 阶段停止点

完成后停止，不做图表和告警。

---

## 65. P4：历史曲线、多磁盘和设备详情

### Vibe Coding 负责

1. 创建 `disk_latest_metrics` migration。
2. Agent 采集所有可访问磁盘。
3. 实现磁盘最新状态 Upsert。
4. 实现历史查询和分辨率聚合。
5. 实现设备详情页。
6. 使用 ECharts 显示 CPU、内存、网络和系统盘曲线。
7. 支持 1 小时、24 小时、7 天和自定义范围。
8. 对空数据、断线、缺失点给出合理展示。
9. 添加历史查询范围、聚合和时区测试。

### 我需要手动完成

- 对比 Windows 任务管理器或 Linux 工具，检查数值大致一致。
- 检查 Windows 多盘符和 Linux 多挂载点。
- 验证 24 小时图表不会卡顿。
- 检查图表鼠标提示时间为本地时间。

### 验收标准

- 单次图表响应点数受到限制。
- 时间范围过大时自动聚合或明确拒绝。
- 磁盘不可访问不会导致整个 Agent 崩溃。
- 页面刷新和路由直接访问设备详情都正常。

### 阶段停止点

完成后停止，不实现告警。

---

## 66. P5：告警、离线检测和维护模式

### Vibe Coding 负责

1. 创建 `alert_rules`、`alert_events` migration。
2. 创建默认告警规则。
3. 实现持续 CPU、内存、磁盘告警。
4. 实现离线检查调度任务。
5. 实现触发、确认、恢复状态。
6. 实现维护模式和禁用设备排除逻辑。
7. 实现告警列表、筛选和设备详情告警区域。
8. 实现数据清理和 Session 清理任务。
9. 添加告警状态机、重复告警和离线恢复测试。
10. 在启动日志中明确显示调度器是否启用，并检测 Worker 配置风险。

### 我需要手动完成

- 临时把 CPU 阈值调低，验证触发和恢复。
- 停止 Agent 超过离线阈值，验证离线告警。
- 重新启动 Agent，验证告警自动恢复。
- 开启维护模式，确认不产生离线告警。
- 确认告警后检查它仍会在指标恢复时转为 resolved。

### 验收标准

- 单个规则不会重复创建 firing 事件。
- 离线补传旧样本不触发当前 CPU/内存告警。
- 维护设备不产生离线告警。
- 调度任务在本地单进程下稳定运行。

### 阶段停止点

完成后停止，不打包 Agent，不部署阿里云生产环境。

---

## 67. P6：Agent 可靠性、打包和安装

### Vibe Coding 负责

1. 实现 SQLite 离线缓存。
2. 实现单条和批量补传接口。
3. 实现指数退避、抖动和错误分类。
4. 实现缓存上限和过期清理。
5. 实现优雅退出和日志轮转。
6. 编写 Linux systemd 安装脚本。
7. 编写 Windows 任务计划程序安装脚本。
8. 配置 PyInstaller。
9. 配置 GitHub Actions 构建 Windows/Linux Agent 包。
10. 生成 SHA-256 校验文件。
11. 编写 `docs/AGENT_INSTALL.md`。

### 我需要手动完成

- 在 Windows 机器安装并重启，确认自动启动。
- 在一台 Linux 机器或虚拟机测试 systemd。
- 断开网络 5～10 分钟再恢复，确认补传。
- 验证 Token 错误时 Agent 不会每秒刷请求。
- 卸载 Agent 并确认残留文件符合说明。

### 验收标准

- 目标机器不安装 Python 也能运行打包 Agent。
- 网络恢复后按时间顺序补传。
- 缓存不会无限增长。
- Agent 被强制结束后 SQLite 不损坏。
- 安装和卸载文档可由初学者执行。

### 阶段停止点

完成后停止，等待阿里云服务器初始化和部署操作。

---

## 68. P7：阿里云轻量应用服务器部署

### Vibe Coding 负责

1. 创建生产多阶段 Dockerfile。
2. Vue 构建产物复制到后端静态目录。
3. 创建生产 entrypoint：执行 Alembic migration 后启动单 Worker Uvicorn。
4. 容器监听 `0.0.0.0:8000`，但 Compose 只能映射到宿主机 `127.0.0.1:8000`。
5. 创建 `deploy/docker-compose.production.yml`，包含 `app` 与 `db`，PostgreSQL 使用命名卷且不暴露端口。
6. 为两个容器添加 healthcheck、重启策略、资源限制和日志轮转配置。
7. 创建宿主机 Nginx 配置模板 `deploy/nginx-nodewatch.conf.example`。
8. 创建 GitHub Actions 镜像构建与推送流程，使用固定版本 tag。
9. 编写 `docs/ALIYUN_DEPLOY.md`，内容与本文第十三部分一致。
10. 提供生产环境变量示例、部署脚本、数据库备份脚本、smoke test 和回滚步骤。
11. 不直接替我登录阿里云、保存 SSH 私钥、修改域名备案信息或保存生产凭据。

### 我需要手动完成

本阶段必须按照“第十三部分：阿里云轻量应用服务器手动部署指南”操作，包括：

- 创建服务器快照。
- 配置阿里云防火墙和 SSH 密钥。
- 安装 Docker、Nginx 和 Certbot。
- 创建 Swap、生产目录和 `.env`。
- 登录镜像仓库并启动 Docker Compose。
- 配置 Nginx、域名解析、ICP 备案和 HTTPS。
- 首次登录后删除 bootstrap 密码。
- 测试备份、更新和回滚流程。

### 验收标准

- `docker compose ps` 中 App 与 PostgreSQL 均为健康状态。
- 公网只开放 22、80、443；8000 和 5432 无公网规则。
- `curl http://127.0.0.1:8000/api/v1/health/live` 正常。
- Nginx 能通过公网访问登录页，`/api/v1/health/live` 与 `/ready` 正常。
- 正式域名完成备案并启用 HTTPS 后，HTTP 自动跳转 HTTPS，证书续期测试通过。
- 可以登录管理员，且 bootstrap 密码已经从服务器 `.env` 删除。
- Agent 能通过公网 HTTPS 上报。
- 执行 `docker compose restart` 后数据仍在。
- 数据库端口没有暴露，应用端口只绑定回环地址。
- 可以生成一份 `pg_dump` 备份，并在独立临时数据库中验证可恢复。
- 服务器重启后 Docker、Nginx 和 NodeWatch 自动恢复运行。

### 阶段停止点

部署成功后停止，先观察至少 24 小时的 CPU、内存、磁盘、容器日志和 Agent 上报，再进入最终整理。

## 69. P8：质量、文档和简历交付

### Vibe Coding 负责

1. 补齐关键后端、Agent 和前端测试。
2. 修复 lint、typecheck 和构建错误。
3. 完善 README：功能、架构、截图、快速开始、部署、限制。
4. 完善安全和故障排查文档。
5. 创建演示数据 seed 命令，不影响生产真实数据。
6. 添加版本信息和开源许可证。
7. 生成架构图源文件（Mermaid）。
8. 编写简历项目描述和面试讲解提纲。
9. 清理临时代码、调试日志和无用依赖。
10. 创建 `v1.0.0` Release checklist。

### 我需要手动完成

- 截取总览、设备详情和告警页截图。
- 对截图隐藏真实 IP、Token 和个人信息。
- 录制 1～2 分钟演示视频（可选）。
- 将仓库设置为公开并检查提交历史无秘密。
- 在简历中填写自己的真实贡献，不声称不存在的性能或用户规模。

### 验收标准

- 新用户按 README 可以本地运行。
- CI 全部通过。
- 公网演示可访问或有清晰截图。
- README 明确说明项目规模和已知限制。
- Git 历史中没有密码、Token 和数据库地址。

---

# 第十三部分：阿里云轻量应用服务器手动部署指南

## 70. 当前服务器与部署架构

本指南针对当前实际服务器：

| 项目 | 值 |
|---|---|
| 云产品 | 阿里云轻量应用服务器（非托管 Kubernetes 平台） |
| 地域 | 西南 1（成都，中国内地） |
| 操作系统 | Ubuntu 24.04 |
| 规格 | 2 vCPU / 2 GiB 内存 |
| 系统盘 | 40 GiB |
| 公网带宽 | 200 Mbps 峰值 |
| 公网 IP | 使用 `<PUBLIC_IP>` 占位，不写入仓库、README 或公开截图 |

部署架构：

```text
GitHub Repository
  |
  | GitHub Actions: test + build + push fixed image tag
  v
GHCR / OCI Image Registry
  |
  | docker compose pull
  v
阿里云轻量应用服务器（Ubuntu 24.04）
  |
  +-- Nginx（宿主机，公网 80/443）
  |      |
  |      `--> 127.0.0.1:8000
  |
  +-- Docker Compose
         +-- app: NodeWatch 镜像，单副本、单 Worker
         `-- db: PostgreSQL，Docker 内部网络，命名卷 postgres_data
```

MVP 不使用阿里云 RDS、SLB、Kubernetes、宝塔面板或 1Panel。这样成本和复杂度最低，也便于理解完整部署链路。数据库与应用位于同一台服务器，因此快照和逻辑备份都必须纳入日常操作。

## 71. 部署前准备与重要限制

我需要准备：

- 阿里云控制台访问权限。
- 当前轻量应用服务器。
- GitHub 仓库与可拉取的固定版本镜像。
- SSH 密钥对；不建议长期只用密码登录。
- 两组生产随机值：`SECRET_KEY`、`POSTGRES_PASSWORD`。
- 可选的已备案域名；服务器在中国内地，域名正式对外提供 Web 服务前需要完成 ICP 备案。
- 服务器外部的备份位置，后续可使用私有 OSS Bucket 或本地加密保存。

部署前本地检查：

```bash
# 后端测试
cd backend
pytest

# 前端测试和构建
cd ../frontend
npm ci
npm run typecheck
npm run test
npm run build

# 生产镜像构建
cd ..
docker build -f deploy/Dockerfile -t nodewatch:local .

# 本地生产 Compose 配置检查
docker compose -f deploy/docker-compose.production.yml config
```

人工检查：

- Dockerfile 不执行 `COPY .env`。
- `.dockerignore` 包含 `.env`、`.git`、缓存、本地数据库和测试产物。
- 镜像内没有 SSH 私钥、Token、数据库备份或真实配置。
- 镜像启动后容器内部监听 8000。
- 镜像使用固定 tag，例如 `v0.1.0`，不把 `latest` 当作唯一生产版本。

## 72. 阿里云控制台初始化

### 72.1 创建初始化前快照

在对服务器安装软件或修改 SSH 前：

1. 打开轻量应用服务器控制台。
2. 进入当前实例。
3. 打开 **磁盘** 页签。
4. 对系统盘创建快照，名称示例：`nodewatch-before-init-20260714`。
5. 等待快照状态完成后再继续。

每次重要升级、Docker 大版本变更或破坏性 migration 前都应创建新快照。快照是整盘恢复手段，不替代 PostgreSQL 逻辑备份。

### 72.2 配置轻量服务器防火墙

只保留业务真正需要的入方向端口：

| 协议 | 端口 | 来源 | 用途 |
|---|---:|---|---|
| TCP | 22 | 优先为管理员可信公网 IP/32 | SSH |
| TCP | 80 | `0.0.0.0/0` | HTTP、证书验证、跳转 HTTPS |
| TCP | 443 | `0.0.0.0/0` | HTTPS 网站和 Agent 上报 |

要求：

- 不添加 8000、5432、2375、2376 或管理面板端口的公网规则。
- 若当前网络公网 IP 经常变化，可以暂时开放 22，但完成部署后应收紧或改用阿里云 Workbench。
- 修改 SSH 规则前保持当前会话，并用第二个终端验证新规则，避免把自己锁在服务器外。

### 72.3 绑定 SSH 密钥

1. 在阿里云控制台进入 **密钥对**。
2. 创建或导入 RSA 密钥对。
3. 绑定到当前 Linux 轻量应用服务器。
4. 按控制台提示重启实例。
5. 私钥只保存在自己的电脑，不上传服务器和仓库。

连接示例：

```bash
chmod 600 ~/.ssh/aliyun-nodewatch.pem
ssh -i ~/.ssh/aliyun-nodewatch.pem root@<PUBLIC_IP>
```

轻量应用服务器 Linux 默认管理员用户名通常为 `root`。首次进入后执行 `whoami` 和 `cat /etc/os-release`，确认账号与系统确实符合预期。

## 73. Ubuntu 初始化与安全加固

以下命令先以 `root` 执行：

```bash
apt update
apt full-upgrade -y
apt install -y ca-certificates curl gnupg git nginx certbot python3-certbot-nginx jq vim
systemctl enable --now nginx

# 若系统提示需要重启，先保持控制台可用，再执行 reboot
[ -f /var/run/reboot-required ] && echo "reboot required"
```

创建日常部署用户：

```bash
adduser deploy
usermod -aG sudo deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
```

打开第二个本地终端验证：

```bash
ssh -i ~/.ssh/aliyun-nodewatch.pem deploy@<PUBLIC_IP>
sudo whoami
```

只有确认 `deploy` 密钥登录和 `sudo` 均正常后，才考虑禁用 SSH 密码登录。创建 `/etc/ssh/sshd_config.d/99-nodewatch.conf`：

```text
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin prohibit-password
```

检查并重载：

```bash
sudo sshd -t
sudo systemctl reload ssh
```

不要在唯一 SSH 会话中直接禁用密码并关闭窗口。

### 73.1 创建 2 GiB Swap

2 GiB 内存较紧，建议创建 2 GiB Swap 作为瞬时内存保护：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-nodewatch.conf
sudo sysctl --system
free -h
```

Swap 不是内存替代品。若持续使用大量 Swap，应降低容器内存、缩短数据查询或升级服务器。

## 74. 安装 Docker Engine 与 Compose

使用 Docker 官方 APT 仓库，不使用不明一键脚本：

```bash
sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc || true
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker compose version
```

把部署用户加入 Docker 组：

```bash
sudo usermod -aG docker deploy
```

退出 SSH 后重新登录，再执行：

```bash
docker version
docker compose version
```

注意：`docker` 组近似拥有 root 权限，只把可信部署用户加入该组。

### 74.1 配置 Docker 日志轮转

创建 `/etc/docker/daemon.json`：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

应用配置：

```bash
sudo systemctl restart docker
sudo systemctl status docker --no-pager
```

## 75. 准备生产目录和环境变量

以 `deploy` 用户执行：

```bash
sudo mkdir -p /opt/nodewatch/deploy /opt/nodewatch/backups
sudo chown -R deploy:deploy /opt/nodewatch
cd /opt/nodewatch/deploy
```

从仓库复制以下文件到服务器：

- `deploy/docker-compose.production.yml` -> `/opt/nodewatch/deploy/docker-compose.yml`
- `deploy/production.env.example` -> `/opt/nodewatch/deploy/.env`
- `deploy/nginx-nodewatch.conf.example` -> 暂存，后续复制到 Nginx。
- `deploy/scripts/backup.sh`、`smoke-test.sh`、`deploy.sh`。

编辑并保护 `.env`：

```bash
cd /opt/nodewatch/deploy
cp production.env.example .env
chmod 600 .env
nano .env
```

生成随机值：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

首次仅用公网 IP 做 HTTP 验证时：

```dotenv
ALLOWED_HOSTS=<PUBLIC_IP>
SESSION_COOKIE_SECURE=false
```

完成域名、备案和 HTTPS 后必须改为：

```dotenv
ALLOWED_HOSTS=monitor.example.com
SESSION_COOKIE_SECURE=true
```

生产 Compose 必须满足以下关键结构：

```yaml
services:
  db:
    image: postgres:17-alpine
    restart: unless-stopped
    env_file: .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
    mem_limit: 768m
    cpus: 0.75

  app:
    image: ${NODEWATCH_IMAGE}
    restart: unless-stopped
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live')"]
      interval: 30s
      timeout: 5s
      retries: 5
    mem_limit: 512m
    cpus: 0.75

volumes:
  postgres_data:
```

禁止为 `db` 添加 `ports`；禁止把 App 映射为 `8000:8000`。

## 76. 首次启动 Docker Compose

公开镜像可以直接拉取。私有 GHCR 镜像需要使用只读 Package Token：

```bash
read -s -p 'GHCR token: ' GHCR_TOKEN; echo
echo "$GHCR_TOKEN" | docker login ghcr.io -u '<GITHUB_USERNAME>' --password-stdin
unset GHCR_TOKEN
```

Token 不得写入 shell 历史、文档或截图。上面的 `read -s` 不回显 Token，登录成功后立即 `unset`。

启动前检查：

```bash
cd /opt/nodewatch/deploy
docker compose config --quiet
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=100 db
```

本机健康检查：

```bash
curl -fsS http://127.0.0.1:8000/api/v1/health/live
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
```

检查端口：

```bash
sudo ss -lntp | grep -E ':(22|80|443|8000|5432)\b'
```

预期：

- 8000 只监听 `127.0.0.1`。
- 5432 不在宿主机监听列表中。
- 80 由 Nginx 监听。
- 443 在启用 HTTPS 后由 Nginx 监听。

## 77. 配置宿主机 Nginx 与首次 HTTP 验证

创建 `/etc/nginx/sites-available/nodewatch`：

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name _;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

启用配置：

```bash
sudo ln -sfn /etc/nginx/sites-available/nodewatch /etc/nginx/sites-enabled/nodewatch
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

通过浏览器短时访问：

```text
http://<PUBLIC_IP>/
http://<PUBLIC_IP>/api/v1/health/live
```

此阶段仅用于确认链路，不算最终生产完成。HTTP 会明文传输 Cookie 和 Agent Token，因此不要长期运行真实 Agent，也不要在 HTTP 环境使用真实敏感数据。

首次登录后：

1. 使用 bootstrap 管理员登录。
2. 立即修改管理员密码。
3. 删除 `/opt/nodewatch/deploy/.env` 中的 `BOOTSTRAP_ADMIN_PASSWORD`。
4. 执行：

```bash
cd /opt/nodewatch/deploy
docker compose up -d --force-recreate app
docker compose logs --tail=100 app
```

5. 重新登录确认管理员仍可使用。

## 78. 域名、ICP 备案和 HTTPS

当前服务器位于成都，属于中国内地地域。使用域名正式对外提供 Web 服务前，必须在接入商平台完成 ICP 备案。不要通过改成 8080、8443 等非标准端口规避备案；端口不会改变备案要求。

备案与上线顺序：

1. 准备已实名认证的域名。
2. 在阿里云提交 ICP 备案，关联当前轻量应用服务器。
3. 备案通过后，在 DNS 中添加 A 记录：

```text
monitor.example.com -> <PUBLIC_IP>
```

4. 等待 DNS 生效：

```bash
getent hosts monitor.example.com
```

5. 修改 Nginx：

```nginx
server_name monitor.example.com;
```

6. 检查并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

7. 确认 `http://monitor.example.com` 已能访问后申请证书：

```bash
sudo certbot --nginx -d monitor.example.com
sudo certbot renew --dry-run
```

8. 修改 `/opt/nodewatch/deploy/.env`：

```dotenv
ALLOWED_HOSTS=monitor.example.com
SESSION_COOKIE_SECURE=true
```

9. 重建 App 容器：

```bash
cd /opt/nodewatch/deploy
docker compose up -d --force-recreate app
```

10. 验证：

```bash
curl -I https://monitor.example.com/
curl -fsS https://monitor.example.com/api/v1/health/live
```

必须确认：

- HTTP 自动跳转到 HTTPS。
- 浏览器证书有效且域名匹配。
- 登录 Cookie 仅通过 HTTPS 发送。
- `certbot renew --dry-run` 成功。

## 79. 连接 Agent 到公网环境

HTTPS 完成后再连接正式 Agent：

1. 在网页创建设备。
2. 复制只显示一次的 Agent Token。
3. 配置：

```toml
server_url = "https://monitor.example.com"
agent_token = "nwa_xxxxxxxxx"
collect_interval_seconds = 60
request_timeout_seconds = 10
verify_tls = true
```

4. 前台运行 Agent，观察 3～5 个采样周期。
5. 网页确认设备在线、指标更新和历史曲线出现。
6. 再安装为 systemd 或 Windows 计划任务。
7. 不要把公网 IP、完整 Token 或真实主机名放入公开截图。

## 80. 更新、回滚与服务器重启验证

### 80.1 正常更新

每次发布：

1. 合并代码并确保 CI 通过。
2. 创建版本 tag，例如 `v0.1.1`。
3. 等待 GitHub Actions 推送固定版本镜像。
4. 在重要 migration 前执行 `pg_dump`，必要时再创建阿里云快照。
5. 编辑 `.env` 中的 `NODEWATCH_IMAGE` 为新 tag。
6. 执行：

```bash
cd /opt/nodewatch/deploy
docker compose pull app
docker compose up -d app
docker compose ps
docker compose logs --tail=200 app
./smoke-test.sh https://monitor.example.com
```

7. 验证健康接口、登录、Agent 上报和图表。
8. 观察至少一个完整采样周期。

不要只部署 `latest`，否则无法明确当前运行版本。

### 80.2 应用回滚

1. 把 `.env` 中 `NODEWATCH_IMAGE` 改回上一个固定 tag。
2. 执行 `docker compose pull app && docker compose up -d app`。
3. 验证健康接口与日志。

数据库默认不自动执行 `alembic downgrade`。优先使用向前兼容 migration；删除字段等破坏性变化采用两次发布。真正做数据库降级或阿里云快照回滚前必须备份并人工确认。

### 80.3 重启验证

```bash
sudo reboot
```

服务器恢复后检查：

```bash
systemctl is-active docker nginx
cd /opt/nodewatch/deploy
docker compose ps
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
```

## 81. PostgreSQL 备份与恢复演练

最低要求采用三层保护：

1. PostgreSQL 每日逻辑备份。
2. 重要变更前阿里云系统盘快照。
3. 定期把备份复制到服务器外的私有位置；同盘备份不能防止整盘损坏或实例丢失。

手工备份：

```bash
cd /opt/nodewatch/deploy
mkdir -p /opt/nodewatch/backups
BACKUP="/opt/nodewatch/backups/nodewatch-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip > "$BACKUP"
chmod 600 "$BACKUP"
ls -lh "$BACKUP"
```

实际脚本不能依赖当前 shell 已存在 `POSTGRES_USER`；`deploy/scripts/backup.sh` 应从受保护的 `.env` 安全读取变量，并在失败时返回非零状态。

本机只保留最近 7 份：

```bash
find /opt/nodewatch/backups -type f -name 'nodewatch-*.sql.gz' -mtime +7 -delete
```

可以使用 root 的 cron 每天执行：

```text
15 3 * * * /opt/nodewatch/deploy/scripts/backup.sh >> /var/log/nodewatch-backup.log 2>&1
```

恢复演练必须在独立临时数据库或本地环境中完成，禁止直接覆盖生产数据库。演练流程：

1. 创建临时 PostgreSQL 数据库。
2. 解压备份并导入。
3. 运行关键表计数与登录/设备查询测试。
4. 记录恢复耗时和问题。
5. 删除临时数据库。

阿里云快照回滚会把整个系统盘恢复到快照时间点，快照之后的数据库、配置和日志都会丢失，因此只能作为严重故障的最后恢复手段。

# 第十四部分：测试计划

## 82. 后端关键测试

必须覆盖：

- 密码验证和 Session 生命周期。
- admin/viewer 权限。
- Agent Token 生成、哈希、撤销和绑定。
- 指标幂等。
- latest Upsert。
- 历史范围查询和聚合。
- CPU/内存持续规则。
- 磁盘回差。
- 离线触发和恢复。
- 维护模式排除。
- 清理任务只删除保留期外数据。

## 83. Agent 关键测试

- CPU、内存和磁盘采集器使用 mock。
- 网络累计计数差值和计数重置。
- SQLite 保存、读取、删除和上限。
- 401、403、422、429、500、超时处理。
- 批量补传部分重复。
- 配置缺失和无效配置错误信息。
- Token 日志脱敏。

## 84. 前端关键测试

- 未登录路由跳转。
- 登录失败提示。
- 权限控制。
- 设备列表空状态、加载和错误状态。
- 指标格式化。
- 时间转换。
- 告警状态显示。

## 85. 手动测试清单

- Windows Agent。
- Linux Agent。
- 网络断开和恢复。
- Agent Token 撤销。
- 设备禁用。
- 维护模式。
- CPU/内存/磁盘告警。
- 应用重启。
- 数据库重启。
- Docker Compose 应用更新和服务器重启。
- 自定义域名（如果使用）。
- 移动端浏览器基本查看。

---

# 第十五部分：故障排查

## 86. Docker Compose 服务无法启动

检查顺序：

1. `docker compose config --quiet` 是否通过。
2. 镜像是否可以拉取，CPU 架构是否匹配。
3. `docker compose ps -a` 中容器退出码和健康状态。
4. `docker compose logs --tail=200 app db` 是否有明确错误。
5. App entrypoint、Alembic migration 和环境变量是否正确。
6. `DATABASE_URL` 的密码是否与 PostgreSQL 初始化密码一致。
7. 端口 8000 是否被其他进程占用。
8. `docker inspect <container> --format '{{.State.OOMKilled}}'` 是否为 true。
9. `free -h`、`df -h`、`docker system df` 是否显示内存或磁盘不足。
10. PostgreSQL 命名卷是否存在且权限正常。

不要直接执行 `docker compose down -v`，该命令会删除数据库卷。

## 87. 公网 URL 502、超时或 HTTPS 异常

按链路逐层检查：

1. 阿里云轻量服务器防火墙是否放行 80/443。
2. `sudo ss -lntp` 是否显示 Nginx 监听相应端口。
3. `sudo nginx -t` 是否通过，`systemctl status nginx` 是否正常。
4. `curl http://127.0.0.1:8000/api/v1/health/live` 是否正常。
5. App 是否只绑定宿主机回环地址，Nginx `proxy_pass` 是否指向同一端口。
6. Nginx 错误日志：`sudo tail -n 100 /var/log/nginx/error.log`。
7. 域名 A 记录是否解析到当前公网 IP。
8. 中国内地服务器的域名是否已完成 ICP 备案。
9. Certbot 证书路径和 Nginx server_name 是否正确。
10. 不要同时改端口、域名、证书和启动命令；一次只排查一个变量。

## 88. Agent 返回 401/403

- Token 是否复制完整。
- 配置文件是否有不可见空格或引号。
- Token 是否撤销或过期。
- Token 是否已经绑定到另一 Agent 实例。
- 设备是否被禁用。
- Agent URL 是否指向正确环境。

## 89. 设备频繁在线/离线切换

- 采样周期和离线阈值是否合理。
- 被监控设备是否休眠。
- Agent 是否被系统杀死。
- 网络是否不稳定。
- 服务器和客户端时钟是否异常。
- 离线判断应使用服务端 `last_seen_at`，不能只信客户端时间。

## 90. 告警重复

- `docker compose ps` 是否出现多个 App 容器。
- Uvicorn 是否启动多个 Worker。
- APScheduler 是否被初始化两次。
- 是否存在同一规则多个未恢复事件。
- 创建告警是否放在事务中。

## 91. 图表没有数据或时间错误

- API 的 from/to 是否为 UTC。
- 前端是否重复转换时区。
- 数据库是否保存 timezone-aware 时间。
- 设备 ID 和范围是否正确。
- 采样是否实际进入 `metric_samples`。

---

# 第十六部分：发布和简历要求

## 92. README 必须包含

- 项目简介。
- 功能截图。
- 架构图。
- 技术栈。
- 数据流。
- 本地启动步骤。
- Agent 安装步骤。
- 阿里云轻量应用服务器部署说明。
- 安全设计。
- 数据保留策略。
- 已知限制。
- 路线图。
- 许可证。

## 93. 演示数据

提供开发 seed 命令：

```bash
python -m app.cli seed-demo
```

要求：

- 只在 `APP_ENV != production` 时默认允许。
- 生产必须显式确认。
- 使用虚构设备和指标。
- 不把真实 Token 写入 seed。

## 94. 简历描述模板

> 独立设计并开发 NodeWatch 轻量级跨平台主机监控平台，使用 Python Agent 采集 Windows/Linux 设备的 CPU、内存、磁盘、网络和系统信息，并通过 HTTPS 与独立设备 Token 定期上报至 FastAPI 服务端。

> 使用 Vue 3、TypeScript 和 ECharts 构建设备总览、历史指标曲线和告警面板；使用 PostgreSQL 保存设备、最新状态及历史样本，实现指标幂等写入、离线检测、持续阈值告警和告警恢复。

> 为 Agent 实现 SQLite 离线缓存、指数退避、批量补传和跨平台打包，并通过 GitHub Actions 构建镜像，在阿里云轻量应用服务器上使用 Docker Compose、Nginx 和 PostgreSQL 完成公网部署、HTTPS、备份与回滚。

实际写简历时，只保留自己真正完成并能够解释的内容。

## 95. 面试重点

需要能解释：

1. 为什么首页使用 latest 表，而不是每次查询历史表最后一条。
2. 为什么设备离线由服务端判断。
3. 为什么 Agent 先写本地缓存再上传。
4. 如何保证重复上报幂等。
5. 如何区分离线补传和实时样本，避免旧数据触发当前告警。
6. 如何防止 CPU 瞬时峰值造成误报。
7. 如何保护 Agent Token。
8. 为什么 2 核 2 GiB 单机部署使用单副本和单 Worker。
9. 数据增长后如何做保留和降采样。
10. 如果未来需要多副本，如何迁移定时任务。

---

# 第十七部分：直接交给 Vibe Coding 的主提示词

## 96. 主提示词

把本文件放在仓库根目录或 `docs/DEVELOPMENT_SPEC.md`，然后向编程代理发送：

```text
你是 NodeWatch 项目的主程。请先完整阅读 docs/DEVELOPMENT_SPEC.md、README.md、PROGRESS.md 和 DECISIONS.md。

严格按照开发文档执行：
1. 本次只执行我指定的阶段，不得提前实现后续阶段。
2. 优先完成最小、可测试、可运行的实现，不得擅自引入 Redis、Celery、Kafka、Prometheus、Grafana、Kubernetes 或微服务。
3. 不得硬编码或提交任何真实密码、Token、数据库连接串和密钥。
4. 所有数据库变化必须使用 Alembic migration。
5. 完成后运行 lint、类型检查、测试和构建。
6. 更新 PROGRESS.md 与 DECISIONS.md。
7. 按文档规定的“阶段完成报告格式”回复，然后停止，等待我验收。
8. 当步骤必须由我在本机、GitHub、阿里云控制台或云服务器手动完成时，不要假装已经完成。请明确标为“需要用户操作”，给出逐步命令、要复制的值、预期结果和失败排查。

现在执行阶段：P0。
```

每次验收后，只把最后一行改成下一阶段，例如：

```text
现在执行阶段：P1。
```

## 97. 阶段验收回复模板

我确认阶段通过时使用：

```text
P0 验收通过。请先读取当前仓库的 PROGRESS.md 和 DECISIONS.md，然后严格执行 DEVELOPMENT_SPEC.md 中的 P1。不要实现 P2 或后续内容。完成后按阶段报告格式停止。
```

需要修复时使用：

```text
P0 暂不通过。请只修复以下问题，不开始 P1：
1. ...
2. ...

修复后重新运行相关测试，更新 PROGRESS.md，并重新提交 P0 完成报告。
```

---

# 第十八部分：个人学习要求

## 98. 每个阶段我需要掌握的知识

### P0

- Git 基础。
- Python 虚拟环境。
- npm 和 Vite。
- Docker Compose 基础。

### P1

- HTTP Cookie 和 Session。
- 密码哈希。
- SQLAlchemy Model 和 Alembic migration。
- Vue Router 和 Pinia。

### P2

- Bearer Token。
- Python 系统信息采集。
- 客户端和服务端认证区别。

### P3

- REST API。
- Upsert。
- 唯一约束和幂等。
- 网络速率计算。

### P4

- 时间范围查询。
- UTC 和本地时区。
- 数据聚合。
- ECharts。

### P5

- 状态机。
- 定时任务。
- 告警去重。
- 数据保留。

### P6

- SQLite。
- 重试和指数退避。
- systemd 和 Windows 计划任务。
- PyInstaller。

### P7

- Docker 多阶段构建。
- 环境变量和秘密管理。
- Docker 内部网络、PostgreSQL 命名卷和数据库备份。
- 域名、DNS、ICP 备案和 HTTPS。

### P8

- CI/CD。
- 项目文档。
- 演示和面试表达。

## 99. 学习纪律

Vibe Coding 可以写代码，但我必须：

- 阅读每个 migration。
- 阅读 Agent 上传和缓存核心逻辑。
- 能手动解释每张数据库表。
- 能通过 Swagger 或 curl 调用主要 API。
- 能自己完成一次阿里云轻量应用服务器部署。
- 能独立排查至少一次 Agent 401、服务 502 或数据库连接错误。
- 不把“AI 生成了”当作无法解释代码的理由。

---

# 第十九部分：后续版本路线图

## 100. v1.1 可选

- 邮件或 Webhook 告警通知。
- 设备标签和分组。
- 告警静默时间。
- Agent 自动检查新版本。
- 自定义数据保留策略。

## 101. v1.2 可选

- 小时聚合表。
- 独立调度 worker、systemd timer 或专门的调度容器。
- 应用多副本。
- 数据库备份自动上传私有对象存储。
- API Key 轮换提醒。

## 102. v2.0 才考虑

- 多租户。
- 容器监控。
- 自定义指标。
- 插件式采集器。
- 更复杂的告警表达式。

---

# 第二十部分：阿里云与部署官方参考

以下内容用于部署时核对当前控制台界面和行为。云平台、Docker 和证书工具可能更新，执行前以官方文档为准：

- [阿里云轻量应用服务器产品文档](https://help.aliyun.com/zh/simple-application-server/)
- [轻量应用服务器防火墙设置](https://help.aliyun.com/zh/simple-application-server/user-guide/manage-the-firewall-of-a-server)
- [远程连接 Linux 轻量应用服务器](https://help.aliyun.com/zh/simple-application-server/user-guide/connect-to-linux-server-remotely)
- [管理轻量应用服务器密钥对](https://help.aliyun.com/zh/simple-application-server/user-guide/manage-key-pairs-linux)
- [管理轻量应用服务器快照](https://help.aliyun.com/zh/simple-application-server/user-guide/manage-snapshots)
- [轻量应用服务器网站 ICP 备案](https://help.aliyun.com/zh/simple-application-server/user-guide/apply-for-an-icp-filing-for-a-domain-name)
- [在 Nginx 服务器安装 SSL 证书](https://help.aliyun.com/zh/ssl-certificate/install-ssl-certificates-on-nginx-servers-or-tengine-servers)
- [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose plugin](https://docs.docker.com/compose/install/linux/)
- [Docker Linux post-installation](https://docs.docker.com/engine/install/linux-postinstall/)
- [Nginx reverse proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Certbot Nginx instructions](https://certbot.eff.org/instructions?ws=nginx&os=snap)

# 附录 A：最终完成定义

只有同时满足以下条件，项目才算完成：

- [ ] Windows Agent 可以运行。
- [ ] Linux Agent 可以运行。
- [ ] Agent 可以在断网后缓存并补传。
- [ ] 管理员可以创建设备和一次性 Token。
- [ ] 总览和设备列表显示真实数据。
- [ ] 设备详情显示历史曲线。
- [ ] CPU、内存、磁盘和离线告警可触发并恢复。
- [ ] viewer 权限有效。
- [ ] 数据保留任务有效。
- [ ] 测试和 CI 通过。
- [ ] 阿里云轻量应用服务器公网部署成功。
- [ ] 应用和数据库重启后数据不丢失。
- [ ] bootstrap 密码已从生产环境变量删除。
- [ ] README、部署、Agent 安装和故障排查文档齐全。
- [ ] Git 历史中不存在秘密。
- [ ] 我可以在不看文档的情况下解释核心架构和关键取舍。

# 附录 B：部署人工操作记录模板

```markdown
## 环境
- 部署日期：
- 阿里云产品：轻量应用服务器
- 地域：西南 1（成都）
- 操作系统：Ubuntu 24.04
- 服务器规格：2 vCPU / 2 GiB / 40 GiB
- 应用名称：
- 数据库名称：
- 应用镜像版本：
- 公网域名：

## 资源
- App CPU/内存限制：
- PostgreSQL CPU/内存限制：
- PostgreSQL 卷：
- Swap：
- 系统盘剩余空间：

## 验证
- [ ] live health
- [ ] ready health
- [ ] 管理员登录
- [ ] 创建设备
- [ ] Agent bootstrap
- [ ] 指标上报
- [ ] 历史曲线
- [ ] 告警触发
- [ ] 告警恢复
- [ ] Docker Compose 更新应用
- [ ] Nginx 配置测试和重载
- [ ] HTTPS 证书续期测试
- [ ] 数据仍存在

## 敏感信息处理
- [ ] 没有把数据库密码写入仓库
- [ ] 没有把 Token 放入截图
- [ ] 已删除 bootstrap 密码
- [ ] 已检查 Git 历史

## 问题与处理
- 问题：
- 原因：
- 处理：
```
