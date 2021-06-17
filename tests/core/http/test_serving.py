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
from hio.core import wiring
from hio.core import http
from hio.core.http import serving

logger = help.ogler.getLogger()



def test_bare_server_echo():
    """
    Test Porter service request response of echo non blocking
    """
    tymist = tyming.Tymist(tyme=0.0)
    alpha = serving.Porter(port = 6101,
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
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
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



def testValetServiceBasic(self):
    """
    Test Valet WSGI service request response
    """
    console.terse("{0}\n".format(self.testValetServiceBasic.__doc__))

    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=wsgiApp)
    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))


    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    path = "http://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = http.Client(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

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
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['body'],bytearray(b'Hello World!'))
    self.assertEqual(response['status'], 200)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.close()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()


def testValetServiceBasicSecure(self):
    """
    Test Valet WSGI service with secure TLS request response
    """
    console.terse("{0}\n".format(self.testValetServiceBasicSecure.__doc__))

    tymist = tyming.Tymist(tyme=0.0)

    def wsgiApp(environ, start_response):
        start_response('200 OK', [('Content-type','text/plain'),
                                  ('Content-length', '12')])
        return [b"Hello World!"]

    console.terse("{0}\n".format("Building Valet ...\n"))
    wireLogAlpha = wiring.WireLog(buffify=True, same=True)
    result = wireLogAlpha.reopen()

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname
    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    serverKeypath = self.certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = self.certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = self.certdirpath + '/client.pem' # remote client public cert

    alpha = serving.Valet(port = 6101,
                          bufsize=131072,
                          wlog=wireLogAlpha,
                          tymth=tymist.tymen(),
                          app=wsgiApp,
                          scheme='https',
                          keypath=serverKeypath,
                          certpath=serverCertpath,
                          cafilepath=clientCafilepath,)

    self.assertIs(alpha.servant.reopen(), True)
    self.assertEqual(alpha.servant.ha, ('0.0.0.0', 6101))
    self.assertEqual(alpha.servant.eha, ('127.0.0.1', 6101))

    wireLogBeta = wiring.WireLog(buffify=True,  same=True)
    result = wireLogBeta.reopen()

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    clientKeypath = self.certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = self.certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = self.certdirpath + '/server.pem' # remote server public cert

    path = "https://{0}:{1}/".format('localhost', alpha.servant.eha[1])

    beta = http.Client(bufsize=131072,
                                 wlog=wireLogBeta,
                                 tymth=tymist.tymen(),
                                 path=path,
                                 reconnectable=True,
                                 scheme='https',
                                 certedhost=serverCertCommonName,
                                 keypath=clientKeypath,
                                 certpath=clientCertpath,
                                 cafilepath=serverCafilepath
                                 )

    self.assertIs(beta.connector.reopen(), True)
    self.assertIs(beta.connector.accepted, False)
    self.assertIs(beta.connector.connected, False)
    self.assertIs(beta.connector.cutoff, False)

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
        alpha.serviceAll()
        time.sleep(0.05)
        beta.serviceAll()
        time.sleep(0.05)

    self.assertIs(beta.connector.accepted, True)
    self.assertIs(beta.connector.connected, True)
    self.assertIs(beta.connector.cutoff, False)

    self.assertEqual(len(alpha.servant.ixes), 1)
    self.assertEqual(len(alpha.reqs), 1)
    self.assertEqual(len(alpha.reps), 1)
    requestant = alpha.reqs.values()[0]
    self.assertEqual(requestant.method, request['method'])
    self.assertEqual(requestant.url, request['path'])
    self.assertEqual(requestant.headers, {'accept': 'application/json',
                                            'accept-encoding': 'identity',
                                            'content-length': '0',
                                            'host': 'localhost:6101'})


    self.assertEqual(len(beta.responses), 1)
    response = beta.responses.popleft()
    self.assertEqual(response['body'],bytearray(b'Hello World!'))
    self.assertEqual(response['status'], 200)

    responder = alpha.reps.values()[0]
    self.assertTrue(responder.status.startswith, str(response['status']))
    self.assertEqual(responder.headers, response['headers'])

    alpha.servant.close()
    beta.connector.close()

    wireLogAlpha.close()
    wireLogBeta.close()




if __name__ == '__main__':
    test_bare_server_echo()
