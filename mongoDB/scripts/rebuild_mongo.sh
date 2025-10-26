#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env}"

[ -f "$ENV_FILE" ] || { echo "Environment file not found at $ENV_FILE" >&2; exit 1; }

set -a; source "$ENV_FILE"; set +a; set -u

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_BIN=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN=(docker-compose)
else
  echo "Docker Compose is required but not installed." >&2; exit 1
fi
compose() { "${COMPOSE_BIN[@]}" "$@"; }

echo "Starting mongo container..."
compose up -d mongo >/dev/null

echo "⏳ Waiting for mongo to be healthy..."
for i in {1..30}; do
  if compose exec -T mongo mongosh --quiet --eval "db.runCommand({ ping: 1 }).ok" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

DB_NAME="${MONGO_INITDB_DATABASE}"
ROOT_USER="${MONGO_INITDB_ROOT_USERNAME}"
ROOT_PASS="${MONGO_INITDB_ROOT_PASSWORD}"
INIT_DIR="/docker-entrypoint-initdb.d"

echo "🗑️  Dropping '${DB_NAME}'..."
compose exec -T mongo mongosh -u "$ROOT_USER" -p "$ROOT_PASS" --authenticationDatabase admin --quiet --eval "db.getSiblingDB('${DB_NAME}').dropDatabase()"

echo "📦  Creating collections..."
compose exec -T mongo mongosh -u "$ROOT_USER" -p "$ROOT_PASS" --authenticationDatabase admin --file "$INIT_DIR/01_collections.js" --eval "DB_NAME='${DB_NAME}'"

echo "🔧  Creating indexes..."
compose exec -T mongo mongosh -u "$ROOT_USER" -p "$ROOT_PASS" --authenticationDatabase admin --file "$INIT_DIR/02_indexes.js" --eval "DB_NAME='${DB_NAME}'"

echo "🌱  Seeding sample recipes..."
compose exec -T mongo mongoimport \
  --username "$MONGO_INITDB_ROOT_USERNAME" \
  --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --db "$DB_NAME" --collection recipes \
  --type json --file "$INIT_DIR/03_seed_small.jsonl"

echo "✅ Mongo database rebuilt successfully!"
