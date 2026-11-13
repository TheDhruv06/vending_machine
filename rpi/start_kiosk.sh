#!/usr/bin/env bash
# =====================================================================================
# SOILVEDA ORGANICS - RASPBERRY PI 5 TOUCHSCREEN KIOSK LAUNCHER
# =====================================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$REPO_DIR/venv/bin/python3"
APP_FILE="$REPO_DIR/app.py"

echo "[SoilVeda] Starting Vending Machine UI on Raspberry Pi 5..."

# 1. Prevent screen from sleeping / turning off
if command -v xset >/dev/null 2>&1; then
    xset s off 2>/dev/null || true
    xset -dpms 2>/dev/null || true
    xset s noblank 2>/dev/null || true
fi

# 2. Hide mouse cursor when idle on the touchscreen
if command -v unclutter >/dev/null 2>&1; then
    pkill unclutter 2>/dev/null || true
    unclutter -idle 0.5 -root &
fi

# 3. Check if Flask server is already running, if not start it
if ! curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000 | grep -q "200"; then
    echo "[SoilVeda] Launching Flask backend server..."
    cd "$REPO_DIR"
    if [ -f "$VENV_PYTHON" ]; then
        "$VENV_PYTHON" "$APP_FILE" > "$REPO_DIR/flask_app.log" 2>&1 &
    else
        python3 "$APP_FILE" > "$REPO_DIR/flask_app.log" 2>&1 &
    fi
    FLASK_PID=$!
    echo "[SoilVeda] Flask PID: $FLASK_PID"
fi

# 4. Wait for Flask server to be ready (up to 30 seconds)
echo "[SoilVeda] Waiting for web application on http://127.0.0.1:5000..."
MAX_TRIES=30
COUNT=0
while [ $COUNT -lt $MAX_TRIES ]; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000 || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "[SoilVeda] Web application is ONLINE!"
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

# 5. Launch Chromium in Fullscreen Kiosk Mode for the 7-inch Touchscreen
echo "[SoilVeda] Launching Chromium in Kiosk Mode..."
CHROMIUM_CMD="chromium-browser"
if ! command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_CMD="chromium"
fi

# Clear any crash bubble from previous unclean power-offs
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences 2>/dev/null || true
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences 2>/dev/null || true

exec $CHROMIUM_CMD \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --check-for-update-interval=31536000 \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-translate \
    --disable-session-crashed-bubble \
    --autoplay-policy=no-user-gesture-required \
    --window-size=1024,600 \
    --window-position=0,0 \
    http://localhost:5000
