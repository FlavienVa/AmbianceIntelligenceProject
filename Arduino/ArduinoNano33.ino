#include <ArduinoBLE.h>
#include <DHT.h>

// Define DHT sensor parameters
#define DHTPIN D5
#define DHTTYPE DHT11
#define SENSOR_SOIL A3


// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// Custom UUIDs for services and characteristics
const char* deviceServiceUuid = "19b10000-e8f2-537e-4f6c-d104768a1214";
const char* ledServiceUuid = "19b10002-e8f2-537e-4f6c-d104768a1214";
const char* sensorServiceUuid = "19b10003-e8f2-537e-4f6c-d104768a1214";
const char* deviceMessageCharacteristicUuid = "19b10010-e8f2-537e-4f6c-d104768a1214";
const char* ledCharacteristicUuid = "19b10012-e8f2-537e-4f6c-d104768a1214";
const char* sensorCharacteristicUuid = "19b10013-e8f2-537e-4f6c-d104768a1214";

// BLE services and characteristics
BLEService ledService(ledServiceUuid);
BLEService sensorService(sensorServiceUuid);
BLECharacteristic ledChar(ledCharacteristicUuid, BLEWrite, 20);
BLEStringCharacteristic sensorCharacteristic(sensorCharacteristicUuid, BLERead | BLENotify, 100);

// Mode switching variables
unsigned long modeStartTime = 0;
const unsigned long COMPUTER_MODE_DURATION = 10000; // 10 seconds
unsigned long lastSensorUpdate = 0;
const unsigned long SENSOR_UPDATE_INTERVAL = 2000; // Update sensor data every 2 seconds

// Data storage for passing between modes
String storedData = "No data yet";
bool newDataAvailable = false;

// Device connection tracking
BLEDevice peripheral;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  pinMode(LED_BUILTIN, OUTPUT);


  dht.begin();

  if (!BLE.begin()) {
    Serial.println("Starting Bluetooth® Low Energy module failed!");
    while (1);
  }

  // Setup for computer mode (peripheral)
  BLE.setLocalName("Nano33_BLE");
  
  // Set up all services

  ledService.addCharacteristic(ledChar);
  sensorService.addCharacteristic(sensorCharacteristic);
  
  BLE.addService(ledService);
  BLE.addService(sensorService);
  
  sensorCharacteristic.writeValue("No sensor data yet");

  // Start advertising
  Serial.println("\n===== COMPUTER MODE =====");
  BLE.advertise();
}

void loop() {
  unsigned long currentTime = millis();

  // Read sensor data
  int soilMoisture = analogRead(SENSOR_SOIL);
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  Serial.println(soilMoisture);
  Serial.println(humidity);
  Serial.println(temperature);
  
  

  // Format sensor data as JSON-like string
  String sensorData = "{\"temp\":" + String(temperature) + 
                      ",\"hum\":" + String(humidity) + 
                      ",\"soil\":" + String(soilMoisture) + "}";
  
  // Update stored data for transmission
  storedData = sensorData;
  newDataAvailable = true;
  
  // Handle BLE communication
  broadcastDataToComputer();
  
  // Small delay to prevent excessive CPU usage
  delay(100);
}

void broadcastDataToComputer() {
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.println("Connected to computer: " + central.address());
    modeStartTime = millis();
    lastSensorUpdate = 0; // Force immediate sensor update on connection
    
    while (central.connected()) {
      unsigned long currentTime = millis();
      
      // Update sensor data at regular intervals
      if (currentTime - lastSensorUpdate >= SENSOR_UPDATE_INTERVAL) {
        // Read fresh sensor data
        int soilMoisture = analogRead(SENSOR_SOIL);
        float humidity = dht.readHumidity();
        float temperature = dht.readTemperature();
        
        // Format and send sensor data
        String sensorData = "{\"temp\":" + String(temperature) + 
                           ",\"hum\":" + String(humidity) + 
                           ",\"soil\":" + String(soilMoisture) + "}";
        
        sensorCharacteristic.writeValue(sensorData);
        
        Serial.println("Sent sensor data: " + sensorData);
        lastSensorUpdate = currentTime;
        
      }
      
      // Handle LED control commands
      if (ledChar.written()) {
        int len = ledChar.valueLength();
        byte buffer[len + 1]; // +1 for null terminator
        ledChar.readValue(buffer, len);
        buffer[len] = 0; // Ensure null termination

        String command = String((char*)buffer);
        Serial.println("Received: " + command);

        if (command == "ON") {
            digitalWrite(LED_BUILTIN, HIGH);
        } else if (command == "OFF") {
            digitalWrite(LED_BUILTIN, LOW);
        }
      }   

      delay(10);
    }
    
    Serial.println("Disconnected from computer");
  }
}
