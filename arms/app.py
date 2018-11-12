"""Initialization of arms."""

from arms.config import config
from arms.utils import log
from arms.uart.Arduino_RPI_communication import Arduino
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
    print(a.receive())
    a.send(1)
    time.sleep(1)
    a.send(0)
    a.disconnect()
    a.connect()
    a.send(1)
    a.disconnect()
    
    
    print("printing in app.py - final line")
