//#include <avr.h>

//PINS
const int STBY = 8; //PB0 Sets the driver in standby mode
const int REF = 9; // determines the reference voltage of the internal pwm:s
const int M1 = 13; // Mode 1, used to select the stepsize
const int M2 = 12; // Mode 2, used to select the stepsize
const int M3 = 11; // Mode 3, used to select the stepsize
const int EN = 2; //PD2 Shuts of the board directly by connecting emitters of transistors to GND
const int STEP = 3; // Input pin for steps, minimum pulse can be 40ns.
const int DECAY = 5; // Selects the decay mode for the motor
const int DIR = 7; // Sets the direction of the stepper motor, 1 is CW and 0 is CC2
const int pressure_voltage = A5;

//Variables
volatile int MODE = 0; // selects the step mode of the motor
volatile int nPulse = 0; //Counter variable for number of pulses (do not mistake this for steps!)
volatile int pulseRef = 0; // The reference value for numbers of pulses
volatile int pulseFactor = 1; // makes sure that the motor goes same length independent of selected mode
volatile boolean runflag = false;

//from timer interrupt to measure sensor values
static boolean state = false;            //This boolean switches between if the current OR the pressure is measured at each timer interrupt
volatile boolean Current_Error = false;  //These flags will be set to TRUE if either current or pressure is too high
volatile boolean Pressure_Error = false; // Needs to be volatile since it's accessed both by ISR and main loop
volatile float pressure = 0.0;
volatile float current = 0.0;
volatile int Pressure_ref = 100;
volatile int nSteps = 0;


//testing variables
boolean time_to_run = true;


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
  pinMode(pressure_voltage, OUTPUT);
  analogWrite(pressure_voltage, 255);

  //Initial configurations
  digitalWrite(STBY,LOW); // put motorshield in standby
  digitalWrite(EN,LOW); // output stage disabled

  //Set mode to 1 full step
  setMode(0);


  Serial.begin(9600);
  //Timer2 Configurations
  TCCR2A &= 0x0F; // CLEAR register
  TCCR2A = _BV(WGM21); // Set CTC mode
  
  setTimer2Prescaler(32); // sets the TCCR2B register bits cs20-cs22 ,32 is good
  TCNT2 = 0; // clear counter
  OCR2A = 150; // should be between 80 and 150, OCR2A+1 is the number of clockcycles between the motor pulses.
  TIMSK2 |= 0x02; // Enable OCEIA2 - turn on the Timer 2 interrupt

  //Timer1 Configurations
  TCCR1A = 0;                            // normal operation
  //setTimer1Prescaler(8);                 //set pre-scalar to 8
  TCCR1B = bit(WGM12) | bit(CS12) | bit(CS10);   // CTC, no pre-scaling (OG: CS10), CS11 should be prescalar 8.
  OCR1A =  2500;                            // compare A register value (1000 * clock speed) THIS NEEDS TUNING OG: 999
  TIMSK1 = bit (OCIE1A);                 // interrupt on Compare A Match


}

void loop() {
  /*
  while(pressure > 50){
    CW(100,150,2);
    Serial.print("running CW: ");
    Serial.println(pressure);
    delay(1000);
  }
//Serial.println("Restarting loop");
//CW(1000,150,2);   //CW öppnar

while(pressure < 400){
  CCW(100,150,2);
  Serial.print("running CCW: ");
  Serial.println(pressure);
  delay(1000);
}
*/
//delay(2000);

/*
Serial.println("restarting loop");
runflag = true;
delay(1000);
CCW(100,150,2);    //CCW stänger
*/
////if(time_to_run){
//
//  CW(1024,75,3);
//  delay(2000);
//  time_to_run = false;
////}
//

openGripper(4000,10);
delay(1000);
closeGripper(4000,10);
delay(1000);
/*
runflag = true;
CW(500,75,3);
delay(2500);
*/

}




void setTimer2Prescaler(int prescaler){
/*
 * Function created to be able to play around with prescalers
 * valid inputs are 1,8,32,64,128,256
 * if invalid input is entered the prescaler will not be altered.
 */
  TCCR2B = 0x00; // CLEAR register
switch( prescaler){
  case 1: //No prescale
  TCCR2B|= _BV(CS20);
  break;

  case 8: // 1/8 prescale
  TCCR2B|= _BV(CS21);
  break;

  case 32: // 1/32 prescale
  TCCR2B|= _BV(CS21)|_BV(CS20);
  break;

  case 64: // 1/64 prescale
  TCCR2B|= _BV(CS22);
  break;

  case 128: // 1/128 prescale
  TCCR2B|= _BV(CS22)|_BV(CS20);
  break;

  case 256: // 1/256 prescale
  TCCR2B|= _BV(CS22)|_BV(CS21);
  break;

  case 1024: // 1/1024 prescale
  TCCR2B|= _BV(CS22)|_BV(CS21)|_BV(CS20);
  break;
  
}

}

