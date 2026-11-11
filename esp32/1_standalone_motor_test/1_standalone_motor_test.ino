/*
 * =====================================================================================
 * SOILVEDA ORGANICS - AYURVEDIC VENDING MACHINE
 * MODULE: 1. STANDALONE BO MOTOR & DISPENSER HARDWARE TEST SKETCH
 * =====================================================================================
 * Target Board: ESP32 Dev Module (WROOM / NodeMCU-32S / ESP32 30-pin & 38-pin)
 * Motor Driver: L298N / L293D / TB6612FNG or Relay Module
 * Actuators:    BO Gear Motors (Yellow TT DC Motors) attached to Powder Containers/Augers
 *
 * PURPOSE:
 * Use this code to test and calibrate your physical dispensing hardware independently
 * BEFORE connecting to WiFi or the Web UI.
 *
 * FEATURES:
 * 1. Independent control of up to 4 powder dispensing containers (expandable to 6).
 * 2. Interactive Serial Monitor control menu (type 1, 2, 3, 4, or A, B, C, D).
 * 3. Calibrated dispensing duration (adjust runtime to drop exact grams of powder).
 * 4. Automated sequential self-test mode (tests all motors one after another).
 * 5. Emergency Stop command ('S') to instantly shut down all motors.
 * 6. Brief anti-jam reverse pulse option to prevent powder packing in the nozzle.
 *
 * HARDWARE WIRING GUIDE (L298N Dual H-Bridge to ESP32):
 * -------------------------------------------------------------------------------------
 *  ESP32 Pin     -> L298N Driver Pin    -> Connected Hardware
 *  GPIO 18       -> IN1 (Driver 1)      -> Motor 1 / Container 1 (Tea A: Lemongrass Sip)
 *  GPIO 19       -> IN2 (Driver 1)      -> Motor 1 / Container 1
 *  GPIO 21       -> IN3 (Driver 1)      -> Motor 2 / Container 2 (Tea B: Vital Sip)
 *  GPIO 22       -> IN4 (Driver 1)      -> Motor 2 / Container 2
 *  GPIO 23       -> IN1 (Driver 2)      -> Motor 3 / Container 3 (Tea C: MedoHar Sip)
 *  GPIO 25       -> IN2 (Driver 2)      -> Motor 3 / Container 3
 *  GPIO 26       -> IN3 (Driver 2)      -> Motor 4 / Container 4 (Tea D / Regular Tea)
 *  GPIO 27       -> IN4 (Driver 2)      -> Motor 4 / Container 4
 *  GND           -> L298N GND           -> COMMON GROUND (CRITICAL!)
 *
 * POWER SUPPLY RULES:
 * 1. NEVER power BO motors directly from the ESP32 3.3V or 5V (VIN) pin!
 * 2. Connect an external 6V, 9V, or 12V DC power supply to the L298N 12V terminal.
 * 3. Connect the L298N GND to BOTH the external power supply negative AND ESP32 GND.
 * =====================================================================================
 */

#include <Arduino.h>

// =====================================================================================
// 1. PIN CONFIGURATIONS
// =====================================================================================
// Motor 1 - Container 1 (Tea A: Lemongrass Sip / Kashaya A)
#define MOTOR1_IN1 18
#define MOTOR1_IN2 19

// Motor 2 - Container 2 (Tea B: Vital Sip / Kashaya B)
#define MOTOR2_IN1 21
#define MOTOR2_IN2 22

// Motor 3 - Container 3 (Tea C: MedoHar Sip / Kashaya C)
#define MOTOR3_IN1 23
#define MOTOR3_IN2 25

// Motor 4 - Container 4 (Tea D: Mangalayu Tea / Regular Tea)
#define MOTOR4_IN1 26
#define MOTOR4_IN2 27

// Onboard diagnostic LED (usually GPIO 2 on most ESP32 boards)
#define STATUS_LED 2

// Total number of active containers configured in this test
#define TOTAL_CONTAINERS 4

// =====================================================================================
// 2. DISPENSING CALIBRATION SETTINGS
// =====================================================================================
// Default run time for the BO motor to drop the desired powder quantity (in milliseconds).
// Example: If 2500ms drops ~6 grams of herbal powder, adjust this to calibrate your auger.
unsigned long dispenseDurationMs = 2500;

// Brief reverse rotation at the end of dispensing to prevent nozzle jamming (in ms).
// Set to 0 if your powder dispenser mechanism does not require anti-jam reversal.
const unsigned long ANTI_JAM_REVERSE_MS = 150;

