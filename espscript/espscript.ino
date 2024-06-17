#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <ArduinoJson.h>
#include <FS.h>
#include <LittleFS.h>
#include <TimeLib.h>
#include <Wire.h>  // Include the Wire library for I2C
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// WiFi credentials
const char* ssid = "JOWIE";
const char* password = "HTTPSNOT";

// API URLs and auth token
const char* discordWebhookUrl = "https://discord.com/api/webhooks/1252179418286129152/0iKelpM-qzIEGUw6oBu9DsAeyMLfqbz9GuLwaCXkpiW5wMlF46BNZD7vmVifDQA55J2_";
const char* apiUrl = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10";
const char* authorizationToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU";

// Secure client for HTTPS connections
WiFiClientSecure wifiClient;

// Dynamic JSON document to save the base leaderboard
DynamicJsonDocument baseLeaderboard(4096);

// OLED display object
#define SSD1306_NO_SPLASH
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1  // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Custom I2C pins
#define SDA_PIN 14  // GPIO 12 (D5)
#define SCL_PIN 12  // GPIO 14 (D6)

unsigned long lastCheckTime = 0; // Store the last check time in milliseconds
unsigned long delayDuration = 1800000; // Delay or time in between checks in milliseconds (30 minutes)
unsigned long lastDisplayUpdate = 0; // Last time the display was updated
unsigned long lastSpecificUserCheck = 0; // Last time the specific user was checked
unsigned long specificUserDelay = 60000; // Delay or time in between specific user checks in milliseconds (60 seconds)



String wifiStatus = "Connecting to WiFi...";
String messageStatus = "";

void setup(void) {
    Serial.begin(9600);

    if (!LittleFS.begin()) {
        Serial.println("An error has occurred while mounting LittleFS");
        return;
    }
    Serial.println("LittleFS mounted successfully");

    // Initialize I2C communication with custom pins
    Wire.begin(SDA_PIN, SCL_PIN);  // Set custom SDA and SCL pins

    // Initialize OLED display
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3C for 128x64
        Serial.println(F("SSD1306 allocation failed"));
        for(;;); // Don't proceed, loop forever
    }
    display.display();
    delay(2000); // Pause for 2 seconds

    display.clearDisplay();
    display.setTextSize(1);      // Normal 1:1 pixel scale
    display.setTextColor(SSD1306_WHITE); // Draw white text
    display.setCursor(0, 0);     // Start at top-left corner
    display.print(F("."));
    display.display();

    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi network");

    updateDisplay();
    while (WiFi.status() != WL_CONNECTED) {
        delay(3000);
        Serial.print(".");
        updateDisplay();
    }

    Serial.println("");
    Serial.println("Connected to WiFi network ");
    Serial.print(ssid);
    Serial.println(WiFi.localIP());

    wifiStatus = "Connected to " + String(ssid);
    updateDisplay();

    loadBaseLeaderboard();
}

void loop() {
    unsigned long currentMillis = millis();

    // Check if it's time to save the current leaderboard and calculate differences
    if (currentMillis - lastCheckTime >= delayDuration) {
        saveCurrentLeaderboard();
        calculateDifferences();
        lastCheckTime = currentMillis;
    }

    // Check if it's time to fetch and display the specific user's score
    if (currentMillis - lastSpecificUserCheck >= specificUserDelay) {
        fetchAndDisplaySpecificUser();
        lastSpecificUserCheck = currentMillis;
    }

    // Update the countdown timer display
    updateCountdown();

    delay(1000); // Small delay to avoid rapid looping
}

void updateCountdown() {
    unsigned long currentMillis = millis();
    unsigned long timeUntilNextCheck = delayDuration - (currentMillis - lastCheckTime);

    // Convert time to minutes and seconds
    int minutes = timeUntilNextCheck / 60000;
    int seconds = (timeUntilNextCheck % 60000) / 1000;

    // Clear the area where the countdown timer is displayed
    display.fillRect(0, 56, SCREEN_WIDTH, 8, SSD1306_BLACK);

    // Update the display with the countdown timer
    display.setCursor(0, 56);
    display.print("Next check in: ");
    display.print(minutes);
    display.print("m ");
    display.print(seconds);
    display.print("s");
    display.display();
}


