# -*- encoding: utf-8 -*-
"""
tests.base.hier.test_acting module

"""
from __future__ import annotations  # so type hints of classes get resolved later

import pytest

from hio.base.hier import acting
from hio.base.hier.acting import Actage, Actor, actify


def test_acting_basic():
    """Test Actor class and subclasses basically"""



    assert Actor.__name__ == 'Actor'
    assert Actor.Registry == {}
    assert Actor.Index == 0
    assert Actor.Attrs == {}

    actor = Actor()
    assert actor.name == 'Actor0'

    act = Actage(act=actor, kwa={})
    act.act(**act.kwa)


    """Done Test"""

if __name__ == "__main__":
    test_acting_basic()
