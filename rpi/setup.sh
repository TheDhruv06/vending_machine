#!/usr/bin/env bash
# =====================================================================================
# SOILVEDA ORGANICS - RASPBERRY PI 5 TOUCHSCREEN KIOSK AUTO-SETUP SCRIPT
# =====================================================================================
set -e

echo "========================================================"
echo " SoilVeda Organics - Raspberry Pi 5 Setup               "
echo "========================================================"

# 1. Update OS package lists
echo "[1/5] Updating Raspberry Pi OS packages..."
sudo apt-get update -y

# 2. Install Python venv, Chromium, unclutter (hides mouse cursor on touchscreen)
echo "[2/5] Installing dependencies (python3-venv, chromium, unclutter, curl)..."
sudo apt-get install -y python3-venv python3-pip git chromium-browser unclutter curl

# 3. Create Virtual Environment
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[3/5] Setting up Python virtual environment in: $REPO_DIR/venv"
cd "$REPO_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv & install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Make scripts executable
echo "[4/5] Setting execution permissions on kiosk scripts..."
chmod +x "$REPO_DIR/rpi/start_kiosk.sh"
chmod +x "$REPO_DIR/rpi/setup.sh"

# 5. Setup Autostart for Kiosk Mode on Boot
echo "[5/5] Configuring Auto-start on boot..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Generate desktop shortcut in autostart directory
cat <<EOF > "$AUTOSTART_DIR/soilveda_kiosk.desktop"
[Desktop Entry]
Type=Application
Name=SoilVeda Vending Kiosk
Comment=Start SoilVeda Herbal Tea Touchscreen Kiosk
Exec=$REPO_DIR/rpi/start_kiosk.sh
Terminal=false
StartupNotify=false
EOF

chmod +x "$AUTOSTART_DIR/soilveda_kiosk.desktop"

echo "========================================================"
echo " SETUP COMPLETE!                                        "
echo "========================================================"
echo "You can now test running the kiosk by typing:"
echo "  $REPO_DIR/rpi/start_kiosk.sh"
echo ""
echo "Or simply reboot your Raspberry Pi 5:"
echo "  sudo reboot"
echo "========================================================"
