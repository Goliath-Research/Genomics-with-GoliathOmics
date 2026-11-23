#!/usr/bin/env bash
# Start the GoliathApp portal (apps/platform-host) in dev mode against the lab database.
# Runs inside the `portal` Compose service after `seed` has checked out the pinned GoliathApp.
#
# Dev sign-in (GOLIATH_PLATFORM_HOST_DEV_LOGIN=1) is a local-lab convenience. GoliathApp refuses
# it in production, and this course never sets it anywhere else.
set -euo pipefail
APP="${SRC_DIR:-/lab-src}/GoliathApp"
[[ -f "$APP/package.json" ]] || { echo "GoliathApp checkout missing; run the seed service first" >&2; exit 1; }
for var in GOLIATH_PORTAL_PASSWORD GOLIATH_PLATFORM_HOST_DEV_LOGIN_SECRET; do
  [[ -n "${!var:-}" ]] || { echo "$var is empty; run 'python course_lab.py init' to write .env" >&2; exit 1; }
done
cd "$APP"
export NEXT_TELEMETRY_DISABLED=1
if [[ ! -d node_modules ]]; then
  npm ci --no-audit --no-fund
fi
npm run build --workspace @goliath/ui --workspace @goliath/client --workspace @goliath/platform-ui
cd apps/platform-host
exec npx next dev --hostname 0.0.0.0 --port 3400
