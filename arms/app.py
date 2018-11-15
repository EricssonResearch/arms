"""Initialization of arms."""

from arms.config import config
from arms.utils import log
from arms.uart.Arduino_RPI_communication_new import Arduino
import time

def main():
    """Main routine."""
    initialization()


def initialization():
    """Initialization routine."""
    log.__init__()
    log.log.info("Log file initialized.")
    if config.var.data is None:
        log.config.warning("{}.".format(config.var.error))
    if log.ERROR:
        log.log.warning('Could not find settings in config.')
        
    a = Arduino()
    a.send(11)
    time.sleep(1)
    a.send(20)
    a.disconnect()
    a.connect()
    a.send(31)
    a.disconnect()
    
    print(a.ID +' '+a.fields+' '+str(a.data))
    
    
    print("printing in app.py - final line")
