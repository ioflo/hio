"""WSGI application iterable ownership through the native HTTP server."""

from types import SimpleNamespace

import pytest

from hio.base import doing
from hio.core import http, tcp


class ResponseBody:
    def __init__(self, start_response, chunks, length=None, close_error=False):
        self.closes = 0
        self.finalized = False
        self.close_error = close_error
        self.generator = self.stream(start_response, chunks, length)

    def stream(self, start_response, chunks, length):
        headers = [('Content-Type', 'text/plain')]
        if length is not None:
            headers.append(('Content-Length', str(length)))
        start_response('200 OK', headers)
        try:
            yield from chunks
        finally:
            self.finalized = True

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.generator)

    def close(self):
        self.closes += 1
        self.generator.close()
        if self.close_error:
            raise RuntimeError('application cleanup failed')


@pytest.mark.parametrize('teardown', ['connection', 'server', 'doer'])
def test_wsgi_teardown_closes_suspended_body(teardown):
    bodies = []

    def application(environ, start_response):
        body = ResponseBody(start_response, iter(lambda: b'', None))
        bodies.append(body)
        return body

    doist = doing.Doist(tock=0.03125)
    with http.openServer(servant=tcp.Server(ha=('127.0.0.1', 0)),
                         app=application) as server:
        server.servant.eha = server.servant.ha
        with http.openClient(hostname='127.0.0.1',
                             port=server.servant.ha[1]) as client:
            client.request(method='GET', path='/')
            serverDoer = http.ServerDoer(server)
            doist.doers = [serverDoer, http.ClientDoer(client)]
            doist.deeds = doist.enter()
            try:
                for _ in range(200):
                    doist.recur()
                    if bodies:
                        break
                assert len(bodies) == 1
                body = bodies[0]
                responder = next(iter(server.reps.values()))
                assert responder.started and not responder.ended
                assert body.closes == 0 and not body.finalized
                if teardown == 'connection':
                    server.closeConnection(next(iter(server.reps)))
                elif teardown == 'server':
                    server.close()
                else:
                    doist.remove([serverDoer])
                assert body.closes == 1
                assert body.finalized
                responder.close()
                assert body.closes == 1
            finally:
                doist.exit()
                for body in bodies:
                    body.generator.close()


@pytest.mark.parametrize('completion', ['exhaustion', 'content-length', 'reset'])
def test_responder_completion_and_reset_close_once(completion):
    bodies = []
    sent = []

    def application(environ, start_response):
        chunks = [b'hello', b' world']
        length = 5 if completion == 'content-length' else None
        body = ResponseBody(start_response, chunks, length=length)
        bodies.append(body)
        return body

    responder = http.serving.Responder(SimpleNamespace(tx=sent.append),
                                        application, {})
    try:
        responder.service()
        body = bodies[0]
        if completion == 'exhaustion':
            responder.service()
            assert body.closes == 0
            responder.service()
            assert responder.ended
            assert b'hello' in b''.join(sent) and b' world' in b''.join(sent)
        elif completion == 'content-length':
            assert responder.ended and b''.join(sent).endswith(b'hello')
        else:
            responder.reset(environ={'PATH_INFO': '/next'})
            assert responder.iterator is None
        assert body.closes == 1 and body.finalized
        responder.reset(environ={})
        responder.close()
        assert body.closes == 1
    finally:
        for body in bodies:
            body.generator.close()


def test_wsgi_iterable_close_when_iter_returns_different_object():
    class IterableBody:
        def __init__(self):
            self.closes = 0

        def __iter__(self):
            return iter([b'hello'])

        def close(self):
            self.closes += 1

    body = IterableBody()

    def application(environ, start_response):
        start_response('200 OK', [('Content-Length', '5')])
        return body

    responder = http.serving.Responder(SimpleNamespace(tx=lambda msg: None),
                                        application, {})
    responder.service()
    assert responder.ended
    assert body.closes == 1
    responder.close()
    assert body.closes == 1


