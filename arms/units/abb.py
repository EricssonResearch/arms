"""Utilities related to the communication with the ABB robotic arm."""

import ast
import json
from arms.misc.socket import SocketClient
from arms.utils import log


class ABB:
    """Handles the communication with the ABB robot with respect to
        - sending command requests to and
        - receiving/evaluating the responds from the ABB robot.

    Attributes:
        client: The socket interface.
    """
    def __init__(self):
        self.client = SocketClient("abb")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Connects to the socket server."""
        ok, connected = self.client.get_config_and_connect()
        return ok, connected
    
    def close(self):
        """Close connection."""
        case = 0
        self._send(case)
        self.client.close()

    def get_system_information(self):
        """Get system information."""
        case = 1
        ok, data = self._exchange(case)
        return ok, data

    def get_joint_coordinates(self):
        """Get joint coordinates."""
        case = 10
        ok, data = self._exchange(case)
        return ok, data

    def get_position(self):
        """Get the current position."""
        case = 29
        ok, data = self._exchange(case)
        return ok, data
        
    def move(self, x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx):
        """Sends absolute movement coordinates."""
        log.abb.debug("Move to (x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx) = "
                      "({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})"
                      .format(x, y, z, q1, q2, q3, q4, cf1, cf4, cf6, cfx))
        case = 30
        data = [x, y, z, q1, q2]
        ok, data = self._exchange(case, data)

        if ok:
            case = 31
            data = [0, 0, 0, 0, 0, q3, q4, cf1, cf4, cf6, cfx]
            ok, data = self._exchange(case, data)
                      
        return ok, data

    def delta_move(self, dx, dy, dz):
        """Sends relative movement coordinates."""
        case = 33
        data = [dx, dy, dz]
        ok, data = self._exchange(case, data)
        return ok, data
    
    def move_to_sleep(self):
        """Move to sleep position."""
        case = 14
        ok, data = self._exchange(case)
        return ok, data
    
    def insert_SFP(self):
        self.sensor.connect()
        z_tot = 0
        stepSizeXY = 0.1
        stepSizeZ = 0.1
        self.sensor.start_ping()
        while True:
            """Moves forward in Z until the self.sensor detects something."""
            self.sensor.read()
            if self.sensor.values.Fz > 0.1 or self.sensor.values.Tx > 0.1 or self.sensor.values.Ty > 0.1:
                break
            self.move(0,0,stepSizeZ)
            z_tot += stepSizeZ
            if z_tot > 1: #aborts if it goes beyond the du, ie. something is wrong.
                return False    #could also be a perfect fit where it got it right the first time, which needs a special case.
        while self.sensor.values.Fz < 24:
            """Reads the sensor and resets the movements, then determines the movements according to z_tot ie. if it's
            inside or not."""
            self.sensor.read()
            dx = dy = dz = 0
            if z_tot <= 1:
                """Detects the torques and moves according to what's detected. TODO: determine threshold"""
                if self.values.Tx >= 1:
                    dy = -stepSizeXY
                elif self.values.Tx <= -1:
                    dy = stepSizeXY
                    
                if self.values.Ty >= 1:
                    dx = -stepSizeXY
                elif self.values.Ty <= -1:
                    dx = stepSizeXY
                """Moves back in z before moving in x and y"""
                dz = stepSizeZ
                self.move(0, 0, -dz)
            else:
                """I'ts now inside and moves only i Z and adds to z_tot"""
                
                dz = stepSizeZ
                z_tot += dz
            if z_tot > z_max: #breaks if z_tot becomes too large
                break
            """moves according to the determined coordinates"""
            if dx > 0 and dy > 0:
                self.move(dx, dy, 0)
            if dz > 0:
                self.move(0, 0, dz)
        
        self.sensor.stop_ping()
        
        return True

    def _exchange(self, case, data=None):
        """Exchanges messages with the ABB robot in two steps:
            1. step: Send a command to the ABB robot.
            2. step: Receive the answer from the ABB robot.

        Moreover, the message to expect from the ABB robot is of JSON format
        and is sent as a string; e.g.:
            "{'id':1,'ok':1,'data':'[1, 2, 3]'}"
        Hence, the 3. step is to convert this string into a dictionary.

        Args:
         case:  The case to address in the RAPID code running on the IRC5
                (ABB robot).
         data:  The data to send to the IRC5 (ABB robot), e.g. coordinates.
         """

        # 1. Send a command to the ABB robot.
        ok = self._send(case, data)
        if not ok:
            return [False, []]

        # 2. Receive the answer from the ABB robot.
        [ok_client, recv_msg] = self.client.recv()
        if not ok_client:
            return [False, []]

        # 3. Convert the received message into a dictionary.
        recv_msg = recv_msg.replace("'", '\"')
        recv_msg = recv_msg.replace("|", "'")
        try:
            recv_msg = json.loads(recv_msg)
            recv_id = recv_msg['id']
            recv_ok = bool(recv_msg['ok'])
            recv_data = ast.literal_eval(recv_msg['data'])
        except (OSError, ValueError, TypeError, KeyError) as e:
            log.abb.error("The received message is of the wrong "
                          "format. The received message is {}; reason for "
                          "error: {}.".format(recv_msg, e))
            return [False, []]

        # Check if the stated case in the received message equals the
        # given (expected) case.
        if recv_id != case:
            log.abb.critical("The case in the received message {} does not "
                             "equal the given (expected) case.")
            return [False, []]
        else:
            return [recv_ok, recv_data]

    def _send(self, case, data=None):
        """Sends a command to the ABB robot in the expected format:
            <length of data in bytes><delimiter = \n><data>
        , where
             <length of data in bytes><delimiter = \n>: Handled by the
                                                        class SocketClient.
             <data>: array/list of 12 elements; first element is the case.

        Args:
            case:   The case to address in the RAPID code running on the IRC5
                    (ABB robot).
            data:   The data to send to the IRC5 (ABB robot), e.g. coordinates.

        Return:
            - True, if the message could be send to the ABB robot successfully.
            - False, if not.
        """
        if not isinstance(case, int):
            log.abb.error('The case has to be provided as an integer. The '
                          'given case was: '.format(case))
            return False

        if data is None:
            data = []

        if len(str(data)) > 80:
            log.abb.error('The data list {} is bigger than 80 bytes and '
                          'therefore can not be send to the ABB robot.'
                          .format(data))
            return False

        msg = [case]
        msg = msg + data
        if len(msg) <= 12:
            msg = msg + (12-len(msg))*[0]
        else:
            log.abb.error('The data list {} has more than 9 elements and '
                          'therefore can not be send to the ABB robot.'
                          .format(data))
            return False

        log.abb.info('An attempt to send a command request to the ABB robot '
                     'is made. The message is {}.'.format(msg))
        ok = self.client.send(msg)
        return ok
