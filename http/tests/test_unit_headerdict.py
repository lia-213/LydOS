"""
Unit tests for HeaderDict — no sockets, no files, pure in-memory behavior.
"""
import pytest

from httpserver import HeaderDict


def test_setitem_then_getitem_same_case_roundtrips():
    h = HeaderDict()
    h["Host"] = "example.com"
    assert h["Host"] == "example.com"


def test_getitem_is_case_insensitive_regardless_of_write_case():
    h = HeaderDict()
    h["Host"] = "example.com"
    assert h["host"] == "example.com"
    assert h["HOST"] == "example.com"
    assert h["hOsT"] == "example.com"


def test_setitem_is_case_insensitive_last_write_wins_regardless_of_case():
    h = HeaderDict()
    h["Host"] = "first.com"
    h["HOST"] = "second.com"
    assert h["host"] == "second.com"
    assert len(h) == 1


def test_getitem_missing_key_raises_keyerror():
    h = HeaderDict()
    with pytest.raises(KeyError):
        h["Nonexistent"]


def test_getitem_missing_key_does_not_swallow_the_exception():
    """
    Regression test: __getitem__ previously caught KeyError/TypeError and
    printed instead of raising, which silently broke every MutableMapping
    mixin built on top of it (.get(), `in`, .pop(), etc.).
    """
    h = HeaderDict()
    assert h.get("Nonexistent") is None
    assert h.get("Nonexistent", "/fallback") == "/fallback"
    assert "Nonexistent" not in h


def test_getitem_non_string_key_raises_attributeerror():
    """Non-string keys fail at `key.upper()`, not at the dict lookup itself."""
    h = HeaderDict()
    with pytest.raises(AttributeError):
        h[123]


def test_delitem_is_case_insensitive():
    h = HeaderDict()
    h["Host"] = "example.com"
    del h["HOST"]
    assert "Host" not in h
    assert len(h) == 0


def test_delitem_missing_key_raises_keyerror():
    h = HeaderDict()
    with pytest.raises(KeyError):
        del h["Nonexistent"]


def test_iter_yields_stored_keys():
    h = HeaderDict()
    h["Host"] = "example.com"
    h["Content-Type"] = "text/html"
    assert set(h) == {"HOST", "CONTENT-TYPE"}


def test_len_reflects_number_of_distinct_headers():
    h = HeaderDict()
    assert len(h) == 0
    h["Host"] = "example.com"
    assert len(h) == 1
    h["Content-Type"] = "text/html"
    assert len(h) == 2


def test_contains_is_case_insensitive():
    h = HeaderDict()
    h["Content-Type"] = "text/html"
    assert "content-type" in h
    assert "CONTENT-TYPE" in h


def test_repr_includes_key_and_value():
    h = HeaderDict()
    h["Host"] = "example.com"
    assert "HOST" in repr(h)
    assert "example.com" in repr(h)


@pytest.mark.xfail(reason="known limitation: original casing is discarded on write (see http-next-steps.md 'case-preserving storage')")
def test_iteration_preserves_originally_submitted_casing():
    h = HeaderDict()
    h["Host"] = "example.com"
    assert "Host" in list(h)
