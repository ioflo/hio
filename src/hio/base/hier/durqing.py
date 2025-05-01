# -*- encoding: utf-8 -*-
"""hio.base.hier.durqing Module

Provides durable  queue for hold hierarchical actions

"""
from __future__ import annotations  # so type hints of classes get resolved later


class Durq():
    """Durq (durable queue) class when injected with
    .sdb and .key will store its ordered list durably and allow access as a FIFO
    queue

    """

