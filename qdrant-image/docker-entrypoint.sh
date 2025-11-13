#!/usr/bin/env bash
set -e

# Restore only if the storage dir is empty (first run on a fresh volume)
if [ -z "$(ls -A /qdrant/storage 2>/dev/null)" ] && [ -f /seed/qdrant_storage.tgz ]; then
  echo "[qdrant] Empty storage detected. Restoring from seed tarball..."
  mkdir -p /qdrant/storage
  tar -xzf /seed/qdrant_storage.tgz -C /qdrant/storage
  echo "[qdrant] Restore complete."
fi

# Start Qdrant normally
exec /qdrant/entrypoint.sh
