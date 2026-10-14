#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# tmp_snapshot_r8m1a3.sh -- read-only snapshot of the top level of /tmp (AGENTS.md section 3): entry count and sha256 of the listing.
# Writes one new file $EV/TMP_SNAPSHOT_<LABEL>_R8_M1a3.txt (refused if it exists, U17).  Reads /tmp only; writes nothing to /tmp.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/tmp_snapshot_r8m1a3.sh p05-s4r8 START
# Output lines: utc, count, sha256 (the listing is "ls -A /tmp" sorted by LC_ALL=C).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "tmp_snapshot_r8m1a3: first argument must be p05-s4r8" >&2; exit 2; }
LABEL=${2:-}
case "$LABEL" in
    START|END) ;;
    *) echo "tmp_snapshot_r8m1a3: REFUSED: label must be START or END" >&2; exit 2 ;;
esac
OUT="$EV/TMP_SNAPSHOT_${LABEL}_R8_M1a3.txt"
test ! -e "$OUT" || { echo "tmp_snapshot_r8m1a3: REFUSED: exists (U17): $OUT" >&2; exit 2; }
LIST="$EV/tmp/tmp_listing_${LABEL}_r8m1a3.txt"
test ! -e "$LIST" || { echo "tmp_snapshot_r8m1a3: REFUSED: exists (U17): $LIST" >&2; exit 2; }
ls -A /tmp | LC_ALL=C sort > "$LIST"
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'tmp_entries=%s\n' "$(wc -l < "$LIST" | tr -d ' ')"
    printf 'tmp_listing_sha256=%s\n' "$(sha256sum "$LIST" | cut -d' ' -f1)"
} > "$OUT"
cat "$OUT"
exit 0
