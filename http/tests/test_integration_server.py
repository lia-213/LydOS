"""
Integration tests: real TCP socket <-> handle_connection() <-> real filesystem.
No mocking of sockets or files — this is where socket framing bugs
(partial recv, connection-close timing) would actually show up.
"""
from .conftest import send_raw_request


def test_server_returns_200_and_body_for_root_request(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "GET / HTTP/1.0\n\n")
    assert response.startswith("HTTP/1.0 200 OK")
    assert "home" in response


def test_server_returns_200_and_body_for_named_file(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "GET /ipsum.html HTTP/1.0\n\n")
    assert response.startswith("HTTP/1.0 200 OK")
    assert "ipsum" in response


def test_server_returns_404_for_unknown_file(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "GET /nope.html HTTP/1.0\n\n")
    assert response.startswith("HTTP/1.0 404 NOT FOUND")


def test_server_closes_connection_after_each_response(running_server):
    """Server is HTTP/1.0, no keep-alive: socket should be closed server-side after one response."""
    import socket

    host, port = running_server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(2.0)
        client.connect((host, port))
        client.sendall(b"GET / HTTP/1.0\n\n")
        first_chunk = client.recv(4096)
        assert first_chunk  # got a response
        # server should now close its end; a further recv should return b'' (EOF)
        trailing = client.recv(4096)
        assert trailing == b""


def test_server_host_header_is_read_case_insensitively(running_server):
    """
    Sanity check that the real end-to-end path (socket -> parse_header ->
    HeaderDict) doesn't choke on a lowercase Host header, since headers.get
    normalizes internally.
    """
    host, port = running_server
    response = send_raw_request(
        host, port, "GET / HTTP/1.0\nhost: example.com\n\n"
    )
    assert response.startswith("HTTP/1.0 200 OK")
