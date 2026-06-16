import os
import tempfile
from pathlib import Path

import pytest

from net_logger.app import create_app


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(prefix="net_logger_test_", suffix=".sqlite3")
    os.close(db_fd)
    try:
        app = create_app({"DATABASE": db_path, "TESTING": True})
        with app.test_client() as client:
            yield client
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_station_can_be_created_and_listed(client):
    res = client.post("/api/stations", json={"callsign": "km4ack", "name": "Jason", "city": "Maryville", "state": "TN"})
    assert res.status_code == 201
    station = res.get_json()
    assert station["callsign"] == "KM4ACK"
    assert station["name"] == "Jason"

    res = client.get("/api/stations?q=km4")
    assert res.status_code == 200
    data = res.get_json()
    assert [s["callsign"] for s in data] == ["KM4ACK"]


def test_session_board_starts_with_known_station_not_checked_in_without_net_control(client):
    created = client.post("/api/stations", json={"callsign": "W5XYZ", "name": "Example Op"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net", "frequency": "146.520"}).get_json()

    res = client.get(f"/api/sessions/{session['id']}/board")
    assert res.status_code == 200
    board = res.get_json()
    assert board["session"]["name"] == "Tuesday Net"
    assert [s["id"] for s in board["known_stations"]] == [created["id"]]
    assert board["checkins"] == []


def test_start_net_automatically_checks_in_known_net_control(client):
    net_control = client.post("/api/stations", json={"callsign": "K5NCS", "name": "Net Control"}).get_json()
    other = client.post("/api/stations", json={"callsign": "W5XYZ", "name": "Example Op"}).get_json()

    session = client.post("/api/sessions/start", json={"name": "Tuesday Net", "net_control": " k5ncs "}).get_json()

    board = client.get(f"/api/sessions/{session['id']}/board").get_json()
    assert [c["station"]["callsign"] for c in board["checkins"]] == ["K5NCS"]
    assert board["checkins"][0]["station"]["name"] == "Net Control"
    assert board["checkins"][0]["checked_in_at"]
    assert [s["callsign"] for s in board["known_stations"]] == ["W5XYZ"]
    assert net_control["id"] != other["id"]


def test_start_net_looks_up_and_checks_in_unknown_net_control_from_fcc(monkeypatch, tmp_path):
    fcc = tmp_path / "fcc"
    data = fcc / "data"
    data.mkdir(parents=True)
    (data / "EN.dat").write_bytes(b"EN|123|x|x|K5SUB|x|x|SUB CLUB|DANNY|x|BUTLER|x|x|x|x|x|MEMPHIS|TN|38101|\n")
    (data / "EN.idx").write_bytes(b"K5SUB|0\n")
    (data / "zipcodes.csv").write_text("zip,lat,lon\n38101,35.1495,-90.049\n")
    (fcc / "maidenhead.py").write_text("def latlon_to_grid(lat, lon, precision=6):\n    return 'EM55aa'\n")
    monkeypatch.setenv("NET_LOGGER_FCC_LOOKUP_PATH", str(fcc))

    db_fd, db_path = tempfile.mkstemp(prefix="net_logger_test_", suffix=".sqlite3")
    os.close(db_fd)
    try:
        app = create_app({"DATABASE": db_path, "TESTING": True})
        with app.test_client() as client:
            session = client.post("/api/sessions/start", json={"name": "Tuesday Net", "net_control": "k5sub"}).get_json()

            board = client.get(f"/api/sessions/{session['id']}/board").get_json()
            assert [c["station"]["callsign"] for c in board["checkins"]] == ["K5SUB"]
            station = board["checkins"][0]["station"]
            assert station["name"] == "DANNY BUTLER"
            assert station["city"] == "MEMPHIS"
            assert station["state"] == "TN"
            assert station["grid"] == "EM55AA"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_delete_all_records_clears_stations_sessions_checkins(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ", "name": "Example Op"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net", "net_control": "K5SUB"}).get_json()
    client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]})

    res = client.delete("/api/records")

    assert res.status_code == 200
    assert res.get_json() == {"deleted": {"checkins": 2, "net_sessions": 1, "stations": 2}}
    assert client.get("/api/stations").get_json() == []
    assert client.get("/api/sessions").get_json() == []
    assert client.get("/api/metrics").get_json()["series_by_net"] == []


