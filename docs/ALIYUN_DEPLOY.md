# 阿里云轻量应用服务器部署

本指南面向 Ubuntu 24.04、2 vCPU、2 GiB 内存的阿里云轻量应用服务器。仓库和截图中始终用 `<PUBLIC_IP>`、`<DOMAIN>`、`<GITHUB_USERNAME>` 占位，不保存公网 IP、SSH 私钥或生产凭据。

生产链路：公网 `80/443` → 宿主机 Nginx → `127.0.0.1:8000` → 单 Worker App 容器 → Docker 内部 PostgreSQL。数据库不映射宿主机端口。

## 1. 部署前检查

本地执行：

```bash
cd backend && ruff check . && pytest
cd ../frontend && npm ci && npm run typecheck && npm run test && npm run build
cd ..
docker build -f deploy/Dockerfile -t nodewatch:local .
docker compose --env-file deploy/production.env.example \
  -f deploy/docker-compose.production.yml config --quiet
```

人工确认 `.dockerignore` 排除了 `.env`、`.git`、虚拟环境、缓存、Token、私钥和备份。发布镜像必须使用 `v0.1.0` 这类固定 tag。

## 2. 阿里云控制台初始化（需要用户操作）

1. 对系统盘创建快照，例如 `nodewatch-before-init-20260716`，等待快照完成。
2. 默认只开放：SSH `22`（优先限制为可信公网 IP）、HTTP `80`、HTTPS `443`。当前服务器还承载 RustDesk，因此额外保留其现有 TCP `21115/21117` 与 UDP `21116` 规则；这是已知的共存例外，不属于 NodeWatch 端口。
3. 不开放 `8000`、`5432`、`2375`、`2376` 或管理面板端口。
4. 创建或导入 SSH 密钥对并绑定服务器，私钥只保存在自己的电脑。
5. 修改 SSH 规则前保持当前会话，并用第二个终端验证，避免锁在服务器外。

连接后确认：

```bash
whoami
cat /etc/os-release
uname -m
```

## 3. 初始化 Ubuntu

以 root 执行：

```bash
apt update
apt full-upgrade -y
apt install -y ca-certificates curl gnupg git nginx certbot python3-certbot-nginx jq vim
systemctl enable --now nginx

adduser deploy
usermod -aG sudo deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
```

在第二个终端验证 `deploy` 的密钥登录和 `sudo whoami`。确认成功后再创建 `/etc/ssh/sshd_config.d/99-nodewatch.conf`：

```text
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin prohibit-password
```

```bash
sudo sshd -t
sudo systemctl reload ssh
```

### 创建 2 GiB Swap

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

## 4. 安装 Docker Engine

