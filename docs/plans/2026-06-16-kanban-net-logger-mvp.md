# Kanban Net Logger MVP Implementation Plan

> **For Hermes:** Implement directly using strict TDD for backend behavior and lightweight browser verification for the static UI.

**Goal:** Build an initial standalone amateur-radio net logger with a two-column known-stations/check-ins board, local persistence, and a path to embed the existing off-grid FCC lookup engine.

**Architecture:** Flask serves a JSON API plus a static browser UI. SQLite stores stations, net sessions, and check-ins. The active-net UI presents known stations on the left and checked-in stations on the right; clicking or dragging a station checks it into the active session. Unknown callsigns can be searched/added manually, with FCC lookup support stubbed through an adapter boundary.

**Tech Stack:** Python 3, Flask, SQLite, pytest, vanilla HTML/CSS/JavaScript.

---

## MVP Tasks

### Task 1: Create project scaffold and backend tests

**Objective:** Establish a testable Flask/SQLite project structure.

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `src/net_logger/__init__.py`
- Create: `src/net_logger/app.py`
- Create: `src/net_logger/db.py`
- Create: `tests/test_api.py`

**Verification:** Run `python3 -m pytest -q`; expected initial RED failure until implementation exists, then passing tests.

### Task 2: Implement stations/session/check-ins API

**Objective:** Support the minimum data operations needed by the two-column board.

**API:**
- `GET /api/stations`
- `POST /api/stations`
- `POST /api/sessions/start`
- `GET /api/sessions/<id>/board`
- `POST /api/sessions/<id>/checkins`
- `PATCH /api/checkins/<id>`

**Verification:** API tests pass and confirm duplicate check-ins are idempotent.

### Task 3: Build two-column Kanban UI

**Objective:** Provide a usable active-net board.

**Files:**
- Create: `src/net_logger/static/index.html`
- Create: `src/net_logger/static/styles.css`
- Create: `src/net_logger/static/app.js`

**Behavior:**
- Search known stations.
- Click/drag known station cards into checked-in column.
- Add unknown callsign manually.
- Edit traffic/notes on checked-in cards.

**Verification:** Start Flask app and load `/`; API-backed board renders without console-blocking server errors.

### Task 4: Add FCC lookup adapter boundary

**Objective:** Prepare for importing the existing flat-file FCC lookup implementation without making QRZ required.

**Files:**
- Create: `src/net_logger/fcc_lookup.py`
- Add endpoint: `GET /api/lookup?callsign=...`

**Verification:** Endpoint returns `found:false` when no FCC data path is configured, and can later wrap `/Users/dbutler/Downloads/Offgrid Tools/fcc_database_web_app/lookup.py` logic.

### Task 5: Documentation

**Objective:** Record how to run, test, and continue the build.

**Files:**
- Create: `README.md`
- Create/update plan file.

**Verification:** Commands in README work locally.
