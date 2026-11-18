FROM python:3.11.14-slim@sha256:c8271b1f627d0068857dce5b53e14a9558603b527e46f1f901722f935b786a39
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src src
COPY config config
ENV PYTHONPATH=/app/src GATEWAY_SERVE=1 GATEWAY_DB=/state/gateway.db
RUN mkdir /state && chown 65534:65534 /state
USER 65534:65534
EXPOSE 8000
CMD ["uvicorn","gateway.app:app","--host","0.0.0.0","--port","8000","--workers","1","--no-access-log"]
