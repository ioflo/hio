# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
from collections import deque

from ..hioing import ValidationError, VersionError
from ..help.timing import MonoTimer
from .basing import Ctl, Stt
from . import playing
from ..core.tcp import serving, clienting


class Actor():
    """
    Base class for hierarchical structured async state machine generators.
    Manages state based generators

    Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme
        .state is operational state of doer
        .desire is desired control for future iteration of generator
        .done is doer completion state True or False

    Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Methods:
        .do  runs its generator  with control parameter
        .makedo  makes or remakes its generator
        .enter perform enter context actions (open setup refresh etc)
        .recur perform recurring context actions (run, repeat)
        .exit perform exit context actions (close clean up tear down etc)

    Hidden:
       ._tock is hidden attribute for .tock property
       ._do is hidden attribute for generator
       ._doer is generator function

    """

    def __init__(self, ticker=None, tock=0.0):
        """
        Initialize instance.
        Parameters:
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        """
        self.ticker = ticker or playing.Player(tyme=0.0)
        self.tock = tock  # desired tyme interval between runs, 0.0 means asap

        self.state = Stt.exited  # operational state of doer
        self.desire = Ctl.exit  # desired control next time Task is iterated
        self.done = True  # doer completion state reset on restart
        self.makedo()  # make generator assign to .run and advance to yield


    @property
    def tock(self):
        """
        tock property getter, get ._tock
        .tock is float desired .tyme increment in seconds
        """
        return self._tock


    @tock.setter
    def tock(self, tock):
        """
        desired cycle tyme interval until next run
        0.0 means run asap,
        set ._tock to tock
        """
        self._tock= abs(float(tock))


    def makedo(self):
        """
        Make and assign generator and advance to first yield
        .send(None) same as .next()
        """
        self._do = self._doer() # make generator
        state = self._do.send(None) # run to first yield and accept default status
        # next .send(control) results in first control being accepted at yield


    def do(self, control):
        """
        Returns state from iteration of generator .do after  send of control
        """
        return(self._do.send(control))


    def _doer(self):
        """
        Generator function to run this doer
        Returns generator

        Simplified state machine switch on control not state
        has less code because of defaults that just ignore control
        when it's not applicable to current state
        Status cycles:
            exited -> entered -> recurring -> exited
            exited -> entered -> recurring -> ...
            exited -> entered -> ...
            exited -> entered -> exited -> entered -> ...
            exited -> entered -> recurring -> exited -> entered -> ...

            exited -> aborted
            exited -> entered -> exited -> aborted
            exited -> entered -> recurring -> exited -> aborted


        """
        self.desire = Ctl.exit  # default what to do next time, override below
        self.state = Stt.exited # operational state of doer
        self.done = True

        try:
            while (True):
                # waits after yield of state for .send to accept new control
                control = (yield (self.state))

                if control == Ctl.recur:  # Want recur and recurring state
                    if self.state in (Stt.entered, Stt.recurring):  # Want recur
                        self.recur()  # .recur may change .desire for next run
                        self.state = Stt.recurring  # stay in recurring

                    elif self.state in (Stt.exited, ):  #  Auto enter on recur in exited
                        self.done = False   # .done may change in .enter, .recur, or .exit
                        self.enter()  # may change .desire for next run
                        self.state = Stt.entered
                        self.recur()  # may change .desire for next run
                        self.state = Stt.recurring

                    else:  # bad state for control
                        break  # break out of while loop. Forces stopIteration

                elif control == Ctl.enter:  # Want enter and entered state
                    if self.state in (Stt.exited, ):  # enter only after exit
                        self.done = False  # .done may change in .enter, .recur, or .exit
                        self.enter()  # may change .desire for next run
                        self.state = Stt.entered

                    elif self.state in  (Stt.recurring, ):  # want exit and reenter
                        # forced reenter without exit so must force exit first
                        self.exit(forced=True)  # do not set .done. May change .desire
                        self.state = Stt.exited
                        self.done = False  # .done may change in .enter, .recur, or .exit
                        self.enter()
                        self.state = Stt.entered

                    elif self.state in  (Stt.entered, ):  # already entered
                        pass  # redundant

                    else:  # bad state for control
                        break  # break out of while loop. Forces stopIteration

                elif control == Ctl.exit:  # Want exit and exited state
                    if self.state in (Stt.entered, Stt.recurring):
                        # clean exit so .done set to True
                        self.exit()  # may change.desire
                        self.state = Stt.exited
                        self.desire = Ctl.exit  #  stay in exited

                    elif self.state in  (Stt.exited, ):  # already exited
                        pass  # redundant

                    else:  # bad state for control
                        break  # break out of while loop. Forces stopIteration

                else :  # control == Ctl.abort or unknown.  Want aborted state
                    if self.state in (Stt.entered, Stt.recurring):  # force exit
                        self.exit(forced=True)  # do not set .done. May change .desire
                        self.state = Stt.exited
                    self.state = Stt.aborted
                    self.desire = Ctl.abort
                    break  # break out of while loop. Forces stopIteration

        finally:  # in case uncaught exceptio
            if self.state in (Stt.entered, Stt.recurring):  # force exit
                self.exit(forced=True)  # do not set .done. May change .desire
                self.state = Stt.exited
            self.state = Stt.aborted
            self.desire = Ctl.abort


    def enter(self):
        """
        Placeholder, Override in sub class
        """

    def recur(self):
        """
        Placeholder, Override in sub class
        """

    def exit(self, forced=False):
        """
        Placeholder, Override in sub class

        forced is boolean. True means forced exit, Otherwise false.
            Only set .done to True if not a forced exit
        """

        if not forced:  # clean unforced exit sets .done to True
            self.done = True



class ServerActor(Actor):
    """
    Basic TCP Server

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

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
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        Parameters:
           server is TCP Server instance

        """
        super(ServerActor, self).__init__(**kwa)
        server.ticker = self.ticker
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
        self.server.serviceAll()

    def exit(self, **kwa):
        """
        Close .server
        """
        self.server.close()
        super(ServerActor, self).exit(**kwa)


class EchoServerActor(ServerActor):
    """
    Echo TCP Server
    Just echoes back to client whatever it receives from client

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme
        .state is operational state of doer
        .desire is desired control asked by this or other taskers
        .done is doer completion state True or False
        .do = generator that runs doer
        .server is TCP Server instance

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    """

    def recur(self):
        """
        Service .server
        """
        super(EchoServerActor, self).recur()

        for ca, ix in self.server.ixes.items():  # echo back
            if ix.rxbs:
                ix.tx(bytes(ix.rxbs))
                ix.clearRxbs()


class ClientActor(Actor):
    """
    Basic TCP Client

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme
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
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        Parameters:
           client is TCP Client instance

        """
        super(ClientActor, self).__init__(**kwa)
        client.ticker = self.ticker
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
        self.client.serviceAll()

    def exit(self, **kwa):
        """
        Close .client
        """
        self.client.close()
        super(ClientActor, self).exit(**kwa)



class WhoActor(Actor):
    """
    For debugging stuff
    """
    def __init__(self, **kwa):
        super(WhoActor, self).__init__(**kwa)
        self.states = list()  # list of triples (states desire,done)

    # override .enter
    def enter(self):
        self.states.append((self.ticker.tyme, "enter", self.state.name, self.desire.name, self.done))

    # override .recur
    def recur(self):
        self.states.append((self.ticker.tyme, "recur", self.state.name, self.desire.name, self.done))

    def exit(self, **kwa):
        super(WhoActor, self).exit(**kwa)
        self.states.append((self.ticker.tyme, "exit", self.state.name, self.desire.name, self.done))
