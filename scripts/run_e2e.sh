#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKEND="${TARGET_DB_BACKEND:-postgres}"
PRODUCT_SOURCE="${SOURCE_PRODUCT_BACKEND:-mysql}"

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  echo "Waiting for ${label} (${host}:${port})..."
  for i in $(seq 1 30); do
    if python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('${host}', ${port})); s.close()" 2>/dev/null; then
      echo "${label} is ready."
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${label}." >&2
  return 1
}

wait_for_http() {
  local url="$1"
  local label="$2"
  echo "Waiting for ${label} (${url})..."
  for i in $(seq 1 30); do
    if python -c "import urllib.request; urllib.request.urlopen('${url}', timeout=1)" 2>/dev/null; then
      echo "${label} is ready."
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${label}." >&2
  return 1
}

wait_for_tcp "${MONGO_HOST:-mongo}" "${MONGO_PORT:-27017}" "MongoDB"
if [ "$PRODUCT_SOURCE" = "mysql" ]; then
  wait_for_tcp "${SOURCE_MYSQL_HOST:-mysql}" "${SOURCE_MYSQL_PORT:-3306}" "MySQL"
fi
wait_for_http "${MOCK_SOURCE_API_URL:-http://external-api-example:8080}/health" "Mock source API"

if [ "$PRODUCT_SOURCE" = "sqlite" ]; then
  echo "Seeding SQLite product source..."
  python scripts/seed_sqlite_source.py
fi

if [ "$BACKEND" = "sqlite" ]; then
  echo "Migrating SQLite..."
  python scripts/migrate_sqlite.py
else
  wait_for_tcp "${TARGET_DB_HOST:-postgres}" "${TARGET_DB_PORT:-5432}" "PostgreSQL"

  echo "Migrating PostgreSQL..."
  python scripts/migrate_postgres.py
fi

echo "Seeding MongoDB..."
python scripts/seed_mongo.py

echo "Running first sync (June 2024)..."
APP_SYNC_TYPE=all APP_PERIODS_TO_RUN="2024-06-01,2024-06-30" python -m my_marketplace_etl.main

echo "Running incremental sync (July 2024)..."
APP_SYNC_TYPE=incremental APP_PERIODS_TO_RUN="2024-07-01,2024-07-31" python -m my_marketplace_etl.main

echo "E2E bootstrap complete."
