/*
 * =====================================================================================
 * SOILVEDA ORGANICS - AYURVEDIC VENDING MACHINE
 * MODULE: 2. WEB-LINKED ESP32 DISPENSER (UI INTEGRATION)
 * =====================================================================================
 * Target Board: ESP32 Dev Module (WROOM / NodeMCU-32S / ESP32 30-pin & 38-pin)
 * Motor Driver: L298N / L293D / TB6612FNG or Relay Module
 * Actuators:    BO Gear Motors attached to Powder Canisters/Augers
 *
 * HOW IT CONNECTS TO THE WEB UI:
 * 1. The user takes the assessment or selects Regular Tea on your website:
 *    (e.g., https://vending-machine-eosin-five.vercel.app or local http://192.168.x.x:5000)
 * 2. When the user clicks "Dispense Beverage", the website pushes a dispense job
 *    to the backend API (/api/dispense) with the prescribed tea formulation and container ID.
 * 3. This ESP32 is connected to WiFi and continuously polls the queue (/api/dispense/poll).
 * 4. As soon as the ESP32 detects the job:
 *    - It identifies the assigned container (e.g., Container 1 for Tea A, Container 2 for Tea B).
 *    - It triggers the corresponding BO motor to rotate and drop the calibrated powder quantity.
 *    - It sends a completion confirmation back to the backend (/api/dispense/complete).
 *
 * BONUS DUAL-MODE FEATURE:
 * This sketch also runs a local HTTP Web Server on the ESP32 itself (port 80).
 * If your tablet/phone is on the same local WiFi, you can also trigger it directly:
 * http://<ESP32_IP>/dispense?container=1
 * =====================================================================================
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <WiFiClientSecure.h>

// =====================================================================================
// 1. WIFI & SERVER CONFIGURATION (ENTER YOUR CREDENTIALS HERE)
// =====================================================================================
// Replace with your WiFi Network Name and Password
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Backend API Base URL
// For live Vercel deployment:
const char* SERVER_BASE_URL = "https://vending-machine-eosin-five.vercel.app";

// For local testing on the same laptop / WiFi (uncomment and replace with your laptop's IP):
// const char* SERVER_BASE_URL = "http://192.168.1.100:5000";

// Polling interval in milliseconds (how often ESP32 checks for new orders)
const unsigned long POLL_INTERVAL_MS = 1000;

// Default powder drop runtime in ms (if not specified by server)
const unsigned long DEFAULT_DISPENSE_DURATION_MS = 2500;

// Optional reverse pulse at end of dispensing to prevent nozzle jamming
const unsigned long ANTI_JAM_REVERSE_MS = 150;

// =====================================================================================
// 2. HARDWARE PIN DEFINITIONS
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

// Onboard diagnostic LED
#define STATUS_LED 2

#define TOTAL_CONTAINERS 4

struct MotorPins {
  uint8_t in1;
  uint8_t in2;
  const char* label;
  const char* defaultTea;
};

const MotorPins containers[TOTAL_CONTAINERS] = {
  {MOTOR1_IN1, MOTOR1_IN2, "Container 1 (Motor 1)", "Tea A (Lemongrass Sip)"},
  {MOTOR2_IN1, MOTOR2_IN2, "Container 2 (Motor 2)", "Tea B (Vital Sip)"},
  {MOTOR3_IN1, MOTOR3_IN2, "Container 3 (Motor 3)", "Tea C (MedoHar Sip)"},
  {MOTOR4_IN1, MOTOR4_IN2, "Container 4 (Motor 4)", "Tea D / Regular Tea"}
};

// Local HTTP Server on Port 80 for direct LAN commands
WebServer localServer(80);

// Tracking timers and state
unsigned long lastPollTime = 0;
bool isDispensingNow = false;

// =====================================================================================
// 3. HARDWARE CONTROL FUNCTIONS
// =====================================================================================

void initHardware() {
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  for (int i = 0; i < TOTAL_CONTAINERS; i++) {
    pinMode(containers[i].in1, OUTPUT);
    pinMode(containers[i].in2, OUTPUT);
    digitalWrite(containers[i].in1, LOW);
    digitalWrite(containers[i].in2, LOW);
  }
}

void stopMotor(int containerIndex) {
  if (containerIndex >= 0 && containerIndex < TOTAL_CONTAINERS) {
    digitalWrite(containers[containerIndex].in1, LOW);
    digitalWrite(containers[containerIndex].in2, LOW);
  }
}

void emergencyStop() {
  for (int i = 0; i < TOTAL_CONTAINERS; i++) {
    stopMotor(i);
  }
  digitalWrite(STATUS_LED, LOW);
  isDispensingNow = false;
  Serial.println("[EMERGENCY STOP] All motors stopped!");
}

/**
 * Executes dispensing on the assigned container motor.
 */
