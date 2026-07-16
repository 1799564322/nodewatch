#!/usr/bin/env bash
set -euo pipefail

deploy_dir=$(cd "$(dirname "$0")/.." && pwd)
backup_dir=${NODEWATCH_BACKUP_DIR:-/opt/nodewatch/backups}
mkdir -p "$backup_dir"
backup="$backup_dir/nodewatch-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

cd "$deploy_dir"
docker compose exec -T db sh -c 'pg_dump --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' |
  gzip -9 >"$backup"
gzip -t "$backup"
chmod 600 "$backup"
find "$backup_dir" -type f -name 'nodewatch-*.sql.gz' -mtime +7 -delete
echo "$backup"
