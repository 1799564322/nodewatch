# API

P1 API 前缀为 `/api/v1`。

## 健康检查

- `GET /health/live`：只确认应用进程可响应，不访问数据库。
- `GET /health/ready`：检查数据库连接以及 Alembic 迁移版本，适合部署就绪检查。

## 登录会话

- `POST /auth/login`：接收 `username` 和 `password`，成功后通过响应头写入 HttpOnly Session Cookie。
- `POST /auth/logout`：删除服务端 Session，并让浏览器清除 Cookie。
- `GET /auth/me`：根据 Cookie 返回当前登录用户；未登录返回 401。

浏览器后续请求会自动携带同源 Cookie，前端不需要把 Session Token 保存到 localStorage。

## 设备与 Agent

- `GET/POST /devices`：查询或创建设备。
- `GET/PATCH/DELETE /devices/{device_id}`：查询、修改或禁用设备。
- `POST /devices/{device_id}/tokens`：轮换并返回只显示一次的 Token。
- `POST /devices/{device_id}/tokens/{token_id}/revoke`：撤销 Token。
- `POST /agent/bootstrap`：使用 Bearer Token 绑定 Agent 实例。
- `POST /agent/system-info`：上报主机名、系统、CPU 核心数和内存总量。
- `POST /agent/metrics`：幂等写入单条指标并更新 latest 状态。
- `POST /agent/metrics/batch`：按请求顺序补传最多 500 条缓存指标，返回接受数与重复数。
- `GET /dashboard`：返回设备总数、在线/离线数和 CPU/内存 Top 5。

指标使用 `(device_id, collected_at)` 唯一约束；单条或批量重复请求只增加 `duplicate` 计数，不会产生第二条历史记录。批量补传中的旧指标不会覆盖 latest，也不会触发实时阈值告警。

## 历史与磁盘

- `GET /devices/{id}/metrics/history?from=&to=&resolution=`：查询历史指标。
- `GET /devices/{id}/disks`：查询所有磁盘的最新状态。

默认分辨率：6 小时以内 `raw`，48 小时以内 `5m`，更长使用 `1h`。单次范围最多 31 天，单序列最多 1500 点；raw 超限返回 422。

## 告警与维护

- `GET /alerts`：按状态、严重程度或设备筛选事件。
- `POST /alerts/{id}/acknowledge`：确认正在处理的事件。
- `GET/POST/PATCH /alert-rules`：查询、创建和修改规则。
- `POST/DELETE /devices/{id}/maintenance`：开启或结束维护模式。

事件状态为 `firing → acknowledged → resolved`；确认不会阻止指标恢复后转为 resolved。

Agent API 只接受 `Authorization: Bearer <agent-token>`，不能用浏览器 Cookie 替代。
