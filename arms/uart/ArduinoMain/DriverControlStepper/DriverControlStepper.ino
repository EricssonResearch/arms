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

const int pressureVDD = A5; //This outputs 5V on pin A5 which powers the pressure sensor
const int PRE  = A0; //input signal to preassure sensor
const int CUR = A1; // input signal to current sensor
//Variables
int MODE = 0; // selects the step mode of the motor
volatile uint32_t nPulse = 0; //Counter variable for number of pulses (do not mistake this for steps!)
volatile uint32_t pulseRef = 0; // The reference value for numbers of pulses
uint32_t pulseFactor = 1; // makes sure that the motor goes same length independent of selected mode
uint32_t nSteps = 0;       //Counter to send back actual emitted pulses to the rPi
volatile int preassureRef = 100;    // Soft-stop for claw to stop when reached, does not trigger pressure_error
volatile int pressure = 0.0;      // variable that saves the measured pressure every interrupt by TIMER1
volatile int current = 0.0;       // variable that saves the measured current every interrupt by TIMER1
const int pressureCritical = 900; //Maximum pressure 
const int currentCritical = 460;  //480 is around 715mA, 485 is around 600mA, 487 is around 530mA, 490 is around 470mA

//flags
static boolean state = false;            //This boolean switches between if the current OR the pressure is measured at each timer interrupt
volatile boolean runFlag = false;   //flag which allows pulses to be emitted, is set to TRUE every time CW or CCW is called
volatile boolean currentError = false;  //These flags will be set to TRUE if either current or pressure is too high, and prevents any movement.
volatile boolean pressureError = false; // Needs to be volatile since it's accessed both by ISR and main loop. These can only be reset by the raspberry pie


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
  pinMode(pressureVDD, OUTPUT);
  analogWrite(pressureVDD, 255);

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

