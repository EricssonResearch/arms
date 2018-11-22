"""Tests for arms.units.abb"""

import pytest
from unittest import mock
from arms.units.abb import ABB


def test_init():
    """The instance attribute 'client' of the class 'ABB' shall be an instance
    of the class 'SocketClient' with the attribute value 'abb'.
    """
    with mock.patch('arms.units.abb.SocketClient') as mock_client:
        ABB()
        mock_client.assert_called_with("abb")


def test_with():
    """The class 'ABB' shall be able to work with Python with statements and
    by leaving its scope the connection to the ABB robot shall be closed.
    """
    with mock.patch('arms.units.abb.ABB.close') as mock_close:
        with ABB():
            pass
        mock_close.assert_called()


@pytest.mark.parametrize("case, msg, expected", [
    (1, "{'id':1,'ok':1,'data':'[]'}", [True, []]),
    (1, "{'id':1,'ok':1,'data':'[1,2,3]'}", [True, [1, 2, 3]]),
])
def test_exchange(case, msg, expected):
    """WHEN the function '_exchange' is called, a command request to the ABB
    robot shall be send by calling the function 'send(case, data)', and the
    received message (answer) from the ABB robot shall be converted into a
    dictionary.

    Comment:
        This requires a working connection to the ABB robot and in addition a
        received message from the ABB robot of the format:
            "{'id':<id number>,
            'ok':<bool as number (1 = True, 0 = False)>,
            'data':<array of variable size>}"
    """
    abb = ABB()

    mock_send = mock.Mock()
    abb._send = mock_send
    mock_send.return_value = True

    mock_client = mock.Mock()
    abb.client = mock_client
    mock_client.recv.return_value = [True, msg]

    received = abb._exchange(case)
    abb._send.assert_called_with(case, None)
    assert received == expected


@pytest.mark.parametrize("ok_send, case, ok_recv, msg, expected", [
    (False, 1, True, "", [False, []]),
    (True, 1, False, "{'id':1,'ok':1,'data':'[1,2,3]'}", [False, []]),
    (True, 1, True, "Not expected.", [False, []]),
    (True, 2, True, "{'id':1,'ok':1,'data':'[1,2,3]'}", [False, []]),
])
def test_exchange_error(ok_send, case, ok_recv, msg, expected):
    """WHEN the function '_exchange' is called, IF there is no working
    connection to the ABB robot or the received message from the ABB robot is
    not of the expected form, THEN the boolean value False and an empty
    list shall be returned.

    Comment:
        The format of the message to expect from the ABB robot is explained in
        the test 'test_exchange'.
    """
    abb = ABB()

    mock_send = mock.Mock()
    abb._send = mock_send
    mock_send.return_value = ok_send

    mock_client = mock.Mock()
    abb.client = mock_client
    mock_client.recv.return_value = [ok_recv, msg]

    received = abb._exchange(case)
    assert received == expected


@pytest.mark.parametrize("case, data, expected", [
    (0, None, [0] + 9*[0]),
    (1, [1, 2, 3], [1] + [1, 2, 3] + 6*[0]),
])
def test_send(case, data, expected):
    """WHEN the function '_send' is called, a command request to the ABB robot
    of the expected form for the data entry shall be made.
    """
    abb = ABB()

    mock_send = mock.Mock()
    abb.client = mock_send

    abb._send(case, data)
    abb.client.send.assert_called_with(expected)


@pytest.mark.parametrize("case, data", [
    ("a", []),
    (1, None),
    (1, 81*"a"),
    (1, 10*[0]),
])
def test_send_error(case, data):
    """WHEN the function '_send' is called, IF there is no working connection to
    the ABB robot, THEN the boolean value False shall be returned.
    """
    abb = ABB()
    ok = abb._send(case, data)
    assert ok is False
