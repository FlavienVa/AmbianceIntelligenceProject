// Include required libraries
#include <DHT.h>
#include <TimeLib.h> // Add Time library for time-based control

// Define DHT sensor parameters
#define DHTPIN 7      // Pin connected to DHT sensor
#define DHTTYPE DHT11 // Change to DHT22 if using DHT22
#define SOIL_SENSOR A0
#define RELAIS_FAN 10
#define RELAIS_POMP 8
#define RELAIS_LAMP 9

// Threshold values
#define HUMIDITY_THRESHOLD 75       // Turn on fan if humidity exceeds this percentage
#define SOIL_MOISTURE_THRESHOLD 450 // Turn on pump if soil moisture is below this value

// Initialize DHT sensor
DHT dht(DHTPIN, DHTTYPE);

// Time settings
const int LIGHT_ON_HOUR = 8;   // 8am
const int LIGHT_OFF_HOUR = 20; // 8pm

void setup()
{
  // Start serial communication
  Serial.begin(9600);

  // Start the DHT sensor
  dht.begin();

  // Set pin modes for relays
  pinMode(RELAIS_FAN, OUTPUT);
  pinMode(RELAIS_POMP, OUTPUT);
  pinMode(RELAIS_LAMP, OUTPUT);

  // Initialize all relays to OFF (LOW)
  digitalWrite(RELAIS_FAN, LOW);
  digitalWrite(RELAIS_POMP, LOW);
  digitalWrite(RELAIS_LAMP, LOW);

  // Set initial time (you would typically sync this with a real-time clock)
  // For testing, set the time to the current compile time
  setTime(10, 0, 0, 25, 3, 2025); // 10:00:00am March 25, 2025
}

void loop()
{
  // Read sensor values
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();
  int soilMoisture = analogRead(SOIL_SENSOR);

  // Check if DHT readings are valid
  if (isnan(humidity) || isnan(temp))
  {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  // Print sensor readings to Serial Monitor
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");

  Serial.print("Temperature: ");
  Serial.print(temp);
  Serial.println(" °C");

  Serial.print("Soil Moisture: ");
  Serial.println(soilMoisture);

  // Control lamp based on time (ON between 8am and 8pm)
  int currentHour = hour();
  if (currentHour >= LIGHT_ON_HOUR && currentHour < LIGHT_OFF_HOUR)
  {
    digitalWrite(RELAIS_LAMP, HIGH);
    Serial.println("Lamp: ON (Daytime)");
  }
  else
  {
    digitalWrite(RELAIS_LAMP, LOW);
    Serial.println("Lamp: OFF (Nighttime)");
  }

  // Control fan based on humidity
  if (humidity > HUMIDITY_THRESHOLD)
  {
    digitalWrite(RELAIS_FAN, HIGH);
    Serial.println("Fan: ON (Humidity high)");
  }
  else
  {
    digitalWrite(RELAIS_FAN, LOW);
    Serial.println("Fan: OFF (Humidity normal)");
  }

  // Control pump based on soil moisture
  if (soilMoisture > SOIL_MOISTURE_THRESHOLD)
  {
    digitalWrite(RELAIS_POMP, HIGH);
    Serial.println("Pump: ON (Soil dry)");
    delay(3000); // Run pump for 3 seconds
    digitalWrite(RELAIS_POMP, LOW);
    Serial.println("Pump: OFF (After watering)");
  }
  else
  {
    Serial.println("Pump: OFF (Soil moist)");
  }

  Serial.println("--------------------");

  // Wait before next update
  delay(20000); // Check every 10 seconds
}
