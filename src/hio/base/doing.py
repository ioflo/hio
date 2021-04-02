# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
import time
from inspect import isgeneratorfunction, ismethod
from collections import deque, namedtuple

from ..hioing import ValidationError, VersionError
from .. import hioing
from .basing import State
from . import tyming
from ..core.tcp import serving, clienting
from ..help import timing, helping




class Doist(tyming.Tymist):
    """
    Doist is the root coroutine scheduler
    Provides relative cycle time in seconds with .tyme property to doers it runs
    The relative cycle time is advanced in .tock size increments by the  by  the
    .tick method.
    The doist may treat .tyme as artificial time or synchonize it to real time.

    .ready method prepares dogs (doer generators) by calling generator functions
        or generator methods and assigning to dogs list of tuples.

    .once method runs its dogs (doer generators) once per invocation.
        This synchronizes their cycle time .tyme to the Doist's tyme.


    .do method repeatedly runs .once until generators are complete
       it may either repeat as fast as possbile or repeat at real time increments.

    Inherited Class Attributes:
        .Tock is default .tock

    Attributes:
        .real is boolean. True means run in real time, Otherwise as fast as possible.
        .limit is float maximum run tyme limit then closes all doers
        .doers is list of doers
        .timer is MonoTimer for real time intervals

    Inherited Properties:
        .tyme is float relative cycle time, .tyme is artificial time
        .tock is float tyme increment of .tick()

    Properties:

    Inherited Methods:
        .tick increments .tyme by one .tock or provided tock

    Methods:
        .ready prepare doer generators (dogs)
        .once  run through dogs one time
        .do repeadedly call .once until all dogs are complete or times out

    """
    def __init__(self, real=False, limit=None, doers=None, **kwa):
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
        self.doers = doers if doers is not None else []  # list of Doers
        self.timer = timing.MonoTimer(duration = self.tock)


    def ready(self, doers=None):
        """
        Returns dogs deque of triples (dog, retyme, index)  where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            index is position of associated doer in .doers list used to assign
                .done state to associated doer for dog

        Calls each generator callable (function or method) in .doers to create
        each generator dog.

        Runs enter context of each dog by calling next(dog)

        Parameters:
            doers is list of generator method or function callables with attributes
                .tock is tyme increment in seconds
                .done is Boolean completion state
                .opts is dict() of optional parameters

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        if doers is not None:
            self.doers = doers

        dogs = deque()
        for index, doer in enumerate(self.doers):
            if ismethod(doer):  # when using bound method for generator function
                doer.__func__.done = None  # None before enter. enter may set to False
            else:
                doer.done = None  #  None before enter. enter may set to False
            opts = doer.opts if hasattr(doer, "opts") else {}
            dog = doer(tymist=self, tock=doer.tock, **opts)
            try:
                next(dog)  # run enter by advancing to first yield
            except StopIteration:
                continue  # don't append
            dogs.append((dog, self.tyme, index))
        return dogs


    def once(self, dogs):
        """
        Cycle once through dogs deque and update in place
        dogs is deque of triples of (dog, retyme, index) where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            index is position of associated doer in .doers list used to assign
                .done state to associated doer for dog

        Each cycle checks all generators in dogs deque and runs if retyme past.
        At end of cycle advances .tyme by one .tock by calling .tick()
        """
        for i in range(len(dogs)):  # iterate once over each deed
            dog, retyme, index = dogs.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:
                    tock = dog.send(self.tyme)  # send tyme. yield tock
                except StopIteration as ex:  # returned instead of yielded
                    self.doers[index].done = ex.value if ex.value else False  # assign done state
                else:  # reappend for next pass
                    if tock is None:  # bare yield returns None
                        tock = 0.0  # rerun asap when tock == 0.0
                    dogs.append((dog, retyme + tock, index))  # tock may change during run
            else:  # not retyme yet
                dogs.append((dog, retyme, index))  # reappend for next pass

        self.tick()  # advance .tyme by one doist .tock


    def do(self, doers=None, limit=None, tyme=None):
        """
        Readies dogs deque from .doers or doers if any and then runs .once with
        dogs until completion
        Each entry in dogs is triples (dog, retyme, index)  where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            index is position of associated doer in .doers list used to assign
                .done state to associated doer for dog

        If interrupted by exception call .close on each dog to force  exit context.

        Keyboard interrupt (cntl-c) forces exit.

        Once finally clause closes a generator it must be reinited
        before it can be run again

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        if limit is not None:  # time limt for running if any. useful in test
            self.limit = abs(float(limit))

        if tyme is not None:  # re-initialize starting tyme
            self.tyme = tyme

        dogs = self.ready(doers=doers)  # runs enter context on each doer

        tymer = tyming.Tymer(tymist=self, duration=self.limit)
        self.timer.start()
        try:  # always clean up resources upon exception
            while True:  # until doers complete or exception or keyboardInterrupt
                try:
                    self.once(dogs)  # increments .tyme runs recur context

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(max(0.0, self.timer.remaining))
                        self.timer.restart()  #  no time lost

                    if self.limit and tymer.expired:
                        break  # break out of forever loop

                    if not dogs:  # no more remaining dogs so done
                        break  # break out of forever loop

                except KeyboardInterrupt:  # use CNTL-C to shutdown from shell
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
                dog, retime, index = dogs.pop() #pop it off
                try:
                    tock = dog.close()  # force GeneratorExit. Maybe log exit tock tyme
                except StopIteration:
                    pass  # Hmm? Not supposed to happen!
                else:  # set done state
                    doer = self.doers[index]
                    if ismethod(doer):  # when using bound method for generator function
                        doer.__func__.done = False  # forced close
                    else:
                        doer.done = False  # forced close


