# -*- coding: utf-8 -*-
"""
test for http serving module with bottle
"""
import sys
import os
import time

import pytest

from hio import help
from hio.help import helping
from hio.base import tyming
from hio.core import wiring
from hio.core import http


logger = help.ogler.getLogger()

tlsdirpath = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(
                            sys.modules.get(__name__).__file__))))
certdirpath = os.path.join(tlsdirpath, 'tls', 'certs')


def test_server_with_bottle():
    """
    Test Server WSGI service request response with Bottle app
    """
    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data

    alpha = http.Server(port = 6101,
                          bufsize=131072,
                          app=app,
                          tymth=tymist.tymen(),)
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
    beta = http.Client(bufsize=131072,
                                 path=path,
                                 reconnectable=True,
                                 tymth=tymist.tymen(),
                                 )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)
    while (beta.requests or beta.connector.txbs or not beta.responses or
           not alpha.idle()):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                 ('Accept-Encoding', 'identity'),
                                                 ('Accept', 'application/json'),
                                                 ('Content-Length', '0')])

    assert len(beta.responses) == 1
    response = beta.responses.popleft()
    assert response['status'] == 200
    assert response['reason'] == 'OK'
    assert response['body'] == (b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                b' null}')

    assert response['data'] == {'action': None,
                                'content': None,
                                'form': {},
                                'query': {'name': 'fame'},
                                'url': 'http://localhost:6101/echo?name=fame',
                                'verb': 'GET'}

    responder = list(alpha.reps.values())[0]
    assert responder.status.startswith(str(response['status']))
    assert responder.headers == response['headers']

    alpha.servant.close()
    beta.connector.close()



def test_server_with_bottle_tls():
    """
    Test WSGI service secure TLS request response
    """
    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = certdirpath + '/client.pem' # remote client public cert

    alpha = http.Server(port = 6101,
                          bufsize=131072,
                          app=app,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,
                          tymth=tymist.tymen(),
                          )
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = http.Client(bufsize=131072,
                            path=path,
                            scheme='https',
                            certedhost=serverCertCommonName,
                            keypath=clientKeypath,
                            certpath=clientCertpath,
                            cafilepath=serverCafilepath,
                            tymth=tymist.tymen(),
                            reconnectable=True,
                            )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    beta.requests.append(request)
    while (beta.requests or beta.connector.txbs or not beta.responses or
           not alpha.idle()):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps), 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url, request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                         ('Accept-Encoding', 'identity'),
                                         ('Accept', 'application/json'),
                                         ('Content-Length', '0')])

    assert len(beta.responses) == 1
    response = beta.responses.popleft()
    assert response['status'] == 200
    assert response['reason'] == 'OK'
    assert response['body'] == (b'{"verb": "GET", '
                                b'"url": "https://localhost:6101/echo?name=fame", '
                                b'"action": null, '
                                b'"query": {"name": "fame"}, '
                                b'"form": {}, '
                                b'"content": null}')
    assert response['data'] == {'action': None,
                                'content': None,
                                'form': {},
                                'query': {'name': 'fame'},
                                'url': 'https://localhost:6101/echo?name=fame',
                                'verb': 'GET'}

    responder = list(alpha.reps.values())[0]
    assert responder.status.startswith(str(response['status']))
    assert responder.headers == response['headers']

    alpha.servant.close()
    beta.connector.close()


def test_request_with_no_content_length():
    """
    Test WSGI service request response no content-length in request
    """

    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data


    alpha = http.Server(port = 6101,
                        bufsize=131072,
                          app=app,
                          tymth=tymist.tymen(),)
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
    beta = http.Client(bufsize=131072,
                       path=path,
                                 reconnectable=True,
                                 tymth=tymist.tymen(),
                                 )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ])),
                    ])

    beta.requests.append(request)
    while (beta.requests or beta.connector.txbs or not beta.responses or
           not alpha.idle()):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                 ('Accept-Encoding', 'identity'),
                                                 ('Accept', 'application/json')])

    assert len(beta.responses) == 1
    response = beta.responses.popleft()
    assert response['status'] == 200
    assert response['reason'] == 'OK'
    assert response['body'] == (b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                b' null}')

    assert response['data'] == {'action': None,
                                'content': None,
                                'form': {},
                                'query': {'name': 'fame'},
                                'url': 'http://localhost:6101/echo?name=fame',
                                'verb': 'GET'}

    responder = list(alpha.reps.values())[0]
    assert responder.status.startswith(str(response['status']))
    assert responder.headers == response['headers']

    alpha.servant.close()
    beta.connector.close()


