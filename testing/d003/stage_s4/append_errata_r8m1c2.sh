#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r8m1c2.sh -- P05-S4 R8 M1c2 ERRATA_8.txt append (prefix-checked, append only).
# Appends E8-79 (a)-(e) and E8-80.
# Block built by testing/d003/stage_s4/build_errata_r8m1c2.py; (e) numbers come from R7_F2_FACT_DIST_R8_M1c2.tsv.
# Refuses unless the living file still matches the recorded base (62127 bytes, sha256 ee7c5e2d...).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- sh testing/d003/stage_s4/append_errata_r8m1c2.sh
set -u
refuse() { echo "append_errata_r8m1c2: REFUSED: $1" >&2; exit 2; }
ERR="$REPO/checkpoints/p05/registries/s4r8/ERRATA_8.txt"
BRIEF1="$REPO/checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md"
DIST="$EV/R7_F2_FACT_DIST_R8_M1c2_R2.tsv"
BLOCK="$EV/tmp/ERRATA_APPEND_R8_M1c2.txt"
BASE_BYTES=62127
BASE_SHA=ee7c5e2def47a45b9602e8ff90687414703e7e955015ca62d0eb222b894dfdba
test -f "$ERR" || refuse "ERRATA_8.txt missing"
test -f "$BRIEF1" || refuse "M1c1 brief missing"
test -f "$DIST" || refuse "R7 F2 fact distribution table missing (run count_r7_f2_facts_r8m1c2_R2.py first)"
[ "$(wc -c < "$ERR" | tr -d ' ')" = "$BASE_BYTES" ] || refuse "ERRATA_8.txt is not at the recorded base size before append"
[ "$(sha256sum "$ERR" | cut -d' ' -f1)" = "$BASE_SHA" ] || refuse "ERRATA_8.txt base sha256 differs before append"
[ "$(grep -c '^E8-79' "$ERR")" = 0 ] || refuse "E8-79 already present; no duplicate append"
python3 -I -B "$REPO/testing/d003/stage_s4/build_errata_r8m1c2.py" "$BRIEF1" "$DIST" "$BLOCK" || refuse "builder failed"
test -f "$BLOCK" || refuse "append block not built"
cat "$BLOCK" >> "$ERR" || refuse "append failed"
echo "append_errata_r8m1c2: appended E8-79 and E8-80 to ERRATA_8.txt"
exit 0
