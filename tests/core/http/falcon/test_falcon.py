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
from hio.base import tyming
from hio.core import wiring
from hio.core import http

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
    def __init__(self, *pa, **kwa):
        super().__init__(*pa, **kwa)
        self.staticDirpath = STATIC_DIR_PATH

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



class ExampleBackendEnd:
    def  __init__(self, store=None, **kwa):
        super(**kwa)
        self.store = store

    @helping.attributize  # support injecting skin reference
    def backendGenerator(self, skin, req=None, rep=None):
        """
        example generator that yields empty before returning json
        """
        path = req.get_param("path")
        if not path:
            path = "/example"
        port = 8101
        berep = yield from backendRequest(method='GET',
                                        port=port,
                                        path=path,
                                        store=self.store,
                                        timeout=0.5)

        if berep is None:  # timed out waiting for authorization server
            raise httping.HTTPError(httping.SERVICE_UNAVAILABLE,
                             title ='Timeout Validation Error',
                             detail ='Timeout backend validation request.')

        if berep['status'] != 200:
            if berep['errored']:
                emsg = berep['error']
            else:
                emsg = "unknown"
            raise httping.HTTPError(berep['status'],
                             title="Backend Validation Error",
                             detail="Error backend validation. {}".format(emsg))

        yield b''
        skin._status = falcon.HTTP_200  # This is the default status
        headers = dict()
        headers["Content-Type"] = "application/json"
        skin._headers = headers

        result = dict(approved=True,
                       body=berep['body'].decode())
        body = json.dumps(result, indent=2)
        bodyb = body.encode()

        return bodyb


    def on_get(self, req, rep):
        """
        Handles GET request that makes request to another backend endpoint

        """
        #path = req.get_param("path")
        #if not path:
            #path = "/example"
        #rep.status = falcon.HTTP_200  # This is the default status
        #rep.content_type = "application/json"
        rep.stream = self.backendGenerator(req=req, rep=rep)


# Falcon reource endpoints
class ExampleEnd:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nHello World\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.text = message


class ExampleJsonEnd:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep, userId):
        """
        Handles GET requests
        """
        message = "\nHello World from {}\n\n".format(userId)
        result = dict(user=userId, msg=message)

        rep.status = falcon.HTTP_200  # This is the default status
        rep.text = json.dumps(result)


    def on_post(self, req, rep, userId):
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
            data = json.loads(raw_json, 'utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_753,
                                       'Malformed JSON',
                                       'Could not decode the request body. The '
                                       'JSON was incorrect.')

        #console.terse("Received JSON Data: \n{}\n".format(data))

        result = dict(userId=userId, data=data)

        #rep.status = falcon.HTTP_201
        #rep.location = '/example/%s' % (userId)  # location header redirect

        rep.status = falcon.HTTP_200  # This is the default status
        rep.text = json.dumps(result)


class ExampleUrlEnd:
    def  __init__(self, **kwa):
        super(**kwa)

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
    def  __init__(self, **kwa):
        super(**kwa)

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
                          country="United States"), "ascii").encode("utf-8")


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


# auto json generator
def autoJsonGenerator():
    """
    example generator that yields empty bytes before returning data as dict
    so falcon auto json serializes it
    """
    for i in range(10):
        yield bytes()
        time.sleep(0.1)
    return dict(name="John Smith", country="United States")


class ExampleUtoEnd:
    def  __init__(self, **kwa):
        super(**kwa)

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "application/json"
        rep.stream = autoJsonGenerator()



exapp = falcon.App() # falcon.App instances are callable WSGI apps

sink = StaticSink()
app.add_sink(sink, prefix=STATIC_DIR_PATH)

example = ExampleEnd()  # Resources are represented by long-lived class instances
exapp.add_route('/example', example) # example handles all requests to '/example' URL path

exampleUser = ExampleJsonEnd()
exapp.add_route('/example/{userId}', exampleUser)

exampleAsync = ExampleAsyncEnd()
exapp.add_route('/example/async', exampleAsync)

examplePause = ExamplePauseEnd()
exapp.add_route('/example/pause', examplePause)

exampleDid = ExampleDidResource()
exapp.add_route('/example/did/{did}', exampleDid)

exampleBackend = ExampleBackendEnd()
exapp.add_route('/example/backend', exampleBackend)



