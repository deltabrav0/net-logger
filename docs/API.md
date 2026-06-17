# Net Logger API Reference

This document is a human-readable, Swagger-style reference for the Net Logger API.

For tooling, import the OpenAPI specification into Swagger UI, Redoc, Insomnia, Postman, or similar tools:

```text
docs/openapi.yaml
```

When the app is running, an interactive Swagger UI page is available at:

```text
http://127.0.0.1:8088/api/docs
```

The served OpenAPI document is available at:

```text
http://127.0.0.1:8088/openapi.yaml
```

Base URL when running locally:

```text
http://127.0.0.1:8088
```

All JSON endpoints return `application/json` unless otherwise noted. The CSV export endpoint returns `text/csv`.

> Security note: Net Logger is intended for trusted local/LAN use. The current Flask API does not implement built-in authentication or authorization. Do not expose it directly to the public internet without an authenticated reverse proxy or other access control.

## Tags

- **Stations** — known callsign/operator records.
- **FCC Lookup** — local FCC flat-file lookup and maintenance endpoints.
- **Sessions** — net sessions and active-board state.
- **Check-ins** — station check-ins within sessions.
- **Metrics** — aggregate check-in reporting.
- **Export** — CSV export.
- **Administrative** — destructive maintenance endpoints.

## Data model summary

### Station

A known callsign/operator record.

```json
{
  "id": 1,
  "callsign": "K5SUB",
  "name": "Daniel Butler",
  "city": "Lufkin",
  "state": "TX",
  "grid": "EM21QG",
  "lat": 31.27,
  "lon": -94.6469,
  "notes": "optional",
  "source": "manual",
  "created_at": "2026-06-16 19:00:00",
  "last_heard_at": "2026-06-16 19:01:00"
}
```

### Net session

One running or historical net.

```json
{
  "id": 12,
  "name": "Weekly Net",
  "frequency": "146.520 MHz",
  "net_control": "K5SUB",
  "status": "open",
  "started_at": "2026-06-16 19:00:00",
  "closed_at": null
}
```

### Check-in

A station checked into a specific net session.

```json
{
  "id": 34,
  "session_id": 12,
  "sequence": 1,
  "checked_in_at": "2026-06-16 19:01:00",
  "traffic": false,
  "traffic_details": "",
  "notes": "Optional signal/report notes",
  "station": {
    "id": 1,
    "callsign": "K5SUB",
    "name": "Daniel Butler",
    "city": "Lufkin",
    "state": "TX",
    "grid": "EM21QG",
    "lat": 31.27,
    "lon": -94.6469,
    "last_heard_at": "2026-06-16 19:01:00"
  }
}
```

## Endpoint summary

- `GET /api/stations`
- `POST /api/stations`
- `GET /api/lookup?callsign=K5SUB`
- `GET /api/fcc/status`
- `POST /api/fcc/update`
- `GET /api/sessions`
- `POST /api/sessions/start`
- `GET /api/sessions/{session_id}/board`
- `POST /api/sessions/{session_id}/checkins`
- `PATCH /api/checkins/{checkin_id}`
- `DELETE /api/checkins/{checkin_id}`
- `POST /api/sessions/{session_id}/stop`
- `GET /api/metrics?period=month`
- `GET /api/export.csv`
- `DELETE /api/records?dry_run=true`
- `DELETE /api/records`

---

## Stations

### `GET /api/stations`

List known stations ordered by callsign.

**Tags:** `Stations`

**Operation ID:** `listStations`

#### Query parameters

- `q` string, optional — case-insensitive callsign/name search string.

#### Responses

- `200 OK` — array of `Station` objects.

#### Example request

```bash
curl http://127.0.0.1:8088/api/stations
```

#### Example response

```json
[
  {
    "id": 1,
    "callsign": "K5SUB",
    "name": "Daniel Butler",
    "city": "Lufkin",
    "state": "TX",
    "grid": "EM21QG",
    "lat": 31.27,
    "lon": -94.6469,
    "notes": "optional",
    "source": "manual",
    "created_at": "2026-06-16 19:00:00",
    "last_heard_at": "2026-06-16 19:01:00"
  }
]
```

---

### `POST /api/stations`

Create a station.

**Tags:** `Stations`

**Operation ID:** `createStation`

Callsigns are normalized to uppercase with whitespace removed. If the callsign already exists, the existing station is returned with HTTP `200`.

#### Request body

Content type: `application/json`

Required fields:

- `callsign` string

Optional fields:

- `name` string
- `city` string
- `state` string
- `grid` string
- `lat` number or null
- `lon` number or null
- `notes` string
- `source` string, default `manual`

#### Example request

```bash
curl -X POST http://127.0.0.1:8088/api/stations \
  -H 'Content-Type: application/json' \
  -d '{
    "callsign": "K5SUB",
    "name": "Daniel Butler",
    "city": "Lufkin",
    "state": "TX",
    "grid": "EM21QG",
    "lat": 31.27,
    "lon": -94.6469,
    "notes": "optional",
    "source": "manual"
  }'
```

#### Responses

