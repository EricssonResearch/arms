"""Initialization of arms."""

from arms.config import config
from arms.utils import log


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
