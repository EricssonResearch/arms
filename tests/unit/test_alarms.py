"""Tests for arms.units.alarms.Alarms.listen"""

import pytest
import requests
from unittest import mock
from arms.config import config
from arms.units import alarms


class DotDict(dict):
    """Access the keys of a dictionary via a dot notation.

    Example:
        val = Map({'text': "No error"})
        val.text -> "No error"
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


@mock.patch.object(alarms.requests, 'get', return_value=DotDict({'text': "A"}))
def test_listen_alarm(mock_requests):
    """WHILE the webpage information for 'alarms' could be found in the
    settings (see details below), WHILE the requested server is online,
    the method 'listen' shall fetch the information from the server and return
    the boolean value True if the received error message equals the letter 'A'.

    Note that the following config entry is needed:
        arms.config.config.json -> web -> alarms -> host, port, url
    """
    alarm = alarms.Alarms()
    config_data = {"web": {"alarms": {"host": "a", "port": "b", "url": "c"}}}
    with mock.patch.object(config.var, 'data', config_data):
        assert alarm.listen() is True
        mock_requests.assert_called()


@pytest.mark.parametrize("config_data", [
    None,
    {},
    ({"color": "blue"}),
    ({"web": {"color": "blue"}}),
    ({"web": {"alarms": {"color": "blue"}}}),
    ({"web": {"alarms": {"host": "a", "color": "b", "url": "c"}}}),
])
def test_listen_dict_error(config_data):
    """IF no webpage information for 'alarms' could be found or if they are
    incomplete, THEN the boolean value False shall be returned.
    """
    alarm = alarms.Alarms()
    with mock.patch.object(config.var, 'data', config_data):
        assert alarm.listen() is False


@mock.patch.object(alarms.requests, 'get', return_value=None,
                   side_effect=requests.exceptions.RequestException)
@mock.patch('time.sleep', return_value=None)
def test_listen_request_error(mock_time, mock_requests):
    """IF the requested server is offline, WHILE the webpage information for
    'alarms' are available, the system shall sleep for awhile and try to
    fetch the information from the server again.
    """
    alarm = alarms.Alarms()
    listen = alarm.listen
    config_data = {"web": {"alarms": {"host": "a", "port": "b", "url": "c"}}}
    with mock.patch.object(config.var, 'data', config_data):
        with mock.patch.object(alarms.Alarms, 'listen', return_value="loop"):
            assert listen() == "loop"
            mock_requests.assert_called()
            mock_time.assert_called()


@mock.patch.object(alarms.requests, 'get',
                   return_value=DotDict({'text': "No error"}))
@mock.patch('time.sleep', return_value=None)
def test_listen_no_alarm(mock_time, mock_requests):
    """WHILE the webpage information for 'alarms' could be found in the
    settings, WHILE the requested server is online, the method 'listen' shall
    sleep awhile and make a request again if the fetched information does not
    equal the letter 'A'.
    """
    alarm = alarms.Alarms()
    listen = alarm.listen
    config_data = {"web": {"alarms": {"host": "a", "port": "b", "url": "c"}}}
    with mock.patch.object(config.var, 'data', config_data):
        with mock.patch.object(alarms.Alarms, 'listen', return_value="loop"):
            assert listen() == "loop"
            mock_requests.assert_called()
            mock_time.assert_called()
