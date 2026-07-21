"""Command-line entry point for Net Logger."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import create_app
from .config import default_config_path, default_data_dir, default_database_path, ensure_config_file, load_app_settings

APP_NAME = "net-logger"


def build_parser() -> argparse.ArgumentParser:
    settings = load_app_settings()
    parser = argparse.ArgumentParser(prog="net-logger", description="Run the amateur-radio Net Logger web app.")
    parser.add_argument("--config", default=settings["CONFIG_PATH"], help="Path to the Net Logger configuration file")
    subcommands = parser.add_subparsers(dest="command")

    serve = subcommands.add_parser("serve", help="Start the Net Logger web server")
    serve.add_argument("--host", default=settings["HOST"], help="Bind host/interface")
    serve.add_argument("--port", type=int, default=settings["PORT"], help="Bind port")
    serve.add_argument("--database", default=str(default_database_path()), help="SQLite database path")
    serve.add_argument("--debug", action="store_true", default=settings["DEBUG"], help="Enable Flask debug mode")

    launch = subcommands.add_parser("launch", help="Start Net Logger and open the browser")
    launch.add_argument("--host", default=settings["HOST"], help="Bind host/interface")
    launch.add_argument("--port", type=int, default=settings["PORT"], help="Bind port")
    launch.add_argument("--database", default=str(default_database_path()), help="SQLite database path")
    return parser


def main(argv: list[str] | None = None) -> int:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config")
    pre_args, _ = pre_parser.parse_known_args(argv)
    if pre_args.config:
        import os
        os.environ["NET_LOGGER_CONFIG"] = pre_args.config

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {None, "serve"}:
        database = Path(args.database).expanduser()
        database.parent.mkdir(parents=True, exist_ok=True)
        app = create_app({"DATABASE": str(database)})
        print(f"Net Logger database: {database}", file=sys.stderr)
        app.run(host=args.host, port=args.port, debug=args.debug)
        return 0
    if args.command == "launch":
        from .windows_launcher import main as launch_main

        return launch_main(host=args.host, port=args.port, database=args.database)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