void updateDisplay() {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.print(F("Pop-a-Loon tracker"));

    display.setCursor(0, 8);
    display.print(wifiStatus);

    display.display();
}

void loadBaseLeaderboard() {
    File file = LittleFS.open("/base_leaderboard.json", "r");
    if (!file) {
        Serial.println("No base leaderboard found, initializing.");
        baseLeaderboard.clear();
        saveCurrentLeaderboardAsBase(); // Fetch and save the initial leaderboard as base
        return;
    }

    String jsonData = file.readString();
    file.close();

    DeserializationError error = deserializeJson(baseLeaderboard, jsonData);
    if (error) {
        Serial.print("Failed to parse base leaderboard: ");
        Serial.println(error.c_str());
        baseLeaderboard.clear();
        saveCurrentLeaderboardAsBase(); // Fetch and save the initial leaderboard as base
    } else {
        Serial.println("Base leaderboard loaded.");
    }
}

void saveCurrentLeaderboardAsBase() {
    HTTPClient http;
    wifiClient.setInsecure();
    http.begin(wifiClient, apiUrl);
    http.addHeader("Authorization", authorizationToken);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.GET(); // 200 = OK, 204 = no content

    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println(httpResponseCode);
        Serial.println("Response received. ");

        File file = LittleFS.open("/base_leaderboard.json", "w");
        if (!file) {
            Serial.println("Failed to open file for writing");
            return;
        }
        file.print(response);
        file.close();
        Serial.println("Initial leaderboard data saved to /base_leaderboard.json");
    } else {
        Serial.print("Error on sending GET to API: ");
        Serial.println(httpResponseCode);
    }

    http.end();
}

void saveCurrentLeaderboard() {
    HTTPClient http;
    wifiClient.setInsecure();
    http.begin(wifiClient, apiUrl);
    http.addHeader("Authorization", authorizationToken);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println(httpResponseCode);
        Serial.println(response);

        File file = LittleFS.open("/current_leaderboard.json", "w");
        if (!file) {
            Serial.println("Failed to open file for writing");
            return;
        }
        file.print(response);
        file.close();
        Serial.println("Leaderboard data saved to /current_leaderboard.json");

        // Save the current time of saving
        lastCheckTime = millis();
        File timeFile = LittleFS.open("/last_check_time.txt", "w");
        if (!timeFile) {
            Serial.println("Failed to open file for writing");
            return;
        }
        timeFile.print(lastCheckTime);
        timeFile.close();
        Serial.println("Last check time saved.");
    } else {
        Serial.print("Error on sending GET to API: ");
        Serial.println(httpResponseCode);
    }

    http.end();
}

