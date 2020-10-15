# hio is a Hierarchically Structured Concurrency with Asynchronous IO Library in Python

## Rich Hierachical Structured Concurrency with Asynchronous IO

This builds on very early work on hierarchical structured concurrency with
lifecycle contexts from [ioflo](https://ioflo.com),
[ioflo github](https://github.com/ioflo/ioflo), and
[ioflo manuals](https://github.com/ioflo/ioflo_manuals).

## Structured Concurrency with Asynchronous IO

More recently the [curio](https://curio.readthedocs.io/en/latest/) and
[trio](https://trio.readthedocs.io/en/stable/) libraries have popularized
coroutine based [structured concurrency](https://en.wikipedia.org/wiki/Structured_concurrency).

See here for why it matters ...
[here](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/)
and
[here](https://vorpus.org/blog/companion-post-for-my-pycon-2018-talk-on-async-concurrency-using-trio/)


## Current Status

As of version 0.0.6

This version provides basic usability for hierarchical structured async
concurrency in general plus support for async io with TCP.

The Doer base structured async class is implemented
The Cycler root scheduler class for Doers is implemeted

The TCP IO  Client and Server classes are implemented. Includes support for TLS

TCP ServerDoer, EchoServerDoer, and ClientDoer classes are implemented as examples

