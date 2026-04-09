#include <Arduino.h>
#include <BLE.h>

// =====================
// Macros / Configuration
// =====================

// H-bridge pins
#define MOTOR_IN1 34
#define MOTOR_IN2 35

// PWM settings
#define PWM_MAX        255
#define MAX_SPEED      255
#define DEFAULT_SPEED  50
#define SPEED_STEP     10

// Button mappings
#define BTN_FORWARD    1
#define BTN_REVERSE    2
#define BTN_STOP       3
#define BTN_SPEED_UP   5
#define BTN_SPEED_DOWN 6

// =====================
// Globals
// =====================

BLEServiceUART uart;

int motorSpeed = DEFAULT_SPEED;
int motorDirection = 0; // 0=stopped, 1=forward, -1=reverse

// =====================
// Motor Control Helpers
// =====================

void applyMotor() {
  if (motorDirection == 1) { // Forward
    analogWrite(MOTOR_IN1, MAX_SPEED - motorSpeed);
    digitalWrite(MOTOR_IN2, HIGH);
  }
  else if (motorDirection == -1) { // Reverse
    digitalWrite(MOTOR_IN1, HIGH);
    analogWrite(MOTOR_IN2, MAX_SPEED - motorSpeed);
  }
  else { // Stop
    digitalWrite(MOTOR_IN1, LOW);
    digitalWrite(MOTOR_IN2, LOW);
  }
}

void changeSpeed(int delta) {
  motorSpeed += delta;
  if (motorSpeed > MAX_SPEED) motorSpeed = MAX_SPEED;
  if (motorSpeed < 0) motorSpeed = 0;

  Serial.print("Speed set to: ");
  Serial.println(motorSpeed);

  applyMotor();
}

// =====================
// Setup
// =====================

void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);

  // Start motor OFF
  applyMotor();

  BLE.begin("DiscoMotor");
  BLE.server()->addService(&uart);
  BLE.startAdvertising();
}

// =====================
// Loop
// =====================

void loop() {
  while (uart.available()) {
    char c = uart.read();

    if (c != '!') continue;

    while (uart.available() < 3);

    char type = uart.read();
    char id = uart.read();
    char state = uart.read();

    if (type == 'B' && isdigit(id) && isdigit(state)) {
      int button = id - '0';
      int pressed = state - '0';

      // Ignore releases
      if (!pressed) continue;

      Serial.print("Button ");
      Serial.print(button);
      Serial.println(" pressed");

      switch (button) {

      case BTN_FORWARD:
        motorDirection = 1;
        applyMotor();
        Serial.println("Motor FORWARD");
        break;

      case BTN_REVERSE:
        motorDirection = -1;
        applyMotor();
        Serial.println("Motor REVERSE");
        break;

      case BTN_STOP:
        motorDirection = 0;
        applyMotor();
        Serial.println("Motor STOP");
        break;

      case BTN_SPEED_UP:
        changeSpeed(SPEED_STEP);
        break;

      case BTN_SPEED_DOWN:
        changeSpeed(-SPEED_STEP);
        break;

      default:
        Serial.println("Unhandled button");
        break;
      }
    }
    else {
      Serial.println("Bad packet received, skipping");
    }
  }
}