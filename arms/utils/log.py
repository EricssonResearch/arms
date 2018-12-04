"""Utilities related to logging."""

import logging
import time
from arms.config import config

# Log format to use.
FORMATTER = logging.Formatter('%(asctime)s | %(name)-10s | '
                              '%(levelname)-8s | %(message)s', '%Y-%m-%d %H:%M')

# Log levels to use.
LOG_LEVELS = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

# Load configurations from file. If it fails, take predefined values.
ERROR = False
FILE_LEVEL = logging.DEBUG
CONSOLE_LEVEL = logging.WARNING
try:
    CONFIG = config.var.data['logger']
    FILE_LEVEL = LOG_LEVELS[CONFIG['file']['level'].upper()]
    CONSOLE_LEVEL = LOG_LEVELS[CONFIG['console']['level'].upper()]
except (TypeError, KeyError):
    ERROR = True


class SocketClientHandler(logging.Handler):
    """Reports the logging output to a socket server.

    Attributes:
        client: Has to be an instance of arms/misc/socket -> SocketClient.
    """

    def __init__(self):
        super().__init__()
        self.client = None
        self.setLevel(logging.INFO)
        self.setFormatter(FORMATTER)

    def connect(self):
        """Connects with the socket server.

        Return:
            - True, if a connection with the socket server could me made.
            - False, if an error occurred.
        """
        while True:
            ok, connected = self.client.get_config_and_connect()
            if not ok:
                return False
            if connected:
                return True
            else:
                time.sleep(10)

    def emit(self, record):
        """Sends the logging output to the socket server."""
        if self.client is not None:
            client = record.name
            level = record.levelno
            msg = record.message

            data = {
                "client": client,
                "level": level,
                "msg": msg
            }

            ok = self.client.send(data)
            if not ok:
                self.client = None


# Initialize handlers.
FILE = logging.FileHandler('arms/utils/log.log')
FILE.setFormatter(FORMATTER)
FILE.setLevel(FILE_LEVEL)

CONSOLE = logging.StreamHandler()
CONSOLE.setFormatter(FORMATTER)
CONSOLE.setLevel(CONSOLE_LEVEL)

CLIENT = SocketClientHandler()


def __init__():
    """Reset log file."""
    wfile = logging.FileHandler('arms/utils/log.log', mode='w')
    wfile.setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(wfile)
    logger.info('Log file')
    logger.info(90 * '-')


def get_logger(name):
    """Set up a new logger.

    Args:
        name: name of the new logger (string).

    Return:
        Logger with specified name.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(FILE)
    logger.addHandler(CONSOLE)
    logger.addHandler(CLIENT)

    return logger


# The different loggers used (alphabetical order).
abb = get_logger('abb')
app = get_logger('app')
ard_log = get_logger('ard_log')
camera = get_logger('camera')
config = get_logger('config')
log = get_logger('log')
sensor = get_logger('sensor')
socket = get_logger('socket')
