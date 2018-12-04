"""Utilities related to receiving and evaluating of DU failure reports."""

import requests
import time
from arms.config import config
from arms.utils import log


class Alarms:

    """Receiving and evaluating of DU failure reports."""

    def listen(self):
        """Connects with the web server 'alarms' specified in the settings
        (arms/config/config.json -> web -> alarms) and waits for an error
        message.

        Return:
            -   True, if a hardware link failure was reported.
            -   False, if an internal error occurred.
        """

        try:
            host = config.var.data['web']['alarms']['host']
            port = config.var.data['web']['alarms']['port']
            url = config.var.data['web']['alarms']['url']
            webpage = host + ":" + str(port) + url
            response = requests.get(webpage).text
        except (TypeError, KeyError):
            log.alarms.critical("Could not find (appropriate) settings in the "
                                "configuration file (arms/config/config.json) "
                                "to reach the website responsible for sending "
                                "failure reports. Hence, this service will be "
                                "closed.")
            return False
        except requests.exceptions.RequestException:
            time.sleep(60)
            return self.listen()

        if response == "A":
            log.alarms.info("The error code ({}) was received. The healing "
                            "process will be started.".format(response))
            return True
        else:
            time.sleep(60)
            return self.listen()
