#include <FastLED.h>

#define DATA_PIN 18    // use your actual GPIO pin
#define NUM_LEDS 2       // only 1 LED
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.clear(true);
}

void loop() {
  leds[1] = CRGB::Red;   // turn first LED red
  FastLED.show();
  delay(1000);
}
