"""Flask application factory for the Kanban net logger."""

from __future__ import annotations

import base64
import csv
import io
import json
import os
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as request_lib

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

from . import db
from .fcc_lookup import fcc_database_status, lookup_callsign, update_fcc_database


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")
    database = os.path.join(app.instance_path, "net_logger.sqlite3")
    app.config.update(
        DATABASE=database,
        LOGO_PATH=os.environ.get("NET_LOGGER_LOGO_PATH"),
        WORDPRESS_ENDPOINT=os.environ.get("NET_LOGGER_WORDPRESS_ENDPOINT", ""),
        WORDPRESS_USERNAME=os.environ.get("NET_LOGGER_WORDPRESS_USERNAME", ""),
        WORDPRESS_APPLICATION_PASSWORD=os.environ.get("NET_LOGGER_WORDPRESS_APPLICATION_PASSWORD", ""),
        WORDPRESS_TIMEOUT=int(os.environ.get("NET_LOGGER_WORDPRESS_TIMEOUT", "20")),
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).expanduser().parent.mkdir(parents=True, exist_ok=True)
    db.init_db(app.config["DATABASE"])

    def con():
        return db.connect(app.config["DATABASE"])

    def station_from_row(row):
        item = db.row_to_dict(row)
        if not item:
            return None
        return item

    def checkin_from_row(row):
        item = db.row_to_dict(row)
        if not item:
            return None
        station = {
            "id": item.pop("station_id"),
            "callsign": item.pop("callsign"),
            "name": item.pop("name"),
            "city": item.pop("city"),
            "state": item.pop("state"),
            "grid": item.pop("grid"),
            "lat": item.pop("lat"),
            "lon": item.pop("lon"),
            "last_heard_at": item.pop("last_heard_at"),
        }
        item["traffic"] = bool(item["traffic"])
        item["station"] = station
        return item

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/app-logo.png")
    def app_logo():
        custom_logo = app.config.get("LOGO_PATH")
        if custom_logo and Path(custom_logo).is_file():
            return send_file(custom_logo, mimetype="image/png")
        return send_from_directory(app.static_folder, "app-logo.png")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/openapi.yaml")
    def openapi_spec():
        spec_path = Path(__file__).resolve().parent / "openapi.yaml"
        return Response(spec_path.read_text(encoding="utf-8"), mimetype="application/yaml")

    @app.get("/api/docs")
    def api_docs():
        return Response(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Net Logger API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    body { margin: 0; background: #fafafa; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: '/openapi.yaml',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis],
      layout: 'BaseLayout'
    });
  </script>
