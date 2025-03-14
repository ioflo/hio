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
from ..hioing import Mixin, HierError
from .. import help


"""Lode
make dict subclass with custom __setitem__ method that will only allow
str as key if tuple then converts tuple to separated string _

class dbdict(dict):

    __slots__ = ('db')  # no .__dict__ just for db reference

    def __init__(self, *pa, **kwa):
        super(dbdict, self).__init__(*pa, **kwa)
        self.db = None

    def __getitem__(self, k):
        try:
            return super(dbdict, self).__getitem__(k)
        except KeyError as ex:
            if not self.db:
                raise ex  # reraise KeyError
            if (ksr := self.db.states.get(keys=k)) is None:
                raise ex  # reraise KeyError
            try:
                kever = eventing.Kever(state=ksr, db=self.db)
            except kering.MissingEntryError:  # no kel event for keystate
                raise ex  # reraise KeyError
            self.__setitem__(k, kever)
            return kever

    def __contains__(self, k):
        if not super(dbdict, self).__contains__(k):
            try:
                self.__getitem__(k)
                return True
            except KeyError:
                return False
        else:
            return True

    def get(self, k, default=None):

        if not super(dbdict, self).__contains__(k):
            return default
        else:
            return self.__getitem__(k)


"""

class Builder(Mixin):
    """Builder Class boxworks of Boxer and Box instances.
    Holds reference to in-memory lode shared by all boxes in boxwork
    Holds reference to current Boxer and Boxe being built

    Attributes:
        lode (dict): in memory data lode shared by all boxes in boxwork
        boxer (Boxer | None): current boxer
        box (Box | None): cureent box

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance

    """
    def __init__(self, *, name='builder', lode=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work


        """
        super(Builder, self).__init__(**kwa)
        self.name = name
        self.lode = lode if lode is not None else {}
        self.boxer = None
        self.box = None

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name


class Boxer(Mixin):
    """Boxer Class that executes hierarchical action framework (boxwork) instances.
    Boxer instance holds reference to in-memory data lode shared by all its boxes
    and other Boxers in a given boxwork.
    Box instance holds a reference to its first (beginning) box.
    Box instance holds references to all its boxes in dict keyed by box name.

    Attributes:
        lode (dict): in memory data lode shared by all boxes in box work
        doer (Doer | None): doer running this boxer
        first (Box | None):  beginning box
        box (Box | None):  current box
        boxes (dict): all boxes mapping of (box name, box) pairs

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance


    Order of Execution of Boxer of its boxwork:


    """
    def __init__(self, *, name='boxer', lode=None, doer=None, first=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work
            doer (Doer | None): Doer running this Boxer
            first (Box | None):  beginning box


        """
        super(Boxer, self).__init__(**kwa)
        self.name = name
        self.lode = lode if lode is not None else {}
        self.doer = None
        self.first = first
        self.box = None  # current box
        self.boxes = {}

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name


class Box(Mixin):
    """Box Class for hierarchical action framework (boxwork) instances.
    Box instance holds reference to in-memory data lode shared by all the boxes in a
    given boxwork as well as its executing Boxer.
    Box instance holds references (links) to its over box and its under boxes.
    Box instance holds the acts to be executed in their context.



    Attributes:
        lode (dict): in memory data lode shared by all boxes in box work
        boxer (Boxer | None):  this box's Boxer instance
        over (Box | None): this box's over box instance or None
        unders (list[Box]): this box's under box instances or empty
        nxt (Box | None): this box's next box if any
        stak (list[Box]): this box's stak of boxes
        beacts (list[act]): benter (before enter) context acts
        renacts (list[act]): renter (re-enter) context acts
        reacts (list[act]): recur context acts
        preacts (list[act]): pretrans (pre-transit) context acts
        tracts (list[act]): transit context acts
        exacts (list[act]): exit context acts
        rexacts (list[act]): rexit (re-exit) context acts

    Properties:
        name (str): unique identifier of instance

    Hidden:
        _name (str): unique identifier of instance

    Order of Execution of Contexts:  (need time[k])
        beacts
        renacts
        enacts
        reacts
        while not done or segued:
            preacts
            if tract in tracts is True
               segue
            reacts
        exacts
        rexacts


    """
    def __init__(self, *, name='box', lode=None, boxer=None, **kwa):
        """Initialize instance.

        Parameters:
            name (str): unique identifier of box
            lode (dict | None): in memory data lode shared by all boxes in box work
            boxer (Boxer | None):  this box's Boxer instance


        """
        super(Box, self).__init__(**kwa)
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self.name = name
        self.lode = lode if lode is not None else {}
        self.boxer = boxer
        self.over = None  # over box
        self.unders = []  # list of under boxes, zeroth entry is primary
        self.nxt = None  # next box
        self.stak = []  # stak of boxes to which this box belongs
        # contexts
        self.beacts = []  # benter context list of before enter acts
        self.renacts = []  # renter context list of re-enter acts
        self.enacts = []  # enter context list of enter acts
        self.reacts = []  # recur context list of recurring acts
        self.preacts = []  # pretrans context list of pre-transit acts
        self.tracts = []  # transit context list of transition acts
        self.exacts = []  # exit context list of exit acts
        self.rexacts = []  # rexit context list of re-exit acts

    @property
    def name(self):
        """Property getter for ._name

        Returns:
            name (str): unique identifier of instance
        """
        return self._name


    @name.setter
    def name(self, name):
        """Property setter for ._name

        Paramaters:
            name (str): unique identifier of instance
        """
        if '_' in name:
            raise HierError(f"Invalid {name=} contains '_'.")
        self._name = name
