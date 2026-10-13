#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# reuse_f2_drivers_r8.sh -- P05-S4 R8 M0 U126: check the F2 plain drivers reused from R7 (new file; no relink).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/reuse_f2_drivers_r8.sh p05-s4r8
# For r6bstate-F2-plain and tri-F2-plain: the driver file of p05-s4r7/drivers_r7/ must exist, and its sha256 must equal the
# value recorded in p05-s4r7/DRIVERS_R7.tsv (read only).  A driver without a record is written as FIRST_RECORD (E8).
# Output: $EV/DRIVERS_R8_F2_REUSED.tsv (new file): name, tree, mode, recorded driver sha256, observed sha256, status.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "reuse_f2_drivers_r8: first argument must be p05-s4r8" >&2; exit 2; }
R7="$REPO/checkpoints/p05/evidence/p05-s4r7"
REC="$R7/DRIVERS_R7.tsv"
test -f "$REC" || { echo "reuse_f2_drivers_r8: REFUSED: $REC missing" >&2; exit 2; }
test ! -e "$EV/DRIVERS_R8_F2_REUSED.tsv" || { echo "reuse_f2_drivers_r8: REFUSED exists" >&2; exit 2; }
for n in r6bstate tri; do
    test -f "$R7/drivers_r7/$n-F2-plain/driver" || { echo "reuse_f2_drivers_r8: REFUSED: driver missing: $n-F2-plain" >&2; exit 2; }
done
OUT="$EV/DRIVERS_R8_F2_REUSED.tsv"
printf 'driver\ttree\tmode\trecorded_driver_sha256\tobserved_driver_sha256\tstatus\tpath\n' > "$OUT"
for n in r6bstate tri; do
    P="$R7/drivers_r7/$n-F2-plain/driver"
    OBS=$(sha256sum "$P" 2>&1 | cut -d' ' -f1)
    if [ "$n" = r6bstate ]; then
        REC_SHA=$(awk -F '\t' '$1 == "r6bstate" && $2 == "F2" && $3 == "plain" { print $5 }' "$REC")
    else
        REC_SHA=$(awk -F '\t' '$1 == "tri" && $2 == "F2" && $3 == "plain" { print $5 }' "$REC")
    fi
    if [ -z "$REC_SHA" ]; then ST=FIRST_RECORD; elif [ "$REC_SHA" = "$OBS" ]; then ST=SAME; else ST=DIFFERENT; fi
    printf '%s\tF2\tplain\t%s\t%s\t%s\t%s\n' "$n-F2-plain" "${REC_SHA:--}" "$OBS" "$ST" "$P" >> "$OUT"
done
echo "reuse_f2_drivers_r8: done -> $OUT"
exit 0
