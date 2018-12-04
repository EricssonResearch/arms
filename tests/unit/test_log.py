"""Tests for arms.utils.log."""

import importlib
import logging
import pytest
from unittest import mock
from arms.config import config
from arms.utils import log


config_none = None
config_empty = {}
config_no_logger = {"color": "blue"}
config_no_file = {"logger": {"color": {"level": "wrong"}, "console": {
    "level": "warning"}}}
config_no_level = {"logger": {"file": {"color": "blue"}, "console": {
    "color": "red"}}}
config_wrong_logger = {"logger": "wrong"}
config_wrong_file = {"logger": {"file": "wrong", "console": {
    "level": "warning"}}}
config_wrong_level = {"logger": {"file": {"level": "wrong"}, "console": {
    "level": "warning"}}}


@pytest.mark.parametrize('config_data', [config_none, config_empty,
                                         config_no_logger, config_no_file,
                                         config_no_level, config_wrong_logger,
                                         config_wrong_file, config_wrong_level])
def test_config_error(config_data):
    """IF the configuration file does not include an entry for
    logging or is incomplete, THEN a corresponding error value should be set to
    True and predefined values should be used instead.
    """
    with mock.patch.object(config.var, 'data', config_data):
        pre_file_level = log.FILE_LEVEL
        pre_console_level = log.CONSOLE_LEVEL
        importlib.reload(log)
        assert log.ERROR is True
        assert log.FILE_LEVEL == pre_file_level
        assert log.CONSOLE_LEVEL == pre_console_level


@mock.patch.object(log, 'logging')
def test_init_(mock_logging):
    """The initialization of the log module shall overwrite the existing log
    file.
    """
    log.__init__()
    mock_logging.FileHandler.assert_called_with(mock.ANY, mode='w')


def test_get_logger():
    """The function 'get_logger' shall return a logger with the specified
    name in the parameter.
    """
    name = "Test"
    logger = log.get_logger(name)
    assert logger == logging.getLogger(name)

    with mock.patch.object(log, 'logging') as mock_logging:
        log.get_logger(name)
        mock_logging.getLogger.assert_called_with(name)


class TestSocketClientHandler:

    """Tests for the class SocketClientHandler."""

    def test_init(self):
        """The instance attribute 'client' shall be changeable."""
        handler = log.SocketClientHandler()

        tmp = handler.client
        handler.client = "Test"
        assert handler.client == "Test"
        handler.client = tmp
        assert handler.client == tmp

    def test_connect(self):
        """When the method 'connect' is called and a connection to the
        socket server could be made, the boolean value True shall be
        returned.
        """
        mock_socket_client = mock.Mock()
        mock_socket_client.get_config_and_connect.return_value = [True, True]

        handler = log.SocketClientHandler()
        handler.client = mock_socket_client
        ok = handler.connect()
        assert ok is True

    @mock.patch('time.sleep', return_value=None, side_effect=InterruptedError)
    def test_connect_loop(self, mock_time):
        """When the method 'connect' is called and no error occurs,
        IF no connection to the socket server could be made, THEN a new
        connection attempt shall be made.
        """
        mock_socket_client = mock.Mock()
        mock_socket_client.get_config_and_connect.return_value = [True, False]

        handler = log.SocketClientHandler()
        handler.client = mock_socket_client

        with pytest.raises(InterruptedError):
            handler.connect()
            mock_time.assert_called()

    @pytest.mark.parametrize("respond", [
        ([False, False]),
        ([False, True])
    ])
    def test_connect_fail(self, respond):
        """When the method 'connect' is called, IF an error occurred,
        THEN the boolean value False shall be returned.
        """
        mock_socket_client = mock.Mock()
        mock_socket_client.get_config_and_connect.return_value = respond

        handler = log.SocketClientHandler()
        handler.client = mock_socket_client
        ok = handler.connect()
        assert ok is False

    def test_connect_error(self):
        """IF the attribute 'client' is not an instance of the class
        'SocketClient' (arms.misc.socket -> SocketClient), WHEN the method
        'connect' is called, THEN an attribute error shall be raised.
        """
        handler = log.SocketClientHandler()
        with pytest.raises(AttributeError):
            handler.connect()

    @pytest.mark.parametrize("val, ok", [
        (None, False),
        ("Instance of SocketClient", True),
        ("Instance of SocketClient", False)
    ])
    def test_emit(self, val, ok):
        """WHERE a connection to a socket server is available,
        the method 'emit' shall send the logging output to it.
        """
        mock_client = mock.Mock()
        handler = log.SocketClientHandler()

        if val is None:
            handler.emit(mock.Mock())
            mock_client.send.assert_not_called()
        else:
            handler.client = mock_client
            mock_client.send.return_value = ok
            handler.emit(mock.Mock())
            mock_client.send.assert_called()
            if ok is True:
                assert handler.client is not None
            else:
                assert handler.client is None