openGripper(4000,10);
delay(1000);
closeGripper(4000,10);
delay(1000);


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
    current = analogRead(CUR);
    if(current < currentCritical){       //480 is around 715mA, 485 is around 600mA, 487 is around 530mA, 490 is around 470mA
      currentError = true;
      //runFlag = false;
    }
  }
  else{                                  //Here we measure the pressure sensor
    pressure = analogRead(PRE);
    if((pressure >= preassureRef) && ~(PIND&0x80)){  //add a reference pressure where we want to stop, otherwise we might stay inside the emergency stop forever.
      runFlag = false;
    }
    if(pressure >= pressureCritical){        //Making sure we never squeeze harder than a set value. This raises pressureError
      pressureError = true;
      runFlag = false;
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
  if((PINB&0x01)&&(PIND&0x04)){                     //Check if EN and STBY is high.
    if((runFlag == 1) && (pressureError == 0)){    //Check that we have a run command and that no pressure error has occurred
   
    // If we have reached the reference
    //Turn off the stepper drive
    if(nPulse >= pulseRef){       
          digitalWrite(EN, LOW);
          digitalWrite(STBY, LOW);
          runFlag = false;
    }

    // If we have not reached the reference
    //Send a pulse and add a count
    else{        
    PORTD |= (1 << PD3);                            // Pin n goes high
    PORTD &= ~(1 << PD3);                           // Pin n goes low   
    nPulse++;
    }
  }
  }
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
  
  setMode(mode);                                   // Set step size
  counterCLEAR();                                 // reset the timer two counter
  setDir(0);                                      // Set counterclock-wise direction
  setFrequency(frequency);                         //Set the frequency
  setPulseRef(steps);                             // Specify how many steps the motor should take
  counterON();                                  // activate Timer2 interrupt on
  
  digitalWrite(EN, HIGH); 
  digitalWrite(STBY, HIGH);
  if(pressureError == 0){                      //If a pressure error has occurred, don't run this function
    runFlag = true;
  }
  while(runFlag){                               // Wait until the reference has been reached
  }
  digitalWrite(EN, LOW);
  digitalWrite(STBY, LOW);
  counterOFF();                                 // Turn the Timer2 interrupt off
  setPulseRef(0);                               // Set the pulse reference to zero
  nSteps = nSteps + nPulse/pulseFactor;         //Cumulatively add the number of steps taken
  counterCLEAR();                               // clear the nPulse variable
}


void CW(int steps, int frequency, int mode){
  /*
 * Function which drives the stepper motor in Counterclockwise
 * direction for *steps* number of steps in speed determined by *frequency*.
 * Important to notice that *frequency* and *mode* are coupled. This means that
 * depending on *mode* the *frequency* must be in certain ranges
 */

  setMode(mode);                                 // Set step size
  counterCLEAR();                                // reset the timer two counter
  setMode(mode);                                 // Set step size
  setDir(1);                                     // Set Clockwise direction
  setFrequency(frequency);                      //Set the frequency
  setPulseRef(steps);                           // Specify how many steps the motor should take
  counterON();                                  // activate Timer2 interrupt 
  digitalWrite(EN, HIGH);
  digitalWrite(STBY, HIGH);
  if(pressureError == 0){                       //If a pressure error has occurred, don't run this function
    runFlag = true;
  }
    while(runFlag){                              //Wait for the pulses to reach the reference
      }
    digitalWrite(EN, LOW);
    digitalWrite(STBY, LOW);
  counterOFF();                                 // Turn the Timer2 interrupt off
  setPulseRef(0);                               // Set the pulse reference to zero
  nSteps = nSteps + nPulse/pulseFactor;         //Cumulatively add the number of steps taken
  counterCLEAR();                                // clear the nPulse variable

}

void closeGripper(int pulser, int setPreassure){
  preassureRef = setPreassure;                  //Set reference preassure
  nSteps = 0;                                   //resets the counter (amount of steps) that will be sent to the rPi
  int full_rotations = pulser/1024;             //Divide the total amount of steps into batches of 1024
  int rest_rotations = pulser%1024;             //Any remaining steps that does not amount to a full 1024
    
  for(int i = 0; i < full_rotations; i++){      //Run the number of batches that equals 1024 steps a piece
    CCW(1024, 75,3);
    delay(3000);                                //Wait for motor to turn the number of steps instructed before sending next batch   
    }
    
    CCW(rest_rotations, 75,3);                   //Run the remaining number of steps
    delay(3000);                                //Wait for motor to turn the number of steps instructed before progressing with program

    //Sending response to rPi: message = (ID,DATA_POINTS,STEPS;PRESSURE;CURRENT_ERROR;PRESSURE_ERROR;)
    Serial.print("0,4,");
    Serial.print(nSteps);
    Serial.print(";");
    Serial.print(pressure);
    Serial.print(";");
    Serial.print(currentError);
    Serial.print(";");
    Serial.print(pressureError);
    Serial.println(";");
    nSteps = 0;                                  //resets the counter (amount of steps) that will be sent to the rPi
}

void openGripper(int pulser, int setPreassure){
  preassureRef = setPreassure;                   //Set reference preassure 
  nSteps = 0;                                   //resets the counter (amount of steps) that will be sent to the rPi
  int full_rotations = pulser/1024;             //Divide the total amount of steps into batches of 1024
  int rest_rotations = pulser%1024;             //Any remaining steps that does not amount to a full 1024
  
    
  for(int i = 0; i < full_rotations; i++){      //Run the number of batches that equals 1024 steps a piece
    CW(1024, 75,3);
    delay(3000);                                //Wait for motor to turn the number of steps instructed before sending next batch
    }
   
    CW(rest_rotations, 75,3);                   //Run the remaining number of steps
    delay(3000);                                //Wait for motor to turn the number of steps instructed before progressing with program

    //Sending response to rPi: message = (ID,DATA_POINTS,STEPS;PRESSURE;CURRENT_ERROR;PRESSURE_ERROR;)
    Serial.print("1,4,");
    Serial.print(nSteps);
    Serial.print(";");
    Serial.print(pressure);
    Serial.print(";");
    Serial.print(currentError);
    Serial.print(";");
    Serial.print(pressureError);
    Serial.println(";");
    nSteps = 0;                                  //resets the counter (amount of steps) that will be sent to the rPi
}

void acknowledgeError(int resetPressure, int resetCurrent){
  if(resetPressure == 1){    
    pressureError = false;
    }

  if(resetCurrent == 1){    
    currentError = false;
    }
}