def test_delete_all_records_supports_dry_run(client):
    client.post("/api/stations", json={"callsign": "W5XYZ", "name": "Example Op"}).get_json()

    res = client.delete("/api/records?dry_run=true")

    assert res.status_code == 200
    assert res.get_json() == {"dry_run": True, "would_delete": {"checkins": 0, "net_sessions": 0, "stations": 1}}
    assert [s["callsign"] for s in client.get("/api/stations").get_json()] == ["W5XYZ"]


def test_checking_in_station_moves_it_from_known_to_checked_in(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net"}).get_json()

    res = client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"], "traffic": True, "traffic_details": "One announcement"})
    assert res.status_code == 201
    checkin = res.get_json()
    assert checkin["station"]["callsign"] == "W5XYZ"
    assert checkin["traffic"] is True
    assert checkin["checked_in_at"]

    board = client.get(f"/api/sessions/{session['id']}/board").get_json()
    assert board["known_stations"] == []
    assert [c["station"]["callsign"] for c in board["checkins"]] == ["W5XYZ"]


def test_duplicate_checkin_is_idempotent(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net"}).get_json()

    first = client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]})
    second = client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]})

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["id"] == second.get_json()["id"]


def test_checkin_traffic_and_notes_can_be_updated(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net"}).get_json()
    checkin = client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]}).get_json()

    res = client.patch(f"/api/checkins/{checkin['id']}", json={"traffic": True, "traffic_details": "Needs relay", "notes": "Weak signal"})
    assert res.status_code == 200
    updated = res.get_json()
    assert updated["traffic"] is True
    assert updated["traffic_details"] == "Needs relay"
    assert updated["notes"] == "Weak signal"


def test_checkin_can_be_removed_to_correct_a_mistake(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net"}).get_json()
    checkin = client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]}).get_json()

    res = client.delete(f"/api/checkins/{checkin['id']}")
    assert res.status_code == 204

    board = client.get(f"/api/sessions/{session['id']}/board").get_json()
    assert [s["callsign"] for s in board["known_stations"]] == ["W5XYZ"]
    assert board["checkins"] == []


def test_stop_net_marks_session_closed_without_losing_checkins(client):
    station = client.post("/api/stations", json={"callsign": "W5XYZ"}).get_json()
    session = client.post("/api/sessions/start", json={"name": "Tuesday Net"}).get_json()
    client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"]})

    res = client.post(f"/api/sessions/{session['id']}/stop")
    assert res.status_code == 200
    stopped = res.get_json()
    assert stopped["status"] == "closed"
    assert stopped["closed_at"]

    board = client.get(f"/api/sessions/{session['id']}/board").get_json()
    assert board["session"]["status"] == "closed"
    assert [c["station"]["callsign"] for c in board["checkins"]] == ["W5XYZ"]


def test_lookup_without_fcc_data_returns_not_found_not_error(monkeypatch, client):
    monkeypatch.setenv("NET_LOGGER_FCC_LOOKUP_PATH", "/path/that/does/not/exist")
    res = client.get("/api/lookup?callsign=W5XYZ")
    assert res.status_code == 200
    assert res.get_json() == {"ok": True, "found": False, "callsign": "W5XYZ"}


