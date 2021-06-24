from __future__ import generator_stop

import sys
import os
from collections import OrderedDict as ODict
import time
import mimetypes
import wsgiref

import pytest
from pytest import approx

import falcon
import pytest_falcon # declares client fixture

from ioflo.aid.timing import Stamper, StoreTimer
from ioflo.aio.http import Valet, Patron
from ioflo.aid import odict
from ioflo.base import Store

from ioflo.aid import getConsole

console = getConsole()

class StaticSink(object):
    """
    Class that provided Falcon sink endpoint for serving static files.

    # Geterating the full path of the static resource
    path = os.path.abspath(
        os.path.join(
            static_path,
            self.static_dir,
            environ['PATH_INFO'].lstrip('/')
        )
    )

    if not path.startswith(static_path) or not os.path.exists(path):
        return self.app(environ, start_response)
    else:
        filetype = mimetypes.guess_type(path, strict=True)[0]
        if not filetype:
            filetype = 'text/plain'
        start_response("200 OK", [('Content-type', filetype)])
        return environ['wsgi.file_wrapper'](open(path, 'rb'), 4096)

    # project directory
    PROJECT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

    # Web application specific static files
    STATIC_APP_PATH = os.path.join(PROJECT_DIR_PATH, 'app')

    """
    def __init__(self, *pa, **kwa):
        super().__init__(*pa, **kwa)
        self.staticDirpath = "/Data/Code/private/indigo/bluepea/src/bluepea/static/"

    def __call__(self, req, rep):
        path = req.path  # Falcon removes trailing "/" if any after non "/"
        splits = path.split("/")[1:]  # split and remove first split [""]
        if not splits[0]:  # empty split
            splits = splits[1:]  #remove empty
        if splits and splits[0] == "static":
            splits = splits[1:]  #remove static
        if not splits:  # return default
            filepath = "main.html"
        else:
            filepath = "/".join(splits)
        filepath = os.path.join(self.staticDirpath, filepath)
        if not os.path.exists(filepath):
            raise falcon.HTTPError(falcon.HTTP_NOT_FOUND,
                            'Missing Resource',
                            'File "{}" not found or forbidden'.format(filepath))
        filetype = mimetypes.guess_type(filepath, strict=True)[0]  # get first guess
        rep.set_header("Content-Type", "{}; charset=UTF-8".format(filetype))
        rep.status = falcon.HTTP_200  # This is the default status
        #rep.stream = open(filepath, 'rb')
        with open(filepath, 'rb') as f:
            rep.body = f.read()


def run_simpleserver():
    """
    Use wsgiref simpleserver server
    """
    from wsgiref import simple_server

    app = falcon.API() # falcon.API instances are callable WSGI apps
    sink = StaticSink()
    app.add_sink(sink, prefix="/")


    httpd = simple_server.make_server('127.0.0.1', 8080, app)
    httpd.serve_forever()  # navigate web client to http://127.0.0.1:8080/example

def run_valet():
    """
    Use ioflo valet server
    """
    console.reinit(verbosity=console.Wordage.profuse)

    store = Store(stamp=0.0)

    app = falcon.API() # falcon.API instances are callable WSGI apps
    sink = StaticSink()
    app.add_sink(sink, prefix="/")

    server = Valet(store=store,
                   app=app,
                   name='test',
                   port=8080,
                   timeout=0.5)
    server.open()


    while True:
        server.serviceAll()
        time.sleep(0.0625)
        store.advanceStamp(0.0625)



if __name__ == '__main__':
    #run_simpleserver()
    run_valet()