def test_get_backend():
    """
    Test get backend request functionality (webhook)
    """


    server = http.Server(port=8101,
                  bufsize=131072,
                  store=store,
                  app=exapp,)

    result = server.reopen()
    assert result
    assert server.servant.ha == ('0.0.0.0', 8101)
    assert server.servant.eha == ('127.0.0.1', 8101)

    path = "http://{}:{}{}".format('localhost',
                                   server.servant.eha[1],
                                   "/example/backend")
    headers = help.Hict([('Accept', 'application/json'),
                            ('Content-Length', 0)])
    client = http.Client(bufsize=131072,
                    store=store,
                    method='GET',
                    path=path,
                    headers=headers,
                    reconnectable=True,)

    assert client.connector.reopen()
    assert client.connector.accepted == False
    assert client.connector.connected == False
    assert client.connector.cutoff == False

    client.transmit()
    timer = StoreTimer(store, duration=1.0)
    while (client.requests or client.connector.txes or not client.responses or
               not server.idle()):
        server.serviceAll()
        time.sleep(0.05)
        client.serviceAll()
        time.sleep(0.05)
        store.advanceStamp(0.1)

    assert client.connector.accepted == True
    assert client.connector.connected == True
    assert client.connector.cutoff == False

    assert len(server.servant.ixes) == 1
    assert len(server.reqs) == 1
    assert len(server.reps) == 1
    requestant = server.reqs.values()[0]
    assert requestant.method == client.requester.method
    assert requestant.url == client.requester.path
    assert requestant.headers == {'accept': 'application/json',
                                              'accept-encoding': 'identity',
                                                'content-length': '0',
                                                'host': 'localhost:8101'}

    assert len(client.responses) == 1
    rep = client.responses.popleft()
    assert rep['status'] == 200
    assert rep['reason'] == 'OK'
    assert rep['body'] == bytearray(b'{\n  "approved": true,\n  "body": "\\nHello World\\n\\n"\n}')
    assert rep['data'] == odict([('approved', True), ('body', '\nHello World\n\n')])

    responder = server.reps.values()[0]
    assert responder.status.startswith(str(rep['status']))
    assert responder.headers == rep['headers']

    # test for error by sending query arg path
    #request = odict([('method', 'GET'),
                     #('path', '/example/backend'),
                         #('qargs', odict(path='/unknown')),
                         #('fragment', u''),
                         #('headers', odict([('Accept', 'application/json'),
                                            #('Content-Length', 0)])),
                         #])

    #patron.requests.append(request)

    headers = odict([('Accept', 'application/json'),
                    ('Content-Length', 0)])
    client.request(method='GET',
                    path='/example/backend',
                    qargs=odict(path='/unknown'),
                    headers=headers)
    timer = StoreTimer(store, duration=1.0)
    while (client.requests or client.connector.txes or not client.responses or
           not server.idle()):
        server.serviceAll()
        time.sleep(0.05)
        client.serviceAll()
        time.sleep(0.05)
        store.advanceStamp(0.1)

    assert len(client.responses) == 1
    rep = client.responses.popleft()
    assert rep['status'] == 404
    assert rep['reason'] == 'Not Found'
    assert rep['body'] == bytearray(b'404 Not Found\nBackend Validation'
                                         b' Error\nError backend validation.'
                                         b' unknown\n')
    assert not rep['data']

    server.close()
    client.close()
    print("Done Test")





@pytest.fixture
def app():  # pytest_falcon client fixture assumes there is a fixture named "app"
    return exapp


def test_get_StaticSink(client):  # client is a fixture in pytest_falcon
    """
    Test GET to static files
    """
    print("Testing GET /static")

    # get default /static
    rep = client.get('/static')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0

    # get default /
    rep = client.get('/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0

    # get default trailing /
    rep = client.get('/static/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0

    # get main.html
    rep = client.get('/static/main.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0

    # get main.html
    rep = client.get('/main.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.body) > 0

    # attempt missing file
    rep = client.get('/static/missing.txt')
    assert rep.status == falcon.HTTP_NOT_FOUND
    assert rep.headers['content-type'] == 'application/json; charset=UTF-8'
    assert rep.json == {
        'description': 'File '
        '"/Data/Code/private/indigo/bluepea/src/bluepea/static/missing.txt" '
        'not found or forbidden',
        'title': 'Missing Resource'}

    # get robots.txt
    rep = client.get('/static/robots.txt')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/plain; charset=UTF-8'
    assert rep.body == '# robotstxt.org\n\nUser-agent: *\n'

    # get trial.js
    rep = client.get('/static/trial.js')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/javascript; charset=UTF-8'
    assert len(rep.body) > 0


def test_get_example(client):  # client is a fixture in pytest_falcon
    """
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named "app"
    """
    print("Testing Falcon Example Call")
    rep = client.get('/example')
    assert rep.status == falcon.HTTP_OK
    assert rep.body == '\nHello World\n\n'
    print("Done Test")

def test_get_user(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example User Call")
    rep = client.get('/example/2')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(msg='\nHello World from 2\n\n', user='2')

    headers = {"Content-Type": "application/json; charset=utf-8",
               }
    rep = client.post('/example/2', dict(name="John Smith"), headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(data=dict(name='John Smith'), userId='2')
    print("Done Test")

def test_get_async(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example Async Call")
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

    print("Done Test")

def test_get_pause(client):  # client is a fixture in pytest_falcon
    """
    """
    print("Testing Falcon Example Pause Call")
    rep = client.get('/example/pause')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'country': 'United States', 'name': 'John Smith'}

    print("Done Test")


if __name__ == '__main__':
    from wsgiref import simple_server

    httpd = simple_server.make_server('127.0.0.1', 8080, exapp)
    httpd.serve_forever()  # navigate web client to http://127.0.0.1:8080/example
