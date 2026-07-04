"""Configuration-file support for Net Logger."""

from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path
from typing import Any

APP_NAME = "net-logger"

CONFIG_TEMPLATE = """# Net Logger configuration file
#
# A configuration file is a small text file Net Logger reads when it starts.
# Edit the values after the equals signs, save the file, then restart Net Logger.
# Leave a value blank when you do not want to use that option.

[server]
# Use 127.0.0.1 for this computer only, or 0.0.0.0 to allow other computers on your LAN.
host = 127.0.0.1
port = 8088
debug = false

[paths]
# Optional. Leave database blank to use the normal per-user database location.
database =
# Optional. Path to a custom square PNG logo image.
logo_path =
# Optional. Folder containing local FCC lookup files.
fcc_lookup_path =

[wordpress]
# WordPress Application Password settings for the Send to WordPress button.
# Example endpoint: https://example.org/wp-json/net-attendance/v1/net-logger/sessions
endpoint =
username =
application_password =
timeout = 20
"""


def default_data_dir() -> Path:
    """Return a writable per-user data directory on Windows, macOS, or Linux."""
    override = os.environ.get("NET_LOGGER_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "Net Logger"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Net Logger"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / APP_NAME


def default_config_path() -> Path:
    override = os.environ.get("NET_LOGGER_CONFIG")
    if override:
        return Path(override).expanduser()
    return default_data_dir() / "config.ini"


def ensure_config_file(path: Path | None = None) -> Path:
    config_path = (path or default_config_path()).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    return config_path


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _truthy(value: str | None) -> bool:
    return _clean(value).lower() in {"1", "true", "yes", "on"}


def _int_value(value: str | None, default: int) -> int:
    try:
        return int(_clean(value))
    except (TypeError, ValueError):
        return default


def load_config_file(path: Path | None = None) -> dict[str, Any]:
    config_path = (path or default_config_path()).expanduser()
    parser = configparser.ConfigParser()
    if config_path.exists():
        parser.read(config_path, encoding="utf-8")

    settings: dict[str, Any] = {}
    if parser.has_section("server"):
        host = _clean(parser.get("server", "host", fallback=""))
        if host:
            settings["HOST"] = host
        port = _clean(parser.get("server", "port", fallback=""))
        if port:
            settings["PORT"] = _int_value(port, 8088)
        debug = _clean(parser.get("server", "debug", fallback=""))
        if debug:
            settings["DEBUG"] = _truthy(debug)

    if parser.has_section("paths"):
        database = _clean(parser.get("paths", "database", fallback=""))
        if database:
            settings["DATABASE"] = str(Path(database).expanduser())
        logo_path = _clean(parser.get("paths", "logo_path", fallback=""))
        if logo_path:
            settings["LOGO_PATH"] = str(Path(logo_path).expanduser())
        fcc_lookup_path = _clean(parser.get("paths", "fcc_lookup_path", fallback=""))
        if fcc_lookup_path:
            settings["FCC_LOOKUP_PATH"] = str(Path(fcc_lookup_path).expanduser())

    if parser.has_section("wordpress"):
        endpoint = _clean(parser.get("wordpress", "endpoint", fallback=""))
        if endpoint:
            settings["WORDPRESS_ENDPOINT"] = endpoint
        username = _clean(parser.get("wordpress", "username", fallback=""))
        if username:
            settings["WORDPRESS_USERNAME"] = username
        password = _clean(parser.get("wordpress", "application_password", fallback=""))
        if password:
            settings["WORDPRESS_APPLICATION_PASSWORD"] = password
        timeout = _clean(parser.get("wordpress", "timeout", fallback=""))
        if timeout:
            settings["WORDPRESS_TIMEOUT"] = _int_value(timeout, 20)

    return settings


def write_wordpress_settings(
    endpoint: str,
    username: str,
    application_password: str,
    timeout: int = 20,
    path: Path | str | None = None,
) -> Path:
    """Write WordPress connection settings to the Net Logger config file."""
    config_path = Path(path).expanduser() if path else ensure_config_file()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()
    if config_path.exists():
        parser.read(config_path, encoding="utf-8")
    if not parser.has_section("server"):
        parser["server"] = {"host": "127.0.0.1", "port": "8088", "debug": "false"}
    if not parser.has_section("paths"):
        parser["paths"] = {"database": "", "logo_path": "", "fcc_lookup_path": ""}
    if not parser.has_section("wordpress"):
        parser.add_section("wordpress")

    parser.set("wordpress", "endpoint", _clean(endpoint))
    parser.set("wordpress", "username", _clean(username))
    parser.set("wordpress", "application_password", _clean(application_password))
    parser.set("wordpress", "timeout", str(timeout or 20))

    with config_path.open("w", encoding="utf-8") as f:
        parser.write(f)
    return config_path


def env_settings() -> dict[str, Any]:
    settings: dict[str, Any] = {}
    mapping = {
        "NET_LOGGER_HOST": ("HOST", str),
        "NET_LOGGER_PORT": ("PORT", int),
        "NET_LOGGER_DATABASE": ("DATABASE", str),
        "NET_LOGGER_LOGO_PATH": ("LOGO_PATH", str),
        "NET_LOGGER_FCC_LOOKUP_PATH": ("FCC_LOOKUP_PATH", str),
        "NET_LOGGER_WORDPRESS_ENDPOINT": ("WORDPRESS_ENDPOINT", str),
        "NET_LOGGER_WORDPRESS_USERNAME": ("WORDPRESS_USERNAME", str),
        "NET_LOGGER_WORDPRESS_APPLICATION_PASSWORD": ("WORDPRESS_APPLICATION_PASSWORD", str),
        "NET_LOGGER_WORDPRESS_TIMEOUT": ("WORDPRESS_TIMEOUT", int),
    }
    for env_name, (key, converter) in mapping.items():
        value = os.environ.get(env_name)
        if value is None or value == "":
            continue
        settings[key] = int(value) if converter is int else value
    debug = os.environ.get("NET_LOGGER_DEBUG")
    if debug:
        settings["DEBUG"] = _truthy(debug)
    return settings


def default_database_path() -> Path:
    settings = load_app_settings(create_missing=False)
    return Path(settings.get("DATABASE") or default_data_dir() / "net_logger.sqlite3").expanduser()


def load_app_settings(create_missing: bool = True) -> dict[str, Any]:
    config_path = ensure_config_file() if create_missing else default_config_path()
    settings = load_config_file(config_path)
    settings.update(env_settings())
    settings.setdefault("HOST", "127.0.0.1")
    settings.setdefault("PORT", 8088)
    settings.setdefault("DEBUG", False)
    settings.setdefault("DATABASE", str(default_data_dir() / "net_logger.sqlite3"))
    settings.setdefault("LOGO_PATH", "")
    settings.setdefault("WORDPRESS_ENDPOINT", "")
    settings.setdefault("WORDPRESS_USERNAME", "")
    settings.setdefault("WORDPRESS_APPLICATION_PASSWORD", "")
    settings.setdefault("WORDPRESS_TIMEOUT", 20)
    settings["CONFIG_PATH"] = str(config_path)
    return settings
