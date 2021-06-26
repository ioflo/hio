# -*- encoding: utf-8 -*-
"""
Test Falcon Module

Includes Falcon ReST endpoints for testing purposes

"""
import sys
import os
import mimetypes

import time
import json


from collections import OrderedDict as ODict
import time

import falcon
import pytest
import pytest_falcon # provides pytest falcon client fixture


from hio import help
from hio.help import helping
from hio.base import tyming
from hio.core import wiring
from hio.core import http
from hio.core.http import httping
from hio.core.http import clienting

logger = help.ogler.getLogger()


# /Users/Load/Data/Code/public/hio/src/hio/demo/web/static
WEB_DIR_PATH = os.path.dirname(
                os.path.abspath(
                    sys.modules.get(__name__).__file__))
STATIC_DIR_PATH = os.path.join(WEB_DIR_PATH, 'static')


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
    def __init__(self):
        self.staticDirpath = STATIC_DIR_PATH

    def __call__(self, req, rep):
        path = req.path  # Falcon removes trailing "/" if any after non "/"
        splits = path.split("/")[1:]  # split and remove first split [""]
        splits = [split for split in splits if split] # remove empty splits
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



# Falcon reource endpoints
class ExampleEnd:


    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nHello World\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.text = message


class ExampleJsonEnd:

    def on_get(self, req, rep, uid):
        """
        Handles GET requests
        """
        message = "\nHello World from {}\n\n".format(uid)
        result = dict(user=uid, msg=message)

        rep.status = falcon.HTTP_200  # This is the default status
        rep.text = json.dumps(result)


    def on_post(self, req, rep, uid):
        """
        Handles POST requests
        """
        try:
            raw_json = req.stream.read()
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_748,
                                       'Read Error',
                                       'Could not read the request body.')

        try:
            data = json.loads(raw_json)
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_753,
                                       'Malformed JSON',
                                       'Could not decode the request body. The '
                                       'JSON was incorrect.')


        result = dict(user=uid, data=data)

        #rep.status = falcon.HTTP_201
        #rep.location = '/example/%s' % (uid)  # location header redirect

        rep.status = falcon.HTTP_200  # This is the default status
        rep.text = json.dumps(result)


class ExampleUrlEnd:

    def on_get(self, req, rep, name):
        """
        Handles GET requests

        So falcon automatically url decodes path components
        """
        message = "\nHello World {} from path\n{}\n\n".format(name, req.path)
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.text = message

# generator
def textGenerator():
    """
    example generator
    """
    yield bytes()
    time.sleep(0.5)
    yield bytes("\n", "ascii")
    for i in range(10):
        yield bytes("Waiting {}\n".format(i), "ascii")
        time.sleep(0.1)

    yield bytes("\r\n", "ascii")

class ExampleAsyncEnd:

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nHello World\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.stream = textGenerator()
        #rep.body = message

# pause generator
def pauseJsonGenerator():
    """
    example generator that yields empty before yielding json and returning
    """
    for i in range(10):
        yield b''
        time.sleep(0.1)
    yield json.dumps(dict(name="John Smith",
                          country="United States")).encode("utf-8")


class ExamplePauseEnd:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "application/json"
        rep.stream = pauseJsonGenerator()


class ExampleBackendEnd:
    def  __init__(self, tymth):
        self.tymth = tymth

    @helping.attributize  # inject generator wrapper reference at me
    def backendGenerator(self, me, req=None, rep=None):
        """
        example backend request generator that yields empty before returning json
        """
        path = req.get_param("path")
        if not path:
            path = "/example"
        port = 8101
        # backendRequests yields b'' empty while waiting for request
        response = yield from clienting.backendRequest(tymth=self.tymth,
                                                    method='GET',
                                                    port=port,
                                                    path=path,
                                                    tymeout=0.5)

        if response is None:  # timed out waiting for authorization server
            raise httping.HTTPError(httping.SERVICE_UNAVAILABLE,
                             title ='Timeout Validation Error',
                             detail ='Timeout backend validation request.')

        if response['status'] != 200:
            if response['errored']:
                emsg = response['error']
            else:
                emsg = "unknown"
            raise httping.HTTPError(response['status'],
                             title="Backend Validation Error",
                             detail="Error backend validation. {}".format(emsg))

        yield b''  # yield empty keep alive
        # me._status = falcon.HTTP_200  # This is the default status
        me._status = httping.CREATED

        headers = help.Hict()
        headers["Content-Type"] = "application/json"
        headers["Location"] = "{}?stuff={}".format("/example/backend/stuff", "good")
        me._headers = headers

        result = dict(approved=True,
                       body=response['body'].decode())
        body = json.dumps(result, indent=2)

        return body.encode("utf-8")


    def on_get(self, req, rep):
        """
        Handles GET request that makes request to another backend endpoint

        """
        # status and headers are injected via ._status and ._headers of
        # backendGenerator
        # alternativly could just get response from backend generator and
        # examine here to assign to rep
        rep.stream = self.backendGenerator(req=req, rep=rep)

