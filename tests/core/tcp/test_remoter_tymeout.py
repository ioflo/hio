# -*- encoding: utf-8 -*-
"""
tests.core.tcp.test_remoter_tymeout

Server and ServerTls built each accepted Remoter with ``timeout=self.tymeout``
but Remoter's parameter is ``tymeout``. The keyword fell into **kwa and was
dropped, so every accepted connection got Remoter.Tymeout (0.0) and never
timed out, whatever tymeout the server was given. In particular http.Server's
idle-connection tymeout (5 s by default) never applied, so a client could hold
a connection open indefinitely by never finishing its request headers.

The remaining tests cover what turning that tymeout on exposed: the tymeout
must measure idle tyme from the latest byte, must not cut a response in
progress, must not crash a server serviced without a Tymist, and must also
reach TLS connections that never finish their handshake.

Ports 6431-6466 are used only here.
"""
import os
import socket
import struct
import time

import pytest

from hio.base import tyming
from hio.core import tcp, http


def _accept(server, port):
    sock = socket.create_connection(("127.0.0.1", port))
    for _ in range(50):
        server.serviceConnects()
        if server.ixes:
            break
        time.sleep(0.02)
    assert server.ixes
    return sock, next(iter(server.ixes.values()))


def _serviceUntil(server, predicate, tries=100):
    """Service server in real time until predicate() or give up."""
    for _ in range(tries):
        server.service()
        if predicate():
            return True
        time.sleep(0.01)
    return False


def _recvAll(sock, server, until, tries=100):
    """Service server and collect bytes from sock until `until` is in them."""
    sock.setblocking(False)
    data = b""
    for _ in range(tries):
        server.service()
        try:
            chunk = sock.recv(4096)
        except BlockingIOError:
            chunk = b""
        data += chunk
        if until in data:
            break
        time.sleep(0.01)
    return data


def _okApp(environ, start_response):
    start_response("200 OK", [("Content-Length", "2")])
    return [b"ok"]


def test_accepted_remoter_gets_server_tymeout():
    tymist = tyming.Tymist()
    with tcp.openServer(tymth=tymist.tymen(), ha=("", 6431), tymeout=1.5) as server:
        sock, ix = _accept(server, 6431)
        try:
            assert ix.tymeout == 1.5
            assert ix.tymer.duration == 1.5
        finally:
            sock.close()


def test_accepted_remoter_default_never_times_out():
    tymist = tyming.Tymist()
    with tcp.openServer(tymth=tymist.tymen(), ha=("", 6432)) as server:
        sock, ix = _accept(server, 6432)
        try:
            assert ix.tymeout == 0.0
        finally:
            sock.close()


def test_http_server_drops_connection_with_unfinished_headers():
    """A client that never finishes its headers is dropped after tymeout."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6433
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc")  # headers never finish
        assert _serviceUntil(server, lambda: server.servant.ixes)  # accepted and held

        for _ in range(8):  # two virtual seconds with no further bytes
            tymist.tick()
            server.service()
        assert not server.servant.ixes  # dropped once idle past tymeout
    finally:
        sock.close()
        server.servant.close()


def test_http_server_tymeout_counts_from_last_byte():
    """
    A client trickling one byte per tick is kept while bytes arrive faster
    than tymeout, and dropped once tymeout has passed since the LAST byte.
    A lossless tymer restart per byte would instead bank a whole tymeout per
    byte, and the trickler would never be dropped.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6434
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"G")  # request line that never ends
        assert _serviceUntil(server, lambda: server.servant.ixes)
        ix = next(iter(server.servant.ixes.values()))

        for _ in range(20):  # five virtual seconds, one byte per 0.25 s
            tymist.tick()
            before = len(ix.rxbs)
            sock.sendall(b"E")
            assert _serviceUntil(server, lambda: len(ix.rxbs) > before)
            assert server.servant.ixes  # still held while bytes keep coming

        for _ in range(3):  # 0.75 s since the last byte
            tymist.tick()
            server.service()
        assert server.servant.ixes

        for _ in range(2):  # 1.25 s since the last byte
            tymist.tick()
            server.service()
        assert not server.servant.ixes
    finally:
        sock.close()
        server.servant.close()


