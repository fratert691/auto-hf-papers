#!/bin/sh

set -eu

# Derive repo root from this script's location (works regardless of cwd)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
TZ_NAME="Asia/Shanghai"
RUN_DATE="$(TZ="$TZ_NAME" date +%F)"

cd "$REPO_DIR"

# Python: prefer venv, fall back to system python3
VENV_PYTHON="$REPO_DIR/.venv/bin/python3"
if [ -x "$VENV_PYTHON" ]; then
    PYTHON_BIN="$VENV_PYTHON"
else
    PYTHON_BIN="$(command -v python3)"
fi

# Node: prefer Homebrew location, fall back to PATH
BREW_NODE="/opt/homebrew/bin/node"
if [ -x "$BREW_NODE" ]; then
    NODE_BIN="$BREW_NODE"
else
    NODE_BIN="$(command -v node)"
fi

"$PYTHON_BIN" -m app.run --date "$RUN_DATE"
"$NODE_BIN" scripts/deliver.js "--file=outputs/$RUN_DATE.md"
