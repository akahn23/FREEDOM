#!/usr/bin/env bash
# Frontend static analysis: install (npm ci, falling back to npm@11 install),
# then `tsc --noEmit` and `next lint` / `eslint .`.
#
# Env:
#   LOG_DIR=<dir>     where logs are written (default: ${TMPDIR:-/tmp}/freedom-static-check)
#   SKIP_INSTALL=1    reuse the existing node_modules
#   STRICT_NPM_CI=1   treat an `npm ci` failure as a failure even if the fallback works
#
# Exits non-zero if the install (including the fallback), tsc, or lint fails.
set -uo pipefail

cd "$(dirname "$0")/.."
LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/freedom-static-check}"
mkdir -p "$LOG_DIR"

echo "node $(node -v), npm $(npm -v)"
echo "logs: $LOG_DIR"

declare -A STATUS
FAIL=0

run() {
  local name="$1"; shift
  echo "==> $name: $*"
  "$@" >"$LOG_DIR/$name.log" 2>&1
  local rc=$?
  STATUS[$name]=$rc
  echo "    exit $rc"
  return $rc
}

restore_manifests() {
  if command -v git >/dev/null 2>&1 && ! git diff --quiet -- package.json package-lock.json 2>/dev/null; then
    echo "    restoring package.json/package-lock.json changed by the fallback install"
    git checkout -- package.json package-lock.json
  fi
}

if [ "${SKIP_INSTALL:-0}" != "1" ]; then
  if ! run npm-ci npm ci; then
    grep -E "Missing:|Invalid:|edgesOut" "$LOG_DIR/npm-ci.log" | sed 's/^/    /'
    [ "${STRICT_NPM_CI:-0}" = "1" ] && FAIL=1
    run npm-install-fallback npx -y npm@11 install --ignore-scripts || FAIL=1
    restore_manifests
    if [ "${STATUS[npm-install-fallback]}" != "0" ]; then
      echo "install failed; see $LOG_DIR/npm-install-fallback.log"
      exit 1
    fi
  fi
fi

run tsc npx tsc --noEmit || FAIL=1
run next-lint npm run lint || FAIL=1
run eslint npx eslint . || FAIL=1
grep -E "[0-9]+ problems \(" "$LOG_DIR/eslint.log" | sed 's/^/    /'

echo "==> summary"
for k in npm-ci npm-install-fallback tsc next-lint eslint; do
  [ -n "${STATUS[$k]+x}" ] && printf '    %-22s exit %s\n' "$k" "${STATUS[$k]}"
done
exit $FAIL
