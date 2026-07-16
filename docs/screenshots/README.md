# P8 截图说明

三张图片已由项目所有者在独立演示数据库中手动截取并通过脱敏检查：

1. `overview.png`：设备总览，展示在线/离线状态和最新指标。
2. `device-detail.png`：设备详情，展示历史曲线与磁盘卡片。
3. `alerts.png`：告警页，展示规则与 firing/resolved 事件。

## 截图前检查

- 优先在本地演示数据库执行 `seed-demo --confirm` 后截图。
- 隐藏地址栏或遮挡公网 IP。
- 不出现完整 Agent Token、登录密码、SSH 信息或数据库地址。
- 把真实主机名、用户名、设备名替换为 `[演示]` 数据。
- 隐藏浏览器头像、收藏栏、聊天窗口和其他个人信息。
- 图片建议使用 PNG，宽度 1440～1920 像素，三张保持相同浏览器缩放比例。

README“界面预览”已引用：

```markdown
![设备总览](docs/screenshots/overview.png)
![设备详情](docs/screenshots/device-detail.png)
![告警状态机](docs/screenshots/alerts.png)
```

不要用生产截图直接覆盖这些演示截图；重拍后仍需逐张放大检查敏感信息。
