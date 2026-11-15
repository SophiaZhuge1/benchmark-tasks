// Arduino Nano Every. D5: irrigation PWM, D6: aspiration PWM.
// D2: momentary START to GND (INPUT_PULLUP); D13: visible trial LED.
// Use suitably rated motor-driver modules and a separate regulated 12 V supply.
// Never connect a pump directly to a GPIO. Controller/pumps stay outside tray.
// Calibrate actual flow at the tool outlet; PWM values are NOT flow calibration.
const byte IR=5, SU=6, START=2, LED=13;
const byte IR_PWM=0, SU_PWM=0; // Set ONLY after measured water-flow calibration.
bool active=false, lastButton=HIGH;
unsigned long started=0;
void setup(){
 pinMode(IR,OUTPUT);pinMode(SU,OUTPUT);pinMode(LED,OUTPUT);
 pinMode(START,INPUT_PULLUP);analogWrite(IR,0);analogWrite(SU,0);
}
void loop(){
 bool b=digitalRead(START);
 if(!active && lastButton==HIGH && b==LOW && IR_PWM>0 && SU_PWM>0){
  active=true;started=millis();digitalWrite(LED,HIGH);
 }
 lastButton=b;
 if(!active) return;
 unsigned long t=millis()-started;
 bool wet=(t>=16000 && t<21000)||(t>=24000 && t<29000)||(t>=32000 && t<37000);
 analogWrite(IR,wet?IR_PWM:0);analogWrite(SU,SU_PWM);
 if(t>=60000){analogWrite(IR,0);analogWrite(SU,0);digitalWrite(LED,LOW);active=false;}
}