# must do it here to inject into Falcon endpoint resource instances
tymist = tyming.Tymist(tyme=0.0)

exapp = falcon.App() # falcon.App instances are callable WSGI apps


STATIC_BASE_PATH = "/static"
DEFAULT_STATIC_BASE_PATH = "/"

sink = StaticSink()
exapp.add_sink(sink, prefix=DEFAULT_STATIC_BASE_PATH)

example = ExampleEnd()  # Resources are represented by long-lived class instances
exapp.add_route('/example', example) # example handles all requests to '/example' URL path

exampleJson = ExampleJsonEnd()
exapp.add_route('/example/{uid}', exampleJson)

exampleUrl = ExampleUrlEnd()
exapp.add_route('/example/url/{name}', exampleUrl)

exampleAsync = ExampleAsyncEnd()
exapp.add_route('/example/async', exampleAsync)

examplePause = ExamplePauseEnd()
exapp.add_route('/example/pause', examplePause)

exampleBackend = ExampleBackendEnd(tymth=tymist.tymen())
exapp.add_route('/example/backend', exampleBackend)



def test_get_backend():
    """
    Test get backend request functionality (webhook)
    """
    tymist.tyme = 0.0  # reset for each test

    with http.openServer(port=8101, bufsize=131072, app=exapp, \
                         tymth=tymist.tymen()) as server:


        #server = http.Server(port=8101,
                      #bufsize=131072,
                      #store=store,
                      #app=exapp,)

        #assert server.reopen()
        assert server.servant.ha == ('0.0.0.0', 8101)
        assert server.servant.eha == ('127.0.0.1', 8101)

        # request to ExampleBackendEnd at /example/backend
        path = "http://{}:{}{}".format('localhost',
                                       server.servant.eha[1],
                                       "/example/backend")
        headers = help.Hict([('Accept', 'application/json'),
                                ('Content-Length', 0)])

        with http.openClient(bufsize=131072, method='GET', path=path, \
                        headers=headers, reconnectable=True, \
                        tymth=tymist.tymen()) as client:

            #client = http.Client(bufsize=131072,
                            #store=store,
                            #method='GET',
                            #path=path,
                            #headers=headers,
                            #reconnectable=True,)

            #assert client.reopen()
            assert client.connector.accepted == False
            assert client.connector.connected == False
            assert client.connector.cutoff == False

            client.transmit()
            while (client.requests or client.connector.txbs or not client.responses or
                       not server.idle()):
                server.service()
                time.sleep(0.05)
                client.service()
                time.sleep(0.05)
                tymist.tick(tock=0.1)

            assert client.connector.accepted == True
            assert client.connector.connected == True
            assert client.connector.cutoff == False

            assert len(server.servant.ixes) == 1
            assert len(server.reqs) == 1
            assert len(server.reps) == 1
            requestant = list(server.reqs.values())[0]
            assert requestant.method == client.requester.method
            assert requestant.url == client.requester.path
            assert requestant.headers == help.Hict([('Host', 'localhost:8101'),
                                               ('Accept-Encoding', 'identity'),
                                               ('Accept', 'application/json'),
                                               ('Content-Length', '0')])

            assert len(client.responses) == 1
            rep = client.responses.popleft()
            assert rep['status'] == 201
            assert rep['reason'] == 'Created'
            assert rep['headers']['Location'] == '/example/backend/stuff?stuff=good'
            assert rep['body'] == (b'{\n  "approved": true,\n  "body": "\\nHello World\\n\\n"\n}')
            assert rep['data'] == dict([('approved', True), ('body', '\nHello World\n\n')])

            responder = list(server.reps.values())[0]
            assert responder.status.startswith(str(rep['status']))
            assert responder.headers == rep['headers']



            # pipeline another request
            # test for error resulting from sending query arg path
            headers = help.Hict([('Accept', 'application/json'),
                                 ('Content-Length', 0)])
            client.request(method='GET',
                            path='/example/backend',
                            qargs=dict(path='/unknown'),
                            headers=headers)

            while (client.requests or client.connector.txbs or not client.responses or
                   not server.idle()):
                server.service()
                time.sleep(0.05)
                client.service()
                time.sleep(0.05)
                tymist.tick(tock=0.1)

            assert len(client.responses) == 1
            rep = client.responses.popleft()
            assert rep['status'] == 404
            assert rep['reason'] == 'Not Found'
            assert rep['body'] == bytearray(b'404 Not Found\nBackend Validation'
                                                 b' Error\nError backend validation.'
                                                 b' unknown\n')
            assert not rep['data']

    """Done Test """