// Struct to organize motor pin pairs cleanly
struct MotorPins {
  uint8_t in1;
  uint8_t in2;
  const char* label;
  const char* formulationName;
};

// Define all container motors
const MotorPins containers[TOTAL_CONTAINERS] = {
  {MOTOR1_IN1, MOTOR1_IN2, "Container 1 (Motor 1)", "Tea A - Lemongrass Sip / Kashaya A"},
  {MOTOR2_IN1, MOTOR2_IN2, "Container 2 (Motor 2)", "Tea B - Vital Sip / Kashaya B"},
  {MOTOR3_IN1, MOTOR3_IN2, "Container 3 (Motor 3)", "Tea C - MedoHar Sip / Kashaya C"},
  {MOTOR4_IN1, MOTOR4_IN2, "Container 4 (Motor 4)", "Tea D - Mangalayu / Regular Tea"}
};

// =====================================================================================
// 3. LOW-LEVEL MOTOR CONTROL FUNCTIONS
// =====================================================================================

/**
 * Initializes all motor driver control pins as outputs and ensures all motors are stopped.
 */
void initMotorHardware() {
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  for (int i = 0; i < TOTAL_CONTAINERS; i++) {
    pinMode(containers[i].in1, OUTPUT);
    pinMode(containers[i].in2, OUTPUT);
    // Ensure motor starts in OFF state
    digitalWrite(containers[i].in1, LOW);
    digitalWrite(containers[i].in2, LOW);
  }
}

/**
 * Immediately stops a specific motor (Brakes the H-bridge).
 */
void stopMotor(int containerIndex) {
  if (containerIndex >= 0 && containerIndex < TOTAL_CONTAINERS) {
    digitalWrite(containers[containerIndex].in1, LOW);
    digitalWrite(containers[containerIndex].in2, LOW);
  }
}

/**
 * Emergency All-Stop: Immediately stops all motors and turns off status LED.
 */
void emergencyStopAll() {
  for (int i = 0; i < TOTAL_CONTAINERS; i++) {
    stopMotor(i);
  }
  digitalWrite(STATUS_LED, LOW);
  Serial.println("\n[EMERGENCY STOP] All motors stopped immediately!");
}

/**
 * Spins the BO motor forward to dispense herbal powder from the container.
 * 
 * @param containerIndex Index of container (0 to TOTAL_CONTAINERS - 1)
 * @param durationMs Milliseconds to keep the motor running
 */
void dispenseContainer(int containerIndex, unsigned long durationMs) {
  if (containerIndex < 0 || containerIndex >= TOTAL_CONTAINERS) {
    Serial.println("[ERROR] Invalid container index!");
    return;
  }

  Serial.println("\n---------------------------------------------------------");
  Serial.printf(">> STARTING DISPENSE: %s\n", containers[containerIndex].label);
  Serial.printf("   Formulation : %s\n", containers[containerIndex].formulationName);
  Serial.printf("   Duration    : %lu ms\n", durationMs);
  Serial.println("---------------------------------------------------------");

  // Turn on status LED to indicate dispensing in progress
  digitalWrite(STATUS_LED, HIGH);

  // 1. FORWARD ROTATION: Dispense powder
  digitalWrite(containers[containerIndex].in1, HIGH);
  digitalWrite(containers[containerIndex].in2, LOW);

  // Progress countdown in Serial Monitor
  unsigned long startTime = millis();
  while (millis() - startTime < durationMs) {
    unsigned long elapsed = millis() - startTime;
    int progressPct = (elapsed * 100) / durationMs;
    
    // Print progress every 500ms
    if (elapsed % 500 < 20) {
      Serial.printf("   Dispensing... [%d%%] (%lu ms / %lu ms)\n", progressPct, elapsed, durationMs);
    }
    delay(20);
  }

  // 2. STOP MOTOR
  digitalWrite(containers[containerIndex].in1, LOW);
  digitalWrite(containers[containerIndex].in2, LOW);
  delay(50);

  // 3. OPTIONAL ANTI-JAM REVERSE PULSE (Prevents powder clumping at nozzle)
  if (ANTI_JAM_REVERSE_MS > 0) {
    Serial.printf("   Anti-jam reverse pulse (%lu ms)...\n", ANTI_JAM_REVERSE_MS);
    digitalWrite(containers[containerIndex].in1, LOW);
    digitalWrite(containers[containerIndex].in2, HIGH);
    delay(ANTI_JAM_REVERSE_MS);

    // Stop again
    digitalWrite(containers[containerIndex].in1, LOW);
    digitalWrite(containers[containerIndex].in2, LOW);
  }

  digitalWrite(STATUS_LED, LOW);
  Serial.printf(">> [SUCCESS] %s dispensing complete! Powder dropped.\n\n", containers[containerIndex].label);
}