- `201 Created` — station created.
- `200 OK` — station already existed; existing record returned.
- `400 Bad Request` — callsign is missing.

---

## FCC Lookup

Net Logger also exposes these endpoints as a small local FCC database API that other trusted local/LAN applications can reuse. See [Local FCC Database API](FCC_DATABASE_API.md) for integration guidance, client examples, and deployment notes.

### `GET /api/lookup`

Look up a callsign in the local FCC database.

**Tags:** `FCC Lookup`

**Operation ID:** `lookupCallsign`

Set `NET_LOGGER_FCC_LOOKUP_PATH` to the directory containing the FCC flat-file lookup data.

#### Query parameters

- `callsign` string, required — callsign to look up.

#### Example request

```bash
curl "http://127.0.0.1:8088/api/lookup?callsign=K5SUB"
```

#### Responses

- `200 OK` — lookup result. Not-found responses still return `200` with `found: false`.

#### Example response: found

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

#### Example response: not found

```json
{
  "ok": true,
  "found": false,
  "callsign": "K5SUB"
}
```

---

### `GET /api/fcc/status`

Get local FCC database status.

**Tags:** `FCC Lookup`

**Operation ID:** `getFccStatus`

#### Responses

- `200 OK` — FCC data availability and approximate age.

#### Example response

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

---

### `POST /api/fcc/update`

Download and rebuild the local FCC database index.

**Tags:** `FCC Lookup`

**Operation ID:** `updateFccDatabase`

Downloads the FCC amateur-license complete file from:

```text
https://data.fcc.gov/download/pub/uls/complete/l_amat.zip
```

Then extracts `EN.dat` and `HD.dat`, and rebuilds `data/EN.idx`. When `HD.dat` is available, only active licenses are indexed.

#### Responses

- `200 OK` — update succeeded.
- `500 Internal Server Error` — update failed.

#### Example success response

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

#### Example error response

```json
{
  "ok": false,
  "error": "download failed",
  "status": {
    "available": false,
    "age_days": null
  }
}
```

---

## Sessions

### `GET /api/sessions`

List saved net sessions with check-in and traffic counts.

**Tags:** `Sessions`

**Operation ID:** `listSessions`

#### Responses

- `200 OK` — array of session summaries ordered by start time descending.

#### Example response

```json
[
  {
    "id": 12,
    "name": "Weekly Net",
    "frequency": "146.520 MHz",
    "net_control": "K5SUB",
    "status": "open",
    "started_at": "2026-06-16 19:00:00",
    "closed_at": null,
    "checkin_count": 24,
    "traffic_count": 2
  }
]
```

---

### `POST /api/sessions/start`

Start a new net session.

**Tags:** `Sessions`

**Operation ID:** `startSession`

Creates a new open net session. If `net_control` is provided, the callsign is normalized, ensured as a station, and automatically checked in as sequence `1`.

#### Request body

Content type: `application/json`

Optional fields:

- `name` string
- `frequency` string
- `net_control` string

#### Example request

```bash
curl -X POST http://127.0.0.1:8088/api/sessions/start \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Weekly Net",
    "frequency": "146.520 MHz",
    "net_control": "K5SUB"
  }'
```

#### Responses

- `201 Created` — session created.

---

### `GET /api/sessions/{session_id}/board`

Get the active board for a session.

**Tags:** `Sessions`

**Operation ID:** `getSessionBoard`

#### Path parameters

- `session_id` integer, required — session ID.

#### Responses

- `200 OK` — session metadata, known stations not checked in, and check-ins.
- `404 Not Found` — session not found.

#### Example response

```json
{
  "session": {
    "id": 12,
    "name": "Weekly Net",
    "frequency": "146.520 MHz",
    "net_control": "K5SUB",
    "status": "open",
    "started_at": "2026-06-16 19:00:00",
    "closed_at": null
  },
  "known_stations": [],
  "checkins": [
    {
      "id": 34,
      "session_id": 12,
      "sequence": 1,
      "checked_in_at": "2026-06-16 19:01:00",
      "traffic": false,
      "traffic_details": "",
      "notes": "",
      "station": {
        "id": 1,
        "callsign": "K5SUB",
        "name": "Daniel Butler",
        "city": "Lufkin",
        "state": "TX",
        "grid": "EM21QG",
        "lat": 31.27,
        "lon": -94.6469,
        "last_heard_at": "2026-06-16 19:01:00"
      }
    }
  ]
}
```

---

### `POST /api/sessions/{session_id}/stop`

Stop a net session.

**Tags:** `Sessions`

**Operation ID:** `stopSession`

Marks the session `closed` and sets `closed_at` if it was not already closed.

#### Path parameters

- `session_id` integer, required — session ID.

#### Responses

- `200 OK` — updated session.
- `404 Not Found` — session not found.

---

## Check-ins

### `POST /api/sessions/{session_id}/checkins`

Create a check-in for a session.

**Tags:** `Check-ins`

**Operation ID:** `createCheckin`