void runDispense(int containerId, unsigned long durationMs, const String& drinkName) {
  int idx = containerId - 1; // Convert 1-based containerId to 0-based array index
  if (idx < 0 || idx >= TOTAL_CONTAINERS) {
    Serial.printf("[ERROR] Requested container ID %d is out of range (1 to %d)!\n", containerId, TOTAL_CONTAINERS);
    return;
  }

  isDispensingNow = true;
  digitalWrite(STATUS_LED, HIGH);

  Serial.println("\n=======================================================");
  Serial.printf(">> DISPENSING ORDER RECEIVED FROM WEB UI!\n");
  Serial.printf("   Drink Name   : %s\n", drinkName.c_str());
  Serial.printf("   Target Motor : %s\n", containers[idx].label);
  Serial.printf("   Duration     : %lu ms\n", durationMs);
  Serial.println("=======================================================");

  // 1. FORWARD RUN: Rotate auger / motor to drop powder
  digitalWrite(containers[idx].in1, HIGH);
  digitalWrite(containers[idx].in2, LOW);

  unsigned long start = millis();
  while (millis() - start < durationMs) {
    // Keep local server responsive even while dispensing
    localServer.handleClient();
    delay(10);
  }

  // 2. STOP MOTOR
  digitalWrite(containers[idx].in1, LOW);
  digitalWrite(containers[idx].in2, LOW);
  delay(50);

  // 3. OPTIONAL ANTI-JAM REVERSE PULSE
  if (ANTI_JAM_REVERSE_MS > 0) {
    digitalWrite(containers[idx].in1, LOW);
    digitalWrite(containers[idx].in2, HIGH);
    delay(ANTI_JAM_REVERSE_MS);
    digitalWrite(containers[idx].in1, LOW);
    digitalWrite(containers[idx].in2, LOW);
  }

  digitalWrite(STATUS_LED, LOW);
  isDispensingNow = false;

  Serial.printf(">> [COMPLETE] %s finished dispensing %s. Powder successfully dropped!\n\n",
                containers[idx].label, drinkName.c_str());
}

// =====================================================================================
// 4. LIGHTWEIGHT JSON PARSER (ZERO EXTERNAL LIBRARIES REQUIRED)
// =====================================================================================
// Extracts simple values from JSON strings safely without adding heavy dependencies.
String extractJsonValue(const String& json, const String& key) {
  String searchKey = "\"" + key + "\":";
  int keyPos = json.indexOf(searchKey);
  if (keyPos == -1) {
    // Try without quotes around key
    searchKey = key + ":";
    keyPos = json.indexOf(searchKey);
    if (keyPos == -1) return "";
  }

  int valStart = keyPos + searchKey.length();
  while (valStart < json.length() && (json[valStart] == ' ' || json[valStart] == '\"')) {
    valStart++;
  }

  char endChar = ',';
  if (json[keyPos + searchKey.length()] == ' ' && json[valStart - 1] == '\"') {
    endChar = '\"';
  } else if (json[valStart] == '\"') {
    valStart++;
    endChar = '\"';
  }

  int valEnd = json.indexOf(endChar, valStart);
  if (valEnd == -1) {
    valEnd = json.indexOf('}', valStart);
  }
  if (valEnd == -1) return "";

  String val = json.substring(valStart, valEnd);
  val.trim();
  val.replace("\"", "");
  return val;
}

// =====================================================================================
// 5. CLOUD QUEUE POLLING & ACKNOWLEDGMENT
// =====================================================================================

void notifyJobComplete(int jobId) {
  if (WiFi.status() != WL_CONNECTED || jobId <= 0) return;

  WiFiClientSecure client;
  client.setInsecure(); // Skip certificate verification for simple fast webhook

  HTTPClient http;
  String completeUrl = String(SERVER_BASE_URL) + "/api/dispense/complete";

  if (http.begin(client, completeUrl)) {
    http.addHeader("Content-Type", "application/json");
    String payload = "{\"job_id\":" + String(jobId) + "}";
    int httpCode = http.POST(payload);
    if (httpCode == 200) {
      Serial.printf(">> [ACK SENT] Server acknowledged completion of Job #%d.\n", jobId);
    }
    http.end();
  }
}