def doify(f, name=None, tock=0.0, **opts):
    """
    Returns Doist compatible copy, g, of converted generator function f.
    Each invoction of doify(f) returns a unique copy of doified function f.
    Imbues copy, g, of converted generator function, f, with attributes used by
    Doist.ready() or DoDoer.enter().
    Allows multiple instances of copy, g, of generator function, f, each with
    unique attributes.

    Usage:
    def f():
       pass

    c = doify(f, name='c')

    Parameters:
        f is generator function
        name is new function name for returned doified copy g. Default is to copy
            f.__name__
        tock is default tock attribute of doified copy g
        opts is dictionary of remaining parameters that becomes .opts attribute
            of doified copy g
    """
    g = helping.copy_func(f, name=name)
    g.tock = tock  # default tock attributes
    g.done = None  # default done state
    g.opts = dict(opts)  #  default opts attribute
    return g


def doize(tock=0.0, **opts):
    """
    Returns decorator that makes decorated generator function Doist compatible.
    Imbues decorated generator function with attributes used by Doist.ready() or
    DoDoer.enter().
    Only one instance of decorated function with shared attributes is allowed.

    Usage:
    @doize
    def f():
       pass

    Parameters:
        tock is default tock attribute of doized f
        opts is dictionary of remaining parameters that becomes .opts attribute
            of doized f
    """
    def decorator(f):
        # must create copy not wrapper so inspect.isgeneratorfunction works
        # result of decoration
        g = helping.copy_func(f)
        g.tock = tock  # default tock attributes
        g.done = None  # default done state
        g.opts = dict(opts)  # default opts attribute
        return g
    return decorator


