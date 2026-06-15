#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_LABEL="com.dailygitcommit.scheduler"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

echo "=== Install local daily scheduler (macOS launchd) ==="
echo

read -r -p "Hour to run daily (0-23) [9]: " hour
hour="${hour:-9}"
read -r -p "Minute [0]: " minute
minute="${minute:-0}"

if ! [[ "$hour" =~ ^[0-9]+$ && "$minute" =~ ^[0-9]+$ && "$hour" -le 23 && "$minute" -le 59 ]]; then
  echo "Error: invalid time."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${ROOT_DIR}/run-now.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>${hour}</integer>
    <key>Minute</key>
    <integer>${minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${ROOT_DIR}/logs/scheduler.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT_DIR}/logs/scheduler.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${PLIST_LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/${PLIST_LABEL}"

echo
echo "Installed. Runs daily at ${hour}:$(printf '%02d' "$minute") local time."
echo "Logs: ${ROOT_DIR}/logs/scheduler.log"
echo "Uninstall: launchctl bootout gui/\$(id -u)/${PLIST_LABEL} && rm ${PLIST_PATH}"