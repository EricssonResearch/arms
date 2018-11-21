//#include "ARMS.h"
#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <TimerOne.h>


//global variable for led
const int led = 13;

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

/*
 * Variables for the motor driver..
 */
const int standby = 8;
const int ref = 9;
const int mode3 = 11;
const int mode2 = 12;
const int mode1 = 13;

const int EN_FAULT = 2;
const int STCK1 = 3;    //PWM Input, which determines speed, "stepsender"
const int DECAY = 5;
const int STCK2 = 6;
const int DIR1 = 4;     //DIR1 = HIGH, DIR2 = LOW is CCW rotation
const int DIR2 = 7;     //DIR1 = LOW, DIR2 = HIGH is CW rotation

/*
 * Stepper related variables.
 */
long stepCounter = 0;
long stepRef=0;
long volatile stepDiff=1;
int volatile stepState = 0;
//Implement a clock to generate a PWM signal. 
//Implement interrupt connected to clock to count pulses. 

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
      //init for stepper motor
      pinMode(DIR1,OUTPUT);
      pinMode(DIR2,OUTPUT);
      pinMode(STCK1, OUTPUT);
      pinMode(standby, OUTPUT);
      digitalWrite(DIR1,HIGH);  digitalWrite(DIR2,LOW); //CCW

   //INIT of variables and functions for parseMSG
      inputString.reserve(200);//Reserve 200 bytes for message.
      temp.reserve(200); //Reserve 200 bytes for message.

   //INIT for serial communication
      Serial.begin(9600);
//      Serial2.begin(9600);

   //INIT for PWM with phase-correct with OCRA controlling the TOP value.
      DDRD = _BV(PD3);  //Set pin 3 (timer 2 OC2B) to OUTPUT mode.
      pinMode(19, INPUT_PULLUP);
      pinMode(18, INPUT_PULLUP);
      TCCR2A = _BV(COM2A1) | _BV(COM2B1) | _BV(WGM20);
      TCCR2B = _BV(CS22)  | _BV(WGM22);
      OCR2A = 125;
      OCR2B = 1;
      
      TCNT2 = 0;      //Reset counter
      
      /*
       * "When this bit (in TIMSK1) is written to '1', and the I-flag in the Status Register is set (interrupts globally enabled), the
       * Timer/Counter 1 Overflow interrupt is enabled. The corresponding Interrupt Vector is executed when the TOV Flag, located in TIFR1, is set."
       */
   //   TIMSK2 = 0x00;    //Reset TISMK
      TIMSK2 |= 0x01;   //Set TOIE=1

      /*
       * The setting of this flag is dependent of the WGM1[3:0] bits setting. In Normal and CTC modes, the TOV1
       * Flag is set when the timer overflows. Refer to the Waveform Generation Mode bit description for the TOV
       * Flag behavior when using another WGM1[3:0] bit setting.
       * TOV1 is automatically cleared when the Timer/Counter 1 Overflow Interrupt Vector is executed.
       * Alternatively, TOV1 can be cleared by writing a logic one to its bit location.
       */
    //  TIFR2 = 0x00;
      TIFR2 |= 0x01;    //Set TOV=1 

      int calcFreq = F_CPU/(2*64*OCR2A);
      float OCR2Btemp = OCR2B;
      float calcDuty = float(OCR2Btemp/OCR2A)*100;
      Serial.print("Frequency should be: ");
      Serial.println(calcFreq);
      Serial.print("Duty cycle should be: ");
      Serial.println(calcDuty);

      
   //init for force sensor
      ADMUX &= ~(1 << ADLAR);
      ADCSRA |= 0b10000111; 
      ADCSRA |= (1 << ADIE);    // Enable Interrupts 
      ADCSRB = 0; // Trigger for ADC is timer 1 compare match B                                            |
      SREG |= 0x80;   // Global interrupt enable flag 
      


      sei();
      //setPWM(4800, 60);
      
      stepRef = 20000;
}

void loop() {
    /*
     * Currently useless LED-code. May be used for testing later.
     */
     if(!digitalRead(19)){
      //Serial.println("HEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEJ");
      stepRef = 0;
     }
     else{
      stepRef = 10000;
     }

      if(!digitalRead(18)){
        pinMode(8, INPUT);
      }
      else{
        pinMode(8, OUTPUT);
      }
     
//    if(stepDiff <= 500){
//      stepRef = 1;
//    }
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
            closeGripper();
            serialSend();
            break;
          case 1:
            openGripper();
            serialSend();
            break;
          case 2:
            error();
            break;
          case 3:
            requestInfo();
            break;

          
       }
    }

    /*
     * The test-string (declared up top) is used in the MSG-parser function.
     */
     Serial.print("stepCounter: ");
     Serial.println(stepCounter);    
     Serial.print("stepDiff: ");
     Serial.println(stepDiff);   
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

ISR(TIMER2_OVF_vect){
  stepDiff = stepRef-stepCounter;
  
    if(stepDiff>0){ 
      if(stepState!=1){
        pinMode(standby,INPUT);
        digitalWrite(DIR1,HIGH);  digitalWrite(DIR2,LOW); //CCW
        stepState = 1;
      }
    stepCounter++;
    }
      
    else if (stepDiff<0){
      if(stepState!=-1){
        pinMode(standby,INPUT);
        digitalWrite(DIR2,HIGH);  digitalWrite(DIR1,LOW); //CW
        stepState = -1;
      }
    stepCounter--;
    }
    else if(stepDiff==0){
      if(stepState != 0){
        pinMode(standby,OUTPUT);
        stepState = 0;
      }
    }
}

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

void closeGripper(){
  
}

void openGripper(){
  
}

void requestInfo(){
  
}

void error(){
  
}

void setPWM(int freq, int duty){
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

