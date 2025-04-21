# -*- encoding: utf-8 -*-
"""
hio.core.doing Module
"""
import time
import types
import inspect
from inspect import isgeneratorfunction
from collections import deque, namedtuple

from .. import hioing
from .basing import State
from . import tyming
from ..help import timing, helping


Deed = namedtuple("Deed", "dog retyme doer")

class Doist(tyming.Tymist):
    """
    Doist is the root coroutine scheduler
    Provides relative cycle time in seconds with .tyme property to doers it runs
    The relative cycle time is advanced in .tock size increments by the  by  the
    .tick method.
    The doist may treat .tyme as artificial time or synchonize it to real time.

    .enter method prepares deeds deque of triples (dog, retyme, doer) where
        dog is a doer generator returned by calling doer generator instances,
        functions, or methods.

    .recur method runs its deeds deque of triples (dog, retyme, doer) once per
        invocation.
        This synchronizes their cycle time .tyme to the Doist's tyme.

    .do method repeatedly runs .recur until generators are complete
       it may either repeat as fast as possbile or repeat at real time increments.

    Inherited Class Attributes:
        .Tock is default .tock

    Inherited Attributes:


    Attributes:
        name (str): unique identifier of doist uses for identifying resources of
                    doists running in child processes in multiprocessing
        real (bool): True means run in real time, Otherwise as fast as possible.
        limit (float):  maximum run tyme limit then closes all doers
        done (bool | None): True means completed due to limit or all deeds completed
                False is forced complete due to error
        doers (list): Doer class instances, generator methods or
                function callables with attributes tock, done, and opts dict().
                Used throughout the execution lifecycle.
        deeds (deque): Tuples of form (dog, retyme, doer). Where:
            dog is generator created by doer
            retyme is tyme (real or simulated) in seconds when dog should run next
            doer is associated doer in .doers list used to assign its .done state
                given completion state of its dog
            Used throughout the execution lifecycle. The normal
            case is use the default empty initialization performed here and
            update in .enter().
        timer (MonoTimer): for real time intervals
        temp (bool): True means use temp resources such as file path.
                     When True inject into doer enters when True.
                     Otherwise do not inject into doer enters.

    Inherited Properties:
        tyme: (float): starting relative cycle time, .tyme is artificial time
        tock (float | None): float tyme lag of .tick(). None means asap

    Properties:

    Inherited Methods:
        .tick increments .tyme by one .tock or provided tock

    Methods:
        .enter prepare deeds, deque of triples (dog, retyme, doer)
        .recur  run through all deeds once
        .do repeadedly call .recur until all dogs in deeds are complete or
            times out do to reaching time limit

    """
    def __init__(self, *, name='doist', real=False, limit=None, doers=None,
                          temp=False, **kwa):
        """
        Returns:
            instance

        Inherited Parameters:
            tyme (float): initial value of cycle time in seconds
            tock (float | None): lag tyme in seconds between runs, None means run ASAP

        Parameters:
            name (str): unique identifier of doist to manage resources
            real (boolean): True means run in real time,
                            Otherwise run faster than real
            limit (float): seconds for max run time of doist. None means no limit.
            doers (iterable): Doer class instances, generator methods or
                function callables with attributes tock, done, and opts dict()
                used to initialize .doers.
                The .doers attribute is used throughout the execution lifecycle.
                Parameterization elsewhere of doers enables some special cases.
                The normal case is to initialize here or in .do().
            temp (bool): True means use temp resources such as file path, inject
                         into doers when True. Otherwise do not inject.
        """
        super(Doist, self).__init__(**kwa)
        self.name = name
        self.real = True if real else False
        self.limit = abs(float(limit)) if limit is not None else None
        self.done = None
        self.doers = list(doers) if doers is not None else []  # list of Doers
        self.deeds = deque()  # deque of deeds
        self.timer = timing.MonoTimer(duration = self.tock)
        self.temp = True if temp else False


    def do(self, doers=None, limit=None, tyme=None, *, temp=None):
        """
        Readies deeds deque from .doers or doers if any and then iteratively
        runs .recur over deeds deque until completion of all deeds.
        Each entry in deeds is a triple (dog, retyme, doer)  where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            doer is from .doers list used to assign its .done state given
            associated completion state of its dog

        If interrupted by exception call .close on each dog to force exit context.

        Keyboard interrupt (cntl-c) forces exit.

        Once finally clause closes a generator it must be reinited
        before it can be run again

        Parameters:
            doers (iterable): generator method or function callables with attributes
                tock, done, and opts dict(). This may be used to update the .doers
                attribute which is used throughout the execution lifecycle.
                If not provided uses .doers.
                Parameterization here of doers enables some special cases.
                The normal case is to initialize in .__init__ or here.
            limit (float): is real time limit on execution. Forces close of all dogs.
            tyme  (float): is optional starting tyme. Resets .tyme to tyme whe provided.
               If not provided uses current .tyme
               temp (bool): True means use temp resources such as file path, inject
                         into doers when True. Otherwise do not inject.

        Returns:
            None

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        temp = temp or (self.temp if self.temp else temp)  # inject if temp or self.temp

        self.done = False
        if doers is not None:
            self.doers = list(doers)
            self.deeds = deque()

        if limit is not None:  # time limt for running if any. useful in test
            self.limit = abs(float(limit))

        if tyme is not None:  # re-initialize starting tyme
            self.tyme = tyme

        try:  # always clean up resources upon exception
            self.enter(temp=temp)  # runs enter context on each doer

            tymer = tyming.Tymer(tymth=self.tymen(), duration=self.limit)
            self.timer.start()

            while True:  # until doers complete or exception or keyboardInterrupt
                try:
                    self.recur()  # increments .tyme runs recur context

                    if self.real:  # wait for real time to expire
                        while not self.timer.expired:
                            time.sleep(max(0.0, self.timer.remaining))
                        self.timer.restart()  #  no time lost

                    if not self.deeds:  # no deeds
                        self.done = True
                        break  # break out of forever loop

                    if self.limit and tymer.expired:  # reached limit before all deeds done
                        break  # break out of forever loop

                except KeyboardInterrupt:  # Forced shutdown due to SIGINT, use CNTL-C to shutdown from shell
                    break

                except SystemExit: # Forced shutdown of process via sys.exit()
                    raise

                except Exception:  # Forced shutdown due to uncaught exception
                    raise

        finally: # finally clause always runs regardless of exception or not.
            self.exit()  # force close remaining deeds throws GeneratorExit


    def enter(self, doers=None, *, temp=None):
        """Enter context
        Returns (deque):  deeds deque of triples (dog, retyme, doer)  where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            doer is from .doers list used to assign its .done state given
                completion state of its dog

        Calls each generator callable (instance or function or method) in .doers
        to create each generator dog. Injects own tymth function closure, and
            generator function's own tock, and opts.

        Runs enter context of each dog by calling next(dog)

        Parameters:
            doers is list of generator method or function callables with attributes
                .tock is tyme increment in seconds
                .done is Boolean completion state
                .opts is dict() of optional parameters
                If not provided uses .doers.
                The normal case is to initialize in .__init__. or .do().
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Returns:
            deeds deque():
                A deed is tuple of form (dog, retyme, doer). If not provided
                uses .deeds.

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """

        if doers is None:
            doers = self.doers
            deeds = self.deeds
        else:
            deeds = deque()  # when doers is provided then don't use .deeds

        for doer in doers:
            try:
                doer.done = False  # False at enter. False signals incomplete
            except AttributeError:  # when using bound method for generator function
                doer.__func__.done = False  # False at enter. False signals incomplete

            temp = temp or (doer.temp if hasattr(doer, "temp") and doer.temp else None)
            opts = doer.opts if hasattr(doer, "opts") else {}

            dog = doer(tymth=self.tymen(), tock=doer.tock, temp=temp, **opts)  # calls doer.do
            try:
                next(dog)  # run enter by advancing to first yield
            except StopIteration as ex:   # return not yield
                # done in enter so assign done state
                try:  # assign done state non forced return
                    doer.done = ex.value if ex.value is not None else doer.done
                except AttributeError:  # bount method generator
                    # write to doer.__func__.done read from doer.done
                    doer.__func__.done = ex.value if ex.value is not None else doer.done
                continue  # don't append
            deeds.append((dog, self.tyme, doer))
        return deeds


    def recur(self, deeds=None):
        """
        Recur once through deeds deque of tuples (triples) of form
        (dog, retyme, doer) and update in place

        Each deed is deque of tuples of  form (dog, retyme, doer) where:
            dog is generator
            retyme is tyme (real or simulated) in seconds when dog should run next
            doer is from .doers list used to assign its .done state given
            associated completion state of its  dog

        Each cycle checks all generators in deeds deque and runs if retyme past.
        At end of cycle advances .tyme by one .tock by calling .tick()

        Parameters:
            deeds (deque):  tuples of form (dog, retyme, doer).
                    Parameterization here of deeds enables some special cases.

        The Parameterization here of deeds enables some special cases
        such as manual testing or iteraton.
        The normal case is to initialize .doers in .__init__. or .do() and to
        initialize .deeds in .__init__. and then update in .enter()
        """
        if deeds is None:
            deeds = self.deeds

        deeds.append((None, None, None))  # append run through once marker
        while deeds: # do while uses explicit break to exit while
            dog, retyme, doer = deeds.popleft()  # pop it off
            if not dog:  # Marker detected so this run through once has completed
                break  # break loop at marker signifies once through

            if retyme <= self.tyme:  # run it now
                try:  # send tyme. yield tock, tock may change during sended run
                    tock = dog.send(self.tyme)  # yielded tock == 0.0 means re-run asap
                except StopIteration as ex:  # returned instead of yielded
                    try:  # assign done state non forced return
                        doer.done = ex.value if ex.value is not None else doer.done
                    except AttributeError:  # bount method generator
                        # write to doer.__func__.done read from doer.done
                        doer.__func__.done = ex.value if ex.value is not None else doer.done
                else:  # reappend for next pass
                    if not tock:  # tock is None or tock == 0.0 with empty yield tock == None
                        retyme = self.tyme + self.tock  # rerun at next recur
                    else:
                        retyme += tock  # cumulative retyme of doer tock
                    deeds.append((dog, retyme, doer))  # reappend for next run through
            else:  # not retyme yet
                deeds.append((dog, retyme, doer))  # reappend for next pass

        self.tick()  # advance .tyme by one doist .tock


    def exit(self, deeds=None):
        """
        Force exit each still opened deed calling .close on the dog generator
        which throws a GeneratorExit to the generator.
        This executes the close context (GeneratorExit) which then excecutes
        the exit context in the finally caluse. Each dogs exit is responsible
        for releasing resources
        Previously aborted or closed dogs have already exited
        Close any running dogs in reverse order so that enters and exits are
        nested pairs so that the corresponding exits appear in reverse order
        to their entes. This preserves nested resource dependencies.
        For example:
            enter A,
                enter B,
                    enter C,
                    exit C,
                exit B,
            exit A

        Parameters:
            deeds (deque): tuples of form (dog, retyme, doer).
                If not provided uses .deeds.
                Parameterization here of deeds enables some special cases.
        """
        if deeds is None:
            deeds = self.deeds

        while(deeds):  # .close each remaining dog in deeds in reverse order
            dog, retime, doer = deeds.pop()  # pop it off in reverse (right side)
            if not dog:  # marker deed
                continue  # skip marker
            try:
                done = dog.close()  # force GeneratorExit. Maybe log exit tock tyme
            except StopIteration:
                pass  # Hmm? Not supposed to happen!
            else:  # set done state forced close
                try:  # not bound method generator but doer instance or function
                    doer.done = done if done is not None else doer.done
                except AttributeError:  # when using bound method generator
                    # writing to doer.__func__.done read from doer.done
                    doer.__func__.done = done if done is not None else doer.done


    def extend(self, doers):
        """
        Extend .doers list with doers. Ready deeds from doers and extend .doers
        and .deeds.  Edit deeds in place so not replace deque.

        Parameters:
            doers is list of doers to add as extension.

        """
        doers = [doer for doer in doers if doer not in self.doers] # ensure unique
        deeds = self.enter(doers=doers)  # provide fresh deeds for new doers
        self.doers.extend(doers)
        self.deeds.extend(deeds)


    def remove(self, doers):
        """
        Remove doers from .doers list and any associated deeds from .deeds deque.
        Force close removed deeds.

        Parameters:
            doers is list of doers to remove.

        """
        rdoers = [doer for doer in doers if doer in self.doers] # ensure in .doers
        rdeeds = deque()  # fresh deque for deeds to remove
        deeds = self.deeds  # edit update self.deeds in place
        for i in range(len(deeds)):  # iterate once over each deed
            dog, retyme, doer = deeds.popleft()
            if not dog:  # reappend the run through once marker deed
                deeds.append((dog, retyme, doer))
            elif doer in rdoers:  # found deed to remove and close
                rdeeds.append((dog, retyme, doer))  # add to removal deque
            else:  # keep deed do not remove and close
                deeds.append((dog, retyme, doer))  # reappend

        for doer in rdoers:  # update .doers to remove rdoers
            self.doers.remove(doer)

        self.exit(deeds=rdeeds)


def doify(f, *, name=None, tock=0.0, temp=None, **opts):
    """Returns Doist/DoDoer compatible copy, g, of converted generator
    function/method f.
    Each doify(f) invoction returns a unique copy of doified function/method f.
    Imbues copy, g, of converted generator function/method, f, with attributes
    used by Doist.enter() or DoDoer.enter().
    Allows multiple instances of copy, g, of generator function/method, f, each with
    unique attributes.

    Usage:
    def f():
       pass

    c = doify(f, name='c')

    Parameters:
        f (function): generator function
        name (str): new function name for returned doified copy g. Default is to copy
            f.__name__
        tock (float): default tock attribute of doified copy g
        temp (bool | None): use temporay file resources if any
        opts (dict): remaining parameters that becomes .opts attribute
            of doified copy g

    Based on:
    https://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance
    """
    g = helping.copyfunc(f, name=name)
    g.done = None  # default done state
    g.tock = tock  # default tock attribute
    g.temp = temp  # default temp attribute
    g.opts = dict(opts)  #  default opts attribute
    if inspect.ismethod(f):  # f.__self__ instance method
        g = types.MethodType(g, f.__self__)  # make g a method of f.__self__ only
    return g


def doize(*, tock=0.0, temp=None, **opts):
    """Returns decorator that makes decorated generator function Doist compatible.
    Imbues decorated generator function with attributes used by Doist.enter() or
    DoDoer.enter().
    Only one instance of decorated function with shared attributes is allowed.

    Usage:
    @doize
    def f():
       pass

    Parameters:
        tock (float): default tock attribute of doized f
        opts (dict): remaining parameters that becomes .opts attribute
            of doized f
    """
    def decorator(f):
        f.done = None  # default done state
        f.tock = tock  # default tock attribute
        f.temp = temp  # default temp attribute
        f.opts = dict(opts)  # default opts attribute
        return f
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
        enter, recur, clean, exit, cease (forced), abort (forced)

    Actual context order may be one of:
        enter, recur, clean, exit
        enter, recur, cease, exit
        enter, recur, abort, exit
        enter, abort, exit

    Attributes:
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        opts (dict): injected options into its .do generator by scheduler
        temp (bool): True means use temporary file resources if any

    Inherited Properties:
        tyme (float): is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): function wrapper closure returned by Tymist.tymen()
                        method. When .tymth is called it returns associated
                        Tymist.tyme. Provides injected dependency on Tymist
                        tyme base.

    Properties:
        tock (float): desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        wind  injects ._tymth dependency from associated Tymist to get its .tyme

    Methods:
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
        .exit is exit context method
        .cease is cease context method
        .abort is abort context method

    Hidden:
        _tymth (closure): is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
        _tock (float): is hidden attribute for .tock property

    """

    def __init__(self, *, tymth=None, tock=0.0, opts=None, temp=False, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymth (closure): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.

        Parameters:
           tock (float): seconds initial value of .tock
           opts (dict): injected options into its .do generator by scheduler
           temp (bool): True means use temporary file resources if any

        """
        super(Doer, self).__init__(tymth=tymth, **kwa)
        self.done = None  #  default completion state
        self.tock = tock  # desired tyme interval between runs, 0.0 means asap
        # used for injection of options into .do by scheduler
        self.opts = opts if opts is not None else {}  # empty dict if None
        self.temp = True if temp else False


    def __call__(self, **kwa):
        """
        Returns generator
        Does not advance to first yield.
        The advance to first yield effectively invokes the enter or open context
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
        self._tock = abs(float(tock))


    def do(self, tymth, *, tock=0.0, temp=None, **opts):
        """
        Generator method to run this doer.
        Calling this method returns generator.
        Interface matches generator function for compatibility.
        To customize create subclasses and override the lifecycle methods:
            .enter, .recur, .exit, .cease, .abort

        Parameters:
            tymth (closure): function wrapper closure returned by Tymist.tymen()
                        method. When .tymth is called it returns associated
                        Tymist.tyme. Provides injected dependency on Tymist
                        tyme base.
            tock (float): injected initial tock value
            temp (bool): True means use temporary file resources if any
            opts (dict): of injected optional additional parameters
        """
        temp = temp or (self.temp if self.temp else temp)  # inject if temp or self.temp

        try:
            # enter context
            self.wind(tymth)  # update tymist dependencies
            self.tock = tock  #  set tock to parameter
            self.enter(temp=temp)

            #recur context self.done set by super doist or dodoer prior to enter
            # doist.enter() or dodoer.enter() advances via doer.next() to here
            # if .recur method is generatorfunction then pauses at first yield
            #    at bottom of yield from delegation chain, i.e. next() decends
            #    the yield from delegation chain until it reaches a plain yield.
            #    note tock passed into .recur(tock) in this case is to setup
            #    the generator at enter tyme
            # else (.recur method is not generator) pauses at yield below
            if isgeneratorfunction(self.recur):  #  .recur is generator method
                self.done = yield from self.recur(tock=self.tock)  # recur context delegated
            else:  # .recur is standard method so iterate in while loop
                while (not self.done):  # recur context
                    tyme = (yield (self.tock))  # yields .tock then waits for next send
                    self.done = self.recur(tyme=tyme)  # False means recur again

        except GeneratorExit:  # close context, forced exit due to .close on generator
            self.cease()

        except Exception as ex:  # abort context, forced exit due to uncaught exception
            self.abort(ex=ex)
            raise

        else:  # clean context
            self.clean()

        finally:  # exit context, exit, unforced if normal exit of try, forced otherwise
            self.exit()

        # return value of yield from or StopIteration.value indicates completion
        # python 3.13 gh-104770: If a generator returns a value upon being
        # closed, the value is now returned by generator.close().
        return self.done  # Only returns done state if normal return or close not abort raise


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any


    def recur(self, tyme):
        """Do 'recur' context actions. Override in subclass.
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


    def cease(self):
        """
        Do 'cease' context actions. Forced exist. Override in subclass.
        Not a generator method.
        Forced cease by thrown generator.close() method causing GeneratorExit.
        .exit() is finally called after .cease().
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
    """ReDoer is an example sub class whose .recur is a generator method not a
    plain method. Its .do method detects that its .recur is a generator method
    and executes it using yield from instead of just calling the method.


    Inherited Attributes:
        done (bool | None): completion state: True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        opts (dict): injected options into its .do generator by scheduler
        temp (bool | None): use temporary file resources if any

    Inherited Properties:
        tyme (float): relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): function wrapper closure returned by Tymist.tymen() method.
            When .tymth is called it returns associated Tymist.tyme.
            .tymth provides injected dependency on Tymist tyme base.
        tock (float): desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Inherited Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
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
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property

    Test Console:
    ****** ReDoer Test **********
    ReDoer enter: temp=None in doist.enter next doer.do -> .enter
    ReDoer recur before yield: tock=1.0, tyme=None, count=0 in doist.enter next doer.do enter
    ReDoer recur after yield: tyme=0.0, count=1 in doist.recur send doer.do recur
    ReDoer recur after yield: tyme=1.0, count=2 in doist.recur send doer.do recur
    ReDoer recur after yield: tyme=2.0, count=3 in doist.recur send doer.do recur
    ReDoer recur after break: tyme=2.0, count=3


    """

    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        print(f"ReDoer enter: {temp=} in doist.enter next doer.do -> .enter")


    def recur(self, tock=None):
        """Do 'recur' context actions as a generator method. Override in subclass.

        Parameters:
            tock (float|None): this doer when creating this generator in recur
                section of its .do method supplies its .tock as this method's
                tock parameter.
                Note, the doist tyme is delegated through the 'yield from'
                to the eventual target yield at the  bottom of delegation chain.
                when tock fed back to doist is None or 0.0 it indicates to
                run again ASAP (on next iteration of doist.do)


        Returns:
           completion (bool): completion state of recurrence actions.
                              True means completed successfully
                              False completed unsuccessfully

        Note that "tyme" is not a parameter when recur is a generator method
        since doist tyme is injected by the explicit yield below.
        The recur method itself returns a generator so parameters
        to this method are to setup the generator not to be used at recur time.

        Assumes resource setup in .enter() and resource takedown in .exit()
        (see Doer for example of .recur that is a regular method)

        yield the current .tock
        accepts the current tyme
        return value is used for .done  (true done false not done but ended)



        For base class do:
            yield from this generator recur method which runs until returns

        """
        tock = tock if tock is not None else self.tock
        tyme = None
        count = 0
        print(f"ReDoer recur before yield: {tock=}, {tyme=}, {count=} in doist.enter next doer.do enter ")
        while (True):  # recur context
            # yield from advances to first yield as next() same as send(None)
            # so never see sent tyme ==0.0
            # when is recieve  tyme it will be following iteration after tick()
            # where tyme = tock
            tyme = yield(tock)
            count += 1
            print(f"ReDoer recur after yield: {tyme=}, {count=} in doist.recur send doer.do recur")
            if count >= 3:
                break

        print(f"ReDoer recur after break: {tyme=}, {count=}")
        return True  # done



class DoDoer(Doer):
    """
    DoDoer implements Doist like functionality to allow nested scheduling of Doers.
    Each DoDoer runs a list of doers like a Doist but using the tyme from its
       injected tymth for the associated tymist as injected by its ultimate root
       parent Doist and any intervening parent DoDoer(s).

    Scheduling hierarchy: Doist->DoDoer...->DoDoer->Doers

    Inherited Attributes:
        done (bool): completion state:
                    True means completed
                    Otherwise incomplete. Incompletion maybe due to close or abort.
        opts (dict): injected options for its generator .do
        temp (bool | None): use temporary file resources if any

    Attributes:

    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:
        doers (list): Doer or Doist compatible generator instances,
            functions, or methods.
        deeds (deque):  tuples of form (dog, retyme, doer)  where:
            dog is generator created by doer.
            retyme is tyme in seconds when next should run may be real or simulated.
            doer is associated doer in .doers list.
            Used throughout the execution lifecycle. The normal
            case is use the default empty initialization performed here and
            update in .enter().
        always (bool): True means keep running even when all dogs in deeds
            are complete. Enables dynamically managing extending or removing
            doers and associated deeds while running.

    Inherited Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
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
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property
       ._always is hidden attribute for .always property
       ._doers is hidden attribute for .doers property
       ._deeds is hidden attribute for .deeds property

    """

    def __init__(self, doers=None, always=False, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is float seconds initial value of .tock

        Parameters:
            doers (iterable): Doer class instances, generator methods or function
                callables with attributes tock, done, and opts dict() used to
                initialize .doers.
                The .doers attribute is used throughout the execution lifecycle.
                Parameterization elsewhere of doers enables some special cases.
                The normal case is to initialize here.

            always is Boolean, True means keep running even when all dogs in deeds
                are complete. Enables dynamically managing extending or removing
                doers and associated deeds while running.

        """
        super(DoDoer, self).__init__(**kwa)
        self.doers = list(doers) if doers is not None else []
        self.deeds = deque()
        self.always = always


    @property
    def doers(self):
        """
        doers property getter, get ._doers
        .doers is list of doist compatible generator instances, functions, or
            methods
        """
        return self._doers


    @doers.setter
    def doers(self, doers):
        """
        set ._doers to doers list
        """
        if not isinstance(doers, list):
            raise TypeError("Expected list, got {}.".format(type(doers)))
        self._doers = doers


    @property
    def deeds(self):
        """
        deeds property getter, get ._deeds
        .deeds is deque of triples, each of form (dog, retyme, doer)
        """
        return self._deeds


    @deeds.setter
    def deeds(self, deeds):
        """
        set ._deeds to deeds deque
        """
        if not isinstance(deeds, deque):
            raise TypeError("Expected deque, got {}.".format(type(deeds)))
        self._deeds = deeds


    @property
    def always(self):
        """
        always property getter, get ._always
        .always is Boolean, True means keep running even when all dogs in deeds
            are complete. Enables dynamically managing extending or removing
            doers and associated deeds while running.
        """
        return self._always


    @always.setter
    def always(self, always):
        """
        set ._always to always
        """
        self._always = True if always else False


    def do(self, tymth, tock=0.0, doers=None, always=None, *, temp=None, **opts):
        """
        Generator method to run this doer. Equivalent of doist.do
        Calling this method returns generator
        Interface matched generator function for compatibility

        Parameters:
            tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
            tock (float): injected initial tock value
            doers (list): of generator method or function callables with attributes
                tock, done, and opts dict(). This may be used to update the .doers
                attribute which is used throughout the execution lifecycle.
                If not provided uses .doers.
                Parameterization here of doers enables some special cases.
                The normal case is to initialize in .__init__.
            always (bool): True means keep running even when all dogs in deeds
                are complete. Enables dynamically managing extending or removing
                doers and associated deeds while running.
                When not provided use .always.
                temp (bool): True means use temporary file resources if any
            opts (dict): injected optional additional parameters
        """
        temp = temp or (self.temp if self.temp else temp)  # inject if temp or self.temp

        always = always if always is not None else self.always
        if doers is not None:
            self.doers = list(doers)
            self.deeds = deque()

        try:
            # enter context
            self.wind(tymth)  # change tymist dependencies
            self.tock = tock  #  set tock to parameter
            # tyme = self.tyme

            self.enter(temp=temp)  # doist.enter() equivalent

            #recur context  self.done set by super doist or dodoer prior to enter
            while (not self.done or always):  # recur context
                tyme = (yield (self.tock))  # yields .tock then waits for next send
                self.done = self.recur(tyme=tyme)  # equv of doist.recur

        except GeneratorExit:  # cease context, forced exit due to generator.close()
            self.cease()

        except Exception as ex:  # abort context, forced exit due to uncaught exception
            self.abort(ex=ex)
            raise

        else:  # clean context
            self.clean()

        finally:  # exit context, exit, unforced if normal exit of try, forced otherwise
            self.exit()  # equiv of doist.do finally clause

        # return value of yield from or StopIteration.value indicates completion
        return self.done  # Only returns done state if normal return not close or abort raise


    def enter(self, doers=None, *, temp=None):
        """Do 'enter' context actions. Equivalent of Doist.enter()
        Set up resources. Comparable to context manager enter.

        Returns deeds deque of triples (dog, retyme, doer)  where:
            dog is generator created by doer
            retyme is tyme in seconds when next should run may be real or simulated
            doer is doer for dog from doers list

        Calls each generator callable (function or method) in .doers to create
        each generator dog.

        Runs enter context of each dog by calling next(dog)

        Parameters:
            doers (list): Doer Instance, generator method or function callables
                with attributes tock, done, and opts dict().
                If not provided uses .doers.
                Parameterization here of doers enables some special cases.
                The normal case is to initialize in .__init__.

            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Returns:
            deeds (deque): A deed is tuple of form (dog, retyme, doer).
                           If not provided uses .deeds.

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        # inject temp into file resources here if any

        if doers is None:
            doers = self.doers
            deeds = self.deeds
        else:
            deeds = deque()

        for doer in doers:
            try:
                doer.done = False  # False at enter. False signals incomplete
            except AttributeError:   # when using bound method for generator function
                doer.__func__.done = False  # False at enter.  False signals incomplete
            temp = temp or (doer.temp if hasattr(doer, "temp") and doer.temp else None)
            opts = doer.opts if hasattr(doer, "opts") else {}

            dog = doer(tymth=self.tymth, tock=doer.tock, temp=temp, **opts)  # calls doer.do
            try:
                next(dog)  # run enter by advancing to first yield
            except StopIteration as ex:  # return not yield
                # done in enter so assign done state
                try:  # assign done state non forced return
                    doer.done = ex.value if ex.value is not None else doer.done
                except AttributeError:  # bount method generator
                    # write to doer.__func__.done read from doer.done
                    doer.__func__.done = ex.value if ex.value is not None else doer.done
                #try:
                    #doer.done = ex.value if ex.value else False  # assign done state
                #except AttributeError:
                    #doer.__func__.done = ex.value if ex.value else False  # assign done state


                continue  # don't append already complete
            deeds.append((dog, self.tyme, doer))
        return deeds


    def recur(self, tyme, deeds = None):
        """
        Do 'recur' context actions. Equivalent of Doist.recur

        Parameters:
            tyme (float): is output of send fed to do yield, The root scheduler
                Doist feeds its .tyme which propagates down the chain of DoDoers
                Because tymist is injected by doist or dodoer, self.tyme is same
                as tyme. So may use either which is more convenient.
             deeds (deque): tuples of form (dog, retyme, doer).
                If not provided uses .deeds.
                Parameterization here of deeds enables some special cases.

        Returns completion state of recurrence actions.
           True means done False means continue

        Cycle once through deeds deque and update in place

        Each cycle checks all generators dogs in deeds deque and runs if retyme past.
        """
        if deeds is None:
            deeds = self.deeds

        deeds.append((None, None, None))  # append run through once marker
        while deeds:  # do while uses explicit break to exit while
            dog, retyme, doer = deeds.popleft()  # pop it off
            if not dog:  # Marker detected so this run through once has completed
                break  # break loop at marker signifies once through

            if retyme <= tyme:  # run it now
                try:  # send tyme. yield tock, tock may change during sended run
                    tock = dog.send(tyme)  # yielded tock == 0.0 means re-run asap
                except StopIteration as ex:  # returned instead of yielded
                    try:  # assign done state non forced return
                        doer.done = ex.value if ex.value is not None else doer.done
                    except AttributeError:  # bount method generator
                        # write to doer.__func__.done read from doer.done
                        doer.__func__.done = ex.value if ex.value is not None else doer.done
                else:  # reappend for next pass
                    if not tock:  # tock is None or tock == 0.0 with empty yield tock == None
                        retyme = tyme + self.tock  # rerun at next recur
                    else:
                        retyme += tock  # cumulative retyme of doer tock
                    deeds.append((dog, retyme, doer))  # reappend for next run through
            else:  # not retyme yet
                deeds.append((dog, retyme, doer))  # reappend for next run through

        return (not deeds)  # True if deeds deque is empty


    def exit(self, deeds = None):
        """
        Do 'exit' context actions.

        Parameters:
            deeds (deque): of deed tuples of form (dog, retyme, doer)
                If not provided uses .deeds.
                Parameterization here of deeds enables some special cases.

        See: https://stackoverflow.com/questions/40528867/setting-attributes-on-func
        For setting attributes on bound methods.
        """
        if deeds is None:
            deeds = self.deeds

        while(deeds):  # .close each remaining dog in deeds in reverse order
            dog, retime, doer = deeds.pop()  # pop it off in reverse (right side)
            if not dog:  # marker deed
                continue  # skip marker
            try:
                done = dog.close()  # force GeneratorExit returns None if already closed or Gen Return value
            except StopIteration:
                pass  # Hmm? Not supposed to happen!
            else:  # set done state forced exit
                try:  # not bound method generator but doer instance or function
                    doer.done = done if done is not None else doer.done
                except AttributeError:  # when using bound method generator
                    # writing to doer.__func__.done read from doer.done
                    doer.__func__.done = done if done is not None else doer.done


    def extend(self, doers):
        """
        Extend .doers list with doers. Ready deeds from doers and extend .doers
        and .deeds.  Edit deeds in place so not replace deque.

        Parameters:
            doers is list of doers to add as extension.

        """
        doers = [doer for doer in doers if doer not in self.doers] # ensure unique
        deeds = self.enter(doers=doers)  # provide fresh deeds for new doers
        self.doers.extend(doers)
        self.deeds.extend(deeds)


    def remove(self, doers):
        """
        Remove doers from .doers list and any associated deeds from .deeds deque.
        Force close removed deeds.

        Parameters:
            doers is list of doers to remove.

        """
        rdoers = [doer for doer in doers if doer in self.doers] # ensure in .doers
        rdeeds = deque()  # fresh deque for deeds to remove
        deeds = self.deeds  # edit update self.deeds in place
        for i in range(len(deeds)):  # iterate once over each deed
            dog, retyme, doer = deeds.popleft()
            if not dog:  # reappend the run through once marker deed
                deeds.append((dog, retyme, doer))
            elif doer in rdoers:  # found deed to remove and close
                rdeeds.append((dog, retyme, doer))  # add to removal deque
            else:  # keep deed do not remove and close
                deeds.append((dog, retyme, doer))  # reappend

        for doer in rdoers:  # update .doers to remove rdoers
            self.doers.remove(doer)

        self.exit(deeds=rdeeds)


def bareDo(tymth=None, tock=0.0, *, temp=None, **opts):
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
        g.temp = None  # temporary resources
        g.opts = opts

    Parameters:
        tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
        tock (float): injected initial tock value
        temp (bool): True means use temporary file resources if any
        opts (dict):  injected optional additional parameters

    The function comments show where the 6 equivalent contexts are performed
    enter, recur, clean, exit, (unforced) close, abort (forced)
    So context order may be:
    enter, recur, clean, exit
    enter, recur, cease, exit
    enter, recur, abort, exit
    enter, abort, exit
    """
    try:
        # enter context
        # tyme = tymth()
        done = False

        while not done:  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            #  do stuff repeately in while loop
            done = True  # means ready to exit while loop

    except GeneratorExit:  # cease context upon Doist thrown .close to force early exit.
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

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       states (list): State namedtuples (tyme, context, feed, count)
       count (int): iteration count

    """

    def __init__(self, **kwa):
        """
        Initialize instance.
        """
        super(ExDoer, self).__init__(**kwa)
        self.states = []
        self.count = None


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        # inject temp into file resources here if any
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

    def cease(self):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='cease',
                                 feed=None, count=self.count))

    def abort(self, ex):
        """"""
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='abort',
                                 feed=ex.args[0], count=self.count))




