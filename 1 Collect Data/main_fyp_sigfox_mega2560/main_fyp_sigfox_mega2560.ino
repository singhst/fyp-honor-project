/*
  Final Year Project - RSSI-Based Sigfox Localization by using Machine Learning
  Version 1.0
  Created by HS Tam
  December 26, 2019.

  Last update on mmmm dd, 201x

  Using Xkit-Sample-master at URL https://github.com/Thinxtra/Xkit-Sample

  Functions,
  1. Receive SIM5320e GPS data from UART2 (TX2 pin16, RX2 pin17).
  2. Send the GPS to Sigfox network by Thinxtra Xkit through UART0 (TX0 pin1, RX0 pin0)
  
*/

#include <Wire.h>
#include <math.h>
#include <avr/wdt.h>
#include "WISOL.h"    //Interface for Sigfox library
#include "Tsensors.h" //For Sigfox Xkit onboard sensors
#include "SimpleTimer.h"
#include "Adafruit_FONA.h" //For 3G module SIM5320e
#include "Self_Function.h" //self defined

Isigfox *Isigfox = new WISOL();
Tsensors *tSensors = new Tsensors();
SimpleTimer timer;
int watchdogCounter;
uint8_t buttonCounter;
uint8_t PublicModeSF;
uint8_t stateLED;
uint8_t ledCounter;
const uint8_t buttonPin = A1;
const int redLED = 6;

//=============== Self variables <BEGIN> =============================================
// For 3G sim5320e
#define FONA_RST 4
HardwareSerial *fonaSerial = &Serial2;
Adafruit_FONA_3G fona = Adafruit_FONA_3G(FONA_RST);

uint16_t timeTick;
uint16_t timeTick_2;
uint32_t timeTick_3 = 99999999;
uint32_t timeTick_LED;
uint8_t stateInitSIM5320e; //0=false; 1=true
uint8_t stateLongPress; //0=false; 1=true
uint8_t stateButton; //0=false; 1=true
String sendMsg;
String replyMsg;
float latitude, longitude, speed_kph, heading, speed_mph, altitude;

typedef union{
  uint32_t number;
  uint8_t bytes[4];
} UINT32UNION_t;

//=============== Self variables <END> ===============================================

typedef union{
    float number;
    uint8_t bytes[4];
} FLOATUNION_t;

typedef union{
    uint16_t number;
    uint8_t bytes[2];
} UINT16_t;

typedef union{
    int16_t number;
    uint8_t bytes[2];
} INT16_t;

void setup() {
  int flagInit;

  Serial.begin(9600); // UART0, Xkit, Sigfox shield
//  Serial1.begin(9600); // UART1, Bluetooth module microchip RN4871
//  Serial3.begin(); // UART3, 3G module A9G pudding
    
  //=============== SELF setup <BEGIN> ================================================
  // Init Sigfox Xkit button
  stateButton = 0; //0=false; 1=true
  stateLongPress = 0;
  buttonCounter = 0;
  timeTick = 0;
  pinMode(buttonPin, INPUT);

  // Init 3G SIM5320e
  Serial.println("\n=== [Begin] Init 3G/GPS SIM5320e =======");
  fonaSerial->begin(115200); // UART2, 3G module SIM5320e
  if (! fona.begin(*fonaSerial)) { //if return false, 3G SIM5320e is not connected.
    stateInitSIM5320e = 0; //0=false
    Serial.println(F("Couldn't find SIM5320e"));
//    while(1);
  }
  else { //if return true, 3G SIM5320e is connected.
    stateInitSIM5320e = 1; //1=true
    // turn off Echo!
    fona.sendCheckReply("ATE0", "OK"); 
    delay(100);
    Serial.println(F("> Found SIM5320e"));
    Serial.println(F("> Restart GPS"));
    fona.sendCheckReply("AT+CGPS=0", "OK"); // Close GPS to change mode
    Serial.println(F("> Restarting..."));
    delay(4000);
    fona.sendCheckReply("AT+CGPS=1,2", "OK"); // Chnage to GPS-MS assit
  }
  Serial.println("=== [End] Init 3G/GPS SIM5320e =======\n\n");
  
  // Init LED
  stateLED = 0;
  ledCounter = 0;
  pinMode(redLED, OUTPUT);
  //=============== SELF setup <END> ==================================================

  // Init watchdog timer
  watchdogSetup();
  watchdogCounter = 0;

  Serial.println("=== [Begin] Init Sigfox Xkit =======");
  // WISOL test, WISOL = Interface for Sigfox library
  flagInit = -1;
  while (flagInit == -1) {
  Serial.println(""); // Make a clean restart
  delay(1000);
  PublicModeSF = 0;
  flagInit = Isigfox->initSigfox();
  Isigfox->testComms();
  GetDeviceID();
  //Isigfox->setPublicKey(); // set public key for usage with SNEK
  }
  Serial.println("=== [End] Init Sigfox Xkit =======\n");
  
  Serial.println("========= Programe begin =========");
  
  // Init timer to send a Sigfox message every 10 minutes
//  unsigned long sendInterval = 600000;
//  timer.setInterval(sendInterval, timeIR);

  BlinkLED();
  pinMode(redLED, OUTPUT);
  Serial.println(""); // Make a clean start
  delay(1000);
}

