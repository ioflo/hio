# -*- encoding: utf-8 -*-
"""
tests.help.test_ogling module

"""
import pytest

import os
import logging
from hio import help
from hio.help import ogling

def test_ogler():
    """
    Test Ogler class instance that builds loggers
    """
    ogler = ogling.Ogler(name="test")
    assert ogler.path is None
    assert ogler.opened == False
    assert ogler.level == logging.ERROR  # default is ERROR
    assert ogler.path == None

    # nothing should log to file because .path not created
    # nothing should log to console because level critical
    blogger, flogger = ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")

    # console should log because error is at ogler.level == ERROR
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error

    # nothing should log  to file because .path still not created
    # but all blogger should log to console because because logging level is now DEBUG
    #  only flogger error should log to console because flogger override level is ERROR
    ogler.level = logging.DEBUG
    blogger, flogger = ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")  # flogger override level is error not log
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")  # flogger override level is error not log
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error so log

    ogler = ogling.Ogler(name="test", level=logging.DEBUG, temp=True,
                         reopen=True, clear=True)
    assert ogler.level == logging.DEBUG
    assert ogler.path.endswith("_test/hio/log/test.log")
    assert ogler.opened == True
    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ''

    # Should log to both file and console since path created flogger still uses ERRROR
    blogger, flogger = ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")  # flogger override level is error not log
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")  # flogger override level is error not log
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error so log

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    ogler.close()  # but do not clear
    assert os.path.exists(ogler.path)
    assert ogler.opened == False

    ogler.reopen(temp=True)
    assert ogler.path.endswith("_test/hio/log/test.log")
    assert ogler.opened == True
    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    blogger, flogger = ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")  # flogger override level is error not log
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")  # flogger override level is error not log
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error so log

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n'
                            'Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    path = ogler.path
    ogler.close(clear=True)
    assert not os.path.exists(path)
    assert ogler.opened == False

    help.ogler = ogling.initOgler()  # reset help.ogler to defaults
    """End Test"""


