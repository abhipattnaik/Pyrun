from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path

from daily_commit.git_utils import run_git
from daily_commit.python_version import PythonVersionSync, sync_python_version

LOG_FILE = Path("logs/activity.log")
MARKER = "automated daily commit"
SCHEDULE_END_DATE = date(2030, 12, 30)


def is_within_schedule(today: date | None = None) -> bool:
    today = today or datetime.now(timezone.utc).date()
    return today <= SCHEDULE_END_DATE


def schedule_status(today: date | None = None) -> str:
    today = today or datetime.now(timezone.utc).date()
    if is_within_schedule(today):
        return f"Active until {SCHEDULE_END_DATE.isoformat()} (inclusive)."
    return f"Schedule ended on {SCHEDULE_END_DATE.isoformat()}. No more commits."


def next_commit_count(log_file: Path) -> int:
    if not log_file.exists():
        return 1
    count = sum(1 for line in log_file.read_text(encoding="utf-8").splitlines() if MARKER in line)
    return count + 1


def _commit_message(commit_count: int, timestamp: str, version_sync: PythonVersionSync) -> str:
    message = f"chore: daily commit #{commit_count} on {timestamp}"
    if version_sync.updated:
        message += (
            f" (Python {version_sync.current_minor} -> {version_sync.latest_minor})"
        )
    return message


def create_daily_commit(root: Path) -> tuple[bool, int, str]:
    if not is_within_schedule():
        print(schedule_status())
        return False, 0, ""

    version_sync = sync_python_version(root)

    log_file = root / LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit_count = next_commit_count(log_file)

    log_lines = []
    if log_file.exists():
        existing = log_file.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"
        log_lines.append(existing)

    log_lines.append(f"{timestamp} — {MARKER} #{commit_count}\n")
    if version_sync.updated:
        log_lines.append(
            f"{timestamp} — python version updated to "
            f"{version_sync.latest_minor} ({version_sync.latest_full})\n"
        )
    log_file.write_text("".join(log_lines), encoding="utf-8")

    files_to_stage = {LOG_FILE, *version_sync.changed_files}
    for path in files_to_stage:
        run_git("add", str(path), cwd=root)

    diff = run_git("diff", "--cached", "--quiet", cwd=root, check=False)
    if diff.returncode == 0:
        print("No changes to commit.")
        return False, commit_count, timestamp

    message = _commit_message(commit_count, timestamp, version_sync)
    author_name = os.environ.get("GIT_AUTHOR_NAME", "").strip()
    author_email = os.environ.get("GIT_AUTHOR_EMAIL", "").strip()
    if author_name and author_email:
        author = f"{author_name} <{author_email}>"
        run_git("commit", "--author", author, "-m", message, cwd=root)
    else:
        run_git("commit", "-m", message, cwd=root)
    return True, commit_count, timestamp


def run_ci(root: Path, branch: str = "main") -> None:
    if not is_within_schedule():
        print(schedule_status())
        return

    run_git("fetch", "origin", branch, cwd=root)
    run_git("checkout", branch, cwd=root)
    run_git("pull", "--rebase", "origin", branch, cwd=root)

    created, commit_count, timestamp = create_daily_commit(root)
    if created:
        run_git("push", "origin", branch, cwd=root)
        print(f"Pushed daily commit #{commit_count} ({timestamp}).")
    else:
        print("Nothing new to push.")