# Daily Git Commit

Automatically commits to GitHub once per day through **December 30, 2030**. Written in **Python**, runs in the cloud via **GitHub Actions**, with an optional **local macOS scheduler** as backup.

## How it works

1. A GitHub Action runs every day at **12:00 UTC**.
2. Python appends a timestamped line to `logs/activity.log`.
3. It creates a commit and pushes to your repository.

You can also trigger a commit manually from **Actions** → **Daily Commit** → **Run workflow**.

## Quick start

```bash
cd daily-git-commit
python3 -m daily_commit setup   # configure git remote and push
python3 -m daily_commit run       # test a commit immediately
```

Requires **Python 3.10+** and **git**. No pip packages needed — stdlib only.

## Setup (manual)

### 1. Create a GitHub repository

Create a new **empty** repo on GitHub (e.g. `daily-git-commit`). Do not add a README or license.

### 2. Push this project

```bash
git remote add origin git@github.com:YOUR_USERNAME/daily-git-commit.git
git add .
git commit -m "chore: initial setup for daily commits"
git push -u origin main
```

### 3. Enable GitHub Actions

Actions are enabled by default. After the first push, open **Actions** in your repo and confirm the **Daily Commit** workflow appears.

### 4. Test it

```bash
python3 -m daily_commit run
```

Or go to **Actions** → **Daily Commit** → **Run workflow**.

## Commands

| Command | Description |
|---------|-------------|
| `python3 -m daily_commit run` | Commit and push |
| `python3 -m daily_commit commit` | Commit only (no push) |
| `python3 -m daily_commit setup` | Interactive first-time setup |
| `python3 -m daily_commit install-local` | macOS daily scheduler |
| `python3 -m daily_commit ci` | Used by GitHub Actions |

## Optional: local macOS scheduler

```bash
python3 -m daily_commit install-local
```

Installs a `launchd` job that runs the Python app daily at your chosen time.

## Customize

| What | Where |
|------|-------|
| Commit time (UTC) | `.github/workflows/daily-commit.yml` → `cron` field |
| Schedule end date | `daily_commit/commit.py` → `SCHEDULE_END_DATE` |
| Commit message | `daily_commit/commit.py` |
| What gets updated | `daily_commit/commit.py` → change `LOG_FILE` |
| Local run time | `python3 -m daily_commit install-local` |

[Cron syntax reference](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

## Notes

- Scheduled workflows may be delayed by a few minutes during high GitHub load.
- Free GitHub accounts require repo activity in the last 60 days for scheduled workflows to keep running.
- The workflow uses the built-in `GITHUB_TOKEN` — no personal access token needed.