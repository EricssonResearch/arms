"""Utilities related to socket communication."""

import socket
from arms.utils import log
from arms.config import config


class SocketClient:

    """A socket client with the capability to send/receive strings.

    Attributes:
        name: The client name; used to find the needed settings (host, port)
        in the config file to be able to connect with the respective server.
        sock: The socket interface.
    """

    def __init__(self, client_name):
        self.name = client_name
        self.sock = None

    def get_config_and_connect(self):
        """Reads the host and port number of the client (client_name)
        defined in the config file and tries to connect with the respective
        server.

        Return:
            - True, if a setting entry belonging to the client (client_name)
            could be found and no data type violation occurred.
            - False, if not.
        """
        try:
            c = config.var.data['socket'][self.name]
            host = c['host']
            port = c['port']
        except (TypeError, KeyError):
            log.socket.error('Could not find (appropriate) settings for the '
                             'socket {} in the configuration file ('
                             'arms/config/config.json). Hence, no '
                             'connection could be made.'.format(self.name))
            return False

        if isinstance(host, str) and isinstance(port, int):
            ok = self.connect(host, port)
            return ok
        else:
            log.socket.error('Data type violation. The host number has to be '
                             'provided as a string and the port number as an '
                             'integer in the configuration file ('
                             'arms/config/config.json). In consequence, the '
                             'socket {} could not connect to the server.'
                             .format(self.name))
            return False

    def connect(self, host, port):
        """Establishes a connection to a server.

        Args:
            host: Represents either a hostname or an IPv4 address.
            port: The port.

        Return:
            - True, if a connection could be made.
            - False, if not.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2.0)
        try:
            self.sock.connect((host, port))
            self.sock.settimeout(None)
            log.socket.info('Client {} | Connected to server at '
                            '(host, port) = ({}, {}).'
                            .format(self.name, host, port))
        except (socket.error, socket.timeout) as e:
            self.sock = None
            log.socket.error('Client {} | No connection could be made to '
                             'server at (host, port) = ({}, {}). Reason: {}'
                             .format(self.name, host, port, e))
            return False
        return True

    def close(self):
        """Closes the connection in a timely fashion."""
        if self.sock is None:
            return

        self.sock.close()
        self.sock = None
        log.socket.info('Client {}: Disconnected from server.'.format(
            self.name))

    def send(self, data):
        """Sends data to the socket in two steps.
            1. step: Sends the length of the original message.
            2. step: Sends the original message.

        Args:
            data: The data to send.

        Return:
            - True, if the data could be sent.
            - False, if not.
        """
        if self.sock is None:
            return False

        if not isinstance(data, str):
            data = str(data)

        length = len(data)

        try:
            # 1. step: Send the length of the original message.
            self.sock.sendall(b'a%d\n' % length)

            # 2. step: Send the original message.
            self.sock.sendall(data.encode())
        except (socket.error, socket.timeout) as e:
            self.sock = None
            log.socket.error('SERVER | Error, can not send data. '
                             'Reason: {}.'.format(e))
            return False

        return True

    def recv(self):
        """Receives data from the socket in two steps.
            1. step: Get the length of the original message.
            2. step: Receive the original message with respect to step one.

        Return:
            - [#1, #2]
                #1: True if a client is connected, False if not.
                #2: The received data.
        """
        if self.sock is None:
            return [False, ""]

        # 1. Get the length of the original message.
        length_str = ""
        char = ""
        while char != '\n':
            length_str += char
            try:
                char = self.sock.recv(1).decode()
            except (socket.error, socket.timeout) as e:
                self.sock = None
                log.socket.error('SERVER | Error, can not receive data. '
                                 'Reason: {}.'.format(e))
                return [False, ""]
            if not char:
                self.sock = None
                log.socket.error('SERVER | Error, can not receive data. '
                                 'Reason: Not connected to server.')
                return [False, ""]
            if (char.isdigit() is False) and (char != '\n'):
                length_str = ""
                char = ""
        total = int(length_str)

        # 2. Receive the data chunk by chunk.
        view = memoryview(bytearray(total))
        next_offset = 0
        while total - next_offset > 0:
            try:
                recv_size = self.sock.recv_into(view[next_offset:],
                                                total - next_offset)
            except (socket.error, socket.timeout) as e:
                self.sock = None
                log.socket.error('SERVER | Error, can not receive data. '
                                 'Reason: {}.'.format(e))
                return [False, ""]
            next_offset += recv_size

        data = view.tobytes().decode()
        return [True, data]