def test_bare_server_drops_idle_connection():
    """BareServer removes an expired connection without mutating ixes mid-iteration."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6435
    server = http.BareServer(port=port, tymth=tymist.tymen(), timeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc")  # headers never finish
        assert _serviceUntil(server, lambda: server.servant.ixes)

        for _ in range(8):
            tymist.tick()
            server.service()  # raised RuntimeError: dict changed size
        assert not server.servant.ixes
        assert not server.stewards
    finally:
        sock.close()
        server.servant.close()


def test_bare_server_keeps_idle_persistent_connection_by_default():
    """BareServer follows the same keep alive rules as Server."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6448
    server = http.BareServer(port=port, tymth=tymist.tymen(), timeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET /echo HTTP/1.1\r\nHost: loc\r\nContent-Length: 0\r\n\r\n")
        data = _recvAll(sock, server, until=b'"method":"GET"')
        assert data.startswith(b"HTTP/1.1 200 OK")

        _advance(server, tymist, 40)  # 10 s idle between requests
        assert server.servant.ixes

        server.keepTymeout = 1.0
        _advance(server, tymist, 1)  # already idle far past keepTymeout
        assert not server.servant.ixes
    finally:
        sock.close()
        server.servant.close()


def test_http_server_without_tymist_serves_request():
    """
    A server serviced by hand with no tymth wound has no tyme. Its connections
    must never be timed out and servicing them must not raise.
    """
    port = 6436
    server = http.Server(port=port, app=_okApp, tymeout=1.0)  # no tymth
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc\r\nContent-Length: 0\r\n\r\n")
        data = _recvAll(sock, server, until=b"\r\n\r\nok")
        assert data.startswith(b"HTTP/1.1 200 OK")
        assert data.endswith(b"\r\n\r\nok")
        server.service()
        assert server.servant.ixes  # persistent and never timed out
    finally:
        sock.close()
        server.close()


REQUEST = b"GET / HTTP/1.1\r\nHost: loc\r\nContent-Length: 0\r\n\r\n"


def _keptConnection(port, tymist, **kwa):
    """Serve one request on a persistent connection; return (server, sock)."""
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(),
                         tymeout=1.0, **kwa)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    sock.sendall(REQUEST)
    data = _recvAll(sock, server, until=b"\r\n\r\nok")
    assert data.endswith(b"\r\n\r\nok")
    assert server.servant.ixes  # kept alive for the next request
    return server, sock


def _advance(server, tymist, ticks):
    for _ in range(ticks):
        tymist.tick()
        server.service()


def test_http_server_keeps_idle_persistent_connection_by_default():
    """
    A keep-alive connection idle between requests is not subject to tymeout,
    and with the default keepTymeout of 0.0 is never dropped. Clients such as
    keripy's HTTPMessenger hold one connection across long gaps and do not
    reconnect when the server closes it.
    """
    tymist = tyming.Tymist(tock=0.25)
    server, sock = _keptConnection(6441, tymist)
    try:
        _advance(server, tymist, 40)  # 10 s idle, 10x tymeout
        assert server.servant.ixes

        sock.sendall(REQUEST)  # and it still serves
        data = _recvAll(sock, server, until=b"\r\n\r\nok")
        assert data.endswith(b"\r\n\r\nok")
    finally:
        sock.close()
        server.close()


