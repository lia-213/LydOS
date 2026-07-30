# ugit Roadmap: Next Steps

## Step 1 — Finish ugit (foundations)

Before building anything new, make sure these core concepts are genuinely
understood, not just implemented:

- **Blobs** — how file contents get hashed and stored as content-addressed objects
- **Trees** — how flat file paths become a nested directory structure, and how that
  structure is serialized/hashed
- **Commits** — how a commit ties a tree snapshot to parent(s) and a message
- **Refs** — how branch names and tags are just files pointing at OIDs
- **HEAD** — the difference between a symbolic HEAD (on a branch) and a detached
  HEAD (pointing directly at a commit), and why that distinction matters for commit()
- **Checkout** — how the working directory gets reconciled with a target tree,
  and why "only touch tracked files" is the safety guarantee that matters
- **Hashing** — why content-addressing (SHA-256 of type + content) gives you
  deduplication and integrity for free

Already done in this project: `merge` and `diff` are implemented, which covers a
good chunk of the "real Git internals" learning goal on their own.

---

## Step 2 — Extend ugit with something new

Already implemented: `merge`, `diff`. Below are the next candidates worth building.

### A. `ugit log --graph`

**Goal:** render commit history as an ASCII/text graph showing branches and merges,
instead of (or alongside) the current flat linear log.

**Implementation steps:**
1. Look at how `log()` in `cli.py` currently walks history via
   `base.iter_commits_and_parents`. Understand what order commits come out in.
2. Decide on a simple visual scheme first — even a minimal one-line-per-commit
   with `*` for a commit and `|` for continuing lines is enough to start.
   Don't aim for git's full graph renderer on the first pass.
3. Figure out how to detect when a commit has multiple parents (a merge commit)
   vs. a single parent — this is the branching point in the graph.
4. Track "columns" — each active branch line needs a lane/column so parallel
   lines don't overlap. This is the hardest part conceptually: you need a
   mapping from OID to which column it currently occupies as you iterate.
5. Decide how to handle a commit finishing (no more children waiting on it) —
   that's when a column can be freed up and reused.
6. Wire this into `cli.py` as a new `--graph` flag on the existing `log` subcommand
   (argparse's `action='store_true'` is what you want here), and branch your
   print logic based on whether it's set.
7. Test with a repo that has at least one actual merge commit, not just a
   linear history — otherwise you'll never exercise the branching logic.

---

### B. `ugit clean`

**Goal:** an explicit, opt-in command that deletes untracked files/directories —
the safe equivalent of what `_empty_current_directory()` used to do
automatically (and dangerously) inside checkout.

**Why this is worth building:** the logic already mostly exists in
`_empty_current_directory()` (currently dead code, since it's no longer called
by `_checkout_index`). The problem was never the deletion logic itself — it's
that it fired silently as a side effect of checkout. As its own command with
explicit invocation, the same approach becomes legitimate and useful.

**Implementation steps:**
1. Add a new `clean` subcommand to `cli.py`'s argparse setup.
2. Add flags mirroring real git's safety model:
   - a dry-run flag (e.g. `-n`) that only *prints* what would be deleted
   - a force flag (e.g. `-f`) required to actually delete anything
   - default behavior with neither flag should probably just print a
     "use -n to preview or -f to actually delete" message, same as real git
3. In `base.py`, write the actual clean logic: walk the working directory,
   skip anything `is_ignored` catches, and additionally skip anything that's
   in the current index (i.e. only delete genuinely *untracked* files —
   never anything staged or committed).
4. Decide what "untracked" means precisely: compare against `get_index_tree()`
   (or `get_working_tree()` vs the index) rather than deleting purely based on
   the ignore list — this is the key safety difference from the old
   `_empty_current_directory()`, which had no concept of "tracked."
5. For directories: after deleting untracked files, clean up any directories
   left empty as a result — but only ones that were purely composed of the
   files you just removed, not directories containing tracked files.
6. Print a clear list of what was (or would be) deleted before/after running,
   so the user isn't surprised.
7. Test carefully in the sandbox: create a mix of tracked, untracked, and
   ignored files/directories, run `clean -n` first and verify the preview is
   exactly what you'd expect, then run `clean -f` and confirm only the
   untracked items disappeared.

---

### C. `ugit ai-commit`

**Goal:** generate a commit message automatically by inspecting the staged diff
and calling an LLM — treats AI as just another interface on top of the existing
plumbing, not the point of the project.

**Implementation steps:**
1. Identify what "the diff to summarize" actually means here — almost
   certainly the same diff `ugit diff --cached` already produces (HEAD tree vs
   index), since that's "what's about to be committed." Reuse the existing
   `diff.diff_trees` / `_diff` logic rather than writing a new diff path.
2. Decide how to invoke an LLM from Python — you'll need an API client and a
   way to supply credentials (environment variable is the standard approach,
   never hardcode a key in source).
3. Design the prompt: feed the diff text in, ask for a concise conventional
   commit-style message. Think about what to do if the diff is very large —
   you may want to truncate or summarize per-file rather than sending
   everything raw.
4. Add a new `ai-commit` subcommand in `cli.py` that:
   - computes the staged diff
   - sends it to the LLM
   - receives back a proposed message
5. Decide the UX: should it commit immediately with the generated message, or
   show it to the user and ask for confirmation/edit first? (Strongly prefer
   the latter — auto-committing with an unreviewed AI-generated message is a
   good way to end up with a confusing history.)
6. Once confirmed, just call the existing `base.commit(message)` — no need to
   reimplement any commit logic, this feature is purely about *generating the
   message* input to a function you already have.
7. Handle failure gracefully: what happens if there's no API key set, the
   network call fails, or the index is empty (nothing staged to summarize)?
   Each of these should give a clear error rather than a stack trace.
8. Test with a few different kinds of diffs (new file, modified file, deleted
   file, multiple files) to see how well the generated messages hold up.

---

## Notes

- Build and test each feature in the sandbox directory, not inside the ugit
  source repo itself, for the same reasons as always: an in-progress feature
  with bugs shouldn't be able to corrupt the source tree you're editing.
- These three are independent of each other — no particular order required,
  though `log --graph` is probably the most "pure Git internals" one and
  `ai-commit` is the most "new interface" one, so pick based on which itch
  you want to scratch first.