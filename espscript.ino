#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <ArduinoJson.h>
#include <FS.h>
#include <LittleFS.h>
#include <TimeLib.h>  // Include Time library for timestamp

// WiFi parameters
const char* ssid = "TP-Link_FA02"; // Replace with your WiFi SSID
const char* password = "90428562"; // Replace with your WiFi password

// Discord webhook URL
const char* discordWebhookUrl = "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ";

// API endpoint and authorization token
const char* apiUrl = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10";
const char* authorizationToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU";

WiFiClientSecure wifiClient;
bool leaderboardInitialized = false;
DynamicJsonDocument previousLeaderboard(4096);

void setup(void) {
  Serial.begin(9600);

  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("An error has occurred while mounting LittleFS");
    return;
  }
  Serial.println("LittleFS mounted successfully");

  // Connect to WiFi
  WiFi.begin(ssid, password);

  // while wifi not connected yet, print '.'
  // then after it connected, get out of the loop
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // print a new line, then print WiFi connected and the IP address
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println(WiFi.localIP());

  // Save leaderboard on startup if not already initialized
  if (!leaderboardInitialized) {
    saveLeaderboard(); // Function to request and save leaderboard
    leaderboardInitialized = true;
  }
}

void loop() {
  // Request leaderboard again and calculate differences
  saveLeaderboard();
  calculateDifferences();

  // Delay for a variable time (30 seconds for example) before next loop
  delay(30000);
}

void saveLeaderboard() {
  HTTPClient http;
  wifiClient.setInsecure(); // Use this only for testing, for production use a proper SSL certificate
  http.begin(wifiClient, apiUrl);  // Specify the URL and WiFiClientSecure
  http.addHeader("Authorization", authorizationToken);  // Add the authorization header
  http.addHeader("Content-Type", "application/json");  // Specify content-type header

  int httpResponseCode = http.GET();

  if (httpResponseCode > 0) {
    String response = http.getString();  // Get the response to the request
    Serial.println(httpResponseCode);  // Print return code
    Serial.println(response);  // Print request answer (if any)

    // Save JSON response to file
    File file = LittleFS.open("/leaderboard.json", "w");
    if (!file) {
      Serial.println("Failed to open file for writing");
      return;
    }
    file.print(response);
    file.close();
    Serial.println("Leaderboard data saved to /leaderboard.json");

    // Store the current leaderboard in previousLeaderboard
    deserializeJson(previousLeaderboard, response);
  } else {
    Serial.print("Error on sending GET to API: ");
    Serial.println(httpResponseCode);
  }

  http.end();  // Free resources
}

void calculateDifferences() {
  // Read current leaderboard from /leaderboard.json
  File file = LittleFS.open("/leaderboard.json", "r");
  if (!file) {
    Serial.println("Failed to open /leaderboard.json for reading");
    return;
  }

  String jsonData = file.readString();
  file.close();

  DynamicJsonDocument currentLeaderboard(4096);
  DeserializationError error = deserializeJson(currentLeaderboard, jsonData);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Prepare embed fields
  String usernameValues = "";
  String countValues = "";
  String increaseValues = "";

  // Get current and previous topUsers arrays
  JsonArray currentUsers = currentLeaderboard["topUsers"].as<JsonArray>();
  JsonArray previousUsers = previousLeaderboard["topUsers"].as<JsonArray>();

  // Iterate through current leaderboard
  for (size_t i = 0; i < currentUsers.size(); ++i) {
    const char* currentId = currentUsers[i]["id"].as<const char*>();
    int currentCount = currentUsers[i]["count"].as<int>();

    // Find the corresponding user in the previous leaderboard
    int previousCount = 0;
    bool found = false;
    for (size_t j = 0; j < previousUsers.size(); ++j) {
      if (strcmp(previousUsers[j]["id"].as<const char*>(), currentId) == 0) {
        previousCount = previousUsers[j]["count"].as<int>();
        found = true;
        break;
      }
    }

    // Calculate difference
    int diff = currentCount - previousCount;

    // Format increase as "+N" or "N"
    String increase;
    if (diff >= 0) {
      increase = "+" + String(diff);
    } else {
      increase = String(diff);
    }

    // Prepare values for embed fields
    const char* username = currentUsers[i]["username"].as<const char*>();
    usernameValues += String(username) + "\n";
    countValues += String(currentCount) + "\n";
    increaseValues += increase + "\n";
  }

  Serial.println("Constructed message:");
  Serial.println(usernameValues);
  Serial.println(countValues);
  Serial.println(increaseValues);

  // Prepare JSON payload for Discord embed
  DynamicJsonDocument jsonPayload(2048);
  JsonArray embeds = jsonPayload.createNestedArray("embeds");
  JsonObject embed = embeds.createNestedObject();
  embed["title"] = "Top 10 Pop-A-Loon Suspects.";
  embed["color"] = 16711680;

  JsonArray fields = embed.createNestedArray("fields");

  JsonObject usernameField = fields.createNestedObject();
  usernameField["name"] = "Username";
  usernameField["value"] = usernameValues;
  usernameField["inline"] = true;

  JsonObject countField = fields.createNestedObject();
  countField["name"] = "Count";
  countField["value"] = countValues;
  countField["inline"] = true;

  JsonObject increaseField = fields.createNestedObject();
  increaseField["name"] = "Increase";
  increaseField["value"] = increaseValues;
  increaseField["inline"] = true;

  // Timestamp formatted as hh:mm:ss
  char timestamp[9];
  sprintf(timestamp, "%02d:%02d:%02d", hour(), minute(), second());

  JsonObject footer = embed.createNestedObject("footer");
  footer["text"] = "Pops since the last check (" + String(timestamp) + " ago).";
  footer["icon_url"] = "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png";

  // Serialize JSON payload to string
  String payload;
  serializeJson(jsonPayload, payload);

  // Send HTTP POST request to Discord webhook
  HTTPClient discordHttp;
  discordHttp.begin(wifiClient, discordWebhookUrl);
  discordHttp.addHeader("Content-Type", "application/json");

  int discordResponseCode = discordHttp.POST(payload);

  if (discordResponseCode > 0) {
    String discordResponse = discordHttp.getString();
    Serial.println(discordResponseCode);
    Serial.println(discordResponse);
  } else {
    Serial.print("Error on sending POST to Discord: ");
    Serial.println(discordResponseCode);
  }

  discordHttp.end();
}
