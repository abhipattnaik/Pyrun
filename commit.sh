#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="logs/activity.log"
mkdir -p logs

timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "$timestamp — automated daily commit" >> "$LOG_FILE"

git add "$LOG_FILE"
git commit -m "chore: daily commit on $timestamp"
