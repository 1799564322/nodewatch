#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || $1 == *:latest ]]; then
  echo "用法：$0 <上一个固定版本镜像，例如 ghcr.io/user/nodewatch:v0.1.0>" >&2
  exit 1
fi
cd "$(dirname "$0")/.."
sed -i "s|^NODEWATCH_IMAGE=.*|NODEWATCH_IMAGE=$1|" .env
docker compose pull app
docker compose up -d app
docker compose ps
"$(dirname "$0")/smoke-test.sh" http://127.0.0.1:8000
