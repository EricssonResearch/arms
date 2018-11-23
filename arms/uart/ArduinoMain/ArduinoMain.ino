//#include "ARMS.h"
#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>
//#include <TimerOne.h>


//------------------------------------------ SERIAL COMMUNICATION VARIABLES----------------
/*
 * Global variables used for parseMsg.
 */
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
String temp = "";                // Used as temporary storage variable when converting inputString to floats and ints

/*
 * The variable for ID, fields and the Data-array are created with their corresponding pointers.
 * These are the variables that parseMsg dumps it's info into.
 */
volatile int ID;
volatile int* pID = &ID;
volatile int fields;
volatile int* pfields = &fields;
float Data[10];
char fData[20];
//------------------------------------------|STEPPER MOTOR VARIABLES|----------------
/*
 * Variables for the motor driver..
 */
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

//Variables
volatile int MODE = 0; // selects the step mode of the motor
volatile int nPulse = 0; //Counter variable for number of pulses (do not mistake this for steps!)
volatile int pulseRef = 0; // The reference value for numbers of pulses
volatile int pulseFactor = 1; // makes sure that the motor goes same length independent of selected mode

//------------------------------------------ |SENSOR VARIABLES|----------------
/*
 * Variables for the sensors ADCs
 */
const uint16_t THRESHOLD0 = 512, THRESHOLD1 = 512;
volatile uint16_t adc;
uint16_t adc0, adc1;

/*
 * A test message of the type that the arduino will recieve is created.
 * First number will be the ID.
 * Second number will be the number of fields that the message will contain.
 * The rest of the numbers in the message (which are separated by semi-colons) are data-values that are to be
 * used in whatever function that is called with the ID.
 */
String test = "1,3,1.0;2;3.14;";
void setup() {
      
//------------------------------------------|INIT SERIAL COMMUNICATION|---------------
   //INIT of variables and functions for parseMSG
      inputString.reserve(200);//Reserve 200 bytes for message.
      temp.reserve(200); //Reserve 200 bytes for message.

   //INIT for serial communication
      Serial.begin(9600);
//------------------------------------------ |INIT STEPPER MOTOR|----------------
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
  
//------------------------------------------|INIT SENSOR|----------------      
   //init for force sensor
      ADMUX &= ~(1 << ADLAR);
      ADCSRA |= 0b10000111; 
      ADCSRA |= (1 << ADIE);    // Enable Interrupts 
      ADCSRB = 0; // Trigger for ADC is timer 1 compare match B                                            |
      SREG |= 0x80;   // Global interrupt enable flag 
      


      sei();

}
//------------------------------------------ |MAIN LOOP|----------------
void loop() {

    if (stringComplete) {
      parseMSG(inputString);
      serialSend();

      /*
       * If stringComplete is true, it means an entire message has been read. Then to interpret the message, parseMSG is run which divides it into
       * ID, number of fields, and an array of data points. Finally the inputString- and stringComplete-variable is reset. 
       * 
       * After this, the program goes into a state-mode where the states are determined by the ID-variable.
       */
       switch(ID){
          case 0:
            //closeGripper();
            //serialSend();
            CW(int(Data[0]),int(Data[1]),int(Data[2]));
            break;
          case 1:
            //openGripper();
            //serialSend();
            
            CCW(int(Data[0]),int(Data[1]),int(Data[2]));
            //CCW(2000,180,2);
            break;
          case 2:
            //error();
            break;
          case 3:
            requestInfo();
            break;

          
       }
    }

   
}

//------------------------------------------ SERIAL COMMUNICATION FUNCTIONS----------------
/*
 * Whenever a line appears in the serial channel, a serial event is triggered.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read(); 
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true; 
//      Serial2.println("MESSAGE RECIEVED: " + inputString);
    } 
  }
}


void serialSend(){      
      Serial.print(ID);
      Serial.print(",");
      Serial.print(fields);
      Serial.print(",");
        for(int i=0; i < fields; i++){
          dtostrf(Data[i], 2, 2, fData);
          Serial.print(fData);
          Serial.print(";");
      }
      Serial.println();
    // clear the string:
}

void parseMSG(String input){ 
 /*
  * A counter is initiated to be able to know where in the parsed string the parser is situated.
  * Then a for-loop iterates untill a comma is reached, which means that the ID-number has been parsed. The pointer
  * is referenced to the new value and temp gets reset again.
  * 
  * After this, the same is done for the fields-variable. Every for loop is ended with a counter++, which makes sure that the
  * next for loop doesnt begin with parsing any char twice.
  */
