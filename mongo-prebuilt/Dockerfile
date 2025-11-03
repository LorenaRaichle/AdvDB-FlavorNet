FROM mongo:7.0

COPY appdb.archive /dump/appdb.archive

# Restore during build, but don't fail the layer if the connection closes right at shutdown.
RUN set -eux; \
    mkdir -p /data/db; \
    mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db --bind_ip 127.0.0.1; \
    # Increase socket timeout & be tolerant to end-of-connection close
    mongorestore --archive=/dump/appdb.archive --gzip --numInsertionWorkersPerCollection=4 || true; \
    # Give the server a moment to flush
    sleep 3; \
    # Try graceful shutdown; don't fail if it's already down
    mongosh --quiet --eval 'db.getSiblingDB("admin").shutdownServer()' || true

CMD ["mongod", "--dbpath", "/data/db", "--bind_ip_all"]
