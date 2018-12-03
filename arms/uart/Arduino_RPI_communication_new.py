# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 15:37:27 2018

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
from threading import Event

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
      pollfunc: function to repeatedly call to poll hardware
    """
    def __init__(self,sleeptime,pollfunc):
    
        self.sleeptime = sleeptime
        self.pollfunc = pollfunc  
        threading.Thread.__init__(self)
        self.runflag = threading.Event()  # clear this to pause thread
        self.runflag.clear()
        self.aliveflag = threading.Event() # added a flag to kill thread, clear this to kill thread
        self.aliveflag.set()
      
    def run(self):
        self.runflag.set()
        self.worker()

    def worker(self):
        while(self.aliveflag.is_set()):
            if self.runflag.is_set():
                self.pollfunc()
                time.sleep(self.sleeptime)
            else:
                time.sleep(self.sleeptime)

    def pause(self):
        self.runflag.clear()

    def resume(self):
        self.runflag.set()

    def running(self):
        return(self.runflag.is_set())

    def kill(self):
        ard_log.info("WORKER END")
        sys.stdout.flush()
        self.aliveflag.clear() # kills the thread
        self.join()



class Arduino():
    """Class to interface with asynchrounous serial hardware.
    Repeatedly polls hardware, unless we are sending a command
    "ser" is a serial port class from the serial module """
    def __init__(self):
        #Initialization for thread
        self.interlock = False  # set to prohibit thread from accessing serial port
        self.response = None # last response retrieved by polling
        self.callback = None
        self.verbose = True # for debugging

        #Attributes for the class
        self.command = ""
        self.load()
        self.connect()
        
        #Attributes of the sent message
        self.ID_sent = ""
        self.fields_sent = ""
        self.data_sent = ""
        
        #Attributes 
        
        #Attributes for the received message
        self.ID_received = ""
        self.fields_received = ""
        self.data_received = ""
        
        #Attributes for open and close Gripper
        self.pulses_sent = 0
        self.pressure_sent = 0       
        self.pulses_received = 0
        self.pressure_received = 0
        self.pressure_error= False  
        
        #Attributes for precision
        
        '''
        The thought behind the precision measurement is the following:
        lower_bound * pressure_sent - lower_bias < pressure_received < upper_bound*pressure_sent + upper_bias
        
        Which is basically saying that the lower number of pulses/pressure inputed, the more error we accept.
        
        example with a low number:
            input: 10 with bound +/-10% and bias of 5
            
            this would yield an acceptable interval where no flags are triggered accordingly:
                9-5 = 4 < output < 11+5 =16  which gives a relative error of 60%
        
        example with a high number
            input: 400 with bound +/-10% and bias of 5
            this would yield an acceptable interval where no flags are triggered accordingly:
                360-5 = 355 < output < 440+5 = 445 which gives a relative error of 11,25%
                
        The inference is that when dealing with low pressure/pules we can't do that much damages whilst
        with high pressures/pulses a lot can go wrong hence we need to be more strict. what controls the ratio is
        the trade-off between bias and the bound constant.
            
        '''
        self.adjustment_pulses = 100 #number of pulses to send when adjusting
        self.upper_bound = 1.1 #adjusts the acceptable upper bound relative error 
        self.upper_bias = 5 #Bias limit on 
        self.lower_bound = 0.9 #adjust the acceptable lower bound
        self.lower_bias = 5 #Bias limit 
        
        self.pulses = 0 #Global pulses
        self.pressure = 0 #Global pressure
        
        #Flags/counters for open and close gripper
        self.adjust_counter = 0
        self.pulseLow = False
        self.pressureLow = False
        self.pressureHigh = False
        self.obstacleFlag = False
        self.max_recursion = 5 #determines the maximum number of adjustments in the command
        
        #Attributes for Solenoid
        self.solenoid_active = 0 #boolen if solenoid is active or not
        
        
        


    def register_callback(self,proc):
        """Call this function when the hardware sends us serial data"""
        self.callback = proc
        #self.callback("test!")
    def pause(self):
        """Call this function to pause the polling thread"""
        self.worker.pause()
        
    def resume(self):
        """Call this function to resume the polling thread"""
        self.worker.resume()

    def kill(self):
        """Call this function to end the polling thread"""
        self.worker.kill()


    def write_HW(self,command):
        """ Send a command to the hardware"""
        while self.interlock: # busy, wait for free, should timout here 
            #print("in write_HW: waiting for interlock")
            #ard_log.info("in write_HW: waiting for interlock")
            time.sleep(self.sleeptime)
            sys.stdout.flush()
        #implementation of a primitive semaphore    
        self.interlock = True
        self.ser.write(bytes(command + "\n", "utf-8"))
        self.interlock = False

    def poll_HW(self):
        """Called repeatedly by thread. Check for interlock, if OK read HW
        Stores response in self.response, returns a status code, "OK" if so"""
        if self.interlock:
            if self.verbose: 
                #print("in poll_HW: poll locked out")
                ard_log.debug("in poll_HW: poll locked out")
                self.response = None
                sys.stdout.flush()   
            return "interlock" # someone else is using serial port, wait till done!
        self.interlock = True # set interlock so we won't be interrupted
        # read  message until \n is encountered
        response = self.ser.read_until()
        self.interlock = False
        if response:
            if len(response) > 0: # did something write to us?
                response = response.strip() #get rid of newline, whitespace
                if len(response) > 0: # if an actual character
                    if self.verbose:
                        self.response = response.decode("utf-8") #added decode for python 3
                        ard_log.debug("poll response: " + self.response )
                        self.evaluate_response()
                        sys.stdout.flush()
                    if self.callback:
                        #a valid response so send it
                        self.callback(self.response)
                return "OK"
            return "null" # got no response        

    #Methods of the class

    def load(self):
        '''Function that loads the configurations from the arms.config module.
        If the module can't be reached it will load default configurations.
        '''
        try:
            UART_config = c.var.data["uart_config"]
            ARDUINO_config = c.var.data["arduino_config"]
            
            self.port = UART_config["port"]                  #Port for Uart, might need to be reconfigured 
            self.baudrate = UART_config["baudrate"]
            self.bytesize = UART_config["bytesize"]          #number of bits per bytes
            self.parity = UART_config["parity"]              #set parity check: no parity
            self.stopbits = UART_config["stopbits"]          #number of stop bits
            self.timeout = UART_config["timeout"]                            
            self.xonxoff = UART_config["xonxoff"]            #disable software flow control
            self.rtscts = UART_config["rtscts"]              #disable hardware (RTS/CTS) flow control
            self.dsrdtr = UART_config["dsrdtr"]              #disable hardware (DSR/DTR) flow control
            self.writeTimeout = UART_config["writeTimeout"]  #timeout for write
            self.sleeptime = UART_config["sleeptime"]        #sets the time between message polling
            
            self.adjustment_pulses = ARDUINO_config['adjustment_pulses'] #number of pulses to send when adjusting
            self.upper_bound = ARDUINO_config['upper_bound'] #adjusts the acceptable upper bound relative error 
            self.upper_bias =  ARDUINO_config['upper_bias'] #Bias limit on 
            self.lower_bound = ARDUINO_config['lower_bound'] #adjust the acceptable lower bound
            self.lower_bias = ARDUINO_config['lower_bias'] #Bias limit 
            self.max_recursion = ARDUINO_config['max_recursion'] #determines the maximum number of adjustments in the command
            ard_log.info("Loaded configurations")
        except(KeyError,TypeError):
            
            self.port = "COM6"          #Port for Uart, might need to be reconfigured on
            self.baudrate = 9600
            self.bytesize = serial.EIGHTBITS    #number of bits per bytes
            self.parity = serial.PARITY_NONE    #set parity check: no parity
            self.stopbits = serial.STOPBITS_ONE #number of stop bits
            self.timeout = 1                    #non-block read
            self.xonxoff = False                #disable software flow control
            self.rtscts = False                 #disable hardware (RTS/CTS) flow control
            self.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
            self.writeTimeout = 2               #timeout for write
            self.sleeptime = 1;               #sets the time between message polling 0.1 is good maybe
            ard_log.error("Could not load configurations, using default values")
        
        
        return
    '''
    This section of the Code handles the connect and disconnect to the Arduino.
    Connect is creating an instance self.ser of the class serial.Serial() using
    the parameters loaded from self.load(). after the connect
    '''
    
    def connect(self):
        try:
            #Creates the serial connection to the Arduino as specified in the config file
            #print("creating serial stuff here - Arduino_RPI_comm line 230")
            ard_log.info("Connecting to port: %s with baudrate: %s" %(self.port, self.baudrate) )
            self.ser = serial.Serial(port = self.port, baudrate = self.baudrate, 
                                    bytesize = self.bytesize, parity = self.parity, 
                                    stopbits = self.stopbits, timeout = self.timeout,
                                    xonxoff = self.xonxoff, rtscts = self.rtscts, 
                                    dsrdtr = self.dsrdtr, writeTimeout = self.writeTimeout)
            
            self.worker = GetHWPoller(self.sleeptime,self.poll_HW)
            self.worker.start()
            
        except serial.SerialException as e:
            ard_log.error(e)
            print("except serial.SerialException as e")
        
        except ValueError as e:
            ard_log.error(e)
            print("except ValueError as e")
   
            
    def disconnect(self):
        ard_log.info("Disconnected from port %s" %(self.port))
        self.kill() #ends the listner thread
        self.ser.close() #closes the serial connection
        return
    
    def send(self,val):
        val = str(val)
        #self.message_sanity_check(val,"send")
        ard_log.debug("sending message " + val)
        sys.stdout.flush()
        self.write_HW(val)
        
    
    def receive(self):
        ard_log.info('Last response: "%s"' % self.response)
        if self.response != None:
            
            msg = self.response.split(",")
            self.ID_received = msg[0]
            self.fields_received = msg[1]
            self.data_received = msg[2].strip("#").split(";")
        ard_log.info('Received - msg_id:%s, num_fields:%s'%(self.ID_received,self.fields_received))
        return
    

    '''
    In this section of the code you add the different commands to be interpreted
    and acted upon by the raspberry pi. To add a new command, simply define a new 
    method in the class according to the syntax command_*what you wanna do* and 
    add the class in the function_vec as self.command_*what you wanna do*. The data
    is stored in a number of fields given by self.fields attribute and provided
    by the self.data list. The command ID is given by the index in function_vec.
    
    The logic behind this section is as follows:
        When sending messages, the message ID implies what function should be run,
        e.g. ID = 1 means that the gripper should be closed. This in turn requires
        certain datapoints to be sent, e.g. how many pulses, what direction, 
        final reading of pressure sensor etc, which is specified in the message.
        
        The Arduino will reply with the same message ID to make sure that the answer 
        relates to the sent message. The number of data points sent back ought to
        include at least the data points originally sent, but may contain more information.
        In the example above, it could be the readings from the current sensor.
        
        The returned message should then be compares to the sent message, and if
        the data received matches the data sent, it will be itnerpreted as successful.
        Otherwise, an error will be raised which may incur corrections to be made.
        This final step of the evaluation will be very catered to what function was run.
    '''
    def evaluate_response(self):
        
        if (self.response != None):
            msg = self.response.split(",")
            self.ID_received = msg[0]
            #print("printing msg[0]" + msg[0])
            self.fields_received = msg[1]
            self.data_received = msg[2].strip("#").split(";")
            print(self.data_received)                                                                                     ##PRINTING HERE
            ard_log.info('Received - msg_id:%s, num_fields:%s'%(self.ID_received,self.fields_received))
            
            
            function_vec = [self.command_close, self.command_open,self.command_activate_solenoid, self.command_deactivate_solenoid, self.command_acknowledge_error, self.command_request_info]
            #function_ID  = [        "0"      ,         "1"      ,              "2"             ,               "3                ,                  "4"          ,            "5"           ]
            function_vec[int(self.ID_received)]() #Execute the function given by the command
            ard_log.info('Executed Command %s'%(self.ID_received))
            
        return True
    
    def command_close(self):
        '''
        This subfunction checks that the data received matches the data sent. If that is the case
        the command is deemed successful. Otherwise, it checks what went wrong and logs this.
        A little bit of slack is introduced so that the executed number of pulses and force is between
        self.lower_bound*sent < executed < self.upper_bound*sent. This probably should be refined
        
        Received message should be: data_received = [pulses, pressure, pressureError, currentError]
        '''
        
        #print(self.data_received)
        
        self.pulses_received = int(self.data_received[0])
        self.pressure_received = int(self.data_received[1])
        self.pressure_error = int(self.data_received[2])
        
        #update the global variables
        self.pressure = self.pressure_received
        self.pulses += self.pulses_received
        
        #Set appropriate flags that tell which situation we're in
        self.pulseLow = (self.pulses_sent < self.pulses_received)
        
        self.pressureLow = (self.lower_bound*self.pressure_sent - self.lower_bias >= self.pressure_received)
        self.pressureHigh = (self.upper_bound*self.pressure_sent + self.upper_bias <= self.pressure_received)
                
        #Notify close_gripper that a response has been received               
        self.Arduino_replied = True
        return
    
    def command_open(self):
        '''
        This subfunction checks that the data received matches the data sent. If that is the case
        the command is deemed successful. Otherwise, it checks what went wrong and logs this.
        A little bit of slack is introduced so that the executed number of pulses and force is between
        self.lower_bound*sent < executed < self.upper_bound*sent. This probably should be refined
        
        Received message should be: data_received = [pulses, pressure, pressureError, currentError]
        '''
        
        #print(self.data_received)
        
        self.pulses_received = int(self.data_received[0])
        self.pressure_received = int(self.data_received[1])
        self.pressure_error = int(self.data_received[2])
        
        #update the global variables
        self.pressure = self.pressure_received
        self.pulses -= self.pulses_received
        
        
        #Set appropriate flags that tell which situation we're in
        self.pulseLow = (self.pulses_sent < self.pulses_received)
        
        self.pressureLow = (self.lower_bound*self.pressure_sent - self.lower_bias >= self.pressure_received)
        self.pressureHigh = (self.upper_bound*self.pressure_sent + self.upper_bias <= self.pressure_received)
                
        #Notify close_gripper that a response has been received               
        self.Arduino_replied = True
        return
    
    def command_activate_solenoid(self):
        self.solenoid_active = int(self.data_received[0])
        #Notify that a response has been received               
        self.Arduino_replied = True
        return       
    
    def command_deactivate_solenoid(self):
        self.solenoid_active = int(self.data_received[0])
        #Notify close_gripper that a response has been received               
        self.Arduino_replied = True
        return
    
    def command_acknowledge_error(self):
        self.pressure_error = int(self.data_received[0])
        self.Arduino_replied = True
        return
        
    def command_request_info(self):
        self.pressure_received = float(self.data_received[0])
        ard_log.info("Pressure at this time is: %s" %(self.data_received[0])  )
        self.Arduino_replied = True
        return      

    def close_gripper(self,pulses,pressure):
        '''
        This command will close the gripper completely and make sure that the force between pinchers reaches 24N, given the slack allowed in command_close.
        It creates a message as follows: [ID, length, pulses, pressure]
        '''
        
        #Saves the relevant information into variables to be compared with when a response from the arduino comes
        self.command = "Close Gripper"
        self.pulses_sent = pulses
        self.pressure_sent = pressure
        self.ID_sent = 0

        #constructing and sending message to the arduino
        msg = str(self.ID_sent) + "," + str(2) + "," + str(self.pulses_sent) + ";" + str(self.pressure_sent) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(3.0) #creates a new thread that acts as a timer to reduce CPU useage
            #ard_log.debug("inside the wait timer thingy")
            
        #Make sure that we don't get stuck in too many recursions
        if(self.adjust_counter >= self.max_recursion):
            self.obstacleFlag = True
            ard_log.error("in function: "+self.command+" Maximum number of recursion reached")
            self.adjust_counter = 0;
            return
        #reply from arduino has been compared, and different flags have been set accordingly.
        #depending on combination of flags, a certain case is true, and possible adjustments made
        if(not self.pulseLow and not self.pressureLow and not self.pressureHigh):
            ard_log.debug("Command successful")
            self.adjust_counter = 0;
            return
        
        elif(not self.pulseLow and self.pressureLow and not self.pressureHigh):
            ard_log.debug("in function: "+self.command+" Pressure_received " + str(self.pressure_received) + " lower than Pressure_sent " + str(self.pressure_sent) + " , adjusting by closing")
            self.adjust_counter = self.adjust_counter + 1
            self.close_gripper(self.adjustment_pulses,self.pressure_sent)
            return
        
        elif(not self.pulseLow and not self.pressureLow and self.pressureHigh):
            ard_log.debug("in function: "+self.command+ "Pressure_received " + str(self.pressure_received) + " higher than Pressure_sent " + str(self.pressure_sent) + " , adjusting by opening")
            self.adjust_counter = self.adjust_counter + 1
            self.open_gripper(self.adjustment_pulses,self.pressure_sent)
            return
        
        elif(self.pulseLow):
            self.obstacleFlag = True
            ard_log.error("in function: "+self.command+" Obstacle error, cease operation\n Flags: pulseLow:%r pressureLow:%r pressureHigh:%r" %(self.pulseLow,self.pressureLow,self.pressureHigh))
            return      
        
        else:
            ard_log.debug("in function: "+self.command+" Jumping into else, some undefined case")
            print("self.pulseLow, self.pressureLow, self.pressureHigh \n")
            print(self.pulseLow, self.pressureLow, self.pressureHigh)
            print("data_sent \n")
            print(self.data_sent)
            print("data_received \n")
            print(self.data_received)
            return
        
    def open_gripper(self,pulses,pressure):
        '''
        This command will close the gripper completely and make sure that the force between pinchers reaches 24N, given the slack allowed in command_close.
        It creates a message as follows: [ID, length, pulses; pressure;]
        '''
        
        #Saves the relevant information into variables to be compared with when a response from the arduino comes
        self.command = "Open Gripper"
        self.pulses_sent = pulses
        self.pressure_sent = pressure
        self.ID_sent  = 1

        #constructing and sending message to the arduino
        msg = str(self.ID_sent) + "," + str(2) + "," + str(self.pulses_sent) + ";" + str(self.pressure_sent) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(3.0) #creates a new thread that acts as a timer to reduce CPU useage
            #ard_log.debug("inside the wait timer thingy")
        
        #Make sure that we don't get stuck in too many recursions
        if(self.adjust_counter >= self.max_recursion):
            ard_log.error("in function: "+self.command+" Maximum number of recursion reached")
            self.adjust_counter = 0;
            return
        
        #reply from arduino has been compared, and different flags have been set accordingly.
        #depending on combination of flags, a certain case is true, and possible adjustments made
        if(not self.pressureHigh and not self.pressureLow and not self.pulseLow):
            ard_log.debug("Command successful")
            self.adjust_counter = 0;
            return
        
        elif(self.pressureHigh) :
            ard_log.debug("in function: "+self.command+" Pressure_received " + str(self.pressure_received) + " higher than Pressure_sent " + str(self.pressure_sent) + " , adjusting by opening")
            self.adjust_counter = self.adjust_counter + 1
            self.open_gripper(self.adjustment_pulses,self.pressure_sent)
            return
        elif(self.pressureLow):
            ard_log.debug( "in function: "+self.command+" Pressure_received " + str(self.pressure_received) + " lower than Pressure_sent " + str(self.pressure_sent) + " , adjusting by closing")
            self.adjust_counter = self.adjust_counter + 1
            self.close_gripper(self.adjustment_pulses,self.pressure_sent)
            return
                    
        elif(self.pulseLow):
            self.obstacleFlag = True
            ard_log.error("in function: "+self.command+" Obstacle error, cease operation\n Flags: pulseLow:%r pressureLow:%r pressureHigh:%r" %(self.pulseLow,self.pressureLow,self.pressureHigh))
            return      
        
        else:
            ard_log.debug("Jumping into else, some undefined case")
            print("self.pulseLow, self.pressureLow, self.pressureHigh \n")
            print(self.pulseLow, self.pressureLow, self.pressureHigh)
            print("data_sent \n")
            print(self.data_sent)
            print("data_received \n")
            print(self.data_received)
            return
        
    def activate_solenoid(self):
        self.command = "Deactivate Solenoid"
        ard_log.debug( "in function: "+self.command)
        self.ID_sent = 2
        msg = str(self.ID_sent) + "," + str(1) + "," + str(1) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(1.0) #creates a new thread that acts as a timer to reduce CPU useage
        ard_log.debug("Command successful")    
        return
    
    def deactivate_solenoid(self):
        self.command = "Deactivate Solenoid"
        ard_log.debug( "in function: "+self.command)
        self.ID_sent = 3
        msg = str(self.ID_sent) + "," + str(1) + "," + str(0) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(1.0) #creates a new thread that acts as a timer to reduce CPU useage
        ard_log.debug("Command successful")
            
        return
        
    def acknowledge_error(self):
        self.command = "Acknowledge Error"
        ard_log.debug( "in function: "+self.command)
        self.ID_sent = 4
        msg = str(self.ID_sent) + "," + str(2) + "," + str(1) + ";" + str(0) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(1.0) #creates a new thread that acts as a timer to reduce CPU useage
        ard_log.debug("Command successful")      
        return
    
    def request_info(self):
        self.command = "Request info"
        ard_log.debug( "in function: "+self.command)
        self.ID_sent = 5
        msg = str(self.ID_sent) + "," + str(2) + "," + str(1) + ";" + str(0) + ";"
        self.Arduino_replied = False #set the flag to false
        self.send(msg)
        
        #waiting for Arduino to reply
        while(self.Arduino_replied == False): #flag will be set to TRUE when checking return message
            Event().wait(1.0) #creates a new thread that acts as a timer to reduce CPU useage
        ard_log.debug("Command successful")      
        return
            
    def calibrate_gripper(self):
        while(self.pressure_received < 5):
            self.close_gripper(100,5)
        while(self.pressure_received > 10):
            self.open_gripper(50,5)
        ard_log.debug("Claw calibrated to be closed with a pressure less than 10, opening Gripper with 6000 pulses")
        self.open_gripper(6000,0)
        self.pulses = 0
