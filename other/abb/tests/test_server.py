"""Tests for the module server.mod running on an ABB robot/controller.

Quick Setup/ Run tests:
    - Start ABB RobotStudio.
    - Create an empty station (File -> New -> Empty station).
    - Place a robot (Home -> Tab 'Build Station' -> ABB Library -> Select a
      robot and press Ok).
    - Create a system based on an existing layout (Home -> Tab 'Build Station'
      -> Robot System -> From Layout... -> Next -> Next -> Finish).
    - Check PC Interface (Controller -> Tab 'Virtual Controller' -> Change
      Options -> Communication -> Check '616-1 PC Interface' -> Ok -> Yes).
    - Create a new RAPID module and name it 'server' (Left panel -> RAPID ->
      Right click on T_ROB1 -> New module... -> Module name: server -> Ok).
    - Copy and Paste the code from server.mod in the just created module.
    - Start the execution (RAPID -> Tab 'Test and Debug' -> Press Start).
    - Open the command window. The tests can be run with:
        $ cd */project folder/arms/other/abb
        $ pytest
"""

import json
import pytest
import socket
import time


def recv(s):
    """Receives data from the socket in two steps.
        1. step: Get the length of the message.
        2. step: Receive the original message with respect to step one.

    Args:
        s: The socket.

    Return:
        [id, ok], where
        id: If the given message to the ABB robot does not contain any errors,
            this id number is the same as in the given message. Otherwise it
            represents an error code (negative number).
        ok: If False, an error occurred during the operation of the ABB robot,
            otherwise not.
    """
    # 1. step: Read the length of the data.
    length_str = ""
    char = ""
    while char != '\n':
        length_str += char
        char = s.recv(1).decode()
        if (char.isdigit() is False) and (char != "") and (char != '\n'):
            char = ""

    total = int(length_str)

    # 2. step: Receive the data chunk by chunk.
    view = memoryview(bytearray(total))
    next_offset = 0
    while total - next_offset > 0:
        recv_size = s.recv_into(view[next_offset:], total - next_offset)
        next_offset += recv_size

    data = view.tobytes().decode()
    data = data.replace("'", '\"')
    data = json.loads(data)

    return [data['id'], bool(data['ok'])]


@pytest.fixture(scope="class")
def server():
    """Connects with the ABB robot and closes the socket once all tests are
    completed in the respective class.
    """
    # Setup: connect to socket.
    host = "127.0.0.1"
    port = 5001
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(20)

    yield s

    # Teardown: close socket.
    msg = b"21\n[0,0,0,0,0,0,0,0,0,0]"
    s.send(msg)
    s.close()


