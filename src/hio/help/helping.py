# -*- encoding: utf-8 -*-
"""
hio.help.helping module

"""

import types
import functools


def copy_func(f, name=None):
    """
    Copy a function in detail.
    To change name of func provide name parameter

    functools to update_wrapper assigns and updates following attributes
    WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__',
                       '__annotations__')
    WRAPPER_UPDATES = ('__dict__',)
    Based on
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python
    https://stackoverflow.com/questions/13503079/how-to-create-a-copy-of-a-python-function
    """
    g = types.FunctionType(f.__code__,
                           f.__globals__,
                           name=f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__
                          )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    if name:
        g.__name__ = name
    return g


def repack(n, seq, default=None):
    """ Repacks seq into a generator of len n and returns the generator.
        The purpose is to enable unpacking into n variables.
        The first n-1 elements of seq are returned as the first n-1 elements of the
        generator and any remaining elements are returned in a tuple as the
        last element of the generator
        default (None) is substituted for missing elements when len(seq) < n

        Example:

        x = (1, 2, 3, 4)
        tuple(repack(3, x))
        (1, 2, (3, 4))

        x = (1, 2, 3)
        tuple(repack(3, x))
        (1, 2, (3,))

        x = (1, 2)
        tuple(repack(3, x))
        (1, 2, ())

        x = (1, )
        tuple(repack(3, x))
        (1, None, ())

        x = ()
        tuple(repack(3, x))
        (None, None, ())

    """
    it = iter(seq)
    for i in range(n - 1):
        yield next(it, default)
    yield tuple(it)


def just(n, seq, default=None):
    """ Returns a generator of just the first n elements of seq and substitutes
        default (None) for any missing elements. This guarantees that a generator of exactly
        n elements is returned. This is to enable unpacking into n varaibles

        Example:

        x = (1, 2, 3, 4)
        tuple(just(3, x))
        (1, 2, 3)
        x = (1, 2, 3)
        tuple(just(3, x))
        (1, 2, 3)
        x = (1, 2)
        tuple(just(3, x))
        (1, 2, None)
        x = (1, )
        tuple(just(3, x))
        (1, None, None)
        x = ()
        tuple(just(3, x))
        (None, None, None)

    """
    it = iter(seq)
    for i in range(n):
        yield next(it, default)
