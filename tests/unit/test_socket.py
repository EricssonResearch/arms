"""Tests for arms.misc.socket"""

import pytest
import socket
import threading
from unittest import mock
from unittest.mock import call
from arms.config import config
from arms.misc.socket import SocketClient

# Global variables.
host = "127.0.0.1"
port = 5000


def test_init():
    """The instance attributes 'client_name' and 'sock' shall be changeable."""
    # Test changeability of 'client_name'.
    client = SocketClient("test_init")
    tmp = client.name
    client.name = "test_init"
    assert client.name == "test_init"
    client.name = tmp
    assert client.name == tmp

    # Test changeability of 'sock'.
    tmp = client.sock
    client.sock = "test_init"
    assert client.sock == "test_init"
    client.sock = tmp
    assert client.sock == tmp


def test_get_config_and_connect():
    """WHEN the function 'get_config_and_connect' is called, and a config entry
    containing the host name (string) and port number (integer) to the
    specified client (client_name) is available and is of the correct format,
    an attempt to connect with the respective server shall be made.
    """
    client = SocketClient("test_socket")
    data = {"socket": {"test_socket": {"host": host, "port": port}}}
    client.connect = mock.MagicMock()

    with mock.patch.object(config.var, 'data', data):
        client.get_config_and_connect()
        client.connect.assert_called_with(host, port)


config_none = None
config_empty = {}
config_only_socket = {"socket": 1}
config_only_host = {"socket": {"test_socket": {"host": 1}}}
config_only_port = {"socket": {"test_socket": {"port": 2}}}
config_wrong_host = {"socket": {"test_socket": {"host": 1, "port": 2}}}
config_wrong_port = {"socket": {"test_socket": {"host": '1', "port": '2'}}}
config_wrong_host_port = {"socket": {"test_socket": {"host": 1, "port": '2'}}}


@pytest.mark.parametrize('config_data', [config_none, config_empty,
                                         config_only_socket,
                                         config_only_host, config_only_port,
                                         config_wrong_host, config_wrong_port,
                                         config_wrong_host_port])
def test_get_config_and_connect_fail(config_data):
    """WHEN the function 'get_config_and_connect' is called, IF the config
    entry containing the host name and port number to the specified client
    (client_name) is of the wrong format or does not exist, THEN no attempt
    to connect with the respective server shall be made and the boolean value
    False shall be returned.
    """
    client = SocketClient("test_socket")
    client.connect = mock.MagicMock()

    with mock.patch.object(config.var, 'data', config_data):
        ok = client.get_config_and_connect()
        client.connect.assert_not_called()
        assert ok is False


def test_connect():
    """WHEN the function function 'connect' is called, and the host name
    (string) and port number (integer) are given, an attempt to connect with
    the respective server (socket) shall be made.
    """
    client = SocketClient("test_connect")

    with mock.patch('socket.socket'):
        client.connect(host, port)
        client.sock.connect.assert_called_with((host, port))


def test_connect_fail():
    """WHEN the function function 'connect' is called, IF the server
    belonging to the given host name (string) and port number (integer) is
    not available, THEN the boolean value False shall be returned and the
    instance attribute "sock" shall be set to None.
    """
    client = SocketClient("test_connect_fail")

    with mock.patch('socket.socket') as mock_socket:
        mock_sock = mock.Mock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.side_effect = socket.error

        ok = client.connect(host, port)
        assert client.sock is None
        assert ok is False


def test_close():
    """WHEN the function 'close' is called, the connection to the server
    shall be closed in a timely fashion.
    """
    client = SocketClient("test_close")
    mock_socket = mock.Mock()
    client.sock = mock_socket

    client.close()
    mock_socket.close.assert_called()


def test_send():
    """The function 'send' shall transmit data to the socket in two steps:
    1. Send the length of the data to transmit in bytes followed by
    the delimiter '\n', 2. Send the data; and shall return the boolean
    value True if no error occurred during this operation.
    """
    client = SocketClient("test_send")
    mock_socket = mock.Mock()
    client.sock = mock_socket

    data = 123
    ok = client.send(data)
    expected = [call.sendall(b'a%d\n' % len(str(data))),
                call.sendall(str(data).encode())]
    assert mock_socket.mock_calls == expected
    assert ok is True


def test_send_fail():
    """WHEN the function 'send' is called, IF the server is not available,
    THEN the boolean value False shall be returned and the instance variable
    'sock' shall be set to None if its value differ from None.
    """
    # Test 1: Socket error occurs; the variable 'sock' differs from None.
    client = SocketClient("test_send_fail")
    mock_socket = mock.Mock()
    client.sock = mock_socket
    mock_socket.sendall.side_effect = socket.error

    ok = client.send(123)
    assert client.sock is None
    assert ok is False

    # Test 2: Variable 'sock' equals already None.
    client.sock = None
    ok = client.send(123)
    assert ok is False


class SocketServer:

    """A socket server to be able to connect with.

    Attributes:
        sock: The socket interface.
        conn: Socket object usable to send and receive data on the connection.
        addr: Address bound to the socket on the other end of the connection.
    """

    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def create(self):
        """Creates a server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.bind((host, port))
        self.sock.listen(1)
        self.conn, self.addr = self.sock.accept()

    def close(self):
        """Closes the socket and the connection to the client."""
        if self.conn is not None:
            self.conn.close()
            
        if self.sock is not None:
            self.sock.close()


@pytest.fixture(scope="class")
def server_client():
    # Setup: create socket.
    server = SocketServer()

    thread = threading.Thread(target=server.create)
    thread.start()

    client = SocketClient("test_recv")
    client.connect(host, port)

    yield server, client

    # Teardown: close socket and thread.
    server.close()
    thread.join()


class TestRecv:

    @pytest.mark.parametrize("msg, expected", [
        (b"3\nabc", [True, "abc"]),
        (b"abc3\nabc", [True, "abc"])
    ])
    def test_recv(self, server_client, msg, expected):
        """WHEN the function 'recv' is called, and a message of the form
        <length of data in bytes><delimiter = \n><data> is available,
        only the received data and the boolean value True indicating that no
        error occurred during this operation shall be returned.
        """
        server, client = server_client
        server.conn.sendall(msg)
        respond = client.recv()
        assert respond == expected

    def test_recv_no_connection(self, server_client):
        """WHEN the function 'recv' is called, IF the server is not
        available, THEN the boolean value False and an empty string shall be
        returned."""
        server, client = server_client
        server.conn.close()
        ok, data = client.recv()
        assert ok is False
        assert data == ""

    def test_recv_sock_is_none(self, server_client):
        """WHEN the function 'recv' is called, IF the instance variable
        'sock' equals None, THEN the boolean value False and an empty string
        shall be returned."""
        server, client = server_client
        client.sock = None
        ok, data = client.recv()
        assert ok is False
        assert data == ""

    def test_recv_error(self, server_client):
        """WHEN the function 'recv' is called, IF a socket error occurs,
        THEN the boolean value False and an empty string shall be returned."""
        server, client = server_client

        # Socket error occurs during the first step of reading the length
        # of the data to receive.
        mock_socket = mock.Mock()
        client.sock = mock_socket
        mock_socket.recv.side_effect = socket.error
        ok, data = client.recv()
        assert ok is False
        assert data == ""

        # Socket error occurs during the second step of reading the data
        # to receive.
        mock_socket = mock.Mock()
        client.sock = mock_socket
        mock_socket.recv.side_effect = [b"1", b"0", b"\n"]
        mock_socket.recv_into.side_effect = socket.error
        ok, data = client.recv()
        assert ok is False
        assert data == ""
