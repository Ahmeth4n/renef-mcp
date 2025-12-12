#!/bin/bash
cd "$(dirname "$0")"
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/readline/lib:$DYLD_LIBRARY_PATH"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

.venv/bin/python -m src.main
