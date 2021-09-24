# -*- encoding: utf-8 -*-
"""
tests.help.test_filing module

"""
import pytest
import os


from hio.help import filing

def test_ocfn():
    """
    Test ocfn
    """

    """Done Test"""


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


if __name__ == "__main__":
    test_filing()

