#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$DIR:$PYTHONPATH"
if command -v python3.14 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.14)"
else
  PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 14):
    raise SystemExit("Angis requires Python 3.14+; install the python.org macOS universal2 Python 3.14 installer.")
PY

exec "$PYTHON_BIN" -m angis "$@"
