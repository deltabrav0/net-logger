#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_VERSION_CHECK="import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"

run_installer() {
  python_cmd=$1
  shift
  if "$python_cmd" -c "$PYTHON_VERSION_CHECK" >/dev/null 2>&1; then
    exec "$python_cmd" "$SCRIPT_DIR/install.py" "$@"
  fi

  found_version=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null || printf 'unknown')
  echo "Found Python $found_version at $(command -v "$python_cmd" 2>/dev/null || printf '%s' "$python_cmd"), but it is too old; Python 3.11 or newer is required to install Net Logger." >&2
  exit 1
}

if command -v python3 >/dev/null 2>&1; then
  run_installer python3 "$@"
elif command -v python >/dev/null 2>&1; then
  run_installer python "$@"
else
  echo "Python 3.11 or newer is required to install Net Logger." >&2
  exit 1
fi