@pytest.fixture
def app():  # pytest_falcon client fixture assumes there is a fixture named "app"
    return exapp


def test_get_StaticSink(client):  # client is a fixture in pytest_falcon
    """
    Test GET to static files
    """
    index = ('<html>\n'
                        '    <head>\n'
                        '        <title>Demo</title>\n'
                        '        <!--\n'
                        '        <link rel="stylesheet" type="text/css" '
                        'href="semantic/dist/semantic.min.css">\n'
                        '        <script src="node_modules/jquery/dist/jquery.min.js"></script>\n'
                        '        <script src="semantic/dist/semantic.min.js"></script>\n'
                        '        -->\n'
                        '    </head>\n'
                        '    <body>\n'
                        '        <!--\n'
                        '        <script src="bin/app.js"></script>\n'
                        '        <button class="ui button">Follow</button>\n'
                        '        -->\n'
                        '        <p>Hello World.</p>\n'
                        '    </body>\n'
                        '</html>\n')

    # get default at  /  which is index.html
    rep = client.get('/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == index

    # get default at /static  which is index.html
    rep = client.get('/static')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == index

    # get default at /static/  e.g. trailing / which is index.html
    rep = client.get('/static/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == index

    # get index.html
    rep = client.get('/index.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == index

    # get /static/index.html
    rep = client.get('/static/index.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == index

    # attempt missing file
    rep = client.get('/static/missing.txt')
    assert rep.status == falcon.HTTP_NOT_FOUND
    assert rep.headers['content-type'] == 'application/json'
    assert rep.json == {'title': 'Missing Resource',
                        'description': 'File '
                        '"/Users/Load/Data/Code/public/hio/tests/core/http/falcon/static/missing.txt" '
                        'not found or forbidden'}

    # get robots.txt
    rep = client.get('/static/robots.txt')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/plain; charset=UTF-8'
    assert rep.body == '# robotstxt.org\n\nUser-agent: *\n'

    # get trial.js
    rep = client.get('/static/index.js')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/javascript; charset=UTF-8'
    assert len(rep.body) > 0
    assert rep.body == '// vanilla index.js\n\nm.render(document.body, "Hello world")\n'


def test_get_example(client):  # client is a fixture in pytest_falcon
    """
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named "app"
    """
    rep = client.get('/example')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == '\nHello World\n\n'


def test_get_uid_json(client):  # client is a fixture in pytest_falcon
    """
    """
    rep = client.get('/example/2')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'user': '2', 'msg': '\nHello World from 2\n\n'}

    headers = {"Content-Type": "application/json; charset=utf-8",
               }
    rep = client.post('/example/2', dict(name="John Smith"), headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(data=dict(name='John Smith'), user='2')


def test_get_url_name(client):  # client is a fixture in pytest_falcon
    """
    """
    rep = client.get('/example/url/Peter')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == '\nHello World Peter from path\n/example/url/Peter\n\n'



def test_get_async(client):  # client is a fixture in pytest_falcon
    """
    """
    rep = client.get('/example/async')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == ('\n'
                        'Waiting 0\n'
                        'Waiting 1\n'
                        'Waiting 2\n'
                        'Waiting 3\n'
                        'Waiting 4\n'
                        'Waiting 5\n'
                        'Waiting 6\n'
                        'Waiting 7\n'
                        'Waiting 8\n'
                        'Waiting 9\n'
                        '\r\n')


def test_get_pause(client):  # client is a fixture in pytest_falcon
    """
    """
    rep = client.get('/example/pause')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'country': 'United States', 'name': 'John Smith'}


if __name__ == '__main__':
    test_get_backend()
