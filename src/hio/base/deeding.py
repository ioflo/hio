# -*- encoding: utf-8 -*-
"""
hio.core.deeding Module
"""
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer
from .basing import Ctl, Stt
from . import cycling
from . import doing
from ..core import serving, clienting


class ServerDoer(Doer):
    """
    Basic TCP Server

    Inherited Attributes:
        .cycler is Cycler instance that provides relative cycle time as .cycler.tyme
                Ultimately a does at top level of run hierarchy are run by cycler

        .state is operational state of doer
        .desire is desired control asked by this or other taskers
        .done is doer completion state True or False
        .do = generator that runs doer

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Attributes
        .server is TCP Server instance
    """

    def __init__(self, server, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
           cycler is Cycler instance
           tock is float seconds initial value of .tock

        Parameters:
           server is TCP Server instance

        """
        super(ServerDoer, self).__init__(**kwa)
        server.cycler = self.cycler
        self.server = server


    def enter(self):
        """
        Open .server
        """
        self.server.reopen()  #  opens accept socket

    def recur(self):
        """
        Service .server
        """
        self.server.serviceAll

    def exit(self, **kwa):
        """
        Close .server
        """
        self.server.close()
        super(ServerDoer, self).exit(**kwa)



class ClientDoer(Doer):
    """
    Basic TCP Client

    Inherited Attributes:
        .cycler is Cycler instance that provides relative cycle time as .cycler.tyme
                Ultimately a does at top level of run hierarchy are run by cycler

        .state is operational state of doer
        .desire is desired control asked by this or other taskers
        .done is doer completion state True or False
        .do = generator that runs doer

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Attributes
        .client is TCP Client instance
    """

    def __init__(self, client, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
           cycler is Cycler instance
           tock is float seconds initial value of .tock

        Parameters:
           client is TCP Client instance

        """
        super(ClientDoer, self).__init__(**kwa)
        client.cycler = self.cycler
        self.client = client


    def enter(self):
        """
        Open .client
        """
        self.client.reopen()  #  opens accept socket

    def recur(self):
        """
        Service .client
        """
        self.client.serviceAll

    def exit(self, **kwa):
        """
        Close .client
        """
        self.client.close()
        super(ServerDoer, self).exit(**kwa)



