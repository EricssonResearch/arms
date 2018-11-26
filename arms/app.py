"""Initialization of arms."""
import arms.config.config as config
import arms.utils.log as log
from arms.sensor.sensor import Sensor


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