void loop() {
  timer.run();
  
  //======== SELF loop FUNCTIONS <BEGIN> =====================
  // Checking the state of the onboard button (Sigfox Xkit)
  // If the button is -- short-pressed, send GPS 
  //                  |__ long-pressed, get xxx xxx
  timeTick++;
  timeTick_2++;
//  // Blinks LED to show arduino is running
//  timeTick_LED++; 
//  if(timeTick_LED > 15000) {
//    pinMode(redLED, OUTPUT);
//    digitalWrite(redLED, HIGH);
//  }
//  if(timeTick_LED > 30000) {
//    timeTick_LED = 0;
//    digitalWrite(redLED, LOW);
//    pinMode(redLED, INPUT);
//  }

  if(timeTick>3000) { // Don't want to check state of the button too frequently
    timeTick = 0;
//    Serial.println(digitalRead(buttonPin)); // Uncomment to debug
    if(digitalRead(buttonPin) == 0) { // If the button is pressed
      buttonCounter++;
      if(buttonCounter >= 5) {
        BlinkLED();
        pinMode(redLED, OUTPUT);
      }
    } else if(digitalRead(buttonPin) == 1) { // If the button is NOT pressed
        if(buttonCounter > 0) {
          if(buttonCounter < 5) {
          Serial.println("> Short press");
          buttonCounter = 0;
          BlinkLED();
          pinMode(redLED, OUTPUT);
          CheckSendGPS();     
        } else if(buttonCounter >= 5) {
          Serial.println("> Long press");
          buttonCounter = 0;
          Serial.println("stateLongPress=");
          Serial.println(stateLongPress);
          if (!stateLongPress){
            Serial.println("> Enable \"repeatedly sending msg\" Mode");
            stateLongPress = 1;
          } else {
            stateLongPress = 0; //Disable "repeatedly sending msg" mode
          }
          Serial.println(stateLongPress);
          //xxxx();
        }
      }
    }
  }

  //"repeatedly sending msg" mode
  if(stateLongPress) {
    timeTick_3++;
    if(timeTick_3 > 200000) { // Don't want to check too frequently
      timeTick_3 = 0;
      Serial.println("> Repeatedly sending......");
      CheckSendGPS();
    } 
  }

  // If the button is NOT pressed, show RSSI after some time
  if(digitalRead(buttonPin) == 1) {
    if(timeTick_2 > 60000) { // Don't want to check too frequently
      timeTick_2 = 0;
      Serial.println("> RSSI");
//      fona.sendCheckReply("AT+CSQ", "OK");
    }
  }

  //======== SELF loop FUNCTIONS <END> =======================
  
  wdt_reset(); // Because arduino didn't hang, reset watch dog timer 
  watchdogCounter = 0; // and set watchdog counter to zero
}

//=============== Self functions <BEGIN> ===============================================
void CheckSendGPS() {
  boolean gps_success = fona.getGPS(&latitude, &longitude, &speed_kph, &heading, &altitude);
  if (gps_success) {
    Serial.print("GPS lat:");
    Serial.println(latitude, 6);
    Serial.print("GPS long:");
    Serial.println(longitude, 6);
    Serial.print("GPS speed KPH:");
    Serial.println(speed_kph);
    Serial.print("GPS speed MPH:");
    speed_mph = speed_kph * 0.621371192;
    Serial.println(speed_mph);
    Serial.print("GPS heading:");
    Serial.println(heading);
    Serial.print("GPS altitude:");
    Serial.println(altitude);
  } else {
    // If can't receive GPS signal send this (22.168598, 113.910168)
    // 近Tai a Chau Landing No. 2 大鴉洲2號梯台
    latitude = 22.168598;
    longitude = 113.910168;
    Serial.println("Waiting for FONA GPS 3D fix...");
    Serial.print("GPS lat:");
    Serial.println(latitude, 6);
    Serial.print("GPS long:");
    Serial.println(longitude, 6);
  }
  
  const uint8_t payloadSize = 12; //in bytes
//  byte* buf_str = (byte*) malloc (payloadSize);
  uint8_t buf_str[payloadSize];
  
  UINT32UNION_t hex_latitude, hex_longitude;
  hex_latitude.number = (latitude*1000000.0);
  hex_longitude.number = (longitude*1000000.0);
  
  buf_str[0] = hex_latitude.bytes[3];
  buf_str[1] = hex_latitude.bytes[2];
  buf_str[2] = hex_latitude.bytes[1];
  buf_str[3] = hex_latitude.bytes[0];
  buf_str[4] = hex_longitude.bytes[3];
  buf_str[5] = hex_longitude.bytes[2];
  buf_str[6] = hex_longitude.bytes[1];
  buf_str[7] = hex_longitude.bytes[0];
  buf_str[8] = 0;  // free to use
  buf_str[9] = 0;  //
  buf_str[10] = 0; //
  buf_str[11] = 0; //

//  for(int i = sizeof(hex_latitude.bytes)-1; i>=0 ;i--) { //For debugging
//    Serial.println(hex_latitude.bytes[i], HEX);
//  }
  Serial.println("> Sending to Sigfox ...");
  Send_Pload(buf_str, payloadSize);
//  free(buf_str);
  Serial.println("> Sent");
}


