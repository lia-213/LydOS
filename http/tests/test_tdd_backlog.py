"""
TDD suite for must-implement features that don't exist yet.

Every test here is expected to FAIL (xfail) against the current
implementation. As each backlog item in http-next-steps.md gets built,
flip its test(s) from xfail to a real assertion and delete the xfail
marker — that's the "done" signal for the item.

Grouped to mirror http-next-steps.md's "Core extensions" and
"Longer backlog" sections.
"""
import socket
import time

import pytest

import httpserver
from .conftest import send_raw_request


# ---------------------------------------------------------------------------
# Concurrency (⭐⭐⭐ not optional)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not implemented: server is a single blocking accept/recv/sendall/close loop")
def test_server_handles_a_second_client_while_first_is_still_connected(running_server):
    """
    A slow client holding its connection open should not block a second,
    faster client from getting a response. Today's single-threaded loop
    can't start accept()-ing client 2 until client 1's handle_connection()
    call returns.
    """
    host, port = running_server

    slow_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    slow_client.settimeout(2.0)
    slow_client.connect((host, port))
    # Deliberately don't send anything yet -- simulate a slow/stalled client.

    fast_client_response = send_raw_request(host, port, "GET / HTTP/1.0\n\n", timeout=1.0)
    assert fast_client_response.startswith("HTTP/1.0 200 OK")

    slow_client.close()


@pytest.mark.xfail(reason="not implemented: concurrency model (threading/select/asyncio) not chosen or built yet")
def test_ten_concurrent_clients_all_receive_correct_responses():
    pytest.skip("placeholder: once a concurrency model exists, spin up N threads hitting the server at once")


# ---------------------------------------------------------------------------
# Header parsing edge cases (also covered at unit level in
# test_unit_parse_header.py -- repeated here as end-to-end acceptance)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not implemented: duplicate headers overwrite (last wins) instead of being combined")
def test_duplicate_request_headers_are_not_silently_dropped():
    request_headers = httpserver.parse_header(
        "GET / HTTP/1.1\nX-Forwarded-For: 1.1.1.1\nX-Forwarded-For: 2.2.2.2\n"
    )
    assert "1.1.1.1" in request_headers["X-Forwarded-For"]
    assert "2.2.2.2" in request_headers["X-Forwarded-For"]


@pytest.mark.xfail(reason="not implemented: case-preserving storage (Option B in http-next-steps.md)")
def test_original_header_casing_is_preserved_for_display():
    h = httpserver.HeaderDict()
    h["X-Custom-Header"] = "value"
    assert "X-Custom-Header" in list(h)


# ---------------------------------------------------------------------------
# POST body handling (⭐⭐)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not implemented: server never reads a request body / never uses Content-Length")
def test_post_request_body_is_captured_and_available(running_server):
    host, port = running_server
    body = "name=lydia"
    request = (
        "POST /form.php HTTP/1.0\n"
        f"Content-Length: {len(body)}\n"
        "\n"
        f"{body}"
    )
    response = send_raw_request(host, port, request)
    assert "lydia" in response


@pytest.mark.xfail(reason="not implemented: a single recv(1024) is assumed to capture the whole request/body")
def test_post_body_larger_than_one_recv_chunk_is_fully_read(running_server):
    host, port = running_server
    body = "x=" + ("a" * 5000)  # comfortably bigger than one 1024-byte recv()
    request = (
        "POST /form.php HTTP/1.0\n"
        f"Content-Length: {len(body)}\n"
        "\n"
        f"{body}"
    )
    response = send_raw_request(host, port, request)
    assert str(len(body)) in response or "a" * 5000 in response


# ---------------------------------------------------------------------------
# Longer backlog
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not implemented: every response closes the connection, no keep-alive support")
def test_connection_keep_alive_header_keeps_socket_open_for_a_second_request(running_server):
    host, port = running_server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(2.0)
        client.connect((host, port))
        client.sendall(b"GET / HTTP/1.1\nConnection: keep-alive\n\n")
        first = client.recv(4096)
        assert first.startswith(b"HTTP/1.0 200 OK") or first.startswith(b"HTTP/1.1 200 OK")

        client.sendall(b"GET /ipsum.html HTTP/1.1\nConnection: keep-alive\n\n")
        second = client.recv(4096)
        assert b"ipsum" in second


@pytest.mark.xfail(reason="not implemented: only 200/404 exist, no 400/500/redirects")
def test_malformed_request_returns_400_bad_request(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "NOT A VALID REQUEST LINE AT ALL\n\n")
    assert response.startswith("HTTP/1.0 400")


@pytest.mark.xfail(reason="not implemented: responses never include a Content-Type header")
def test_html_response_includes_content_type_header(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "GET / HTTP/1.0\n\n")
    assert "Content-Type: text/html" in response


@pytest.mark.xfail(reason="not implemented: chunked transfer encoding does not exist")
def test_large_response_can_be_sent_chunked():
    pytest.skip("placeholder: needs a chunked-encoding implementation to test against")


@pytest.mark.xfail(reason="not implemented: no routing layer, everything reads from htdocs/")
def test_custom_route_is_handled_by_a_function_not_a_file(running_server):
    host, port = running_server
    response = send_raw_request(host, port, "GET /api/ping HTTP/1.0\n\n")
    assert "pong" in response


@pytest.mark.xfail(reason="not implemented: no request logging exists yet")
def test_each_request_is_logged_with_method_path_status_and_timing(tmp_path):
    pytest.skip("placeholder: once logging exists, point it at tmp_path and assert on the log file's contents")


@pytest.mark.xfail(reason="not implemented: an exception in the connection loop currently kills the whole server")
def test_one_bad_request_does_not_take_down_the_server_for_later_clients(running_server):
    host, port = running_server
    # A request with a header line missing the required ': ' separator currently
    # raises ValueError inside parse_header (unpacking `k, v = line.split(': ')`),
    # which today propagates all the way up and kills the accept() loop.
    send_raw_request(host, port, "GET / HTTP/1.0\nMalformed-Header-No-Colon-Space\n\n")

    # Server should still be alive and answer the next client normally.
    time.sleep(0.05)
    response = send_raw_request(host, port, "GET / HTTP/1.0\n\n")
    assert response.startswith("HTTP/1.0 200 OK")


@pytest.mark.xfail(reason="not implemented: no rate limiting / connection limits")
def test_excessive_requests_from_one_client_are_throttled():
    pytest.skip("placeholder: needs a rate-limiting implementation to test against")