def doifyExDo(tymth, tock=0.0, states=None, *, temp=None, **opts):
    """
    Example generator function for testing and demonstration.
    Example non-class based generator for use with doify wrapper.
    Calling this function returns generator.
    Wrapping this function with doify returns copy with unique attributes

    Parameters:
        tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
        tock (float): injected initial tock value
        states (list): State namedtuples (tyme, context, feed, count)
        temp (bool): True means use temporary file resources if any
        opts (dict): injected optional additional parameters

    """
    tyme = tymth()
    count = 0
    states = states if states is not None else []

    try:
        # enter context
        states.append(State(tyme=tymth(), context="enter", feed=tyme, count=count))
        while (True):  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymth(), context="recur", feed=tyme, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # cease context, forced exit due to generator.close
        count += 1
        states.append(State(tyme=tymth(), context='cease', feed=None, count=count))

    except Exception as ex:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymth(), context='abort', feed=ex.args[0], count=count))
        raise ex

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymth(), context='exit', feed=None, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration


@doize(tock=0, states=None)
def doizeExDo(tymth, tock=0.0, states=None, *, temp=None, **opts):
    """
    Example decorated generator function for use with doize decorator.
    Example non-class based generator
    Calling this function returns generator

    Parameters:
        tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
        tock (float): injected initial tock value
        states (list): of State namedtuples (tyme, context, feed, count)
        temp (bool): True means use temporary file resources if any
        opts (dict): injected optional additional parameters
    """
    tyme = tymth()
    count = 0
    states = states if states is not None else []

    try:
        # enter context
        states.append(State(tyme=tymth(), context="enter", feed=tyme, count=count))
        while (True):  # recur context
            tyme = (yield (tock))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymth(), context="recur", feed=tyme, count=count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # cease context, forced exit due to generator.close
        count += 1
        states.append(State(tyme=tymth(), context='cease', feed=None, count=count))

    except Exception as ex:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymth(), context='abort', feed=ex.args[0], count=count))
        raise ex

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymth(), context='exit', feed=None, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration




