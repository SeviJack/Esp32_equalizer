#include <FastLED.h>

#define DATA_PIN  18          // use a 5V level shifter
#define WIDTH     10
#define HEIGHT    15
#define NUM_LEDS  (WIDTH*HEIGHT)
#define BRIGHTNESS 64         // cap to reduce current
#define COLOR_ORDER GRB
#define LED_TYPE   WS2812B

CRGB leds[NUM_LEDS];
uint8_t levels[WIDTH];        // 0..HEIGHT per column

// serpentine wiring: col0 bottom->top, col1 top->bottom, ...
static inline uint16_t XY(uint8_t x, uint8_t y){
  if (x & 1) return x*HEIGHT + (HEIGHT-1 - y); // odd column reversed
  return x*HEIGHT + y;                          // even column forward
}

void drawBars(){
  for(uint8_t x=0; x<WIDTH; x++){
    uint8_t h = levels[x] > HEIGHT ? HEIGHT : levels[x];
    for(uint8_t y=0; y<HEIGHT; y++){
      // gradient: low rows dim, high rows bright; hue by column
      uint8_t v = (y < h) ? scale8(255, (y+1)*255/HEIGHT) : 0;
      leds[XY(x, y)] = CHSV(map(x,0,WIDTH-1,0,160), 255, v);
    }
  }
}

void setup(){
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear(true);
}

void loop(){
  // --- demo filler: fake audio levels ---
  static uint16_t t=0; t++;
  for(uint8_t x=0;x<WIDTH;x++){
    // simple moving peak for demo; replace with real audio
    float s = 0.5f + 0.5f*sin( (t*0.05f) + x*0.35f );
    levels[x] = (uint8_t)(s * HEIGHT);
  }
  // --------------------------------------

  drawBars();
  FastLED.show();
  FastLED.delay(16); // ~60 FPS
}
