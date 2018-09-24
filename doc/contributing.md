# Contributing to arms

This document contains guidelines for contributing to *arms*, as well as useful hints when doing so.

 **Table of contents:**
- [Useful utilities](#useful-utilities)
  * [Running tests](#running-tests)
  * [Useful websites](#useful-websites)
- [Style conventions](#style-conventions)

## Useful utilities

### Running tests
*arms* uses the command line tool [tox](https://tox.readthedocs.io/en/latest/) to run its tests for the purpose of:
- making sure that the file `setup.py` is configured properly so that the final distribution can be successfully installed under the environment of Python 3.6;
- making sure that *arms* runs properly by calling the unit test framework [pytest](https://docs.pytest.org/en/latest/), which takes the test cases in the folder `tests/` in the root directory into account.

In addition the plugin [pytest-cov](https://pypi.org/project/pytest-cov/) is installed to calculate the test coverage.
When working on this project the default test suite can be easily run with the command

```
  $ tox
```

For the reason that by now *arms* only requires Python 3.6 it can be convenient to set up a local virtual environment and installing *arms* in it by following the steps:

```
  # Navigate to the GitHub folder.
  $ cd to/GitHub/

  # Create a virtual environment called 'virtual'
  $ virtualenv -p python virtual

  # Activate the virtual environment.
  $ source virtual/bin/activate

  # Install arms in 'editable' mode.
  $ pip install -e ./arms/
```

, where `$ python` is referring to Python 3.6. Then, the tests can be run by calling

```
  $ cd to/GitHub/arms
  $ pytest --cov=arms tests/
```


### Useful websites

Some handy resources:
- [The Python Standard Library](https://docs.python.org/3/library/index.html)

## Style conventions

The coding conventions of this project are based on [PEP8](http://legacy.python.org/dev/peps/pep-0008). Because its following is not controlled by [Travis CI](https://travis-ci.org/) it is recommended to use an editor with a respective checker like [PyCharm](https://www.jetbrains.com/pycharm/).  