class Doer(tyming.Tymee):
    """
    Doer base class for hierarchical structured async coroutine like generators.
    Doer.__call__ on instance returns generator.
    Interface for Doist etc is generator function like object.
    Doer is generator method instance creator and has extra methods and
    attributes that a plain generator function does not

    The .do method executes other methods each corresponding to one of the
    six econtexts:
        enter, recur, clean, exit, (unforced) close, abort (forced)

    Actual context order may be one of:
        enter, recur, clean, exit
        enter, recur, close, exit
        enter, recur, abort, exit
        enter, abort, exit

    Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options into its .do generator by scheduler

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance

    Properties:
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .wind  injects ._tymist dependency

    Methods:
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
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
        self.done = None  #  default completion state
        self.opts = {}  # used for injection of options into .do by scheduler


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


    def do(self, tymist=None, tock=0.0, **opts):
        """
        Generator method to run this doer.
        Calling this method returns generator.
        Interface matches generator function for compatibility.
        To customize create subclasses and override the lifecycle methods:
            .enter, .recur, .exit, .close, .abort

        Parameters:
            tymist is injected Tymist instance with tymist.tyme
            tock is injected initial tock value
            args is dict of injected optional additional parameters
        """
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock  #  set tock to parameter
            tyme = self.tyme
            self.done = False  # allows enter to override completion state
            self.enter()

            #recur context
            if isgeneratorfunction(self.recur):  #  .recur is generator method
                self.done = yield from self.recur(tyme)  # recur context
            else:  # .recur is standard method so iterate in while loop
                while (not self.done):  # recur context
                    tyme = (yield (self.tock))  # yields .tock then waits for next send
                    self.done = self.recur(tyme=tyme)

        except GeneratorExit:  # close context, forced exit due to .close
            self.close()

        except Exception as ex:  # abort context, forced exit due to uncaught exception
            self.abort(ex=ex)
            raise

        else:  # clean context
            self.clean()

        finally:  # exit context, exit, unforced if normal exit of try, forced otherwise
            self.exit()

        # return value of yield from or StopIteration.value indicates completion
        return self.done  # Only returns done state if normal return not close or abort raise


    def enter(self):
        """
        Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.
        """


    def recur(self, tyme):
        """
        Do 'recur' context actions. Override in subclass.
        Regular method that perform repetitive actions once per invocation.
        Assumes resource setup in .enter() and resource takedown in .exit()
        (see ReDoer below for example of .recur that is a generator method)

        Returns completion state of recurrence actions.
           True means done False means continue

        Parameters:
            Doist feeds its .tyme through .send to .do yield which passes it here.


        .recur maybe implemented by a subclass either as a non-generator method
        or a generator method. This stub here is as a non-generator method.
        The base class .do detects which type:
            If non-generator .do method runs .recur method once per iteration
                until .recur returns (True)
            If generator .do method runs .recur with (yield from) until .recur
                returns (see ReDoer for example of generator .recur)

        """
        return (False)


    def clean(self):
        """
        Do 'clean' context actions. Override in subclass. Not a generator method.
        Clean up resources that are unique to a clean exit.
        Called by else after normal return.
        """

    def exit(self):
        """
        Do 'exit' context actions. Override in subclass. Not a generator method.
        Clean up resources. Comparable to context manager exit.
        Called by finally after normal return, close, or abort.
        After .exit() do returns resulting in StopIteration.
        """


    def close(self):
        """
        Do 'close' context actions. Override in subclass. Not a generator method.
        Forced close by thrown generator .close() method causing GeneratorExit.
        .exit() is finally called after .close().
        """


    def abort(self, ex):
        """
        Do 'abort' context actions. Override in subclass. Not a generator method.
        Parameters:
            ex is Exception instance that caused abort.
        Unexpected exception that results in generator exiting but not GeneratorExit.
        .exit() is finally called after .abort().
        """


class ReDoer(Doer):
    """
    ReDoer is an example sub class whose .recur is a generator method not a
    plain method. Its .do method detects that its .recur is a generator method
    and executes it using yield from instead of just calling the method.

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options into its .do generator by scheduler

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Overidden Methods:
        .recur

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property

    """

    def recur(self, tyme):
        """
        Do 'recur' context actions as a generator method. Override in subclass.
        Assumes resource setup in .enter() and resource takedown in .exit()
        (see Doer for example of .recur that is a regular method)

        yield the current .tock
        accepts the current tyme
        returns the .done

        Parameters:
            tyme is initial output of send fed to do yield, Doist feeds its .tyme
        Returns completion state of recurrence actions.
           True means done False means continue
        Maybe a non-generator method or a generator method.
        For base class do:
            non-generator recur method runs until returns (True)
            generator recur method runs until returns (yield from)

        """
        count = 0
        # print("ReDoer recur before yield. tyme = {} count={}\n".format(tyme, count))
        while (True):  # recur context
            tyme = yield(self.tock)  # first yield of None
            count += 1
            # print("ReDoer recur after yield. tyme = {} count={}\n".format(tyme, count))
            if count >= 3:
                break

        # print("ReDoer recur after break tyme = {} count={}\n".format(tyme, count))
        return True  # done



class DoDoer(Doer):
    """
    DoDoer implements Doist like functionality to allow nested scheduling of Doers.
    Each DoDoer runs a list of doers like a Doist but using the tyme from its
       injected tymist as injected by its parent DoDoer or Doist.

    Scheduling hierarchy: Doist->DoDoer...->DoDoer->Doers

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options for its generator .do

    Attributes:
        .doers is list of Doers or Doer like generator functions

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .wind  injects ._tymist dependency
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Overidden Methods:
        .do
        .enter
        .recur
        .exit

    Hidden:
       ._tymist is Tymist instance reference
       ._tock is hidden attribute for .tock property

    """

    def __init__(self, doers=None, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance

        Parameters:
           tock is float seconds initial value of .tock

        """
        super(DoDoer, self).__init__(**kwa)
        self.doers = doers if doers is not None else []


    def do(self, tymist=None, tock=0.0, doers=None, **opts):
        """
        Generator method to run this doer
        Calling this method returns generator
        Interface matched generator function for compatibility

        Parameters:
            tymist is injected Tymist instance with tymist.tyme
            tock is injected initial tock value
            opts is dict of injected optional additional parameters
        """
        dogs = deque()
        try:
            # enter context
            self.wind(tymist)  # change tymist and dependencies
            self.tock = tock  #  set tock to parameter
            tyme = self.tyme
            self.done = False  # allows enter to override completion state
            dogs = self.enter(doers=doers)

            #recur context
            while (not self.done):  # recur context
                tyme = (yield (self.tock))  # yields .tock then waits for next send
                self.done = self.recur(tyme=tyme, dogs=dogs)

        except GeneratorExit:  # close context, forced exit due to .close
            self.close()

        except Exception as ex:  # abort context, forced exit due to uncaught exception
            self.abort(ex=ex)
            raise

        else:  # clean context
            self.clean()

        finally:  # exit context, exit, unforced if normal exit of try, forced otherwise
            self.exit(dogs=dogs)

        # return value of yield from or StopIteration.value indicates completion
        return self.done  # Only returns done state if normal return not close or abort raise


    def enter(self, doers=None):
        """
        Do 'enter' context actions. Equivalent of Doist.ready()

         Returns dogs deque of triples (dog, retyme, index)  where:
            dog is generator
            retyme is tyme in seconds when next should run may be real or simulated
            index is position of associated doer in .doers list

        Calls each generator callable (function or method) in .doers to create
        each generator dog.

        Runs enter context of each dog by calling next(dog)

        Parameters:
            doers is list of generator method or function callables with attributes
                tock, done, and opts dict()

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        if doers is not None:
            self.doers = doers

        dogs = deque()
        for index, doer in enumerate(self.doers):
            if ismethod(doer):  # when using bound method for generator function
                doer.__func__.done = None  # None before enter. enter may set to False
            else:
                doer.done = None  # None before enter. enter may set to False
            opts = doer.opts if hasattr(doer, "opts") else {}
            dog = doer(tymist=self._tymist, tock=doer.tock, **opts)
            try:
                next(dog)  # run enter by advancing to first yield
            except StopIteration:
                continue  # don't append
            dogs.append((dog, self.tyme, index))
        return dogs


    def recur(self, tyme, dogs):
        """
        Do 'recur' context actions.

        Parameters:
            tyme is output of send fed to do yield, Doist feeds its .tyme

        Returns completion state of recurrence actions.
           True means done False means continue

        Cycle once through dogs deque and update in place
        dogs is deque of triples of (dog, retyme, index) where:
            dog is generator
            retyme is tyme in seconds when next should run may be real or simulated
            index is position of associated doer in .doers list

        Each cycle checks all generators in dogs deque and runs if retyme past.
        """
        for i in range(len(dogs)):  # iterate once over each deed
            dog, retyme, index = dogs.popleft()  # pop it off

            if retyme <= self.tyme:  # run it now
                try:  # tock == 0.0 means re-run asap
                    tock = dog.send(self.tyme)  # send tyme. yield tock
                except StopIteration as ex:  # returned instead of yielded
                    self.doers[index].done = ex.value if ex.value else False  # assign done state
                else:  # reappend for next pass
                    if tock is None:  # bare yield results None
                        tock = 0.0  # # rerun asap when tock == 0.0
                    dogs.append((dog, retyme + tock, index))  # tock may change during run
            else:  # not retyme yet
                dogs.append((dog, retyme, index))  # reappend for next pass

        return (not dogs)  # True if dogs empty


    def exit(self, dogs):
        """
        Do 'exit' context actions.

        Parameters:
            dogs is deque of duples (dog, retyme)

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        while(dogs):  # .close each remaining do in dogs in reverse order
            dog, retime, index = dogs.pop() #pop it off
            try:
                tock = dog.close()  # force GeneratorExit
            except StopIteration:
                pass  # Hmm? Not supposed to happen!
            else:  # set done state
                doer = self.doers[index]
                if ismethod(doer):  # when using bound method for generator function
                    doer.__func__.done = False  # forced close
                else:
                    doer.done = False  # forced close



