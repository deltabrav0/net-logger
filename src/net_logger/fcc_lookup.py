"""FCC lookup adapter for local/off-grid flat-file FCC data.

Set NET_LOGGER_FCC_LOOKUP_PATH to the directory containing Danny's copied
`fcc_database_web_app` files. By default, the adapter checks the known sample
location under Downloads. If FCC data files are absent, lookup safely returns
`found: false` so QRZ or internet access is not required for the app to run.
"""

from __future__ import annotations

import csv
import importlib.util
import os
from pathlib import Path

from .db import normalize_callsign

DEFAULT_FCC_PATH = Path("/Users/dbutler/Downloads/Offgrid Tools/fcc_database_web_app")

COL_CALLSIGN = 4
COL_ENTITY_NAME = 7
COL_FIRST_NAME = 8
COL_LAST_NAME = 10
COL_CITY = 16
COL_STATE = 17
COL_ZIP = 18


def _base_path() -> Path:
    return Path(os.environ.get("NET_LOGGER_FCC_LOOKUP_PATH") or DEFAULT_FCC_PATH)


def _load_zip_table(zip_path: Path) -> dict[str, tuple[float, float]]:
    table: dict[str, tuple[float, float]] = {}
    if not zip_path.exists():
        return table
    with zip_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            zip5 = (row.get("zip") or "").strip()[:5]
            if not zip5:
                continue
            try:
                table[zip5] = (float(row["lat"]), float(row["lon"]))
            except (KeyError, ValueError):
                continue
    return table


def _latlon_to_grid(base: Path, lat: float, lon: float) -> str | None:
    maidenhead_path = base / "maidenhead.py"
    if not maidenhead_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("net_logger_external_maidenhead", maidenhead_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.latlon_to_grid(lat, lon, precision=6)


def _find_offset(callsign: str, index_path: Path) -> int | None:
    target = callsign.encode("ascii", "ignore")
    if not target or not index_path.exists():
        return None
    # Index files are small enough for this MVP, and this linear parser also
    # handles tests' tiny synthetic indexes. The original app uses binary search.
    with index_path.open("rb") as fh:
        for raw in fh:
            key, sep, offset = raw.partition(b"|")
            if sep and key == target:
                try:
                    return int(offset.strip())
                except ValueError:
                    return None
    return None


def _parse_record(raw: bytes, base: Path, zip_table: dict[str, tuple[float, float]]) -> dict:
    fields = raw.decode("latin-1").rstrip("\n").rstrip("\r").split("|")

    def get(i: int) -> str:
        return fields[i].strip() if i < len(fields) else ""

    first = get(COL_FIRST_NAME)
    last = get(COL_LAST_NAME)
    entity = get(COL_ENTITY_NAME)
    name = " ".join(p for p in (first, last) if p).strip() or entity
    zip5 = get(COL_ZIP)[:5]
    lat = lon = None
    grid = None
    if zip5 in zip_table:
        lat, lon = zip_table[zip5]
        grid = _latlon_to_grid(base, lat, lon)
    return {
        "callsign": get(COL_CALLSIGN),
        "name": name,
        "city": get(COL_CITY),
        "state": get(COL_STATE),
        "zip": zip5,
        "grid": grid,
        "lat": lat,
        "lon": lon,
    }


def lookup_callsign(callsign: str) -> dict:
    call = normalize_callsign(callsign)
    base = _base_path()
    data = base / "data"
    en_path = data / "EN.dat"
    index_path = data / "EN.idx"
    if not call or not en_path.exists() or not index_path.exists():
        return {"ok": True, "found": False, "callsign": call}

    offset = _find_offset(call, index_path)
    if offset is None:
        return {"ok": True, "found": False, "callsign": call}

    with en_path.open("rb") as fh:
        fh.seek(offset)
        raw = fh.readline()
    if not raw:
        return {"ok": True, "found": False, "callsign": call}

    zip_table = _load_zip_table(data / "zipcodes.csv")
    return {"ok": True, "found": True, "result": _parse_record(raw, base, zip_table)}
