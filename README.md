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

## Running tests

pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
### or, if using pytest:
pytest tests/ -v

## Repo layout and test workflow

Source code and all tests (Python + PowerShell) live in this repo (`l_git`)
and are tracked by real git as normal. The PowerShell CLI test scripts are
never *run* from inside this repo, though -- they're run from a separate,
untracked sandbox directory, so a buggy `ugit checkout`/`add`/etc. can never
touch this source tree (see earlier incident history if you ever wonder why
this rule exists).

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
do the copy + run in one step -- see below.

### Running the Python tests

```powershell
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
# or, if using pytest:
pytest tests/ -v
```

### `.gitignore` safety net

In case the PowerShell scripts are ever accidentally run from inside this
repo, make sure their throwaway output can never be committed by mistake:

```
test-*/
.ugit/
```