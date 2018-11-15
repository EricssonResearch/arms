// CommaDelimitedOutput sketch

void setup()
{
  Serial.begin(9600);
}

void loop()
{
  int ID = 1;    // some hardcoded values to send
  int len = 3;
  float fdata1 = 1000.372;
  char data1[20] = "";
  #//char* dtostrf(double __val, signed char __width, unsigned char __prec, char * __s);
  dtostrf(fdata1, 2, 2, data1);
  int data2 = 2000;
  int data3 = 3000;

  
  Serial.print(ID,DEC);
  Serial.print(",");
  Serial.print(len,DEC);
  Serial.print(",");
  Serial.print(data1);
  Serial.print(";");  // note that a comma is sent after the last field
  Serial.print(data2,DEC);
  Serial.print(";");
  Serial.print(data3,DEC);
  Serial.print("#");
  Serial.println();  // send a cr/lf
  delay(1000);
}