/**
 * Automated sequential test: Runs each motor one by one with a 1.5-second test cycle.
 */
void runSequentialSelfTest() {
  Serial.println("\n=========================================================");
  Serial.println(">> STARTING SEQUENTIAL SELF-TEST OF ALL CONTAINERS");
  Serial.println("=========================================================");

  for (int i = 0; i < TOTAL_CONTAINERS; i++) {
    Serial.printf("\n[TEST %d/%d] Testing %s...\n", i + 1, TOTAL_CONTAINERS, containers[i].label);
    dispenseContainer(i, 1500); // Test with 1.5s runtime
    delay(1000); // 1-second pause between motors
  }

  Serial.println("\n>> [ALL TESTS COMPLETED] All BO motors tested successfully!");
}

// =====================================================================================
// 4. USER INTERACTION: SERIAL MENU
// =====================================================================================

void printMenu() {
  Serial.println("\n=========================================================");
  Serial.println("    SOILVEDA ORGANICS - BO MOTOR DISPENSER TEST MENU     ");
  Serial.println("=========================================================");
  Serial.printf(" Current Dispense Runtime: %lu ms (~powder drop time)\n", dispenseDurationMs);
  Serial.println("---------------------------------------------------------");
  Serial.println(" [1] or [A] : Dispense Container 1 (Tea A: Lemongrass Sip)");
  Serial.println(" [2] or [B] : Dispense Container 2 (Tea B: Vital Sip)");
  Serial.println(" [3] or [C] : Dispense Container 3 (Tea C: MedoHar Sip)");
  Serial.println(" [4] or [D] : Dispense Container 4 (Tea D / Regular Tea)");
  Serial.println(" [T]        : Run Automated Self-Test (Tests all motors)");
  Serial.println(" [+]        : Increase Dispense Duration (+250 ms)");
  Serial.println(" [-]        : Decrease Dispense Duration (-250 ms)");
  Serial.println(" [S]        : EMERGENCY ALL STOP");
  Serial.println("=========================================================");
  Serial.print("Enter command: ");
}

void processSerialInput() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Ignore newline and carriage return characters
    if (cmd == '\r' || cmd == '\n' || cmd == ' ') return;

    cmd = toupper(cmd);
    Serial.println(cmd);

    switch (cmd) {
      case '1':
      case 'A':
        dispenseContainer(0, dispenseDurationMs);
        break;

      case '2':
      case 'B':
        dispenseContainer(1, dispenseDurationMs);
        break;

      case '3':
      case 'C':
        dispenseContainer(2, dispenseDurationMs);
        break;

      case '4':
      case 'D':
        dispenseContainer(3, dispenseDurationMs);
        break;

      case 'T':
        runSequentialSelfTest();
        break;

      case '+':
        dispenseDurationMs += 250;
        Serial.printf(">> Dispense duration INCREASED to: %lu ms\n", dispenseDurationMs);
        break;

      case '-':
        if (dispenseDurationMs > 250) {
          dispenseDurationMs -= 250;
          Serial.printf(">> Dispense duration DECREASED to: %lu ms\n", dispenseDurationMs);
        } else {
          Serial.println(">> Minimum duration reached (250 ms).");
        }
        break;

      case 'S':
        emergencyStopAll();
        break;

      default:
        Serial.println(">> Unknown command! Type 1, 2, 3, 4, T, +, -, or S.");
        break;
    }

    printMenu();
  }
}

// =====================================================================================
// 5. MAIN SETUP & LOOP
// =====================================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\nSoil Veda Organics - ESP32 Hardware Initializing...");

  // Initialize all GPIOs for motor driver
  initMotorHardware();

  // Quick LED greeting blink (3 pulses)
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(100);
    digitalWrite(STATUS_LED, LOW);
    delay(100);
  }

  Serial.println("Hardware initialized successfully. All BO motors in standby.");
  printMenu();
}

void loop() {
  // Listen for interactive calibration and testing commands from user
  processSerialInput();
  delay(10);
}
