#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate3_r8.sh -- P05-S4 R8 M0, closing gate (end mode), per the closing brief section 2 and U133.  New file.
# It is gate2_r8.sh (committed, not modified) with three changes only:
#   (1) the status rule of U133: modified (M) tracked files may be checkpoints/p05/STATE.md,
#       checkpoints/p05/registries/s4r8/ERRATA_8.txt and checkpoints/p05/registries/RULINGS.tsv; untracked (??) only under
#       checkpoints/p05/ or testing/d003/stage_s4r8/;
#   (2) HEAD must be the records commit 2875c557c6f2348bdbad3b077af4651f94eb65b2, and HEAD^ must be 3ab56801e697910bdff9fbe6056807c2e41841b5;
#   (3) the sha256 of GATE_R8_M0_R2_END.txt (the stopped first closing gate, U133) must be a10e081742bb4df95cb4c31b31706fe992fc427be1db4e1642f81232ee2494c9.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate3_r8.sh p05-s4r8 GATE_R8_M0_R3_END.txt end TMP_COUNT TMP_SHA256 0 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
# Each output line is PASS or FAIL (counted), or RECORD.  Last line: FAILS=<n>.  The output name must be a plain file name;
# an existing output file is refused (U17).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate3_r8: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate3_r8: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
[ "$MODE" = end ] || { echo "gate3_r8: REFUSED: this gate is the closing gate (end)" >&2; exit 2; }
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate3_r8: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test ! -e "$EV/S4R7_RECHECK_R8_R3_END.txt" || { echo "gate3_r8: REFUSED: exists (U17): S4R7_RECHECK_R8_R3_END.txt" >&2; exit 2; }
TC=${4:-}
TS=${5:-}
SC=${6:-}
SS=${7:-}
REC_HEAD=2875c557c6f2348bdbad3b077af4651f94eb65b2
BASE_HEAD=3ab56801e697910bdff9fbe6056807c2e41841b5
REC_MSG="P05-S4 R8 M0 records (restart 2): rulings U121-U132, errata ES3R4-31 and ERRATA_8 (E8-1..E8-4); gate per U128/U132; briefs archived. awaiting user review"
END_GATE_SHA=a10e081742bb4df95cb4c31b31706fe992fc427be1db4e1642f81232ee2494c9
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M0 gate3 (end, closing) -> %s, utc=%s\n' "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

check() {
    _e=$(printf '%s' "$2" | tr '\n' ';')
    _a=$(printf '%s' "$3" | tr '\n' ';')
    if [ "$2" = "$3" ]; then _r=PASS; else _r=FAIL; FAILS=$((FAILS + 1)); fi
    printf '%s\t%s\texpected=%s\tactual=%s\n' "$_r" "$1" "$_e" "$_a" >> "$OUT"
}
record() {
    _v=$(printf '%s' "$2" | tr '\n' ';')
    printf 'RECORD\t%s\tvalue=%s\n' "$1" "$_v" >> "$OUT"
}

# ---- HEAD (change 2 of gate3) ----
check HEAD "$REC_HEAD" "$(git rev-parse HEAD 2>&1)"
check HEAD_PARENT "$BASE_HEAD" "$(git rev-parse HEAD^ 2>&1)"
check HEAD_SUBJECT "$REC_MSG" "$(git log -1 --format=%s 2>&1)"

# ---- repeated checks of the closing gate (gate2 end items 1 without HEAD, 2, 3, 6, 7) ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"
# the registries/s4r7 manifest checks are repeated read only (recheck_s4r7_r8_r3.py); the details go to a new file
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8_r3.py > "$EV/S4R7_RECHECK_R8_R3_END.txt" 2>&1
S4R7_LINE=$(tail -n 1 "$EV/S4R7_RECHECK_R8_R3_END.txt")
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/S4R7_RECHECK_R8_R3_END.txt"

# ---- change 3: the stopped first closing gate is unchanged ----
check GATE_R8_M0_R2_END_SHA256 "$END_GATE_SHA" "$(sha256sum checkpoints/p05/evidence/p05-s4r8/GATE_R8_M0_R2_END.txt 2>&1 | cut -d' ' -f1)"

# ---- change 1: status scope (U133) ----
ST=$(git status --short 2>&1)
BAD=$(printf '%s\n' "$ST" | awk 'length($0) == 0 { next }
    { x = substr($0, 1, 2); p = substr($0, 4)
      if (x == "??") { if (p !~ /^checkpoints\/p05\// && p !~ /^testing\/d003\/stage_s4r8\//) print "OUTSIDE " $0 }
      else if (x == " M") { if (p != "checkpoints/p05/STATE.md" && p != "checkpoints/p05/registries/s4r8/ERRATA_8.txt" && p != "checkpoints/p05/registries/RULINGS.tsv") print "MODIFIED " $0 }
      else print "OTHER " $0 }')
check GIT_STATUS_END_SCOPE "" "$BAD"
record GIT_STATUS_END "$ST"
check TMP_COUNT_END_EQ_START "$SC" "$TC"
check TMP_SHA256_END_EQ_START "$SS" "$TS"

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate3_r8: end FAILS=$FAILS -> $OUT"
exit 0
