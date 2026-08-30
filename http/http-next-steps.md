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

- [x] **Proper header parsing** ⭐⭐ — case-insensitivity done via a hand-rolled `HeaderDict(abc.MutableMapping)`; duplicate headers and folded headers still open (see below).
  The tutorial only ever reads `headers[0]` — the request line. Everything else (`Host`, `Content-Type`, `Content-Length`, `Connection`, etc.) is ignored.
  Parse the full header block into a dict/map, not just the first line.
  Signal: string/protocol parsing, edge cases (folded headers, case-insensitivity, duplicate headers).
  - [x] Case-insensitive header names — `HeaderDict` normalizes keys to uppercase on write (`__setitem__`) and read (`__getitem__`/`__delitem__`), verified with `curl -H "host/Host/HOST: ..."` all resolving to the same entry. See `http-case-insensitivity.md`.
  - [ ] **Stretch: case-preserving storage (Option B)** — current `HeaderDict` is case-insensitive for matching but destructive: the original casing a client sent (`Host` vs `host`) is discarded the moment `__setitem__` uppercases it, so iteration/`__repr__`/logging only ever show the normalized form. `requests.structures.CaseInsensitiveDict` (and most real implementations) instead store something like `{normalized_key: (original_key, value)}` so lookup stays case-insensitive but display/iteration returns the casing exactly as received. Worth doing specifically because it forces a storage-shape redesign, not just a tweak — a good standalone exercise, not a blocker for closing out the header-parsing TODO. Decide deliberately whether this is worth the complexity for a hand-rolled learning server, or a case of "A is fine, B is over-engineering" — either answer is defensible, but make it on purpose.
  - [ ] Duplicate headers — `header_dict[k] = v` currently overwrites on repeat keys; last one wins, earlier values silently dropped. **Scope decision:** fix by comma-merging repeats per RFC 9110's general-header rule (`Accept: a` + `Accept: b` → `Accept: a, b`) only. The `Set-Cookie`-style exception (repeats are independent instructions, not comma-mergeable — merging would corrupt values like `Expires=Wed, 21 Oct...` that already contain commas) is explicitly **not** being built now, since this server doesn't implement cookies. Documented here as a known gap so it isn't silently forgotten if `Set-Cookie` support is ever added later — at that point this needs a per-header merge-strategy, not a blanket comma-join.
  - [x] Folded headers — deliberately **not** implemented. `obs-fold` (multi-line header continuation) is deprecated/forbidden by RFC 7230/9110 and was a real source of request-smuggling bugs; a continuation line still hits the "no colon → this must be the request line" branch and corrupts the parsed path, but that's accepted as correct behavior for a non-conformant sender, not a bug to fix. See `README.md` → "Design decisions". Multi-value headers are handled via comma-separation or repeated header lines instead (repeated-header support depends on fixing duplicate-header handling below).
  - [ ] Trailing `\r` on header values (splitting only on `\n` leaves `\r` at the end of each line).

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
- [ ] **Error logging (crash resilience)** — right now an unhandled exception anywhere in the `while True` loop (e.g. the `abc.MutableMapping()` instantiation bug hit while building `HeaderDict`) takes down the entire listening socket, killing the server for every future client, not just the one bad request.
  - Wrap the per-connection body of the loop in `try/except Exception` (with a `finally: client_connection.close()` so the socket always gets cleaned up), so one malformed request or bug can't kill the whole server.
  - Use the standard-library `logging` module instead of ad hoc `print()` — `logging.basicConfig(filename=..., level=..., format=...)` to set it up, then `logging.exception(msg)` inside the `except` block specifically (not `logging.error`), since it automatically captures and writes the full traceback — the same kind of stack trace that's been getting pasted into chat by hand during debugging.
  - Decisions to make deliberately, not by default: where the log file lives (inside `http/`, or elsewhere) and whether it's gitignored (probably yes — run-specific noise, not source); log level threshold (`DEBUG` while actively developing vs. `INFO`/`WARNING` once stable); whether to attach both a `FileHandler` and a `StreamHandler` so output still shows in the terminal during dev, not just the file.
  - Ties into the concurrency TODO above: once threading/`select` lands, a single linear terminal won't map cleanly to "which line belongs to which client" — timestamped, per-connection log entries become much more valuable at that point than they are now.
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