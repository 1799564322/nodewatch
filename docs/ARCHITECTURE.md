# 架构

P1 建立了浏览器、Vue、FastAPI 和 PostgreSQL 之间的登录链路：

1. Vue 登录页将账号密码提交给 FastAPI。
2. FastAPI 使用 Argon2 验证 `users` 表中的密码哈希。
3. 验证成功后，服务端在 `user_sessions` 表保存 Session 哈希，并给浏览器写入 HttpOnly Cookie。
4. Vue 路由守卫访问 `/auth/me` 判断是否已登录。
5. 登录、退出和失败事件写入 `audit_logs`，用于安全审计。

SQLAlchemy 模型描述应用如何读写数据；Alembic 迁移描述数据库结构如何从一个版本演进到下一个版本。两者职责不同，因此修改模型后仍需创建并执行迁移。

本地只把 PostgreSQL 放进 Docker，前后端仍直接运行在电脑上，便于初学阶段调试代码。数据库容器提供隔离、固定版本和可重复启动，数据通过 Docker Volume 持久化。

P2 增加独立 Agent 认证链路：网页管理员使用 Session Cookie 管理设备；Python Agent 使用每台设备独立的 Bearer Token。Agent 首次运行生成随机实例 UUID，bootstrap 将设备绑定到该实例，随后 system-info 更新设备基本信息与最后在线时间。

P3 同时写入 `metric_samples` 历史表和 `device_latest_metrics` 最新表。历史表用于后续曲线，latest 表每台设备只有一行，供总览和列表查询，避免扫描不断增长的历史数据。

P4 使用 PostgreSQL `date_bin` 在数据库端完成 5 分钟或 1 小时时间桶平均，限制图表点数。`disk_latest_metrics` 以设备与挂载点唯一，Agent 对单个不可访问磁盘容错，其他磁盘仍可上报。

P5 在指标事务中评估实时阈值规则，partial unique index 防止同设备同规则重复未恢复事件。单进程 APScheduler 每分钟检查离线，每日清理过期 Session 和历史指标；多 Worker 时启动日志会警告重复任务风险。

P6 的 Agent 先把每次采集写入本地 SQLite WAL，再按采集时间批量发送。服务端确认接受或判定重复后才从队列删除；网络和 5xx 错误使用带抖动的指数退避，认证错误固定等待 300 秒。这样断网与进程异常不会直接丢失尚未确认的样本。

P7 使用多阶段 Dockerfile 构建 Vue 静态资源和 Python wheel，最终镜像由非 root 用户运行。entrypoint 先执行 Alembic migration，再启动单 Worker Uvicorn。宿主机 Nginx 是唯一公网入口，App 只绑定回环地址，PostgreSQL 只存在于 Compose 内部网络；命名卷、逻辑备份和阿里云快照分别覆盖容器重建、误操作和整盘故障。
