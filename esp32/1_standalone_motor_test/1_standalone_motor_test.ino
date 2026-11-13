/*
 * =====================================================================================
 * SOILVEDA ORGANICS - AYURVEDIC VENDING MACHINE
 * MODULE: STANDALONE ESP32 MOTOR & PUMP CONTROLLER (BLUETOOTH + USB SERIAL)
 * =====================================================================================
 */

#include <Arduino.h>
#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please select a standard ESP32 board (e.g. ESP32 Dev Module).
#endif

const char* BT_DEVICE_NAME = "SoilVeda_ESP32";
BluetoothSerial SerialBT;
volatile bool btJustConnected = false;

// MOTOR DRIVER 1 (L298N #1): BO MOTORS (TEA CONTAINERS)
#define MD1_IN1 18   // Motor 1 (Lemongrass Sip) -> L298N #1 IN1
#define MD1_IN2 19   // Motor 1 (Lemongrass Sip) -> L298N #1 IN2
#define MD1_IN3 21   // Motor 2 (MedoHar Sip)    -> L298N #1 IN3
#define MD1_IN4 22   // Motor 2 (MedoHar Sip)    -> L298N #1 IN4

// MOTOR DRIVER 2 (L298N #2): WATER PUMPS
#define MD2_IN1 23   // Pump 1 (Water Dispense)  -> L298N #2 IN1
#define MD2_IN2 25   // Pump 1 (Water Dispense)  -> L298N #2 IN2
#define MD2_IN3 26   // Pump 2 (Water Extract)   -> L298N #2 IN3
#define MD2_IN4 27   // Pump 2 (Water Extract)   -> L298N #2 IN4

#define STATUS_LED 2

struct ActuatorChannel {
  uint8_t driverId;     // 1 or 2
  uint8_t motorId;      // 1 or 2
  uint8_t pinIn1;
  uint8_t pinIn2;
  const char* name;
  const char* role;
};

const ActuatorChannel channels[4] = {
  {1, 1, MD1_IN1, MD1_IN2, "Driver 1 - Motor 1", "BO Motor 1 (Lemongrass Sip Container)"},
  {1, 2, MD1_IN3, MD1_IN4, "Driver 1 - Motor 2", "BO Motor 2 (MedoHar Sip Container)"},
  {2, 1, MD2_IN1, MD2_IN2, "Driver 2 - Motor 1", "Water Pump 1 (Water Dispense Pump)"},
  {2, 2, MD2_IN3, MD2_IN4, "Driver 2 - Motor 2", "Water Pump 2 (Water Extract Pump)"}
};

void logPrint(const String& msg) {
  Serial.print(msg);
  if (SerialBT.hasClient()) {
    SerialBT.print(msg);
  }
}

void logPrintln(const String& msg) {
  Serial.println(msg);
  if (SerialBT.hasClient()) {
    SerialBT.println(msg);
  }
}

void initHardware() {
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  for (int i = 0; i < 4; i++) {
    pinMode(channels[i].pinIn1, OUTPUT);
    pinMode(channels[i].pinIn2, OUTPUT);
    digitalWrite(channels[i].pinIn1, LOW);
    digitalWrite(channels[i].pinIn2, LOW);
  }
}

void emergencyStopAll() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(channels[i].pinIn1, LOW);
    digitalWrite(channels[i].pinIn2, LOW);
  }
  digitalWrite(STATUS_LED, LOW);
  logPrintln("\n[STOPPED] All motors and pumps are OFF.");
}

int findChannelIndex(int driverId, int motorId) {
  for (int i = 0; i < 4; i++) {
    if (channels[i].driverId == driverId && channels[i].motorId == motorId) {
      return i;
    }
  }
  return -1;
}

void runMotorForDuration(int driverId, int motorId, unsigned long durationMs) {
  int idx = findChannelIndex(driverId, motorId);
  if (idx == -1) {
    logPrintln("[ERROR] Invalid selection! Driver must be 1 or 2, Motor must be 1 or 2.");
    return;
  }

  float durationSec = durationMs / 1000.0;

  logPrintln("\n==================================================");
  logPrintln(">> STARTING : " + String(channels[idx].name));
  logPrintln("   Function : " + String(channels[idx].role));
  logPrintln("   Duration : " + String(durationSec, 2) + " sec (" + String(durationMs) + " ms)");
  logPrintln("   (Send 'S' or 'STOP' anytime to abort)");
  logPrintln("==================================================");

  digitalWrite(STATUS_LED, HIGH);
  digitalWrite(channels[idx].pinIn1, HIGH);
  digitalWrite(channels[idx].pinIn2, LOW);

  unsigned long startTime = millis();
  unsigned long lastPrintTime = 0;

  while (millis() - startTime < durationMs) {
    unsigned long elapsed = millis() - startTime;

    if (elapsed - lastPrintTime >= 1000 || lastPrintTime == 0) {
      lastPrintTime = elapsed;
      float remainingSec = (durationMs - elapsed) / 1000.0;
      logPrintln("   Running... " + String(remainingSec, 1) + " sec left");
    }

    if (SerialBT.available() > 0) {
      String abortCmd = SerialBT.readStringUntil('\n');
      abortCmd.trim();
      abortCmd.toUpperCase();
      if (abortCmd == "S" || abortCmd == "STOP") {
        emergencyStopAll();
        logPrintln("[ABORTED FROM PHONE]\n");
        return;
      }
    }

    if (Serial.available() > 0) {
      String abortCmd = Serial.readStringUntil('\n');
      abortCmd.trim();
      abortCmd.toUpperCase();
      if (abortCmd == "S" || abortCmd == "STOP") {
        emergencyStopAll();
        logPrintln("[ABORTED FROM SERIAL]\n");
        return;
      }
    }

    delay(10);
  }

  digitalWrite(channels[idx].pinIn1, LOW);
  digitalWrite(channels[idx].pinIn2, LOW);
  digitalWrite(STATUS_LED, LOW);

  logPrintln(">> [COMPLETE] " + String(channels[idx].name) + " stopped after " + String(durationSec, 2) + " sec.\n");
}

