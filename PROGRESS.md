# NodeWatch 开发进度

## 当前阶段

P8：质量、文档和简历交付（已验收，项目完成）。

## 已完成

- 使用 Pydantic Settings 加载配置，输出结构化 JSON 日志和请求 ID。
- 接入 SQLAlchemy、Alembic 与 PostgreSQL。
- 创建 `users`、`user_sessions`、`audit_logs` 三张业务表。
- 数据库为空时自动创建首个管理员。
- 实现登录、退出、当前用户以及 admin/viewer 权限依赖。
- 使用 HttpOnly Session Cookie，并只在数据库保存 Session 哈希。
- 实现 Vue 登录页、路由守卫和基础后台布局。
- 实现数据库与迁移版本就绪检查。
- 添加后端认证测试、健康检查测试和前端组件测试。
- CI 使用独立 PostgreSQL 测试库并自动执行迁移。
- 创建 `devices` 和 `agent_tokens` 表及 P2 migration。
- 实现设备 CRUD、Token 生成、轮换、撤销和只显示一次。
- 实现 Agent bootstrap、实例绑定和 system-info 上报。
- 实现 Python Agent 配置、持久身份和系统信息/CPU/内存采集。
- 实现前端设备列表、创建设备和 Token 保存确认弹窗。
- CI 增加 Agent lint 和测试任务。
- 创建 `metric_samples` 和 `device_latest_metrics` 及 P3 migration。
- 实现单条指标幂等上报、历史写入和 latest upsert。
- Agent 采集 CPU、内存、系统盘、网络速率和 uptime，并按服务端周期上报。
- 实现总览统计、在线/离线计算、CPU/内存 Top 5。
- 设备列表展示 CPU、内存、系统盘、网络速率和动态状态。
- 增加 50 台设备规模测试和 Agent 采集范围测试。
- 创建 `disk_latest_metrics` 和 P4 migration。
- Agent 采集所有可访问磁盘并对单盘异常容错。
- 实现磁盘 latest upsert、历史 raw/5m/1h 聚合和 1500 点限制。
- 实现设备详情、1 小时/24 小时/7 天/自定义范围与 ECharts 曲线。
- 实现历史空状态、缺失点断线和浏览器本地时间轴。
- 创建 `alert_rules`、`alert_events` 和 P5 migration，并初始化 4 条默认规则。
- 实现持续 CPU/内存/磁盘告警、磁盘回差、去重、确认和恢复状态机。
- 实现离线检查、维护/禁用排除、重新上线恢复。
- 实现 APScheduler 离线任务、Session 和原始指标清理。
- 实现告警/规则 API、告警页、筛选和设备详情告警区域。
- 实现 Agent SQLite WAL 离线队列、按采集时间批量补传、容量与过期清理。
- 实现网络/服务端错误指数退避与抖动、认证错误长退避、优雅退出和日志轮转。
- 实现单条与批量指标入口，并保持补传幂等、latest 防旧数据覆盖和实时告警隔离。
- 配置 PyInstaller、Windows 计划任务和 Linux systemd 安装卸载脚本。
- 配置 GitHub Actions 构建 Windows/Linux 独立包并生成 SHA-256。
- 完成初学者可执行的 Agent 安装、校验、断网验证、升级和卸载文档。
- 修复 Windows Agent 覆盖安装时旧进程占用可执行文件的问题，安装脚本会注销旧任务、结束旧进程并等待文件解锁。
- 实现 Vue/FastAPI 同源静态托管、Host 白名单和容器内管理员密码修改命令。
- 创建生产多阶段 Dockerfile、Alembic entrypoint 和固定单 Worker 启动流程。
- 创建仅回环映射 App、内部 PostgreSQL、命名卷、健康检查、资源限制和日志轮转的生产 Compose。
- 创建 Nginx、生产环境变量、部署、冒烟、备份、临时库恢复演练和回滚脚本。
- 创建固定 Git tag 触发、验证通过后推送 GHCR 的镜像发布流程。
- 完成阿里云快照、SSH、Swap、Docker、Nginx、公网 IP HTTPS、备份和重启部署文档。
- P8 添加可重复的演示数据命令，使用固定演示 UUID、保留真实设备，并在生产环境拒绝运行。
- P8 将后端、Agent、前端和部署模板版本统一为 `1.0.0`，保留 MIT License。
- P8 重写 README，补齐 Mermaid 架构源文件、安全公开检查、常见故障、简历面试提纲、截图规则和 Release checklist。
- P8 创建并推送 `v1.0.0` tag，发布 GHCR 应用与 PostgreSQL 固定版本镜像，并创建 GitHub Release。
- P8 将阿里云生产环境升级到 v1.0.0，App 与 PostgreSQL 均健康，冒烟测试及公网网页验收通过。

