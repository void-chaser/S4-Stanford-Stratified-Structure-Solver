#!/bin/bash
# verify-manifest.sh <manifest> [tee-log]
# Verifies a manifest and RETURNS sha256sum's real exit status.
#
# The optional tee-log receives a copy of the verification output.  The caller
# is responsible for keeping that log out of the manifest being verified, or
# for appending the manifest's own hash afterwards; run-all.sh does the latter.
set -u
M="$1"
LOG="${2:-}"
[ -n "$M" ] || { echo "usage: verify-manifest.sh <manifest> [tee-log]" >&2; exit 2; }
[ -s "$M" ] || { echo "manifest missing or empty: $M" >&2; exit 2; }

if [ -z "$LOG" ]; then
  sha256sum -c "$M"
  rc=$?
  echo "manifest=$M entries=$(grep -c . "$M") verify_rc=$rc"
  exit $rc
fi

tmp=$(mktemp) || exit 1
sha256sum -c "$M" > "$tmp" 2>&1
rc=$?
{
  cat "$tmp"
  echo "manifest=$M entries=$(grep -c . "$M") verify_rc=$rc"
} > "$LOG"
cat "$tmp"
rm -f "$tmp"
exit $rc
