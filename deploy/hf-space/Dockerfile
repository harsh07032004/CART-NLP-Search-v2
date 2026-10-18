# All-in-one demo image for Hugging Face Spaces (Docker SDK, free CPU tier):
# MongoDB + Elasticsearch 7.17 + FastAPI in one container, re-seeded on boot.
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg ca-certificates procps \
 && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-7.gpg \
 && echo "deb [ signed-by=/usr/share/keyrings/mongodb-7.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
      > /etc/apt/sources.list.d/mongodb-org-7.0.list \
 && apt-get update && apt-get install -y --no-install-recommends mongodb-org-server \
 && rm -rf /var/lib/apt/lists/*

ARG ES_VERSION=7.17.25
RUN curl -fsSL https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ES_VERSION}-linux-x86_64.tar.gz \
    | tar -xz -C /opt && mv /opt/elasticsearch-${ES_VERSION} /opt/es \
 && rm -rf /opt/es/modules/x-pack-ml/platform

RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R user /app /opt/es

USER user
ENV PORT=7860 \
    ES_HOST=http://127.0.0.1:9200 \
    ES_INDEX=products \
    MONGO_URI=mongodb://127.0.0.1:27017 \
    MONGO_DB=ecommerce \
    PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["bash", "start.sh"]
