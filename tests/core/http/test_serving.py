# -*- coding: utf-8 -*-
"""
Tests for http serving module
"""
import sys
import os
import time

import pytest

from hio import help
from hio.help import helping
from hio.base import tyming, doing
from hio.core import http


logger = help.ogler.getLogger()

tlsdirpath = os.path.dirname(
                os.path.dirname(
                        os.path.abspath(
                            sys.modules.get(__name__).__file__)))
certdirpath = os.path.join(tlsdirpath, 'tls', 'certs')

def test_bare_server_echo():
    """
    Test BaserServer service request response of echo non blocking
    """
    tymist = tyming.Tymist(tyme=0.0)

    with http.openServer(cls=http.BareServer, port = 6101, bufsize=131072, \
                         tymth=tymist.tymen()) as alpha:

        assert alpha.servant.ha == ('0.0.0.0', 6101)
        assert alpha.servant.eha == ('127.0.0.1', 6101)


        path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
        with http.openClient(bufsize=131072, path=path, tymth=tymist.tymen(), \
                             reconnectable=True,) as  beta:

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
                   not alpha.servant.ixes or not alpha.idle()):
                alpha.service()
                time.sleep(0.05)
                beta.service()
                time.sleep(0.05)

            assert beta.connector.accepted
            assert beta.connector.connected
            assert not beta.connector.cutoff

            assert len(alpha.servant.ixes) == 1
            assert len(alpha.stewards) == 1
            requestant = list(alpha.stewards.values())[0].requestant
            assert requestant.method == request['method']
            assert requestant.url == request['path']
            assert requestant.headers == help.Hict([('Host', 'localhost:6101'),
                                                         ('Accept-Encoding', 'identity'),
                                                         ('Accept', 'application/json'),
                                                         ('Content-Length', '0')])

            assert len(beta.responses) == 1
            response = beta.responses.popleft()
            assert response['data'] == {'version': 'HTTP/1.1',
                                        'method': 'GET',
                                        'path': '/echo',
                                        'qargs': {'name': 'fame'},
                                        'fragment': '',
                                        'headers': [['Host', 'localhost:6101'],
                                                    ['Accept-Encoding', 'identity'],
                                                    ['Accept', 'application/json'],
                                                    ['Content-Length', '0']],
                                        'body': '',
                                        'data': None}

            responder = list(alpha.stewards.values())[0].responder
            assert responder.status == response['status']
            assert responder.headers == response['headers']


def test_wsgi_server():
    """
    Test WSGI Server service request response
    """
    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    with http.openServer(port = 6101, bufsize=131072, app=wsgiApp, \
                         tymth=tymist.tymen()) as alpha:  # passthrough

        assert alpha.servant.ha == ('0.0.0.0', 6101)
        assert alpha.servant.eha == ('127.0.0.1', 6101)

        path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

        with http.openClient(bufsize=131072, path=path, reconnectable=True, \
                             tymth=tymist.tymen()) as beta:

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
            assert response['body'] == (b'Hello World!')
            assert response['status'] == 200

            responder = list(alpha.reps.values())[0]
            assert responder.status.startswith(str(response['status']))
            assert responder.headers == response['headers']


def test_wsgi_server_tls():
    """
    Test Valet WSGI service with secure TLS request response
    """
    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = certdirpath + '/client.pem' # remote client public cert

    with http.openServer(port = 6101, bufsize=131072, app=wsgiApp, \
                         scheme='https', keypath=serverKeypath, \
                         certpath=serverCertpath, cafilepath=clientCafilepath, \
                         tymth=tymist.tymen()) as alpha:

        assert alpha.servant.ha == ('0.0.0.0', 6101)
        assert alpha.servant.eha == ('127.0.0.1', 6101)

        #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
        #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
        #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

        clientKeypath = certdirpath + '/client_key.pem'  # local client private key
        clientCertpath = certdirpath + '/client_cert.pem'  # local client public cert
        serverCafilepath = certdirpath + '/server.pem' # remote server public cert

        path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

        with http.openClient(bufsize=131072, path=path, scheme='https', \
                    certedhost=serverCertCommonName, keypath=clientKeypath, \
                    certpath=clientCertpath, cafilepath=serverCafilepath, \
                    tymth=tymist.tymen(), reconnectable=True,) as beta:

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
            assert response['body'] == (b'Hello World!')
            assert response['status'] == 200

            responder = list(alpha.reps.values())[0]
            responder.status.startswith(str(response['status']))
            assert responder.headers == response['headers']


def test_server_client_doers():
    """
    Test HTTP ServerDoer ClientDoer classes
    """
    tock = 0.03125
    ticks = 16
    limit = ticks * tock
    doist = doing.Doist(tock=tock, real=True, limit=limit)
    assert doist.tyme == 0.0  # on next cycle
    assert doist.tock == tock == 0.03125
    assert doist.real == True
    assert doist.limit == limit == 0.5
    assert doist.doers == []

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                              ('Content-length', '12')])
        return [b"Hello World!"]

    port = 6101
    server = http.Server(port=port, app=wsgiApp, tymth=doist.tymen())
    assert server.servant.tyme == doist.tyme

    serdoer = http.ServerDoer(tymth=doist.tymen(), server=server)
    assert serdoer.server ==  server
    assert serdoer.tyme ==  serdoer.server.servant.tyme == doist.tyme

    path = "http://{0}:{1}/".format('localhost', port)
    client = http.Client(path=path, tymth=doist.tymen())
    assert client.connector.tyme == doist.tyme

    request = dict([('method', u'GET'),
                     ('path', u'/echo?name=fame'),
                     ('qargs', dict()),
                     ('fragment', u''),
                     ('headers', dict([('Accept', 'application/json'),
                                        ('Content-Length', 0)])),
                    ])

    client.requests.append(request)

    clidoer = http.ClientDoer(tymth=doist.tymen(), client=client)
    assert clidoer.client == client
    assert clidoer.tyme == clidoer.client.connector.tyme == doist.tyme

    assert serdoer.tock == 0.0  # ASAP
    assert clidoer.tock == 0.0  # ASAP

    doers = [serdoer, clidoer]

    doist.do(doers=doers, limit=limit)
    assert doist.tyme == limit
    assert server.servant.opened == False
    assert client.connector.opened == False

    assert len(client.responses) == 1
    response = client.responses.popleft()
    assert response['body'] == (b'Hello World!')
    assert response['status'] == 200
    """End Test """


if __name__ == '__main__':
    test_server_client_doers()
