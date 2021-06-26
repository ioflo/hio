# -*- encoding: utf-8 -*-
"""
hio.core.http Package
"""
from .httping import HTTPError
from .clienting import Client, openClient, ClientDoer
from .serving import BareServer, Server, WsgiServer, openServer, ServerDoer
