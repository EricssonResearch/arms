//#include "ARMS.h"
#include <Arduino.h>


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
int ID;
int* pID = &ID;
int fields;
int* pfields = &fields;
float Data[10];
char fData[20];
/*
 * A test message of the type that the arduino will recieve is created.
 * First number will be the ID.
 * Second number will be the number of fields that the message will contain.
 * The rest of the numbers in the message (which are separated by semi-colons) are data-values that are to be
 * used in whatever function that is called with the ID.
 */
String test = "1,3,1.0;2;3.14;";
void setup() {
  //init led for testing
      pinMode(led, OUTPUT);

   //INIT of variables and functions for parseMSG
      inputString.reserve(200);//Reserve 200 bytes for message.
      temp.reserve(200); //Reserve 200 bytes for message.

   //INIT for serial communication
      Serial.begin(9600);
      Serial2.begin(9600);

   //init for interrupts stepper motor

   //init for interrupts force sensor
}

void loop() {
    /*
     * Currently useless LED-code. May be used for testing later.
     */
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
      Serial2.println("MESSAGE RECIEVED: " + inputString);
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

void parseMSG(String input){ 
 /*
  * A counter is initiated to be able to know where in the parsed string the parser is situated.
  * Then a for-loop iterates untill a comma is reached, which means that the ID-number has been parsed. The pointer
  * is referenced to the new value and temp gets reset again.
  * 
  * After this, the same is done for the fields-variable. Every for loop is ended with a counter++, which makes sure that the
  * next for loop doesnt begin with parsing any char twice.
  */
  Serial2.println("PROBE1");
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
        Serial2.println("appended to temp");
        temp += input[i];
      }
      else if(input[i]==';'){
        Serial2.println("appended to data");
        Data[fieldCounter] = temp.toFloat();
        fieldCounter++;
        temp = "";
      }
    }
      inputString = "";
      stringComplete = false;
}

