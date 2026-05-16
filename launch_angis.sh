#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$DIR:$PYTHONPATH"
exec python3 -m angis "$@"
