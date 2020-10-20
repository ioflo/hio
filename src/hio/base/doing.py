# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
import time
from collections import deque, namedtuple

from ..hioing import ValidationError, VersionError
from .. import hioing
from .basing import State
from . import tyming
from ..core.tcp import serving, clienting
from ..help import timing



class Doist(tyming.Tymist):
    """
    Doist is coroutine scheduler
    Provides relative cycle time in seconds with .tyme property and advanced
    by .tick method of .tock sized increments.
    .tyme may be artificial time or real time in seconds.

    .ply method runs generators once that are synchronized to cycle time .tyme
           cycle may run as fast as possbile or run in real time.

    .run method continually runs .ply until generators are complete

    Inherited Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is float tyme increment of .tick()

    Inherited Methods:
        .tick increments .tyme by one .tock or provided tock

    Attributes:
        .real is boolean. True means run in real time, Otherwise as fast as possible.
        .limit is float maximum run tyme limit then closes all doers
        .timer is MonoTimer for real time intervals

    """
    def __init__(self, real=False, limit=None, **kwa):
        """
        Initialize instance
        Inherited Parameters:
            tyme is float initial value of cycle time in seconds
            tock is float tock time in seconds

        Parameters:
            real is boolean True means run in real time,
                            Otherwise run faster than real
            limit is float seconds for max run time of doist. None means no limit.
            doers is list of doers
        """
        super(Doist, self).__init__(**kwa)

        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.timer = timing.MonoTimer(duration = self.tock)
        self.doers = list()  # list of Doers


    def ready(self, doers=None):
        """
        Returns dogs deque of duples (dog, retyme).
        Runs each generator callable (function or method) in .doers
        to create each do generator dog.
        Runs enter context of each dog by calling next(dog)
        Parameters:

        """
        if doers is not None:
            self.doers = doers

        dogs = deque()
        for doer in self.doers:
            dog = doer(tymist=self, tock=doer.tock)
            try:
                next(dog)  # run enter by advancing to first yield
            except StopIteration:
                continue  # don't append
            dogs.append((dog, self.tyme))  #  ply is duple of (dog, retyme)
        return dogs


    def once(self, dogs):
        """
        Cycle once through dogs deque and update in place
        dogs is deque of duples of (dog, retyme) where dog is generator and
        retyme is tyme in seconds when next should run may be real or simulated

        Each cycle checks all generators in dogs deque and runs if retyme past.
        At end of cycle advances .tyme by one .tock by calling .tick()
        """
        for i in range(len(dogs)):  # iterate once over each deed
            dog, retyme = dogs.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:
                    tock = dog.send(self.tyme)  #  nothing to send for now
                    dogs.append((dog, retyme + tock))  # reappend for next pass
                    # allows for tock change during run
                except StopIteration:  # returned instead of yielded
                    pass  # effectively do exited or aborted itself

            else:  # not retyme yet
                dogs.append((dog, retyme))  # reappend for next pass

        self.tick()  # advance .tyme by one doist .tock


    def do(self, doers=None, limit=None, tyme=None):
        """
        Readies dogs deque from .doers or doers if any and then runs .once with
        dogs until completion
        Each entry in dogs is duple of (dog, retyme) where retyme is tyme in
            seconds when next should run may be real or simulated
        Each cycle runs all generators in dogs deque by calling .send on each one.

        If interrupted by exception call .close on each dog to force  exit context.

        Keyboard interrupt (cntl-c) forces exit.

        Since finally clause closes generators they must be reinited before then
        can be run again
        """
        if limit is not None:
            self.limit = abs(float(limit))

        if tyme is not None:
            self.tyme = tyme

        dogs = self.ready(doers=doers)

        tymer = tyming.Tymer(tymist=self, duration=self.limit)
        self.timer.start()
        try: #so always clean up resources if exception
            while True:  # until doers complete or exception
                try:  #CNTL-C generates keyboardInterrupt to break out of while loop

                    self.once(dogs)  # increments .tyme

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(max(0.0, self.timer.remaining))
                        self.timer.restart()  #  no time lost

                    if self.limit and tymer.expired:
                        break  # use for testing

                    if not dogs:  # no more remaining plys so done
                        break  # break out of forever loop

                except KeyboardInterrupt: # CNTL-C shutdown skedder
                    break

                except SystemExit: # Forced shutdown of process
                    raise

                except Exception:  # Unknown exception
                    raise


        finally: # finally clause always runs regardless of exception or not
            # Abort any running taskers to reclaim resources
            # Stopped or aborted taskers should have already released resources
            # if last run doer exited due to exception then try finally clause in
            # its generator is responsible for releasing resources

            while(dogs):  # .close each remaining do in plys
                dog, retime = dogs.popleft() #pop it off
                try:
                    tock = dog.close()  # force GeneratorExit
                except StopIteration:  # Hmm? What happened?
                    pass


