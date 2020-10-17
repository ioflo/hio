# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
from collections import deque, namedtuple

from ..hioing import ValidationError, VersionError
from .basing import State
from . import ticking
from ..core.tcp import serving, clienting

"""
Also create bare generator functions

whodo

"""

class Doer():
    """
    Doer base class for hierarchical structured async coroutine like generators.
    Doer.__call__ on instance returns generator
    Doer is generator creator and has extra methods and attributes that plain
    generator function does not

    Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

    Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    """

    def __init__(self, ticker=None, tock=0.0):
        """
        Initialize instance.
        Parameters:
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        """
        self.ticker = ticker or ticking.Ticker(tyme=0.0)
        self.tock = tock  # desired tyme interval between runs, 0.0 means asap


    def __call__(self, **kwa):
        """
        Returns generator
        Does not advance to first yield.
        The advance to first yield effectively invodes the enter or open context
        on the generator.
        To enter either call .next or .send(None) on generator
        """
        return self.do(**kwa)


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


    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock

        try:
            # enter context

            while (True):  # recur context
                feed = (yield (self.tock))  # yields tock then waits for next send


        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration


def dog(ticker, tock=0.0):
    """
    Generator function example non-class based generator
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context


        while (True):  # recur context
            feed = (yield (tock))  # yields tock then waits for next send

    except GeneratorExit:  # close context, forced exit due to .close
        pass

    except Exception:  # abort context, forced exit due to uncaught exception
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        pass

    return True # return value of yield from, or yield ex.value of StopIteration



class TestDoer(Doer):
    """
    TestDoer supports testing with methods to record sends and yields

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    Attributes:
       .states is list of State namedtuples (tyme, feed, result)

    """

    def __init__(self, **kwa):
        """
        Initialize instance.
        Parameters:
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        """
        super(TestDoer, self).__init__(**kwa)
        self.states = []


    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock
        feed = "Default"
        count = 0

        try:
            # enter context

            self.states.append(State(tyme=self.ticker.tyme, context="enter", feed=feed, count=count))
            while (True):  # recur context
                feed = (yield (count))  # yields tock then waits for next send
                count += 1
                self.states.append(State(tyme=self.ticker.tyme, context="recur", feed=feed, count = count))
                if count > 3:
                    break  # normal exit

        except GeneratorExit:  # close context, forced exit due to .close
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='close', feed=feed, count=count))

        except Exception:  # abort context, forced exit due to uncaught exception
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='abort', feed=feed, count=count))
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='exit', feed=feed, count=count))

        return (True)  # return value of yield from, or yield ex.value of StopIteration


def testdog(states, ticker, tock=0.0):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=ticker.tyme, context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (count))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=ticker.tyme, context="recur", feed=feed, count = count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=ticker.tyme, context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=ticker.tyme, context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=ticker.tyme, context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


class WhoDoer(Doer):
    """
    WhoDoer supports inspecption with methods to record sends and yields

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    Attributes:
       .states is list of State namedtuples (tyme, feed, result)

    """

    def __init__(self, **kwa):
        """
        Initialize instance.
        Parameters:
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        """
        super(WhoDoer, self).__init__(**kwa)
        self.states = []


    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock
        feed = "_"
        count = 0

        try:
            # enter context

            self.states.append(State(tyme=self.ticker.tyme, context="enter", feed=feed, count=count))
            while (True):  # recur context
                feed = (yield (self.tock))  # yields tock then waits for next send
                count += 1
                self.states.append(State(tyme=self.ticker.tyme, context="recur", feed=feed, count=count))
                if count > 3:
                    break  # normal exit

        except GeneratorExit:  # close context, forced exit due to .close
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='close', feed=feed, count=count))

        except Exception:  # abort context, forced exit due to uncaught exception
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='abort', feed=feed, count=count))
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            count += 1
            self.states.append(State(tyme=self.ticker.tyme, context='exit', feed=feed, count=count))

        return (True)  # return value of yield from, or yield ex.value of StopIteration


def whodog(states, ticker, tock=0.0):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=ticker.tyme, context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=ticker.tyme, context="recur", feed=feed, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=ticker.tyme, context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=ticker.tyme, context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=ticker.tyme, context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


class ServerDoer(Doer):
    """
    Basic TCP Server

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    Attributes:
       .server is TCP Server instance

    """

    def __init__(self, server, **kwa):
        """
        Inherited Parameters:
           ticker is Ticker instance
           tock is float seconds initial value of .tock

        Parameters:
           server is TCP Server instance
        """
        super(ServerDoer, self).__init__(**kwa)
        server.ticker = self.ticker
        self.server = server


    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock

        try:
            # enter context
            self.server.reopen()  #  opens accept socket

            while (True):  # recur context
                feed = (yield (self.tock))  # yields tock then waits for next send
                self.server.serviceAll()

        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            self.server.close()

        return


class EchoServerDoer(ServerDoer):
    """
    Echo TCP Server
    Just echoes back to client whatever it receives from client

    Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme
        .server is TCP Server instance

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    """

    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock

        try:
            # enter context
            self.server.reopen()  #  opens accept socket

            while (True):  # recur context
                feed = (yield (self.tock))  # yields tock then waits for next send
                self.server.serviceAll()

                for ca, ix in self.server.ixes.items():  # echo back
                    if ix.rxbs:
                        ix.tx(bytes(ix.rxbs))
                        ix.clearRxbs()

        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            self.server.close()

        return


class ClientDoer(Doer):
    """
    Basic TCP Client

        Inherited Attributes:
        .ticker is Ticker instance that provides relative cycle time as .ticker.tyme

    Inherited Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    Attributes:
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
        super(ClientDoer, self).__init__(**kwa)
        client.ticker = self.ticker
        self.client = client


    def do(self, ticker=None, tock=None):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """
        if ticker is not None:
            self.ticker = ticker
        if tock is not None:
            self.tock = tock

        try:
            # enter context
            self.client.reopen()  #  opens accept socket

            while (True):  # recur context
                feed = (yield (self.tock))  # yields tock then waits for next send
                self.client.serviceAll()

        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            self.client.close()

        return

