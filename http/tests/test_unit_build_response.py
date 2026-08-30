"""
Unit tests for resolve_file_path() / build_response() — file resolution and
response-string construction, using a real (throwaway) filesystem but no
sockets.
"""
from httpserver import build_response, resolve_file_path, parse_header

GET_ROOT = "GET / HTTP/1.1\nHost: example.com\n"
GET_IPSUM = "GET /ipsum.html HTTP/1.1\nHost: example.com\n"
GET_MISSING = "GET /does-not-exist.html HTTP/1.1\nHost: example.com\n"
GET_FAVICON = "GET /favicon.ico HTTP/1.1\nHost: example.com\n"


def test_resolve_file_path_root_maps_to_index(htdocs):
    headers = parse_header(GET_ROOT)
    assert resolve_file_path(headers, htdocs) == htdocs / "index.html"


def test_resolve_file_path_favicon_maps_to_index(htdocs):
    headers = parse_header(GET_FAVICON)
    assert resolve_file_path(headers, htdocs) == htdocs / "index.html"


def test_resolve_file_path_named_file_maps_to_itself(htdocs):
    headers = parse_header(GET_IPSUM)
    assert resolve_file_path(headers, htdocs) == htdocs / "ipsum.html"


def test_build_response_root_returns_200_and_index_content(htdocs):
    response = build_response(GET_ROOT, htdocs)
    assert response.startswith("HTTP/1.0 200 OK")
    assert "home" in response


def test_build_response_known_file_returns_200_and_its_content(htdocs):
    response = build_response(GET_IPSUM, htdocs)
    assert response.startswith("HTTP/1.0 200 OK")
    assert "ipsum" in response


def test_build_response_missing_file_returns_404(htdocs):
    response = build_response(GET_MISSING, htdocs)
    assert response.startswith("HTTP/1.0 404 NOT FOUND")
    assert "Not Found" in response
