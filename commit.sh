#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_FILE="logs/activity.log"
mkdir -p logs

timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
commit_count=0
if [[ -f "$LOG_FILE" ]]; then
  commit_count="$(grep -c "automated daily commit" "$LOG_FILE" 2>/dev/null || true)"
  commit_count="${commit_count:-0}"
fi
commit_count=$((commit_count + 1))
echo "$timestamp — automated daily commit #$commit_count" >> "$LOG_FILE"

git add "$LOG_FILE"

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "chore: daily commit #$commit_count on $timestamp"