#  for testing purposes
class TryDoer(Doer):
    """
    TryDoer supports testing with methods to record sends and yields

    Inherited Attributes:
        done (bool | None): completion state:
                             True means completed Otherwise incomplete.
                             Incompletion maybe due to close or abort.
        opts (dict): injected options into its .do generator by scheduler
        temp (bool | None): use temporary file resources if any

    Attributes:
       states (list): State namedtuples (tyme, context, feed, count)
       count (int): is context count
       stop (int): count where doer completes

    Inherited Properties:
        tyme (float): relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
        tock (float): injected initial tock value. non negative, zero means run asap


    Properties:

    Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .exit is exit context method
        .close is close context method
        .abort is abort context method
    """

    def __init__(self, stop=3, **kwa):
        """
        Initialize instance.
        Inherited Parameters:
           tymist is Tymist instance
           tock is float seconds initial value of .tock
        Parameters:
           stop is count when complete

        """
        super(TryDoer, self).__init__(**kwa)
        self.states = []
        self.count = None
        self.stop = stop

    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any
        """
        # inject temp into file resources here if any

        feed = "Default"
        self.count = 0
        self.states.append(State(tyme=self.tyme, context="enter",
                                 feed=feed, count=self.count))

    def recur(self, tyme):
        """

        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context="recur",
                                 feed=tyme, count=self.count))
        if self.count > self.stop:
            return True  # complete
        return False  # incomplete

    def exit(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='exit',
                                 feed=None, count=self.count))

    def cease(self):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='cease',
                                 feed=None, count=self.count))

    def abort(self, ex):
        """
        """
        self.count += 1
        self.states.append(State(tyme=self.tyme, context='abort',
                                 feed=ex.args[0], count=self.count))


