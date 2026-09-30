#!/bin/sh
# Update the guestbook on the Raspberry Pi to the latest main.
#
# Run as the service user (karlal) on the Pi:
#   sh /srv/gastbok/current/docs/deploy/update.sh

set -eu

APP_DIR="${APP_DIR:-/srv/gastbok/current}"
ENV_FILE="${ENV_FILE:-/etc/gastbok/gastbok.env}"

cd "$APP_DIR"

# Back up before touching the database, if the backup script is installed.
if command -v gastbok-backup >/dev/null 2>&1; then
    gastbok-backup
fi

git pull --ff-only

.venv/bin/pip install --quiet -r requirements.txt

set -a
. "$ENV_FILE"
set +a

.venv/bin/python manage.py check --deploy --fail-level ERROR
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput

sudo systemctl restart gastbok
sleep 2
systemctl is-active gastbok

echo "Updated to $(git log -1 --oneline)"
