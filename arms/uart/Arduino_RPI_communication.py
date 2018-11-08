# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 14:24:37 2018

@author: esven
"""

import arms.config as c
# IF you get a error here, working on a windows machine, you need to create
# a environmental variable called PYTHONPATH and add the arms directory as value
# eg "C:\Uselfs\esven\Documents\GitHub\arms;"

import sys
import serial

# Module originates form the package pyserial, needs to be imported in order to
# work https://github.com/pyserial/pyserial

#Sending the data thorugh UART 
#UART PINOUT
#Rx -> GPIO15
#Tx -> GPIO14

#initialization and open the port

#possible timeout values:
#    1. None: wait forever, block call
#    2. 0: non-blocking mode, return immediately
#    3. x, x is bigger than 0, float allowed, timeout block call

#self = serial.serial()
#self.port = "/dev/ttyAMA0"          #Port for Uart, might need to be reconfigured on
#self.baudrate = 9600
#self.bytesize = serial.EIGHTBITS    #number of bits per bytes
#self.parity = serial.PARITY_NONE    #set parity check: no parity
#self.stopbits = serial.STOPBITS_ONE #number of stop bits
#self.timeout = None                 #block read
#self.timeout = 1                    #non-block read
#self.timeout = 2                    #timeout block read
#self.xonxoff = False                #disable software flow control
#self.rtscts = False                 #disable hardware (RTS/CTS) flow control
#self.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
#self.writeTimeout = 2               #timeout for write

#https://www.raspberrypi.org/documentation/configuration/uart.md
#https://radiostud.io/understanding-raspberrypi-uart-communication/
#https://stackoverflow.com/questions/21050671/how-to-check-if-device-is-connected-pyserial



class UART():
    
    def __init__(self):
        #Attribites for the class
        self.test
        self.serial = serial.Serial()
    #Methods of the class

    def load(self):
        '''Function that loads the configurations from the arms.config module.
        If the module can't be reached it will load default configurations.
        '''
        try:
            config = c.var.data['uart_config']
            self.port = config["port"]                  #Port for Uart, might need to be reconfigured 
            self.baudrate = config["baudrate"]
            self.bytesize = config["bytesize"]          #number of bits per bytes
            self.parity = config["parity"]              #set parity check: no parity
            self.stopbits = config["stopbits"]          #number of stop bits
            self.timeout = config["timeout"]                            
            self.xonxoff = config["xonxoff"]            #disable software flow control
            self.rtscts = config["rtscts"]              #disable hardware (RTS/CTS) flow control
            self.dsrdtr = config["dsrdtr"]              #disable hardware (DSR/DTR) flow control
            self.writeTimeout = config["writeTimeout"]  #timeout for write
        except(KeyError,TypeError):
            
            self.port = "/dev/ttyAMA0"          #Port for Uart, might need to be reconfigured on
            self.baudrate = 9600
            self.bytesize = serial.EIGHTBITS    #number of bits per bytes
            self.parity = serial.PARITY_NONE    #set parity check: no parity
            self.stopbits = serial.STOPBITS_ONE #number of stop bits
            self.timeout = 1                    #non-block read
            self.xonxoff = False                #disable software flow control
            self.rtscts = False                 #disable hardware (RTS/CTS) flow control
            self.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
            self.writeTimeout = 2               #timeout for write
        
        return
    
    def connect(self):
        
        return
    
    def disconnect(self):
        
        return
    def send(self):
        
        return
    
    def receive(self):
        
        return