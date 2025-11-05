FROM qdrant/qdrant:v1.9.0

# Seed data (your 5.2 GB tarball of /qdrant/storage)
COPY qdrant_storage.tgz /seed/qdrant_storage.tgz

# One-time restore on first boot into the mounted storage volume
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=100
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
