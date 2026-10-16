#!/bin/sh
# First-boot auth setup, then start Next.js. Both steps are idempotent.
set -e
cd /app/frontend

echo "[freedom-frontend] running Better Auth migrations"
i=0
until auth migrate --config src/lib/auth.ts --yes; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then echo "[freedom-frontend] migration failed"; exit 1; fi
  echo "[freedom-frontend] database not ready, retrying ($i/30)"; sleep 2
done

echo "[freedom-frontend] seeding admin user (admin/admin123)"
tsx scripts/seed-admin.ts

exec npm run start -- -p "${PORT:-3000}"
