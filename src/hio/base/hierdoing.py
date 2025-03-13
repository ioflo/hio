# -*- encoding: utf-8 -*-
"""
hio.core.hierdoing Module

Provides hierarchical action support

"""
import os
import sys
import time
import logging
import json
import signal
import re
import multiprocessing as mp

from collections import deque, namedtuple
from dataclasses import dataclass, astuple, asdict, field
import typing


from . import tyming
from .doing import Doist, Doer
from .. import hioing
from ..hioing import Mixin
from .. import help


class Builder(Mixin):
    """Builder Class boxworks of Boxer and Box instances.
    Holds reference to in-memory lode shared by all boxes in boxwork
    Holds reference to current Boxer and Boxe being built

    Attributes:
        name (str): unique identifier of builder
        lode (dict): in memory data lode shared by all boxes in boxwork
        boxer (Boxer | None): current boxer
        box (Box | None): cureent box

    """
    def __init__(self, *, name='builder', lode=None, **kw):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work


        """
        super(Builder, self).__init__(**kw)
        self.name = name
        self.lode = lode if lode is not None else {}
        self.boxer = None
        self.box = None



class Boxer(Mixin):
    """Boxer Class that executes hierarchical action framework (boxwork) instances.
    Boxer instance holds reference to in-memory data lode shared by all its boxes
    and other Boxers in a given boxwork.
    Box instance holds a reference to its first (beginning) box.
    Box instance holds references to all its boxes in dict keyed by box name.

    Attributes:
        name (str): unique identifier of box
        lode (dict): in memory data lode shared by all boxes in box work
        first (Box | None):  beginning box
        boxes (dict): all boxes mapping of (box name, box) pairs


    Order of Execution of Boxer of its boxwork:


    """
    def __init__(self, *, name='boxer', lode=None, first=None, boxes=None, **kw):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work
            first (Box | None):  beginning box
            boxes (dict | None): all boxes mapping of (box name, box) pairs

        """
        super(Boxer, self).__init__(**kw)
        self.name = name
        self.lode = load if lode is not None else {}
        self.first = first
        self.boxes = boxes if boxes is not None else {}


class Box(Mixin):
    """Box Class for hierarchical action framework (boxwork) instances.
    Box instance holds reference to in-memory data lode shared by all the boxes in a
    given boxwork as well as its executing Boxer.
    Box instance holds references (links) to its over box and its under boxes.
    Box instance holds the acts to be executed in their context.



    Attributes:
        name (str): unique identifier of box
        lode (dict): in memory data lode shared by all boxes in box work
        boxer (Boxer | None):  this box's Boxer instance
        over (Box | None): this box's over box instance or None
        unders (list[Box]): this box's under box instances or empty
        nxt (Box | None): this box's next box if any
        beacts (list[act]): benter context acts
        enacts (list[act]): benter context acts
        beacts (list[act]): benter context acts
        beacts (list[act]): benter context acts



    Order of Execution of Contexts:
        beacts
        aux beacts
        renacts
        enacts
        aux renacts
        aux enacts
        reacts
        aux reacts
        while not done or segued:
            aux tracts
            aux if preact in aux preacts is True
                aux seque
            tracts
            if preact in preacts is True
               segue
            reacts
            aux reacts
        aux exacts
        aux rexacts
        exacts
        rexacts


    """
    def __init__(self, *, name='box', lode=None, boxer=None, **kw):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work
            boxer (Boxer | None):  this box's Boxer instance


        """
        super(Box, self).__init__(**kw)
        self.name = name
        self.lode = load if lode is not None else {}
        self.boxer = boxer
        self.over = None  # over box
        self.unders = []  # list of under boxes, zeroth entry is primary
        self.nxt = None  # next box

        self.beacts = []  # benter context list of before enter acts
        self.renacts = []  # renter context list of re-enter acts
        self.enacts = []  # enter context list of enter acts
        self.reacts = []  # recur context list of recurring acts
        self.tracts = []  # transit context list of pre-transition acts
        self.preacts = []  # precur context list transistion acts
        self.exacts = []  # exit context list of exit acts
        self.rexacts = []  # rexit context list of re-exit acts

        self.auxes = []  # auxiliary Boxers
