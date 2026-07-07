# Net & Meeting Attendance API

Namespace:

```text
/wp-json/net-attendance/v1
```

## Authentication

REST imports require a WordPress user who either has `manage_options` or the plugin's custom import capability:

```text
import_net_attendance
```

For Net Logger integration, use WordPress Application Passwords over HTTPS. Create an Application Password for a trusted Net Control user and send HTTP Basic authentication with the WordPress username and the generated application password. Do not store the password in source control or documentation.

On DETARC sites, only the Net Control role (`net_control`) should receive `import_net_attendance` for API pushes. The Net Attendance → Settings → API Import Permissions screen documents the import capability, but DETARC Member users retain view-only access to Events and Reports & Charts and should not be able to push Net Logger sessions. Administrators remain allowed automatically.

Unauthenticated requests must be rejected by WordPress before import logic writes data.

## Validate Import

```http
POST /wp-json/net-attendance/v1/imports/validate
Content-Type: application/json
```

Validates a payload and returns expected counts without writing rows.

## Create Import

```http
POST /wp-json/net-attendance/v1/imports
Content-Type: application/json
```

Creates or updates one attendance event plus participant/attendance rows.

Imports are intended to be idempotent:

- Event identity: `source + external_id`.
- Participant identity: callsign first, then `source + external_id`.
- Attendance identity: `event_id + participant_id`.

## Net Logger Session Endpoint

```http
POST /wp-json/net-attendance/v1/net-logger/sessions
Content-Type: application/json
Authorization: Basic base64(username:application-password)
```

This endpoint accepts the native Net Logger saved-session JSON shape, adapts it through the same importer used by `/imports`, and writes one event plus attendance rows.

A seeded example payload is available at:

```text
docs/sample-data/net-logger-session.json
```

Repeated pushes are idempotent. The plugin uses these constraints/lookups to avoid duplicate WordPress records:

- Event identity: `source + external_id`, where Net Logger sends `source: "net_logger"` and the saved session id as `external_id`.
- Participant identity: callsign first, then `source + external_id`.
- Attendance identity: `event_id + participant_id`.

The Net Logger app should also prevent duplicate sends after a successful push, but the WordPress importer remains safe if a request is retried.

## Generic Payload

A single-event import uses this shape:

```json
{
  "source": "net_logger",
  "external_id": "12",
  "event": {
    "name": "Tuesday Night Net",
    "event_type": "Repeater Net",
    "frequency": "147.180 MHz",
    "net_control": "K5SUB",
    "status": "closed",
    "started_at": "2026-06-16 19:00:00",
    "ended_at": "2026-06-16 19:45:00"
  },
  "attendance": [
    {
      "sequence": 1,
      "checked_in_at": "2026-06-16 19:01:00",
      "status": "present",
      "role": "net_control",
      "traffic": false,
      "traffic_details": "",
      "notes": "",
      "participant": {
        "external_id": "1",
        "callsign": "K5SUB",
        "name": "Daniel Butler",
        "city": "Lufkin",
        "state": "TX",
        "grid": "EM21QG"
      }
    }
  ]
}
```

## Batch Payload

Manual imports may include multiple events in one JSON file by wrapping individual event payloads in an `events` array:

```json
{
  "format": "net-attendance-logger-batch-v1",
  "events": [
    {
      "source": "net_logger_sample",
      "external_id": "sample-weekly-net-2026-06-03",
      "event": {
        "name": "Weekly Net",
        "event_type": "Repeater Net",
        "started_at": "2026-06-03 19:00:00"
      },
      "attendance": []
    }
  ]
}
```

## Response Shape

```json
{
  "ok": true,
  "dry_run": false,
  "event_id": 123,
  "created": {
    "events": 1,
    "participants": 1,
    "records": 1
  },
  "updated": {
    "events": 0,
    "participants": 0,
    "records": 0
  },
  "errors": []
}
```
