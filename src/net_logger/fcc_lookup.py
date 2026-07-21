"""FCC lookup adapter for local/off-grid flat-file FCC data.

Set NET_LOGGER_FCC_LOOKUP_PATH to override the directory containing local FCC
lookup files. By default, the adapter uses Net Logger's writable per-user data
directory. If FCC data files are absent, lookup safely returns `found: false` so
QRZ or internet access is not required for the app to run.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import os
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .db import normalize_callsign

DEFAULT_FCC_DIR_NAME = "fcc_lookup"
FCC_DOWNLOAD_URL = "https://data.fcc.gov/download/pub/uls/complete/l_amat.zip"

REQUIRED_FILES = ("EN.dat", "EN.idx", "zipcodes.csv")

COL_CALLSIGN = 4
COL_ENTITY_NAME = 7
COL_FIRST_NAME = 8
COL_LAST_NAME = 10
COL_CITY = 16
COL_STATE = 17
COL_ZIP = 18


def _base_path() -> Path:
    override = os.environ.get("NET_LOGGER_FCC_LOOKUP_PATH")
    if override:
        return Path(override).expanduser()
    return config.default_data_dir() / DEFAULT_FCC_DIR_NAME


def _data_path(base: Path | None = None) -> Path:
    return (base or _base_path()) / "data"


def _iso_from_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def fcc_database_status() -> dict:
    """Return local FCC flat-file availability and age details."""
    base = _base_path()
    data = _data_path(base)
    files = {name: (data / name).exists() for name in REQUIRED_FILES}
    en_path = data / "EN.dat"
    updated_at = _iso_from_mtime(en_path)
    age_days = None
    if en_path.exists():
        age_days = int((time.time() - en_path.stat().st_mtime) // 86400)
        if age_days < 0:
            age_days = 0
    return {
        "data_path": str(base),
        "available": files["EN.dat"] and files["EN.idx"],
        "updated_at": updated_at,
        "age_days": age_days,
        "files": files,
    }


def _active_unique_ids(hd_path: Path) -> set[str] | None:
    if not hd_path.exists():
        return None
    active: set[str] = set()
    with hd_path.open("rb") as fh:
        for raw in fh:
            fields = raw.decode("latin-1").rstrip("\n").rstrip("\r").split("|")
            if len(fields) > 5 and fields[0] == "HD" and fields[5].strip().upper() == "A":
                active.add(fields[1].strip())
    return active


def build_fcc_index(base: Path | None = None) -> dict:
    """Build data/EN.idx from EN.dat, filtering to active HD.dat rows when present."""
    root = base or _base_path()
    data = _data_path(root)
    en_path = data / "EN.dat"
    hd_path = data / "HD.dat"
    index_path = data / "EN.idx"
    if not en_path.exists():
        raise FileNotFoundError(f"FCC entity file not found: {en_path}")

    active_ids = _active_unique_ids(hd_path)
    rows: list[tuple[str, int]] = []
    with en_path.open("rb") as fh:
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            fields = raw.decode("latin-1").rstrip("\n").rstrip("\r").split("|")
            if len(fields) <= COL_CALLSIGN or fields[0] != "EN":
                continue
            unique_id = fields[1].strip() if len(fields) > 1 else ""
            if active_ids is not None and unique_id not in active_ids:
                continue
            callsign = normalize_callsign(fields[COL_CALLSIGN])
            if callsign:
                rows.append((callsign, offset))

    rows.sort(key=lambda item: item[0])
    data.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="ascii", newline="") as fh:
        for callsign, offset in rows:
            fh.write(f"{callsign}|{offset}\n")
    return {"indexed_count": len(rows), "active_filter": active_ids is not None, "index_path": str(index_path)}


def download_fcc_zip(url: str = FCC_DOWNLOAD_URL) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def update_fcc_database() -> dict:
    """Download FCC amateur data, extract EN/HD files, rebuild index, and report status."""
    base = _base_path()
    data = _data_path(base)
    data.mkdir(parents=True, exist_ok=True)
    payload = download_fcc_zip()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for name in ("EN.dat", "HD.dat"):
            try:
                source = archive.open(name)
            except KeyError:
                source = archive.open(f"l_amat/{name}")
            with source, (data / name).open("wb") as out:
                out.write(source.read())
    build = build_fcc_index(base)
    return {"ok": True, **build, "status": fcc_database_status()}


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
