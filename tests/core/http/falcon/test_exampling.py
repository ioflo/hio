from __future__ import generator_stop

from collections import OrderedDict as ODict
import time

import pytest
from pytest import approx

import falcon
import pytest_falcon # declares client fixture

from ioflo.aid.timing import Stamper, StoreTimer
from ioflo.aio.http import Valet, Patron
from ioflo.aid import odict
from ioflo.base import Store

from bluepea.end.exampling import app as exapp
from bluepea.prime import priming

@pytest.fixture
def app():
    return exapp

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


def test_get_backend():
    """
    """
    print("Testing Falcon Example Backend Call")

    store = Store(stamp=0.0)  # create store
    priming.setupTest()

    valet = Valet(port=8101,
                  bufsize=131072,
                  store=store,
                  app=exapp,)

    result = valet.open()
    assert result
    assert valet.servant.ha == ('0.0.0.0', 8101)
    assert valet.servant.eha == ('127.0.0.1', 8101)

    path = "http://{}:{}{}".format('localhost',
                                   valet.servant.eha[1],
                                   "/example/backend")
    headers = odict([('Accept', 'application/json'),
                            ('Content-Length', 0)])
    patron = Patron(bufsize=131072,
                    store=store,
                    method='GET',
                    path=path,
                    headers=headers,
                    reconnectable=True,)

    assert patron.connector.reopen()
    assert patron.connector.accepted == False
    assert patron.connector.connected == False
    assert patron.connector.cutoff == False

    patron.transmit()
    timer = StoreTimer(store, duration=1.0)
    while (patron.requests or patron.connector.txes or not patron.responses or
               not valet.idle()):
        valet.serviceAll()
        time.sleep(0.05)
        patron.serviceAll()
        time.sleep(0.05)
        store.advanceStamp(0.1)

    assert patron.connector.accepted == True
    assert patron.connector.connected == True
    assert patron.connector.cutoff == False

    assert len(valet.servant.ixes) == 1
    assert len(valet.reqs) == 1
    assert len(valet.reps) == 1
    requestant = valet.reqs.values()[0]
    assert requestant.method == patron.requester.method
    assert requestant.url == patron.requester.path
    assert requestant.headers == {'accept': 'application/json',
                                              'accept-encoding': 'identity',
                                                'content-length': '0',
                                                'host': 'localhost:8101'}

    assert len(patron.responses) == 1
    rep = patron.responses.popleft()
    assert rep['status'] == 200
    assert rep['reason'] == 'OK'
    assert rep['body'] == bytearray(b'{\n  "approved": true,\n  "body": "\\nHello World\\n\\n"\n}')
    assert rep['data'] == odict([('approved', True), ('body', '\nHello World\n\n')])

    responder = valet.reps.values()[0]
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
    patron.request(method='GET',
                    path='/example/backend',
                    qargs=odict(path='/unknown'),
                    headers=headers)
    timer = StoreTimer(store, duration=1.0)
    while (patron.requests or patron.connector.txes or not patron.responses or
           not valet.idle()):
        valet.serviceAll()
        time.sleep(0.05)
        patron.serviceAll()
        time.sleep(0.05)
        store.advanceStamp(0.1)

    assert len(patron.responses) == 1
    rep = patron.responses.popleft()
    assert rep['status'] == 404
    assert rep['reason'] == 'Not Found'
    assert rep['body'] == bytearray(b'404 Not Found\nBackend Validation'
                                         b' Error\nError backend validation.'
                                         b' unknown\n')
    assert not rep['data']

    valet.close()
    patron.close()
    print("Done Test")


if __name__ == '__main__':
    from wsgiref import simple_server

    httpd = simple_server.make_server('127.0.0.1', 8080, exapp)
    httpd.serve_forever()  # navigate web client to http://127.0.0.1:8080/example
