# hio is a Hierarchically Structured Concurrency with Asynchronous IO Library in Python

## Rich Flow Based Programming Hierarchical Structured Concurrency with Asynchronous IO

This builds on very early work on hierarchical structured concurrency with
lifecycle contexts from [ioflo](https://ioflo.com),
[ioflo github](https://github.com/ioflo/ioflo), and
[ioflo manuals](https://github.com/ioflo/ioflo_manuals).

This approach is compatible with flow based programming that sees all components
as asynchronous and linked by asynchronous buffers. FPB naturally lends itself
to a much lighter weight async structure based on a hierachical scheduling approach.

This is even lighter weight and more performant than non-hierarchical structured
concurrency approaches such as trio or curio.

## Structured Concurrency with Asynchronous IO

More recently the [curio](https://curio.readthedocs.io/en/latest/) and
[trio](https://trio.readthedocs.io/en/stable/) libraries have popularized
coroutine based [structured concurrency](https://en.wikipedia.org/wiki/Structured_concurrency).

See here for why it matters ...
[here](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/)
and
[here](https://vorpus.org/blog/companion-post-for-my-pycon-2018-talk-on-async-concurrency-using-trio/)

The main difference between hio and curio or trio is that hio uses extremely
lightweight asynchronous hierarchical co-routine scheduling. The scheduler only
does one thing, that is, time slice sub coroutines or sub coroutine schedulers.

The coroutines are responsible for managing the asynchrounous IO not the scheduler.
This is compatible with a flow based programming (FBP) approach where Async IO only services
buffers. All interaction with other system components happens through those buffers
not some other mechanism. And certainly not a mechanism provided by the async
scheduler.  This makes the architecture as flat as possible. All async IO is
accessed via a buffer. Back pressure is naturally exhibited via the buffer state.
This approach merges the best of FBP and a bare bones coroutine based async.


## Components

### Root Scheduler

The root scheduler is an instance of the Doist class in hio.base.doing.Doist

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
    .timer is MonoTimer for real time intervals

Inherited Properties:
    .tyme is float relative cycle time, .tyme is artificial time
    .tock is float tyme increment of .tick()

Properties:
    .tyme is float relative cycle time, .tyme is artificial time
    .tock is float tyme increment of .tick()

Inherited Methods:
    .tick increments .tyme by one .tock or provided tock

Methods:
    .ready prepare doer generators (dogs)
    .once  run through dogs one time
    .do repeadedly call .once until all dogs are complete or times out

### Async Coroutines

The async coroutines in hio are instances or subclasses of the Doer class in hio.base.doing.Doer

Doer base class for hierarchical structured async coroutine like generators.

Doer.__call__ on instance returns generator.
Doers provide generator function like object that a Doist or DoDoer can schedule directly.
Doer is generator creator and has extra methods and attributes that a plain
generator function does not.

Attributes:
    .done is Boolean completion state:
        True means completed
        Otherwise incomplete. Incompletion maybe due to close or abort.
    .opts is dict of injected options into its .do generator by scheduler

Inherited Properties:
    .tyme is float ._tymist.tyme, relative cycle or artificial time

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
    .exit is exit context method
    .close is close context method
    .abort is abort context method

Hidden:
   ._tymist is Tymist instance reference
   ._tock is hidden attribute for .tock property

A doer is executed in a life cycle that leverages the exiting python generator interface. The lifecycle methods are .enter, .recur, .exit, .close, and .abort. The lifecycle methods provides rich
context management.

#### DoDoer Subclass

One subclass of Doer is DoDoer in hio.base.doing.DoDoer

DoDoer implements Doist like functionality to allow nested scheduling of Doers.
Each DoDoer runs a list of doers like a Doist but using the tyme from its
   injected tymist

Inherited Attributes:
    .done is Boolean completion state:
        True means completed
        Otherwise incomplete. Incompletion maybe due to close or abort.
    .opts is dict of injected options for generator

Attributes:
    .doers is list of Doers or Doer like generator functions

Inherited Properties:
    .tyme is float ._tymist.tyme, relative cycle or artificial time
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
    .do
    .enter
    .recur
    .exit

Hidden:
   ._tymist is Tymist instance reference
   ._tock is hidden attribute for .tock property

#### Example Subclasses

The hio.base.doing module also includes example subclasses of Doer that show how to build different
Doers.

The ReDoer is an example sub class whose .recur is a generator method not a plain method.
Its .do method detects that its .recur is a generator method and executes it
   using yield from instead of just calling the method.

Inherited Attributes:
    .done is Boolean completion state:
        True means completed
        Otherwise incomplete. Incompletion maybe due to close or abort.
    .opts is dict of injected options for generator

Inherited Properties:
    .tyme is float ._tymist.tyme, relative cycle or artificial time
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

### Utility Functions

Doist and DoDoer schedule coroutine generators as either object instances that provide generator methods via .__call__ or generator functions. In order that these may be scheduled in the rich context the generator method or function must support a given interface with a couple of attributes.

Doer subclasses support the required interface. Generator methods can be wrapped or decorated to support the required interface. There are two utility functions that respectively wrap or decorate a generator function.

#### doify wrapper


```python
def doify(f, name=None, tock=0.0, **opts):
```

Parameters:

    f is generator function
    name is new function name for returned doified copy g. Default is to copy f.__name__
    tock is default tock attribute of doified copy g
    opts is dictionary of remaining parameters that becomes eventually inject .opts attribute of doified copy g


Returns Doist compatible copy, g, of converted generator function f. Each invoction of doify(f) returns a unique copy of doified function f. Imbues copy, g, of converted generator function, f, with attributes used by
Doist.ready() or DoDoer.enter(). Allows multiple instances of copy, g, of generator function, f, each with unique attributes.


Usage:

```python
def f():
   pass

c = doify(f, name='c')
```



#### Doize Decorator

```python
def doize(tock=0.0, **opts):
```

Parameters:

    tock is default tock attribute of doized f
    opts is dictionary of remaining parameters that becomes .opts attribute of doized f



Returns decorator that makes decorated generator function Doist compatible. Imbues decorated generator function with attributes used by Doist.ready() or DoDoer.enter().
Only one instance of decorated function with shared attributes is allowed.

Usage:
```python
@doize
def f():
    pass
```

## Scheduler Usage

```python

doers =[doing.Doer(), doing.Doer()]
doist = doing.Doist(tock=tock, real=True, limit=limit)
doist.do(doers=doers)

```

## Current Status

Version 0.1.3

Moved repo to Ioflo organization and repo as its a better home for hio i.e. same
place as ioflo which hio is a cousin of.



Version 0.1.2

The tcp support is well developed. Ported libraries for UDP and Serial also working
but need some minor attention

Asynchronous interface to logging module done.

Complete refactor of Doer and Doist classes. Now can have nested doers below the
root Doist.


As of version 0.0.6

This version provides basic usability for hierarchical structured async
concurrency in general plus support for async io with TCP.

The Doer base structured async class is implemented
The Cycler root scheduler class for Doers is implemeted

The TCP IO  Client and Server classes are implemented. Includes support for TLS

TCP ServerDoer, EchoServerDoer, and ClientDoer classes are implemented as examples

