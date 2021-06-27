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
from falcon import testing

import pytest

from hio import help
from hio.help import helping
from hio.base import tyming
from hio.core import wiring
from hio.core import http
from hio.core.http import httping, clienting, serving

logger = help.ogler.getLogger()



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
            raw_json = req.bounded_stream.read()
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


class ExampleJsonMediaEnd:

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
            data = req.media
        except Exception:
            raise falcon.HTTPError(falcon.HTTP_748,
                                       'Read Error',
                                       'Could not read the request body.')


        result = dict(user=uid, data=data)

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

WEB_DIR_PATH = os.path.dirname(
                os.path.abspath(
                    sys.modules.get(__name__).__file__))
STATIC_DIR_PATH = os.path.join(WEB_DIR_PATH, 'static')
# /Users/Load/Data/Code/public/hio/tests/core/http/falcon

sink = serving.StaticSink(staticDirPath=STATIC_DIR_PATH)
exapp.add_sink(sink, prefix=sink.DefaultStaticSinkBasePath)

example = ExampleEnd()  # Resources are represented by long-lived class instances
exapp.add_route('/example', example) # example handles all requests to '/example' URL path

exampleJson = ExampleJsonEnd()
exapp.add_route('/example/{uid}', exampleJson)

exampleMediaJson = ExampleJsonMediaEnd()
exapp.add_route('/example/media/{uid}', exampleMediaJson)

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


def test_get_static_sink():
    """
    Test GET to static files
    """
    # must do it here to inject into Falcon endpoint resource instances
    tymist = tyming.Tymist(tyme=0.0)

    #myapp = falcon.App() # falcon.App instances are callable WSGI apps
    #ending.loadEnds(myapp, tymth=tymist.tymen())

    client = testing.TestClient(app=exapp)

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
    rep = client.simulate_get('/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == index

    # get default at /static  which is index.html
    rep = client.simulate_get('/static')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == index

    # get default at /static/  e.g. trailing / which is index.html
    rep = client.simulate_get('/static/')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == index

    # get index.html
    rep = client.simulate_get('/index.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == index

    # get /static/index.html
    rep = client.simulate_get('/static/index.html')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/html; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == index

    # attempt missing file
    rep = client.simulate_get('/static/missing.txt')
    assert rep.status == falcon.HTTP_NOT_FOUND
    assert rep.headers['content-type'] == 'application/json'
    assert rep.json['title'] == 'Missing Resource'

    # get robots.txt
    rep = client.simulate_get('/static/robots.txt')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'text/plain; charset=UTF-8'
    assert rep.text == '# robotstxt.org\n\nUser-agent: *\n'

    # get trial.js
    rep = client.simulate_get('/static/index.js')
    assert rep.status == falcon.HTTP_OK
    assert rep.headers['content-type'] == 'application/javascript; charset=UTF-8'
    assert len(rep.text) > 0
    assert rep.text == '// vanilla index.js\n\nm.render(document.body, "Hello world")\n'


def test_get_example():
    """
    PyTest fixtures are registered globally in the pytest package
    So any test function can accept a fixture as a parameter supplied by
    the pytest runner

    pytest_falcon assumes there is a fixture named "app"
    """
    client = testing.TestClient(app=exapp)

    rep = client.simulate_get('/example')
    assert rep.status == falcon.HTTP_OK
    assert rep.text == '\nHello World\n\n'


def test_get_uid_json():
    """
    """
    client = testing.TestClient(app=exapp)

    rep = client.simulate_get(path='/example/2')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'user': '2', 'msg': '\nHello World from 2\n\n'}

    headers = {"Content-Type": "application/json; charset=utf-8",
               }
    rep = client.simulate_post(path='/example/2',
                               body=json.dumps(dict(name="John Smith")),
                               headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(data=dict(name='John Smith'), user='2')


def test_get_uid__media_json():
    """
    """
    client = testing.TestClient(app=exapp)

    rep = client.simulate_get(path='/example/media/2')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'user': '2', 'msg': '\nHello World from 2\n\n'}

    headers = {"Content-Type": "application/json; charset=utf-8",
               }
    rep = client.simulate_post(path='/example/media/2',
                               json=dict(name="John Smith"),
                               headers=headers)
    assert rep.status == falcon.HTTP_OK
    assert rep.json == dict(data=dict(name='John Smith'), user='2')


def test_get_url_name():
    """
    """
    client = testing.TestClient(app=exapp)
    rep = client.simulate_get('/example/url/Peter')
    assert rep.status == falcon.HTTP_OK
    assert rep.text == '\nHello World Peter from path\n/example/url/Peter\n\n'



def test_get_async():
    """
    """
    client = testing.TestClient(app=exapp)
    rep = client.simulate_get('/example/async')
    assert rep.status == falcon.HTTP_OK
    assert rep.text == ('\n'
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


def test_get_pause():
    """
    """
    client = testing.TestClient(app=exapp)
    rep = client.simulate_get('/example/pause')
    assert rep.status == falcon.HTTP_OK
    assert rep.json == {'country': 'United States', 'name': 'John Smith'}


if __name__ == '__main__':
    test_get_pause()