def test_connection_non_persistent():
    """
    Test WSGI service request response non persistent connection in request
    """
    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/echo')
    @app.get('/echo/<action>')
    @app.post('/echo')
    @app.post('/echo/<action>')
    def echoGet(action=None):
        """
        Echo back request data
        """
        query = dict(bottle.request.query.items())
        body = bottle.request.json
        raw = bottle.request.body.read()
        form = dict(bottle.request.forms)

        data = dict(verb=bottle.request.method,
                    url=bottle.request.url,
                    action=action,
                    query=query,
                    form=form,
                    content=body)
        return data

    alpha = http.Server(port = 6101,
                        bufsize=131072,
                          app=app,
                          tymth=tymist.tymen(),)
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
    beta = http.Client(bufsize=131072,
                       path=path,
                                 reconnectable=True,
                                 tymth=tymist.tymen(),
                                 )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Connection', 'close')])),
                    ])

    beta.requests.append(request)
    while (beta.requests or beta.connector.txbs or not beta.responses or
           not alpha.idle()):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                 ('Accept-Encoding', 'identity'),
                                                 ('Accept', 'application/json'),
                                                 ('Connection', 'close')])


    assert len(beta.responses) == 1
    response = beta.responses.popleft()
    assert response['status'] == 200
    assert response['reason'] == 'OK'
    assert response['body'] == (b'{"verb": "GET", "url": "http://localhost:6101/echo?name=fame", "'
                                b'action": null, "query": {"name": "fame"}, "form": {}, "content":'
                                b' null}')

    assert response['data'] == {'action': None,
                                'content': None,
                                'form': {},
                                'query': {'name': 'fame'},
                                'url': 'http://localhost:6101/echo?name=fame',
                                'verb': 'GET'}

    responder = list(alpha.reps.values())[0]
    assert responder.status.startswith(str(response['status']))
    assert responder.headers == response['headers']

    alpha.servant.close()
    beta.connector.close()



def test_sse_stream():
    """
    Test WSGI service request response stream sse
    """
    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/stream')
    def streamGet():
        """
        Create test server sent event stream that sends count events
        """
        tymer = tyming.Tymer(tymth=tymist.tymen(), duration=2.0)
        bottle.response.set_header('Content-Type',  'text/event-stream') #text
        bottle.response.set_header('Cache-Control',  'no-cache')
        # HTTP 1.1 servers detect text/event-stream and use Transfer-Encoding: chunked
        # Set client-side auto-reconnect timeout to 1000 ms.
        yield 'retry: 1000\n\n'
        i = 0
        yield 'id: {0}\n'.format(i)
        i += 1
        yield 'data: START\n\n'
        n = 1
        while not tymer.expired:
            yield 'id: {0}\n'.format(i)
            i += 1
            yield 'data: {0}\n\n'.format(n)
            n += 1
        yield "data: END\n\n"

    alpha = http.Server(port = 6101,
                        bufsize=131072,
                          app=app,
                          tymth=tymist.tymen(),)
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
    beta = http.Client(bufsize=131072,
                       path=path,
                                 reconnectable=True,
                                 tymth=tymist.tymen(),
                                 )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/stream'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                     ('body', None),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (not tymer.expired):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                 ('Accept-Encoding', 'identity'),
                                                 ('Accept', 'application/json'),
                                                 ('Content-Length', '0')])


    # timed out while body streaming still open so no completed responses
    # in .responses. But headers fully received
    assert beta.waited
    assert not beta.respondent.ended
    assert len(beta.responses) == 0
    assert 'Content-Type' in beta.respondent.headers
    assert beta.respondent.headers['Content-Type'] == 'text/event-stream'
    assert 'Transfer-Encoding'in beta.respondent.headers
    assert beta.respondent.headers['Transfer-Encoding'] == 'chunked'

    assert len(beta.events) == 4
    assert beta.respondent.retry == 1000
    assert int(beta.respondent.leid) >= 2
    event = beta.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = beta.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': '1'}
    event = beta.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': '2'}
    event = beta.events.popleft()
    assert event == {'id': '3', 'name': '', 'data': '3'}
    assert not beta.events

    #keep going until ended
    tymer.restart(duration=1.5)
    while (not tymer.expired):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert len(beta.events) == 7
    assert beta.respondent.leid ==  '9'
    assert beta.events[-2] == {'id': '9', 'name': '', 'data': '9'}
    assert beta.events[-1] == {'id': '9', 'name': '', 'data': 'END'}
    beta.events.clear()

    alpha.servant.close()
    beta.connector.close()