class Doer(tyming.Tymee):
    """
    Doer base class for hierarchical structured async coroutine like generators.
    Doer.__call__ on instance returns generator
    Doer is generator creator and has extra methods and attributes that plain
    generator function does not

    Inherited Attributes:

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time

    Attributes:


    Properties:
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property

    """

    def __init__(self, tock=0.0, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance

        Parameters:
           tock is float seconds initial value of .tock

        """
        super(Doer, self).__init__(**kwa)
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


    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer
        Calling this method returns generator
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send


        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            pass

        return True # return value of yield from, or yield ex.value of StopIteration


def dog(tymist, tock=0.0):
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
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme

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
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        """
        super(TestDoer, self).__init__(**kwa)
        self.states = []


    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator
        """
        feed = "Default"
        count = 0

        try:
            # enter context

            self.states.append(State(tyme=tymist.tyme, context="enter", feed=feed, count=count))
            while (True):  # recur context
                feed = (yield (count))  # yields tock then waits for next send
                count += 1
                self.states.append(State(tyme=tymist.tyme, context="recur", feed=feed, count = count))
                if count > 3:
                    break  # normal exit

        except GeneratorExit:  # close context, forced exit due to .close
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='close', feed=feed, count=count))

        except Exception:  # abort context, forced exit due to uncaught exception
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='abort', feed=feed, count=count))
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='exit', feed=feed, count=count))

        return (True)  # return value of yield from, or yield ex.value of StopIteration


def testdog(states, tymist, tock=0.0):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=tymist.tyme, context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (count))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymist.tyme, context="recur", feed=feed, count = count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymist.tyme, context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymist.tyme, context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymist.tyme, context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


class WhoDoer(Doer):
    """
    WhoDoer supports inspecption with methods to record sends and yields

    Inherited Attributes:
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme

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
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        """
        super(WhoDoer, self).__init__(**kwa)
        self.states = []


    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator
        """
        try:
            # enter context
            count = 0
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock
            tyme = self.tyme

            self.states.append(State(tyme=tymist.tyme, context="enter", feed=tyme, count=count))
            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                count += 1
                self.states.append(State(tyme=tymist.tyme, context="recur", feed=tyme, count=count))
                if count > 3:
                    break  # normal exit

        except GeneratorExit:  # close context, forced exit due to .close
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='close', feed=tyme, count=count))

        except Exception:  # abort context, forced exit due to uncaught exception
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='abort', feed=tyme, count=count))
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            count += 1
            self.states.append(State(tyme=tymist.tyme, context='exit', feed=tyme, count=count))

        return (True)  # return value of yield from, or yield ex.value of StopIteration


def whodog(states, tymist, tock=0.0):
    """
    Generator function test example non-class based generator.
    Calling this function returns generator
    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=tymist.tyme, context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymist.tyme, context="recur", feed=feed, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymist.tyme, context='close', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymist.tyme, context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymist.tyme, context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


class ServerDoer(Doer):
    """
    Basic TCP Server

    Inherited Attributes:
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme

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
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        Parameters:
           server is TCP Server instance
        """
        super(ServerDoer, self).__init__(**kwa)
        server.tymist = self._tymist
        self.server = server


    def wind(self, tymist):
        """
        Inject new ._tymist and any other bundled tymee references
        Update any dependencies on a change in ._tymist:
            starts over itself at new ._tymists time
        """
        super(ServerDoer, self).wind(tymist)
        self.server.tymist = self._tymist


    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """

        try:
            # enter context
            self.wind(tymist)
            self.tock = tock
            tyme = self.tyme
            self.server.reopen()  #  opens accept socket

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                self.server.serviceAll()

        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            self.server.close()

        return True


class EchoServerDoer(ServerDoer):
    """
    Echo TCP Server
    Just echoes back to client whatever it receives from client

    Inherited Attributes:
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme
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

    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """


        try:
            # enter context
            self.wind(tymist)
            self.tock = tock
            tyme = self.tyme
            self.server.reopen()  #  opens accept socket

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
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

        return True


class ClientDoer(Doer):
    """
    Basic TCP Client

        Inherited Attributes:
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme

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
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        Parameters:
           client is TCP Client instance
        """
        super(ClientDoer, self).__init__(**kwa)
        client.tymist = self._tymist
        self.client = client


    def wind(self, tymist):
        """
        Inject new ._tymist and any other bundled tymee references
        Update any dependencies on a change in ._tymist:
            starts over itself at new ._tymists time
        """
        super(ClientDoer, self).wind(tymist)
        self.client.tymist = self._tymist


    def do(self, tymist, tock=0.0):
        """
        Generator method to run this doer, class based generator
        Calling this method returns generator

        Run Server
        """

        try:
            # enter context
            self.wind(tymist)
            self.tock = tock
            tyme = self.tyme
            self.client.reopen()  #  opens accept socket

            while (True):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                self.client.serviceAll()

        except GeneratorExit:  # close context, forced exit due to .close
            pass

        except Exception:  # abort context, forced exit due to uncaught exception
            raise

        finally:  # exit context,  unforced exit due to normal exit of try
            self.client.close()

        return True

