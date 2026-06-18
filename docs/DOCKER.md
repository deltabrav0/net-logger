# Running Net Logger with Docker

Net Logger can run in Docker on any host that supports Docker Engine or Docker Desktop. The container serves the same browser UI on port `8088` and stores SQLite data in a persistent Docker volume.

## Quick start

From the repository root:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8088
```

View logs:

```bash
docker compose logs -f net-logger
```

Stop the container:

```bash
docker compose down
```

## Persistent data

The compose file uses a named Docker volume:

```text
net-logger-data
```

Inside the container, Net Logger stores its default SQLite database under:

```text
/data/net_logger.sqlite3
```

The volume keeps your stations, sessions, check-ins, notes, and metrics when the container is restarted or recreated.

To remove the container but keep data:

```bash
docker compose down
```

To remove the container and delete the persistent database volume:

```bash
docker compose down -v
```

Back up the volume before using destructive reset endpoints or deleting the volume.

## Custom logo in Docker

The compose file mounts a local configuration directory:

```text
./config:/config:ro
```

To customize the application logo, create:

```text
./config/app-logo.png
```

The container uses this environment variable:

```text
NET_LOGGER_LOGO_PATH=/config/app-logo.png
```

If `./config/app-logo.png` is missing, Net Logger falls back to the bundled logo. For best results, use a square PNG, ideally `1024 x 1024` pixels.

## Optional FCC lookup data

The compose file mounts optional FCC lookup files from:

```text
./fcc-data:/fcc:ro
```

Set up the directory so it contains the expected FCC lookup files:

```text
./fcc-data/data/EN.dat
./fcc-data/data/EN.idx
./fcc-data/data/zipcodes.csv
./fcc-data/maidenhead.py
```

If the FCC files are missing, callsign lookup returns `found: false` and the rest of the app still works.

The browser's **Update FCC Database** button needs a writable FCC directory. The default compose mount is read-only so Docker deployments do not accidentally mutate host files. If you want browser-based FCC updates inside Docker, change the FCC volume to writable:

```yaml
- ./fcc-data:/fcc
```

## Build without Compose

Build the image:

```bash
docker build -t net-logger .
```

Run it:

```bash
docker run --rm \
  -p 8088:8088 \
  -e NET_LOGGER_DATA_DIR=/data \
  -v net-logger-data:/data \
  -v "$PWD/config:/config:ro" \
  -v "$PWD/fcc-data:/fcc:ro" \
  net-logger
```

Open:

```text
http://localhost:8088
```

## Environment variables

Common container environment variables:

- `NET_LOGGER_HOST`: default `0.0.0.0` in Docker
- `NET_LOGGER_PORT`: default `8088`
- `NET_LOGGER_DATA_DIR`: default `/data` in Docker
- `NET_LOGGER_DATABASE`: explicit SQLite database path, if you do not want the default under `/data`
- `NET_LOGGER_FCC_LOOKUP_PATH`: default `/fcc` in the compose file
- `NET_LOGGER_LOGO_PATH`: default `/config/app-logo.png` in the compose file
- `NET_LOGGER_DEBUG`: set to `true` only for local development

## Health check

The image and compose service define a health check against:

```text
/api/health
```

You can check status with:

```bash
docker compose ps
```

## Security note

Do not expose Net Logger directly to the public internet. It is intended for local or trusted LAN use. The API includes station/session mutation endpoints and a destructive reset endpoint. If you need remote access, place it behind a properly configured reverse proxy with TLS and authentication, or use a VPN into your local network.
