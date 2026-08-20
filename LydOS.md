# LydOS

An evolving systems software project, implementing core components of a
modern software stack from scratch: version control, HTTP networking,
database storage, caching, containerisation, and (eventually) distributed
consensus.

Each component is built independently first, following its own tutorial/
learning path, then deliberately integrated afterwards — this repo is meant
to be evidence of understanding how the pieces underneath modern software
fit together, not five disconnected tutorials sharing a folder.

## Components

| Folder | What it is | Status |
|---|---|---|
| [`ugit/`](./ugit/README.md) | **l_git (ugit)** — Git reimplementation: objects, commits, branches, merging, remotes | Most complete — see its own README |
| `http/` | HTTP/1.x server from raw sockets | In progress |
| `database/` | SQLite-style storage/query engine | Not started |
| `cache/` | Redis-style in-memory key-value store | Not started |
| `containers/` | Container runtime (namespaces, isolation) | Not started |
| `distributed/` | Raft consensus | Not started |

Each folder has (or will have) its own README with implementation detail,
known limitations, and its own backlog file — this root README is
deliberately just a map, not a deep-dive.

## Planned integrations

The goal is at least 2–3 real integrations between components, not just a
shared repo name. Currently planned:

- **`ugit` + `http`** — the HTTP server as an interface onto the l_git (ugit)
  implementation (`GET /repos/:user/commits`, `.../tree`, `.../diff`)
- **`database` + `http`** — `POST /users`, `GET /users/:id`, persisted for
  real through the SQLite-style storage engine
- **`cache` + `http`** — the Redis-style store sitting in front of
  frequently accessed data

## Why "LydOS"

Working name — not an actual operating system, just a monorepo for the
pieces you'd find underneath one.