# l_git (ugit)

A from-scratch reimplementation of git, built to actually understand what
git is doing under the hood rather than just using it.

This project follows [Nikita Leshenko's *"Write yourself a Git!"*](https://www.leshenko.net/p/ugit/)
tutorial — huge thanks to Nikita for writing a walkthrough that actually
explains git's internals (objects, trees, refs, the index) clearly enough
to build something real from, rather than just skimming the surface. If
you're curious how git actually works under the hood, go read it.

This repo picks up where the tutorial leaves off: fixing real bugs found
along the way, adding a full test suite, and pushing the implementation
further than the tutorial itself goes.

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
- **Graph visualisation** — `ugit k`, dumping the commit/ref graph as DOT.
  The code attempts to render with Graphviz's `dot` (and on macOS opens the
  generated PNG with Preview), but the local rendering path is platform-
  specific and may be broken; when Graphviz rendering isn't available the
  DOT is printed and a quickchart.io web fallback is opened instead.

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
 - **`ugit k` local Graphviz rendering is platform-specific / may be broken** —
   the CLI's local rendering path attempts to call `dot` and open the
   generated PNG with macOS' Preview; that path can fail on non-macOS
   systems or due to a bug in the current invocation. In those cases the
   DOT will be printed and a quickchart.io web fallback is used.

---

## Where I'm hoping to take this next

A few directions I want to push this in beyond where the tutorial (and the
current state of this repo) leaves off:

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

---

## Running tests

```powershell
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
# or, if using pytest:
pytest tests/ -v
```

---

## Repo layout and test workflow

Source code and all tests (Python + PowerShell) live in this repo (`l_git`)
and are tracked by real git as normal. The PowerShell CLI test scripts are
never *run* from inside this repo, though — they're run from a separate,
untracked sandbox directory, so a buggy `ugit checkout`/`add`/etc. can never
touch this source tree (see commit/PR history if you're ever curious why
this rule exists — short version: it happened once, it's not happening
again).

```
l_git/                          <- this repo, tracked by real git
  ugit/                         <- ugit source
  tests/
    test_base.py                <- Python unittest suite
    test_cli.py
    test_data.py
    test_diff.py
    test_remote.py
    powershell/                 <- CLI-level .ps1 test scripts
      00-run-all.ps1
      01-init.ps1
      ...

ugit-sandbox/                   <- NOT tracked by git, purely local scratch
  ugit-scripts/                 <- scripts get copied here before running
    (copies of the .ps1 files, plus disposable test-*/ output dirs)
```

### One-time setup

Move the PowerShell scripts into this repo alongside the Python tests:

```powershell
cd C:\Users\lydbo\l_git
mkdir tests\powershell
Copy-Item C:\Users\lydbo\ugit-sandbox\ugit-scripts\*.ps1 tests\powershell\
git add tests/powershell/
git commit -m "Add PowerShell CLI test scripts covering all ugit commands"
git push
```

### Running the PowerShell tests day-to-day

Never run the `.ps1` scripts directly from `tests\powershell\` inside this
repo. Instead, copy them out to the sandbox and run them from there:

```powershell
Copy-Item C:\Users\lydbo\l_git\tests\powershell\*.ps1 C:\Users\lydbo\ugit-sandbox\ugit-scripts\ -Force
cd C:\Users\lydbo\ugit-sandbox\ugit-scripts
.\00-run-all.ps1
```

Or use `run-ps1-tests.ps1` (in this repo's root, or wherever you keep it) to
do the copy + run in one step — see below.

### `.gitignore` safety net

In case the PowerShell scripts are ever accidentally run from inside this
repo, make sure their throwaway output can never be committed by mistake:

```
test-*/
.ugit/
```