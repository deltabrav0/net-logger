FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NET_LOGGER_HOST=0.0.0.0 \
    NET_LOGGER_PORT=8088 \
    NET_LOGGER_DATA_DIR=/data

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin netlogger \
    && mkdir -p /data /config /fcc \
    && chown -R netlogger:netlogger /data /config /fcc /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

USER netlogger

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8088/api/health', timeout=3).read()"

CMD ["net-logger", "serve", "--host", "0.0.0.0", "--port", "8088"]
