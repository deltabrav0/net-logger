import sys
from pathlib import Path

from net_logger import cli


def test_default_data_dir_is_cross_platform(monkeypatch):
    monkeypatch.delenv("NET_LOGGER_DATA_DIR", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    assert cli.default_data_dir() == Path.home() / ".local" / "share" / "net-logger"

    monkeypatch.setattr(sys, "platform", "darwin")
    assert cli.default_data_dir() == Path.home() / "Library" / "Application Support" / "Net Logger"

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\\Users\\Danny\\AppData\\Roaming")
    assert cli.default_data_dir() == Path(r"C:\\Users\\Danny\\AppData\\Roaming") / "Net Logger"


def test_database_environment_override(monkeypatch, tmp_path):
    db_path = tmp_path / "custom.sqlite3"
    monkeypatch.setenv("NET_LOGGER_DATABASE", str(db_path))

    assert cli.default_database_path() == db_path


def test_cli_parser_defaults_to_serve_options(tmp_path):
    parser = cli.build_parser()
    args = parser.parse_args(["serve", "--host", "0.0.0.0", "--port", "9000", "--database", str(tmp_path / "net.sqlite3")])

    assert args.command == "serve"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.database.endswith("net.sqlite3")
