FROM apache/spark:3.5.8-python3@sha256:1916d1d43a6ff0e4d7ac682c84c0412e4a609fca11dd56cfdae592dcde3a378c AS spark_distribution
FROM python:3.11.11-slim-bookworm@sha256:081075da77b2b55c23c088251026fb69a7b2bf92471e491ff5fd75c192fd38e5
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 update && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY requirements.txt .
COPY --from=spark_distribution /opt/spark /opt/spark
# Use the official Spark distribution; pip installs only the small Python dependencies.
RUN sed '/^pyspark==/d' requirements.txt > /tmp/python-requirements.txt && pip install --timeout 180 --retries 5 --no-cache-dir -r /tmp/python-requirements.txt
COPY . .
ENV SPARK_HOME=/opt/spark PYTHONPATH=/lab/src:/opt/spark/python SPARK_LOCAL_IP=127.0.0.1 PYSPARK_PYTHON=python
CMD ["python", "-m", "small_files.cli", "--config", "config/quick.json"]