def test_cleanup_error_does_not_prevent_connection_teardown(monkeypatch):
    bodies = []
    errors = []
    monkeypatch.setattr(http.serving.logger, 'error',
                        lambda message, error: errors.append(str(error)))

    def application(environ, start_response):
        body = ResponseBody(start_response, [b''], close_error=True)
        bodies.append(body)
        return body

    responder = http.serving.Responder(SimpleNamespace(tx=lambda msg: None),
                                        application, {})
    responder.service()
    responder.close()
    assert responder.closed and responder.ended
    assert bodies[0].closes == 1 and bodies[0].finalized
    responder.close()
    assert bodies[0].closes == 1
    assert errors == ['application cleanup failed']


@pytest.mark.parametrize('error', [RuntimeError('response failed'), http.HTTPError(500)])
def test_failed_response_closes_body_without_terminating_chunked_response(error):
    class FailingBody:
        def __init__(self):
            self.closes = 0
            self.sent = False

        def __iter__(self):
            return self

        def __next__(self):
            if self.sent:
                raise error
            self.sent = True
            return b'partial'

        def close(self):
            self.closes += 1

    body = FailingBody()
    sent = []

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return body

    responder = http.serving.Responder(SimpleNamespace(tx=sent.append), application, {}, chunkable=True)
    responder.service()
    responder.service()
    assert responder.closed
    assert body.closes == 1
    responder.close()
    assert body.closes == 1
    assert not b''.join(sent).endswith(b'0\r\n\r\n')



@pytest.mark.parametrize('fail_at', [0, 1, 2])
def test_write_failure_closes_application_body(fail_at):
    body = ResponseBody(lambda status, headers: None, [b'partial'])
    sent = []

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return body

    def write(message):
        if len(sent) == fail_at:
            raise OSError('write failed')
        sent.append(message)

    responder = http.serving.Responder(SimpleNamespace(tx=write), application, {}, chunkable=True)
    with pytest.raises(OSError, match='write failed'):
        while not responder.ended:
            responder.service()
    assert responder.closed
    assert body.closes == 1 and body.finalized
    responder.close()
    assert body.closes == 1


def test_failure_creating_iterator_closes_application_body():
    class FailingBody:
        closes = 0

        def __iter__(self):
            raise RuntimeError('iterator creation failed')

        def close(self):
            self.closes += 1

    body = FailingBody()
    responder = http.serving.Responder(SimpleNamespace(tx=lambda msg: None),
                                        lambda environ, start_response: body, {})
    responder.service()
    assert responder.closed
    assert body.closes == 1


def test_wsgi_persistent_connection_releases_each_body():
    bodies = []

    def application(environ, start_response):
        body = ResponseBody(start_response, [b'hello'], length=5)
        bodies.append(body)
        return body

    doist = doing.Doist(tock=0.03125)
    with http.openServer(servant=tcp.Server(ha=('127.0.0.1', 0)),
                         app=application) as server:
        server.servant.eha = server.servant.ha
        with http.openClient(hostname='127.0.0.1',
                             port=server.servant.ha[1]) as client:
            doist.doers = [http.ServerDoer(server), http.ClientDoer(client)]
            doist.deeds = doist.enter()
            try:
                responder = None
                for request in range(2):
                    client.request(method='GET', path='/')
                    for _ in range(200):
                        doist.recur()
                        if client.responses:
                            break
                    response = client.respond()
                    assert response.status == 200
                    assert bytes(response.body) == b'hello'
                    current = next(iter(server.reps.values()))
                    if responder is not None:
                        assert current is responder
                    responder = current
                    assert len(bodies) == request + 1
                    assert all(body.closes == 1 and body.finalized for body in bodies)
                server.close()
                assert all(body.closes == 1 for body in bodies)
            finally:
                doist.exit()
                for body in bodies:
                    body.generator.close()
