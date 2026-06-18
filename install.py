#!/usr/bin/env python3
"""Cross-platform installer for Net Logger.

This script intentionally uses only the Python standard library so it can run on
Windows, macOS, and Linux before Net Logger's package dependencies are present.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO_URL = "https://github.com/deltabrav0/net-logger.git"
MIN_PYTHON = (3, 11)


def build_install_command(*, source: str, method: str, repo_url: str, upgrade: bool = False) -> list[str]:
    """Return the install command for the requested source and method."""
    target = "." if source == "local" else f"git+{repo_url}"

    if method == "pipx":
        command = ["pipx", "install"]
        if upgrade:
            command.append("--force")
        command.append(target)
        return command

    if method == "pip":
        command = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            command.append("--upgrade")
        command.append(target)
        return command

    if method == "uv":
        command = ["uv", "tool", "install"]
        if upgrade:
            command.append("--force")
        command.append(target)
        return command

    raise ValueError(f"unsupported install method: {method}")


def _format_command(command: list[str]) -> str:
    return " ".join(command)


def _ensure_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        wanted = ".".join(str(part) for part in MIN_PYTHON)
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise SystemExit(f"Net Logger requires Python {wanted}+; current Python is {current}.")


def _ensure_method_available(method: str, *, dry_run: bool) -> None:
    if method == "pip":
        return
    if shutil.which(method):
        return
    if dry_run:
        print(f"Would require command on PATH: {method}")
        return
    if method == "pipx":
        print("pipx was not found; installing pipx with the current Python...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pipx"])
        subprocess.check_call([sys.executable, "-m", "pipx", "ensurepath"])
        return
    raise SystemExit(f"Required command not found on PATH: {method}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Net Logger on Windows, macOS, or Linux.")
    parser.add_argument("--source", choices=["github", "local"], default="github", help="Install from GitHub or the current checkout.")
    parser.add_argument("--method", choices=["pipx", "pip", "uv"], default="pipx", help="Installer backend to use.")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="Git repository URL used when --source=github.")
    parser.add_argument("--upgrade", action="store_true", help="Force/reinstall or upgrade an existing installation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _ensure_python_version()

    if args.source == "local" and not (Path.cwd() / "pyproject.toml").exists():
        raise SystemExit("--source local must be run from the Net Logger checkout directory.")

    _ensure_method_available(args.method, dry_run=args.dry_run)
    command = build_install_command(source=args.source, method=args.method, repo_url=args.repo_url, upgrade=args.upgrade)

    print("Net Logger installer")
    print(f"Install command: {_format_command(command)}")
    if args.dry_run:
        print("Dry run only; no changes made.")
    else:
        subprocess.check_call(command)

    print("\nRun Net Logger with:")
    print("  net-logger serve")
    print("Then open:")
    print("  http://127.0.0.1:8088")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
