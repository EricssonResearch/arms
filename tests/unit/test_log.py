"""Tests for arms.utils.log."""

import importlib
import pytest
from unittest import mock
from arms.utils import log
from arms.config import config

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
        assert log.ERROR == True
        assert log.FILE_LEVEL == pre_file_level
        assert log.CONSOLE_LEVEL == pre_console_level


@mock.patch.object(log, 'logging')
def test_init_(mock_logging):
    """The initialization of the log module shall overwrite the existing log
    file or shall create a new one if a respective file does not exist.
    """
    log.__init__()
    mock_logging.FileHandler.assert_called_with(mock.ANY, mode='w')
