// NOTE: This sketch currently uses 89% of the arduino's dynamic memory
// due to the U8g2 display library's internal
// Adding servo control logic on top of this will require careful memory management
// consider fixed-size buffers over String objects,and monitor compile output for memory usage before adding new features.

#include <U8g2lib.h>

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

char message[32];
unsigned long foundDisplayUntil = 0;
bool showingFoundMessage = false;

void setup() {
  Serial.begin(1000000);
  u8g2.begin();

  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_6x10_tf);
  u8g2.drawStr(10, 32, "Waiting...");
  u8g2.sendBuffer();
}

void loop() {
  if (Serial.available() > 0) {
    int len = Serial.readBytesUntil('\n', message, sizeof(message) - 1);
    message[len] = '\0';

    if (strcmp(message, "SEARCH") == 0) {
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_6x10_tf);
      u8g2.drawStr(10, 32, "Searching...");
      u8g2.sendBuffer();
      showingFoundMessage = false;
    }
    else if (strcmp(message, "FOUND") == 0) {
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_6x10_tf);
      u8g2.drawStr(5, 32, "Target found!");
      u8g2.sendBuffer();
      showingFoundMessage = true;
      foundDisplayUntil = millis() + 2000;
    }
    else if (strncmp(message, "DIST,", 5) == 0) {
      if (!showingFoundMessage || millis() >= foundDisplayUntil) {
        char displayText[32];
        snprintf(displayText, sizeof(displayText), "Target at: %s m", message + 5);

        u8g2.clearBuffer();
        u8g2.setFont(u8g2_font_6x10_tf);
        u8g2.drawStr(5, 32, displayText);
        u8g2.sendBuffer();
      }
    }
  }
}