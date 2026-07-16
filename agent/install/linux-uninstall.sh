#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "请使用 sudo 运行此脚本" >&2
  exit 1
fi
systemctl disable --now nodewatch-agent 2>/dev/null || true
rm -f /etc/systemd/system/nodewatch-agent.service
rm -rf /opt/nodewatch
systemctl daemon-reload
if [[ ${1:-} == "--remove-data" ]]; then
  rm -rf /var/lib/nodewatch
  userdel nodewatch 2>/dev/null || true
  echo "服务和本地数据已删除"
else
  echo "服务已删除；配置、身份、缓存和日志保留在 /var/lib/nodewatch"
fi
