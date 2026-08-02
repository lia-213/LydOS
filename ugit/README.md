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