void setFrequency(int freq){
/*
 * The timer speed is set by freq, which should be an int between 1-255 that changes OCR2A.
 * This means that only certain freqencies can be reached depending on what prescaler is used
 * prescaler  OCR2A             Hz
 *  1         1-255 -> 8,000,000 - 62,500
 *  8         1-255 -> 1,000,000 - 7,813
 *  32        1-255 -> 250,000 - 1,953
 *  64        1-255 -> 125,000 - 977
 *  128       1-255 -> 62,500 - 488
 *  256       1-255 -> 31,250 - 244
 *  1024      1-255 -> 7,813 - 61
 *  
 *  This must be matched with the Mode used for the motor, otherwise it will consume
 *  to much current or not being able to complete the step in time.
 */
  OCR2A = freq;
}
void setDir(bool dir){
  //Change the direction of the stepper motor
  //1 is Clockwise
  //0 is counter clockwise
  digitalWrite(DIR, dir);
}
/*
 * Sets the pulse counter limit.
 */
void setPulseRef(int stepRef){
  pulseRef = pulseFactor*stepRef;
}

void counterON(){
  //Turns the Timer2 compare A interrupt on by enabling the OCIE2A
  TIMSK2 |= 0x02;
}

void counterOFF(){
  //Turns the Timer2 compare A interrupt on by disabling the OCIE2A
  TIMSK2 &= 0xFD;
}

void counterCLEAR(){
  //Clear the pulse-counter
  nPulse = 0;
}

void setMode(int mode){
  /*
   * Sets the three pins M1,M2 and M3 according to 8 different
   * modes (0-7) where each mode decides on a 
   */
  MODE = mode;
  switch(mode){
    case 0: //Full-step
      pulseFactor = 1;
      digitalWrite(M1,LOW);
      digitalWrite(M2,LOW);
      digitalWrite(M3,LOW);
      
    break;
  
    case 1: // 1/2 step
      pulseFactor = 2;
      digitalWrite(M1,HIGH);
      digitalWrite(M2,LOW);
      digitalWrite(M3,LOW);
    
    break; 
    
    case 2: // 1/4 step
      pulseFactor = 4;
      digitalWrite(M1,LOW);
      digitalWrite(M2,HIGH);
      digitalWrite(M3,LOW);
    break;
  
    case 3: // 1/8 step
      pulseFactor = 8;
      digitalWrite(M1,HIGH);
      digitalWrite(M2,HIGH);
      digitalWrite(M3,LOW);
    break;
  
    case 4:// 1/16 step
      pulseFactor = 16;
      digitalWrite(M1,LOW);
      digitalWrite(M2,LOW);
      digitalWrite(M3,HIGH);
    break;
  
    case 5: // 1/32 step
      pulseFactor = 32;
      digitalWrite(M1,HIGH);
      digitalWrite(M2,LOW);
      digitalWrite(M3,HIGH);
    break;
  
    case 6: // 1/128 step
      pulseFactor = 128;
      digitalWrite(M1,LOW);
      digitalWrite(M2,HIGH);
      digitalWrite(M3,HIGH);
    break;
  
    case 7: // 1/ 256 step
      pulseFactor = 256;
      digitalWrite(M1,HIGH);
      digitalWrite(M2,HIGH);
      digitalWrite(M3,HIGH);
    break;
}
}
  

  

//Interrupts

ISR(TIMER1_COMPA_vect){
  state = !state;                        // toggle state
  if(state){                             //Here we measure the current sensor
    current = analogRead(A1);
    if(current < 470){                   //480 is around 715mA, 485 is around 600mA, 487 is around 530mA, 490 is around 470mA
      //Serial.print("A2 current: ");
      //Serial.println(current);
      Current_Error = true;
      runflag = false;
    }
  }
  else{                                  //Here we measure the pressure sensor
    pressure = analogRead(A0);
    if((pressure >= Pressure_ref) && ~(PIND&0x80)){  //add a reference pressure where we want to stop, otherwise we might stay inside the emergency stop forever.
      runflag = false;
    }
    if(pressure >= 700){                    //This value needs tuning, roughly 300-400 range ish
      //Serial.print("A1 pressure: ");
      //Serial.println(pressure);
      Pressure_Error = true;
      runflag = false;
    }
    }
}


ISR(TIMER2_COMPA_vect){
  /*
 * Timer interrupt vector based on OCR2A.
 * Checks if EN and STBY are high.
 * Emitts a short pulse with 4 cpu cycles pulse width.
 * Increments the pulse counter.
 */
 //cli();
  if((PINB&0x01)&&(PIND&0x04)){ //Check if EN and STBY is high.
    if(runflag == 1){
    // Have we reached the reference?
    if(nPulse >= pulseRef){ //YES
          //Turn off the stepper drive
          digitalWrite(EN, LOW);
          digitalWrite(STBY, LOW);
          runflag = false;
    }
    else{//NO
      
    //Send a pulse and add a count
    PORTD |= (1 << PD3); // Pin n goes high
    PORTD &= ~(1 << PD3); // Pin n goes low   
    nPulse++;
    }
  }
  }
  //sei();
}