def test_fcc_status_reports_local_database_age(monkeypatch, tmp_path):
    import os
    import time

    fcc = tmp_path / "fcc"
    data = fcc / "data"
    data.mkdir(parents=True)
    en_path = data / "EN.dat"
    idx_path = data / "EN.idx"
    zip_path = data / "zipcodes.csv"
    en_path.write_text("EN|123|x|x|K5SUB|x|x|SUB CLUB|DANNY|x|BUTLER|x|x|x|x|x|MEMPHIS|TN|38101|\n")
    idx_path.write_text("K5SUB|0\n")
    zip_path.write_text("zip,lat,lon\n38101,35.1495,-90.049\n")
    three_days_old = time.time() - (3 * 24 * 60 * 60)
    os.utime(en_path, (three_days_old, three_days_old))
    monkeypatch.setenv("NET_LOGGER_FCC_LOOKUP_PATH", str(fcc))

    db_fd, db_path = tempfile.mkstemp(prefix="net_logger_test_", suffix=".sqlite3")
    os.close(db_fd)
    try:
        app = create_app({"DATABASE": db_path, "TESTING": True})
        with app.test_client() as client:
            res = client.get("/api/fcc/status")
            assert res.status_code == 200
            status = res.get_json()
            assert status["available"] is True
            assert status["age_days"] >= 2
            assert status["files"]["EN.dat"] is True
            assert status["files"]["EN.idx"] is True
            assert status["data_path"] == str(fcc)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_fcc_update_downloads_data_and_rebuilds_index(monkeypatch, tmp_path):
    import io
    import zipfile

    from net_logger import fcc_lookup

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as archive:
        archive.writestr("EN.dat", "EN|123|x|x|K5SUB|x|x|SUB CLUB|DANNY|x|BUTLER|x|x|x|x|x|MEMPHIS|TN|38101|\n")
        archive.writestr("HD.dat", "HD|123|x|x|K5SUB|A|HA\n")
    zip_bytes.seek(0)

    fcc = tmp_path / "fcc"
    data = fcc / "data"
    data.mkdir(parents=True)
    (data / "zipcodes.csv").write_text("zip,lat,lon\n38101,35.1495,-90.049\n")
    (fcc / "maidenhead.py").write_text("def latlon_to_grid(lat, lon, precision=6):\n    return 'EM55aa'\n")
    monkeypatch.setenv("NET_LOGGER_FCC_LOOKUP_PATH", str(fcc))
    monkeypatch.setattr(fcc_lookup, "download_fcc_zip", lambda url=fcc_lookup.FCC_DOWNLOAD_URL: zip_bytes.getvalue())

    db_fd, db_path = tempfile.mkstemp(prefix="net_logger_test_", suffix=".sqlite3")
    os.close(db_fd)
    try:
        app = create_app({"DATABASE": db_path, "TESTING": True})
        with app.test_client() as client:
            res = client.post("/api/fcc/update")
            assert res.status_code == 200
            result = res.get_json()
            assert result["ok"] is True
            assert result["indexed_count"] == 1
            assert result["active_filter"] is True
            assert result["status"]["available"] is True
            assert (data / "EN.dat").exists()
            assert (data / "HD.dat").exists()
            assert (data / "EN.idx").read_text() == "K5SUB|0\n"
            assert client.get("/api/lookup?callsign=K5SUB").get_json()["found"] is True
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_lookup_uses_configured_fcc_flat_file_data(monkeypatch, tmp_path):
    fcc = tmp_path / "fcc"
    data = fcc / "data"
    data.mkdir(parents=True)
    (data / "EN.dat").write_bytes(b"EN|123|x|x|K5SUB|x|x|SUB CLUB|DANNY|x|BUTLER|x|x|x|x|x|MEMPHIS|TN|38101|\n")
    (data / "EN.idx").write_bytes(b"K5SUB|0\n")
    (data / "zipcodes.csv").write_text("zip,lat,lon\n38101,35.1495,-90.049\n")
    (fcc / "maidenhead.py").write_text("def latlon_to_grid(lat, lon, precision=6):\n    return 'EM55aa'\n")
    monkeypatch.setenv("NET_LOGGER_FCC_LOOKUP_PATH", str(fcc))

    db_fd, db_path = tempfile.mkstemp(prefix="net_logger_test_", suffix=".sqlite3")
    os.close(db_fd)
    try:
        app = create_app({"DATABASE": db_path, "TESTING": True})
        with app.test_client() as client:
            res = client.get("/api/lookup?callsign=k5sub")
            assert res.status_code == 200
            data = res.get_json()
            assert data["ok"] is True
            assert data["found"] is True
            assert data["result"]["callsign"] == "K5SUB"
            assert data["result"]["name"] == "DANNY BUTLER"
            assert data["result"]["city"] == "MEMPHIS"
            assert data["result"]["state"] == "TN"
            assert data["result"]["grid"] == "EM55aa"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)



def _make_session_with_checkin(client, session_name="Tuesday Net", station_call="W5XYZ"):
    station = client.post("/api/stations", json={"callsign": station_call, "name": f"{station_call} Op"}).get_json()
    session = client.post("/api/sessions/start", json={"name": session_name, "frequency": "146.520"}).get_json()
    client.post(f"/api/sessions/{session['id']}/checkins", json={"station_id": station["id"], "traffic": True, "traffic_details": "Bulletin"})
    return session, station


