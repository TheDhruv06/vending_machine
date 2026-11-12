/*
 * =====================================================================================
 * SOILVEDA ORGANICS - AYURVEDIC VENDING MACHINE
 * MODULE: STANDALONE ESP32 MOTOR & WATER PUMP CONTROLLER (SERIAL TERMINAL CONTROL)
 * =====================================================================================
 * Target Board  : ESP32 Dev Module (30-pin / 38-pin)
 * Motor Driver 1: L298N #1 -> Controls 2 BO Motors (Powder Containers)
 *   - Motor 1 (D1 M1): Container 1 -> Lemongrass Sip BO Motor
 *   - Motor 2 (D1 M2): Container 2 -> MedoHar Sip BO Motor
 * Motor Driver 2: L298N #2 -> Controls 2 Water Pumps
 *   - Motor 1 (D2 M1): Water Dispense Pump (Dispenses water)
 *   - Motor 2 (D2 M2): Water Extract Pump  (Extracts / pumps out water)
 *
 * HOW TO CONTROL VIA SERIAL MONITOR (Baud Rate: 115200):
 * Simply type any command like:
 *   - "MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC"  -> Runs Driver 1, Motor 2 for 3 seconds
 *   - "D1 M1 2.5"                         -> Runs Driver 1, Motor 1 for 2.5 seconds
 *   - "1 2 3"                             -> Runs Driver 1, Motor 2 for 3 seconds
 *   - "MOTOR DRIVER 2 MOTOR 1 FOR 5 SEC"  -> Runs Water Dispense Pump for 5 seconds
 *   - "D2 M2 4"                           -> Runs Water Extract Pump for 4 seconds
 *   - "S" or "STOP"                       -> Emergency Stop (works anytime!)
 *
 * HARDWARE WIRING (ESP32 TO BOTH L298N DRIVERS):
 * -------------------------------------------------------------------------------------
 *  ESP32 Pin  -> Driver Pin          -> Hardware Function
 *  GPIO 18    -> Driver 1 IN1        -> Driver 1, Motor 1 (Lemongrass Sip BO Motor)
 *  GPIO 19    -> Driver 1 IN2        -> Driver 1, Motor 1
 *  GPIO 21    -> Driver 1 IN3        -> Driver 1, Motor 2 (MedoHar Sip BO Motor)
 *  GPIO 22    -> Driver 1 IN4        -> Driver 1, Motor 2
 *
 *  GPIO 23    -> Driver 2 IN1        -> Driver 2, Motor 1 (Water Dispense Pump)
 *  GPIO 25    -> Driver 2 IN2        -> Driver 2, Motor 1
 *  GPIO 26    -> Driver 2 IN3        -> Driver 2, Motor 2 (Water Extract Pump)
 *  GPIO 27    -> Driver 2 IN4        -> Driver 2, Motor 2
 *
 *  GND        -> Driver 1 & 2 GND    -> COMMON GROUND WITH EXTERNAL POWER SUPPLY!
 *
 * NOTE ON L298N JUMPERS:
 * Keep the 2 green/black ENA & ENB jumper caps ON both L298N boards for full speed.
 * Always use an external 6V-12V power supply connected to the L298N 12V terminal
 * (never power motors/pumps from ESP32 3.3V/5V pins).
 * =====================================================================================
 */

#include <Arduino.h>

// =====================================================================================
// 1. PIN DEFINITIONS
// =====================================================================================
// MOTOR DRIVER 1: BO MOTORS (TEA CONTAINERS)
#define MD1_M1_IN1 18   // Container 1: Lemongrass Sip
#define MD1_M1_IN2 19
#define MD1_M2_IN1 21   // Container 2: MedoHar Sip
#define MD1_M2_IN2 22

// MOTOR DRIVER 2: WATER PUMPS
#define MD2_M1_IN1 23   // Water Pump 1: Water Dispense Pump
#define MD2_M1_IN2 25
#define MD2_M2_IN1 26   // Water Pump 2: Water Extract Pump
#define MD2_M2_IN2 27

// Onboard status LED (GPIO 2 on most ESP32 boards)
#define STATUS_LED 2

// Structure representing each Driver/Motor channel
struct ActuatorChannel {
  uint8_t driverId;     // 1 or 2
  uint8_t motorId;      // 1 or 2
  uint8_t pinIn1;
  uint8_t pinIn2;
  const char* name;
  const char* role;
};

