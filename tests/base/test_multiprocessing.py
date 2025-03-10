# -*- encoding: utf-8 -*-
"""
tests.core.test_doing module


Notes:
Always use set_start_method('spawn') since 'spawn' not default on linux but
default on macOS and Windows. Spawn is safer than fork.
set_start_method() should not be used more than once in the program.

Alternatively, you can use get_context() to obtain a context object.
Context objects have the same API as the multiprocessing module, and allow one
to use multiple start methods in the same program.

import multiprocessing as mp

def foo(q):
    q.put('hello')

if __name__ == '__main__':
    ctx = mp.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=foo, args=(q,))
    p.start()
    print(q.get())
    p.join()

MyNote: try putting all the stuff under if __name__=='__main__' into a function

def main():
    ctx = mp.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=foo, args=(q,))
    p.start()
    print(q.get())
    p.join()

if __name__=="__main__":
    main()

And then run in pytest to see if works



Note that objects related to one context may not be compatible with processes
for a different context. In particular, locks created using the fork context
cannot be passed to processes started using the spawn or forkserver start methods.

A library which wants to use a particular start method should probably use
get_context() to avoid interfering with the choice of the library user.

So to ensure better compatibility always use mp.get_context('spawn') instead
of set_start_method



API

Multiprocessing module methods

import multiprocessing as mp

mp.get_context(method=None)  Return a context object which has the same
    attributes as the multiprocessing module. If method is None then the default
    context is returned. Otherwise method should be 'fork', 'spawn', 'forkserver'.
    ValueError is raised if the specified start method is not available.

mp.active_children() Return list of all live children of the current process.
    Calling this has the side effect of “joining” any processes which have
    already finished. This prevents them from becoming zombies
    Usage:
        while True:
            time.sleep(1)
            if not mp.active_children():
                break

mp.cpu_count()    Return the number of CPUs in the system.
    This number is not equivalent to the number of CPUs the current process
    can use. The number of usable CPUs can be obtained with
    os.process_cpu_count() (or len(os.sched_getaffinity(0))).
    When the number of CPUs cannot be determined a NotImplementedError is raised.
    See also os.cpu_count() os.process_cpu_count()

mp.current_process()   Return the Process object corresponding to the current process.

mp.parent_process() Return the Process object corresponding to the parent
    process of the current_process(). For the main process, parent_process will be None.

mp.freeze_support()  Only on windows

mp.get_all_start_methods()  Returns a list of the supported start methods,
    the first of which is the default. The possible start methods are
    'fork', 'spawn' and 'forkserver'. Not all platforms support all methods.

mp.get_start_method(allow_none=False)  Return the name of start method used for
    starting processes.

mp.set_start_method(method, force=False)  Set the method which should be used
    to start child processes. The method argument can be 'fork', 'spawn' or 'forkserver'.
    Raises RuntimeError if the start method has already been set and force is not True.
    If method is None and force is True then the start method is set to None.
    If method is None and force is False then the context is set to the default context.
    Note that this should be called at most once, and it should be protected
    inside the if __name__ == '__main__' clause of the main module.

mp.set_executable(executable)  Set the path of the Python interpreter to use
    when starting a child process. (By default sys.executable is used).
    Embedders will probably need to do some thing like
    set_executable(os.path.join(sys.exec_prefix, 'pythonw.exe'))
    before they can create child processes.

mup.set_forkserver_preload(module_names)  Set a list of module names for the
    forkserver main process to attempt to import so that their already imported state
    is inherited by forked processes. Any ImportError when doing so is silently ignored.
    This can be used as a performance enhancement to avoid repeated work in every process.
    For this to work, it must be called before the forkserver process has been launched
    (before creating a Pool or starting a Process).
    Only meaningful when using the 'forkserver' start method.



Process class:

process references child process created in parent by invoking Process class

process = multiprocessing.Process(group=None,
                                  target=None,
                                  name=None,
                                  args=(),
                                  kwargs={},
                                  *, daemon=None)

process.start()  parent starts child that is process
process.run()  called by .start() in child process  once setup
process.join() blocks parent of process until process completes
process.terminate()  terminate child process using SIGTERM
                     Note that descendant processes of the process will not be
                     terminated – they will simply become orphaned.
                     so need to create
                     signal handler for SIGTERM since python only has built in
                    support to catch SIGINT == KeyboardInterrupt
                    exit clauses and finally will not be will not be executed
                    and child processes of the terminated process will be orphaned
                    so need to first have child terminate its children.
process.kill()  same as terminate but uses SIGKILL so need signal handler for SIGKILL
process.close()  close the process releasing all resources associated with it
                 raises ValueError if the process is still running so need to
                 end (terminate) process before closing.


process.name
process.is_alive()
process.daemon  daemon flag
process.pid  process ID
process.exitcode == 0 when exited normally,
                    1 when terminated by uncaught exception,
                    -N when terminated by signal number N

process.authkey  default is random string for parent and shared with its children
process.sentinel  os object that becomes ready when process ends



Examples:

from multiprocessing import Process
import os

def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)

if __name__ == '__main__':
    info('main line')
    p = Process(target=f, args=('bob',), kwargs={})
    p.start()
    p.join()

import multiprocessing as mp

def foo(q):
    q.put('hello')

if __name__ == '__main__':
    mp.set_start_method('spawn')
    q = mp.Queue()
    p = mp.Process(target=foo, args=(q,))
    p.start()
    print(q.get())
    p.join()

Python REPL examples

import multiprocessing, time, signal
mp_context = multiprocessing.get_context('spawn')
p = mp_context.Process(target=time.sleep, args=(1000,))
print(p, p.is_alive())
<...Process ... initial> False
p.start()
print(p, p.is_alive())
<...Process ... started> True
p.terminate()
time.sleep(0.1)
print(p, p.is_alive())
<...Process ... stopped exitcode=-SIGTERM> False
p.exitcode == -signal.SIGTERM
True


Signal handlers
https://docs.python.org/3/library/signal.html
A handler for a particular signal, once set, remains installed until it is explicitly reset
A Python signal handler does not get executed inside the low-level (C) signal handler.
Instead, the low-level signal handler sets a flag which tells the virtual machine
to execute the corresponding Python signal handler at a later point(for example
at the next bytecode instruction). This has consequences:

If the handler raises an exception, it will be raised “out of thin air”
in the main thread. See the note below for a discussion.

A caveat when setting a signal handler is that only one handler can be defined
for a given signal. Therefore, all handling must be done from a single callback function.

import signal
signal.SIGINT
signal.SIGTERM

Cannot register signal handler in python for SIGKILL cannot be caught
signal.SIGKILL

def handler(signum, frame):
    print('Signal handler called with signal', signum)
    interrupt_write.send(b'\0')
signal.signal(signal.SIGINT, handler)


https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully

import signal
import time

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_now = True

if __name__ == '__main__':
  killer = GracefulKiller()
  while not killer.kill_now:
    time.sleep(1)
    print("doing something in a loop ...")

  print("End of the program. I was killed gracefully :)")


Context Manager
import logging
import signal
import sys


class TerminateProtected:

    killed = False

    def _handler(self, signum, frame):
        logging.error("Received SIGINT or SIGTERM! Finishing this block, then exiting.")
        self.killed = True

    def __enter__(self):
        self.old_sigint = signal.signal(signal.SIGINT, self._handler)
        self.old_sigterm = signal.signal(signal.SIGTERM, self._handler)

    def __exit__(self, type, value, traceback):
        if self.killed:
            sys.exit(0)
        signal.signal(signal.SIGINT, self.old_sigint)
        signal.signal(signal.SIGTERM, self.old_sigterm)


if __name__ == '__main__':
    print("Try pressing ctrl+c while the sleep is running!")
    from time import sleep
    with TerminateProtected():
        sleep(10)
        print("Finished anyway!")
    print("This only prints if there was no sigint or sigterm")


https://avi.im/blag/2016/sigterm-in-python/

import signal
import sys
import time


def sigterm_handler(signal, frame):
    # save the state here or do whatever you want
    print('booyah! bye bye')
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)


def main():
    for i in range(100):
        print(i)
        time.sleep(i)


if __name__ == '__main__':
    main()

"""
import pytest

