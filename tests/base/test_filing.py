# -*- encoding: utf-8 -*-
"""
tests.help.test_filing module

"""
import pytest
import os

from hio.base import doing
from hio.base import filing


def test_filing():
    """
    Test Filer class
    """
    dirpath = '/usr/local/var/hio/test'
    filer = filing.Filer(name="test")  # defaults
    assert filer.path == dirpath
    assert filer.opened
    assert os.path.exists(filer.path)
    assert not filer.file
    filer.close()
    assert not filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    # Test with clean
    dirpath = '/usr/local/var/hio/clean/test'
    filer = filing.Filer(name="test", clean="true")  # defaults
    assert filer.path == dirpath
    assert filer.opened
    assert os.path.exists(filer.path)
    assert not filer.file
    filer.close()
    assert not filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(clean=True)  # reuse False so remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clean=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True, clean=True)  # clear True so remake even if reuse
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.reopen(clear=True, clean=True)  # clear True so remake
    assert filer.opened
    assert filer.path == dirpath
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)


    # Test Filer with file not dir
    filepath = '/usr/local/var/hio/conf/test.txt'

    filer = filing.Filer(name="test", base="conf", filed=True)  # defaults
    assert filer.path == filepath
    assert filer.opened
    assert os.path.exists(filer.path)
    assert filer.file
    assert not filer.file.closed
    assert not filer.file.read()
    msg = f"Hello Jim\n"
    assert len(msg) == filer.file.write(msg)
    assert 0 == filer.file.seek(0)
    assert  msg == filer.file.read()

    filer.close()
    assert not filer.opened
    assert filer.file.closed
    assert filer.path == filepath
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path == filepath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path == filepath
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert not filer.file.closed
    assert filer.path == filepath
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path == filepath
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    #test openfiler with defaults temp == True
    with filing.openFiler() as filer:
        dirpath = '/tmp/hio_hcbvwdnt_test/hio/test'
        assert filer.path.startswith('/tmp/hio_')
        assert filer.path.endswith('_test/hio/test')
        assert filer.opened
        assert os.path.exists(filer.path)
        assert not filer.file

    assert not os.path.exists(filer.path)  # if temp cleans

    #test openfiler with filed == True but otherwise defaults temp == True
    with filing.openFiler(filed=True) as filer:
        dirpath = '/tmp/hio_6t3vlv7c_test/hio/test.txt'
        assert filer.path.startswith('/tmp/hio_')
        assert filer.path.endswith('_test/hio/test.txt')
        assert filer.opened
        assert os.path.exists(filer.path)
        assert filer.file
        assert not filer.file.closed

    assert not os.path.exists(filer.path)  # if temp cleans

    """Done Test"""


def test_filer_doer():
    """
    Test FilerDoer
    """
    filer0 = filing.Filer(name='test0', temp=True, reopen=False)
    assert filer0.opened == False
    assert filer0.path == None
    assert filer0.file == None

    filerDoer0 = filing.FilerDoer(filer=filer0)
    assert filerDoer0.filer == filer0
    assert filerDoer0.filer.opened == False

    filer1 = filing.Filer(name='test1', temp=True, reopen=False)
    assert filer1.opened == False
    assert filer1.path == None
    assert filer0.file == None

    filerDoer1 = filing.FilerDoer(filer=filer1)
    assert filerDoer1.filer == filer1
    assert filerDoer1.filer.opened == False

    limit = 0.25
    tock = 0.03125
    doist = doing.Doist(limit=limit, tock=tock)

    doers = [filerDoer0, filerDoer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]  #  retymes
    for doer in doers:
        assert doer.filer.opened
        assert "_test/hio/test" in doer.filer.path

    doist.recur()
    assert doist.tyme == 0.03125  # on next cycle
    assert len(doist.deeds) == 2
    for doer in doers:
        assert doer.filer.opened == True

    for dog, retyme, index in doist.deeds:
        dog.close()

    for doer in doers:
        assert doer.filer.opened == False
        assert not os.path.exists(doer.filer.path)

    # start over
    doist.tyme = 0.0
    doist.do(doers=doers)
    assert doist.tyme == limit
    for doer in doers:
        assert doer.filer.opened == False
        assert not os.path.exists(doer.filer.path)

    # test with filed == True
    filer0 = filing.Filer(name='test0', temp=True, reopen=False, filed=True)
    assert filer0.opened == False
    assert filer0.path == None
    assert filer0.file == None

    filerDoer0 = filing.FilerDoer(filer=filer0)
    assert filerDoer0.filer == filer0
    assert filerDoer0.filer.opened == False

    filer1 = filing.Filer(name='test1', temp=True, reopen=False, filed=True)
    assert filer1.opened == False
    assert filer1.path == None
    assert filer0.file == None

    filerDoer1 = filing.FilerDoer(filer=filer1)
    assert filerDoer1.filer == filer1
    assert filerDoer1.filer.opened == False

    limit = 0.25
    tock = 0.03125
    doist = doing.Doist(limit=limit, tock=tock)

    doers = [filerDoer0, filerDoer1]

    doist.doers = doers
    doist.enter()
    assert len(doist.deeds) == 2
    assert [val[1] for val in doist.deeds] == [0.0, 0.0]  #  retymes
    for doer in doers:
        assert doer.filer.opened
        assert "_test/hio/test" in doer.filer.path
        assert  doer.filer.path.endswith(".txt")
        assert doer.filer.file is not None
        assert not doer.filer.file.closed

    doist.recur()
    assert doist.tyme == 0.03125  # on next cycle
    assert len(doist.deeds) == 2
    for doer in doers:
        assert doer.filer.opened
        assert doer.filer.file is not None
        assert not doer.filer.file.closed

    for dog, retyme, index in doist.deeds:
        dog.close()

    for doer in doers:
        assert doer.filer.opened == False
        assert not os.path.exists(doer.filer.path)
        assert doer.filer.file is None

    # start over
    doist.tyme = 0.0
    doist.do(doers=doers)
    assert doist.tyme == limit
    for doer in doers:
        assert doer.filer.opened == False
        assert not os.path.exists(doer.filer.path)
        assert doer.filer.file is None

    """End Test"""



if __name__ == "__main__":
    test_filer_doer()

