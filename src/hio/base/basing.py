# -*- encoding: utf-8 -*-
"""
hio.base.basing Module
"""
import enum


Ctl = enum.Enum('Control', 'enter recur exit abort')
Stt = enum.Enum('State', 'entered recurring exited aborted')

