#!/bin/sh

set -eu

REPO_DIR="/Users/hetong.31/code/auto-hf-papers"
PYTHON_BIN="/usr/bin/python3"
NODE_BIN="/opt/homebrew/bin/node"
TZ_NAME="Asia/Shanghai"
RUN_DATE="$(TZ="$TZ_NAME" date +%F)"

cd "$REPO_DIR"

"$PYTHON_BIN" -m app.run --date "$RUN_DATE"
"$NODE_BIN" scripts/deliver.js "--file=outputs/$RUN_DATE.md"
