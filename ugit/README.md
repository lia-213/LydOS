## Prerequisites

- Python 3.x
- `diff3` (GNU diffutils) — required for `ugit merge` on diverging branches.
  - **Windows**: install via `choco install diffutils`, or use the
    `diff3.exe` bundled with Git for Windows (`<git-install-dir>\usr\bin`)
    and ensure it's on your PATH.
  - **macOS**: `brew install diffutils`
  - **Linux**: usually preinstalled; otherwise `apt install diffutils` /
    equivalent for your distro.