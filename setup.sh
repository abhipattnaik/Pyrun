#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=== Daily Git Commit — Setup ==="
echo

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is not installed."
  exit 1
fi

if [[ ! -d .git ]]; then
  git init -b main
  echo "Initialized git repository."
fi

chmod +x commit.sh run-now.sh install-local.sh

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote already configured: $(git remote get-url origin)"
else
  read -r -p "GitHub username: " github_user
  read -r -p "Repository name [daily-git-commit]: " repo_name
  repo_name="${repo_name:-daily-git-commit}"

  echo
  echo "Choose remote URL type:"
  echo "  1) SSH   (git@github.com:USER/REPO.git)"
  echo "  2) HTTPS (https://github.com/USER/REPO.git)"
  read -r -p "Choice [1]: " url_choice
  url_choice="${url_choice:-1}"

  if [[ "$url_choice" == "2" ]]; then
    remote_url="https://github.com/${github_user}/${repo_name}.git"
  else
    remote_url="git@github.com:${github_user}/${repo_name}.git"
  fi

  git remote add origin "$remote_url"
  echo "Added remote: $remote_url"
  echo
  echo "Create an empty repo at: https://github.com/new"
  echo "Name it: $repo_name (do not add README/license)"
fi

if ! git rev-parse HEAD >/dev/null 2>&1; then
  git add .
  git commit -m "chore: initial setup for daily commits"
fi

read -r -p "Push to GitHub now? [Y/n]: " push_now
push_now="${push_now:-Y}"

if [[ "$push_now" =~ ^[Yy]$ ]]; then
  git push -u origin main
  echo "Pushed to GitHub."
fi

echo
echo "Setup complete."
echo
echo "Next steps:"
echo "  1. GitHub Actions runs daily at 12:00 UTC (see .github/workflows/daily-commit.yml)"
echo "  2. Test now: ./run-now.sh"
echo "  3. Optional local scheduler: ./install-local.sh"
echo "  4. Manual trigger in GitHub: Actions → Daily Commit → Run workflow"