Duplicate check-ins for the same session/station are idempotent and return the existing check-in with HTTP `200`. New check-ins return HTTP `201`. The station `last_heard_at` timestamp is updated for new check-ins.

#### Path parameters

- `session_id` integer, required — session ID.

#### Request body

Content type: `application/json`

Required fields:

- `station_id` integer

Optional fields:

- `traffic` boolean, default `false`
- `traffic_details` string
- `notes` string

#### Example request

```bash
curl -X POST http://127.0.0.1:8088/api/sessions/12/checkins \
  -H 'Content-Type: application/json' \
  -d '{
    "station_id": 1,
    "traffic": true,
    "traffic_details": "Announcement for the group",
    "notes": "Optional signal/report notes"
  }'
```

#### Responses

- `201 Created` — check-in created.
- `200 OK` — check-in already existed; existing record returned.
- `400 Bad Request` — `station_id` is missing.

---

### `PATCH /api/checkins/{checkin_id}`

Update check-in traffic or notes.

**Tags:** `Check-ins`

**Operation ID:** `updateCheckin`

#### Path parameters

- `checkin_id` integer, required — check-in ID.

#### Request body

Content type: `application/json`

May include any of:

- `traffic` boolean
- `traffic_details` string
- `notes` string

#### Example request

```bash
curl -X PATCH http://127.0.0.1:8088/api/checkins/34 \
  -H 'Content-Type: application/json' \
  -d '{
    "traffic": true,
    "traffic_details": "Updated details",
    "notes": "Updated notes"
  }'
```

#### Responses

- `200 OK` — updated check-in.
- `404 Not Found` — check-in not found.

---

### `DELETE /api/checkins/{checkin_id}`

Delete one check-in.

**Tags:** `Check-ins`

**Operation ID:** `deleteCheckin`

Use this to correct accidental check-ins.

#### Path parameters

- `checkin_id` integer, required — check-in ID.

#### Responses

- `204 No Content` — check-in deleted. Empty response body.
- `404 Not Found` — check-in not found.

---

## Metrics

### `GET /api/metrics`

Get aggregate check-in metrics.

**Tags:** `Metrics`

**Operation ID:** `getMetrics`

#### Query parameters

- `period` string, optional — bucket size for `series_by_net`.
  - Allowed values: `week`, `month`, `year`
  - Default: `month`
  - Invalid values default to `month`.

#### Example request

```bash
curl "http://127.0.0.1:8088/api/metrics?period=month"
```

#### Responses

- `200 OK` — check-in metrics grouped by net and selected period.

#### Example response

```json
{
  "period": "month",
  "by_net": [
    {
      "net_name": "Weekly Net",
      "checkin_count": 24
    }
  ],
  "by_date": [
    {
      "date": "2026-06-16",
      "checkin_count": 8
    }
  ],
  "series_by_net": [
    {
      "net_name": "Weekly Net",
      "points": [
        {
          "bucket": "2026-06",
          "checkin_count": 24
        }
      ]
    }
  ]
}
```

---

## Export

### `GET /api/export.csv`

Export all or one session as CSV.

**Tags:** `Export`

**Operation ID:** `exportCsv`

#### Query parameters

- `session_id` integer, optional — if omitted, all sessions are exported.

#### CSV columns

```text
session_id,session_name,frequency,net_control,status,started_at,closed_at,sequence,checked_in_at,callsign,station_name,city,state,grid,lat,lon,traffic,traffic_details,checkin_notes
```

#### Example requests

```bash
curl http://127.0.0.1:8088/api/export.csv
curl "http://127.0.0.1:8088/api/export.csv?session_id=12"
```

#### Responses

- `200 OK` — CSV export.
  - Content type: `text/csv`
  - Header: `Content-Disposition: attachment; filename=net-logger-export.csv`

---

## Administrative

### `DELETE /api/records`

Delete all application records.

**Tags:** `Administrative`

**Operation ID:** `deleteAllRecords`

Deletes all application records from the SQLite database:

- check-ins,
- net sessions,
- stations.

Warning: this endpoint is destructive and cannot be undone except by restoring a database backup.

#### Query parameters

- `dry_run` boolean, optional — return counts without deleting anything.

#### Example: dry run

```bash
curl -X DELETE "http://127.0.0.1:8088/api/records?dry_run=true"
```

#### Example dry-run response

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

#### Example: delete records

```bash
curl -X DELETE http://127.0.0.1:8088/api/records
```

#### Example delete response

```json
{
  "deleted": {
    "checkins": 24,
    "net_sessions": 8,
    "stations": 12
  }
}
```

#### Responses

- `200 OK` — delete result or dry-run counts.

---

## Loading the OpenAPI file in Swagger UI

If you have Docker installed, one quick local preview option is:

```bash
docker run --rm -p 8089:8080 \
  -e SWAGGER_JSON=/spec/openapi.yaml \
  -v "$PWD/docs/openapi.yaml:/spec/openapi.yaml" \
  swaggerapi/swagger-ui
```

Then open:

```text
http://127.0.0.1:8089
```

You can also paste `docs/openapi.yaml` into the online Swagger Editor or import it into Postman/Insomnia.
