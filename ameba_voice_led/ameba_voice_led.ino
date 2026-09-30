// Target: Ameba AMB82-MINI (RTL8735B), AmebaPro2 Arduino package.
// In the installed board variant: LED_B = D23, LED_G = D24.
// The bundled AMB82-MINI LED example uses HIGH = on, LOW = off.
// USB serial protocol at 115200 baud:
//   CMD <id> LEFT|RIGHT|BLINK3|OFF|STATUS\n
//   ACK <id> BLUE=0|1 GREEN=0|1\n  or  ERR <id> UNKNOWN BLUE=0 GREEN=0\n

const int BLUE_LED_PIN = LED_B;
const int GREEN_LED_PIN = LED_G;
const int LED_ON = HIGH;
const int LED_OFF = LOW;

bool blueOn = false;
bool greenOn = false;
char inputLine[48];
size_t inputLength = 0;
bool discardingLongLine = false;

void applyLedState(bool blue, bool green) {
  digitalWrite(BLUE_LED_PIN, blue ? LED_ON : LED_OFF);
  digitalWrite(GREEN_LED_PIN, green ? LED_ON : LED_OFF);
  blueOn = blue;
  greenOn = green;
}

void blinkThreeTimes() {
  const bool previousBlue = blueOn;
  const bool previousGreen = greenOn;
  for (int count = 0; count < 3; count++) {
    applyLedState(true, true);
    delay(300);
    applyLedState(false, false);
    delay(300);
  }
  applyLedState(previousBlue, previousGreen);
}

void sendState(const char *id) {
  Serial.print("ACK ");
  Serial.print(id);
  Serial.print(" BLUE=");
  Serial.print(blueOn ? '1' : '0');
  Serial.print(" GREEN=");
  Serial.println(greenOn ? '1' : '0');
}

void processLine(char *line) {
  // Require exactly: CMD + space + 1-to-6 digit id + space + action.
  if (strncmp(line, "CMD ", 4) != 0) return;
  char *id = line + 4;
  char *separator = strchr(id, ' ');
  if (!separator) return;
  *separator = '\0';
  size_t idLength = strlen(id);
  if (idLength == 0 || idLength > 6 || id[0] == '0') return;
  for (size_t i = 0; i < idLength; i++) {
    if (id[i] < '0' || id[i] > '9') return;
  }

  const char *action = separator + 1;
  if (strcmp(action, "LEFT") == 0) {
    applyLedState(true, false);
    sendState(id);
  } else if (strcmp(action, "RIGHT") == 0) {
    applyLedState(false, true);
    sendState(id);
  } else if (strcmp(action, "BLINK3") == 0) {
    blinkThreeTimes();
    sendState(id);
  } else if (strcmp(action, "OFF") == 0) {
    applyLedState(false, false);
    sendState(id);
  } else if (strcmp(action, "STATUS") == 0) {
    sendState(id);
  } else {
    applyLedState(false, false);
    Serial.print("ERR ");
    Serial.print(id);
    Serial.println(" UNKNOWN BLUE=0 GREEN=0");
  }
}

void setup() {
  pinMode(BLUE_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  applyLedState(false, false);
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) {
    char incoming = (char)Serial.read();
    if (incoming == '\r') continue;
    if (incoming == '\n') {
      if (!discardingLongLine && inputLength > 0) {
        inputLine[inputLength] = '\0';
        processLine(inputLine);
      }
      inputLength = 0;
      discardingLongLine = false;
    } else if (!discardingLongLine) {
      if (inputLength < sizeof(inputLine) - 1) {
        inputLine[inputLength++] = incoming;
      } else {
        inputLength = 0;
        discardingLongLine = true;
      }
    }
  }
}
