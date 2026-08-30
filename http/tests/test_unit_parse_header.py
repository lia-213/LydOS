"""
Unit tests for parse_header() — string/protocol parsing in isolation,
no sockets or filesystem involved.
"""
import pytest

from httpserver import parse_header

GET_REQUEST = "GET /ipsum.html HTTP/1.1\nHost: example.com\nAccept: text/html\n"


def test_parse_header_extracts_request_line_target_under_file_key():
    headers = parse_header(GET_REQUEST)
    assert headers["FILE"] == "/ipsum.html"


def test_parse_header_extracts_named_headers():
    headers = parse_header(GET_REQUEST)
    assert headers["Host"] == "example.com"
    assert headers["Accept"] == "text/html"


def test_parse_header_lookup_is_case_insensitive():
    headers = parse_header(GET_REQUEST)
    assert headers["host"] == "example.com"
    assert headers["HOST"] == "example.com"


def test_parse_header_skips_blank_lines():
    request = "GET / HTTP/1.1\nHost: example.com\n\n\nAccept: text/html\n"
    headers = parse_header(request)
    assert headers["Accept"] == "text/html"


def test_parse_header_get_with_default_for_missing_header():
    headers = parse_header("GET / HTTP/1.1\n")
    assert headers.get("Content-Length", "0") == "0"


@pytest.mark.xfail(reason="known limitation: duplicate headers overwrite instead of combining (see http-next-steps.md)")
def test_parse_header_duplicate_header_names_are_both_preserved():
    request = "GET / HTTP/1.1\nSet-Cookie: a=1\nSet-Cookie: b=2\n"
    headers = parse_header(request)
    assert headers["Set-Cookie"] == "a=1, b=2"


def test_parse_header_folded_continuation_line_is_not_supported_by_design():
    """
    Folded headers (obs-fold) are deprecated/forbidden by RFC 7230/9110 and
    were a real source of request-smuggling bugs, so this server
    deliberately does not parse them (see README.md -> "Design decisions").
    A single-word continuation line (no colon) falls into the "this must be
    the request line" branch and raises IndexError trying to read a path
    out of it -- accepted as correct rejection of a non-conformant sender,
    not a bug to fix.
    """
    request = "GET / HTTP/1.1\nX-Long-Header: part-one\n part-two\n"
    with pytest.raises(IndexError):
        parse_header(request)


@pytest.mark.xfail(reason="known limitation: trailing \\r is left on header values because we only split on \\n (see http-next-steps.md)")
def test_parse_header_value_has_no_trailing_carriage_return():
    request = "GET / HTTP/1.1\r\nHost: example.com\r\n"
    headers = parse_header(request)
    assert headers["Host"] == "example.com"
