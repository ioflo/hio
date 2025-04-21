# Hierarchical Action Framework

## Hierarchical State Machines

Hierarchical State Machines herein is a euphamism for a hierarchical action framework,
This is not a finite state machine in the mathematically defined sense. It is
a graph of states, or frames, or boxes or containers of actions or behaviors
 where some subset of the containers are active at any point in time
 and the actions or behaviors in the containers in that active set get executed.

For the sake of simplicity we call this a HAF for hierachical action framework.
The advantage of a HAF are several. The hierachy of behavioirs minimizes redundant
expression of behaviors. This significatntly reduces the apparent complexity of
a complex HAF. This reduced apparent complexity in turn makes it easier to
reason about the HAf and build more capable, and reliable HAFs.

This hierarchy driven reduction in apparent complexity exibits as follows:

1. Shared transitions in substates may be moved to super states. The number of
actual transitions implemented in code may theyby be reduced by an order of magnitude.

2. Share recuring behaviors in substates may be moved to super states. The number
of actual behaviors implemented in code may thereby be reduced by an order of magnitude.

3. Repeated entry and exit behaviors in substates may be moved to super states.
The number of actual behaviors implemented in code may thereby be reduced by an
order of magnitude.

4. Hierarchical containers of actions with an inverted priorty vis-a-vis OOP
where transitions at super states take priority over transitions in sub-states.
This priorty inversion enables reusable reliable service envelopes of behaviors
at higher layers to ensure safety and fault-tolerance in complex systems while
enabling use case  specific transition logic at the lower layers. This is a
critical enabling feature for any real-world automation system.

5. Use of a key-value store shared by all states with action/behavior access to
this key-value store directly. Interaction between behaviors is modulated through
the store, i.e. is indirect instead of direct. This indirect interaction enables a
flow-based programming paradigm with true replacement independence of all
behaviors while enabling observation and capture of all data flows vis-a-vis the
shared key-value store. This also removes upstream and downstream scalability
limits based on control flow dependencies. Indeed, this provides very loose
coupling and removes dependencies on interfaces. All dependencies are data items
in the shared key-value store.

6. Asynchronous IO and asynchronous execution at the HAF level enables ultra-fine
execution granularity, scalability, and distribution across execution
infrastructure such as coroutine, process, core, CPU, host or distributed hosts.

7. Predefined components as actions or behaviors that may be flexibly composed
to provide high expressive power. This is a critical enabler for dynamic and
adaptive workflow based programming.

These properties are mutually supporting. Together they provide a powerful foundation
for solving the hard problem of automation systems, that is, the coordination
problem. The coordination problem poses the following question; how best to
coordinate the various components of an automation system especially
a coordiantion system that is dynamically adaptive (in-stride) to both a
changing environment and changing goals and objectives for mission success?


## Relationship with Ioflo

Ioflo both inspired and informed Hio. Ioflow was originally developed with
Python 2.x (some of the early development started with Python 1.x). Hio started
with the latest Python 3.x.  As a result was able to leverage the latest generator
(coroutine) features of Python 3.x including delegation via the `yield from`
expression. Ioflo had to do a lot of things the hard way compared to Hio.

To avoid confusion with Ioflo, some of the naming conventions were changed in
Hio to avoid to close collisions with features in Ioflo. Hio's approach to a
hierachical action framework is enough different from Ioflo that it was easier
to reason about Hio without the confusion of too-close yet not close-enough
naming conventions.

Likewise Hio makes a much cleaner separation between the different types
of hierachical actioning in Ioflo.  The first type, in Ioflo are Tasks and
subclasses of Tasks that include Servers and Framers that are all executed
by a Skedder (scheduler). Tasks are generators.  The second type of of
hierarchical actioning in Ioflo are hierarchical frameworks of frames as
executed by Framer Tasks.  The third type arises when a main Framer executes other
Framers as auxiliaries.  In Ioflo the naming conventions for actioning contexts
within these three types have a lot of overlap, even though they operate in
different ways. Having let Ioflo sit for a while, it became apparent that in
adapting Ioflo for Hio that cleaner separation in action context naming would
reduce confusion.

## Hierarchical Boxwork

Hio has two types of hierarchical actioning. The first is for scheduling as
asynchronous coroutines. These consist of the Doist class and Doer subclasses.
The Doist schedules Doers. A special Doer subclass, the DoDoer enables, Doist
like scheduling of Doers by a DoDoer. This enables a hierarchy of asynchronous
schedulers. Doists andDoers have actioning contexts derived from the intrinsic
properties of Python generators used as a type of coroutine.
Doists operate in three contexts. These are: enter, recur, and exit.
Doers are operated in these same contexts but with three additional subcontexts
for exit. These exit subcontexts are: clean, cease, abort. These correspond to
the three ways a generator may complete operation.

The second type of hierarchical actioning in Hio is via a Boxwork which is
essentially a type of hierarchical state machine that is run by a Doer.
A Boxwork in Hio is analogous to a Framework in Ioflo. In Hio a Boxer runs a
boxwork. In Ioflo, a Framer runs a framework.