class ServerDoer(Doer):
    """
    Basic TCP Server

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options into its .do generator by scheduler

    Attributes:
       .server is TCP Server instance

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
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


    def enter(self):
        """"""
        self.server.reopen()


    def recur(self, tyme):
        """"""
        self.server.service()


    def exit(self):
        """"""
        self.server.close()


class EchoServerDoer(ServerDoer):
    """
    Echo TCP Server
    Just echoes back to client whatever it receives from client

    Inherited Attributes:
        .server is TCP Server instance

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    """

    def enter(self):
        """"""
        self.server.reopen()


    def recur(self, tyme):
        """"""
        self.server.service()
        for ca, ix in self.server.ixes.items():  # echo back
            if ix.rxbs:
                ix.tx(bytes(ix.rxbs))
                ix.clearRxbs()


    def exit(self):
        """"""
        self.server.close()


class ClientDoer(Doer):
    """
    Basic TCP Client

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
        .tock is float, desired time in seconds between runs or until next run,
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


    def enter(self):
        """"""
        self.client.reopen()


    def recur(self, tyme):
        """"""
        self.client.service()


    def exit(self):
        """"""
        self.client.close()


class EchoConsoleDoer(Doer):
    """
    Basic Terminal Console IO to buffers. Echos input back to output

    To test in WingIde must configure Debug i/O to use external console

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Hidden:
       ._tock is hidden attribute for .tock property

    Attributes:
       .console is serial Console instance

    """

    def __init__(self, console, lines=None, txbs=None, **kwa):
        """
        Initialize instance.
        Inherited Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        Parameters:
           console is serial Console instance
           lines is deque of input bytes bytearrays of each line from console
           txbs is ouput bytes bytearray to send to console

        """
        super(EchoConsoleDoer, self).__init__(**kwa)
        self.console = console
        self.lines = lines if lines is not None else deque()
        self.txbs = txbs if txbs is not None else bytearray()


    def enter(self):
        """"""
        self.console.reopen()
        self.txbs.extend(b"Cmds: q=quit, h=help otherwise echoes.\n")
        self.txbs.extend(b"Type cmd & \n: ")


    def recur(self, tyme):
        """"""
        done = False
        prompt = False
        while self.lines:
            line = self.lines.popleft()
            #process line here
            if line == b'q':
                self.txbs.extend(b"Goodbye\n.")
                done = True  #  all done so indicate exit
                break

            elif line == b'h':
                self.txbs.extend(b"Help: type q to quit or h for help.\n")

            else:
                self.txbs.extend(b"Echo: %s\n" % line )

            prompt = True

        if prompt:
            self.txbs.extend(b"Type cmd & \n: ")


        if self.txbs:
            count =  self.console.put(self.txbs)  #  write
            del self.txbs[:count]

        line = self.console.getLine()  #  read
        if line:
            self.lines.append(line)


        return done  # keep going if done == False else ends

    def exit(self):
        """"""
        self.console.close()


