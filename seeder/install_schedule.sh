#!/bin/bash
# Installs (or removes with --uninstall) a macOS launchd job that runs seed.py
# Mon-Fri at 08:00, 12:00 and 16:00 local time.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.spooky.seed.plist"
if [ "$1" = "--uninstall" ]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"; echo "Schedule removed."; exit 0
fi
SLOTS=""
for d in 1 2 3 4 5; do for h in 8 12 16; do
  SLOTS+="    <dict><key>Weekday</key><integer>$d</integer><key>Hour</key><integer>$h</integer><key>Minute</key><integer>0</integer></dict>
"
done; done
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.spooky.seed</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>-I</string><string>$DIR/seed.py</string>
  </array>
  <key>StartCalendarInterval</key><array>
$SLOTS  </array>
  <key>StandardOutPath</key><string>$DIR/seed.log</string>
  <key>StandardErrorPath</key><string>$DIR/seed.log</string>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Schedule installed: Mon-Fri 08:00, 12:00, 16:00 (local time). Log: $DIR/seed.log"
