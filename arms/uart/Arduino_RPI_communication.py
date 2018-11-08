# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 14:24:37 2018

@author: esven
"""

from arms.config import config as c
from arms.utils.log import ard_log
# IF you get a error here, working on a windows machine, you need to create
# a environmental variable called PYTHONPATH and add the arms directory as value
# eg "C:\Uselfs\esven\Documents\GitHub\arms;"

import sys
import serial
import time
import threading

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

class GetHWPoller(threading.Thread):
    """ thread to repeatedly poll hardware
    sleeptime: time to sleep between pollfunc calls
    pollfunc: function to repeatedly call to poll hardware"""

    def __init__(self,sleeptime,pollfunc):

        self.sleeptime = sleeptime
        self.pollfunc = pollfunc  
        threading.Thread.__init__(self)
        self.runflag = threading.Event()  # clear this to pause thread
        self.runflag.clear()

    def run(self):
        self.runflag.set()
        self.worker()

    def worker(self):
        while(1):
            if self.runflag.is_set():
                self.pollfunc()
                time.sleep(self.sleeptime)
            else:
                time.sleep(0.01)

    def pause(self):
        self.runflag.clear()

    def resume(self):
        self.runflag.set()

    def running(self):
        return(self.runflag.is_set())

    def kill(self):
        print("WORKER END")
        sys.stdout.flush()
        self._Thread__stop()


class HW_Interface(object):
    """Class to interface with asynchrounous serial hardware.
    Repeatedly polls hardware, unless we are sending a command
    "ser" is a serial port class from the serial module """

    def __init__(self,ser,sleeptime):
        self.ser = ser
        self.sleeptime = float(sleeptime)
        self.worker = GetHWPoller(self.sleeptime,self.poll_HW)
        self.interlock = False  # set to prohibit thread from accessing serial port
        self.response = None # last response retrieved by polling
        self.worker.start()
        self.callback = None
        self.verbose = True # for debugging

    def register_callback(self,proc):
        """Call this function when the hardware sends us serial data"""
        self.callback = proc
        #self.callback("test!")

    def kill(self):
        self.worker.kill()


    def write_HW(self,command):
        """ Send a command to the hardware"""
        while self.interlock: # busy, wait for free, should timout here 
            print("waiting for interlock")
            sys.stdout.flush()
            
        self.interlock = True
        self.ser.write(command + "\n")
        self.interlock = False

    def poll_HW(self):
        """Called repeatedly by thread. Check for interlock, if OK read HW
        Stores response in self.response, returns a status code, "OK" if so"""
        if self.interlock:
            if self.verbose: 
                print("poll locked out")
                self.response = None
                sys.stdout.flush()   
            return "interlock" # someone else is using serial port, wait till done!
        self.interlock = True # set interlock so we won't be interrupted
        # read a byte from the hardware
        response = self.ser.read(1)
        self.interlock = False
        if response:
            if len(response) > 0: # did something write to us?
                response = response.strip() #get rid of newline, whitespace
                if len(response) > 0: # if an actual character
                    if self.verbose:
                        self.response = response
                        print("poll response: " + self.response )
                        sys.stdout.flush()
                    if self.callback:
                        #a valid response so send it
                        self.callback(self.response)
                return "OK"
            return "null" # got no response


def my_callback(response):
    """example callback function to use with HW_interface class.
    Called when the target sends a byte, just print it out
    
    Expected message back from the Arduino is simply 1 for DONE and
    2 for ERROR. It is up to the rPi to keep track of where the error came 
    and thus deduct which step is not completed.
    """
    if response[0] == 1:
        ard_log.info("Command completed")
    elif response[0] == 2:
        ard_log.error("Command failed")


class Arduino():
    
    def __init__(self):
        #Attribites for the class
        self.command = ""
        self.load()
        #self.serial = serial.Serial()
    #Methods of the class

    def load(self):
        '''Function that loads the configurations from the arms.config module.
        If the module can't be reached it will load default configurations.
        '''
        try:
            config = c.var.data["uart_config"]
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
            self.sleeptime = config["sleeptime"]        #sets the time between message polling
            ard_log.info("Loaded configurations")
        except(KeyError,TypeError):
            
            self.port = "COM3"          #Port for Uart, might need to be reconfigured on
            self.baudrate = 9600
            self.bytesize = serial.EIGHTBITS    #number of bits per bytes
            self.parity = serial.PARITY_NONE    #set parity check: no parity
            self.stopbits = serial.STOPBITS_ONE #number of stop bits
            self.timeout = 1                    #non-block read
            self.xonxoff = False                #disable software flow control
            self.rtscts = False                 #disable hardware (RTS/CTS) flow control
            self.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
            self.writeTimeout = 2               #timeout for write
            self.sleeptime = 0.1;               #sets the time between message polling
            ard_log.error("Could not load configurations, using default values")
        #ard_log.error('Hello')
        return
    
    def connect(self):
        try:
            #Creates the serial connection to the Arduino as specified in the config file
            self.serial = serial.Serial(port = self.port, baudrate = self.baudrate, 
                                    bytesize = self.bytesize, parity = self.parity, 
                                    stopbits = self.stopbits, timeout = self.timeout,
                                    xonxoff = self.xonxoff, rtscts = self.rtscts, 
                                    dsrdtr = self.dsrdtr, writeTimeout = self.writeTimeout)
           
        except serial.SerialException as e:
            ard_log.error(e)
            print("except serial.SerialException as e")
        
        except ValueError as e:
            ard_log.error(e)
            print("except ValueError as e")
            
            
            
        try:
             #Creates thread that listens to the Arduino
             self.hw = HW_Interface(self.serial,self.sleeptime)
        except:
            print("Hello")
            
            
        return
    
    def disconnect(self):
        self.serial.close()
        return
    
    def send(self):
        
        return
    
    def receive(self):
        
        return
    