void calculateDifferences() {
    File currentFile = LittleFS.open("/current_leaderboard.json", "r");
    if (!currentFile) {
        Serial.println("Failed to open /current_leaderboard.json for reading");
        return;
    }

    String currentJsonData = currentFile.readString();
    currentFile.close();

    DynamicJsonDocument currentLeaderboard(4096);
    DeserializationError error = deserializeJson(currentLeaderboard, currentJsonData);
    if (error) {
        Serial.print("deserializeJson() failed: ");
        Serial.println(error.c_str());
        return;
    }

    // Ensure baseLeaderboard is valid before proceeding
    if (baseLeaderboard.isNull() || baseLeaderboard["topUsers"].isNull()) {
        Serial.println("Base leaderboard is not initialized, skipping difference calculation.");
        return;
    }

    String usernameValues = "";
    String countValues = "";
    String increaseValues = "";

    JsonArray currentUsers = currentLeaderboard["topUsers"].as<JsonArray>();
    JsonArray baseUsers = baseLeaderboard["topUsers"].as<JsonArray>();

    for (size_t i = 0; i < currentUsers.size(); ++i) {
        const char* currentId = currentUsers[i]["id"].as<const char*>();
        int currentCount = currentUsers[i]["count"].as<int>();

        int baseCount = 0;
        bool found = false;
        for (size_t j = 0; j < baseUsers.size(); ++j) {
            if (strcmp(baseUsers[j]["id"].as<const char*>(), currentId) == 0) {
                baseCount = baseUsers[j]["count"].as<int>();
                found = true;
                break;
            }
        }

        int diff = currentCount - baseCount;
        String increase;
        if (diff >= 0) {
            increase = "+" + String(diff);
        } else {
            increase = String(diff);
        }

        const char* username = currentUsers[i]["username"].as<const char*>();
        usernameValues += String(username) + "\n";
        countValues += String(currentCount) + "\n";
        increaseValues += increase + "\n";

        Serial.print("Username: ");
        Serial.print(username);
        Serial.print(", Current Count: ");
        Serial.print(currentCount);
        Serial.print(", Base Count: ");
        Serial.print(baseCount);
        Serial.print(", Increase: ");
        Serial.println(increase);
    }

    DynamicJsonDocument jsonPayload(2048);
    JsonArray embeds = jsonPayload.createNestedArray("embeds");
    JsonObject embed = embeds.createNestedObject();
    embed["title"] = "Top 10 Poppers.";
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

    // Calculate the time since the last check
    File timeFile = LittleFS.open("/last_check_time.txt", "r");
    if (timeFile) {
        String lastCheckTimeStr = timeFile.readString();
        timeFile.close();
        unsigned long lastCheckTimeMillis = lastCheckTimeStr.toInt();
        unsigned long timeSinceLastCheck = (millis() - lastCheckTimeMillis) / 1000; // in seconds

        char timeSinceLastCheckStr[16];
        sprintf(timeSinceLastCheckStr, "%lus", timeSinceLastCheck);

        JsonObject footer = embed.createNestedObject("footer");
        footer["text"] = "Pops since the last check (" + String(timeSinceLastCheckStr) + " ago).";
        footer["icon_url"] = "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png";
    }

    String payload;
    serializeJson(jsonPayload, payload);

    HTTPClient discordHttp;
    discordHttp.begin(wifiClient, discordWebhookUrl);
    discordHttp.addHeader("Content-Type", "application/json");

    int discordResponseCode = discordHttp.POST(payload);

    if (discordResponseCode > 0) {
        String discordResponse = discordHttp.getString();

        Serial.println("Discord response code: " + String(discordResponseCode));
        Serial.println("Discord response: " + discordResponse);
    } else {
        Serial.println("Error on sending POST to Discord: " + String(discordResponseCode));
    }

    discordHttp.end();

    // Update base leaderboard with the current one
    baseLeaderboard = currentLeaderboard;

    File baseFile = LittleFS.open("/base_leaderboard.json", "w");
    if (!baseFile) {
        Serial.println("Failed to open /base_leaderboard.json for writing");
        return;
    }

    serializeJson(baseLeaderboard, baseFile);
    baseFile.close();
    Serial.println("Base leaderboard updated.");
}

void fetchAndDisplaySpecificUser() {
    HTTPClient http;
    wifiClient.setInsecure();
    http.begin(wifiClient, apiUrl);
    http.addHeader("Authorization", authorizationToken);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
        String response = http.getString();
        DynamicJsonDocument doc(4096);
        DeserializationError error = deserializeJson(doc, response);
        if (error) {
            Serial.print("Failed to parse JSON: ");
            Serial.println(error.c_str());
            return;
        }

        JsonArray users = doc["topUsers"].as<JsonArray>();
        for (JsonObject user : users) {
            const char* username = user["username"];
            if (strcmp(username, "BanaantjeJowie") == 0) {
                int count = user["count"];

                // Clear the area where the count is displayed
                display.fillRect(0, 24, SCREEN_WIDTH, 8, SSD1306_BLACK);

                // Update the display with the new count
                display.setCursor(0, 24);
                display.print(username);
                display.print(":");
                display.print(count);
                display.display();

                Serial.print("BanaantjeJowie count: ");
                Serial.println(count);
                break;
            }
        }
    } else {
        Serial.print("Error on sending GET to API: ");
        Serial.println(httpResponseCode);
        display.fillRect(0, 24, SCREEN_WIDTH, 8, SSD1306_BLACK);
        display.setCursor(0, 24);
        display.print("No connection");
        display.display();

    }

    http.end();
}

