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
from hio.base import tyming
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
    alpha = http.BareServer(port = 6101,
                          bufsize=131072,
                          tymth=tymist.tymen())
    assert alpha.servant.reopen()
    assert alpha.servant.ha == ('0.0.0.0', 6101)
    assert alpha.servant.eha == ('127.0.0.1', 6101)


    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])
    beta = http.Client(bufsize=131072,
                                 tymth=tymist.tymen(),
                                 path=path,
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
    assert requestant.headers == helping.imdict([('Host', 'localhost:6101'),
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

    alpha.servant.close()
    beta.connector.close()



def test_wsgi_server():
    """
    Test WSGI Server service request response
    """
    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    alpha = http.Server(port = 6101,
                          bufsize=131072,
                          app=wsgiApp,
                          tymth=tymist.tymen())  # jpassthrough
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

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == helping.imdict([('Host', 'localhost:6101'),
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

    alpha.servant.close()
    beta.connector.close()


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

    alpha = http.Server(port = 6101,
                          bufsize=131072,
                          app=wsgiApp,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,
                          tymth=tymist.tymen())

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

    assert beta.connector.accepted
    assert beta.connector.connected
    assert not beta.connector.cutoff

    assert len(alpha.servant.ixes) == 1
    assert len(alpha.reqs) == 1
    assert len(alpha.reps) == 1
    requestant = list(alpha.reqs.values())[0]
    assert requestant.method == request['method']
    assert requestant.url == request['path']
    assert requestant.headers == helping.imdict([('Host', 'localhost:6101'),
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

    alpha.servant.close()
    beta.connector.close()


if __name__ == '__main__':
    test_wsgi_server_tls()
