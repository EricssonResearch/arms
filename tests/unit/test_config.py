"""Tests for arms.config.config."""

from unittest import mock
from arms.config import config


def test_var_is_container():
    """The variable var shall be an instance of the class Container."""
    assert isinstance(config.var, config.Container) == True


@mock.patch.object(config, 'open')
def test_load_os_error(mock_open):
    """IF a system-related error occurs, WHEN the configuration file is
    loaded, THEN the respective error message shall be stored and the data
    field shall be empty.
    """
    mock_open.side_effect = OSError
    config.var.data = "OSError"
    config.var.load()
    assert (config.var.data is None) == True
    assert ("OSError" in config.var.error) == True


@mock.patch.object(config, 'open')
def test_load_value_error(mock_open):
    """IF a value error occurs, WHEN the configuration file is
    loaded, THEN the respective error message shall be stored and the data
    field shall be empty.
    """
    mock_open.side_effect = ValueError
    config.var.data = "ValueError"
    config.var.load()
    assert (config.var.data is None) == True
    assert ("ValueError" in config.var.error) == True
