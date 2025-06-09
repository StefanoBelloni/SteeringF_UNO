/*
  AnalogReadSerial

  Reads an analog input on pin 0, prints the result to the Serial Monitor.
  Graphical representation is available using Serial Plotter (Tools > Serial Plotter menu).
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.

  This example code is in the public domain.

  https://www.arduino.cc/en/Tutorial/BuiltInExamples/AnalogReadSerial
*/

#define VERSION  2

#define PIN_BTN_GEAR 2
#define PIN_BTN_GEAR_MIN 3

#if VERSION == 2
#   define PIN_BTN_RIGHT 4
#   define PIN_BTN_LEFT  5
#endif

#define PIN_WHEEL_INPUT A0
#define PIN_GAS_INPUT A2
#define PIN_BREAK_INPUT A1

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  pinMode(PIN_BTN_GEAR, INPUT_PULLUP);
  pinMode(PIN_BTN_GEAR_MIN, INPUT_PULLUP);
#if VERSION == 2
  pinMode(PIN_BTN_RIGHT, INPUT_PULLUP);
  pinMode(PIN_BTN_LEFT, INPUT_PULLUP);
#endif
}

// the loop routine runs over and over again forever:
void loop() {

  uint32_t steer      = analogRead(PIN_WHEEL_INPUT);
  uint32_t breakpedal = analogRead(PIN_BREAK_INPUT);
  uint32_t throttle   = analogRead(PIN_GAS_INPUT);
  uint32_t gear_up    = digitalRead(PIN_BTN_GEAR);
  uint32_t gear_down  = digitalRead(PIN_BTN_GEAR_MIN);
#if VERSION == 2
  uint32_t left_btn   = digitalRead(PIN_BTN_LEFT);
  uint32_t right_btn  = digitalRead(PIN_BTN_RIGHT);
#endif

  Serial.print(steer);       Serial.print(';');
  Serial.print(breakpedal);  Serial.print(';');
  Serial.print(throttle);    Serial.print(';');
  Serial.print(gear_up);     Serial.print(';');
  Serial.print(gear_down);   
  #if VERSION == 2
                             Serial.print(';'); 
  Serial.print(right_btn);   Serial.print(';');
  Serial.print(left_btn);    
  #endif
                             Serial.print('\n');
  delay(10);  // delay in between reads for stability

}