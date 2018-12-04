"""Initialization of arms."""
import arms.config.config as config
import arms.utils.log as log
#from arms.camera.camera import Camera
#import RPi.GPIO as GPIO
from time import sleep
import numpy as np
import arms.sensor.sensor as S


def main():
    """Main routine."""
    initialization() 
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(17, GPIO.OUT)

    #while True:
     #   GPIO.output(17, GPIO.HIGH)
      #  sleep(15/(130*2))
       # GPIO.output(17, GPIO.LOW)
        #sleep(45/(130*2))
    #c = Camera(True)
    #c.cableInsertion(True,'2018-11-26 16:07:39.962209')
    #c.cableInsertion(True,'2018-11-26 15:56:09.641098')
    #c.cableInsertion(True,'2018-11-26 15:02:42.568639')
    #a = np.array(([1],[2]))
    #
    #print(a.shape)

def initialization():
    """Initialization routine."""
    log.__init__()
    log.log.info("Log file initialized.")
    if config.var.data is None:
        log.config.warning("{}.".format(config.var.error))
    if log.ERROR:
        log.log.warning('Could not find settings in config.')


    force_sense = S.Sensor()
    force_sense.connect()
    #for i in range(10):
    while True:
        try:
           print("---------------------")
           force_sense.read()
           print(force_sense.values.Tx)
           print(force_sense.values.Ty)
           print(force_sense.values.Fz)
           sleep(1)
        except KeyboardInterrupt:
            break
        
        finally:
            'Some crazy shit'


    