def test_http_server_drops_idle_persistent_connection_after_keep_tymeout():
    """A keep-alive connection idle between requests is dropped after keepTymeout."""
    tymist = tyming.Tymist(tock=0.25)
    server, sock = _keptConnection(6442, tymist, keepTymeout=3.0)
    try:
        _advance(server, tymist, 11)  # 2.75 s idle, past tymeout
        assert server.servant.ixes

        _advance(server, tymist, 2)  # 3.25 s idle
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_http_server_drops_partial_second_request_after_tymeout():
    """
    Once the next request on a keep-alive connection begins to arrive,
    tymeout applies again, so a stalled second request head is dropped.
    """
    tymist = tyming.Tymist(tock=0.25)
    server, sock = _keptConnection(6443, tymist)
    try:
        _advance(server, tymist, 12)  # 3 s idle between requests is fine
        assert server.servant.ixes

        sock.sendall(b"GET / HTTP/1.1\r\nHo")  # head never finishes
        ix = next(iter(server.servant.ixes.values()))
        assert _serviceUntil(server, lambda: server.reqs[ix.ca].started)  # request begun
        _advance(server, tymist, 3)  # 0.75 s
        assert server.servant.ixes
        _advance(server, tymist, 2)  # 1.25 s
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_http_server_serves_request_buffered_at_tymeout_boundary():
    """
    Bytes already received by the kernel when the tymer runs out count as
    activity: the request is served, not discarded with unread data.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6444
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc")
        assert _serviceUntil(server, lambda: server.servant.ixes)
        _advance(server, tymist, 3)  # 0.75 s silent

        sock.sendall(b"\r\nContent-Length: 0\r\n\r\n")  # rest of head
        time.sleep(0.05)  # now sitting in the server's kernel buffer
        tymist.tick()  # 1.0 s: tymer expired before the bytes are read
        server.service()
        assert server.servant.ixes  # the buffered bytes kept it alive

        data = _recvAll(sock, server, until=b"\r\n\r\nok")
        assert data.endswith(b"\r\n\r\nok")
    finally:
        sock.close()
        server.close()


BIG = 20000  # response body size


def _bigApp(environ, start_response):
    start_response("200 OK", [("Content-Length", str(BIG))])
    return [b"x" * BIG]


def test_http_server_drops_stopped_reader():
    """
    A finished response whose bytes the reader has stopped taking is dropped
    after tymeout without send progress, rather than held forever.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6445
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        ix = next(iter(server.servant.ixes.values()))
        ix.send = lambda data: 0  # reader takes nothing: every send blocks

        sock.sendall(REQUEST)
        assert _serviceUntil(server, lambda: server.reps and
                             next(iter(server.reps.values())).ended)
        assert ix.txbs  # response finished but unsent

        _advance(server, tymist, 3)  # 0.75 s without progress
        assert server.servant.ixes
        _advance(server, tymist, 2)  # 1.25 s without progress
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_http_server_keeps_slow_reader():
    """
    A reader taking a large response a little at a time, more often than
    tymeout, is not cut however long the whole body takes.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6451
    server = http.Server(port=port, app=_bigApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        ix = next(iter(server.servant.ixes.values()))
        send = ix.send
        ix.send = lambda data: send(data[:1000])  # 1000 bytes per cycle

        sock.sendall(REQUEST)
        sock.setblocking(False)
        data = b""
        for _ in range(60):  # 15 virtual s, far past tymeout
            tymist.tick()
            server.service()
            time.sleep(0.005)
            try:
                data += sock.recv(65536)
            except BlockingIOError:
                pass
            assert server.servant.ixes
            if data.endswith(b"x" * 1000) and len(data) > BIG:
                break
        assert data.endswith(b"\r\n\r\n" + b"x" * BIG)
    finally:
        sock.close()
        server.close()


def test_http_server_applies_explicit_tymeout_to_passed_servant():
    """An explicit tymeout reaches a servant passed in; None leaves its own."""
    servant = tcp.Server(ha=("", 6446))
    server = http.Server(port=6446, app=_okApp, servant=servant, tymeout=2.0)
    assert server.servant is servant
    assert servant.tymeout == 2.0

    servant = tcp.Server(ha=("", 6446), tymeout=3.0)
    http.Server(port=6446, app=_okApp, servant=servant)
    assert servant.tymeout == 3.0


@pytest.mark.parametrize("port, connection", [(6438, b"close"),
                                              (6440, b"keep-alive")])
def test_http_server_keeps_long_poll_response(port, connection):
    """
    A response in progress whose iterable yields b'' while it waits (a long
    poll or event stream) sends no bytes, but must not be cut by the idle
    tymeout, whether or not the connection is persistent.
    """
    state = dict(done=False)

    def longPollApp(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/event-stream")])
        while not state["done"]:
            yield b""
        yield b"data: done\n\n"

    tymist = tyming.Tymist(tock=0.25)
    server = http.Server(port=port, app=longPollApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET /poll HTTP/1.1\r\nHost: loc\r\nConnection: "
                     + connection + b"\r\n\r\n")
        assert _serviceUntil(server, lambda: server.reps)  # response started

        for _ in range(16):  # four virtual seconds of waiting, 4x tymeout
            tymist.tick()
            server.service()
            assert server.servant.ixes  # in-progress response is not idle
        assert server.reps and not next(iter(server.reps.values())).ended

        state["done"] = True
        data = _recvAll(sock, server, until=b"data: done\n\n")
        assert b"data: done\n\n" in data
    finally:
        sock.close()
        server.close()


def localTestCertDirPath():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs')


def test_tls_server_drops_connection_without_handshake():
    """
    A client that opens TCP to a ServerTls and never sends a ClientHello is
    dropped from .cxes once tymeout passes, instead of holding an fd forever.
    """
    certDirPath = localTestCertDirPath()
    tymist = tyming.Tymist(tock=0.25)
    port = 6439
    with tcp.openServer(cls=tcp.ServerTls,
                        tymth=tymist.tymen(),
                        ha=("", port),
                        tymeout=1.0,
                        keypath=os.path.join(certDirPath, 'server_key.pem'),
                        certpath=os.path.join(certDirPath, 'server_cert.pem'),
                        cafilepath=os.path.join(certDirPath, 'client.pem')) as server:
        sock = socket.create_connection(("127.0.0.1", port))
        try:
            for _ in range(50):
                server.serviceConnects()
                if server.cxes:
                    break
                time.sleep(0.02)
            assert server.cxes  # accepted, handshake pending
            cx = next(iter(server.cxes.values()))

            for _ in range(3):  # 0.75 s
                tymist.tick()
                server.serviceConnects()
            assert server.cxes

            for _ in range(2):  # 1.25 s
                tymist.tick()
                server.serviceConnects()
            assert not server.cxes
            assert not server.ixes
            assert cx.cs is None  # socket closed

            sock.settimeout(1.0)
            assert sock.recv(1) == b""  # far side sees the close
        finally:
            sock.close()


def test_tls_server_expires_handshake_accepted_before_wind():
    """
    A connection accepted before the server is wound onto a Tymist is wound
    with it, so a handshake that never completes still expires.
    """
    certDirPath = localTestCertDirPath()
    port = 6447
    with tcp.openServer(cls=tcp.ServerTls,
                        ha=("", port),
                        tymeout=1.0,
                        keypath=os.path.join(certDirPath, 'server_key.pem'),
                        certpath=os.path.join(certDirPath, 'server_cert.pem'),
                        cafilepath=os.path.join(certDirPath, 'client.pem')) as server:
        sock = socket.create_connection(("127.0.0.1", port))
        try:
            for _ in range(50):
                server.serviceConnects()
                if server.cxes:
                    break
                time.sleep(0.02)
            assert server.cxes  # accepted with no tymth

            tymist = tyming.Tymist(tock=0.25)
            server.wind(tymist.tymen())
            for _ in range(3):  # 0.75 s
                tymist.tick()
                server.serviceConnects()
            assert server.cxes

            for _ in range(2):  # 1.25 s
                tymist.tick()
                server.serviceConnects()
            assert not server.cxes
        finally:
            sock.close()


def test_http_server_keeps_fresh_connection_before_first_byte():
    """
    tymeout starts at a request's first byte. A client that connects and
    sends its first request much later, as keripy's HTTPMessenger may, is
    governed by keepTymeout (default never), not dropped after tymeout.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6449
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        _advance(server, tymist, 24)  # 6 s before the first byte
        assert server.servant.ixes

        sock.sendall(REQUEST)
        data = _recvAll(sock, server, until=b"\r\n\r\nok")
        assert data.endswith(b"\r\n\r\nok")
    finally:
        sock.close()
        server.close()


