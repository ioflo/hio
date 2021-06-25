# -*- encoding: utf-8 -*-
"""
Demo web server for static files for client side web app
"""
import sys
import os
import mimetypes

import falcon

from ... import help

logger = help.ogler.getLogger()

# /Users/Load/Data/Code/public/hio/src/hio/demo/web/static
WebDirPath = os.path.dirname(
                os.path.abspath(
                    sys.modules.get(__name__).__file__))
StaticDirPath = os.path.join(WebDirPath, 'static')

class StaticSink():
    """
    Class that provided Falcon sink endpoint for serving static files in support
    of client side web app.

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
        self.staticDirpath = StaticDirPath

    def __call__(self, req, rep):
        path = req.path  # Falcon removes trailing "/" if any after non "/"
        splits = path.split("/")[1:]  # split and remove first split [""]
        if not splits[0]:  # empty split
            splits = splits[1:]  #remove empty
        if splits and splits[0] == "static":
            splits = splits[1:]  #remove static
        if not splits:  # return default
            filepath = "index.html"
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

        # for better stream handling provide "wsgi.file_wrapper" in wsgi environ
        # rep.stream = open(filepath, 'rb')
        # the following works faster and more consistently than rep.stream above
        # Maybe Falcon's default is to throttle the reads too much for rep.stream
        with open(filepath, 'rb') as f:
            rep.data = f.read()


