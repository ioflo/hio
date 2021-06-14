# -*- coding: utf-8 -*-
"""
Unittests for http clienting module
"""
import sys
import os
import time
from urllib.parse import urlsplit, quote_plus, unquote


import pytest

from hio import help
from hio.help import timing
from hio.base import tyming
from hio.core import wiring, tcp
from hio.core.http import clienting


logger = help.ogler.getLogger()

tlsdirpath = os.path.dirname(
                os.path.dirname(
                        os.path.abspath(
                            sys.modules.get(__name__).__file__)))
certdirpath = os.path.join(tlsdirpath, 'tls', 'certs')


def test_requester_respondent_echo():
    """
    Test basic nonblocking request response with
    client Requester class and client Respondent class
    use manual echo server
    """
    # Test tcp connection
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072,)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    # build http request
    host = '127.0.0.1'
    port = 6101
    method = 'GET'
    path = '/echo?name=fame'
    # GET /echo?name=fame from 127.0.0.1:6101
    headers = dict([('Accept', 'application/json')])
    request = clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)
    betaMsgOut = request.rebuild()
    assert request.lines == [b'GET /echo?name=fame HTTP/1.1',
                                b'Host: 127.0.0.1:6101',
                                b'Accept-Encoding: identity',
                                b'Accept: application/json',
                                b'',
                                b'']

    assert request.head == betaMsgOut  # only headers no body
    assert request.head == (b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: ide'
                            b'ntity\r\nAccept: application/json\r\n\r\n')
    assert betaMsgOut == (b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6101\r\nAccept-Encoding: ide'
                      b'ntity\r\nAccept: application/json\r\n\r\n')

    # Beta sends to Alpha
    beta.tx(betaMsgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    alphaMsgIn = bytes(ixBeta.rxbs)
    assert alphaMsgIn == betaMsgOut
    ixBeta.clearRxbs()

    # Alpha responds to Beta
    alphaMsgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
    ixBeta.tx(alphaMsgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    betaMsgIn = bytes(beta.rxbs)
    assert betaMsgIn == alphaMsgOut

    response = clienting.Respondent(msg=beta.rxbs, method=method)
    while response.parser:
        response.parse()
    assert not beta.rxbs  # fully extracted

    assert list(response.headers.items()) == [('Content-Length', '122'),
                                            ('Content-Type', 'application/json'),
                                            ('Date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                            ('Server', 'IoBook.local')]

    assert response.body ==  (b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url'
                                     b'": "http://127.0.0.1:8080/echo?name=fame", "action": null}')

    response.dictify()  # converts response.data to dict()

    assert response.data == {'action': None,
                                     'content': None,
                                     'query': {'name': 'fame'},
                                     'url': 'http://127.0.0.1:8080/echo?name=fame',
                                     'verb': 'GET'}

    alpha.close()
    beta.close()
    """End Test"""



def test_requester_respondent_echo_tls():
    """
    Test NonBlocking HTTPS (TLS/SSL) client
    """
    #'/Users/Load/Data/Code/public/hio/tests/core/tls/certs'
    assert certdirpath.endswith('/hio/tests/core/tls/certs')

    #serverKeypath = '/etc/pki/tls/certs/server_key.pem'  # local server private key
    #serverCertpath = '/etc/pki/tls/certs/server_cert.pem'  # local server public cert
    #clientCafilepath = '/etc/pki/tls/certs/client.pem' # remote client public cert

    #clientKeypath = '/etc/pki/tls/certs/client_key.pem'  # local client private key
    #clientCertpath = '/etc/pki/tls/certs/client_cert.pem'  # local client public cert
    #serverCafilepath = '/etc/pki/tls/certs/server.pem' # remote server public cert

    serverKeypath = certdirpath + '/server_key.pem'  # local server private key
    serverCertpath = certdirpath + '/server_cert.pem'  # local server public cert
    clientCafilepath = certdirpath + '/client.pem' # remote client public cert

    clientKeypath = certdirpath + '/client_key.pem'  # local client private key
    clientCertpath = certdirpath + '/client_cert.pem'  # local client public cert
    serverCafilepath = certdirpath + '/server.pem' # remote server public cert

    alpha = tcp.ServerTls(host='localhost',
                                  port = 6101,
                                  bufsize=131072,
                                  context=None,
                                  version=None,
                                  certify=None,
                                  keypath=serverKeypath,
                                  certpath=serverCertpath,
                                  cafilepath=clientCafilepath,
                                  )
    assert alpha.reopen()
    assert alpha.ha == ('127.0.0.1', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    serverCertCommonName = 'localhost' # match hostname uses servers's cert commonname

    beta = tcp.ClientTls(ha=alpha.ha,
                                  bufsize=131072,
                                  context=None,
                                  version=None,
                                  certify=None,
                                  hostify=None,
                                  certedhost=serverCertCommonName,
                                  keypath=clientKeypath,
                                  certpath=clientCertpath,
                                  cafilepath=serverCafilepath,
                                  )
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    #  connect and do tls handshake
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and len(alpha.ixes) >= 1:
            break
        time.sleep(0.01)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    #  build request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/echo?name=fame'
    headers = dict([('Accept', 'application/json')])
    request =  clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)
    betaMsgOut = request.rebuild()
    assert request.lines == [b'GET /echo?name=fame HTTP/1.1',
                            b'Host: 127.0.0.1:6061',
                            b'Accept-Encoding: identity',
                            b'Accept: application/json',
                            b'',
                            b'']

    assert request.head == betaMsgOut  # only headers no body
    assert request.head == (b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6061\r\n'
                            b'Accept-Encoding: identity\r\nAccept: application/json\r\n\r\n')
    assert betaMsgOut == (b'GET /echo?name=fame HTTP/1.1\r\nHost: 127.0.0.1:6061\r\n'
                          b'Accept-Encoding: identity\r\nAccept: application/json\r\n\r\n')

    # Beta sends to Alpha
    beta.tx(betaMsgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    alphaMsgIn = bytes(ixBeta.rxbs)
    assert alphaMsgIn == betaMsgOut
    ixBeta.clearRxbs()

    # Alpha responds to Beta
    alphaMsgOut = b'HTTP/1.1 200 OK\r\nContent-Length: 122\r\nContent-Type: application/json\r\nDate: Thu, 30 Apr 2015 19:37:17 GMT\r\nServer: IoBook.local\r\n\r\n{"content": null, "query": {"name": "fame"}, "verb": "GET", "url": "http://127.0.0.1:8080/echo?name=fame", "action": null}'
    ixBeta.tx(alphaMsgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    betaMsgIn = bytes(beta.rxbs)
    assert betaMsgIn == alphaMsgOut

    response = clienting.Respondent(msg=beta.rxbs, method=method)
    while response.parser:
        response.parse()
    assert not beta.rxbs  # fully extracted

    assert list(response.headers.items()) == [('Content-Length', '122'),
                                            ('Content-Type', 'application/json'),
                                            ('Date', 'Thu, 30 Apr 2015 19:37:17 GMT'),
                                            ('Server', 'IoBook.local')]

    assert response.body ==  (b'{"content": null, "query": {"name": "fame"}, "verb": "GET", "url'
                                     b'": "http://127.0.0.1:8080/echo?name=fame", "action": null}')

    response.dictify()  # converts response.data to dict()

    assert response.data == {'action': None,
                                     'content': None,
                                     'query': {'name': 'fame'},
                                     'url': 'http://127.0.0.1:8080/echo?name=fame',
                                     'verb': 'GET'}

    alpha.close()
    beta.close()


def test_requester_respondent_sse_stream():
    """
    Test NonBlocking Http client with SSE streaming server
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    #  build request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/stream'

    headers = dict([('Accept', 'application/json')])
    request = clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)
    msgOut = request.rebuild()
    assert request.lines == [b'GET /stream HTTP/1.1',
                            b'Host: 127.0.0.1:6061',
                            b'Accept-Encoding: identity',
                            b'Accept: application/json',
                            b'',
                            b'']

    assert msgOut == request.head  # header only
    assert request.head == b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nAccept: application/json\r\n\r\n'


    # send Beta request to Alpha
    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # build response header with event-stream content-type
    lines = [
                    b'HTTP/1.0 200 OK\r\n',
                    b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
                    b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
                    b'Content-Type: text/event-stream\r\n',
                    b'Cache-Control: no-cache\r\n',
                    b'Connection: close\r\n\r\n',
                ]

    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    # build response
    lines =  [
                b'retry: 1000\n\n',
                b'data: START\n\n',
                b'data: 1\n\n',
                b'data: 2\n\n',
                b'data: 3\n\n',
                b'data: 4\n\n',
             ]
    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    # create Respondent to handle streaming response from beta.rxbs
    response = clienting.Respondent(msg=beta.rxbs, method=method)
    # assert here

    timer = timing.Timer(duration=0.5)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()  # parse response
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs  # parser consumed it
    assert not response.body  # empty
    if response.parser:
        response.parser.close()
        response.parser = None

    response.dictify()  # make .data a dict from json if any
    assert response.data is None

    assert not response.eventSource.raw  # empty
    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert response.eventSource.leid is None
    assert response.leid == response.eventSource.leid
    assert len(response.events) == 5

    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '1'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '2'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '3'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '4'}
    assert not response.events

    alpha.close()
    beta.close()



def test_requester_respondent_sse_stream_chunked():
    """
    Test NonBlocking Http client with SSE streaming server with transfer encoding
    (chunked)
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    # build request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/stream'
    headers = dict([('Accept', 'application/json')])
    request = clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)
    msgOut = request.rebuild()
    assert request.lines == [b'GET /stream HTTP/1.1',
                            b'Host: 127.0.0.1:6061',
                            b'Accept-Encoding: identity',
                            b'Accept: application/json',
                            b'',
                            b'']

    assert request.head == b'GET /stream HTTP/1.1\r\nHost: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\nAccept: application/json\r\n\r\n'
    assert msgOut == request.head

    #  send Beta request to Alpha
    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs:
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # build response header Alpha to Beta with chunk header
    lines = [
                    b'HTTP/1.1 200 OK\r\n',
                    b'Content-Type: text/event-stream\r\n',
                    b'Cache-Control: no-cache\r\n',
                    b'Transfer-Encoding: chunked\r\n',
                    b'Date: Thu, 30 Apr 2015 20:11:35 GMT\r\n',
                    b'Server: IoBook.local\r\n\r\n',
                ]

    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    # build response body
    lines =  [
                b'd\r\nretry: 1000\n\n\r\n',
                b'd\r\ndata: START\n\n\r\n',
                b'9\r\ndata: 1\n\n\r\n',
                b'9\r\ndata: 2\n\n\r\n',
                b'9\r\ndata: 3\n\n\r\n',
                b'9\r\ndata: 4\n\n\r\n',
             ]
    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)

    #  create Respondent to process response
    response = clienting.Respondent(msg=beta.rxbs, method=method)

    timer = timing.Timer(duration=0.5)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs  #  empty
    assert not response.body  # empty
    assert not response.eventSource.raw  # empty

    if response.parser:
        response.parser.close()
        response.parser = None

    response.dictify()  # .data is None
    assert response.data is None


    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert response.eventSource.leid is None
    assert response.leid == response.eventSource.leid
    assert len(response.events) == 5
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '1'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '2'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '3'}
    event = response.events.popleft()
    assert event == {'id': None, 'name': '', 'data': '4'}
    assert not response.events

    alpha.close()
    beta.close()


def test_requester_respondent_sse_stream_fancy():
    """
    Test NonBlocking Http client to SSE server with non trivial path and
    multiline data in reponse events
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    #  build request with fancy path
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/fancy?idify=true&multiply=true'

    headers = dict([('Accept', 'application/json')])
    request =  clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)
    msgOut = request.rebuild()
    assert request.lines == [b'GET /fancy?idify=true&multiply=true HTTP/1.1',
                            b'Host: 127.0.0.1:6061',
                            b'Accept-Encoding: identity',
                            b'Accept: application/json',
                            b'',
                            b'']


    assert request.head == (b'GET /fancy?idify=true&multiply=true HTTP/1.1\r\n'
                            b'Host: 127.0.0.1:6061\r\nAccept-Encoding: identity\r\n'
                            b'Accept: application/json\r\n\r\n')
    assert msgOut == request.head

    # send request
    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # Build response
    lines = [
        b'HTTP/1.0 200 OK\r\n',
        b'Server: PasteWSGIServer/0.5 Python/2.7.9\r\n',
        b'Date: Thu, 30 Apr 2015 21:35:25 GMT\r\n'
        b'Content-Type: text/event-stream\r\n',
        b'Cache-Control: no-cache\r\n',
        b'Connection: close\r\n\r\n',
    ]

    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    # build sse response with multiline data in events
    lines =  [
        b'retry: 1000\n\n',
        b'id: 0\ndata: START\n\n',
        b'id: 1\ndata: 1\ndata: 2\n\n',
        b'id: 2\ndata: 3\ndata: 4\n\n',
        b'id: 3\ndata: 5\ndata: 6\n\n',
        b'id: 4\ndata: 7\ndata: 8\n\n',
    ]
    msgOut = b''.join(lines)

    response = clienting.Respondent(msg=beta.rxbs, method=method)

    ixBeta.tx(msgOut)
    timer = timing.Timer(duration=0.5)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs
    assert not response.body
    assert not response.eventSource.raw

    if response.parser:
        response.parser.close()
        response.parser = None

    response.dictify()
    assert response.data is None

    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert int(response.eventSource.leid) == 4
    assert response.leid == response.eventSource.leid
    assert len(response.events) == 5
    event = response.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': '1\n2'}
    event = response.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': '3\n4'}
    event = response.events.popleft()
    assert event == {'id': '3', 'name': '', 'data': '5\n6'}
    event = response.events.popleft()
    assert event == {'id': '4', 'name': '', 'data': '7\n8'}
    assert  not response.events

    alpha.close()
    beta.close()



def test_requester_respondent_sse_stream_fancy_chunked():
    """
    Test NonBlocking Http client to server Fancy SSE with chunked transfer encoding
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    # Build Request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = '/fancy?idify=true&multiply=true'
    headers = dict([('Accept', 'application/json')])
    request =  clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)

    msgOut = request.rebuild()
    assert  request.lines == [b'GET /fancy?idify=true&multiply=true HTTP/1.1',
                                b'Host: 127.0.0.1:6061',
                                b'Accept-Encoding: identity',
                                b'Accept: application/json',
                                b'',
                                b'']

    assert msgOut == request.head
    assert request.head == (b'GET /fancy?idify=true&multiply=true HTTP/1.1\r\n'
                            b'Host: 127.0.0.1:6061\r\nAccept-Encoding: '
                            b'identity\r\nAccept: application/json\r\n\r\n')

    # send request
    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # build response
    lines = [
        b'HTTP/1.1 200 OK\r\n',
        b'Content-Type: text/event-stream\r\n',
        b'Cache-Control: no-cache\r\n',
        b'Transfer-Encoding: chunked\r\n',
        b'Date: Thu, 30 Apr 2015 22:11:53 GMT\r\n',
        b'Server: IoBook.local\r\n\r\n',
    ]

    msgOut = b''.join(lines)

    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    lines =  [
        b'd\r\nretry: 1000\n\n\r\n',
        b'6\r\nid: 0\n\r\n',
        b'd\r\ndata: START\n\n\r\n',
        b'6\r\nid: 1\n\r\n',
        b'8\r\ndata: 1\n\r\n',
        b'8\r\ndata: 2\n\r\n',
        b'1\r\n\n\r\n',
        b'6\r\nid: 2\n\r\n',
        b'8\r\ndata: 3\n\r\n',
        b'8\r\ndata: 4\n\r\n',
        b'1\r\n\n\r\n',
        b'6\r\nid: 3\n\r\n',
        b'8\r\ndata: 5\n\r\n',
        b'8\r\ndata: 6\n\r\n',
        b'1\r\n\n\r\n',
        b'6\r\nid: 4\n\r\n8\r\ndata: 7\n\r\n8\r\ndata: 8\n\r\n',
        b'1\r\n\n\r\n',
    ]
    msgOut = b''.join(lines)
    response = clienting.Respondent(msg=beta.rxbs, method=method)
    ixBeta.tx(msgOut)
    timer = timing.Timer(duration=0.5)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs
    assert not response.body
    assert not response.eventSource.raw

    if response.parser:
        response.parser.close()
        response.parser = None

    response.dictify()
    assert response.data is None

    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert int(response.eventSource.leid) == 4
    assert response.leid == response.eventSource.leid
    assert len(response.events) == 5
    event = response.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': '1\n2'}
    event = response.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': '3\n4'}
    event = response.events.popleft()
    assert event == {'id': '3', 'name': '', 'data': '5\n6'}
    event = response.events.popleft()
    assert event == {'id': '4', 'name': '', 'data': '7\n8'}
    assert  not response.events

    alpha.close()
    beta.close()



def test_requester_respondent_sse_stream_fancy_json():
    """
    Test NonBlocking Http client to server Fancy SSE JSON with chunked transfer
    encoding
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    # Build Request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/fancy?idify=true&jsonify=true'
    headers = dict([('Accept', 'application/json')])
    request =  clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)

    msgOut = request.rebuild()
    assert  request.lines == [b'GET /fancy?idify=true&jsonify=true HTTP/1.1',
                                b'Host: 127.0.0.1:6061',
                                b'Accept-Encoding: identity',
                                b'Accept: application/json',
                                b'',
                                b'']

    assert msgOut == request.head
    assert request.head == (b'GET /fancy?idify=true&jsonify=true HTTP/1.1\r\n'
                            b'Host: 127.0.0.1:6061\r\nAccept-Encoding: '
                            b'identity\r\nAccept: application/json\r\n\r\n')

    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # Build Response
    lines = [
        b'HTTP/1.0 200 OK\r\n',
        b'Content-Type: text/event-stream\r\n',
        b'Cache-Control: no-cache\r\n',
        b'Date: Thu, 30 Apr 2015 22:11:53 GMT\r\n',
        b'Server: IoBook.local\r\n\r\n',
    ]

    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    lines =  [
        b'retry: 1000\n\n',
        b'id: 0\ndata: START\n\n',
        b'id: 1\ndata: {"count":1}\n\n',
        b'id: 2\n',
        b'data: {"count":2}\n\n',
        b'id: 3\ndata: {"count":3}\n\n',
        b'id: 4\ndata: {"count":4}\n\n',
    ]
    msgOut = b''.join(lines)
    response = clienting.Respondent(msg=beta.rxbs,
                                  method=method,
                                  dictable=True,  # convert event data to dict from json
                                  )
    ixBeta.tx(msgOut)
    timer = timing.Timer(duration=1.0)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs
    assert not response.body
    assert not response.eventSource.raw

    if response.parser:
        response.parser.close()
        response.parser = None

    assert response.data is None

    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert int(response.eventSource.leid) == 4
    assert response.leid == response.eventSource.leid
    # event data is dict not string since dictable
    assert len(response.events) == 5
    event = response.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': {'count': 1}}
    event = response.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': {'count': 2}}
    event = response.events.popleft()
    assert event == {'id': '3', 'name': '', 'data': {'count': 3}}
    event = response.events.popleft()
    assert event == {'id': '4', 'name': '', 'data': {'count': 4}}
    assert  not response.events

    alpha.close()
    beta.close()



def test_requester_respondent_sse_stream_fancy_json_chunked():
    """
    Test NonBlocking Http client to server Fancy SSE with chunked transfer encoding
    """
    alpha = tcp.Server(port = 6101, bufsize=131072)
    assert alpha.reopen()
    assert alpha.ha == ('0.0.0.0', 6101)
    assert alpha.eha == ('127.0.0.1', 6101)

    beta = tcp.Client(ha=alpha.eha, bufsize=131072)
    assert beta.reopen()
    assert not beta.accepted
    assert not beta.connected
    assert not beta.cutoff

    # connect beta to alpha
    while True:
        beta.serviceConnect()
        alpha.serviceConnects()
        if beta.connected and beta.ca in alpha.ixes:
            break
        time.sleep(0.05)

    assert beta.accepted
    assert beta.connected
    assert not beta.cutoff
    assert beta.ca == beta.cs.getsockname()
    assert beta.ha == beta.cs.getpeername()
    assert alpha.eha == beta.ha

    ixBeta = alpha.ixes[beta.ca]
    assert ixBeta.ca is not None
    assert ixBeta.cs is not None
    assert ixBeta.cs.getsockname() == beta.cs.getpeername()
    assert ixBeta.cs.getpeername() == beta.cs.getsockname()
    assert ixBeta.ca == beta.ca
    assert ixBeta.ha == beta.ha

    # Build Request
    host = u'127.0.0.1'
    port = 6061
    method = u'GET'
    path = u'/fancy?idify=true&jsonify=true'
    headers = dict([('Accept', 'application/json')])
    request =  clienting.Requester(hostname=host,
                                 port=port,
                                 method=method,
                                 path=path,
                                 headers=headers)

    msgOut = request.rebuild()
    assert  request.lines == [b'GET /fancy?idify=true&jsonify=true HTTP/1.1',
                                b'Host: 127.0.0.1:6061',
                                b'Accept-Encoding: identity',
                                b'Accept: application/json',
                                b'',
                                b'']

    assert msgOut == request.head
    assert request.head == (b'GET /fancy?idify=true&jsonify=true HTTP/1.1\r\n'
                            b'Host: 127.0.0.1:6061\r\nAccept-Encoding: '
                            b'identity\r\nAccept: application/json\r\n\r\n')

    beta.tx(msgOut)
    while beta.txbs and not ixBeta.rxbs :
        beta.serviceSends()
        time.sleep(0.05)
        alpha.serviceReceivesAllIx()
        time.sleep(0.05)
    msgIn = bytes(ixBeta.rxbs)
    assert msgIn == msgOut
    ixBeta.clearRxbs()

    # Build Response
    lines = [
        b'HTTP/1.0 200 OK\r\n',
        b'Content-Type: text/event-stream\r\n',
        b'Cache-Control: no-cache\r\n',
        b'Transfer-Encoding: chunked\r\n',
        b'Date: Thu, 30 Apr 2015 22:11:53 GMT\r\n',
        b'Server: IoBook.local\r\n\r\n',
    ]

    msgOut = b''.join(lines)
    ixBeta.tx(msgOut)
    while ixBeta.txbs or not beta.rxbs:
        alpha.serviceSendsAllIx()
        time.sleep(0.05)
        beta.serviceReceives()
        time.sleep(0.05)
    msgIn = bytes(beta.rxbs)
    assert msgIn == msgOut

    lines =  [
        b'd\r\nretry: 1000\n\n\r\n',
        b'6\r\nid: 0\n\r\n'
        b'd\r\ndata: START\n\n\r\n',
        b'6\r\nid: 1\n\r\n',
        b'12\r\ndata: {"count":1}\n\r\n',
        b'1\r\n\n\r\n',
        b'6\r\nid: 2\n\r\n12\r\ndata: {"count":2}\n\r\n1\r\n\n\r\n',
        b'6\r\nid: 3\n\r\n12\r\ndata: {"count":3}\n\r\n1\r\n\n\r\n',
        b'6\r\nid: 4\n\r\n12\r\ndata: {"count":4}\n\r\n1\r\n\n\r\n',
    ]
    msgOut = b''.join(lines)
    response = clienting.Respondent(msg=beta.rxbs,
                                  method=method,
                                  dictable=True,  # convert event data to dict from json
                                  )
    ixBeta.tx(msgOut)
    timer = timing.Timer(duration=1.0)
    while response.parser and not timer.expired:
        alpha.serviceSendsAllIx()
        response.parse()
        beta.serviceReceives()
        time.sleep(0.01)

    assert not beta.rxbs
    assert not response.body
    assert not response.eventSource.raw

    if response.parser:
        response.parser.close()
        response.parser = None

    assert response.data is None

    assert response.eventSource.retry == 1000
    assert response.retry == response.eventSource.retry
    assert int(response.eventSource.leid) == 4
    assert response.leid == response.eventSource.leid
    # event data is dict not string since dictable
    assert len(response.events) == 5
    event = response.events.popleft()
    assert event == {'id': '0', 'name': '', 'data': 'START'}
    event = response.events.popleft()
    assert event == {'id': '1', 'name': '', 'data': {'count': 1}}
    event = response.events.popleft()
    assert event == {'id': '2', 'name': '', 'data': {'count': 2}}
    event = response.events.popleft()
    assert event == {'id': '3', 'name': '', 'data': {'count': 3}}
    event = response.events.popleft()
    assert event == {'id': '4', 'name': '', 'data': {'count': 4}}
    assert  not response.events

    alpha.close()
    beta.close()




if __name__ == '__main__':
    test_requester_respondent_sse_stream_fancy_json_chunked()
