# Daily Git Commit

Automatically commits to GitHub once per day. Runs in the cloud via **GitHub Actions** (no Mac required), with an optional **local macOS scheduler** as backup.

## How it works

1. A GitHub Action runs every day at **12:00 UTC**.
2. It appends a timestamped line to `logs/activity.log`.
3. It creates a commit and pushes to your repository.

You can also trigger a commit manually from **Actions** → **Daily Commit** → **Run workflow**.

## Quick start

```bash
cd daily-git-commit
./setup.sh      # configure git remote and push
./run-now.sh    # test a commit immediately
```

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
./run-now.sh
```

Or go to **Actions** → **Daily Commit** → **Run workflow**.

## Optional: local macOS scheduler

If you want commits to run from your Mac (e.g. when GitHub Actions is delayed):

```bash
./install-local.sh
```

This installs a `launchd` job that runs `./run-now.sh` daily at your chosen time.

## Customize

| What | Where |
|------|-------|
| Commit time (UTC) | `.github/workflows/daily-commit.yml` → `cron` field |
| Commit message | `commit.sh` |
| What gets updated | `commit.sh` → change `LOG_FILE` or add more files |
| Local run time | `./install-local.sh` |

[Cron syntax reference](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

## Notes

- Scheduled workflows may be delayed by a few minutes during high GitHub load.
- Free GitHub accounts require repo activity in the last 60 days for scheduled workflows to keep running.
- The workflow uses the built-in `GITHUB_TOKEN` — no personal access token needed.