# Soil Veda Organics - ESP32 Dispensing Hardware Guide

This directory contains the complete ESP32 firmware for controlling the BO gear motors attached to the powder dispensing containers / augers.

---

## 📁 Sketches in this Directory

| Sketch Folder | Purpose | When to Use |
| :--- | :--- | :--- |
| **`1_standalone_motor_test/`** | Hardware Calibration & Diagnostics | **Start here!** Test your BO motors, verify wiring, and calibrate exact powder drop runtime using the Serial Monitor menu without needing WiFi. |
| **`2_web_linked_dispenser/`** | Web UI Integration & Cloud Polling | Connects to your WiFi and listens to the web app (`/api/dispense/poll`). Triggers the exact BO motor when someone clicks **"Dispense"** on the website. |

---

## 🔌 Hardware Wiring Diagram

### 1. ESP32 to L298N Motor Driver Connection

```
ESP32 Dev Board                     L298N Motor Driver 1 (Containers 1 & 2)
  [GPIO 18] ------------------------> [IN1] (Motor 1 / Container 1 Forward)
  [GPIO 19] ------------------------> [IN2] (Motor 1 / Container 1 Reverse)
  [GPIO 21] ------------------------> [IN3] (Motor 2 / Container 2 Forward)
  [GPIO 22] ------------------------> [IN4] (Motor 2 / Container 2 Reverse)
  [GND]     ------------------------> [GND] (COMMON GROUND WITH POWER SUPPLY)

ESP32 Dev Board                     L298N Motor Driver 2 (Containers 3 & 4)
  [GPIO 23] ------------------------> [IN1] (Motor 3 / Container 3 Forward)
  [GPIO 25] ------------------------> [IN2] (Motor 3 / Container 3 Reverse)
  [GPIO 26] ------------------------> [IN3] (Motor 4 / Container 4 Forward)
  [GPIO 27] ------------------------> [IN4] (Motor 4 / Container 4 Reverse)
  [GND]     ------------------------> [GND] (COMMON GROUND)
```

### 2. Motor & Power Supply Wiring (CRITICAL)

> [!CAUTION]
> **NEVER power BO motors directly from the ESP32 3.3V or 5V (VIN) pin!**  
> BO motors draw heavy current surges when starting, which will crash or permanently damage your ESP32 board.

- **External DC Power Supply (6V, 9V, or 12V DC):**
  - Connect **Positive (+)** from battery/adapter &rarr; **L298N 12V Screw Terminal**.
  - Connect **Negative (-)** from battery/adapter &rarr; **L298N GND Screw Terminal**.
  - Connect **ESP32 GND** &rarr; **L298N GND Screw Terminal** *(Common ground is mandatory so signals are recognized).*
- **Motor Outputs:**
  - Connect BO Motor 1 (Container 1) wires &rarr; L298N **OUT1** and **OUT2**.
  - Connect BO Motor 2 (Container 2) wires &rarr; L298N **OUT3** and **OUT4**.
  - Connect BO Motor 3 (Container 3) wires &rarr; L298N Driver 2 **OUT1** and **OUT2**.
  - Connect BO Motor 4 (Container 4) wires &rarr; L298N Driver 2 **OUT3** and **OUT4**.

---

## 🌿 Container to Formulation Mapping

| Container ID | BO Motor | Formulation | Clinical Role |
| :---: | :---: | :--- | :--- |
| **1** | Motor 1 | **Tea A: Lemongrass Sip** / Kashaya A | Vata-Hara / Digestive Carminative |
| **2** | Motor 2 | **Tea B: Vital Sip** / Kashaya B | Pitta-Hara / Cooling & Cardiotonic |
| **3** | Motor 3 | **Tea C: MedoHar Sip** / Kashaya C | Kapha-Hara / Deepana-Pachana |
| **4** | Motor 4 | **Tea D: Mangalayu Tea** / Regular Tea | Vata-Anulomana / Gut Regularizer |

---

## 🚀 How to Run & Calibrate

### Step 1: Upload `1_standalone_motor_test.ino`
1. Open Arduino IDE.
2. Select your board: **Tools &rarr; Board &rarr; ESP32 Arduino &rarr; ESP32 Dev Module**.
3. Select your COM Port under **Tools &rarr; Port**.
4. Open `esp32/1_standalone_motor_test/1_standalone_motor_test.ino` and click **Upload**.
5. Open **Serial Monitor** at **115200 baud**.
6. Type:
   - `1` or `A` &rarr; Spins Motor 1 for 2.5 seconds.
   - `2` or `B` &rarr; Spins Motor 2 for 2.5 seconds.
   - `T` &rarr; Runs automated test on all 4 motors.
   - `+` or `-` &rarr; Adjusts duration in steps of 250ms until you get the exact grams of powder needed!

---

### Step 2: Upload `2_web_linked_dispenser.ino`
1. Open `esp32/2_web_linked_dispenser/2_web_linked_dispenser.ino`.
2. Edit lines 33-34 with your WiFi name and password:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   ```
3. Click **Upload**.
4. Open **Serial Monitor** at **115200 baud**.
5. Watch the ESP32 connect to WiFi and display its IP address and polling status.
6. Open your website (`https://vending-machine-eosin-five.vercel.app`), answer the 7 questions, and click **Dispense**.
7. Watch the ESP32 receive the order in real time and trigger the exact motor for that prescribed formulation!
