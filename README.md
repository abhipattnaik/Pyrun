# daily-git-commit

Automatically commits to GitHub once per day using a scheduled GitHub Actions workflow.

## How it works

1. A GitHub Action runs every day at **12:00 UTC**.
2. It appends a timestamped line to `logs/activity.log`.
3. It creates a commit and pushes it to your repository.

You can also trigger a commit manually from the **Actions** tab → **Daily Commit** → **Run workflow**.

## Setup

### 1. Create a GitHub repository

Create a new empty repo on GitHub (e.g. `daily-git-commit`).

### 2. Push this project

```bash
git remote add origin https://github.com/YOUR_USERNAME/daily-git-commit.git
git add .
git commit -m "chore: initial setup for daily commits"
git push -u origin main
```

If your default branch is `master`, replace `main` above.

### 3. Enable GitHub Actions

Actions are enabled by default on new repos. After the first push, open **Actions** in your repo and confirm the **Daily Commit** workflow appears.

### 4. (Optional) Run it now

Go to **Actions** → **Daily Commit** → **Run workflow** to test without waiting for the schedule.

## Customize

| What | Where |
|------|-------|
| Commit time (UTC) | `.github/workflows/daily-commit.yml` → `cron` field |
| Commit message | `commit.sh` |
| What gets updated | `commit.sh` → change `LOG_FILE` or add more files |

[Cron syntax reference](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

## Notes

- Scheduled workflows may be delayed by a few minutes during high GitHub load.
- Free GitHub accounts require the repo to have had activity in the last 60 days for scheduled workflows to keep running.
- The workflow uses the built-in `GITHUB_TOKEN` — no personal access token needed.
