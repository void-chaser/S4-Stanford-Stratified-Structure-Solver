#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r8m1c2.sh -- P05-S4 R8 M1c2 RULINGS.tsv append (prefix-checked, append only).
# Appends U209-U217 to checkpoints/p05/registries/RULINGS.tsv.
# Block text built by testing/d003/stage_s4/build_rulings_r8m1c2.py (U209-U214 verbatim from M1c1 brief section 3.1).
# Refuses to run unless the living file still matches the recorded base (79849 bytes, sha256 d7262cf7...).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- sh testing/d003/stage_s4/append_rulings_r8m1c2.sh
set -u
refuse() { echo "append_rulings_r8m1c2: REFUSED: $1" >&2; exit 2; }
RUL="$REPO/checkpoints/p05/registries/RULINGS.tsv"
BRIEF1="$REPO/checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c1.md"
BLOCK="$EV/tmp/RULINGS_APPEND_R8_M1c2.tsv"
BASE_BYTES=79849
BASE_SHA=d7262cf74df0eb13fa4f91b44f5a8e7342936dea524c439c01f308255216bdc7
test -f "$RUL" || refuse "RULINGS.tsv missing"
test -f "$BRIEF1" || refuse "M1c1 brief missing"
[ "$(wc -c < "$RUL" | tr -d ' ')" = "$BASE_BYTES" ] || refuse "RULINGS.tsv is not at the recorded base size before append"
[ "$(sha256sum "$RUL" | cut -d' ' -f1)" = "$BASE_SHA" ] || refuse "RULINGS.tsv base sha256 differs before append"
[ "$(grep -c '^U209	' "$RUL")" = 0 ] || refuse "U209 already present; no duplicate append"
python3 -I -B "$REPO/testing/d003/stage_s4/build_rulings_r8m1c2.py" "$BRIEF1" "$BLOCK" || refuse "builder failed"
test -f "$BLOCK" || refuse "append block not built"
[ "$(wc -l < "$BLOCK" | tr -d ' ')" = 9 ] || refuse "append block row count is not 9"
cat "$BLOCK" >> "$RUL" || refuse "append failed"
echo "append_rulings_r8m1c2: appended $(wc -l < "$BLOCK" | tr -d ' ') rows (U209-U217) to RULINGS.tsv"
exit 0