A boxwork consists of a graph of connected boxes. Each box belongs to a pile of
stacked boxes. A given pile constitues a hierarchical state. State changes by
transitioning from one pile to a different pile as determined by a transition
from one box to another box in the boxwork.
### Box Piles

Each box may have an over box and zero or more under boxes. A box at the top
of a pile has no over box. Its over is None or empty. A box at the bottom of
a pile has no under boxes. Its unders list is empty. The unders list is ordered.
The zeroth under box is the primary under.  With this organization it is
possible to trace the pile for any box by following the sequence of over boxes
until the top box is reached and also following the sequence of primary unders
until the box at the bottom is reached. This traced pile is the box's pile.
A given box may be a member of other box's piles but it has only one pile that
belongs to it.


### Action Nabes

Each action within each box is actioned (executed) within one of the box
contexts. Box actioning contexts in Hio are called Nabes (neighborhoods) to avoid
confustion generator (coroutine) based actioning contexts used by Doists and Doers
as well as the frame actioning contexts from Ioflo.

The Box Nabes are as follows:  predo, rendo, endo, redo, exdo, rexdo, afdo, godo.
In addition, there are to special sub-nabes for marking state. These are remark
for marking state relative to the rendo nabe and enmark for marking state
relative to the endo nabe.

To reiterate, each action in a box is executed in one of the following nabes:
predo, renmark, rendo, enmark, endo, redo, afdo, godo, exdo, rexdo.

The nabe names follow a mneumonic.

The prefix pre- in english means before in time or place.
For example, `enter`, or `engulf`. This gives rise to the nabe `endo` (en-do)
for actions to do upon entering a box.

The prefix en- in english means make entry into a place or state of being.
For example, `precede`, or `precaution`. This gives rise to the nabe `predo`
(pre-do) for actions to do before entering a box, i.e. preconditions of entry.

The prefix ex- in english means make to go outside of a place or state of being.
For example, `exit` or `expel`. This gives rise to the nabe `exdo` (en-do)
for actions to do upon exiting a box.

The prefix re- in english means to once more visit a previous state or place.
For example, `return`, `repeat`, and `reactivate`. This gives rise to the nabe
`redo`  (re-do) for actions to do (repeat) upon each recurrence of a box.

This also gives rise to the nabes `rendo` for re-endo and `rexdo` for re-exdo.

The prefix af- in english has several meanings. One is to change into.
For example, `affiliate`, `affirm`, or `affix`. This gives rise to the nabe
`afdo` (af-do) for actions to do that set up conditions for changing boxes.

The word go in english means to move or transition from one place to another.
This gives rise to the nabe `godo` (go-do) for actions to do that transition
to a new box.


### Acts

Each action run in each nabe in each box is a subclass of ActBase. Each box stores
its actions in lists by nabe. These lists are values of the following attributes:
preacts (predo nabe)
remarks (remark nabe)
renacts (rendo nabe)
enmarks (enmark nambe)
enacts (endo nabe)
reacts (redo nabe)
afacts (afdo nabe)
goacts (godo nabe)
exacts (exdo nabe)
rexacts (rexdo nabe)


### Nabe Action Ordering


#### First Run

The first time a boxwork is run is special. For any boxwork there is a first or
starting box. If not explicitly chosen, the default first box is the first box created.
The first boxes pile is the first pile. It defines the predos list of boxes
whose preconditionsk must be satisfied before entry. The first pile also defines
the endos list of boxes that must be entered to start the run.

All the actions in the preacts of each box in predos are evaluated in top down
order. The first one encountered that fails (returns False) terminates the
preact evaluation. This indicates that not all preconditions are satisfied so
the run stops and ends.  Only if all preacts return True do the run proceed.

Given all the preacts are satisfied, the execution resumes with the remarks and
renacts  and then the enmarks and enacts for each box in the endos list in top
down order.

Execution then resumes with the reacts for each box in the first pile (endos) in
top down order. This completes the first run.  The cycle tyme is incremented

#### Subsequent Runs

The next and all subsequent runs start with each box in the first boxes pile in
top down order.
The afacts (afdo) are evaluated first. Then each goact in a given box is evaluated.
If the goact transistion condition is satisfied then a transition is executed.
If not then each goact is evaluated in turn. As long as a transition condition
is not satisfied, the evaluation of afacts and then goacts proceeds until these
have been evaluated for all boxes in the pile in top down order.

When a transition condition is satisfied for a given godo, the lists of exdos,
rexdos, rendos and endos for the transition are calculated.
A given transistion has a near and a far box. The near is the current box that
determines the current pile of boxes. The far box is the destination or target
box of the  transition in the event that the transition condition is satisfied.
based on comparing the piles of the near and far boxes the exdo, rexdo, rendo,
and endo box lists for the transition can be calculated.

