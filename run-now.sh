#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not a git repository. Run ./setup.sh first."
  exit 1
fi

./commit.sh

if git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
  git push
  echo "Pushed to GitHub."
else
  echo "Committed locally. Add a remote with ./setup.sh to push to GitHub."
fi