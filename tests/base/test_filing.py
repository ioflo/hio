# -*- encoding: utf-8 -*-
"""
tests.base.test_filing module

"""
import platform
import shutil
import tempfile

import pytest
import os
from unittest import mock

from hio import hioing
from hio.base import doing
from hio.base import filing


def test_filing():
    """
    Test Filer class
    """

    dirpath = os.path.join(os.path.sep, 'usr', 'local', 'var', 'hio', 'test')

    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)

    altdirpath = os.path.join(os.path.expanduser('~'), '.hio', 'test')
    altdirpath = os.path.abspath(
                os.path.expanduser(altdirpath))
    if os.path.exists(altdirpath):
        shutil.rmtree(altdirpath)

    filer = filing.Filer(name="test", reopen=False)  # defaults
    assert filer.exists(name="test") is False

    filer = filing.Filer(name="test")  # defaults
    assert filer.exists(name="test") is True
    assert filer.path.endswith(os.path.join("hio", "test"))
    assert filer.opened
    assert os.path.exists(filer.path)
    assert not filer.file
    filer.close()
    assert not filer.opened

    _, pathFiler = os.path.splitdrive(os.path.normpath(filer.path))
    _, pathTest = os.path.splitdrive(os.path.normpath(dirpath))

    assert pathFiler == pathTest
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "test"))
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    # Test with clean not same as clear
    # remove both clean and not clean

    # remove both alt not clean and alt clean
    dirpath = os.path.join(os.path.expanduser('~'), '.hio', 'test')
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)
    dirpath = os.path.join(os.path.expanduser('~'), '.hio', 'clean', 'test')
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)
    dirpath = os.path.join(os.path.sep, 'usr', 'local', 'var', 'hio', 'test')  # remove both clean and not clean
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)
    dirpath = os.path.join(os.path.sep, 'usr', 'local', 'var', 'hio', 'clean', 'test')
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)

    filer = filing.Filer(name="test", clean="true", reopen=False)  # defaults
    assert filer.exists(name="test", clean="true") is False

    filer = filing.Filer(name="test", clean="true")  # defaults
    assert filer.exists(name="test", clean="true") is True

    assert filer.path.endswith(os.path.join("hio", "clean", "test"))
    assert filer.opened
    assert os.path.exists(filer.path)
    assert not filer.file
    filer.close()
    assert not filer.opened

    dirpath = os.path.join(os.path.sep, 'usr', 'local', 'var', 'hio', 'clean', 'test')

    _, pathFiler = os.path.splitdrive(os.path.normpath(filer.path))
    _, pathTest = os.path.splitdrive(os.path.normpath(dirpath))

    assert pathFiler == pathTest
    assert os.path.exists(filer.path)

    filer.reopen(clean=True)  # reuse False so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "clean", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clean=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "clean", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True, clean=True)  # clear True so remake even if reuse
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "clean", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(clear=True, clean=True)  # clear True so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join("hio", "clean", "test"))
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    # test with alt
    #dirpath = '/Users/samuel/.hio/test'
    dirpath = os.path.join(os.path.expanduser('~'), '.hio', 'test')
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)

    headDirPath = os.path.join(os.path.sep, 'root', 'hio')
    if platform.system() == 'Windows':
        headDirPath = 'C:\\System Volume Information\\hio'
    headDirPath = os.path.join(headDirPath, 'hio')

    # headDirPath that is not permitted to force using AltPath
    filer = filing.Filer(name="test", headDirPath=headDirPath, reopen=False)
    assert filer.exists(name="test", headDirPath=headDirPath) is False


    filer = filing.Filer(name="test", headDirPath=headDirPath, reopen=True)

    assert filer.exists(name="test", headDirPath=headDirPath) is True
    assert filer.path.endswith(os.path.join(".hio", "test"))

    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert filer.opened
    assert os.path.exists(filer.path)
    assert not filer.file
    filer.close()
    assert not filer.opened
    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert filer.path.endswith(os.path.join(".hio", "test"))
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    # Test Filer with file not dir
    filepath = os.path.join(os.path.sep, 'usr', 'local', 'var', 'hio', 'conf', 'test.text')
    if os.path.exists(filepath):
        os.remove(filepath)
    alt_filepath = os.path.join(os.path.expanduser('~'), '.hio', 'conf', 'test.text')
    if os.path.exists(alt_filepath):
        os.remove(alt_filepath)

    assert os.path.exists(filepath) is False
    filer = filing.Filer(name="test", base="conf", filed=True, reopen=False)
    assert filer.exists(name="test", base="conf", filed=True) is False

    filer = filing.Filer(name="test", base="conf", filed=True)
    assert filer.exists(name="test", base="conf", filed=True) is True
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
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
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join("hio", "conf", "test.text"))
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    # Test Filer with file not dir and with Alt path
    filepath = os.path.join(os.path.expanduser('~'), '.hio', 'conf', 'test.text')
    if os.path.exists(filepath):
        os.remove(filepath)

    headDirPath = os.path.join(os.path.sep, 'root', 'hio')
    if platform.system() == 'Windows':
        headDirPath = 'C:\\System Volume Information'

    # force altPath by using headDirPath of "/root/hio" which is not permitted
    filer = filing.Filer(name="test", base="conf", headDirPath=headDirPath, filed=True, reopen=False)
    assert filer.exists(name="test", base="conf", headDirPath=headDirPath, filed=True) is False

    filer = filing.Filer(name="test", base="conf", headDirPath=headDirPath, filed=True)

    assert filer.exists(name="test", base="conf", headDirPath=headDirPath, filed=True) is True
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
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
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
    assert os.path.exists(filer.path)

    filer.reopen()  # reuse False so remake but file exists so opens not creates
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True)  # reuse True and clear False so don't remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
    assert os.path.exists(filer.path)

    filer.reopen(reuse=True, clear=True)  # clear True so remake even if reuse
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
    assert os.path.exists(filer.path)

    filer.reopen(clear=True)  # clear True so remake
    assert filer.opened
    assert not filer.file.closed
    assert filer.path.endswith(os.path.join('.hio', 'conf', 'test.text'))
    assert os.path.exists(filer.path)

    filer.close(clear=True)
    assert not os.path.exists(filer.path)

    #test openfiler with defaults temp == True
    with filing.openFiler() as filer:
        tempDirPath = os.path.join(os.path.sep, "tmp") if platform.system() == "Darwin" else tempfile.gettempdir()
        #dirPath = os.path.join(tempDirPath, 'hio_hcbvwdnt_test', 'hio', 'test')
        #assert dirPath.startswith(os.path.join(tempDirPath, 'hio_'))
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(filer.path)
        assert path.startswith(os.path.join(tempDirPath, "hio_"))
        assert filer.path.endswith(os.path.join('_test', 'hio', 'test'))
        assert filer.opened
        assert os.path.exists(filer.path)
        assert not filer.file
    assert not os.path.exists(filer.path)  # if temp clears

    #test openfiler with filed == True but otherwise defaults temp == True
    with filing.openFiler(filed=True) as filer:
        tempDirPath = os.path.join(os.path.sep, "tmp") if platform.system() == "Darwin" else tempfile.gettempdir()
        #dirPath = os.path.join(tempDirPath, 'hio_6t3vlv7c_test', 'hio', 'test.text')
        #assert dirPath.startswith(os.path.join(tempDirPath, 'hio_'))
        tempDirPath = os.path.normpath(tempDirPath)
        path = os.path.normpath(filer.path)
        assert path.startswith(os.path.join(tempDirPath, "hio_"))
        assert filer.path.endswith(os.path.join('_test', 'hio', 'test.text'))
        assert filer.opened
        assert os.path.exists(filer.path)
        assert filer.file
        assert not filer.file.closed
    assert not os.path.exists(filer.path)  # if temp clears

    headDirPath = os.path.join(os.path.sep, 'root', 'hio')
    if platform.system() == 'Windows':
        headDirPath = 'C:\\System Volume Information'
    # test alternate path use headDirPath not permitted to force use altPath
    with filing.openFiler(filed=True, temp=False, headDirPath=headDirPath, clear=True) as  filer:
        assert filer.path.endswith(os.path.join('.hio', 'test.text'))  # uses altpath
        assert filer.opened
        assert os.path.exists(filer.path)
        assert filer.file
        assert not filer.file.closed
    assert not os.path.exists(filer.path)  # not temp but clear=True


    # Test bad file path components
    with pytest.raises(hioing.FilerError):
        name = "/test"
        if platform.system() == 'Windows':
            name = "C:\\test"
        filer = filing.Filer(name=name, base="conf", filed=True)

    with pytest.raises(hioing.FilerError):
        conf = "/conf"
        if platform.system() == 'Windows':
            conf = "C:\\conf"
        filer = filing.Filer(name="test", base=conf, filed=True)

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
        assert os.path.join('_test', 'hio', 'test') in doer.filer.path

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
        assert os.path.join('_test', 'hio', 'test') in doer.filer.path
        assert doer.filer.path.endswith(".text")
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
    test_filing()
    test_filer_doer()