def test_init_ogler():
    """
    Test initOgler function for ogler global
    """
    #defined by default in help.__init__ on import of ogling
    assert isinstance(help.ogler, ogling.Ogler)
    assert not help.ogler.opened
    assert help.ogler.level == logging.CRITICAL  # default
    assert help.ogler.path == None

    # nothing should log to file because .path not created and level critical
    # # nothing should log to console because level critical
    blogger, flogger = help.ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")

    help.ogler.level = logging.DEBUG
    # nothing should log because .path not created despite loggin level debug
    blogger, flogger = help.ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")  # flogger override level is error not log
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")  # flogger override level is error not log
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error so log

    #reopen ogler to create path
    help.ogler.reopen(temp=True, clear=True)
    assert help.ogler.opened
    assert help.ogler.level == logging.DEBUG
    assert help.ogler.path.endswith("_test/hio/log/main.log")
    blogger, flogger = help.ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")  # flogger override level is error not log
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")  # flogger override level is error not log
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")  # flogger override level is error so log

    with open(help.ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    ogler = help.ogler = ogling.initOgler(name="test", level=logging.DEBUG,
                                          temp=True, reopen=True, clear=True)
    assert ogler.opened
    assert ogler.level == logging.DEBUG
    assert ogler.path.endswith("_test/hio/log/test.log")

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ''

    blogger, flogger = ogler.getLoggers()
    blogger.debug("Test blogger at debug level")
    flogger.debug("Test flogger at debug level")
    blogger.info("Test blogger at info level")
    flogger.info("Test flogger at info level")
    blogger.error("Test blogger at error level")
    flogger.error("Test flogger at error level")

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    path = ogler.path
    ogler.close(clear=True)
    assert not os.path.exists(path)

    help.ogler = ogling.initOgler()  # reset help.ogler to defaults
    """End Test"""


def test_set_levels():
    """
    Test setLevel on preexisting loggers
    """
    #defined by default in help.__init__ on import of ogling
    assert isinstance(help.ogler, ogling.Ogler)
    assert not help.ogler.opened
    assert help.ogler.level == logging.CRITICAL  # default
    assert help.ogler.path == None
    blogger, flogger = help.ogler.getLoggers()
    assert len(blogger.handlers) == 1
    assert len(flogger.handlers) == 1

    # blogger console: nothing should log  because level CRITICAL
    # blogger file: nothing should log because .path not created
    blogger.debug("Test blogger at debug level")
    blogger.info("Test blogger at info level")
    blogger.error("Test blogger at error level")

    # flogger console: nothing should log  because level CRITICAL
    # flogger file: nothing should log because .path not created
    flogger.debug("Test flogger at debug level")  # flogger min level is ERROR
    flogger.info("Test flogger at info level")  # flogger min level is ERROR
    flogger.error("Test flogger at error level")  # flogger min level is ERROR

    help.ogler.level = logging.DEBUG
    help.ogler.resetLevels()

    # blogger console: All should log  because level DEBUG
    # blogger file: Nothing should log because .path not created
    blogger.debug("Test blogger at debug level")
    blogger.info("Test blogger at info level")
    blogger.error("Test blogger at error level")

    # flogger console: Only error should log because min level is Error
    # flogger file: nothing should log because .path not created
    flogger.debug("Test flogger at debug level")  # flogger min level is ERROR
    flogger.info("Test flogger at info level")  # flogger min level is ERROR
    flogger.error("Test flogger at error level")  # flogger min level is ERROR

    # reopen ogler to create path
    help.ogler.reopen(temp=True, clear=True)
    assert help.ogler.opened
    assert help.ogler.level == logging.DEBUG
    assert help.ogler.path.endswith("_test/hio/log/main.log")
    # recreate loggers to pick up file handler
    blogger, flogger = help.ogler.getLoggers()
    assert len(blogger.handlers) == 2
    assert len(flogger.handlers) == 2

    # blogger console: All should log  because level DEBUG
    # blogger file: All should log because .path created
    blogger.debug("Test blogger at debug level")
    blogger.info("Test blogger at info level")
    blogger.error("Test blogger at error level")

    # flogger console: Only error should log because min level is Error
    # flogger file: Only error should log because .path created  and min level is Error
    flogger.debug("Test flogger at debug level")  # flogger min level is ERROR
    flogger.info("Test flogger at info level")  # flogger min level is ERROR
    flogger.error("Test flogger at error level")  # flogger min level is ERROR

    with open(help.ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')


    # force reinit on different path
    ogler = help.ogler = ogling.initOgler(name="test", level=logging.DEBUG,
                                          temp=True, reopen=True, clear=True)
    assert ogler.opened
    assert ogler.level == logging.DEBUG
    assert ogler.path.endswith("_test/hio/log/test.log")
    # Still have 2 handlers
    assert len(blogger.handlers) == 2
    assert len(flogger.handlers) == 2

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ''


    # blogger console: All should log  because level DEBUG
    # blogger file: None should log because old path on file handler
    blogger.debug("Test blogger at debug level")
    blogger.info("Test blogger at info level")
    blogger.error("Test blogger at error level")

    # flogger console: Only error should log because min level is Error
    # flogger file: None should log because old path on file handler
    flogger.debug("Test flogger at debug level")  # flogger min level is ERROR
    flogger.info("Test flogger at info level")  # flogger min level is ERROR
    flogger.error("Test flogger at error level")  # flogger min level is ERROR

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ''

    # recreate loggers to pick up new path
    blogger, flogger = ogler.getLoggers()
    assert len(blogger.handlers) == 2
    assert len(flogger.handlers) == 2

    # blogger console: All should log  because level DEBUG
    # blogger file: All should log because new path on file handler
    blogger.debug("Test blogger at debug level")
    blogger.info("Test blogger at info level")
    blogger.error("Test blogger at error level")

    # flogger console: Only error should log because min level is Error
    # flogger file: Error should log because new path on file handler
    flogger.debug("Test flogger at debug level")  # flogger min level is ERROR
    flogger.info("Test flogger at info level")  # flogger min level is ERROR
    flogger.error("Test flogger at error level")  # flogger min level is ERROR

    with open(ogler.path, 'r') as logfile:
        contents = logfile.read()
        assert contents == ('Test blogger at debug level\n'
                            'Test blogger at info level\n'
                            'Test blogger at error level\n'
                            '***Fail: Test flogger at error level\n')

    path = ogler.path
    ogler.close(clear=True)
    assert not os.path.exists(path)

    help.ogler = ogling.initOgler()  # reset help.ogler to defaults
    """End Test"""


if __name__ == "__main__":
    test_ogler()
    test_init_ogler()
    test_set_levels()
