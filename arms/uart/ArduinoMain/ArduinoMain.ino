#include "ARMS.h"
#include <Arduino.h>


// Pin 13 has an LED connected on most Arduino boards.
// give it a name:
const int led = 13;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
int ID = 0;
int* pID = &ID;
int fields;
int* pfields = &fields;
float Data[10];

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
 String temp = "";
 temp.reserve(20);
  //for(int i=0, i==input.length()-1, i++){
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
    int fieldCounter = 0;
    int len = input.length();
//    Serial.print("HEJ");
//    Serial.println();
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

