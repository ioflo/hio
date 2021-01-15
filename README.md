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
concurrency approaches.

## Structured Concurrency with Asynchronous IO

More recently the [curio](https://curio.readthedocs.io/en/latest/) and
[trio](https://trio.readthedocs.io/en/stable/) libraries have popularized
coroutine based [structured concurrency](https://en.wikipedia.org/wiki/Structured_concurrency).

See here for why it matters ...
[here](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/)
and
[here](https://vorpus.org/blog/companion-post-for-my-pycon-2018-talk-on-async-concurrency-using-trio/)


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

