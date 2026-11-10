# http

A from-scratch HTTP/1.0 server built on raw sockets, no framework. This is
the `http/` component of [LydOS](../README.md).

Started from João Ventura's tutorial *"Building a basic HTTP Server from
scratch in Python"*; extended beyond it (see [`http-next-steps.md`](./http-next-steps.md)
for the full backlog).

---

## Design decisions

### Folded headers: not supported, by design

HTTP's old "obsolete line folding" (`obs-fold`) let a single header value
span multiple lines, continued by a leading space/tab:

```
User-Agent: Mozilla/5.0
    Chrome/120.0.0.0
```

This is **deprecated and forbidden** by the current spec (RFC 7230 / RFC
9110) — senders must not generate it, and receivers should reject or
carefully normalize it rather than parse it naively. It was removed
specifically because inconsistent folding support across proxies/servers
enabled HTTP request smuggling and CRLF injection attacks.

Given that, this server intentionally does **not** implement folded-header
parsing. Multi-value/long header values are handled the modern, spec-compliant
way instead:

- **Comma-separated values** on a single line, for most headers — repeating
  a header is equivalent to sending one comma-joined line per RFC 9110
  (`Accept: a` + `Accept: b` == `Accept: a, b`).
- **Repeated header lines** kept as independent entries, for the small set
  of headers where comma-joining would corrupt the value — `Set-Cookie`
  being the primary case (each line sets one cookie with its own
  attributes, and `Expires=Wed, 21 Oct 2026...` already contains a comma).
  `WWW-Authenticate`/`Proxy-Authenticate` share the same hazard.

`parse_header()`'s known limitation around duplicate headers (currently
last-value-wins) is what needs fixing to support both cases properly —
tracked in [`http-next-steps.md`](./http-next-steps.md). Tests for the
target behavior already exist (TDD, currently failing) in
[`test_unit_parse_header.py`](./tests/test_unit_parse_header.py).

---

## Tests

See [`tests/`](./tests/) — unit, integration, acceptance, end-to-end, and a
TDD backlog suite (`xfail` tests for not-yet-built features). Run with:

```bash
python3 -m pytest http/tests -q
```
