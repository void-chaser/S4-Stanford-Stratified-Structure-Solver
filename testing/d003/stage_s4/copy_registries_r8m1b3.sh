#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r8m1b3.sh -- copy small result tables of R8 M1b3 into registries and verify sha256. New file.
set -u
DST="$REPO/checkpoints/p05/registries/s4r8/M1b/r8m1b3"
mkdir -p "$DST" || exit 2
for f in PREREG_SUPP_R8_M1b3.tsv PREREG_SUPP_RECORD_R8_M1b3.txt RESULTS_SUPP_R8_M1b3.tsv VERDICT_SUPP_R8_M1b3.tsv VERDICT_SUPP_R8_M1b3_AGG.tsv CROSSWALK_M1B1_SUPP_R8_M1b3.tsv EFFECTIVE_M1B_R8_M1b3.tsv ENV_LOGCHECK_M1C_R8_M1b3.tsv; do
    cp "$EV/$f" "$DST/$f" || exit 3
    a=$(sha256sum "$EV/$f" | cut -d' ' -f1)
    b=$(sha256sum "$DST/$f" | cut -d' ' -f1)
    [ "$a" = "$b" ] || { echo "SHA_MISMATCH $f" >&2; exit 4; }
done
for f in GATE_R8_M1b3_START.txt; do
    cp "$EV/$f" "$DST/$f" || exit 3
    a=$(sha256sum "$EV/$f" | cut -d' ' -f1)
    b=$(sha256sum "$DST/$f" | cut -d' ' -f1)
    [ "$a" = "$b" ] || { echo "SHA_MISMATCH $f" >&2; exit 4; }
done
echo "copied and verified"