## 待完成

- 无。

## 阶段状态

P6、P7、P8 均已由项目所有者验收通过。P8 的测试、演示数据、版本信息、README、架构、安全、排错、简历、截图、公开仓库、`v1.0.0` tag、GHCR 镜像、GitHub Release、Agent 附件、异机备份、恢复演练和生产复查均已完成；阿里云生产环境已升级到 v1.0.0 并通过公网人工验收。v1.0.0 Release checklist 已全部勾选，项目按开发文档完成交付。项目所有者明确不进行完整 24 小时观察，现有整机重启、健康检查、HTTPS、备份恢复、回滚、公网 Agent 缓存补传和实时上报证据作为 P7 稳定性验收依据，不声称已完成 24 小时稳定性测试。

## 验证记录

- P8 交付提交 `0b90aa5`：已推送到 `main`，GitHub Actions CI 全部绿色。
- P8 公开展示：仓库已设为 Public，公开前已完成当前工作树、Git 历史、截图和敏感文件名检查。
- P8 后端 Ruff 与 pytest：通过，21 个后端测试全部通过。
- P8 Agent Ruff、pytest 与版本命令：通过，5 个 Agent 测试全部通过，版本为 `1.0.0`。
- P8 前端 TypeScript、5 个 Vitest 测试与 Vite 生产构建：通过；设备详情 chunk 大于 500 kB 为非阻塞性能提示，记录为后续拆包优化项。
- P8 当前工作树与完整 Git 历史均未发现真实公网 IP、完整 Agent Token、私钥正文或被跟踪的敏感文件名。
- P8 使用独立 `nodewatch_demo` 数据库生成设备总览、24 小时历史曲线和告警页截图；三张截图只包含演示设备并已通过人工脱敏验收。
- P8 正式发布：带说明的 `v1.0.0` tag 已推送，发布镜像工作流绿色，GitHub Release 已公开。
- P8 升级前备份：生成 `/opt/nodewatch/backups/nodewatch-20260716T164809Z.sql.gz`，复制到 Windows 异机目录后大小为 39,889 字节，SHA-256 为 `2D60589A24EEFB4629FD0B3C9F2BD2FF63CDC88AAA762074F080D3AE4EB47C5E`；恢复到临时数据库并验证包含 11 张 public 表。
- P8 生产升级：App 使用 `ghcr.io/1799564322/nodewatch:v1.0.0`，PostgreSQL 使用 `ghcr.io/1799564322/nodewatch-postgres:17-alpine-v1.0.0`，两者均为 healthy，部署脚本冒烟测试通过。
- P8 公网验收：项目所有者已确认登录、设备在线状态、最后上报、历史曲线和告警页面正常。
- P8 发布后复查：App/DB v1.0.0 均为 healthy，就绪接口迁移版本为 `20260715_05`，公网 IP 证书有效，最近 15 分钟日志未发现严重错误，最新 39K 备份仍在服务器且权限为 `600`。
- P8 Release 附件：GitHub Release 已附加 `nodewatch-agent-linux-x86_64.zip` 与 `nodewatch-agent-windows-x86_64.zip`；压缩包内包含可执行程序、安装脚本、示例配置和 SHA-256 文件，Release 说明已补充升级与回滚范围。
- P8 最终验收：提交 `0420c6c` 已推送到 `main` 且最终 CI 全部绿色，项目所有者于 2026-07-17 确认 P8 验收通过。
- Alembic 开发库和测试库迁移：通过。
- 后端 Ruff：通过。
- 后端 pytest：6 个测试通过。
- Uvicorn 实际启动、存活与就绪检查：通过。
- 登录、读取当前用户、退出的真实 HTTP 链路：通过。
- 前端 TypeScript 类型检查：通过。
- 前端 Vitest：2 个测试通过。
- 前端 Vite 生产构建：通过。
- P2 Alembic migration 与模型一致性：通过。
- 后端设备、Token、绑定冲突、撤销和禁用测试：9 个后端测试全部通过。
- Agent Ruff 与身份持久化测试：通过。
- 前端设备空状态测试：3 个前端测试全部通过。
- 真实 Windows Agent bootstrap 与 system-info：均返回 200，网页正确显示主机信息。
- 撤销真实 Token 后 Agent bootstrap：返回 403，完整 Token 未进入日志。
- P4 migration/model 一致性：通过。
- 后端历史范围、自动聚合、多磁盘与 31 天限制：12 个后端测试全部通过。
- 前端设备详情、空数据和直接路由：4 个前端测试全部通过。
- Windows 真实识别 C、D、E 三个 NTFS 盘：通过。
- 1 小时 raw、24 小时 5m、7 天 1h 曲线和本地时区：人工截图验证通过。
- P5 CPU、系统盘与离线告警触发、确认、恢复及去重：人工验证通过。
- P5 维护模式屏蔽离线告警，结束维护后重新触发，Agent 恢复上报后自动解决：人工截图验证通过。
- P6 后端批量补传与幂等测试：16 个后端测试全部通过。
- P6 Agent SQLite 顺序、重开恢复、缓存上限与退避测试：5 个 Agent 测试全部通过。
- P6 Windows PyInstaller 单文件构建、独立启动、采集落盘和安全退出：通过。
- P6 Windows 计划任务安装、重启后自动运行、20 条离线缓存恢复补传与卸载脚本修复：人工验证通过。
- P6 Linux x86-64 独立包在移除虚拟环境后运行：人工验证通过，SHA-256 为 `e35bde6a2b73410a2f841ba2c685dfc3aea60a7e36c9a4510daf34c08bada6e7`。
- P6 Linux systemd 安装、服务重启、优雅退出、SQLite 队列延续、保留数据卸载和彻底卸载：人工验证通过。
- Linux 电脑因使用限制未执行整机重启；已确认服务为 `enabled`，并以 `systemctl restart` 验证服务恢复，但不记为开机实测。
- P7 后端 Ruff、18 个后端测试、生产 Compose 配置和 Shell 语法：通过。
- P7 Vue 静态首页、SPA 路由回退、未知 API 404 隔离和 Host 白名单：通过。
- P7 前端 TypeScript 类型检查、5 个 Vitest 测试和 Vite 生产构建：通过。
- P7 GitHub Actions 工作流 YAML 语法与任务依赖：通过。
- P7 Docker 多阶段镜像构建：通过，本地测试镜像为 `nodewatch:p7-local`。
- P7 生产 Compose 隔离启动：App 与 PostgreSQL 均为 healthy，自动迁移到 `20260715_05`，首页与就绪检查通过。
- P7 网络暴露：测试时 App 仅绑定宿主机 `127.0.0.1`，PostgreSQL 未发布宿主端口。
- P7 备份恢复：`pg_dump` 压缩备份通过完整性检查，并成功恢复到独立临时数据库，恢复后包含 11 张 public 表。
- P7 阿里云初始化：已创建快照，配置 2 GiB Swap，完成系统升级、Nginx、`deploy` 用户、SSH 密钥登录与禁用密码登录。
- P7 服务器共存约束：同机已有 RustDesk，保留 Ubuntu Docker Engine 并安装 Compose v2；防火墙额外保留 RustDesk TCP `21115/21117`、UDP `21116`，NodeWatch 仍不公开 `8000` 和 `5432`。
- P7 镜像可达性：阿里云到 Docker Hub 持续超时，发布流程增加官方 PostgreSQL 镜像的固定版本 GHCR 副本，未使用第三方镜像站。
- P7 阿里云生产部署：`v0.1.1` App 与 PostgreSQL GHCR 镜像均启动健康，Nginx 反向代理、首页、登录、数据库就绪与迁移版本验证通过。
- P7 生产凭据：已交互式修改管理员密码并从 `.env` 删除 bootstrap 账号密码；生产 `.env` 权限为 `600`。
- P7 生产备份：压缩备份权限为 `600`，成功恢复到独立临时数据库并验证 11 张 public 表，已配置 `deploy` 用户每日 03:15 自动备份。
- P7 重启验收：Docker、Nginx、Cron、2 GiB Swap、NodeWatch App、PostgreSQL 与同机 RustDesk 均在整机重启后自动恢复。
- P7 回滚验收：App 从 `v0.1.1` 回滚到 `v0.1.0` 后再恢复到 `v0.1.1`，两次均通过健康检查与冒烟测试，PostgreSQL 未重建且迁移版本保持 `20260715_05`。
- P7 公网 HTTPS：使用 Certbot 5.7.0 和 Let’s Encrypt 短期公网 IP 证书，HTTP 自动跳转 HTTPS，浏览器信任验证、安全 Cookie、续期钩子与 `renew --dry-run` 均通过；`snap.certbot.renew.timer` 已启用。
- P7 Windows 覆盖安装：复现并修复旧 PyInstaller Agent 进程占用程序文件的问题，修复后的脚本成功更新计划任务并启动 Agent。
- P7 公网 Agent：通过受信任公网 IP HTTPS 完成绑定，一次性补传 557 条离线指标（500 + 57），随后连续 4 个实时采样周期均为 `accepted=1`、`remaining=0`；网页设备在线、实时指标、最后上报时间和历史曲线均人工验收通过。
- P7 范围确认：项目不配置域名，域名与 ICP 备案不属于交付范围。
