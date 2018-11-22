//#include <avr.h>

//PINS
const int STBY = 8;
const int REF = 9;
const int M1 = 13;
const int M2 = 12;
const int M3 = 11;
const int EN = 2;
const int STEP = 3;
const int DECAY = 5;
const int DIR = 7;

//Variables
int nPulse = 0;
int dirState =0;
int pulseLim = 0;

void setup() {
  //init for pins
  pinMode(STBY, OUTPUT);
  pinMode(REF, OUTPUT);
  pinMode(M1, OUTPUT);
  pinMode(M2, OUTPUT);
  pinMode(M3, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(STEP, OUTPUT);
  pinMode(DECAY, OUTPUT);
  pinMode(DIR, OUTPUT);

  //Initial configurations
  digitalWrite(STBY,LOW); // put motorshield in standby
  digitalWrite(EN,LOW); // output stage disabled

  //Set mode to 1/256 step
  digitalWrite(M1,HIGH);
  digitalWrite(M2,HIGH);
  digitalWrite(M3,HIGH);


  Serial.begin(9600);
  
  TCCR2A = 0x00;
  TCCR2A = _BV(WGM21);

  TCCR2B = 0x00;
  TCCR2B = _BV(CS22); //| _BV(CS21);

  TCNT2 = 0;
  OCR2A = 254;
  TIMSK2 |= 0x02;

}

void loop() {
// Serial.print("nPulse:");
// Serial.println(nPulse);
// Serial.print("DIR: ");
// Serial.println(digitalRead(DIR));
// Serial.print("OCR2A: ");
// Serial.println(OCR2A);
// Serial.print("pulseLim: ");
// Serial.println(pulseLim);
  CW(10000, 240);
  setPulseRef(0);
  delay(10000);
  CCW(1000, 90);
  setPulseRef(0);
  delay(1000);
}
/*
 * Timer interrupt vector based on OCR2A.
 * Checks if EN and STBY are high.
 * Emitts a short pulse with 4 cpu cycles pulse width.
 * Increments the pulse counter.
 */

/*
 * The timer speed is set by vel, which should be an int between 1-255. 
 * By changing OCR2A, while having a prescaler value of 256, one can get a timer frequency
 * between 31250Hz-244Hz.
 */
void setVelocity(int vel){
  OCR2A = vel;
}
void setDir(bool dir){
  digitalWrite(DIR, dir);
}
/*
 * Sets the pulse counter limit.
 */
void setPulseRef(int pulses){
  pulseLim = pulses;
}

void counterON(){
  TIMSK2 |= 0x02;
}

void counterOFF(){
  TIMSK2 &= 0xFD;
}

void counterCLEAR(){
  nPulse = 0;
}

void CCW(int steps, int velocity){
 // counterCLEAR();
  setDir(0);
  setVelocity(velocity);
  setPulseRef(steps);

  counterON();
  
  digitalWrite(EN, HIGH);
  digitalWrite(STBY, HIGH);
  while(nPulse <= pulseLim){
    Serial.print("nPulse: ");
    Serial.println(nPulse);
  }
  digitalWrite(EN, LOW);
  digitalWrite(STBY, LOW);
  counterOFF();
  setPulseRef(0);
//  counterCLEAR();
}
void CW(int steps, int velocity){
  //counterCLEAR();
  setDir(1);
  setVelocity(velocity);
  setPulseRef(steps);
  counterON();
  
  digitalWrite(EN, HIGH);
  digitalWrite(STBY, HIGH);
    while(nPulse <= pulseLim){
        Serial.print("nPulse: ");
        Serial.println(nPulse);
      }
    digitalWrite(EN, LOW);
    digitalWrite(STBY, LOW);
    counterOFF();
    setPulseRef(0);
    counterCLEAR();
}

ISR(TIMER2_COMPA_vect){
  //if((PORTD&0x04)&(PORTB&0x01)){ //Check if EN and STBY is high.
    PIND |= 0x08;
    PIND &= 0xF7;
    nPulse++;
  //}
}

