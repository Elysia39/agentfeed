#!/usr/bin/env bash
# ==============================================================================
# AgentFeed Desktop Launcher (macOS / Linux)
# ==============================================================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 desktop.py || python desktop.py
