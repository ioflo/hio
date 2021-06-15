# -*- encoding: utf-8 -*-
"""
hio.help.helping module

"""
import types
import functools

from multidict import MultiDict, CIMultiDict
from orderedset import OrderedSet as oset

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




class mdict(MultiDict):
    """
    Multiple valued dictionary. Insertion order of keys preserved.
    Associated with each key is a valuelist i.e. a list of values for that key.
    Extends  MultiDict
    https://multidict.readthedocs.io/en/stable/
    MultiDict keys must be subclass of str no ints allowed
    In MultiDict:
        .add(key,value)  appends value to the valuelist at key

        m["key"] = value replaces the valuelist at key with [value]

        m["key"] returns the first added element of the valuelist at key

    MultiDict methods access values in FIFO order
    mdict adds method to access values in LIFO order

    Extended methods in mdict but not in MultiDict are:
       nabone(key [,default])  get last value at key else default or KeyError
       nab(key [,default])  get last value at key else default or None
       naball(key [,default]) get all values inverse order else default or KeyError

    """

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, list(self.items()))



    def nabone(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns last value at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def nab(self, key, *pa, **kwa):
        """
        Usage:
            .nab(key [, default])

        returns last value at key if key in dict else default
        returns None if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                return None
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def naball(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns list of values at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            # getall returns copy of list so safe to reverse
            return list(reversed(self.getall(key)))
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def firsts(self):
        """
        Returns list of (key, value) pair where each value is first value at key
        No duplicate keys

        This is useful for forked lists of values with same keys
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.getone(k)) for k in keys]


    def lasts(self):
        """
        Returns list of (key, value) pairs where each value is last value at key

        This is useful fo forked lists  of values with same keys
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.nabone(k)) for k in keys]



class imdict(CIMultiDict):
    """
    Insensitive MultiDict, Case Insensitive Keyed Multiple valued dictionary.
    Insertion order of keys preserved.
    Associated with each key is a valuelist i.e. a list of values for that key.
    Extends  CIMultiDict
    https://multidict.readthedocs.io/en/stable/
    MultiDict keys must be subclass of str no ints allowed
    In MultiDict:
        .add(key,value)  appends value to the valuelist at key

        m["key"] = value replaces the valuelist at key with [value]

        m["key"] returns the first added element of the valuelist at key

    MultiDict methods access values in FIFO order
    mdict adds method to access values in LIFO order

    Extended methods in imdict but not in MultiDict are:
       nabone(key [,default])  get last value at key else default or KeyError
       nab(key [,default])  get last value at key else default or None
       naball(key [,default]) get all values inverse order else default or KeyError
       firsts() get all items where item value is first inserted value at key
       lasts() get all items where item value is last insterted value at key
    """

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, list(self.items()))


    def nabone(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns last value at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def nab(self, key, *pa, **kwa):
        """
        Usage:
            .nab(key [, default])

        returns last value at key if key in dict else default
        returns None if key not in dict and default not provided.
        """
        try:
            return self.getall(key)[-1]
        except KeyError:
            if not pa and "default" not in kwa:
                return None
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def naball(self, key, *pa, **kwa):
        """
        Usage:
            .nabone(key [, default])

        returns list of values at key if key in dict else default
        raises KeyError if key not in dict and default not provided.
        """
        try:
            # getall returns copy of list so safe to reverse
            return list(reversed(self.getall(key)))
        except KeyError:
            if not pa and "default" not in kwa:
                raise
            elif pa:
                return pa[0]
            else:
                return kwa["default"]

    def firsts(self):
        """
        Returns list of (key, value) pair where each value is first value at key
        but with no duplicate keys. MultiDict .keys() returns a key for each
        duplicate value
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.getone(k)) for k in keys]

    def lasts(self):
        """
        Returns list of (key, value) pairs where each value is last value at key
        but with no duplicate keys. MultiDict .keys() returns a key for each
        duplicate value
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.nabone(k)) for k in keys]

