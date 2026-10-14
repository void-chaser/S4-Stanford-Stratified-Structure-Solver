#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# check_registries_r8m1a4audit2.sh -- check every line of registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT2.txt with sha256sum -c,
# and compare each registry copy byte for byte with its evidence source where a source name is known.  New file.
# Writes the report into $EV/tmp.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/check_registries_r8m1a4audit2.sh
set -u
MAN="$REPO/checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT2.txt"
test -f "$MAN" || { echo "check_registries: missing $MAN" >&2; exit 2; }
TOTAL=$(grep -c . "$MAN")
CHECK="$EV/tmp/registries_check_r8m1a4audit2.txt"
(cd "$REPO" && sha256sum -c "$MAN") > "$CHECK" 2>&1
OK=$(grep -c ': OK$' "$CHECK")
echo "registries_manifest lines=$TOTAL ok=$OK"
test "$OK" = "$TOTAL" || { echo "check_registries: NOT ALL OK" >&2; exit 3; }
exit 0