void pollDispenseQueue() {
  if (WiFi.status() != WL_CONNECTED || isDispensingNow) return;

  WiFiClientSecure client;
  client.setInsecure(); // Fast SSL handshake for cloud HTTPS

  HTTPClient http;
  String pollUrl = String(SERVER_BASE_URL) + "/api/dispense/poll";

  if (http.begin(client, pollUrl)) {
    int httpCode = http.GET();

    if (httpCode == 200) {
      String response = http.getString();
      
      // Check if server reports a pending job
      if (response.indexOf("\"has_job\":true") != -1 || response.indexOf("\"has_job\": true") != -1) {
        Serial.println("\n[POLL] New Dispense Job Detected!");
        Serial.println("Server Response: " + response);

        int jobId = extractJsonValue(response, "job_id").toInt();
        int containerId = extractJsonValue(response, "container_id").toInt();
        unsigned long duration = extractJsonValue(response, "duration_ms").toInt();
        String drinkName = extractJsonValue(response, "drink_name");

        if (containerId <= 0) containerId = 1;
        if (duration <= 0) duration = DEFAULT_DISPENSE_DURATION_MS;
        if (drinkName.length() == 0) drinkName = "Ayurvedic Tea";

        // Trigger physical BO motor dispensing!
        runDispense(containerId, duration, drinkName);

        // Inform backend that dispensing is finished
        notifyJobComplete(jobId);
      }
    } else {
      // Optional: Serial.printf("[POLL] HTTP %d\n", httpCode);
    }
    http.end();
  }
}

// =====================================================================================
// 6. LOCAL WEB SERVER (DIRECT REST API ON ESP32)
// =====================================================================================

void handleLocalRoot() {
  String html = "<!DOCTYPE html><html><head><title>SoilVeda Dispenser</title>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<style>body{font-family:sans-serif;text-align:center;padding:20px;background:#f5fbf7;}";
  html += ".btn{display:block;width:80%;max-width:300px;margin:12px auto;padding:15px;background:#1b4332;color:#fff;text-decoration:none;font-weight:bold;border-radius:8px;}";
  html += "</style></head><body>";
  html += "<h2>Soil Veda Dispenser Node</h2>";
  html += "<p>Connected to: " + WiFi.SSID() + "</p>";
  html += "<p>IP Address: " + WiFi.localIP().toString() + "</p>";
  html += "<hr>";
  html += "<a class='btn' href='/dispense?container=1'>Dispense Container 1 (Tea A)</a>";
  html += "<a class='btn' href='/dispense?container=2'>Dispense Container 2 (Tea B)</a>";
  html += "<a class='btn' href='/dispense?container=3'>Dispense Container 3 (Tea C)</a>";
  html += "<a class='btn' href='/dispense?container=4'>Dispense Container 4 (Tea D)</a>";
  html += "<a class='btn' style='background:#b91c1c;' href='/stop'>Emergency Stop</a>";
  html += "</body></html>";
  localServer.send(200, "text/html", html);
}

void handleLocalDispense() {
  if (!localServer.hasArg("container")) {
    localServer.send(400, "text/plain", "Missing container parameter (e.g. /dispense?container=1)");
    return;
  }

  int containerId = localServer.arg("container").toInt();
  unsigned long duration = DEFAULT_DISPENSE_DURATION_MS;
  if (localServer.hasArg("duration")) {
    duration = localServer.arg("duration").toInt();
  }

  String drinkName = localServer.hasArg("drink") ? localServer.arg("drink") : "Direct Dispense";

  localServer.send(200, "application/json", "{\"status\":\"dispensing\",\"container\":" + String(containerId) + "}");
  runDispense(containerId, duration, drinkName);
}

void handleLocalStop() {
  emergencyStop();
  localServer.send(200, "text/plain", "Emergency stop executed.");
}

void setupLocalServer() {
  localServer.on("/", handleLocalRoot);
  localServer.on("/dispense", handleLocalDispense);
  localServer.on("/stop", handleLocalStop);
  localServer.begin();
  Serial.println("[LOCAL SERVER] HTTP Server running on port 80.");
}

// =====================================================================================
// 7. MAIN SETUP & LOOP
// =====================================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n=======================================================");
  Serial.println(" Soil Veda Organics - Web-Linked Dispenser Initializing ");
  Serial.println("=======================================================");

  initHardware();

  // Connect to WiFi
  Serial.printf("Connecting to WiFi: %s ", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED)); // Toggle LED while connecting
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(STATUS_LED, HIGH);
    Serial.println("\n>> WiFi Connected Successfully!");
    Serial.print(">> ESP32 IP Address : ");
    Serial.println(WiFi.localIP());
    Serial.print(">> Linked Server URL: ");
    Serial.println(SERVER_BASE_URL);
  } else {
    Serial.println("\n[WARNING] WiFi Connection failed! Verify credentials.");
    Serial.println("ESP32 will retry connecting in background while local server runs.");
  }

  setupLocalServer();

  Serial.println("\n>> Ready! Waiting for orders from Soil Veda Web UI...");
  Serial.println("=======================================================\n");
}

void loop() {
  // 1. Handle incoming direct local HTTP requests
  localServer.handleClient();

  // 2. Poll Cloud Server Queue every POLL_INTERVAL_MS
  if (millis() - lastPollTime >= POLL_INTERVAL_MS) {
    lastPollTime = millis();
    pollDispenseQueue();
  }

  delay(10);
}

