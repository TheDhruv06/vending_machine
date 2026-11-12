/*
 * =====================================================================================
 * SOILVEDA ORGANICS - AYURVEDIC VENDING MACHINE
 * MODULE: STANDALONE ESP32 MOTOR & PUMP CONTROLLER (PHONE WIFI + USB SERIAL CONTROL)
 * =====================================================================================
 * Target Board  : ESP32 Dev Module (30-pin / 38-pin)
 * Motor Driver 1: L298N #1 -> Controls 2 BO Motors (Powder Containers)
 *   - Motor 1 (D1 M1): Container 1 -> Lemongrass Sip BO Motor
 *   - Motor 2 (D1 M2): Container 2 -> MedoHar Sip BO Motor
 * Motor Driver 2: L298N #2 -> Controls 2 Water Pumps
 *   - Motor 1 (D2 M1): Water Dispense Pump (Dispenses water)
 *   - Motor 2 (D2 M2): Water Extract Pump  (Extracts / pumps out water)
 *
 * HOW TO CONTROL FROM YOUR PHONE (NO INTERNET OR APP NEEDED):
 * 1. Power the ESP32 (via USB charger, power bank, or laptop).
 * 2. On your phone, open WiFi settings and connect to:
 *      WiFi Name : SoilVeda_Dispenser
 *      Password  : 12345678
 * 3. Open Chrome / Safari on your phone and go to: http://192.168.4.1
 * 4. Use the quick buttons OR type commands like "MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC"!
 *
 * HOW TO CONTROL VIA USB SERIAL MONITOR (Baud Rate: 115200):
 *   - "MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC"  -> Runs Driver 1, Motor 2 for 3 seconds
 *   - "D1 M1 2.5"                         -> Runs Driver 1, Motor 1 for 2.5 seconds
 *   - "1 2 3"                             -> Runs Driver 1, Motor 2 for 3 seconds
 *   - "MOTOR DRIVER 2 MOTOR 1 FOR 5 SEC"  -> Runs Water Dispense Pump for 5 seconds
 *   - "S" or "STOP"                       -> Emergency Stop (works anytime!)
 * =====================================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// =====================================================================================
// 1. PHONE WIFI HOTSPOT CONFIGURATION (NO INTERNET REQUIRED)
// =====================================================================================
const char* AP_SSID = "SoilVeda_Dispenser";
const char* AP_PASS = "12345678";

WebServer server(80);
volatile bool abortRequested = false;

// Pending job queued from Phone UI so HTTP response returns immediately
bool hasPendingPhoneJob = false;
int pendingDriver = 1;
int pendingMotor = 1;
unsigned long pendingDurationMs = 0;

// =====================================================================================
// 2. PIN DEFINITIONS (MATCHING L298N SILKSCREEN LABELS: IN1, IN2, IN3, IN4)
// =====================================================================================
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

// Onboard status LED (GPIO 2 on most ESP32 boards)
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

String lastLogMessage = "Ready. Waiting for command from Phone or Serial Monitor.";

// =====================================================================================
// 3. HARDWARE INITIALIZATION & MOTOR CONTROL
// =====================================================================================

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
  abortRequested = true;
  for (int i = 0; i < 4; i++) {
    digitalWrite(channels[i].pinIn1, LOW);
    digitalWrite(channels[i].pinIn2, LOW);
  }
  digitalWrite(STATUS_LED, LOW);
  lastLogMessage = "EMERGENCY STOP: All motors and pumps are OFF.";
  Serial.println("\n[STOPPED] All motors and pumps are OFF.");
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
    lastLogMessage = "ERROR: Invalid Driver (1-2) or Motor (1-2).";
    Serial.println("[ERROR] Invalid selection! Driver must be 1 or 2, Motor must be 1 or 2.");
    return;
  }

  abortRequested = false;
  float durationSec = durationMs / 1000.0;

  Serial.println("\n=========================================================");
  Serial.printf(">> STARTING : %s\n", channels[idx].name);
  Serial.printf("   Function : %s\n", channels[idx].role);
  Serial.printf("   Duration : %.2f seconds (%lu ms)\n", durationSec, durationMs);
  Serial.println("=========================================================");

  lastLogMessage = "Completed: " + String(channels[idx].name) + " (" + String(channels[idx].role) + ") for " + String(durationSec, 2) + " sec.";

  digitalWrite(STATUS_LED, HIGH);
  digitalWrite(channels[idx].pinIn1, HIGH);
  digitalWrite(channels[idx].pinIn2, LOW);

  unsigned long startTime = millis();
  unsigned long lastPrintTime = 0;

  while (millis() - startTime < durationMs) {
    // Keep Phone Web UI responsive during run so STOP button works instantly
    server.handleClient();

    if (abortRequested) {
      Serial.println("[ABORTED BY USER]\n");
      return;
    }

    unsigned long elapsed = millis() - startTime;
    if (elapsed - lastPrintTime >= 1000 || lastPrintTime == 0) {
      lastPrintTime = elapsed;
      float remainingSec = (durationMs - elapsed) / 1000.0;
      Serial.printf("   Running... %.1f sec remaining\n", remainingSec);
    }

    if (Serial.available() > 0) {
      String abortCmd = Serial.readStringUntil('\n');
      abortCmd.trim();
      abortCmd.toUpperCase();
      if (abortCmd == "S" || abortCmd == "STOP") {
        emergencyStopAll();
        Serial.println("[ABORTED BY SERIAL USER]\n");
        return;
      }
    }

    delay(10);
  }

  digitalWrite(channels[idx].pinIn1, LOW);
  digitalWrite(channels[idx].pinIn2, LOW);
  digitalWrite(STATUS_LED, LOW);

  Serial.printf(">> [COMPLETE] %s stopped after %.2f seconds.\n\n", channels[idx].name, durationSec);
}

// =====================================================================================
// 4. SMART TEXT COMMAND PARSER (SHARED BY PHONE & SERIAL)
// =====================================================================================

bool parseCommandString(String rawInput, int &outDriver, int &outMotor, unsigned long &outDurationMs, String &errMsg) {
  rawInput.trim();
  String upper = rawInput;
  upper.toUpperCase();

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
    errMsg = "Need 3 numbers (Driver, Motor, Duration). Example: MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC";
    return false;
  }

  outDriver = (int)nums[0];
  outMotor  = (int)nums[1];
  float rawDuration = nums[2];

  if (outDriver < 1 || outDriver > 2) {
    errMsg = "Invalid Motor Driver '" + String(outDriver) + "'. Use Driver 1 or 2.";
    return false;
  }
  if (outMotor < 1 || outMotor > 2) {
    errMsg = "Invalid Motor '" + String(outMotor) + "'. Use Motor 1 or 2.";
    return false;
  }
  if (rawDuration <= 0) {
    errMsg = "Duration must be greater than 0!";
    return false;
  }

  outDurationMs = isMilliseconds ? (unsigned long)rawDuration : (unsigned long)(rawDuration * 1000.0);
  return true;
}

void handleSerialCommand(String rawInput) {
  rawInput.trim();
  if (rawInput.length() == 0) return;

  Serial.println(rawInput);
  String upper = rawInput;
  upper.toUpperCase();

  if (upper == "S" || upper == "STOP") {
    emergencyStopAll();
    Serial.print("Waiting for command > ");
    return;
  }

  int driverId, motorId;
  unsigned long durationMs;
  String errMsg;

  if (parseCommandString(rawInput, driverId, motorId, durationMs, errMsg)) {
    runMotorForDuration(driverId, motorId, durationMs);
  } else {
    Serial.println("[ERROR] " + errMsg);
  }
  Serial.print("Waiting for command > ");
}

// =====================================================================================
// 5. PHONE WIFI CONTROL PANEL (SERVED AT http://192.168.4.1)
// =====================================================================================

void handlePhoneHome() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SoilVeda ESP32 Controller</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #f3f8f4; margin: 0; padding: 16px; color: #1b3022; }
    .card { max-width: 460px; margin: 0 auto 16px auto; background: #fff; border-radius: 16px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border: 1px solid #d9e8dd; }
    h2 { margin: 0 0 4px 0; color: #1b4332; font-size: 20px; }
    p.sub { margin: 0 0 16px 0; font-size: 13px; color: #52796f; }
    label { display: block; font-size: 13px; font-weight: 700; margin-bottom: 6px; margin-top: 12px; }
    select, input[type=number], input[type=text] { width: 100%; padding: 12px; border: 1.5px solid #cbd9cf; border-radius: 10px; font-size: 15px; box-sizing: border-box; background: #fafcfa; }
    .btn { width: 100%; padding: 14px; border: none; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 14px; }
    .btn-run { background: #1b4332; color: #fff; }
    .btn-cmd { background: #2d6a4f; color: #fff; }
    .btn-stop { background: #dc2626; color: #fff; margin-top: 10px; }
    .status { background: #e8f5ec; border: 1px solid #b7e3c2; color: #1b4332; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 600; margin-bottom: 14px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Soil Veda Hardware Tester</h2>
    <p class="sub">Connected directly to ESP32 via WiFi</p>
    <div class="status">)rawliteral";
  html += lastLogMessage;
  html += R"rawliteral(</div>

    <form action="/run" method="GET">
      <div class="row">
        <div>
          <label>Motor Driver</label>
          <select name="driver">
            <option value="1">Driver 1 (BO Motors)</option>
            <option value="2">Driver 2 (Water Pumps)</option>
          </select>
        </div>
        <div>
          <label>Motor / Channel</label>
          <select name="motor">
            <option value="1">Motor 1 (Lemongrass / Dispense)</option>
            <option value="2">Motor 2 (MedoHar / Extract)</option>
          </select>
        </div>
      </div>

      <label>Duration (Seconds)</label>
      <input type="number" name="sec" step="0.1" min="0.1" value="3">

      <button type="submit" class="btn btn-run">RUN MOTOR / PUMP</button>
    </form>

    <form action="/stop" method="GET">
      <button type="submit" class="btn btn-stop">EMERGENCY STOP ALL</button>
    </form>
  </div>

  <div class="card">
    <h2>Text Command Console</h2>
    <p class="sub">Type commands just like the Serial Monitor:</p>
    <form action="/cmd" method="GET">
      <input type="text" name="text" placeholder="e.g. MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC" required>
      <button type="submit" class="btn btn-cmd">SEND COMMAND</button>
    </form>
  </div>
</body>
</html>
)rawliteral";
  server.send(200, "text/html", html);
}

void handlePhoneRun() {
  int driver = server.arg("driver").toInt();
  int motor  = server.arg("motor").toInt();
  float sec  = server.arg("sec").toFloat();

  if (driver >= 1 && driver <= 2 && motor >= 1 && motor <= 2 && sec > 0) {
    pendingDriver = driver;
    pendingMotor = motor;
    pendingDurationMs = (unsigned long)(sec * 1000.0);
    hasPendingPhoneJob = true;
    int idx = findChannelIndex(driver, motor);
    lastLogMessage = "Running: " + String(channels[idx].name) + " for " + String(sec, 2) + " sec...";
  } else {
    lastLogMessage = "Invalid parameters received from Phone.";
  }
  server.sendHeader("Location", "/");
  server.send(302, "text/plain", "");
}

void handlePhoneCmd() {
  String cmd = server.arg("text");
  cmd.trim();
  String upper = cmd;
  upper.toUpperCase();

  if (upper == "S" || upper == "STOP") {
    emergencyStopAll();
  } else {
    int driverId, motorId;
    unsigned long durationMs;
    String errMsg;
    if (parseCommandString(cmd, driverId, motorId, durationMs, errMsg)) {
      pendingDriver = driverId;
      pendingMotor = motorId;
      pendingDurationMs = durationMs;
      hasPendingPhoneJob = true;
      int idx = findChannelIndex(driverId, motorId);
      lastLogMessage = "Running: " + String(channels[idx].name) + " for " + String(durationMs / 1000.0, 2) + " sec...";
    } else {
      lastLogMessage = "ERROR: " + errMsg;
    }
  }
  server.sendHeader("Location", "/");
  server.send(302, "text/plain", "");
}

void handlePhoneStop() {
  emergencyStopAll();
  server.sendHeader("Location", "/");
  server.send(302, "text/plain", "");
}

// =====================================================================================
// 6. MAIN SETUP & LOOP
// =====================================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  initHardware();

  // Start built-in WiFi Hotspot so any Phone can connect wirelessly
  WiFi.softAP(AP_SSID, AP_PASS);
  IPAddress myIP = WiFi.softAPIP();

  server.on("/", handlePhoneHome);
  server.on("/run", handlePhoneRun);
  server.on("/cmd", handlePhoneCmd);
  server.on("/stop", handlePhoneStop);
  server.begin();

  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH); delay(100);
    digitalWrite(STATUS_LED, LOW); delay(100);
  }

  Serial.println("\n=========================================================");
  Serial.println(" SOIL VEDA ESP32 READY (PHONE WIFI + USB SERIAL CONTROL) ");
  Serial.println("=========================================================");
  Serial.printf(" Phone WiFi SSID : %s\n", AP_SSID);
  Serial.printf(" Phone Password  : %s\n", AP_PASS);
  Serial.print(" Phone Browser   : http://");
  Serial.println(myIP);
  Serial.println("---------------------------------------------------------");
  Serial.println(" Or type in Serial Monitor: MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC");
  Serial.println("=========================================================");
  Serial.print("Waiting for command > ");
}

void loop() {
  // Listen to requests from Phone Web Panel
  server.handleClient();

  // Execute any queued command from Phone UI immediately
  if (hasPendingPhoneJob) {
    hasPendingPhoneJob = false;
    runMotorForDuration(pendingDriver, pendingMotor, pendingDurationMs);
  }

  // Listen to commands from USB Serial Monitor
  if (Serial.available() > 0) {
    String inputLine = Serial.readStringUntil('\n');
    handleSerialCommand(inputLine);
  }

  delay(10);
}
