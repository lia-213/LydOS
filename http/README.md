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

- **Comma-separated values** on a single line, for headers like
  `Cache-Control: no-cache, no-store, must-revalidate`
- **Repeated header lines** with the same key, for headers like
  `Set-Cookie` where combining would lose meaning

`parse_header()`'s known limitation around duplicate headers (currently
last-value-wins) is what needs fixing to support the "repeating headers"
case properly — tracked in [`http-next-steps.md`](./http-next-steps.md).

---

## Tests

See [`tests/`](./tests/) — unit, integration, acceptance, end-to-end, and a
TDD backlog suite (`xfail` tests for not-yet-built features). Run with:

```bash
python3 -m pytest http/tests -q
```
