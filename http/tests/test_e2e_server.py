"""
End-to-end tests: exercise the server as a whole running process would be
used in practice — a sequence of real requests over real sockets, no
internals touched or monkeypatched beyond pointing at a throwaway htdocs
dir. These are broader than the acceptance tests (which check one
request/response pair at a time); these check full journeys and
overall system behavior.
"""
import http.client
import socket

from .conftest import send_raw_request


def test_typical_browsing_session_visits_home_then_a_page_then_a_typo(running_server):
    """
    Simulates a user: lands on the homepage, clicks through to a real page,
    then mistypes a URL. Each step is a fresh connection, matching this
    HTTP/1.0, no-keep-alive server's actual behavior.
    """
    host, port = running_server

    home = http.client.HTTPConnection(host, port, timeout=2)
    home.request("GET", "/")
    home_response = home.getresponse()
    assert home_response.status == 200
    assert "home" in home_response.read().decode()
    home.close()

    page = http.client.HTTPConnection(host, port, timeout=2)
    page.request("GET", "/ipsum.html")
    page_response = page.getresponse()
    assert page_response.status == 200
    assert "ipsum" in page_response.read().decode()
    page.close()

    typo = http.client.HTTPConnection(host, port, timeout=2)
    typo.request("GET", "/ipsum.htm")  # missing the final 'l'
    typo_response = typo.getresponse()
    assert typo_response.status == 404
    typo.close()


def test_browser_landing_on_homepage_triggers_expected_favicon_fallback(running_server):
    """
    Real browsers issue two requests on first visit: GET / and GET
    /favicon.ico. Both should succeed end-to-end against this server,
    which has no favicon.ico file and is documented to fall back to
    index.html for it.
    """
    host, port = running_server

    for path in ("/", "/favicon.ico"):
        conn = http.client.HTTPConnection(host, port, timeout=2)
        conn.request("GET", path)
        response = conn.getresponse()
        assert response.status == 200
        conn.close()


def test_server_stays_up_and_correct_across_many_sequential_requests(running_server):
    """
    Overall system stability: N full request/response cycles in a row,
    alternating known-good and known-missing paths, none of which should
    ever crash the listening socket or return the wrong content.
    """
    host, port = running_server
    paths_and_expected_status = [
        ("/", 200),
        ("/ipsum.html", 200),
        ("/missing-1.html", 404),
        ("/", 200),
        ("/missing-2.html", 404),
        ("/ipsum.html", 200),
    ]

    for path, expected_status in paths_and_expected_status:
        conn = http.client.HTTPConnection(host, port, timeout=2)
        conn.request("GET", path)
        response = conn.getresponse()
        response.read()
        assert response.status == expected_status, f"unexpected status for {path}"
        conn.close()


def test_raw_socket_client_gets_a_well_formed_http_response(running_server):
    """
    Confirms the response is usable by something that isn't Python's
    http.client -- i.e. it's actually a valid-shaped HTTP response on the
    wire (status line, blank line, body), the way curl/a browser would
    parse it.
    """
    host, port = running_server
    raw_response = send_raw_request(host, port, "GET / HTTP/1.0\n\n")

    status_line, _, rest = raw_response.partition("\n")
    assert status_line.startswith("HTTP/1.0 200")
    assert "\n\n" in raw_response  # header/body separator present
    body = raw_response.split("\n\n", 1)[1]
    assert "home" in body


def test_server_socket_is_reusable_immediately_after_a_client_disconnects_abruptly(running_server):
    """
    A client that connects and disconnects without sending anything
    (e.g. a browser pre-connect, or a health check) shouldn't wedge the
    server for the next real client.
    """
    host, port = running_server

    abrupt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    abrupt.connect((host, port))
    abrupt.close()  # no request sent at all

    response = send_raw_request(host, port, "GET / HTTP/1.0\n\n")
    assert response.startswith("HTTP/1.0 200 OK")
