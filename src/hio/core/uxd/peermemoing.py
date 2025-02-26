# -*- encoding: utf-8 -*-
"""
hio.core.uxd.peermemoing Module
"""

from ... import help
from ... import hioing
from ...base import doing
from ..uxd import Peer
from ..memo import Memoer, GramDex

logger = help.ogler.getLogger()


class PeerMemoer(Peer, Memoer):
    """Class for sending memograms over UXD transport
    Mixin base classes Peer and Memoer to attain memogram over uxd transport.


    Inherited Class Attributes:
        MaxGramSize (int): absolute max gram size on tx with overhead
        See memoing.Memoer Class
        See Peer Class

    Inherited Attributes:
        See memoing.Memoer Class
        See Peer Class

    Class Attributes:


    Attributes:


    """


    def __init__(self, *, bc=4, **kwa):
        """Initialization method for instance.

        Inherited Parameters:
            bc (int | None): count of transport buffers of MaxGramSize

            See memoing.Memoer for other inherited paramters
            See Peer for other inherited paramters


        Parameters:

        """
        super(PeerMemoer, self).__init__(bc=bc, **kwa)


