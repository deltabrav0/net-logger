# Net Logger API Documentation

Base URL when running locally:

```text
http://127.0.0.1:8088
```

All JSON endpoints return `application/json` unless otherwise noted.

## Data model summary

- **Station**: A known callsign/operator record.
- **Net session**: One running or historical net.
- **Check-in**: A station checked into a specific net session.

## Stations

### List stations

```http
GET /api/stations
GET /api/stations?q=K5
```

Query parameters:

- `q` optional callsign/name search string.

Example:

```bash
curl http://127.0.0.1:8088/api/stations
```

### Create station

```http
POST /api/stations
Content-Type: application/json
```

Request body:

```json
{
  "callsign": "K5SUB",
  "name": "Daniel Butler",
  "city": "Lufkin",
  "state": "TX",
  "grid": "EM21QG",
  "lat": 31.27,
  "lon": -94.6469,
  "notes": "optional",
  "source": "manual"
}
```

Notes:

- `callsign` is required.
- Callsigns are normalized to uppercase with whitespace removed.
- If the callsign already exists, the existing station is returned with HTTP `200`.
- New stations return HTTP `201`.

## FCC lookup

Net Logger also exposes these endpoints as a small local FCC database API that other trusted local/LAN applications can reuse. See [Local FCC Database API](FCC_DATABASE_API.md) for integration guidance, client examples, and deployment notes.

### Lookup callsign

```http
GET /api/lookup?callsign=K5SUB
```

Example response when found:

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

Example response when not found or local FCC files are unavailable:

```json
{
  "ok": true,
  "found": false,
  "callsign": "K5SUB"
}
```

FCC lookup is local/off-grid. Set `NET_LOGGER_FCC_LOOKUP_PATH` to the directory containing the FCC flat-file lookup data.

### Get FCC database status

```http
GET /api/fcc/status
```

Returns local FCC data availability and the age of `data/EN.dat`:

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

### Update FCC database

```http
POST /api/fcc/update
```

Downloads the FCC amateur-license complete file from `https://data.fcc.gov/download/pub/uls/complete/l_amat.zip`, extracts `EN.dat` and `HD.dat`, and rebuilds `data/EN.idx`. When `HD.dat` is available, only active licenses are indexed.

Example response:

```json
{
  "ok": true,
  "indexed_count": 750000,
  "active_filter": true,
  "index_path": "/path/to/fcc_database_web_app/data/EN.idx",
  "status": {
    "available": true,
    "age_days": 0
  }
}
```

## Sessions

### List sessions

```http
GET /api/sessions
```

Returns saved sessions with check-in and traffic counts.

### Start net session

```http
POST /api/sessions/start
Content-Type: application/json
```

Request body:

```json
{
  "name": "Weekly Net",
  "frequency": "146.520 MHz",
  "net_control": "K5SUB"
}
```

Behavior:

- Creates a new open net session.
- Normalizes `net_control` to uppercase.
- If `net_control` is provided, it automatically ensures that callsign exists as a station:
  - uses the existing station if known,
  - otherwise attempts local FCC lookup,
  - otherwise creates a callsign-only station.
- Automatically checks Net Control into the new session as the first check-in.

### Get session board

```http
GET /api/sessions/{session_id}/board
```

Returns:

- `session`: session metadata,
- `known_stations`: stations not checked into this session,
- `checkins`: checked-in stations in sequence order.

### Stop session

```http
POST /api/sessions/{session_id}/stop
```

Marks the session `closed` and sets `closed_at` if it was not already closed.

## Check-ins

### Create check-in

```http
POST /api/sessions/{session_id}/checkins
Content-Type: application/json
```

Request body:

```json
{
  "station_id": 1,
  "traffic": true,
  "traffic_details": "Announcement for the group",
  "notes": "Optional signal/report notes"
}
```

Notes:

- `station_id` is required.
- Duplicate check-ins for the same session/station are idempotent and return the existing check-in with HTTP `200`.
- New check-ins return HTTP `201`.
- The station `last_heard_at` timestamp is updated.

### Update check-in

```http
PATCH /api/checkins/{checkin_id}
Content-Type: application/json
```

Request body may include any of:

```json
{
  "traffic": true,
  "traffic_details": "Updated details",
  "notes": "Updated notes"
}
```

### Delete check-in

```http
DELETE /api/checkins/{checkin_id}
```

Removes one check-in. Use this to correct accidental check-ins.

## Metrics

### Get metrics

```http
GET /api/metrics
GET /api/metrics?period=week
GET /api/metrics?period=month
GET /api/metrics?period=year
```

Returns check-in metrics grouped by net and selected period.

`period` values:

- `week`
- `month` default
- `year`

Invalid period values default to `month`.

## CSV export

### Export all sessions

```http
GET /api/export.csv
```

### Export one session

```http
GET /api/export.csv?session_id=12
```

Returns `text/csv`.

## Administrative reset

### Delete all records

```http
DELETE /api/records
```

Deletes all application records from the SQLite database:

- check-ins,
- net sessions,
- stations.

Example:

```bash
curl -X DELETE http://127.0.0.1:8088/api/records
```

Example response:

```json
{
  "deleted": {
    "checkins": 24,
    "net_sessions": 8,
    "stations": 12
  }
}
```

### Dry-run delete all records

```http
DELETE /api/records?dry_run=true
```

Returns counts without deleting anything.

Example:

```bash
curl -X DELETE "http://127.0.0.1:8088/api/records?dry_run=true"
```

Example response:

```json
{
  "dry_run": true,
  "would_delete": {
    "checkins": 24,
    "net_sessions": 8,
    "stations": 12
  }
}
```

Warning: `DELETE /api/records` is destructive and cannot be undone except by restoring a database backup.