def test_sessions_can_be_listed_with_checkin_counts(client):
    first, _ = _make_session_with_checkin(client, "Tuesday Net", "W5XYZ")
    second, _ = _make_session_with_checkin(client, "Thursday Net", "K5SUB")
    client.post(f"/api/sessions/{second['id']}/stop")

    res = client.get("/api/sessions")
    assert res.status_code == 200
    sessions = res.get_json()
    assert [s["name"] for s in sessions] == ["Thursday Net", "Tuesday Net"]
    assert sessions[0]["checkin_count"] == 1
    assert sessions[0]["traffic_count"] == 1
    assert sessions[0]["status"] == "closed"


def test_export_specific_session_as_csv(client):
    session, _ = _make_session_with_checkin(client, "Tuesday Net", "W5XYZ")

    res = client.get(f"/api/export.csv?session_id={session['id']}")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    csv_text = res.get_data(as_text=True)
    assert "session_id,session_name" in csv_text
    assert "Tuesday Net" in csv_text
    assert "W5XYZ" in csv_text
    assert "Bulletin" in csv_text


def test_export_all_sessions_as_csv(client):
    _make_session_with_checkin(client, "Tuesday Net", "W5XYZ")
    _make_session_with_checkin(client, "Thursday Net", "K5SUB")

    res = client.get("/api/export.csv")
    assert res.status_code == 200
    csv_text = res.get_data(as_text=True)
    assert "Tuesday Net" in csv_text
    assert "Thursday Net" in csv_text


def test_metrics_group_checkins_by_net_and_date(client):
    _make_session_with_checkin(client, "Tuesday Net", "W5XYZ")
    _make_session_with_checkin(client, "Thursday Net", "K5SUB")

    res = client.get("/api/metrics")
    assert res.status_code == 200
    metrics = res.get_json()
    assert {row["net_name"]: row["checkin_count"] for row in metrics["by_net"]} == {"Tuesday Net": 1, "Thursday Net": 1}
    assert sum(row["checkin_count"] for row in metrics["by_date"]) == 2


def _set_session_and_checkin_time(client, session_id, checked_in_at):
    import sqlite3

    with sqlite3.connect(client.application.config["DATABASE"]) as con:
        con.execute("UPDATE net_sessions SET started_at = ? WHERE id = ?", (checked_in_at, session_id))
        con.execute("UPDATE checkins SET checked_in_at = ? WHERE session_id = ?", (checked_in_at, session_id))


def test_metrics_series_groups_checkins_by_net_and_month(client):
    weekly_1, _ = _make_session_with_checkin(client, "Weekly Net", "W5AAA")
    weekly_2, _ = _make_session_with_checkin(client, "Weekly Net", "W5AAB")
    skywarn, _ = _make_session_with_checkin(client, "Skywarn Net", "W5AAC")
    _set_session_and_checkin_time(client, weekly_1["id"], "2026-01-15 19:00:00")
    _set_session_and_checkin_time(client, weekly_2["id"], "2026-02-16 19:00:00")
    _set_session_and_checkin_time(client, skywarn["id"], "2026-02-20 21:00:00")

    res = client.get("/api/metrics?period=month")

    assert res.status_code == 200
    metrics = res.get_json()
    assert metrics["period"] == "month"
    assert metrics["series_by_net"] == [
        {
            "net_name": "Skywarn Net",
            "points": [{"bucket": "2026-02", "checkin_count": 1}],
        },
        {
            "net_name": "Weekly Net",
            "points": [
                {"bucket": "2026-01", "checkin_count": 1},
                {"bucket": "2026-02", "checkin_count": 1},
            ],
        },
    ]


def test_metrics_series_groups_checkins_by_week(client):
    first, _ = _make_session_with_checkin(client, "Weekly Net", "W5AAA")
    second, _ = _make_session_with_checkin(client, "Weekly Net", "W5AAB")
    _set_session_and_checkin_time(client, first["id"], "2026-01-05 19:00:00")
    _set_session_and_checkin_time(client, second["id"], "2026-01-12 19:00:00")

    res = client.get("/api/metrics?period=week")

    assert res.status_code == 200
    assert res.get_json()["series_by_net"] == [
        {
            "net_name": "Weekly Net",
            "points": [
                {"bucket": "2026-W01", "checkin_count": 1},
                {"bucket": "2026-W02", "checkin_count": 1},
            ],
        }
    ]


def test_metrics_defaults_invalid_period_to_month(client):
    res = client.get("/api/metrics?period=bad")

    assert res.status_code == 200
    assert res.get_json()["period"] == "month"