import os
import multiprocessing as mp
import time


def info(title):
    print(title)
    print('    module name:', __name__)
    print('    parent process:', os.getppid())
    print('    process id:', os.getpid())
    time.sleep(0.01)

def main_basic():
    """Basic multiprocessing example

    Consoler printout

    Parent: started.
    Parent Info:
        module name: __main__
        parent process: 78293
        process id: 17418
    Child Started child0 17420 True
    Child Started child1 17421 True
    Child Started child2 17424 True
    Child Started child3 17426 True
    Child child0 17420 True
    Child child1 17421 True
    Child child2 17424 True
    Child child3 17426 True
    Child child0 17420 True
    Child child1 17421 True
    Child child2 17424 True
    Child child3 17426 True
    Child child0 17420 True
    Child child1 17421 True
    Child child2 17424 True
    Child child3 17426 True
    Child child0 17420 True
    Child child1 17421 True
    Child child2 17424 True
    Child child3 17426 True
    Child3 Info:
        module name: __mp_main__
        parent process: 17418
        process id: 17426
    Child1 Info:
        module name: __mp_main__
        parent process: 17418
        process id: 17421
    Child0 Info:
        module name: __mp_main__
        parent process: 17418
        process id: 17420
    Child2 Info:
        module name: __mp_main__
        parent process: 17418
        process id: 17424
    Child child0 17420 False
    Child child1 17421 False
    Child child2 17424 False
    Child child3 17426 False
    Parent: children ended.
    Child Ended child0 17420 False
    0
    Child Ended child1 17421 False
    0
    Child Ended child2 17424 False
    0
    Child Ended child3 17426 False
    0
    """
    print("Parent: started.")
    info("Parent Info:")
    ctx = mp.get_context('spawn')
    n = 4
    pxes = []
    for i in range(4):
        name = f"child{i}"
        title = f"{name.capitalize()} Info:"
        p = ctx.Process(name=name, target=info, kwargs=dict(title=title))
        pxes.append(p)
        p.start()
        print("Child Started", p.name, p.pid, p.is_alive())


    while True:
        for p in pxes:
            print("Child", p.name, p.pid, p.is_alive())
        if not ctx.active_children():
            break
        time.sleep(0.05)

    print("Parent: children ended.")
    for p in pxes:
        print("Child Ended", p.name, p.pid, p.is_alive())
        print(p.exitcode)


def test_basic():
    """Basic tests of functionality of multiprocessing module

    """
    main_basic()
    """Done Test"""



if __name__ == "__main__":
    test_basic()