</body>
</html>
""",
            mimetype="text/html",
        )

    @app.get("/api/stations")
    def list_stations():
        q = (request.args.get("q") or "").strip().upper()
        sql = "SELECT * FROM stations"
        params: list[Any] = []
        if q:
            sql += " WHERE callsign LIKE ? OR upper(name) LIKE ?"
            params.extend([f"%{q}%", f"%{q}%"])
        sql += " ORDER BY callsign"
        with con() as c:
            rows = c.execute(sql, params).fetchall()
        return jsonify([station_from_row(r) for r in rows])

    @app.post("/api/stations")
    def create_station():
        payload = request.get_json(silent=True) or {}
        callsign = db.normalize_callsign(payload.get("callsign", ""))
        if not callsign:
            return jsonify({"error": "callsign is required"}), 400
        fields = {
            "callsign": callsign,
            "name": (payload.get("name") or "").strip(),
            "city": (payload.get("city") or "").strip(),
            "state": (payload.get("state") or "").strip().upper(),
            "grid": (payload.get("grid") or "").strip().upper(),
            "lat": payload.get("lat"),
            "lon": payload.get("lon"),
            "notes": (payload.get("notes") or "").strip(),
            "source": (payload.get("source") or "manual").strip() or "manual",
        }
        with con() as c:
            existing = c.execute("SELECT * FROM stations WHERE callsign = ?", (callsign,)).fetchone()
            if existing:
                return jsonify(station_from_row(existing)), 200
            cur = c.execute(
                """
                INSERT INTO stations (callsign, name, city, state, grid, lat, lon, notes, source)
                VALUES (:callsign, :name, :city, :state, :grid, :lat, :lon, :notes, :source)
                """,
                fields,
            )
            row = c.execute("SELECT * FROM stations WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(station_from_row(row)), 201

    @app.delete("/api/stations/<int:station_id>")
    def delete_station(station_id: int):
        with con() as c:
            cur = c.execute("DELETE FROM stations WHERE id = ?", (station_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "station not found"}), 404
        return "", 204

    @app.post("/api/stations/<int:station_id>/refresh-fcc")
    def refresh_station_from_fcc(station_id: int):
        with con() as c:
            station = c.execute("SELECT * FROM stations WHERE id = ?", (station_id,)).fetchone()
            if station is None:
                return jsonify({"error": "station not found"}), 404

            callsign = station["callsign"]
            lookup = lookup_callsign(callsign)
            if not (lookup.get("ok") and lookup.get("found") and lookup.get("result")):
                return jsonify({"error": "FCC record not found", "callsign": callsign}), 404

            result = lookup["result"]
            c.execute(
                """
                UPDATE stations
                SET name = ?, city = ?, state = ?, grid = ?, lat = ?, lon = ?, source = 'fcc'
                WHERE id = ?
                """,
                (
                    (result.get("name") or "").strip(),
                    (result.get("city") or "").strip(),
                    (result.get("state") or "").strip().upper(),
                    (result.get("grid") or "").strip().upper(),
                    result.get("lat"),
                    result.get("lon"),
                    station_id,
                ),
            )
            row = c.execute("SELECT * FROM stations WHERE id = ?", (station_id,)).fetchone()
        return jsonify(station_from_row(row))

    @app.get("/api/sessions")
    def list_sessions():
        with con() as c:
            rows = c.execute(
                """
                SELECT ns.*,
                       COUNT(ch.id) AS checkin_count,
                       COALESCE(SUM(CASE WHEN ch.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count,
                       MAX(wp.pushed_at) AS wordpress_pushed_at,
                       MAX(wp.wordpress_event_id) AS wordpress_event_id
                FROM net_sessions ns
                LEFT JOIN checkins ch ON ch.session_id = ns.id
                LEFT JOIN wordpress_pushes wp ON wp.session_id = ns.id
                GROUP BY ns.id
                ORDER BY ns.started_at DESC, ns.id DESC
                """
            ).fetchall()
        return jsonify([db.row_to_dict(r) for r in rows])

    def export_rows(session_id: str | None = None):
        sql = """
            SELECT ns.id AS session_id, ns.name AS session_name, ns.frequency, ns.net_control,
                   ns.status, ns.started_at, ns.closed_at,
                   ch.sequence, ch.checked_in_at, ch.traffic, ch.traffic_details, ch.notes AS checkin_notes,
                   s.callsign, s.name AS station_name, s.city, s.state, s.grid, s.lat, s.lon
            FROM net_sessions ns
            LEFT JOIN checkins ch ON ch.session_id = ns.id
            LEFT JOIN stations s ON s.id = ch.station_id
        """
        params: list[Any] = []
        if session_id:
            sql += " WHERE ns.id = ?"
            params.append(session_id)
        sql += " ORDER BY ns.started_at DESC, ns.id DESC, ch.sequence"
        with con() as c:
            return c.execute(sql, params).fetchall()

    @app.get("/api/export.csv")
    def export_csv():
        rows = export_rows(request.args.get("session_id"))
        output = io.StringIO()
        fieldnames = [
            "session_id", "session_name", "frequency", "net_control", "status", "started_at", "closed_at",
            "sequence", "checked_in_at", "callsign", "station_name", "city", "state", "grid", "lat", "lon",
            "traffic", "traffic_details", "checkin_notes",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            item = db.row_to_dict(row)
            if item.get("traffic") is not None:
                item["traffic"] = "yes" if item["traffic"] else "no"
            writer.writerow({key: item.get(key, "") for key in fieldnames})
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=net-logger-export.csv"},
        )

    def build_wordpress_payload(session_id: int):
        with con() as c:
            session = c.execute("SELECT * FROM net_sessions WHERE id = ?", (session_id,)).fetchone()
            if session is None:
                return None
            checkins = c.execute(
                """
                SELECT ch.*, s.id AS station_id, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.source
                FROM checkins ch
                JOIN stations s ON s.id = ch.station_id
                WHERE ch.session_id = ?
                ORDER BY ch.sequence
                """,
                (session_id,),
            ).fetchall()
        session_item = db.row_to_dict(session)
        if session_item is None:
            return None
        attendance = []
        for row in checkins:
            item = db.row_to_dict(row)
            callsign = item["callsign"]
            attendance.append({
                "sequence": item["sequence"],
                "checked_in_at": item["checked_in_at"],
                "status": "present",
                "role": "net_control" if callsign == session_item.get("net_control") else None,
                "traffic": bool(item["traffic"]),
                "traffic_details": item["traffic_details"],
                "notes": item["notes"],
                "participant": {
                    "external_id": str(item["station_id"]),
                    "source": item.get("source") or "net_logger",
                    "callsign": callsign,
                    "name": item["name"],
                    "city": item["city"],
                    "state": item["state"],
                    "grid": item["grid"],
                    "lat": item["lat"],
                    "lon": item["lon"],
                },
                "metadata": {"net_logger_checkin_id": item["id"]},
            })
        return {
            "source": "net_logger",
            "external_id": str(session_item["id"]),
            "event": {
                "name": session_item["name"] or "Imported Net",
                "event_type": "Repeater Net",
                "frequency": session_item["frequency"],
                "net_control": session_item["net_control"],
                "status": session_item["status"],
                "started_at": session_item["started_at"],
                "ended_at": session_item["closed_at"],
                "metadata": {"net_logger_session": session_item},
            },
            "attendance": attendance,
        }

    @app.get("/api/sessions/<int:session_id>/wordpress-payload")
    def wordpress_payload(session_id: int):
        payload = build_wordpress_payload(session_id)
        if payload is None:
            return jsonify({"error": "session not found"}), 404
        return jsonify(payload)

    @app.post("/api/sessions/<int:session_id>/send-wordpress")
    def send_wordpress(session_id: int):
        endpoint = (app.config.get("WORDPRESS_ENDPOINT") or "").strip()
        username = (app.config.get("WORDPRESS_USERNAME") or "").strip()
        password = (app.config.get("WORDPRESS_APPLICATION_PASSWORD") or "").strip()
        if not (endpoint and username and password):
            return jsonify({"error": "WordPress endpoint, username, and application password are required"}), 400

        payload = build_wordpress_payload(session_id)
        if payload is None:
            return jsonify({"error": "session not found"}), 404

        with con() as c:
            existing = c.execute(
                "SELECT * FROM wordpress_pushes WHERE session_id = ? AND endpoint = ?",
                (session_id, endpoint),
            ).fetchone()
            if existing:
                return jsonify({"error": "session already sent to WordPress", "push": db.row_to_dict(existing)}), 409

        body = json.dumps(payload).encode("utf-8")
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        req = request_lib.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with request_lib.urlopen(req, timeout=app.config["WORDPRESS_TIMEOUT"]) as response:
                response_text = response.read().decode("utf-8")
                response_data = json.loads(response_text) if response_text else {}
                status = getattr(response, "status", 201)
        except urlerror.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="replace")
            return jsonify({"error": "WordPress import failed", "status": exc.code, "response": error_text}), 502
        except Exception as exc:
            return jsonify({"error": "WordPress import failed", "details": str(exc)}), 502

        if status < 200 or status >= 300 or not response_data.get("ok", True):
            return jsonify({"error": "WordPress import failed", "status": status, "response": response_data}), 502

        with con() as c:
            c.execute(
                """
                INSERT INTO wordpress_pushes (session_id, endpoint, wordpress_event_id, response_json)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, endpoint, str(response_data.get("event_id") or ""), json.dumps(response_data)),
            )
            push = c.execute(
                "SELECT * FROM wordpress_pushes WHERE session_id = ? AND endpoint = ?",
                (session_id, endpoint),
            ).fetchone()
        return jsonify({"ok": True, "wordpress": response_data, "push": db.row_to_dict(push)}), 201

    @app.get("/api/metrics")
    def metrics():
        period = (request.args.get("period") or "month").strip().lower()
        net_name = (request.args.get("net_name") or "").strip()
        bucket_exprs = {
            "week": "strftime('%Y-W%W', ch.checked_in_at)",
            "month": "strftime('%Y-%m', ch.checked_in_at)",
            "year": "strftime('%Y', ch.checked_in_at)",
        }
        if period not in bucket_exprs:
            period = "month"
        bucket_expr = bucket_exprs[period]
        where_sql = "WHERE ns.name = ?" if net_name else ""
        date_join_sql = "JOIN net_sessions ns ON ns.id = ch.session_id" if net_name else ""
        date_where_sql = "WHERE ns.name = ?" if net_name else ""
        params = (net_name,) if net_name else ()
        with con() as c:
            by_net = c.execute(
                f"""
                SELECT ns.name AS net_name, COUNT(ch.id) AS checkin_count
                FROM net_sessions ns
                LEFT JOIN checkins ch ON ch.session_id = ns.id
                {where_sql}
                GROUP BY ns.name
                ORDER BY checkin_count DESC, ns.name
                """,
                params,
            ).fetchall()
            by_date = c.execute(
                f"""
                SELECT DATE(ch.checked_in_at) AS date, COUNT(ch.id) AS checkin_count
                FROM checkins ch
                {date_join_sql}
                {date_where_sql}
                GROUP BY DATE(ch.checked_in_at)
                ORDER BY date
                """,
                params,
            ).fetchall()
            series_rows = c.execute(
                f"""
                SELECT ns.name AS net_name,
                       {bucket_expr} AS bucket,
                       COUNT(ch.id) AS checkin_count
                FROM checkins ch
                JOIN net_sessions ns ON ns.id = ch.session_id
                {where_sql}
                GROUP BY ns.name, bucket
                ORDER BY ns.name, bucket
                """,
                params,
            ).fetchall()
        series_by_net: list[dict[str, Any]] = []
        series_index: dict[str, dict[str, Any]] = {}
        for row in series_rows:
            item = db.row_to_dict(row)
            net_name = item["net_name"] or "Untitled net"
            series = series_index.get(net_name)
            if series is None:
                series = {"net_name": net_name, "points": []}
                series_index[net_name] = series
                series_by_net.append(series)
            series["points"].append({"bucket": item["bucket"], "checkin_count": item["checkin_count"]})
        return jsonify({
            "period": period,
            "net_name": net_name,
            "by_net": [db.row_to_dict(r) for r in by_net],
            "by_date": [db.row_to_dict(r) for r in by_date],
            "series_by_net": series_by_net,
        })

    def ensure_station_for_callsign(c, callsign: str):
        call = db.normalize_callsign(callsign)
        if not call:
            return None
        existing = c.execute("SELECT * FROM stations WHERE callsign = ?", (call,)).fetchone()
        if existing:
            return existing

        lookup = lookup_callsign(call)
        result = lookup.get("result") if lookup.get("ok") and lookup.get("found") else {}
        fields = {
            "callsign": call,
            "name": (result.get("name") or "").strip(),
            "city": (result.get("city") or "").strip(),
            "state": (result.get("state") or "").strip().upper(),
            "grid": (result.get("grid") or "").strip().upper(),
            "lat": result.get("lat"),
            "lon": result.get("lon"),
            "notes": "",
            "source": "fcc" if result else "manual",
        }
        cur = c.execute(
            """
            INSERT INTO stations (callsign, name, city, state, grid, lat, lon, notes, source)
            VALUES (:callsign, :name, :city, :state, :grid, :lat, :lon, :notes, :source)
            """,
            fields,
        )
        return c.execute("SELECT * FROM stations WHERE id = ?", (cur.lastrowid,)).fetchone()

    def ensure_checkin(c, session_id: int, station_id: int):
        existing = c.execute(
            """
            SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
            FROM checkins ch JOIN stations s ON s.id = ch.station_id
            WHERE ch.session_id = ? AND ch.station_id = ?
            """,
            (session_id, station_id),
        ).fetchone()
        if existing:
            return existing
        next_seq = c.execute("SELECT COALESCE(MAX(sequence), 0) + 1 FROM checkins WHERE session_id = ?", (session_id,)).fetchone()[0]
        cur = c.execute(
            """
            INSERT INTO checkins (session_id, station_id, sequence, traffic, traffic_details, notes)
            VALUES (?, ?, ?, 0, '', '')
            """,
            (session_id, station_id, next_seq),
        )
        c.execute("UPDATE stations SET last_heard_at = CURRENT_TIMESTAMP WHERE id = ?", (station_id,))
        return c.execute(
            """
            SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
            FROM checkins ch JOIN stations s ON s.id = ch.station_id
            WHERE ch.id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()

    @app.delete("/api/records")
    def delete_all_records():
        dry_run = (request.args.get("dry_run") or "").strip().lower() in {"1", "true", "yes", "on"}
        with con() as c:
            counts = {
                "checkins": c.execute("SELECT COUNT(*) FROM checkins").fetchone()[0],
                "net_sessions": c.execute("SELECT COUNT(*) FROM net_sessions").fetchone()[0],
                "stations": c.execute("SELECT COUNT(*) FROM stations").fetchone()[0],
            }
            if dry_run:
                return jsonify({"dry_run": True, "would_delete": counts})
            c.execute("DELETE FROM checkins")
            c.execute("DELETE FROM net_sessions")
            c.execute("DELETE FROM stations")
        return jsonify({"deleted": counts})

    @app.post("/api/sessions/start")
    def start_session():
        payload = request.get_json(silent=True) or {}
        net_control = db.normalize_callsign(payload.get("net_control") or "")
        with con() as c:
            cur = c.execute(
                """
                INSERT INTO net_sessions (name, frequency, net_control)
                VALUES (?, ?, ?)
                """,
                (
                    (payload.get("name") or "").strip(),
                    (payload.get("frequency") or "").strip(),
                    net_control,
                ),
            )
            if net_control:
                station = ensure_station_for_callsign(c, net_control)
                if station:
                    ensure_checkin(c, cur.lastrowid, station["id"])
            row = c.execute("SELECT * FROM net_sessions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(db.row_to_dict(row)), 201

    @app.get("/api/sessions/<int:session_id>/board")
    def board(session_id: int):
        with con() as c:
            session = c.execute("SELECT * FROM net_sessions WHERE id = ?", (session_id,)).fetchone()
            if session is None:
                return jsonify({"error": "session not found"}), 404
            known = c.execute(
                """
                SELECT * FROM stations
                WHERE id NOT IN (SELECT station_id FROM checkins WHERE session_id = ?)
                ORDER BY callsign
                """,
                (session_id,),
            ).fetchall()
            checkins = c.execute(
                """
                SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
                FROM checkins ch
                JOIN stations s ON s.id = ch.station_id
                WHERE ch.session_id = ?
                ORDER BY ch.sequence
                """,
                (session_id,),
            ).fetchall()
        return jsonify({
            "session": db.row_to_dict(session),
            "known_stations": [station_from_row(r) for r in known],
            "checkins": [checkin_from_row(r) for r in checkins],
        })

    @app.post("/api/sessions/<int:session_id>/checkins")
    def create_checkin(session_id: int):
        payload = request.get_json(silent=True) or {}
        station_id = payload.get("station_id")
        if not station_id:
            return jsonify({"error": "station_id is required"}), 400
        with con() as c:
            existing = c.execute(
                """
                SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
                FROM checkins ch JOIN stations s ON s.id = ch.station_id
                WHERE ch.session_id = ? AND ch.station_id = ?
                """,
                (session_id, station_id),
            ).fetchone()
            if existing:
                return jsonify(checkin_from_row(existing)), 200
            next_seq = c.execute("SELECT COALESCE(MAX(sequence), 0) + 1 FROM checkins WHERE session_id = ?", (session_id,)).fetchone()[0]
            cur = c.execute(
                """
                INSERT INTO checkins (session_id, station_id, sequence, traffic, traffic_details, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    station_id,
                    next_seq,
                    1 if payload.get("traffic") else 0,
                    (payload.get("traffic_details") or "").strip(),
                    (payload.get("notes") or "").strip(),
                ),
            )
            c.execute("UPDATE stations SET last_heard_at = CURRENT_TIMESTAMP WHERE id = ?", (station_id,))
            row = c.execute(
                """
                SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
                FROM checkins ch JOIN stations s ON s.id = ch.station_id
                WHERE ch.id = ?
                """,
                (cur.lastrowid,),
            ).fetchone()
        return jsonify(checkin_from_row(row)), 201

    @app.patch("/api/checkins/<int:checkin_id>")
    def update_checkin(checkin_id: int):
        payload = request.get_json(silent=True) or {}
        with con() as c:
            c.execute(
                """
                UPDATE checkins
                SET traffic = COALESCE(?, traffic),
                    traffic_details = COALESCE(?, traffic_details),
                    notes = COALESCE(?, notes)
                WHERE id = ?
                """,
                (
                    None if "traffic" not in payload else (1 if payload.get("traffic") else 0),
                    None if "traffic_details" not in payload else (payload.get("traffic_details") or "").strip(),
                    None if "notes" not in payload else (payload.get("notes") or "").strip(),
                    checkin_id,
                ),
            )
            row = c.execute(
                """
                SELECT ch.*, s.callsign, s.name, s.city, s.state, s.grid, s.lat, s.lon, s.last_heard_at
                FROM checkins ch JOIN stations s ON s.id = ch.station_id
                WHERE ch.id = ?
                """,
                (checkin_id,),
            ).fetchone()
        if row is None:
            return jsonify({"error": "checkin not found"}), 404
        return jsonify(checkin_from_row(row))

    @app.delete("/api/checkins/<int:checkin_id>")
    def delete_checkin(checkin_id: int):
        with con() as c:
            cur = c.execute("DELETE FROM checkins WHERE id = ?", (checkin_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "checkin not found"}), 404
        return "", 204

    @app.post("/api/sessions/<int:session_id>/stop")
    def stop_session(session_id: int):
        with con() as c:
            c.execute(
                """
                UPDATE net_sessions
                SET status = 'closed', closed_at = COALESCE(closed_at, CURRENT_TIMESTAMP)
                WHERE id = ?
                """,
                (session_id,),
            )
            row = c.execute("SELECT * FROM net_sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return jsonify({"error": "session not found"}), 404
        return jsonify(db.row_to_dict(row))

    @app.delete("/api/sessions/<int:session_id>")
    def cancel_session(session_id: int):
        with con() as c:
            cur = c.execute("DELETE FROM net_sessions WHERE id = ?", (session_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "session not found"}), 404
        return "", 204

    @app.get("/api/lookup")
    def lookup():
        callsign = request.args.get("callsign") or ""
        return jsonify(lookup_callsign(callsign))

    @app.get("/api/fcc/status")
    def fcc_status():
        return jsonify(fcc_database_status())

    @app.post("/api/fcc/update")
    def update_fcc():
        try:
            return jsonify(update_fcc_database())
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc), "status": fcc_database_status()}), 500

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8088, debug=True)
