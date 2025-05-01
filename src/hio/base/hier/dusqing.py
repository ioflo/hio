# -*- encoding: utf-8 -*-
"""hio.base.hier.dusqing Module

Provides durable set queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later


class Dusq():
    """Dusq (durable set queue) class when injected with
    .sdb and .key will store its ordered set durably and allow access as a
    deduped FIFO queue. A set is deduped.


    """
