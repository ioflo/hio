# -*- encoding: utf-8 -*-
"""hio.help.mining module

Support for Mine dict subclass for shared in memory database
"""

from __future__ import annotations  # so type hints of classes get resolved later

import re
from collections.abc import Iterable, Mapping
from ..help import isNonStringIterable, NonStringIterable



# Regular expression to detect valid attribute names for Components that use Mine
# same as attribute name except '_' not allowed
NAMREX = r'^[a-zA-Z][a-zA-Z0-9]*$'
# Usage: if Renam.match(name): or if not Renam.match(name):
Renam = re.compile(NAMREX)  # compile is faster



class Mine(dict):
    """Mine subclass of dict with custom methods dunder methods and get that
    will only allow actual keys as str. Iterables passed in as key are converted
    to a "_' joined str. Uses "_" so can use dict constuctor if need be with str
    path. Assumes items in Iterable do not contain '_'.
    Supports attribute syntax to access items:
        mine.a = 5
        mine.a_b = 4

    Special staticmethods:
        tokeys(k) returns split of k at separator '_' as tuple.
    """

    def __init__(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)
        """
        self.update(*pa, **kwa)


    def __setitem__(self, k, v):
        return super(Mine, self).__setitem__(self.tokey(k), v)


    def __getitem__(self, k):
        return super(Mine, self).__getitem__(self.tokey(k))


    def __delitem__(self, k):
        return super(Mine, self).__delitem__(self.tokey(k))


    def __contains__(self, k):
        return super(Mine, self).__contains__(self.tokey(k))


    def __setattr__(self, k, v):
        try:
            getattr(dict, k)
        except AttributeError:
            try:
                return self.__setitem__(k, v)
            except Exception as ex:
                raise AttributeError(ex.args) from ex
        else:
            raise AttributeError(f"'{self.__class__.__name__}' attribute '{k}' "
                                 f"is read only")


    def __getattr__(self, k):
        if k not in self:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{k}'")
        return self.__getitem__(k)


    def get(self, k, default=None):
        if not self.__contains__(k):
            return default
        else:
            return self.__getitem__(k)


    def update(self, *pa, **kwa):
        """Convert keys that are tuples when positional argument is Iterable or
        Mapping to '.' joined strings

        dict __init__ signature options are:
            dict(**kwa)
            dict(mapping, **kwa)
            dict(iterable, **kwa)
        dict.update has same call signature
            d.update({"a": 5, "b": 2,}, c=3 , d=4)

        """
        if len(pa) > 1:
            raise TypeError(f"Expected 1 positional argument got {len(pa)}.")

        if pa:
            di = pa[0]
            if isinstance(di, Mapping):
                rd = {}
                for k, v in di.items():
                    rd[self.tokey(k)] = v
                super(Mine, self).update(rd, **kwa)

            elif isinstance(di, NonStringIterable):
                ri = []
                for k, v in di:
                    ri.append((self.tokey(k), v))
                super(Mine, self).update(ri, **kwa)

            else:
                raise TypeError(f"Expected Mapping or NonStringIterable got "
                                f"{type(di)}.")

        else:
            super(Mine, self).update(**kwa)


    @staticmethod
    def tokey(keys):
        """Joins tuple of strings keys to '_' joined string key. If already
        str then returns unchanged.

        Parameters:
            keys (Iterable[str] | str ): non-string Iteralble of path key
                    components to be '_' joined into key.
                    If keys is already str then returns unchanged

        Returns:
            key (str): '.' joined string
        """
        if isNonStringIterable(keys):
            try:
                for key in keys:
                    if key and not Renam.match(key):
                        raise KeyError(f"Invalid {key=}.")
                key = '_'.join(keys)
            except Exception as ex:
                raise KeyError(ex.args) from ex
        else:
            key = keys

        if not isinstance(key, str):
            raise KeyError(f"Expected str got {key}.")
        return key


    @staticmethod
    def tokeys(key):
        """Converts '_' joined string key to tuple of keys by splitting on '_'

        Parameters:
            key (str): '_' joined string to be split
        Returns:
            keys (tuple[str]): split of key on '_' into path key components
        """
        return tuple(key.split('_'))


