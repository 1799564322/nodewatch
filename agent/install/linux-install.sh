#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "请使用 sudo 运行此脚本" >&2
  exit 1
fi
if [[ $# -ne 3 ]]; then
  echo "用法: sudo ./linux-install.sh <Agent文件> <服务端URL> <Agent Token>" >&2
  exit 1
fi

binary_path=$(realpath "$1")
server_url=$2
agent_token=$3
if [[ ! -f "$binary_path" ]]; then
  echo "找不到 Agent 文件: $binary_path" >&2
  exit 1
fi
if [[ $agent_token != nwa_* ]]; then
  echo "Agent Token 格式无效" >&2
  exit 1
fi

id nodewatch >/dev/null 2>&1 || useradd --system --home /var/lib/nodewatch --shell /usr/sbin/nologin nodewatch
install -d -m 0755 /opt/nodewatch
install -d -o nodewatch -g nodewatch -m 0700 /var/lib/nodewatch
install -m 0755 "$binary_path" /opt/nodewatch/nodewatch-agent
cat >/var/lib/nodewatch/config.toml <<EOF
server_url = "$server_url"
agent_token = "$agent_token"
collect_interval_seconds = 60
request_timeout_seconds = 10
verify_tls = true
log_level = "INFO"
cache_max_samples = 10000
cache_retention_days = 7
max_batch_samples = 500
retry_max_seconds = 300
log_max_bytes = 5242880
log_backup_count = 3
EOF
chown nodewatch:nodewatch /var/lib/nodewatch/config.toml
chmod 0600 /var/lib/nodewatch/config.toml
cat >/etc/systemd/system/nodewatch-agent.service <<'EOF'
[Unit]
Description=NodeWatch Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=nodewatch
Group=nodewatch
WorkingDirectory=/var/lib/nodewatch
ExecStart=/opt/nodewatch/nodewatch-agent --config /var/lib/nodewatch/config.toml
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now nodewatch-agent
echo "NodeWatch Agent 已安装并启动"