def test_sse_stream_tls():
    """
    Test WSGI service request response stream sse with tls
    """
    try:
        import bottle
    except ImportError as ex:
        logger.error("Bottle not available.\n")
        return

    tymist = tyming.Tymist(tyme=0.0)

    app = bottle.default_app() # create bottle app

    @app.get('/stream')
    def streamGet():
        """
        Create test server sent event stream that sends count events
        """
        tymer = tyming.Tymer(tymth=tymist.tymen(), duration=2.0)
        bottle.response.set_header('Content-Type',  'text/event-stream') #text
        bottle.response.set_header('Cache-Control',  'no-cache')
        # HTTP 1.1 servers detect text/event-stream and use Transfer-Encoding: chunked
        # Set client-side auto-reconnect timeout to 1000 ms.
        yield 'retry: 1000\n\n'
        i = 0
        yield 'id: {0}\n'.format(i)
        i += 1
        yield 'data: START\n\n'
        n = 1
        while not tymer.expired:
            yield 'id: {0}\n'.format(i)
            i += 1
            yield 'data: {0}\n\n'.format(n)
            n += 1
        yield "data: END\n\n"


    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = certdirpath + '/client.pem' # remote client public cert

    alpha = http.Server(port = 6101,
                          bufsize=131072,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,
                          tymth=tymist.tymen(),
                          app=app,
                          )
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = http.Client(bufsize=131072,
                        path=path,
                        scheme='https',
                        certedhost=serverCertCommonName,
                        keypath=clientKeypath,
                        certpath=clientCertpath,
                        cafilepath=serverCafilepath,
                        reconnectable=True,
                        tymth=tymist.tymen(),
                      )

    assert beta.connector.reopen()
    assert not beta.connector.accepted
    assert not beta.connector.connected
    assert not beta.connector.cutoff

    request = dict([('method', u'GET'),
                     ('path', u'/stream'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                     ('body', None),
                    ])

    beta.requests.append(request)
    tymer = tyming.Tymer(tymth=tymist.tymen(), duration=1.0)
    while (not tymer.expired):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                 ('Accept-Encoding', 'identity'),
                                                 ('Accept', 'application/json'),
                                                 ('Content-Length', '0')])


    # timed out while body streaming still open so no completed responses
    # in .responses. But headers fully received
    assert beta.waited
    assert not beta.respondent.ended
    assert len(beta.responses) == 0
    assert 'Content-Type' in beta.respondent.headers
    assert beta.respondent.headers['Content-Type'] == 'text/event-stream'
    assert 'Transfer-Encoding'in beta.respondent.headers
    assert beta.respondent.headers['Transfer-Encoding'] == 'chunked'
    assert len(beta.events) == 3
    assert beta.respondent.retry == 1000
    assert int(beta.respondent.leid) >= 2
    event = beta.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = beta.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': '1'}
    event = beta.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': '2'}
    assert not beta.events

    #keep going until ended
    tymer.restart(duration=1.5)
    while (not tymer.expired):
        alpha.service()
        time.sleep(0.05)
        beta.service()
        time.sleep(0.05)
        tymist.tick(tock=0.1)

    assert len(beta.events) == 8
    assert beta.respondent.leid ==  '9'
    assert beta.events[-2] == {'id': '9', 'name': '', 'data': '9'}
    assert beta.events[-1] == {'id': '9', 'name': '', 'data': 'END'}
    beta.events.clear()


    alpha.servant.close()
    beta.connector.close()


if __name__ == '__main__':
    test_sse_stream()