def bareDo(tymist=None, tock=0.0, **opts):
    """
    Bare bones generator function template as example of generator function
    suitable for use with either doify wrapper or doize decorator.
    Make copy and rename for given application.
    Calling copied renamed function returns basic generator.
    Wrapping copied renamed function with doify returns yet unique wrapped copy
    with unique values of injected attributes and  parameters and further
    renamed by wrapper.
    Decorating copied renamed function with doize returns singleton with injected
    parameter values.

    Injected Attributes:
        g.tock = tock  # default tock attributes
        g.done = None  # default done state
        g.opts

    Parameters:
        tymist is injected Tymist instance with tymist.tyme
        tock is injected initial tock value
        opts is dict of injected optional additional parameters

    The function comments show where the 6 equivalent contexts are performed
    enter, recur, clean, exit, (unforced) close, abort (forced)
    So context order may be:
    enter, recur, clean, exit
    enter, recur, close, exit
    enter, recur, abort, exit
    enter, abort, exit
    """
    try:
        # enter context
        tyme = tymist.tyme
        done = False

        while not done:  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            #  do stuff repeately in while loop
            done = True  # means ready to exit while loop

    except GeneratorExit:  # close context upon Doist thrown .close to force early exit.
        pass  # do forced close clean up here

    except Exception as ex:  # abort context, forced exit due to uncaught exception
        pass  # do unexpected exception clean up here
        raise ex  # always re-raise exception after any exception specific actions

    else:  # clean context, clean exit processing when not (close or abort)
        pass  # do clean exit only clean up here

    finally:  # exit context,  all exits both forced and unforced come through here
        pass  # manditory clean up here

    return (done)  # returned value on final yield from, or yielded ex.value of StopIteration


