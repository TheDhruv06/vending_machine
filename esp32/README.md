# Soil Veda Organics - ESP32 Hardware Control Guide

This directory contains the ESP32 firmware for your 2-Tea Herbal Vending Machine hardware.

---

## 📁 Hardware Architecture

- **Motor Driver 1 (L298N #1) — Powder Containers (2 BO Motors):**
  - **Driver 1, Motor 1:** Container 1 BO Motor &rarr; **Lemongrass Sip (`Tea A`)**
  - **Driver 1, Motor 2:** Container 2 BO Motor &rarr; **MedoHar Sip (`Tea C`)**
- **Motor Driver 2 (L298N #2) — Water System (2 Water Pumps):**
  - **Driver 2, Motor 1:** **Water Dispense Pump** (dispenses water)
  - **Driver 2, Motor 2:** **Water Extract Pump** (extracts/pumps out water)

---

## 🔌 Wiring Diagram (ESP32 to L298N Drivers)

```
ESP32 Dev Board                     L298N Motor Driver 1 (2 BO Motors)
  [GPIO 18] ------------------------> [IN1] -> Driver 1, Motor 1 (Lemongrass Sip)
  [GPIO 19] ------------------------> [IN2] -> Driver 1, Motor 1
  [GPIO 21] ------------------------> [IN3] -> Driver 1, Motor 2 (MedoHar Sip)
  [GPIO 22] ------------------------> [IN4] -> Driver 1, Motor 2
  [GND]     ------------------------> [GND] -> COMMON GROUND

ESP32 Dev Board                     L298N Motor Driver 2 (2 Water Pumps)
  [GPIO 23] ------------------------> [IN1] -> Driver 2, Motor 1 (Water Dispense Pump)
  [GPIO 25] ------------------------> [IN2] -> Driver 2, Motor 1
  [GPIO 26] ------------------------> [IN3] -> Driver 2, Motor 2 (Water Extract Pump)
  [GPIO 27] ------------------------> [IN4] -> Driver 2, Motor 2
  [GND]     ------------------------> [GND] -> COMMON GROUND
```

> [!CAUTION]
> **Power Supply Rules:**
> 1. Keep the **ENA** and **ENB** jumper caps **ON** both L298N boards for full speed.
> 2. **NEVER** power BO motors or water pumps from the ESP32 3.3V or 5V (VIN) pins!
> 3. Use an external 6V–12V DC power supply connected to the L298N `12V` terminal, and share a **Common Ground (`GND`)** between the power supply, L298N drivers, and ESP32.

---

## 📱 How to Control from Your Phone via Bluetooth ("Serial Bluetooth Terminal")

File: [`1_standalone_motor_test/1_standalone_motor_test.ino`](1_standalone_motor_test/1_standalone_motor_test.ino)

1. Upload `esp32/1_standalone_motor_test/1_standalone_motor_test.ino` to your ESP32 via Arduino IDE (Board: **ESP32 Dev Module**).
2. Power the ESP32 (from a power bank, USB charger, or laptop).
3. On your Android phone, open **Bluetooth Settings** and pair with **`SoilVeda_ESP32`**.
4. Open the **Serial Bluetooth Terminal** app:
   - Tap the top-left menu (&equiv;) &rarr; **Devices** &rarr; **Bluetooth Classic** &rarr; Tap **`SoilVeda_ESP32`**.
5. Once connected, the ESP32 sends the command menu directly to your phone screen!
6. Type any command in the terminal and press Send:
   - `MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC` &rarr; Spins MedoHar Sip BO Motor for 3 seconds
   - `MOTOR DRIVER 1 MOTOR 1 FOR 2.5 SEC` &rarr; Spins Lemongrass Sip BO Motor for 2.5 seconds
   - `MOTOR DRIVER 2 MOTOR 1 FOR 5 SEC` &rarr; Runs Water Dispense Pump for 5 seconds
   - `D2 M2 4` &rarr; Runs Water Extract Pump for 4 seconds
   - `1 2 3` &rarr; Shortcut for Driver 1, Motor 2, 3 seconds
   - `S` or `STOP` &rarr; Immediately aborts and stops all motors &amp; pumps!
   - `MENU` &rarr; Prints the command menu again

*(Note: USB Serial Monitor in Arduino IDE at `115200` baud also works identically at the same time.)*
