# -*- encoding: utf-8 -*-
"""
hio.help.hicting module

"""
from multidict import MultiDict, CIMultiDict
from orderedset import OrderedSet as oset


class Hict(CIMultiDict):
    """
    Hict is a Case Insensitive Keyed Multiple valued dictionary like class that
    extends CIMultiDict and is used for HTTP headers which have case insentive
    labels.
    Insertion order of keys preserved.
    Associated with each key is a valuelist i.e. a list of values for that key.

    https://multidict.readthedocs.io/en/stable/
    CIMultiDict keys must be subclass of str no ints allowed
    In CIMultiDict:
        .add(key,value)  appends value to the valuelist at key

        m["key"] = value replaces the valuelist at key with [value]

        m["key"] returns the first added element of the valuelist at key

    MultiDict methods access values in FIFO order
    Hict adds method to access values in LIFO order

    Extended methods in Hict but not in CIMultiDict are:
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



class Mict(MultiDict):
    """
    Mict is a multiple valued dictionary like class that extends  MultiDict.
    Insertion order of keys preserved.
    Associated with each key is a valuelist i.e. a list of values for that key.

    https://multidict.readthedocs.io/en/stable/
    MultiDict keys must be subclass of str no ints allowed
    In MultiDict:
        .add(key,value)  appends value to the valuelist at key

        m["key"] = value replaces the valuelist at key with [value]

        m["key"] returns the first added element of the valuelist at key

    MultiDict methods access values in FIFO order
    Mict adds methods to access values in LIFO order

    Extended methods in Mict but not in MultiDict are:
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
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.getone(k)) for k in keys]


    def lasts(self):
        """
        Returns list of (key, value) pairs where each value is last value at key
        No duplicate keys
        """
        keys = oset(self.keys())  # get rid of duplicates provided by .keys()
        return [(k, self.nabone(k)) for k in keys]

