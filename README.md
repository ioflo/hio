Introduction to HIO
***********************

Weightless hierarchical asynchronous coroutines and I/O in Python.

Rich Flow Based Programming Hierarchical Structured Concurrency with Asynchronous IO

Hio builds on very early work on hierarchical structured concurrency with
lifecycle contexts from [ioflo](https://ioflo.com),
[ioflo github](https://github.com/ioflo/ioflo), and
[ioflo manuals](https://github.com/ioflo/ioflo_manuals).

This approach is compatible with flow based programming that sees all components
as asynchronous and linked by asynchronous buffers. FPB naturally lends itself
to a much lighter weight async structure based on a hierarchical scheduling approach.

This is even lighter weight and more performant than non-hierarchical structured
concurrency approaches such as trio or curio.

 approach also is informed by and supports cooperative concurrent
discrete event simulation (DES). One important feature of concurrent
discrete event simulation is reproducibility. This requires tight control over
scheduling order as in completely deterministic control of scheduling.
In order to have high fidelity reproduction or replay, all coroutines used in
a discrete event simulation must be scheduled exactly in the same relative order.
An asyncio event loop does not have such tight control over scheduling order. But
Hio does and therefore can be used for discrete event simulations with
high fidelity replay. One can always add noise and uncertainty to a Hio replay
as needed, but due to its underlying deterministic scheduling even the addition
of noise can be done in a predetermined reproducible way.


Structured Concurrency with Asynchronous IO
=============================================

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

The coroutines are responsible for managing the asynchronous IO not the scheduler.
This is compatible with a flow based programming (FBP) approach where Async IO only services
buffers. All interaction with other system components happens through those buffers
not some other mechanism. And certainly not a mechanism provided by the async
scheduler.  This makes the architecture as flat as possible. All async IO is
accessed via a buffer. Back pressure is naturally exhibited via the buffer state.
This approach merges the best of FBP and a bare-bones coroutine based async.

See API docs on readthedocs.org [Here](https://hio-py.readthedocs.io/en/latest/index.html)

Current Status
================

Version 0.4.1
  Refined Doist and DoDoer makes their protocol interfaces nearly identical as
    as is reasonably practical
  Added HTTP support with hio compatible HTTP Client and HTTP WSGI Server
  Example test code shows HTTP Server working with Falcon and Bottle ReST Micro
    frameworks


Version 0.3.4
  The async scheduler features should be pretty stable going forward.
  The tcp library should also be stable going forward.

  The TCP IO  Client and Server classes are implemented. Includes support for TLS

  TCP ServerDoer, EchoServerDoer, and ClientDoer classes are implemented as examples

