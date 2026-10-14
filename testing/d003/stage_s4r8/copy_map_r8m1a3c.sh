REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_map_r8m1a3c.sh -- P05-S4 R8 M1a CONT2c section 5.2: copy map_f2_f3_r8m1a3.py to map_f2_f3_r8m1a3c.py (the original is not modified).  New file.
# The copy is byte-identical to the original; the six classes of change of brief 5.2 are then applied with the edit tool.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/copy_map_r8m1a3c.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_map_r8m1a3c: first argument must be p05-s4r8" >&2; exit 2; }
SRC=testing/d003/stage_s4r8/map_f2_f3_r8m1a3.py
DST=testing/d003/stage_s4r8/map_f2_f3_r8m1a3c.py
test -f "$SRC" || { echo "copy_map_r8m1a3c: REFUSED: source missing" >&2; exit 2; }
test ! -e "$DST" || { echo "copy_map_r8m1a3c: REFUSED: exists (U17): $DST" >&2; exit 2; }
cp "$SRC" "$DST" || { echo "copy_map_r8m1a3c: COPY FAIL" >&2; exit 2; }
cmp -s "$SRC" "$DST" || { echo "copy_map_r8m1a3c: CMP FAIL" >&2; exit 2; }
echo "copy_map_r8m1a3c: copied and cmp OK -> $DST"
exit 0
