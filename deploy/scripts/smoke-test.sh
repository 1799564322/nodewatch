#!/usr/bin/env bash
set -euo pipefail

base_url=${1:-http://127.0.0.1:8000}
base_url=${base_url%/}
curl --fail --silent --show-error "$base_url/api/v1/health/live" >/dev/null
curl --fail --silent --show-error "$base_url/api/v1/health/ready" >/dev/null
curl --fail --silent --show-error "$base_url/" | grep -q "NodeWatch"
echo "冒烟测试通过：$base_url"