#  for testing purposes
@doize()
def tryDo(states, tymth, tock=0.0, *, temp=None, **opts):
    """Generator function test example non-class based generator.
    Calling this function returns generator:

    Parameters:
        tymth (closure): injected function wrapper closure returned by
                Tymist.tymen(). Calling tymth() returns associated Tymist.tyme.
        tock (float): injected initial tock value
        temp (bool): True means use temporary file resources if any
        opts (dict): injected optional additional parameters

    """
    feed = "Default"
    count = 0

    try:
        # enter context

        states.append(State(tyme=tymth(), context="enter", feed=feed, count=count))
        while (True):  # recur context
            feed = (yield (count))  # yields tock then waits for next send
            count += 1
            states.append(State(tyme=tymth(), context="recur", feed=feed, count = count))
            if count > 3:
                break  # normal exit

    except GeneratorExit:  # cease context, forced exit due to generator.close
        count += 1
        states.append(State(tyme=tymth(), context='cease', feed=feed, count=count))

    except Exception:  # abort context, forced exit due to uncaught exception
        count += 1
        states.append(State(tyme=tymth(), context='abort', feed=feed, count=count))
        raise

    finally:  # exit context,  unforced exit due to normal exit of try
        count += 1
        states.append(State(tyme=tymth(), context='exit', feed=feed, count=count))

    return (True)  # return value of yield from, or yield ex.value of StopIteration