/*
 * This section contains functions composed of the functions above, but packaged
 * for easy use
 */
void CCW(int steps, int frequency, int mode){
  /*
   * Function which drives the stepper motor in Counterclockwise
   * direction for *steps* number of steps in speed determined by *frequency*.
   * Important to notice that *frequency* and *mode* are coupled. This means that
   * depending on *mode* the *frequency* must be in certain ranges
   */
  
  setMode(mode); // Set step size
  counterCLEAR(); // reset the timer two counter
  setDir(0); // Set counterclock-wise direction
  setFrequency(frequency); //Set the frequency
  setPulseRef(steps); // Specify how many steps the motor should take
  counterON();  // activate Timer2 interrupt on
  
  digitalWrite(EN, HIGH); 
  digitalWrite(STBY, HIGH);
  runflag = true;
  Serial.println("CCW");
  while(runflag){ // Wait until the reference has been reached
//    Serial.print("nPulse: ");
//    Serial.println(nPulse);
      //Serial.print("runflag: ");
//      //Serial.println(runflag);
//      Serial.print("Current: ");
//      Serial.println(current);
//      Serial.print("Pressure: ");
//      Serial.println(pressure);
      //delay(500);
  }
  digitalWrite(EN, LOW);
  digitalWrite(STBY, LOW);
  counterOFF(); // Turn the Timer2 interrupt off
  setPulseRef(0); // Set the pulse reference to zero
  nSteps = nSteps + nPulses/pulseFactor;
  counterCLEAR(); // clear the nPulse variable
}
void CW(int steps, int frequency, int mode){
  /*
 * Function which drives the stepper motor in Counterclockwise
 * direction for *steps* number of steps in speed determined by *frequency*.
 * Important to notice that *frequency* and *mode* are coupled. This means that
 * depending on *mode* the *frequency* must be in certain ranges
 */
  
  setMode(mode); // Set step size
  counterCLEAR(); // reset the timer two counter
  setMode(mode); // Set step size
  setDir(1); // Set Clockwise direction
  setFrequency(frequency); //Set the frequency
  setPulseRef(steps); // Specify how many steps the motor should take
  counterON();  // activate Timer2 interrupt 
  digitalWrite(EN, HIGH);
  digitalWrite(STBY, HIGH);
  runflag = true;
  //Serial.println("CW");
    while(runflag){
//        Serial.print("nPulse: ");
//        Serial.println(nPulse);
          //Serial.print("runflag: ");
//          //Serial.println(runflag);
//          Serial.print("Current: ");
//          Serial.println(current);
//          Serial.print("Pressure: ");
//          Serial.println(pressure);
          //delay(500);
      }
    digitalWrite(EN, LOW);
    digitalWrite(STBY, LOW);
  counterOFF(); // Turn the Timer2 interrupt off
  setPulseRef(0); // Set the pulse reference to zero
  nSteps = nSteps + nPulses/pulseFactor;
  counterCLEAR(); // clear the nPulse variable
}

void closeGripper(int pulser, int preasure){
  int full_rotations = pulser/1024;
  int rest_rotations = pulser%1024;
 volatile int pulse_cnter = pulser;
      Serial.print("Full_rotations ");
    Serial.println(full_rotations);

    Serial.print("rest_rotations ");
    Serial.println(rest_rotations);
  for(int i = 0; i >= full_rotations; i++){
    CCW(1024, 75,3);

    pulse_cnter -= 1024;
    Serial.print("Pulse counter: ");
    Serial.println(pulse_cnter);
    delay(3000);

    
    }
    CCW(rest_rotations, 75,3);
    pulse_cnter = pulse_cnter - rest_rotations;
    Serial.print("Pulse counter: ");
    Serial.println(pulse_cnter);
    delay(3000);
    
}

void openGripper(int pulser, int preasure){
  int full_rotations = pulser/1024;
  int rest_rotations = pulser%1024;
 //volatile int pulse_cnter = 0;
    Serial.print("Full_rotations ");
    Serial.println(full_rotations);

    Serial.print("rest_rotations ");
    Serial.println(rest_rotations);
  for(int i = 0; i >= full_rotations; i++){
    CW(1024, 75,3);
    //pulse_cnter += 1024;
    Serial.print("nSteps: ");
    Serial.println(nSteps);
    delay(3000);

    
    }
    CW(rest_rotations, 75,3);
    //pulse_cnter = pulse_cnter + rest_rotations;
    Serial.print("nSteps: ");
    Serial.println(nSteps);
    delay(3000);
    
}