class TestExchangeOfMessages:

    """Contains all tests regarding the exchange (sending and
    receiving) of messages between the ABB robot and the client.
    """

    @pytest.mark.parametrize("msg, no, expected", [
        (b"21\n[1,0,0,0,0,0,0,0,0,0]", 1, [[1, True]]),
        (b"21\n[1,0,0,0,0,0,0,0,0,0]21\n[1,0,0,0,0,0,0,0,0,0]", 2,
         [[1, True], [1, True]]),
    ])
    def test_correct(self, server, msg, no, expected):
        """WHEN a message of expected form is given to the ABB robot,
        THEN the ABB robot shall respond with ok = True and the returned id
        number shall equal the given id number.
        """
        server.send(msg)
        for idx in range(no):
            received = recv(server)
            assert received == expected[idx]


    @pytest.mark.parametrize("msg, no, expected", [
        (b"24\n[1000,0,0,0,0,0,0,0,0,0]", 1, [[-1, False]]),
        (b"24\n[1000,0,0,0,0,0,0,0,0,0]24\n[1000,0,0,0,0,0,0,0,0,0]", 2,
         [[-1, False], [-1, False]]),
    ])
    def test_no_respective_case(self, server, msg, no, expected):
        """IF there is no case belonging to an id number, THEN the ABB robot
        shall respond with id = -1 and ok = False.
        """
        server.send(msg)
        for idx in range(no):
            received = recv(server)
            assert received == expected[idx]


    @pytest.mark.parametrize("msg, expected", [
        (b"0\n", [-2, False]),
        (b"81\n", [-2, False]),
        (b"\n", [-2, False]),
        (b"\n[0,1,2,3,4,5,6,7,8,9]", [-2, False]),
        (b"a\n[0,1,2,3,4,5,6,7,8,9]", [-2, False]),
    ])
    def test_wrong_length(self, server, msg, expected):
        """IF the given length l of the original message exceeds the
        bounds 0 < l <= 80, or the given length can not be read/ casted
        into a number, THEN the ABB robot shall respond with id = -2 and ok
        = False.
        """
        server.send(msg)
        received = recv(server)
        assert received == expected


    @pytest.mark.parametrize("msg, expected", [
        (b"7\n[1,0,0]", [-3, False]),
        (b"10\n[1,0,0]", [-3, False]),
        (b"30\n[0,1,2,3,4,5,6,7,8,9,10,11,12]", [-3, False]),
        (b"1\n[0,1,2,3,4,5,6,7,8,9]", [-3, False]),
        (b"20\n[0,1,2,3,4,5,6,7,8,9]", [-3, False]),
        (b"3\nabc", [-3, False]),
        (b"3\n123", [-3, False]),
        (b"10\n[1,0,0]21\n[1,0,0,0,0,0,0,0,0,0]", [-3, False]),
    ])
    def test_wrong_array(self, server, msg, expected):
        """IF the given original message can not be casted into an array,
        and the error code {-2} does not apply, THEN the ABB robot shall
        respond with id = -3 and ok = False.
        Note: Reasons that this error code gets raised include:
            - The array size in the given original message differs from 10.
            - The given length of the original message is too small and hence
              the original message is not read completely by the ABB robot.
            - The given original message does not contain an array.
            - The message contains several command requests, but the given
              length of the first one is greater than the actual length of
              the original message.
        """
        server.send(msg)
        received = recv(server)
        assert received == expected


    @pytest.mark.parametrize("msg, expected", [
        (b"30\n[0,1,2,3,4,5,6,7,8,9]", [-4, False]),
    ])
    def test_discrepancy_length(self, server, msg, expected):
        """IF the given length is greater than the actual length of the
        original message, and the error codes {-2, -3} do not apply, THEN
        the ABB robot shall respond with id = -4 and ok = False.
        """
        server.send(msg)
        received = recv(server)
        assert received == expected


    @pytest.mark.parametrize("msg, no, expected", [
        (b"22\n[-1,0,0,0,0,0,0,0,0,0]", 1, [[-5, False]]),
        (b"22\n[-2,0,0,0,0,0,0,0,0,0]", 1, [[-5, False]]),
        (b"22\n[-3,0,0,0,0,0,0,0,0,0]", 1, [[-5, False]]),
        (b"22\n[-4,0,0,0,0,0,0,0,0,0]", 1, [[-5, False]]),
        (b"22\n[-5,0,0,0,0,0,0,0,0,0]", 1, [[-5, False]]),
    ])
    def test_negative_id(self, server, msg, no, expected):
        """IF the given id number is below zero, and the error codes {-2,
        -3, -4} do not apply, THEN the ABB robot shall respond with id = -5
        and ok = False.
        Reason: id numbers below zero (<0) are reserved for error codes.
        """
        server.send(msg)
        for idx in range(no):
            received = recv(server)
            assert received == expected[idx]


    @pytest.mark.parametrize("msg, no, expected", [
        (b"22\n[-1,0,0,0,0,0,0,0,0,0]22\n[-1,0,0,0,0,0,0,0,0,0]", 2,
         [[-5, False], [-5, False]]),
        (b"7\n[1,0,0]21\n[1,0,0,0,0,0,0,0,0,0]", 2, [[-3, False], [1, True]]),
        (b"3\n[1,0,0]21\n[1,0,0,0,0,0,0,0,0,0]", 2, [[-3, False], [1, True]]),
        (b"8\n[1,0,0]21\n[1,0,0,0,0,0,0,0,0,0]", 2, [[-3, False], [-3, False]]),
        (b"21\n[1,0,0,0,0,0,0,0,0,0]7\n[1,0,0]", 2, [[1, True], [-3, False]]),
    ])
    def test_mix(self, server, msg, no, expected):
        """IF the given message contains several command requests with correct
        message length and delimiter, THEN all command requests shall be
        processed correctly with respect to the error codes.
        """
        server.send(msg)
        for idx in range(no):
            received = recv(server)
            assert received == expected[idx]


    def test_no_delimiter(self, server):
        """When the given message does not contain the expected delimiter '\n',
        the ABB robot shall keep listening for new messages."""
        # A message that does not contain the expected delimiter '\n'.
        msg = b"21[1,0,0,0,0,0,0,0,0,0]"
        server.send(msg)
        server.settimeout(1)
        with pytest.raises(socket.timeout):
            recv(server)
        server.settimeout(None)

        # A new (correct) message.
        msg = b"21\n[1,0,0,0,0,0,0,0,0,0]"
        server.send(msg)
        received = recv(server)
        assert received == [1, True]


def test_reconnect():
    """IF the ABB robot looses the connection to the client, THEN the ABB
    robot shall restart the server."""
    host = "127.0.0.1"
    port = 5001

    for _ in range(2):
        time.sleep(0.5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((host, port))
        s.send(b"21\n[1,0,0,0,0,0,0,0,0,0]")
        assert recv(s) == [1, True]
        s.close()
