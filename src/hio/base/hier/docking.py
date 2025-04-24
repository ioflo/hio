# -*- encoding: utf-8 -*-
"""hio.base.hier.docking module

Support for Dock class

"""
from ...hold import Holder, Suber, IoSetSuber


class Dock(Holder):
    """Dock subclass of Holder for managing durable storage action data

    """
    def __init__(self, **kwa):
        """
        Setup named sub databases.

        Inherited Parameters:  (see Holder)


        """
        super(Dock, self).__init__(**kwa)


    def reopen(self, **kwa):
        """Open sub databases

        Attributes:
            cans (Suber): subdb whose values are serialized Can instances
                Can is a durable Bag
            drqs (IoSetSub): subdb whose values are serialized Durq instances
                Durq is a durable Deck (deque)

        """
        super(Dock, self).reopen(**kwa)

        self.cans = Suber(db=self, subkey='cans.')
        self.drqs = IoSetSuber(db=self, subkey="drqs.")

        return self.env
