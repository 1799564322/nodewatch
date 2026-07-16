#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  echo "缺少 .env，请先复制并编辑 production.env.example" >&2
  exit 1
fi
image=$(sed -n 's/^NODEWATCH_IMAGE=//p' .env | tail -n 1)
if [[ -z $image || $image == *:latest ]]; then
  echo "NODEWATCH_IMAGE 必须使用固定版本 tag，不能只使用 latest" >&2
  exit 1
fi

docker compose config --quiet
docker compose pull
docker compose up -d --wait --wait-timeout 180
docker compose ps
"$(dirname "$0")/smoke-test.sh" http://127.0.0.1:8000