//  Serial2.println("PROBE1");
  int counter = 0;
  int fieldCounter = 0;
  int len = input.length();
  
  for(int i = counter; input[i] !=','; i++){
    temp += input[i];
    counter ++;    
  }
  *pID = temp.toInt();
  temp = "";
  counter++;
  for(int i = counter; input[i] !=','; i++){
    temp += input[i];
    counter ++;    
  }
    counter++;
    *pfields = temp.toInt();
    temp= "";
    /*
     *When parsing the data-fields (separated by ";"), a while loop is used to be able to store a dynamic number of data-fields.
     *The variable fieldCounter is used to know where to place the data-fields in Data[].
     *The for loop which iterates through each data-field available gets "break"ed whenever the End-of-Message sign "#" is reached.
     */

    for(int i = counter; i<=len; i++){
      if( (input[i]>= '0' && input[i] <= '9')|| input[i] =='.'){
//        Serial2.println("appended to temp");
        temp += input[i];
      }
      else if(input[i]==';'){
//        Serial2.println("appended to data");
        Data[fieldCounter] = temp.toFloat();
        fieldCounter++;
        temp = "";
      }
    }
      inputString = "";
      stringComplete = false;
}
//------------------------------------------|STEPPER MOTOR FUNCTIONS|----------------


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
  TCCR2B|= _BV(CS20)|_BV(CS21)|_BV(CS20);
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
   * modes (0-7) where each mode decides on a step fraction
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
ISR(TIMER2_COMPA_vect){
  /*
 * Timer interrupt vector based on OCR2A.
 * Checks if EN and STBY are high.
 * Emitts a short pulse with 4 cpu cycles pulse width.
 * Increments the pulse counter.
 */
  if((PINB&0x01)&&(PIND&0x04)){ //Check if EN and STBY is high.
    
    // Have we reached the reference?
    if(nPulse >= pulseRef){ //YES
          //Turn off the stepper drive
          digitalWrite(EN, LOW);
          digitalWrite(STBY, LOW);
    }
    else{//NO
      
    //Send a pulse and add a count
    PORTD |= (1 << PD3); // Pin n goes high
    PORTD &= ~(1 << PD3); // Pin n goes low   
    nPulse++;
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
  setMode(mode); // Set step size
  counterCLEAR(); // reset the timer two counter
  setDir(0); // Set counterclock-wise direction
  setFrequency(frequency); //Set the frequency
  setPulseRef(steps); // Specify how many steps the motor should take
  counterON();  // activate Timer2 interrupt on
  
  digitalWrite(EN, HIGH); 
  digitalWrite(STBY, HIGH);
  while(nPulse < pulseRef){ // Wait until the reference has been reached
//    Serial.print("nPulse: ");
//    Serial.println(nPulse);
  }
  digitalWrite(EN, LOW);
  digitalWrite(STBY, LOW);
  counterOFF(); // Turn the Timer2 interrupt off
  setPulseRef(0); // Set the pulse reference to zero
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
    while(nPulse < pulseRef){
//        Serial.print("nPulse: ");
//        Serial.println(nPulse);
      }
    digitalWrite(EN, LOW);
    digitalWrite(STBY, LOW);
  counterOFF(); // Turn the Timer2 interrupt off
  setPulseRef(0); // Set the pulse reference to zero
  counterCLEAR(); // clear the nPulse variable
}

//------------------------------------------|COMMAND FUNCTIONS|----------------

void closeGripper(){
  
}

void openGripper(){
  
}

void requestInfo(){
  
}

void error(){
  
}
