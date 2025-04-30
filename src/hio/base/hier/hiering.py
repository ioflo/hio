# -*- encoding: utf-8 -*-
"""
hio.base.hier.hiering Module

Provides hierarchical action support


Syntax notes for Mine and Dock use in boxwork:
    H hold (Hold) boxwork shared data attribute syntax with locally scoped
       variable H ref for hold .

    so need syntax does not heed to "quote" paths keys into the bags
    containers Mine dict subclasses with attribute support.

    H.root_dog.value  is equivalent to self.hold["root_dog"].value or
                                       self.hold[("root", "dog")].value

    So need term  "H.root_dog.value > 5" should compile directly and eval
    as long as H is in the locals() and H is a Mine instance.

    Likewise for
    D.root_dog.value where D is a Dock and root_dog is a key in the Dock.

    So no need to do substitutions or shorthand
    The hierarchy in the .mine/.dock is indicated by '_' separated keys
    The Box Boxer Actor names are forbidden from having '_" as an element
    with Renam regex test.



"""
from __future__ import annotations  # so type hints of classes get resolved later


from collections import deque, namedtuple
from collections.abc import Iterable, Mapping, Callable
from typing import Any, Type
from dataclasses import dataclass, astuple, asdict, field


from ..tyming import Tymee
from ... import hioing
from ...hioing import Mixin, HierError
from ...help import isNonStringIterable, MapDom, modify, Renam


"""Nabage (namedtuple):
Action nabes (contexts mileu neighborhood) for Acts

Fields:
   native (str): native nabe
   predo (str): predo nabe
   remark (str): remark sub-nabe of rendo
   rendo (str): rendo nabe
   enmark (str): enmark sub-nabe of endo
   endo (str): endo nabe
   redo (str): redo nabe
   afdo (str): afdo nabe
   godo (str): godo nabe
   exdo (str): exdo nabe
   rexdo (str): rexdo nabe
"""
Nabage = namedtuple("Nabage", "native predo remark rendo enmark endo"
                                      " redo afdo godo exdo rexdo")

Nabes = Nabage(native="native", predo="predo", remark="remark",
                     rendo="rendo", enmark="enmark", endo="endo",
                     redo="redo", afdo="afdo", godo="godo",
                     exdo="exdo", rexdo="rexdo")


@dataclass
class WorkDom(MapDom):
    """WorkDom provides state for building boxwork by a boxer to be injected
    make methods of Boxer by workify wrapper.


    Attributes:
        box (Box | None): current box in box work. None if not yet a box
        over (Box | None): current over Box in box work. None if top level
        bxpre (str):  default box name prefix used to generate unique box name
                    relative to boxer.boxes
        bxidx (int): default box name index used to generate unique box name
                    relative to boxer.boxes
        acts (dict):  registry of ActBase subclasses by name (including aliases)
        context (str): action context for act
    """
    box: None | Box = None  # current box in boxwork. None if not yet any box
    over: None | Box = None  # current over box in boxwork. None if not yet any over
    bxpre: str = 'box'  # default box name prefix when name not provided
    bxidx: int = 0  # default box name index when name not provided
    acts: dict = field(default_factory=dict)  # registry of Acts by name & aliases
    nabe: str = Nabes.native  # current action nabe (context)


