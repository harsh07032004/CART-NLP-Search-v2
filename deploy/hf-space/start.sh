#!/usr/bin/env bash
# Boots MongoDB + Elasticsearch, seeds the catalog, then serves the API.
set -euo pipefail

mkdir -p /tmp/mongo /tmp/es/data /tmp/es/logs

mongod --dbpath /tmp/mongo --bind_ip 127.0.0.1 --port 27017 \
       --wiredTigerCacheSizeGB 0.5 --fork --logpath /tmp/mongod.log

ES_JAVA_OPTS="-Xms1g -Xmx1g" /opt/es/bin/elasticsearch -d -p /tmp/es/pid \
  -Ediscovery.type=single-node \
  -Enetwork.host=127.0.0.1 \
  -Expack.security.enabled=false \
  -Expack.ml.enabled=false \
  -Eingest.geoip.downloader.enabled=false \
  -Epath.data=/tmp/es/data -Epath.logs=/tmp/es/logs

echo "Waiting for Elasticsearch..."
until curl -fs "${ES_HOST}/_cluster/health?wait_for_status=yellow&timeout=5s" >/dev/null; do sleep 1; done

python seed_fast.py
exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