void printMenu() {
  logPrintln("\n==================================================");
  logPrintln("  SOILVEDA ORGANICS - BLUETOOTH MOTOR CONTROLLER  ");
  logPrintln("==================================================");
  logPrintln(" HARDWARE MAP:");
  logPrintln("  Driver 1, Motor 1 : BO Motor 1 (Lemongrass Sip)");
  logPrintln("  Driver 1, Motor 2 : BO Motor 2 (MedoHar Sip)");
  logPrintln("  Driver 2, Motor 1 : Water Dispense Pump");
  logPrintln("  Driver 2, Motor 2 : Water Extract Pump");
  logPrintln("--------------------------------------------------");
  logPrintln(" COMMAND EXAMPLES:");
  logPrintln("  1) MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC");
  logPrintln("  2) D1 M2 3       (Driver 1, Motor 2, 3 sec)");
  logPrintln("  3) 2 1 5         (Driver 2, Motor 1, 5 sec)");
  logPrintln("  4) 1 1 2.5       (Decimal seconds supported)");
  logPrintln("  5) 1 2 1500ms    (Add 'ms' for milliseconds)");
  logPrintln("  6) STOP or S     (Emergency Stop anytime)");
  logPrintln("  7) MENU or HELP  (Show this menu)");
  logPrintln("==================================================");
  logPrint("Enter command > ");
}

void parseAndExecuteCommand(String rawInput) {
  rawInput.trim();
  if (rawInput.length() == 0) return;

  logPrintln(rawInput);

  String upper = rawInput;
  upper.toUpperCase();

  if (upper == "S" || upper == "STOP") {
    emergencyStopAll();
    logPrint("Enter command > ");
    return;
  }

  if (upper == "HELP" || upper == "MENU" || upper == "?") {
    printMenu();
    return;
  }

  bool isMilliseconds = (upper.indexOf("MS") != -1);

  float nums[3] = {0, 0, 0};
  int numCount = 0;
  String currentToken = "";

  for (unsigned int i = 0; i < upper.length(); i++) {
    char c = upper[i];
    if (isdigit(c) || c == '.') {
      currentToken += c;
    } else {
      if (currentToken.length() > 0 && numCount < 3) {
        nums[numCount++] = currentToken.toFloat();
        currentToken = "";
      }
    }
  }
  if (currentToken.length() > 0 && numCount < 3) {
    nums[numCount++] = currentToken.toFloat();
  }

  if (numCount < 3) {
    logPrintln("[ERROR] Could not read Driver, Motor, and Duration.");
    logPrintln("Example: 'MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC' or '1 2 3'");
    logPrint("Enter command > ");
    return;
  }

  int driverId = (int)nums[0];
  int motorId  = (int)nums[1];
  float rawDuration = nums[2];

  if (driverId < 1 || driverId > 2) {
    logPrintln("[ERROR] Invalid Driver '" + String(driverId) + "'. Specify Driver 1 or 2.");
    logPrint("Enter command > ");
    return;
  }

  if (motorId < 1 || motorId > 2) {
    logPrintln("[ERROR] Invalid Motor '" + String(motorId) + "'. Specify Motor 1 or 2.");
    logPrint("Enter command > ");
    return;
  }

  if (rawDuration <= 0) {
    logPrintln("[ERROR] Duration must be greater than 0!");
    logPrint("Enter command > ");
    return;
  }

  unsigned long durationMs = isMilliseconds ? (unsigned long)rawDuration : (unsigned long)(rawDuration * 1000.0);

  runMotorForDuration(driverId, motorId, durationMs);
  logPrint("Enter command > ");
}

void btConnectionCallback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param) {
  if (event == ESP_SPP_SRV_OPEN_EVT) {
    btJustConnected = true;
  } else if (event == ESP_SPP_CLOSE_EVT) {
    Serial.println("\n[BLUETOOTH] Phone disconnected.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  initHardware();

  SerialBT.register_callback(btConnectionCallback);
  SerialBT.begin(BT_DEVICE_NAME);

  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH); delay(100);
    digitalWrite(STATUS_LED, LOW); delay(100);
  }

  Serial.println("\n==================================================");
  Serial.println(" SOIL VEDA ESP32 READY (BLUETOOTH + USB SERIAL)   ");
  Serial.println("==================================================");
  Serial.printf(" Bluetooth Name: %s\n", BT_DEVICE_NAME);
  Serial.println(" Open 'Serial Bluetooth Terminal' app and connect!");
  printMenu();
}

void loop() {
  if (btJustConnected) {
    btJustConnected = false;
    delay(200);
    Serial.println("\n[BLUETOOTH] Phone connected to SoilVeda_ESP32!");
    printMenu();
  }

  if (SerialBT.available() > 0) {
    String btInput = SerialBT.readStringUntil('\n');
    parseAndExecuteCommand(btInput);
  }

  if (Serial.available() > 0) {
    String usbInput = Serial.readStringUntil('\n');
    parseAndExecuteCommand(usbInput);
  }

  delay(10);
}