Given the endos list of boxes, the preacts of each box in endos are evaluated.
If all are satisfied the transition proceeds if not the transition fails and
the evalution of goacts resumes with the next one in the goacts list.
If no goacts with associated preacts for entry are ever satisfied then the run
pass ends without a transition and will resume on the next run cycle with an
incremeted tyme. The current active box pile is not changed.

Given the preacts are satisfied, the transition proceeds by first evaluating
all the exacts and then all the rexacts in turn in all the boxes in bottom up
order for the exdos list computed  for the given transition
(exits are reversed from entries).

After the the transistion the run pass is resumed for the new box pile of the
destination box.  First the renmarks and the the renacts for each box in the
new rendos are evaluated in top down order.
The run pass further proceeds  by evaluating the enmarks and the enacts for each
box in the new endos list in top down order.
The run pass then resumes by evaluating all the reacts in each box in the
pile in top down order. This completes the run pass.

The cycle tyme is then incremented and the next run pass begins as above with
the aftacts of the box pile boxes in top down order.

The run passes are reiterated until an end condition is met. When end it satisfied
then all the boxes in the active pile are exited by evaluating the exacts in
each bo in the pile in bottom up order. This terminates actioning of the boxwork.

#### Run code

The code for the boxer.run generator method is shown below.

```python

if not self.first:  # first box in boxes is default first
    self.first = list(self.boxes.values())[0]
self.box = self.first
rendos = []  # first pass no rendo (re-enter) of any boxes
endos = self.box.pile  # endo (enter) all boxes in pile potential entry

if not self.predo(endos):  # predo nabe, action preacts not satisfied
    # since no entry yet then no exdo
    self.box = None  # no active box anymore
    return False  # signal failure due to end in enter before first pass

akeys = ("", "boxer", self.name, "active")
if akeys not in self.mine:
    self.mine[akeys] = Bag()
self.mine[akeys].value = self.box.name  # assign active box name

# finished of enter next() delegation 'yield from' delegation
tyme = yield(tock)  # pause end of next, resume start of send

# begin first pass after send()
self.rendo(rendos)  # rendo nabe, action remarks and renacts
self.endo(endos)  # endo nabe, action enmarks and enacts

for box in self.box.pile:  # top down redo
    for react in box.reacts:   # redo nabe top down
        react()

while True:  # run forever
    tyme = yield(tock)  # resume on send
    rendos = []
    endos = []

    if self.endial():  # previous pass actioned desire to end
        self.end()  # exdos all active boxes in self.box.pile
        self.box = None  # no active box
        self.mine[akeys].value = None  # assign active box name to None
        return True  # signal successful end after last pass

    transit = False
    for box in self.box.pile:  # top down evaluate andos and godos
        for afact in box.afacts:   # afdo nabe top down, after tyme tick
            afact()

        for goact in box.goacts:  # godo nabe top down
            if dest := goact():  # transition condition satisfied
                exdos, endos, rendos, rexdos = self.exen(box, dest)
                if not self.predo(endos):  # godo not satisfied
                    continue  # keep trying
                self.exdo(exdos)  # exdo bottom up
                self.rexdo(rexdos)  # rexdo bottom up  (boxes retained)
                self.box = dest  # set new active box
                self.mine[akeys].value = self.box.name  # active box name
                transit = True
                break

        if transit:
            break

    self.rendo(rendos)  # rendo nabe, action remarks and renacts
    self.endo(endos)  # endo nabe, action enmarks and enacts

    for box in self.box.pile:  # top down
        for react in box.reacts:   # redo nabe top down
            react()

```

## Building a boxwork

The boxwork managed and run by a Boxer is made with a function called `fun`.
The make function uses a set of verbs to compose the piles of boxes with the
actions within each nabe in each box. Each verb is a special function with
associated parameters. The Boxer.make method injects the build context into
each of the verbs to minimize verbosity of boilerplate code. The goal is to
enable convenient composition of a boxwork.

These verbs are as follows:

bx() creates a new box and attaches it to its over box if any
go() defines a transition in nabe godo
do() defines an action in a box at a given nabe
on() defines a special condition action as a arg to a go or a do
at() sets the default nabe for the current box
be() defines a special assignment action at a given nabe

### Data Mine

Each boxwork has an in memory database called a data mine or mine for short.
The mine is a in-memory key-value store with special properties. Item values
in the mine may be instances of a Bag. A Bag is a special dataclass instance
with special properties. One of a Bag's special properties is that any update to
dataclass field in that bag is time stamped with the ._tyme attribute.  Python
dataclasses have two types of attributes, field attributes and normal attributes.
The ._tyme normal attribute is used to track the cycle tyme whenever on of its
field attributes is updated.

The actions in each box use the shared mine to communicate and manage data in
a flow based programming sense. The buffers between behaviors (actions) are
stored in the mine. Defining the box work also means defining the items in
the mine.

### Data Dock

In the future the boxwork will also support on on-disk durable key-value store
that may be used to manage durable data in a flow based programming sense.
The is called the data dock.  This is not exclusive as individual items in
the data mine could be special dataclasses that have a read/write through cache
to durable storage.