def test_http_server_drops_fresh_connection_after_keep_tymeout():
    """A fresh connection with no bytes is dropped after keepTymeout when set."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6457
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(),
                         tymeout=1.0, keepTymeout=2.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        _advance(server, tymist, 7)  # 1.75 s
        assert server.servant.ixes
        _advance(server, tymist, 2)  # 2.25 s
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_http_server_prunes_removed_and_replaced_connections():
    """
    A connection the servant removes or replaces at the same ca leaves no
    requestant or responder reading the old remoter.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6450
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sockA = socket.create_connection(("127.0.0.1", port))
    sockB = socket.create_connection(("127.0.0.1", port))
    try:
        sockA.sendall(REQUEST)
        data = _recvAll(sockA, server, until=b"\r\n\r\nok")
        assert data.endswith(b"\r\n\r\nok")
        assert len(server.servant.ixes) == 2
        caA = sockA.getsockname()
        caB = sockB.getsockname()
        caA = next(ca for ca in server.servant.ixes if ca[1] == caA[1])
        caB = next(ca for ca in server.servant.ixes if ca[1] == caB[1])
        assert caA in server.reqs and caA in server.reps

        # replace: the remoter for B now sits under A's ca
        ixB = server.servant.ixes.pop(caB)
        server.servant.ixes[caA].close()
        server.servant.ixes[caA] = ixB
        sockB.sendall(REQUEST)
        data = _recvAll(sockB, server, until=b"\r\n\r\nok")
        assert data.endswith(b"\r\n\r\nok")  # served from the new remoter
        assert server.reqs[caA].remoter is ixB
        assert caB not in server.reqs

        # remove, as serviceReceivesAllIx does on an OSError
        server.servant.removeIx(caA)
        server.service()
        assert not server.reqs and not server.reps
    finally:
        sockA.close()
        sockB.close()
        server.close()


