# l_git (ugit)

A from-scratch reimplementation of git, built to actually understand what
git is doing under the hood rather than just using it. Project name is
`l_git`; the tool/CLI itself is `ugit`, per the tutorial it's built from
(see below) — `l_git` refers to the project, `ugit` is the actual command,
package, and folder name.

This is the `ugit/` component of [LydOS](../README.md), an evolving
monorepo of systems projects. It's the oldest and most complete piece —
everything else (HTTP server, database, cache, containers, distributed
consensus) is being built alongside it, and will eventually integrate
with it (e.g. the HTTP server exposing `ugit` repositories over an API).

This project follows [Nikita Leshenko's *"Write yourself a Git!"*](https://www.leshenko.net/p/ugit/)
tutorial — huge thanks to Nikita for writing a walkthrough that actually
explains git's internals (objects, trees, refs, the index) clearly enough
to build something real from, rather than just skimming the surface. If
you're curious how git actually works under the hood, go read it.

This repo picks up where the tutorial leaves off: fixing real bugs found
along the way, adding a full test suite, and pushing the implementation
further than the tutorial itself goes.

### Robustness against Python optimization flags

The original tutorial relies on `assert` statements for defensive programming.
This implementation is **robust against Python's `-O` and `-oo` optimization
flags** (which strip out all `assert` statements) because correctness is
backed by proper exception handling and input validation, not assertions:

- **No defensive asserts**: Critical invariants are validated with `raise
  ValueError()` rather than `assert`, so stripping them has no impact
- **Input validation at boundaries**: Filenames from the object store are
  validated (e.g., `get_tree()` rejects paths with `/` or `..`), reference
  content is parsed safely, and object types are verified on read
- **Proper error handling**: Edge cases (circular symbolic refs, missing
  objects, malformed tree entries) are handled explicitly, not caught by
  asserts
- **No behavior changes under optimization**: This code works identically
  whether run with `python -O`, `python -oo`, or plain `python`

This means `ugit` can safely be deployed in production with Python
optimization enabled for performance, without sacrificing correctness.

---

## What this covers (and where it's limited)

`ugit` implements the core git object model and the everyday commands built
on top of it:

- **Object storage** — content-addressed blobs, trees, and commits
  (`hash-object`, `cat-file`, `write-tree`, `read-tree`)
- **Commits & history** — `commit`, `log`, `show`, with proper parent
  chains and commit traversal
- **Branches & tags** — `branch`, `tag`, both backed by the same simple
  ref-file mechanism
- **Checkout** — switching between commits/branches/tags, including
  detached HEAD, without touching untracked files (this took a few
  iterations to get right — see commit history)
- **Staging** — an `add`/index workflow distinct from the working directory
- **Diffing** — `diff` (working dir/index/commit, `--cached` supported),
  `status`
- **Merging** — fast-forward merges, and true three-way merges via
  `diff3` for diverged branches
- **Remotes** — `fetch` and `push` against another `ugit` repo on disk
  (no server, no network protocol — just another local `.ugit` directory)
- **Graph visualisation** — `ugit k`, dumping the commit/ref graph as DOT,
  rendered via Graphviz if installed, or a quickchart.io fallback if not

### Known limitations

- **No merge conflict resolution UI** — `diff3` inserts standard conflict
  markers into the working tree, but there's no interactive resolution
  helper; you resolve conflicts by hand and `commit` when ready
- **No `.gitignore`-style user-configurable ignore rules** — `is_ignored()`
  is a hardcoded list (`.ugit`, `.git`, `.venv`, `ugit.egg-info`), not a
  pattern file you can edit per-project
- **No pack files or compression** — every object is stored as its own
  loose file, exactly like git before it packs objects; fine for a
  learning project, not built for large repo performance
- **Remotes are local-filesystem only** — `fetch`/`push` expect a path to
  another `.ugit` directory on disk, not a real network protocol (no
  `git://`, SSH, or HTTP transport)
- **No rebase, cherry-pick, stash, or bisect** — the tutorial (and this
  fork) stops at merge; these are common real-git workflows this doesn't
  attempt yet
- **`diff3` is an external dependency** — three-way merges shell out to
  GNU diffutils' `diff3` binary rather than implementing the merge
  algorithm natively (see Prerequisites below)

---

## Where I'm hoping to take this next

See [`ugit-next.md`](./ugit-next.md) for the full, up-to-date backlog. Short version:

- **`ugit log --graph`** — a real ASCII/text commit graph rendered inline
  in the terminal, instead of relying on `ugit k` + Graphviz/a browser tab
  for anything with branching history
- **`ugit clean`** — a proper, explicit, opt-in "delete untracked files"
  command (with `-n` dry-run and `-f` force flags), reusing the walk-the-tree
  logic that used to live — dangerously, as an automatic side effect of
  checkout — in `_empty_current_directory()`
- **`ugit ai-commit`** — generate a candidate commit message by feeding the
  staged diff to an LLM, shown to the user for review/edit before actually
  committing (never auto-committed unreviewed)
- **`ugit serve`** — expose repositories over HTTP once the LydOS HTTP
  server component exists (`GET /repos/:user/commits`, `.../tree`,
  `.../diff`) — this is the first planned LydOS integration
- Continuing to harden the test suite (both the Python `unittest` suite and
  the PowerShell CLI-level scripts) as a safety net for any of the above

---

## Prerequisites

- Python 3.x
- `diff3` (GNU diffutils) — required for `ugit merge` on diverging branches.
  - **Windows**: install via `choco install diffutils`, or use the
    `diff3.exe` bundled with Git for Windows (`<git-install-dir>\usr\bin`)
    and ensure it's on your PATH.
  - **macOS**: `brew install diffutils`
  - **Linux**: usually preinstalled; otherwise `apt install diffutils` /
    equivalent for your distro.

### Windows: unblocking downloaded scripts

PowerShell scripts downloaded via a browser (or extracted from downloaded
`.md` files) get tagged with a hidden "Mark of the Web" flag. Even with an
execution policy of `RemoteSigned`, Windows will refuse to run these with an
error like:

```
File ... cannot be loaded. The file ... is not digitally signed. You cannot
run this script on the current system.
```

Fix by unblocking the scripts once after downloading/extracting them:

```powershell
Get-ChildItem *.ps1 | Unblock-File
```

Run this from inside the folder containing the `.ps1` files before executing
them (e.g. before `.\00-run-all.ps1`).

### A note on PATH and terminal/IDE environment caching

If `diff3` (or any newly-installed tool) still isn't found even after
installing it and confirming it's on PATH, the terminal you're using may be
holding a **stale, cached environment** rather than PATH itself being wrong.

- **Windows**: PATH changes only take effect in *new* processes launched
  after the change. Opening a new tab inside an already-running app (VS
  Code, Windows Terminal, etc.) often reuses that app's original
  environment snapshot rather than fetching a fresh one — so the fix isn't
  "open a new terminal tab," it's "fully quit and reopen the app itself"
  (check Task Manager for lingering processes, e.g. `Code.exe`, and end
  them). If that still doesn't work, the parent shell process
  (`explorer.exe`) may itself be stale; restarting it forces a reload:
  ```powershell
  taskkill /f /im explorer.exe
  start explorer.exe
  ```
  As a reliable workaround either way: run tests from a plain PowerShell 7
  window opened directly (not through an IDE's integrated terminal) rather
  than debugging environment inheritance further.

- **macOS**: this specific problem is much less common, because opening a
  new Terminal/iTerm window normally spawns a brand-new shell process that
  re-reads your shell's profile (`~/.zprofile`, `~/.zshrc`, etc.) from
  scratch — so a fresh terminal window is usually enough after installing
  something with Homebrew. If `diff3` still isn't found after
  `brew install diffutils`, check that Homebrew's own path is on PATH
  (Apple Silicon installs to `/opt/homebrew/bin`, Intel Macs to
  `/usr/local/bin`) by running:
  ```bash
  eval "$(brew shellenv)"
  which diff3
  ```
  If that resolves it, add the `brew shellenv` line to your `~/.zprofile`
  so it's picked up automatically in future sessions. The same *IDE
  integrated terminal caching an old environment* issue described above for
  Windows can still happen on macOS too (VS Code, for example, behaves the
  same way regardless of OS) — if a plain Terminal.app window finds
  `diff3` but your IDE's terminal doesn't, fully quit and reopen the IDE
  rather than just the terminal panel/tab.

---

## Running tests

Install this component with its dev dependencies (currently just `pytest`):

```powershell
pip install -e ".[dev]"
```

Then run either test suite:

```powershell
python -m unittest discover -s tests -v
# or, if using pytest:
pytest tests/ -v
```

---

## Repo layout and test workflow

This is one component of the [LydOS](../README.md) monorepo. Source code and
all tests (Python + PowerShell) live in this folder and are tracked by git
as normal:

```
LydOS/                           <- monorepo root
  ugit/                          <- this folder, tracked by git
    ugit/                        <- ugit source
    tests/
      test_base.py               <- Python unittest suite
      test_cli.py
      test_data.py
      test_diff.py
      test_remote.py
      powershell/                <- CLI-level .ps1 test scripts
        00-run-all.ps1
        ...
    setup.py
    run-ps1-tests.ps1
    ugit-next.md
    README.md                    <- this file
  http/                          <- other LydOS components
  database/
  cache/
  containers/
  distributed/
```

The PowerShell CLI test scripts are never *run* from inside this repo,
though — they're run from a separate, untracked sandbox directory, so a
buggy `ugit checkout`/`add`/etc. can never touch this source tree (see
commit/PR history if you're ever curious why this rule exists — short
version: it happened once, it's not happening again).

```
ugit/                            <- this folder, tracked by git
  ugit/
  tests/
    powershell/
      00-run-all.ps1
      ...

ugit-sandbox/                    <- NOT tracked by git, purely local scratch
  ugit-scripts/                  <- scripts get copied here before running
    (copies of the .ps1 files, plus disposable test-*/ output dirs)
```

### One-time setup

Move the PowerShell scripts into this repo alongside the Python tests
(adjust the sandbox path to wherever you keep it):

```powershell
cd /Users/lydiakoleosho/l_git/ugit
mkdir tests/powershell
Copy-Item /path/to/ugit-sandbox/ugit-scripts/*.ps1 tests/powershell/
git add tests/powershell/
git commit -m "Add PowerShell CLI test scripts covering all ugit commands"
git push
```

### Running the PowerShell tests day-to-day

Never run the `.ps1` scripts directly from `tests/powershell/` inside this
repo. Instead, copy them out to the sandbox and run them from there:

```powershell
Copy-Item /Users/lydiakoleosho/l_git/ugit/tests/powershell/*.ps1 /path/to/ugit-sandbox/ugit-scripts/ -Force
cd /path/to/ugit-sandbox/ugit-scripts
./00-run-all.ps1
```

Or use `run-ps1-tests.ps1` (in this folder's root) to do the copy + run in
one step.

When editing the PowerShell tests, use forward slashes in file paths passed
to `ugit` and PowerShell cmdlets. Only use the native separator when
comparing against JSON index keys, because those keys come from Python's
stored path format on that OS.

### `.gitignore` safety net

In case the PowerShell scripts are ever accidentally run from inside this
repo, make sure their throwaway output can never be committed by mistake:

```
test-*/
.ugit/
```