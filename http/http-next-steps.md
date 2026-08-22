# http-server-next.md — backlog

Status: base tutorial (João Ventura's single-page "Building a basic HTTP Server from scratch in Python") finished and understood. This tutorial alone does **not** satisfy the week's learning objective — it's missing concurrency entirely, which was explicitly on the plan. Treat the items below as the actual point of the week, not optional polish.

Same rule as `ugit-next.md`: don't grind this top to bottom for its own sake. But unlike ugit's backlog, the first item here isn't optional — do it before calling Week 2 done.

---

## Core extensions (do these — this is what makes it Week 2's actual deliverable)

- [ ] **Concurrency** ⭐⭐⭐ — not optional
  The tutorial is a single blocking `while True: accept() → recv() → sendall() → close()` loop. One client at a time. This was explicitly called out as this week's focus and the tutorial doesn't touch it.
  Pick **one** approach deliberately and be ready to explain the tradeoff, don't just bolt on threading because it's easiest:
  - **Threading** (`threading.Thread` per connection) — simplest to reason about, but doesn't scale well past moderate connection counts, and you'll hit shared-state/locking questions the moment two requests touch the same resource.
  - **`select`/`selectpoll`-style event loop** — single-threaded, non-blocking I/O multiplexing. More representative of how real servers (nginx, Redis) actually work, harder to get right, much better interview material ("I understand why event loops exist" beats "I called Thread()").
  - **`asyncio`** — Python's built-in async approach; a middle ground, worth knowing but arguably less educational here than hand-rolling `select` once.
  Signal: concurrency models, I/O multiplexing, the C10K problem, why real servers don't just spawn a thread per connection at scale.

- [ ] **Proper header parsing** ⭐⭐
  The tutorial only ever reads `headers[0]` — the request line. Everything else (`Host`, `Content-Type`, `Content-Length`, `Connection`, etc.) is ignored.
  Parse the full header block into a dict/map, not just the first line.
  Signal: string/protocol parsing, edge cases (folded headers, case-insensitivity, duplicate headers).

- [ ] **POST body handling** ⭐⭐
  Tutorial never reads a request body at all — it can't handle the `POST /form.php` example from its own first section.
  Use `Content-Length` from the parsed headers to know how many bytes to read after the blank line; don't just assume one `recv(1024)` call captures everything (it won't, for anything non-trivial).
  Signal: this is also where you'll bump into partial reads on sockets — `recv()` isn't guaranteed to return everything in one call, which is a real, commonly-tested systems concept.

---

## Longer backlog (organic pickup, same as ugit's)

- [ ] Keep-alive / persistent connections (`Connection: keep-alive`) — currently every response closes the connection, which is not how HTTP/1.1 actually behaves by default
- [ ] Proper status codes beyond 200/404 (400 Bad Request, 500 Internal Server Error, 301/302 redirects)
- [ ] `Content-Type` headers based on file extension (currently everything is served with no content-type at all)
- [ ] Chunked transfer encoding
- [ ] Basic routing (map paths to handler functions instead of always reading from `htdocs/`)
- [ ] Request logging (method, path, status, timing — useful once this becomes part of LydOS)
- [ ] Basic rate limiting / connection limits
- [ ] HTTPS/TLS (probably out of scope for this summer, but worth knowing it's missing)
- [ ] Tests
- [ ] Performance benchmarking (requests/sec under threading vs. `select`, once both exist — genuinely interesting comparison to have real numbers for)

---

## Integration idea (ties into LydOS, Week 5–6)

This server is the piece the rest of LydOS plugs into. Once ugit and SQLite exist, this is where they get exposed:

```
GET  /repos/:user/commits      → ugit
GET  /repos/:user/tree         → ugit
GET  /repos/:user/diff         → ugit (needs ugit diff built first — see ugit-next.md)
POST /users                    → database (SQLite)
GET  /users/:id                → database (SQLite)
```

Routing (from the backlog above) becomes a prerequisite for this — a server that only ever reads from `htdocs/` can't serve dynamic endpoints. Build routing when integration time actually arrives (Week 5), not before, unless there's a specific reason to pull it forward.

---

*Same convention as ugit-next.md: check items off in place, don't delete. The gap between "tutorial as given" and "what's actually here" is itself a good interview story — "the tutorial didn't handle concurrent connections at all, so I added X and chose Y because..." is a stronger answer than "I followed a tutorial."*