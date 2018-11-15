#include "ARMS.h"
#include <Arduino.h>


// Pin 13 has an LED connected on most Arduino boards.
// give it a name:
const int led = 13;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete

/*
 * The variable for ID, fields and the Data-array are created with their corresponding pointers.
 */
int ID;
int* pID = &ID;
int fields;
int* pfields = &fields;
float Data[10];

/*
 * A test message of the type that the arduino will recieve is created.
 * First number will be the ID.
 * Second number will be the number of fields that the message will contain.
 * The rest of the numbers in the message (which are separated by semi-colons) are data-values that are to be
 * used in whatever function that is called with the ID.
 */
String test = "1,3,1.0;2;3.14#";
void setup() {
  pinMode(led, OUTPUT);
  /*
   * Reserve 20 bytes for message.
   */
  inputString.reserve(20); 
   Serial.begin(9600);
}

void loop() {
    
    /*
     * Currently useless LED-code. May be used for testing later.
     */
    if (stringComplete) {
      if (inputString[0] == '0') {
        digitalWrite(led, LOW);
      }
      else {
        //Serial.println("on!"); 
        digitalWrite(led, HIGH);
      }

    
      
    // clear the string:
    inputString = "";
    stringComplete = false;
    }

    /*
     * The test-string (declared up top) is used in the MSG-parser function.
     */
    parseMSG(test);
    Serial.print(ID);
    Serial.print(",");
    Serial.print(fields);
      for(int i=0; i < fields; i++){
        Serial.print(Data[i]);
      }
    Serial.println();
    delay(1000);
    
    
}

void serSend(String s){
  
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
    } 
  }
}



void parseMSG(String input){
 
 //A temporary string to use for parsing is created and 20 bytes gets reserved for it.
  
 String temp = "";
 temp.reserve(20);

 /*
  * A counter is initiated to be able to know where in the parsed string the parser is situated.
  * Then a for-loop iterates untill a comma is reached, which means that the ID-number has been parsed. The pointer
  * is referenced to the new value and temp gets reset again.
  * 
  * After this, the same is done for the fields-variable. Every for loop is ended with a counter++, which makes sure that the
  * next for loop doesnt begin with parsing any char twice.
  */
  int counter = 0;
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
    int fieldCounter = 0;
    int len = input.length();
    while(counter<len) {

    Serial.print("temp");    
    Serial.print(temp);
    Serial.println();
      
      for(int i = counter; input[i] !=';'; i++){
        if(input[i]=='#'){
          break;
        }
        temp += input[i];
        counter ++;
            Serial.print("tempnext");    
            Serial.print(temp);
            Serial.println();    
    }

      Data[fieldCounter] = temp.toFloat();
          Serial.print("fieldcounter");    
          Serial.print(Data[fieldCounter]);
          Serial.println();
      temp = "";
      counter++;
      fieldCounter++;
    }

  
}

