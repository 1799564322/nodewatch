#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "用法：$0 <nodewatch-备份文件.sql.gz>" >&2
  exit 1
fi
backup=$(realpath "$1")
gzip -t "$backup"
deploy_dir=$(cd "$(dirname "$0")/.." && pwd)
temporary_db="nodewatch_restore_test_$(date -u +%Y%m%d%H%M%S)"

cd "$deploy_dir"
db_user=$(docker compose exec -T db printenv POSTGRES_USER | tr -d '\r')
cleanup() {
  docker compose exec -T db dropdb -U "$db_user" --if-exists "$temporary_db" >/dev/null
}
trap cleanup EXIT
docker compose exec -T db createdb -U "$db_user" "$temporary_db"
gzip -dc "$backup" | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$db_user" -d "$temporary_db" >/dev/null
table_count=$(docker compose exec -T db psql -At -U "$db_user" -d "$temporary_db" -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d '\r')
if [[ $table_count -lt 1 ]]; then
  echo "恢复后的临时数据库没有业务表" >&2
  exit 1
fi
echo "恢复演练通过：临时数据库包含 $table_count 张 public 表"