def test_bare_server_sends_http10_response_before_closing():
    """
    A non-persistent (HTTP/1.0) connection is closed only after its response
    has been sent.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6453
    server = http.BareServer(port=port, tymth=tymist.tymen(), timeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET /echo HTTP/1.0\r\nHost: loc\r\n\r\n")
        sock.setblocking(False)
        data = b""
        closed = False
        for _ in range(100):
            server.service()
            try:
                chunk = sock.recv(65536)
            except BlockingIOError:
                chunk = None
            if chunk == b"":
                closed = True
                break
            if chunk:
                data += chunk
            time.sleep(0.01)
        assert data.startswith(b"HTTP/1.1 200 OK")
        assert b'"method":"GET"' in data
        assert closed
        assert not server.servant.ixes
    finally:
        sock.close()
        server.servant.close()


def test_bare_server_wound_by_server_doer():
    """BareServer can be wound, as by http.ServerDoer, so its timeouts fire."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6454
    server = http.BareServer(port=port, timeout=1.0)  # no tymth
    doer = http.ServerDoer(server=server)
    doer.wind(tymist.tymen())
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc")  # headers never finish
        assert _serviceUntil(server, lambda: server.servant.ixes)
        _advance(server, tymist, 5)  # 1.25 s
        assert not server.servant.ixes
    finally:
        sock.close()
        server.servant.close()


def test_http_server_applies_explicit_tymeout_to_held_connections():
    """
    An explicit tymeout given with a servant also reaches the connections
    the servant already holds, in .ixes and, for TLS, in .cxes.
    """
    tymist = tyming.Tymist(tock=0.25)
    with tcp.openServer(tymth=tymist.tymen(), ha=("", 6455)) as servant:
        sock, ix = _accept(servant, 6455)
        try:
            assert ix.tymeout == 0.0
            http.Server(port=6455, app=_okApp, servant=servant, tymeout=1.5)
            assert ix.tymeout == 1.5
            assert ix.tymer.duration == 1.5
        finally:
            sock.close()

    certDirPath = localTestCertDirPath()
    with tcp.openServer(cls=tcp.ServerTls,
                        tymth=tymist.tymen(),
                        ha=("", 6456),
                        keypath=os.path.join(certDirPath, 'server_key.pem'),
                        certpath=os.path.join(certDirPath, 'server_cert.pem'),
                        cafilepath=os.path.join(certDirPath, 'client.pem')) as servant:
        sock = socket.create_connection(("127.0.0.1", 6456))
        try:
            for _ in range(50):
                servant.serviceConnects()
                if servant.cxes:
                    break
                time.sleep(0.02)
            cx = next(iter(servant.cxes.values()))
            assert cx.tymeout == 0.0
            http.Server(port=6456, app=_okApp, servant=servant, tymeout=1.0)
            assert cx.tymeout == 1.0
            _advance(servant, tymist, 5)
            assert not servant.cxes  # handshake deadline now applies
        finally:
            sock.close()


