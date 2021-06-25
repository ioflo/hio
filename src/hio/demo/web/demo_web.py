# -*- encoding: utf-8 -*-
"""
Demo web server for static files for client side web app
"""
import os
import time
import mimetypes

import falcon

from hio import help
from hio.base import tyming
from hio.core import http
from hio.demo.web import demoing

logger = help.ogler.getLogger()



def run():
    """
    Use hio http server
    """
    tymist = tyming.Tymist(tyme=0.0)

    app = falcon.App()  # falcon.API instances are callable WSGI apps
    sink = demoing.StaticSink()
    app.add_sink(sink, prefix="/")

    try:
        server = http.Server(name='test',
                             port=8080,
                             tymeout=0.5,
                             app=app,
                             tymth=tymist.tymen())
        server.reopen()


        while True:
            try:
                server.service()
                time.sleep(0.0625)
                tymist.tick(tock=0.0625)

            except KeyboardInterrupt:  # use CNTL-C to shutdown from shell
                break

    finally:
        server.close()



if __name__ == '__main__':
    run()
