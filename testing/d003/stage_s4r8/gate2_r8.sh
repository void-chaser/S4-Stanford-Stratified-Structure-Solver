#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate2_r8.sh -- P05-S4 R8 M0, restart 2: opening (start) and closing (end) gate.  New file.
# Rules: RESTART section 2.1 with the changes of RESTART2 section 3 (stage_s4r8 sha256 list, three untracked briefs,
# manifest check through standard input, stderr merged with 2>&1).  Decisions U128, U129, U132.
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate2_r8.sh p05-s4r8 GATE_R8_M0_R2.txt start TMP_COUNT TMP_SHA256
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate2_r8.sh p05-s4r8 GATE_R8_M0_R2_END.txt end TMP_COUNT TMP_SHA256 START_TMP_COUNT START_TMP_SHA256
#
# The temporary-directory snapshot (entry count and sha256 of the top level) is taken by the caller with the read-only
# inline commands "ls -A ... | wc -l" and "ls -A ... | sha256sum" and passed in as arguments.
# Each output line is PASS or FAIL (counted), or RECORD (a value written down, not compared).  Last line: FAILS=<n>.
# The output name must be a plain file name; an existing output file is refused (U17).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate2_r8: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate2_r8: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
case "$MODE" in
    start|end) ;;
    *) echo "gate2_r8: REFUSED: mode must be start or end" >&2; exit 2 ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate2_r8: REFUSED: exists (U17): $OUT" >&2; exit 2; }
TC=${4:-}
TS=${5:-}
REC_MSG="P05-S4 R8 M0 records (restart 2): rulings U121-U132, errata ES3R4-31 and ERRATA_8 (E8-1..E8-4); gate per U128/U132; briefs archived. awaiting user review"
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M0 gate2 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- HEAD (mode dependent) ----
if [ "$MODE" = start ]; then
    check HEAD 3ab56801e697910bdff9fbe6056807c2e41841b5 "$(git rev-parse HEAD 2>&1)"
else
    check HEAD_PARENT 3ab56801e697910bdff9fbe6056807c2e41841b5 "$(git rev-parse HEAD^ 2>&1)"
    check HEAD_SUBJECT "$REC_MSG" "$(git log -1 --format=%s 2>&1)"
fi

# ---- checks repeated at the end (RESTART2 section 3, item 1 without HEAD, items 2, 3, 6, 7) ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"
if [ "$MODE" = start ]; then MF=S4R7_MANIFEST_CHECK_R8_R2.tsv; else MF=S4R7_MANIFEST_CHECK_R8_R2_END.tsv; fi
S4R7_LINE=$(python3 -I -B testing/d003/stage_s4r8/check_s4r7_manifests_r8.py "$MF" 2>&1 | tail -n 1)
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_MANIFEST_FILE "checkpoints/p05/evidence/p05-s4r8/$MF"

# ---- start only ----
if [ "$MODE" = start ]; then
    check BRIEF_BASE_SHA256 868dc6820e17e7245527cca132c4d9d0f28bbad2af5b15ffebd775ddbae80408 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md 2>&1 | cut -d' ' -f1)"
    check BRIEF_RESTART_SHA256 ba8fb515f251589ea8ae5fe8e0b71fb4277d12165e5fa5d932e1de05b955abf1 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md 2>&1 | cut -d' ' -f1)"
    check FIRST_START_GATE_R8_M0_SHA256 1c8ecdd6e8d1301fa986fa0025008a22f8a23c2c71c29068f2bf772f6e6d9725 "$(sha256sum checkpoints/p05/evidence/p05-s4r8/GATE_R8_M0.txt 2>&1 | cut -d' ' -f1)"
    check GATE_R8_SH_SHA256 8c997618d68da8802b6465d5b1318c730da28acc61dff6e14f58064d0cc934b7 "$(sha256sum testing/d003/stage_s4r8/gate_r8.sh 2>&1 | cut -d' ' -f1)"
    check PRERUN_LOG_R8_SH_SHA256 a079a35e47e1243551fcee28d51e358bc31ba24ba0e6325c159805ae6ad417ca "$(sha256sum testing/d003/stage_s4r8/prerun_log_r8.sh 2>&1 | cut -d' ' -f1)"
    GS=$(git status --short 2>&1 | grep -v 'testing/d003/stage_s4r8/' | LC_ALL=C sort)
    GS_EXP=$(printf '%s\n' '?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md' '?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md' '?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md' | LC_ALL=C sort)
    check GIT_STATUS_EXCEPT_STAGE_S4R8 "$GS_EXP" "$GS"
    if [ -n "$TC" ] && [ -n "$TS" ]; then TSG=yes; else TSG=no; fi
    check TMP_SNAPSHOT_ARGS_GIVEN yes "$TSG"
    record TMP_COUNT_START "$TC"
    record TMP_SHA256_START "$TS"
fi

# ---- end only ----
if [ "$MODE" = end ]; then
    ST=$(git status --short 2>&1)
    BAD=$(printf '%s\n' "$ST" | awk 'length($0) == 0 { next }
        { x = substr($0, 1, 2); p = substr($0, 4)
          if (x == "??") { if (p !~ /^checkpoints\/p05\// && p !~ /^testing\/d003\/stage_s4r8\//) print "OUTSIDE " $0 }
          else if (x == " M") { if (p != "checkpoints/p05/STATE.md") print "MODIFIED " $0 }
          else print "OTHER " $0 }')
    check GIT_STATUS_END_SCOPE "" "$BAD"
    record GIT_STATUS_END "$ST"
    check TMP_COUNT_END_EQ_START "${6:-}" "$TC"
    check TMP_SHA256_END_EQ_START "${7:-}" "$TS"
fi

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate2_r8: $MODE FAILS=$FAILS -> $OUT"
exit 0