def test_server_timeouts_off_by_default():
    """
    Every server timeout is opt in: tyme can jump during Doist catch up, so
    a timeout on by default would drop healthy clients.
    """
    assert http.Server.Tymeout == 0.0
    assert http.Server.KeepTymeout == 0.0
    assert http.BareServer.Timeout == 0.0
    assert http.BareServer.KeepTymeout == 0.0
    assert http.Server(port=6463, app=_okApp).servant.tymeout == 0.0
    assert http.BareServer(port=6463).servant.tymeout == 0.0


def test_http_server_drops_stopped_reader_that_keeps_sending():
    """
    Received bytes do not count as send progress, so a peer that has stopped
    reading cannot hold a stalled send open by trickling bytes.
    """
    tymist = tyming.Tymist(tock=0.25)
    port = 6458
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), tymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        ix = next(iter(server.servant.ixes.values()))
        ix.send = lambda data: 0  # reader takes nothing: every send blocks
        sock.sendall(REQUEST)
        assert _serviceUntil(server, lambda: server.reps and
                             next(iter(server.reps.values())).ended)
        assert ix.txbs

        for _ in range(8):  # 2 s, a byte from the peer every tick
            if not server.servant.ixes:
                break
            sock.sendall(b"X")
            before = len(ix.rxbs)
            _serviceUntil(server, lambda: len(ix.rxbs) > before or
                          not server.servant.ixes, tries=20)
            tymist.tick()
            server.service()
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_bare_server_removes_connection_closed_by_peer():
    """BareServer removes a connection the peer has closed, as Server does."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6459
    server = http.BareServer(port=port, tymth=tymist.tymen())
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET /echo HTTP/1.1\r\nHost: loc\r\nContent-Length: 0\r\n\r\n")
        data = _recvAll(sock, server, until=b'"method":"GET"')
        assert data.startswith(b"HTTP/1.1 200 OK")
        sock.close()
        assert _serviceUntil(server, lambda: not server.servant.ixes)
        assert not server.stewards
    finally:
        sock.close()
        server.servant.close()


def _tlsServer(port, **kwa):
    certDirPath = localTestCertDirPath()
    return tcp.openServer(cls=tcp.ServerTls,
                          ha=("", port),
                          keypath=os.path.join(certDirPath, 'server_key.pem'),
                          certpath=os.path.join(certDirPath, 'server_cert.pem'),
                          cafilepath=os.path.join(certDirPath, 'client.pem'),
                          **kwa)


def _acceptCx(servant):
    for _ in range(50):
        servant.serviceConnects()
        if servant.cxes:
            break
        time.sleep(0.02)
    assert servant.cxes
    return next(iter(servant.cxes.values()))


def test_tls_set_tymeout_keeps_handshake_deadline_from_accept():
    """
    Setting tymeout on a ServerTls changes the handshake deadline's length
    but not its start, so it still counts from accept and setting it again
    cannot extend it.
    """
    tymist = tyming.Tymist(tock=0.25)
    with _tlsServer(6460, tymth=tymist.tymen(), tymeout=1.0) as servant:
        sock = socket.create_connection(("127.0.0.1", 6460))
        try:
            _acceptCx(servant)
            _advance(servant, tymist, 3)  # 0.75 s since accept
            assert servant.cxes
            servant.setTymeout(1.0)  # again
            servant.setTymeout(1.0)
            _advance(servant, tymist, 1)  # 1.0 s since accept
            assert not servant.cxes
        finally:
            sock.close()


def test_server_closes_replaced_remoter():
    """
    A new connection accepted at the same ca as one still held replaces it,
    and the old remoter's socket is closed rather than leaked.
    """
    tymist = tyming.Tymist()
    port = 6461
    with tcp.openServer(tymth=tymist.tymen(), ha=("", port)) as server:
        first = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        first.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        first.bind(("127.0.0.1", 0))
        local = first.getsockname()
        first.connect(("127.0.0.1", port))
        for _ in range(50):
            server.serviceConnects()
            if server.ixes:
                break
            time.sleep(0.02)
        old = server.ixes[local]
        # abort with RST so the local port is free at once, then reuse it
        first.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        first.close()
        second = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        second.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        second.bind(local)
        second.connect(("127.0.0.1", port))
        try:
            for _ in range(50):
                server.serviceConnects()
                if server.ixes[local] is not old:
                    break
                time.sleep(0.02)
            assert server.ixes[local] is not old
            assert old.cs is None  # closed, not just shut down
        finally:
            second.close()


def test_tls_server_closes_remoter_replaced_on_handshake():
    """
    When a handshake completes for a ca that already has a connection in
    .ixes, the old remoter is closed. Uses a stub for the completed handshake.
    """
    class Stub:
        connected = True
        aborted = False
        def __init__(self, ca):
            self.ca = ca
        def handshake(self):
            pass
        def refresh(self):
            pass
        def close(self):
            pass

    tymist = tyming.Tymist()
    with _tlsServer(6462, tymth=tymist.tymen()) as servant:
        sock = socket.create_connection(("127.0.0.1", 6462))
        try:
            cx = _acceptCx(servant)
            ca = cx.ca
            servant.cxes.clear()
            servant.ixes[ca] = cx  # as if its handshake had completed
            stub = Stub(ca)
            servant.cxes[ca] = stub  # a new connection at the same ca
            servant.serviceCxes()
            assert servant.ixes[ca] is stub
            assert cx.cs is None  # old remoter closed
        finally:
            sock.close()


def test_keep_tymeout_alone_bounds_request_receipt():
    """With only keepTymeout set, a stalled request is dropped after it."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6464
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), keepTymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        sock.sendall(b"GET / HTTP/1.1\r\nHost: loc")  # headers never finish
        assert _serviceUntil(server, lambda: server.servant.ixes)
        _advance(server, tymist, 5)  # 1.25 s
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_keep_tymeout_alone_bounds_stalled_send():
    """With only keepTymeout set, a stopped reader is dropped after it."""
    tymist = tyming.Tymist(tock=0.25)
    port = 6465
    server = http.Server(port=port, app=_okApp, tymth=tymist.tymen(), keepTymeout=1.0)
    server.servant.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: server.servant.ixes)
        ix = next(iter(server.servant.ixes.values()))
        ix.send = lambda data: 0  # reader takes nothing
        sock.sendall(REQUEST)
        assert _serviceUntil(server, lambda: server.reps and
                             next(iter(server.reps.values())).ended)
        assert ix.txbs
        _advance(server, tymist, 5)  # 1.25 s
        assert not server.servant.ixes
    finally:
        sock.close()
        server.close()


def test_keep_tymeout_alone_bounds_tls_handshake():
    """
    With only keepTymeout set on an http.Server given a ServerTls servant, a
    connection that never handshakes is dropped after keepTymeout.
    """
    certDirPath = localTestCertDirPath()
    tymist = tyming.Tymist(tock=0.5)
    port = 6466
    servant = tcp.ServerTls(ha=("", port),
                            keypath=os.path.join(certDirPath, 'server_key.pem'),
                            certpath=os.path.join(certDirPath, 'server_cert.pem'),
                            cafilepath=os.path.join(certDirPath, 'client.pem'))
    server = http.Server(servant=servant, app=_okApp, keepTymeout=2.0)
    server.wind(tymist.tymen())
    server.reopen()
    sock = socket.create_connection(("127.0.0.1", port))
    try:
        assert _serviceUntil(server, lambda: servant.cxes)
        _advance(server, tymist, 3)  # 1.5 s
        assert servant.cxes
        _advance(server, tymist, 2)  # 2.5 s
        assert not servant.cxes
        assert not servant.ixes
    finally:
        sock.close()
        server.close()
