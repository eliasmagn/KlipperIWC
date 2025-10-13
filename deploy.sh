#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/app.pid"

mkdir -p "$LOG_DIR"

if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
echo "Installing Python dependencies..."
python -m pip install --upgrade pip wheel
python -m pip install -r "$PROJECT_ROOT/requirements.txt"

deactivate

source "$VENV_PATH/bin/activate"
export APP_ENV=production
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="info"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Stopping existing KlipperIWC process..."
  kill "$(cat "$PID_FILE")"
  rm -f "$PID_FILE"
  sleep 2
fi

echo "Starting KlipperIWC in production mode..."
nohup "$VENV_PATH/bin/uvicorn" klipperiwc.app:create_app --factory --host "$HOST" --port "$PORT" --log-level "$LOG_LEVEL" >>"$LOG_DIR/app.log" 2>&1 &
echo $! > "$PID_FILE"

echo "Application started with PID $(cat "$PID_FILE"). Logs: $LOG_DIR/app.log"
