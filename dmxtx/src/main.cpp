#include <Arduino.h>
#include <ArtnetWifi.h>
#include <DmxOutput.h>
#include "config.h"

DmxOutput dmx[NUM_OUTPUTS];
uint8_t channels[UNIVERSE_LENGTH + 1];
ArtnetWifi artnet;
int lastMillisDmxPortSent[NUM_OUTPUTS];

// Connect to Wifi
bool connectToWifi(void) {
  bool connected = true;
  int attempts = 0;

  Serial.print("Connecting");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
    if (attempts > 30) {
      connected = false;
      break;
    }
    attempts++;
  }

  // Display WiFi connection result
  if (connected) {
    Serial.print("Connected to ");
    Serial.println(WIFI_SSID);
    Serial.print("IP: ");
    Serial.println(IPAddress(WiFi.localIP()));
  }
  else {
    Serial.println("WiFi Connection Failed");
    delay(3000);
  }

  return connected;
}

void printDmxFrameInfoToConsole(uint16_t universe, uint16_t length, uint8_t sequence, uint8_t* data) {
  Serial.print("DMX: Univ: ");
  Serial.print(universe, DEC);
  Serial.print(", Data Length: ");
  Serial.print(length, DEC);
  Serial.print(", Sequence: ");
  Serial.print(sequence, DEC);
  Serial.print(", Data: ");

  for (int i = 0; i < length; i++) {
    if (i < 16) { // only print first 16 channels
      Serial.print(data[i], DEC);
      Serial.print(" ");
    }
  }
  Serial.println("...");
}

void setChannelsFromDmxFrameData(uint8_t* data, uint16_t length) {
  if (length > UNIVERSE_LENGTH) {
    length = UNIVERSE_LENGTH;
  }

  memset(channels + 1, 0, UNIVERSE_LENGTH);
  memcpy(channels + 1, data, length);
}

void onDmxFrame(uint16_t universe, uint16_t length, uint8_t sequence, uint8_t* data) {
#ifdef DEBUG_PACKETS_SERIAL
  // Note: we capture and print other universes on the network too, we just won't send them out
  printDmxFrameInfoToConsole(universe, length, sequence, data);
#endif
  // Send out the universe if it's a universe we care about
  if (universe == OUTPUT_A_UNIVERSE) {
    setChannelsFromDmxFrameData(data, length);
    dmx[0].write(channels, UNIVERSE_LENGTH);
    lastMillisDmxPortSent[0] = millis();
    while (dmx[0].busy()) {
      // Do nothing while the DMX frame transmits
    }
  }
}

void initializeDmxOutputPorts() {
  dmx[0].begin(OUTPUT_A_GPIO);
  lastMillisDmxPortSent[0] = 0;
}

void turnOnPicoOnboardLed() {
  // Turn on Pico's on-board LED
  // This shows that the Pico is turned on
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
}

void setAllChannelsToZero() {
  for (int i = 1; i < UNIVERSE_LENGTH + 1; i++) {
    channels[i] = 0;
  }
}

// Some DMX software (QLC+) can only send a packet once a second over the network
// but lights might turn off after a 0.1-0.5s delay
// to make things easier, we will hold the last packet and keep sending it for a bit
void writeHoldPacketIfNeeded() {
  if (millis() - 100 > lastMillisDmxPortSent[0]) {
    lastMillisDmxPortSent[0] = millis();
    dmx[0].write(channels, UNIVERSE_LENGTH);
    while (dmx[0].busy()) {
      // Do nothing while the DMX frame transmits
    }
  }
}
//-------------------------------------------
void setup() {
  Serial.begin(115200);
  turnOnPicoOnboardLed();
  initializeDmxOutputPorts();
  setAllChannelsToZero();
  // Connect to WiFi
  while (!connectToWifi()) {}
  artnet.setArtDmxCallback(onDmxFrame);
  artnet.begin();
}
//-------------------------------------------
void loop() {
  artnet.read();
  writeHoldPacketIfNeeded();
}