全新服务器使用 Docker 官方 APT 仓库：

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
sudo usermod -aG docker deploy
```

退出并重新登录 `deploy` 后确认：

```bash
docker version
docker compose version
```

`docker` 组近似 root 权限，只加入可信用户。

### 与既有 RustDesk 共存的服务器

当前阿里云服务器已有 Ubuntu `docker.io` 运行 RustDesk，直接替换 Docker 包会造成额外停机风险，因此保留现有 Engine，只补装 Compose v2：

```bash
sudo apt update
sudo apt install -y docker-compose-v2
sudo usermod -aG docker deploy
```

重新登录后必须确认 `docker compose version` 正常，且 `hbbs`、`hbbr` 仍为 `Up`。NodeWatch 继续只把 App 映射到 `127.0.0.1:8000`，PostgreSQL 不映射端口；RustDesk 的公网规则不允许扩大为全部端口。

## 5. 发布固定版本镜像

推送 Git tag（例如 `v0.1.0`）会触发 `.github/workflows/publish-image.yml`，将同名固定 tag 推送到 GHCR。私有镜像在服务器使用只读 Package Token：

```bash
read -s -p 'GHCR token: ' GHCR_TOKEN; echo
echo "$GHCR_TOKEN" | docker login ghcr.io -u '<GITHUB_USERNAME>' --password-stdin
unset GHCR_TOKEN
```

Token 不写入 shell 历史、文件或截图。

## 6. 创建生产目录和 `.env`

把 `deploy/docker-compose.production.yml` 复制为服务器 `/opt/nodewatch/deploy/docker-compose.yml`，同时复制 `production.env.example`、Nginx 模板和 `deploy/scripts/`。

```bash
sudo mkdir -p /opt/nodewatch/deploy/scripts /opt/nodewatch/backups
sudo chown -R deploy:deploy /opt/nodewatch
cd /opt/nodewatch/deploy
cp production.env.example .env
chmod 600 .env
chmod +x scripts/*.sh
nano .env
```

生成密钥：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

分别写入 `SECRET_KEY` 和 `POSTGRES_PASSWORD`。首次通过 IP 验证时设置：

```dotenv
NODEWATCH_IMAGE=ghcr.io/<GITHUB_USERNAME>/nodewatch:v0.1.0
ALLOWED_HOSTS=<PUBLIC_IP>
SESSION_COOKIE_SECURE=false
```

不要提交服务器 `.env`。

## 7. 启动生产 Compose

```bash
cd /opt/nodewatch/deploy
docker compose config --quiet
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=100 db
curl -fsS http://127.0.0.1:8000/api/v1/health/live
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
sudo ss -lntp | grep -E ':(22|80|443|8000|5432)\b'
```

必须确认 App 和 DB 均健康、8000 只监听 `127.0.0.1`、5432 不在宿主机监听。

## 8. 配置 Nginx

```bash
sudo cp nginx-nodewatch.conf.example /etc/nginx/sites-available/nodewatch
sudo ln -sfn /etc/nginx/sites-available/nodewatch /etc/nginx/sites-enabled/nodewatch
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

短时访问 `http://<PUBLIC_IP>/` 和健康接口确认链路。HTTP 会明文传输 Cookie/Token，不要长期运行正式 Agent。

首次登录后，在服务器交互式修改管理员密码：

```bash
cd /opt/nodewatch/deploy
docker compose exec app python -m app.cli change-password admin
```

随后删除 `.env` 中两行 bootstrap 配置，并重建 App：

```bash
sed -i '/^BOOTSTRAP_ADMIN_USERNAME=/d;/^BOOTSTRAP_ADMIN_PASSWORD=/d' .env
docker compose up -d --force-recreate app
```

重新登录确认新密码有效。

## 9. 域名、备案与 HTTPS

中国内地服务器使用域名正式提供 Web 服务前，需要完成 ICP 备案。备案通过后将 `<DOMAIN>` 的 A 记录指向公网 IP，把 Nginx `server_name` 改为域名：

```bash
getent hosts <DOMAIN>
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d <DOMAIN>
sudo certbot renew --dry-run
```

修改 `.env`：

```dotenv
ALLOWED_HOSTS=<DOMAIN>
SESSION_COOKIE_SECURE=true
```

```bash
docker compose up -d --force-recreate app
curl -I https://<DOMAIN>/
curl -fsS https://<DOMAIN>/api/v1/health/ready
```

确认 HTTP 自动跳转 HTTPS、证书匹配、Cookie 仅通过 HTTPS 发送。

## 10. Agent 公网上报

HTTPS 完成后在网页创建设备，以 `https://<DOMAIN>` 配置 Agent，前台观察 3～5 个采样周期，再安装为 Windows 计划任务或 Linux systemd。公开截图不得包含完整 Token、真实公网 IP或敏感主机名。

## 11. 备份与恢复演练

```bash
cd /opt/nodewatch/deploy
./scripts/backup.sh
./scripts/restore-test.sh /opt/nodewatch/backups/nodewatch-时间.sql.gz
```

恢复脚本只创建独立临时数据库，结束后自动删除，不覆盖生产库。每日备份可加入 root cron：

```text
15 3 * * * /opt/nodewatch/deploy/scripts/backup.sh >> /var/log/nodewatch-backup.log 2>&1
```

服务器只保留最近 7 天备份，并定期复制到服务器外的私有位置。同盘备份不能防止整盘损坏。

## 12. 更新与回滚

更新前先备份；破坏性 migration 前额外创建阿里云快照。把 `.env` 中镜像改为新固定 tag 后：

```bash
./scripts/deploy.sh
./scripts/smoke-test.sh https://<DOMAIN>
```

回滚 App：

```bash
./scripts/rollback.sh ghcr.io/<GITHUB_USERNAME>/nodewatch:<PREVIOUS_TAG>
```

脚本不会执行 `alembic downgrade`。数据库结构回滚必须先备份并单独人工确认。

## 13. 服务器重启验收

```bash
sudo reboot
```

恢复后检查：

```bash
systemctl is-active docker nginx
cd /opt/nodewatch/deploy
docker compose ps
curl -fsS http://127.0.0.1:8000/api/v1/health/ready
```

## 14. 故障排查

```bash
docker compose config --quiet
docker compose ps -a
docker compose logs --tail=200 app db
docker inspect nodewatch-app-1 --format '{{.State.OOMKilled}}'
free -h
df -h
docker system df
sudo nginx -t
sudo tail -n 100 /var/log/nginx/error.log
```

不要执行 `docker compose down -v`，它会删除 PostgreSQL 命名卷。公网异常按“阿里云防火墙 → Nginx → 127.0.0.1:8000 → App → DB”的顺序逐层检查。
