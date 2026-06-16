# Net Logger

Standalone amateur-radio net logger with a simplified two-column Kanban-style active net board.

## Features

- Known Stations and Checked In columns
- Click or drag a known station to check it into the active session
- Net Control is automatically checked in when a net starts
- Automatic local FCC lookup for unknown Net Control callsigns when FCC data is available
- Add previously unknown callsigns manually or through local FCC lookup
- Traffic and notes on checked-in station cards
- Last Heard timestamps on known station cards
- Saved net sessions with CSV export
- Metrics by net, grouped by week/month/year
- SQLite persistence
- Flask JSON API plus vanilla HTML/CSS/JS UI
- Installable `net-logger` command for Windows, macOS, and Linux

## Documentation

- [API documentation](docs/API.md)
- [User/install guide](docs/USER_GUIDE.md)
- [Original MVP implementation plan](docs/plans/2026-06-16-kanban-net-logger-mvp.md)

## Install from GitHub

Recommended with pipx:

```bash
pipx install git+https://github.com/deltabrav0/net-logger.git
net-logger serve
```

With pip:

```bash
python -m pip install "git+https://github.com/deltabrav0/net-logger.git"
net-logger serve
```

With uv tool:

```bash
uv tool install git+https://github.com/deltabrav0/net-logger.git
net-logger serve
```

Open:

```text
http://127.0.0.1:8088/
```

The package is pure Python and runs on Windows, macOS, and Linux with Python 3.11+.

## Developer quick start from GitHub

```bash
git clone https://github.com/deltabrav0/net-logger.git
cd net-logger
uv sync --extra dev
uv run net-logger serve
```

## Install from a local checkout

Recommended with pipx:

```bash
cd /path/to/net-logger
pipx install .
net-logger serve
```

Or build a wheel:

```bash
uv build
python -m pip install dist/net_logger-0.1.0-py3-none-any.whl
net-logger serve
```

## Run options

```bash
net-logger serve --host 127.0.0.1 --port 8088
net-logger serve --host 0.0.0.0 --port 8088
net-logger serve --database /path/to/net_logger.sqlite3
```

Environment variables:

- `NET_LOGGER_HOST`
- `NET_LOGGER_PORT`
- `NET_LOGGER_DATABASE`
- `NET_LOGGER_DATA_DIR`
- `NET_LOGGER_DEBUG`
- `NET_LOGGER_FCC_LOOKUP_PATH`

## Run tests

```bash
uv run --extra dev pytest -q
```

## API sketch

See [docs/API.md](docs/API.md) for full request/response details.

Common endpoints:

- `GET /api/stations`
- `POST /api/stations`
- `GET /api/lookup?callsign=W5XYZ`
- `GET /api/sessions`
- `POST /api/sessions/start`
- `GET /api/sessions/<id>/board`
- `POST /api/sessions/<id>/checkins`
- `PATCH /api/checkins/<id>`
- `DELETE /api/checkins/<id>`
- `POST /api/sessions/<id>/stop`
- `GET /api/export.csv`
- `GET /api/metrics?period=month`
- `DELETE /api/records?dry_run=true`
- `DELETE /api/records`

## FCC lookup

The app uses a local/off-grid FCC flat-file lookup adapter at:

```text
src/net_logger/fcc_lookup.py
```

Set:

```bash
export NET_LOGGER_FCC_LOOKUP_PATH="/path/to/fcc_database_web_app"
```

Required files under that directory:

```text
data/EN.dat
data/EN.idx
data/zipcodes.csv
maidenhead.py
```

If FCC files are missing, lookup returns `found: false` and the app still works.

## Destructive reset API

Preview counts:

```bash
curl -X DELETE "http://127.0.0.1:8088/api/records?dry_run=true"
```

Delete all stations, sessions, and check-ins:

```bash
curl -X DELETE http://127.0.0.1:8088/api/records
```

Back up the SQLite database before using the destructive reset endpoint.
