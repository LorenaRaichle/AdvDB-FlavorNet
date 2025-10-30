#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found at $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
set -u

: "${POSTGRES_DB:?POSTGRES_DB is not set}"
: "${POSTGRES_USER:?POSTGRES_USER is not set}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_BIN=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN=(docker-compose)
else
  echo "Docker Compose is required but not installed." >&2
  exit 1
fi

compose() {
  "${COMPOSE_BIN[@]}" "$@"
}

INIT_DIR="$PROJECT_ROOT/sql/init"
if [ ! -d "$INIT_DIR" ]; then
  echo "Initialization directory not found at $INIT_DIR" >&2
  exit 1
fi

echo "Starting postgres container..."
compose up -d postgres >/dev/null

psql_exec() {
  compose exec -T \
    -e PGPASSWORD="$POSTGRES_PASSWORD" \
    postgres \
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" "$@"
}

echo "🗑️  Dropping and recreating $POSTGRES_DB..."
psql_exec -d postgres -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";"
psql_exec -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\";"

for sql_file in "$INIT_DIR"/*.sql; do
  [ -e "$sql_file" ] || continue
  sql_name="$(basename "$sql_file")"
  echo "📦  Applying $sql_name..."
  psql_exec -d "$POSTGRES_DB" -f "/docker-entrypoint-initdb.d/$sql_name"
done

echo "✅ Database rebuilt successfully!"

# to make it executable: chmod +x sql/scripts/rebuild_db.sh
