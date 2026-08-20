# ugit-next.md — backlog

Status: tutorial finished, code understood, moving on to **Build Your Own HTTP Server** as the main track. ugit is not abandoned — it's a side track. Nothing here is scheduled. Pick items up when a later tutorial gives a genuine reason to ("oh, this could improve ugit"), not on a fixed cadence.

Rule: don't work through this list top to bottom for its own sake. That's a form of procrastination disguised as thoroughness. The main track (HTTP → SQLite → Docker → Raft) always takes priority.

---

## Core extensions (the three worth doing properly, eventually)

These were the three originally scoped as "make ugit feel like a real systems project" — do these three before anything further down the list, whenever they get picked up.

- [ ] **`ugit log --graph`** ⭐
  Display commit history as a graph, roughly `git log --graph`-style.
  Forces understanding of the commit DAG instead of treating commits as a flat list.
  Signal: Git internals, data structures, graph traversal, CLI design.

- [ ] **`ugit diff`** ⭐
  Compare two commits, or commit vs. working tree, and show what changed.
  Can start simple (line-level) and progressively handle harder cases (renames, binary files).
  Signal: file manipulation, algorithms, Git's object model, text processing.

- [ ] **`ugit merge`** ⭐
  Real branch merging: find common ancestors, determine changes on each side, handle conflicts, create a merge commit.
  Probably the most technically interesting of the three — this is where DAG traversal actually pays off.
  Signal: DAGs, algorithms, version-control internals, conflict resolution.

- [ ] **`ugit ai-commit`** — optional, not a priority
  Flow: inspect uncommitted diff → send diff to an LLM → generate a commit message → pass to `commit()`.
  Demonstrates API integration + practical LLM use, but explicitly **not** something needed to prove AI fluency. Only do this if it's actually interesting at the time.

---

## Longer backlog (organic pickup only)

Rough order of "probably worth it eventually" → "only if there's a specific reason":

- [ ] Log improvements (beyond `--graph` — e.g. `--oneline`, filtering by author/date)
- [ ] `ugit status` improvements
- [ ] Branches (proper branch pointers, not just refs)
- [ ] `.gitignore` support
- [ ] Staging / unstaging (a real index, not commit-everything)
- [ ] Commit history visualisation (could tie into the portfolio site — a rendered graph, not just CLI ASCII)
- [ ] Better error handling (real Git gives useful messages; does ugit?)
- [ ] Config (`ugit config user.name`, etc.)
- [ ] Remote repositories (push/pull/fetch — this is where it starts overlapping with the HTTP server)
- [ ] Authentication (only meaningful once remotes exist)
- [ ] Tests + CI
- [ ] Performance profiling
- [ ] Documentation pass (README, architecture notes)

---

## Integration idea (main reason to come back to this file)

Once the HTTP server exists, the most natural reason to reopen ugit is **`ugit serve`** — exposing the repository over HTTP instead of just the CLI:

```
GET /repos/:user/commits
GET /repos/:user/tree
GET /repos/:user/diff
```

This is one of the 2–3 target integrations for LydOS (see Pillar 1 / Week 5–6 in the main plan). If `diff` isn't built yet by the time this integration is attempted, that's the natural trigger to come back and build it — driven by a real need, not a checklist.

---

*Add items here as they come up. Check items off in place rather than deleting them — the crossed-out list is itself useful evidence of iterative development if this ever comes up in an interview.*