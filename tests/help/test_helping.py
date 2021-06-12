# -*- encoding: utf-8 -*-
"""
tests.help.test_helping module

"""
import pytest

from hio.help import helping

def test_copy_func():
    """
    Test the utility function for copying functions
    """
    def a(x=1):
        return x
    assert a() == 1
    assert a.__name__ == 'a'
    a.m = 2

    b = helping.copy_func(a, name='b')
    assert b.__name__ == 'b'
    b.m = 4

    assert a.m != b.m
    assert a.__name__ == 'a'

    assert id(a) != id(b)

    """Done Test"""

def test_just():
    """
    Test just function
    """

    x = (1, 2, 3, 4)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2, 3)
    assert tuple(helping.just(3, x)) == (1, 2, 3)

    x = (1, 2)
    assert tuple(helping.just(3, x)) == (1, 2, None)

    x = (1, )
    assert tuple(helping.just(3, x)) == (1, None, None)

    x = ()
    assert tuple(helping.just(3, x)) == (None, None, None)

def test_repack():
    """
    Test repack function
    """
    x = (1, 2, 3, 4)
    assert tuple(helping.repack(3, x)) == (1, 2, (3, 4))

    x = (1, 2, 3)
    assert tuple(helping.repack(3, x)) == (1, 2, (3,))

    x = (1, 2)
    assert tuple(helping.repack(3, x)) == (1, 2, ())

    x = (1, )
    assert tuple(helping.repack(3, x)) == (1, None, ())

    x = ()
    assert tuple(helping.repack(3, x)) == (None, None, ())




if __name__ == "__main__":
    test_copy_func()
