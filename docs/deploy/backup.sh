#!/bin/sh
# Daily backup of the guestbook database and uploaded images.
#
# Install on the Pi:
#   sudo cp docs/deploy/backup.sh /usr/local/bin/gastbok-backup
#   sudo chmod +x /usr/local/bin/gastbok-backup
#   crontab -e   ->   15 3 * * * /usr/local/bin/gastbok-backup
#
# BACKUP_DIR should point at storage other than the SD card
# (for example a USB stick), otherwise a failing card takes the
# backups with it.

set -eu

APP_DIR="${APP_DIR:-/srv/gastbok/current}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/gastbok}"
KEEP_DAYS="${KEEP_DAYS:-30}"
STAMP="$(date +%Y-%m-%d)"

mkdir -p "$BACKUP_DIR"

# SQLite's online backup API gives a consistent copy even while the
# app is running, unlike a plain file copy.
"$APP_DIR/.venv/bin/python" - "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$STAMP.sqlite3" <<'PY'
import sqlite3
import sys

source = sqlite3.connect(sys.argv[1])
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
target.close()
source.close()
PY

tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" -C "$APP_DIR" media

find "$BACKUP_DIR" -type f -mtime +"$KEEP_DAYS" -delete

echo "Backup written to $BACKUP_DIR ($STAMP)"
