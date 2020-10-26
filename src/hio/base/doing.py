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

        dogs = self.ready(doers=doers)  # runs enter context

        tymer = tyming.Tymer(tymist=self, duration=self.limit)
        self.timer.start()
        try: #so always clean up resources if exception
            while True:  # until doers complete or exception
                try:  #CNTL-C generates keyboardInterrupt to break out of while loop

                    self.once(dogs)  # increments .tyme runs recur context

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
            # exit in each dog is run by try finally clause. Each dogs exit is
            # responsible for releasing resources
            # Previously aborted or closed dogs have already exited
            # Close any running dogs in reverse order to force exit and reclaim
            # resources. enters and exits are nested pairs in reverse order so
            # nested resource dependencies are maintained.
            #  enter A, enter B, enter C, exit C, exit B, exit A
            while(dogs):  # .close each remaining do in dogs in reverse order
                dog, retime = dogs.pop() #pop it off
                try:
                    tock = dog.close()  # force GeneratorExit
                except StopIteration:
                    pass  # Hmm? Not supposed to happen!


class Doer(tyming.Tymee):
    """
    Doer base class for hierarchical structured async coroutine like generators.
    Doer.__call__ on instance returns generator.
    Interface for Doist etc is generator function like object.
    Doer is generator creator and has extra methods and attributes that plain
    generator function does not

    Inherited Attributes:

    Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time

    Properties:
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

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
        self.done = False


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
            self.tock = tock  #  set tock to parameter
            tyme = self.tyme
            self.done = False  # allows enter to override completion state
            self.enter()

            while (not self.done):  # recur context
                tyme = (yield (tock))  # yields tock then waits for next send
                self.done = self.recur(tyme=tyme)

        except GeneratorExit:  # close context, forced exit due to .close
            self.close()

        except Exception as ex:  # abort context, forced exit due to uncaught exception
            self.abort(ex=ex)
            raise

        finally:  # exit context, exit, unforced if normal exit of try, forced otherwise
            self.exit()

        # return value of yield from or StopIteration.value indicates completion
        return self.done  # Only returns done state if normal return not close or abort raise


    def enter(self):
        """
        Do 'enter' context actions. Override in subclass. Not a generator method.
        """


    def recur(self, tyme):
        """
        Do 'recur' context actions. Override in subclass.
        Parameters:
            tyme is output of send fed to do yield, Doist feeds its .tyme
        Returns completion state of recurrence actions.
           True means done False means continue
        Maybe a non-generator method or a generator method.
        For base class do:
            non-generator recur method runs until returns (True)
            generator recur method runs until returns (yield from)

        """
        return (False)


    def exit(self):
        """
        Do 'exit' context actions. Override in subclass. Not a generator method.
        """


    def close(self):
        """
        Do 'close' context actions. Override in subclass. Not a generator method.
        """


    def abort(self, ex):
        """
        Do 'abort' context actions. Override in subclass. Not a generator method.
        Parameters:
            ex is Exception instance that caused abort.
        """

def Do(tymist, tock=0.0):
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



class ServerDoer(Doer):
    """
    Basic TCP Server

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Attributes:
       .server is TCP Server instance

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
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


class WhoDoer(Doer):
    """
    WhoDoer supports introspection with methods to record sends and yields

    Inherited Attributes:
        .tymist is Tymist instance that provides relative cycle time as .tymist.tyme
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.

    Attributes:
       .states is list of State namedtuples (tyme, context, feed, count)
       .count is iteration count

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property
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
        self.count = None


    def enter(self):
        """
        """
        feed = "Default"
        self.count = 0
        self.states.append(State(tyme=self.tyme, context="enter",
                                 feed=self.tyme, count=self.count))

    def recur(self, tyme):
        """

        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context="recur",
                                 feed=self.tyme, count=self.count))
        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='exit',
                                 feed=None, count=self.count))

    def close(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='close',
                                 feed=None, count=self.count))

    def abort(self, ex):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='abort',
                                 feed=ex.args[0], count=self.count))


def WhoDo(states, tymist, tock=0.0):
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

