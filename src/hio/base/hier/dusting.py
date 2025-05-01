# -*- encoding: utf-8 -*-
"""hio.base.hier.durqing Module

Provides durable double ended queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later


class Dust():
    """Dust (durable ordered set) class when injected with .sdb and .key will store
    its ordered set durably.


    """