// Complete table of all 4 controlled channels
const ActuatorChannel channels[4] = {
  {1, 1, MD1_M1_IN1, MD1_M1_IN2, "Driver 1 - Motor 1", "BO Motor 1 (Lemongrass Sip Container)"},
  {1, 2, MD1_M2_IN1, MD1_M2_IN2, "Driver 1 - Motor 2", "BO Motor 2 (MedoHar Sip Container)"},
  {2, 1, MD2_M1_IN1, MD2_M1_IN2, "Driver 2 - Motor 1", "Water Pump 1 (Water Dispense Pump)"},
  {2, 2, MD2_M2_IN1, MD2_M2_IN2, "Driver 2 - Motor 2", "Water Pump 2 (Water Extract Pump)"}
};

// =====================================================================================
// 2. HARDWARE INITIALIZATION & MOTOR CONTROL
// =====================================================================================

/**
 * Sets all motor/pump control pins as OUTPUT and ensures everything starts OFF.
 */
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

/**
 * Stops all 4 motors/pumps immediately.
 */
void emergencyStopAll() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(channels[i].pinIn1, LOW);
    digitalWrite(channels[i].pinIn2, LOW);
  }
  digitalWrite(STATUS_LED, LOW);
  Serial.println("\n[STOPPED] All motors and pumps are OFF.");
}

/**
 * Finds the matching channel index for a given (driverId, motorId).
 */
int findChannelIndex(int driverId, int motorId) {
  for (int i = 0; i < 4; i++) {
    if (channels[i].driverId == driverId && channels[i].motorId == motorId) {
      return i;
    }
  }
  return -1;
}

/**
 * Runs a specific Motor Driver & Motor for the assigned duration in milliseconds.
 * Monitors Serial input during runtime so user can type 'S' to abort anytime.
 */
void runMotorForDuration(int driverId, int motorId, unsigned long durationMs) {
  int idx = findChannelIndex(driverId, motorId);
  if (idx == -1) {
    Serial.println("[ERROR] Invalid selection! Driver must be 1 or 2, Motor must be 1 or 2.");
    return;
  }

  float durationSec = durationMs / 1000.0;

  Serial.println("\n=========================================================");
  Serial.printf(">> STARTING : %s\n", channels[idx].name);
  Serial.printf("   Function : %s\n", channels[idx].role);
  Serial.printf("   Duration : %.2f seconds (%lu ms)\n", durationSec, durationMs);
  Serial.println("   (Type 'S' or 'STOP' anytime to abort)");
  Serial.println("=========================================================");

  digitalWrite(STATUS_LED, HIGH);

  // Turn ON Motor / Pump (Forward polarity: IN1 = HIGH, IN2 = LOW)
  digitalWrite(channels[idx].pinIn1, HIGH);
  digitalWrite(channels[idx].pinIn2, LOW);

  unsigned long startTime = millis();
  unsigned long lastPrintTime = 0;

  while (millis() - startTime < durationMs) {
    unsigned long elapsed = millis() - startTime;

    // Print progress once every 1000ms
    if (elapsed - lastPrintTime >= 1000 || lastPrintTime == 0) {
      lastPrintTime = elapsed;
      float remainingSec = (durationMs - elapsed) / 1000.0;
      Serial.printf("   Running... %.1f sec remaining\n", remainingSec);
    }

    // Check if user sent an emergency stop during execution
    if (Serial.available() > 0) {
      String abortCmd = Serial.readStringUntil('\n');
      abortCmd.trim();
      abortCmd.toUpperCase();
      if (abortCmd == "S" || abortCmd == "STOP") {
        emergencyStopAll();
        Serial.println("[ABORTED BY USER]\n");
        return;
      }
    }

    delay(10);
  }

  // Turn OFF Motor / Pump
  digitalWrite(channels[idx].pinIn1, LOW);
  digitalWrite(channels[idx].pinIn2, LOW);
  digitalWrite(STATUS_LED, LOW);

  Serial.printf(">> [COMPLETE] %s stopped after %.2f seconds.\n\n", channels[idx].name, durationSec);
}

// =====================================================================================
// 3. SMART SERIAL TERMINAL COMMAND PARSER
// =====================================================================================

