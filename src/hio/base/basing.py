# -*- encoding: utf-8 -*-
"""
hio.base.basing Module
"""
import enum


Ctl = enum.Enum('Control', 'enter recur exit abort')
Sts = enum.Enum('Status', 'entered recurring exited aborted')

