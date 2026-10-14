REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# sums_m1a3c_all.sh -- P05-S4 R8 M1a CONT2c section 6: write $EV/SHA256SUMS_M1a3c.txt for all new non-binary evidence of
# this round (segments A and B).  New file.  Refused if the list exists (U17).  The list is checked with sha256sum -c by the
# caller (check_sums_m1a3c_all.sh).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/sums_m1a3c_all.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "sums_m1a3c_all: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/SHA256SUMS_M1a3c.txt"
test ! -e "$OUT" || { echo "sums_m1a3c_all: REFUSED: exists (U17): $OUT" >&2; exit 2; }
cd "$EV" || { echo "sums_m1a3c_all: cannot enter evidence dir" >&2; exit 2; }
for f in GATE_R8_M1a3c_START.txt GATE_R8_M1a3c_ENDA.txt GATE_R8_M1a3c_STARTB.txt APPEND_R8_M1a3c.txt APPEND_R8_M1a3c_B.txt \
         COPY_M1A_R8_M1a3c_A.txt COPY_M1A_R8_M1a3c_B.txt CHECK_SUMS_M1A3C_B.txt FINAL_GIT_R8_M1a3c_A.txt \
         MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt EXPECT_LINEMAP_R8_M1a3c.txt LINEMAP_F2_F3_R8_M1a3c.tsv \
         PARSER_SELFCHECK_R8_M1a3c.tsv FUNC_BP_SYMBOLS_R8_M1a3c.tsv LINEMAP_CHECK_R8_M1a3c.txt LINEMAP_V3_V3C_DIFF_R8_M1a3c.txt \
         S4R7_RECHECK_GATE_R8_M1A3C_START.tsv S4R7_RECHECK_GATE_R8_M1A3C_ENDA.tsv S4R7_RECHECK_GATE_R8_M1A3C_STARTB.tsv \
         PRERUN_CHECKS_R8_M1a.txt; do
    test -f "$f" || { echo "sums_m1a3c_all: MISSING $f" >&2; exit 2; }
    sha256sum "$f"
done > "$OUT"
echo "sums_m1a3c_all: lines=$(grep -c . "$OUT") -> $OUT"
exit 0
