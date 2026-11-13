# Raspberry Pi 5 (4GB) + 7-Inch Touchscreen Deployment Guide

This guide explains how to migrate, configure, and run the **SoilVeda Organics AI Herbal Vending Machine** on a **Raspberry Pi 5** with a **7-inch Touchscreen Display** in **Kiosk Mode** (fullscreen, no browser bars, no mouse cursor, auto-starting on power-on).

---

## 🖥️ 1. Hardware Connections (7-Inch Touchscreen to Pi 5)

Depending on your 7-inch touchscreen model:

### Case A: Official Raspberry Pi 7" Touchscreen (DSI Ribbon)
- Connect the ribbon cable to either **CAM/DISP0** or **CAM/DISP1** on the Pi 5.
- *Note:* Raspberry Pi 5 uses a high-density 22-pin connector, so use the **15-pin to 22-pin DSI adapter cable** (standard for Pi 5).

### Case B: HDMI + USB Touchscreen (Waveshare / Elecrow / generic)
1. **Display:** Plug a **Micro-HDMI to HDMI** cable from the Pi 5's **HDMI-0** port to the screen's HDMI input.
2. **Touch Digitizer & Power:** Plug a **USB-A to Micro-USB / Type-C** cable from any USB 3.0 port on the Pi 5 to the screen's **Touch / USB** port.

---

## 🚀 2. Quick 1-Command Setup on Raspberry Pi 5

Open the terminal on your Raspberry Pi 5 and run:

```bash
# 1. Clone your project repository
cd ~
git clone https://github.com/TheDhruv06/vending_machine.git
cd vending_machine

# 2. Run the automated setup script
bash rpi/setup.sh
```

### What `setup.sh` does automatically:
- Installs `python3-venv`, `chromium-browser`, `unclutter` (hides cursor on touch), and `curl`.
- Creates an isolated Python virtual environment (`venv`) to comply with Raspberry Pi OS Bookworm rules.
- Installs all dependencies (`Flask`, `pyserial`, `requests`).
- Configures auto-start on boot so the touchscreen opens the vending machine UI immediately when powered on.

---

## 🧪 3. Test Running the Kiosk Manually

To launch the kiosk right now without rebooting:

```bash
cd ~/vending_machine
bash rpi/start_kiosk.sh
```

Your 7-inch touchscreen will immediately launch into **fullscreen Kiosk mode**:
- Welcome screen appears with 2 options: **Take Health Assessment** and **Direct Quick Brew**.
- Touch buttons are responsive and styled for finger taps.
- The mouse cursor is hidden.
- There are no window frames, URLs, or browser tabs.

*(To exit Kiosk mode during testing, press `Alt + F4` or `Ctrl + W` on a keyboard connected to the Pi).*

---

## 🔄 4. Auto-Start on Every Boot

Because `setup.sh` installed the autostart entry into `~/.config/autostart/soilveda_kiosk.desktop`:

1. Simply reboot the Pi:
   ```bash
   sudo reboot
   ```
2. When the Raspberry Pi 5 finishes booting, it automatically starts the Flask server and opens the full-screen touch interface on the 7-inch screen!

---

## 🛠️ 5. Helpful Tips for 7-Inch Touchscreen

### If the display orientation is upside down:
1. Open the Raspberry Pi Menu &rarr; **Preferences** &rarr; **Screen Configuration**.
2. Right-click the display &rarr; **Orientation** &rarr; Select `Normal`, `Inverted`, or `Right` &rarr; Click **Apply**.

### Accessing the UI from your laptop/phone on the same Wi-Fi:
The Flask server listens on `0.0.0.0:5000`. You can test it remotely by finding your Pi's IP address (`hostname -I`) and typing in your laptop browser:
```
http://<YOUR_PI_IP>:5000
```