void printMenu() {
  Serial.println("\n=========================================================");
  Serial.println("   SOILVEDA ORGANICS - STANDALONE MOTOR & PUMP TESTER    ");
  Serial.println("=========================================================");
  Serial.println(" HARDWARE MAP:");
  Serial.println("   Motor Driver 1, Motor 1 : BO Motor 1 (Lemongrass Sip)");
  Serial.println("   Motor Driver 1, Motor 2 : BO Motor 2 (MedoHar Sip)");
  Serial.println("   Motor Driver 2, Motor 1 : Water Dispense Pump");
  Serial.println("   Motor Driver 2, Motor 2 : Water Extract Pump");
  Serial.println("---------------------------------------------------------");
  Serial.println(" HOW TO ENTER COMMANDS (Any format works!):");
  Serial.println("   1) MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC");
  Serial.println("   2) D1 M2 3       (Driver 1, Motor 2, 3 sec)");
  Serial.println("   3) 2 1 5         (Driver 2, Motor 1, 5 sec)");
  Serial.println("   4) 1 1 2.5       (Supports decimals like 2.5 sec)");
  Serial.println("   5) 1 2 1500ms    (Add 'ms' to specify milliseconds)");
  Serial.println("   6) STOP or S     (Emergency Stop all motors & pumps)");
  Serial.println("   7) HELP or MENU  (Show this guide again)");
  Serial.println("=========================================================");
  Serial.print("Waiting for command > ");
}

/**
 * Parses natural language or numeric serial commands.
 * Extracts the first 3 numbers found in the string:
 *   Number 1 -> Motor Driver (1 or 2)
 *   Number 2 -> Motor (1 or 2)
 *   Number 3 -> Duration (seconds, or ms if "ms" is in the string)
 */
void parseAndExecuteCommand(String rawInput) {
  rawInput.trim();
  if (rawInput.length() == 0) return;

  Serial.println(rawInput);

  String upper = rawInput;
  upper.toUpperCase();

  // Quick special commands
  if (upper == "S" || upper == "STOP") {
    emergencyStopAll();
    Serial.print("Waiting for command > ");
    return;
  }

  if (upper == "HELP" || upper == "MENU" || upper == "?") {
    printMenu();
    return;
  }

  bool isMilliseconds = (upper.indexOf("MS") != -1);

  // Extract up to 3 numeric values (supports decimals like 2.5)
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
  // Catch trailing number at the end of string
  if (currentToken.length() > 0 && numCount < 3) {
    nums[numCount++] = currentToken.toFloat();
  }

  if (numCount < 3) {
    Serial.println("[ERROR] Could not read Driver, Motor, and Duration.");
    Serial.println("Example: 'MOTOR DRIVER 1 MOTOR 2 FOR 3 SEC' or '1 2 3'");
    Serial.print("Waiting for command > ");
    return;
  }

  int driverId = (int)nums[0];
  int motorId  = (int)nums[1];
  float rawDuration = nums[2];

  if (driverId < 1 || driverId > 2) {
    Serial.printf("[ERROR] Invalid Motor Driver '%d'. Please specify Driver 1 or 2.\n", driverId);
    Serial.print("Waiting for command > ");
    return;
  }

  if (motorId < 1 || motorId > 2) {
    Serial.printf("[ERROR] Invalid Motor '%d'. Please specify Motor 1 or 2.\n", motorId);
    Serial.print("Waiting for command > ");
    return;
  }

  if (rawDuration <= 0) {
    Serial.println("[ERROR] Duration must be greater than 0!");
    Serial.print("Waiting for command > ");
    return;
  }

  unsigned long durationMs = isMilliseconds ? (unsigned long)rawDuration : (unsigned long)(rawDuration * 1000.0);

  // Execute the command!
  runMotorForDuration(driverId, motorId, durationMs);
  Serial.print("Waiting for command > ");
}

// =====================================================================================
// 4. MAIN SETUP & LOOP
// =====================================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  initHardware();

  // Startup LED blink (3 pulses)
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(100);
    digitalWrite(STATUS_LED, LOW);
    delay(100);
  }

  printMenu();
}

void loop() {
  if (Serial.available() > 0) {
    String inputLine = Serial.readStringUntil('\n');
    parseAndExecuteCommand(inputLine);
  }
  delay(10);
}
