"""SQLite persistence for the net logger MVP."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  callsign TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL DEFAULT '',
  city TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT '',
  grid TEXT NOT NULL DEFAULT '',
  lat REAL,
  lon REAL,
  notes TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT 'manual',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_heard_at TEXT
);

CREATE TABLE IF NOT EXISTS net_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL DEFAULT '',
  frequency TEXT NOT NULL DEFAULT '',
  net_control TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  closed_at TEXT
);

CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES net_sessions(id) ON DELETE CASCADE,
  station_id INTEGER NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
  sequence INTEGER NOT NULL,
  checked_in_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  traffic INTEGER NOT NULL DEFAULT 0,
  traffic_details TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  UNIQUE(session_id, station_id)
);

CREATE TABLE IF NOT EXISTS wordpress_pushes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES net_sessions(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL,
  wordpress_event_id TEXT,
  response_json TEXT NOT NULL DEFAULT '',
  pushed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, endpoint)
);
"""


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(path: str) -> None:
    with connect(path) as con:
        con.executescript(SCHEMA)


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def normalize_callsign(value: str) -> str:
    return ''.join((value or '').upper().split())
