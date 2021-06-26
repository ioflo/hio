# -*- encoding: utf-8 -*-
"""
hio.core.http Package
"""
from .httping import HTTPError
from .clienting import Client, openClient
from .serving import BareServer, Server, WsgiServer, openServer
