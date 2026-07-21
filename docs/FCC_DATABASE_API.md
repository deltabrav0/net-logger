# Local FCC Database API

Net Logger exposes a small JSON API around the configured local FCC amateur-radio database. Other local applications can use these endpoints as a lightweight FCC callsign lookup service without reading the FCC flat files directly.

## Base URL

When Net Logger is running locally with the default port:

```text
http://127.0.0.1:8088
```

For another device on the same LAN, start Net Logger with a LAN-accessible host:

```bash
net-logger serve --host 0.0.0.0 --port 8088
```

Then call the host computer's LAN address, for example:

```text
http://192.168.1.70:8088
```

## Local data path

The FCC lookup data directory can be overridden with:

```bash
NET_LOGGER_FCC_LOOKUP_PATH=/path/to/fcc_database_web_app
```

If that environment variable is not set, Net Logger uses the normal writable per-user application data directory:

```text
Windows: %APPDATA%\Net Logger\fcc_lookup
macOS: ~/Library/Application Support/Net Logger/fcc_lookup
Linux: ~/.local/share/net-logger/fcc_lookup
```

Expected files:

```text
data/EN.dat
data/EN.idx
data/zipcodes.csv
maidenhead.py
```

When updating through the API, Net Logger also downloads/extracts:

```text
data/HD.dat
```

`HD.dat` is used when rebuilding `EN.idx` so only active licenses are indexed.

## Endpoints

### Lookup callsign

```http
GET /api/lookup?callsign=K5SUB
```

Example:

```bash
curl "http://127.0.0.1:8088/api/lookup?callsign=K5SUB"
```

Successful lookup response:

```json
{
  "ok": true,
  "found": true,
  "result": {
    "callsign": "K5SUB",
    "name": "DANIEL BUTLER",
    "city": "LUFKIN",
    "state": "TX",
    "zip": "75901",
    "grid": "EM21QG",
    "lat": 31.27,
    "lon": -94.6469
  }
}
```

Not found response:

```json
{
  "ok": true,
  "found": false,
  "callsign": "K5SUB"
}
```

Notes for client applications:

- `callsign` input is normalized to uppercase with whitespace removed.
- Matching is exact; this endpoint is not a prefix search.
- `grid`, `lat`, and `lon` are ZIP-derived, not operator-address-precise coordinates.
- If local FCC files are missing, the endpoint still returns HTTP `200` with `found: false`.

### FCC database status

```http
GET /api/fcc/status
```

Example:

```bash
curl "http://127.0.0.1:8088/api/fcc/status"
```

Example response:

```json
{
  "data_path": "/path/to/fcc_database_web_app",
  "available": true,
  "updated_at": "2026-06-16T12:00:00+00:00",
  "age_days": 3,
  "files": {
    "EN.dat": true,
    "EN.idx": true,
    "zipcodes.csv": true
  }
}
```

Fields:

- `data_path`: configured FCC lookup directory.
- `available`: true when `EN.dat` and `EN.idx` exist.
- `updated_at`: UTC timestamp from the local `EN.dat` file modification time.
- `age_days`: integer age of the local `EN.dat` file, or `null` if missing.
- `files`: presence flags for required local lookup files.

Client applications should call this endpoint before relying on lookup results if stale or missing data matters.

### Update FCC database

```http
POST /api/fcc/update
```

Example:

```bash
curl -X POST "http://127.0.0.1:8088/api/fcc/update"
```

What it does:

1. Downloads the FCC amateur-license complete dump from:

   ```text
   https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
   ```

2. Extracts `EN.dat` and `HD.dat` into the configured local FCC data directory.
3. Rebuilds `data/EN.idx`.
4. Uses `HD.dat` to index only active licenses when available.
5. Returns the updated database status.

Example response:

```json
{
  "ok": true,
  "indexed_count": 750000,
  "active_filter": true,
  "index_path": "/path/to/fcc_database_web_app/data/EN.idx",
  "status": {
    "data_path": "/path/to/fcc_database_web_app",
    "available": true,
    "updated_at": "2026-06-16T12:00:00+00:00",
    "age_days": 0,
    "files": {
      "EN.dat": true,
      "EN.idx": true,
      "zipcodes.csv": true
    }
  }
}
```

Failure response example:

```json
{
  "ok": false,
  "error": "<error message>",
  "status": {
    "available": false,
    "age_days": null
  }
}
```

The update endpoint requires internet access from the machine running Net Logger and may take a few minutes.

## Example client usage

Python:

```python
import requests

base_url = "http://127.0.0.1:8088"

status = requests.get(f"{base_url}/api/fcc/status", timeout=5).json()
if not status["available"]:
    raise RuntimeError("Local FCC database is unavailable")

lookup = requests.get(
    f"{base_url}/api/lookup",
    params={"callsign": "K5SUB"},
    timeout=5,
).json()

if lookup["found"]:
    print(lookup["result"]["name"])
```

Shell:

```bash
FCC_API="http://127.0.0.1:8088"
curl "$FCC_API/api/fcc/status"
curl "$FCC_API/api/lookup?callsign=K5SUB"
```

## Security and deployment notes

- These endpoints are designed for trusted local/LAN use.
- There is currently no authentication on the local Flask API.
- Avoid exposing the service directly to the public internet.
- The update endpoint writes files in the configured FCC lookup directory and downloads data from the FCC.
- If other applications depend on this API, run Net Logger as a local service and keep the port stable.

## Possible reuse cases

Other applications could use this API for:

- Callsign enrichment in loggers or net-control tools.
- Offline/LAN callsign lookup dashboards.
- Amateur-radio contact-management utilities.
- Repeater, AllStarLink, or event-logging tools that need operator name, city/state, or approximate grid square.
- Scheduled freshness checks using `/api/fcc/status`.
