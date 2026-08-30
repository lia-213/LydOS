"""
Acceptance tests: describe the server's observable behavior from a real
client's point of view (a browser, curl, or http.client), in plain terms a
non-implementer would recognize as "the server working."
"""
import http.client

import pytest


@pytest.fixture
def client(running_server):
    host, port = running_server
    conn = http.client.HTTPConnection(host, port, timeout=2)
    yield conn
    conn.close()


def test_visiting_the_site_root_shows_the_homepage(client):
    client.request("GET", "/")
    response = client.getresponse()
    body = response.read().decode()
    assert response.status == 200
    assert "home" in body


def test_requesting_favicon_does_not_error_and_falls_back_to_homepage(client):
    """Browsers auto-request /favicon.ico; this shouldn't produce an error page."""
    client.request("GET", "/favicon.ico")
    response = client.getresponse()
    body = response.read().decode()
    assert response.status == 200
    assert "home" in body


def test_requesting_a_page_that_exists_shows_that_page(client):
    client.request("GET", "/ipsum.html")
    response = client.getresponse()
    body = response.read().decode()
    assert response.status == 200
    assert "ipsum" in body


def test_requesting_a_page_that_does_not_exist_shows_a_not_found_message(client):
    client.request("GET", "/this-page-was-never-created.html")
    response = client.getresponse()
    body = response.read().decode()
    assert response.status == 404
    assert "Not Found" in body


def test_can_serve_two_separate_visitors_one_after_another(running_server):
    """Two independent 'visitors' each get a correct response, in sequence."""
    host, port = running_server

    conn1 = http.client.HTTPConnection(host, port, timeout=2)
    conn1.request("GET", "/")
    resp1 = conn1.getresponse()
    assert resp1.status == 200
    conn1.close()

    conn2 = http.client.HTTPConnection(host, port, timeout=2)
    conn2.request("GET", "/ipsum.html")
    resp2 = conn2.getresponse()
    assert resp2.status == 200
    conn2.close()