//=============== Self functions <END> ==================================================


void BlinkLED() {
  ledCounter++;
  if (ledCounter<=6) {
    if (stateLED == 0){
      digitalWrite(redLED, HIGH);
      stateLED = 1;
      timer.setTimeout(200, BlinkLED);
    } else {
      digitalWrite(redLED, LOW);
      stateLED = 0;
      timer.setTimeout(200, BlinkLED);
    }
  } else {
    pinMode(redLED, INPUT);
    ledCounter = 0;
  }
}


void Send_Pload(uint8_t *sendData, const uint8_t len){
  // No downlink message require
  recvMsg *RecvMsg;

  RecvMsg = (recvMsg *)malloc(sizeof(recvMsg));
  Isigfox->sendPayload(sendData, len, 0, RecvMsg);
  for (int i = 0; i < RecvMsg->len; i++) {
    Serial.print(RecvMsg->inData[i]);
  }
  Serial.println("");
  free(RecvMsg);


  // If want to get blocking downlink message, use the folling block instead
  /*
  recvMsg *RecvMsg;

  RecvMsg = (recvMsg *)malloc(sizeof(recvMsg));
  Isigfox->sendPayload(sendData, len, 1, RecvMsg);
  for (int i=0; i<RecvMsg->len; i++){
    Serial.print(RecvMsg->inData[i]);
  }
  Serial.println("");
  free(RecvMsg);
  */

  // If want to get non-blocking downlink message, use the folling block instead
  /*
  Isigfox->sendPayload(sendData, len, 1);
  timer.setTimeout(46000, getDLMsg);
  */
}

// For Sigfox Xkit
void GetDeviceID(){
  recvMsg *RecvMsg;
  const char msg[] = "AT$I=10";

  RecvMsg = (recvMsg *)malloc(sizeof(recvMsg));
  Isigfox->sendMessage(msg, 7, RecvMsg);

  Serial.print("Device ID: ");
  for (int i=0; i<RecvMsg->len; i++){
    Serial.print(RecvMsg->inData[i]);
  }
  Serial.println("");
  free(RecvMsg);
}


void watchdogSetup(void) { // Enable watchdog timer
  cli();  // disable all interrupts
  wdt_reset(); // reset the WDT timer
  /*
   WDTCSR configuration:
   WDIE = 1: Interrupt Enable
   WDE = 1 :Reset Enable
   WDP3 = 1 :For 8000ms Time-out
   WDP2 = 1 :For 8000ms Time-out
   WDP1 = 1 :For 8000ms Time-out
   WDP0 = 1 :For 8000ms Time-out
  */
  // Enter Watchdog Configuration mode:
  // IF | IE | P3 | CE | E | P2 | P1 | P0
  WDTCSR |= B00011000;
  WDTCSR = B01110001;
//  WDTCSR |= (1<<WDCE) | (1<<WDE);
//  // Set Watchdog settings:
//   WDTCSR = (1<<WDIE) | (1<<WDE) | (1<<WDP3) | (1<<WDP2) | (1<<WDP1) | (1<<WDP0);
  sei();
}


void watchdog_disable() { // Disable watchdog timer
  cli();  // disable all interrupts
  WDTCSR |= B00011000;
  WDTCSR = B00110001;
  sei();
}


ISR(WDT_vect) // Watchdog timer interrupt.
{
// Include your code here - be careful not to use functions they may cause the interrupt to hang and
// prevent a reset.
  Serial.print("WD reset: ");
  Serial.println(watchdogCounter);
  watchdogCounter++;
  if (watchdogCounter == 20) { // reset CPU after about 180 s
      // Reset the CPU next time
      // Enable WD reset
      cli();  // disable all interrupts
      WDTCSR |= B00011000;
      WDTCSR = B01111001;
      sei();
      wdt_reset();
  } else if (watchdogCounter < 8) {
    wdt_reset();
  }
}
