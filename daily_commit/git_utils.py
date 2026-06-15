from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise GitError(stderr or f"git {' '.join(args)} failed")
    return result


def is_git_repo(root: Path) -> bool:
    result = run_git("rev-parse", "--is-inside-work-tree", cwd=root, check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def has_upstream(root: Path) -> bool:
    result = run_git("rev-parse", "--abbrev-ref", "@{u}", cwd=root, check=False)
    return result.returncode == 0


def remote_url(root: Path, name: str = "origin") -> str | None:
    result = run_git("remote", "get-url", name, cwd=root, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()