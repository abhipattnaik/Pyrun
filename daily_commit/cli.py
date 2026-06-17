from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from daily_commit.commit import create_daily_commit, run_ci
from daily_commit.git_utils import GitError, has_upstream, is_git_repo, remote_url, run_git

ROOT = Path(__file__).resolve().parent.parent


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    if not value and default is not None:
        return default
    return value


def cmd_commit(_: argparse.Namespace) -> int:
    try:
        create_daily_commit(ROOT)
    except GitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_run(_: argparse.Namespace) -> int:
    if not is_git_repo(ROOT):
        print("Error: not a git repository. Run `python -m daily_commit setup` first.", file=sys.stderr)
        return 1

    try:
        created, _, _ = create_daily_commit(ROOT)
        if not created:
            return 0

        if has_upstream(ROOT):
            branch = run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=ROOT).stdout.strip()
            run_git("pull", "--rebase", "origin", branch, cwd=ROOT, check=False)
            run_git("push", "origin", branch, cwd=ROOT)
            print("Pushed to GitHub.")
        else:
            print("Committed locally. Add a remote with `python -m daily_commit setup` to push.")
    except GitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_ci(args: argparse.Namespace) -> int:
    try:
        run_ci(ROOT, branch=args.branch)
    except GitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_setup(_: argparse.Namespace) -> int:
    print("=== Daily Git Commit — Setup ===\n")

    if not (ROOT / ".git").is_dir():
        subprocess.run(["git", "init", "-b", "main"], cwd=ROOT, check=True)
        print("Initialized git repository.")

    if remote_url(ROOT):
        print(f"Remote already configured: {remote_url(ROOT)}")
    else:
        github_user = _prompt("GitHub username")
        repo_name = _prompt("Repository name", "daily-git-commit")

        print("\nChoose remote URL type:")
        print("  1) SSH   (git@github.com:USER/REPO.git)")
        print("  2) HTTPS (https://github.com/USER/REPO.git)")
        url_choice = _prompt("Choice", "1")

        if url_choice == "2":
            remote = f"https://github.com/{github_user}/{repo_name}.git"
        else:
            remote = f"git@github.com:{github_user}/{repo_name}.git"

        run_git("remote", "add", "origin", remote, cwd=ROOT)
        print(f"Added remote: {remote}")
        print("\nCreate an empty repo at: https://github.com/new")
        print(f"Name it: {repo_name} (do not add README/license)")

    head = run_git("rev-parse", "HEAD", cwd=ROOT, check=False)
    if head.returncode != 0:
        run_git("add", ".", cwd=ROOT)
        run_git("commit", "-m", "chore: initial setup for daily commits", cwd=ROOT)

    push_now = _prompt("Push to GitHub now? [Y/n]", "Y")
    if push_now.lower() in {"", "y", "yes"}:
        try:
            run_git("push", "-u", "origin", "main", cwd=ROOT)
            print("Pushed to GitHub.")
        except GitError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    print("\nSetup complete.\n")
    print("Next steps:")
    print("  1. GitHub Actions runs 3x daily (08:00, 14:00, 20:00 IST)")
    print("  2. Test now: python -m daily_commit run")
    print("  3. Optional local scheduler: python -m daily_commit install-local")
    print("  4. Manual trigger: Actions → Daily Commit → Run workflow")
    return 0


def cmd_install_local(_: argparse.Namespace) -> int:
    print("=== Install local daily scheduler (macOS launchd) ===\n")

    hour = int(_prompt("Hour to run daily (0-23)", "9"))
    minute = int(_prompt("Minute", "0"))

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        print("Error: invalid time.", file=sys.stderr)
        return 1

    python_bin = sys.executable
    label = "com.dailygitcommit.scheduler"
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    plist_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_bin}</string>
    <string>-m</string>
    <string>daily_commit</string>
    <string>run</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{ROOT}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{hour}</integer>
    <key>Minute</key>
    <integer>{minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{ROOT / "logs" / "scheduler.log"}</string>
  <key>StandardErrorPath</key>
  <string>{ROOT / "logs" / "scheduler.log"}</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )

    uid = os.getuid()
    target = f"gui/{uid}/{label}"
    subprocess.run(["launchctl", "bootout", target], check=False)
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)], check=True)
    subprocess.run(["launchctl", "enable", target], check=True)

    print(f"\nInstalled. Runs daily at {hour}:{minute:02d} local time.")
    print(f"Logs: {ROOT / 'logs' / 'scheduler.log'}")
    print(f"Uninstall: launchctl bootout gui/{uid}/{label} && rm {plist_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automatically commit to GitHub three times per day.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("commit", help="Create today's commit locally")
    subparsers.add_parser("run", help="Create today's commit and push if configured")
    subparsers.add_parser("setup", help="Configure git remote and initial push")

    ci_parser = subparsers.add_parser("ci", help="GitHub Actions entrypoint")
    ci_parser.add_argument("--branch", default="main")

    subparsers.add_parser("install-local", help="Install macOS launchd daily scheduler")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "commit": cmd_commit,
        "run": cmd_run,
        "ci": cmd_ci,
        "setup": cmd_setup,
        "install-local": cmd_install_local,
    }
    return handlers[args.command](args)