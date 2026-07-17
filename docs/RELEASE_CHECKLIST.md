# NodeWatch v1.0.0 Release Checklist

勾选项必须有命令输出、CI 记录、截图或部署记录作为证据，不能只凭“看起来没问题”。

## 版本与代码

- [x] 后端、Agent、前端和示例环境变量版本均为 `1.0.0`
- [x] `git status` 只包含计划内修改
- [x] 没有临时调试代码、真实凭据、数据库备份或本地缓存
- [x] `git diff --check` 通过
- [x] MIT License 与版权年份正确

## 自动化质量

- [x] 后端 Ruff 通过
- [x] 后端 Alembic 在空测试库升级到 head
- [x] 后端 pytest 通过
- [x] Agent Ruff 和 pytest 通过
- [x] 前端 typecheck、Vitest 和 production build 通过
- [x] GitHub Actions `CI` 全部绿色
- [x] GitHub Actions 能生成 Windows/Linux Agent Artifact 与 SHA-256

## 功能验收

- [x] 登录、退出和权限校验正常
- [x] 创建设备、一次性 Token、撤销和重新生成正常
- [x] Windows 或 Linux Agent 连续上报至少 3 个周期
- [x] 离线缓存恢复后 `remaining=0`
- [x] 总览、设备详情、历史聚合、多磁盘和告警状态机正常
- [x] `seed-demo --confirm` 在非生产库可重复运行且保留真实设备
- [x] `seed-demo --confirm` 在 `APP_ENV=production` 拒绝执行

## 文档与公开展示

- [x] 新用户按 README 能完成本地启动
- [x] README 包含功能、架构、技术栈、快速开始、部署、安全和限制
- [x] 总览截图已脱敏并保存为 `docs/screenshots/overview.png`
- [x] 设备详情截图已脱敏并保存为 `docs/screenshots/device-detail.png`
- [x] 告警截图已脱敏并保存为 `docs/screenshots/alerts.png`
- [x] 架构 Mermaid、排错、安全、简历与面试文档完整
- [x] 不声称未经验证的用户数、性能或高可用能力

## 安全

- [x] 当前工作树秘密扫描无结果
- [x] Git 历史秘密检查完成
- [x] 截图隐藏公网 IP、Token、用户名、真实主机名和个人浏览器信息
- [x] 生产 bootstrap 管理员账号密码已从 `.env` 删除
- [x] 生产 `.env`、备份与 SSH 私钥权限正确
- [x] App 和 PostgreSQL 未直接暴露公网
- [x] HTTPS 可信，安全 Cookie 已启用，Certbot 定时器与模拟续期通过

## 生产与恢复

- [x] 固定 `v1.0.0` 镜像已发布到 GHCR
- [x] 生产 Compose 配置检查通过，App/DB 均 healthy
- [x] 首页、登录、ready 接口和 Agent 公网上报冒烟通过
- [x] 新备份已生成并复制到服务器外
- [x] 备份成功恢复到临时数据库
- [x] 已记录上一个可回滚镜像 tag
- [x] 回滚脚本在不重建 PostgreSQL 的情况下验证通过
- [x] NodeWatch 与同机 RustDesk 重启后均能恢复

## 发布

- [x] 仓库公开前最后一次人工秘密检查完成
- [x] GitHub 仓库已设为 Public，README 与脱敏截图可公开访问
- [x] 更新日志只描述真实完成内容
- [x] 创建并推送带说明的 `v1.0.0` tag
- [x] 发布镜像工作流绿色
- [x] 创建 GitHub Release，附安装包、校验值、升级和回滚说明
- [x] 发布后再次检查公网健康、证书有效期、日志和最新备份

## 范围说明

项目所有者已决定不进行完整 24 小时连续观察。P7 已用整机重启、容器健康、HTTPS、备份恢复、版本回滚、公网 Agent 缓存补传及多个实时周期替代验证；此范围调整不应被描述为完成了 24 小时稳定性测试。
