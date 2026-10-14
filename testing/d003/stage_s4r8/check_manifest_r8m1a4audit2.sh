#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# check_manifest_r8m1a4audit2.sh -- check every line of SHA256SUMS_M1a4AUDIT2.txt with sha256sum -c and count the results.
# New file.  Writes the count to $EV/tmp (round evidence only).  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/check_manifest_r8m1a4audit2.sh
set -u
MAN="$EV/SHA256SUMS_M1a4AUDIT2.txt"
test -f "$MAN" || { echo "check_manifest: missing $MAN" >&2; exit 2; }
TOTAL=$(grep -c . "$MAN")
CHECK="$EV/tmp/manifest_check_r8m1a4audit2.txt"
(cd "$REPO" && sha256sum -c "$MAN") > "$CHECK" 2>&1
OK=$(grep -c ': OK$' "$CHECK")
BAD=$(grep -vc ': OK$' "$CHECK")
echo "manifest lines=$TOTAL ok=$OK not_ok_lines=$BAD"
test "$OK" = "$TOTAL" || { echo "check_manifest: NOT ALL OK" >&2; exit 3; }
exit 0