class ExDoer(Doer):
    """
    ExDoer is example Doer for testing and demonstration
    Supports introspection with methods to record sends and yields

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options into its .do generator by scheduler

    Attributes:
       .states is list of State namedtuples (tyme, context, feed, count)
       .count is iteration count

    Inherited Properties:
        .tyme is float ._tymist.tyme, relative cycle or artificial time
        .tymist is Tymist instance
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

    def __init__(self, **kwa):
        """
        Initialize instance.
        Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock

        """
        super(ExDoer, self).__init__(**kwa)
        self.states = []
        self.count = None


    def enter(self):
        """"""
        self.count = 0
        self.states.append(State(tyme=self.tyme, context="enter",
                                 feed=self.tyme, count=self.count))

    def recur(self, tyme):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context="recur",
                                 feed=self.tyme, count=self.count))
        if self.count > 3:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='exit',
                                 feed=None, count=self.count))

    def close(self):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='close',
                                 feed=None, count=self.count))

    def abort(self, ex):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='abort',
                                 feed=ex.args[0], count=self.count))




def doifyExDo(tymist=None, tock=0.0, states=None, **opts):
    """
    Example generator function for testing and demonstration.
    Example non-class based generator for use with doify wrapper.
    Calling this function returns generator.
    Wrapping this function with doify returns copy with unique attributes
    """
    tyme = tymist.tyme
    count = 0
    states = states if states is not None else []

    try:
        # enter context
        states.append(State(tyme=tymist.tyme, context="enter", feed=tyme, count=count))
        while (True):  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymist.tyme, context="recur", feed=tyme, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymist.tyme, context='close', feed=None, count=count))

    except Exception as ex:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymist.tyme, context='abort', feed=ex.args[0], count=count))
        raise ex

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymist.tyme, context='exit', feed=None, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


@doize(tock=0, states=None)
def doizeExDo(tymist=None, tock=0.0, states=None, **opts):
    """
    Example decorated generator function for use with doize decorator.
    Example non-class based generator
    Calling this function returns generator
    """
    tyme = tymist.tyme
    count = 0
    states = states if states is not None else []

    try:
        # enter context
        states.append(State(tyme=tymist.tyme, context="enter", feed=tyme, count=count))
        while (True):  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymist.tyme, context="recur", feed=tyme, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # close context, forced exit due to .close
        count += 1
        states.append(State(tyme=tymist.tyme, context='close', feed=None, count=count))

    except Exception as ex:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymist.tyme, context='abort', feed=ex.args[0], count=count))
        raise ex

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymist.tyme, context='exit', feed=None, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration
