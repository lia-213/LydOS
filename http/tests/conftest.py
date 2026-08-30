import socket
import threading
import time
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpserver  # noqa: E402


@pytest.fixture
def htdocs(tmp_path):
    """A throwaway htdocs dir so tests don't depend on / mutate the real one."""
    docs = tmp_path / "htdocs"
    docs.mkdir()
    (docs / "index.html").write_text("<html>home</html>")
    (docs / "ipsum.html").write_text("<html>ipsum</html>")
    return docs


@pytest.fixture
def running_server(htdocs, monkeypatch):
    """
    Starts the real serve_forever() loop in a background thread, bound to an
    ephemeral port, pointed at the throwaway htdocs fixture. Used by
    integration/acceptance tests that need a real socket round-trip.
    """
    monkeypatch.setattr(httpserver, "HTDOCS_DIR", htdocs)

    # port 0 -> OS picks a free ephemeral port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]

    def serve_one_connection_at_a_time():
        while True:
            try:
                client_connection, _ = sock.accept()
            except OSError:
                return
            try:
                httpserver.handle_connection(client_connection)
            except OSError:
                return

    thread = threading.Thread(target=serve_one_connection_at_a_time, daemon=True)
    thread.start()
    time.sleep(0.05)  # give the accept() loop a moment to start

    yield ("127.0.0.1", port)

    sock.close()


def send_raw_request(host, port, raw_request: str, timeout=2.0) -> str:
    """Opens a real TCP connection, sends raw_request bytes, returns the decoded response."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect((host, port))
        client.sendall(raw_request.encode())
        chunks = []
        try:
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        except socket.timeout:
            pass
        return b"".join(chunks).decode()
