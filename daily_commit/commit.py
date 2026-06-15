from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from daily_commit.git_utils import run_git

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


def create_daily_commit(root: Path) -> tuple[bool, int, str]:
    if not is_within_schedule():
        print(schedule_status())
        return False, 0, ""

    log_file = root / LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit_count = next_commit_count(log_file)

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} — {MARKER} #{commit_count}\n")

    run_git("add", str(LOG_FILE), cwd=root)

    diff = run_git("diff", "--cached", "--quiet", cwd=root, check=False)
    if diff.returncode == 0:
        print("No changes to commit.")
        return False, commit_count, timestamp

    message = f"chore: daily commit #{commit_count} on {timestamp}"
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