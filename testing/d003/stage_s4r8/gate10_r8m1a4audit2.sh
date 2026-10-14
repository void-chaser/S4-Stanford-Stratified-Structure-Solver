#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate10_r8m1a4audit2.sh -- P05-S4 R8 M1a CONT3a audit part 2 gate (r8m1a4audit2).  New file; gate9_r8m1a4.sh is not modified (U186).
# Modes (through safe_run; every argument is checked before any output file is written):
#   sh testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh p05-s4r8 OUT startA TC TS
#   sh testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh p05-s4r8 OUT startB TC TS
#   sh testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh p05-s4r8 OUT end START_FILE TC TS
# OUT = GATE_R8_M1a4_AUDIT2_<name>.txt in the evidence directory; it must not exist (U17).
# TC = entry count and TS = sha256 of the temporary-area listing, taken by the caller with the permitted inline form.
# The recheck output is derived from OUT: S4R7_RECHECK_GATE_R8_M1A4_AUDIT2_<NAME>.tsv (matches the recheck script pattern).
# startA: status minus the four round-own pre-start files (named exactly) must equal gate_allow_r8m1a4audit2_A.txt (31 lines).
# startB: reads the phase-A whole-file values from GATE_R8_M1a4_AUDIT2_END_A.txt (RECORD lines), never from arguments.
# end: reads every start value (HEAD, status, temporary area, file values) from START_FILE.
# Output: one PASS/FAIL line per check, RECORD lines, and FAILS=<n> as the last line.  Exit 2 = refused before any output.
set -u
refuse() { echo "gate10_r8m1a4audit2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8 ] || refuse "first argument must be p05-s4r8"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1a4_AUDIT2_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a4_AUDIT2_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
NAMEPART=${OUTSTEM#GATE_R8_M1a4_AUDIT2_}
case "$NAMEPART" in
    '') refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
STARTF=""
case "$MODE" in
    startA|startB)
        [ $# -eq 5 ] || refuse "$MODE takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    end)
        [ $# -eq 6 ] || refuse "end takes START_FILE TC TS"
        STARTF=${4:-}; TC=${5:-}; TS=${6:-} ;;
    *) refuse "mode must be startA, startB or end" ;;
esac
case "$TC" in
    ''|*[!0-9]*) refuse "TC must be digits" ;;
esac
case "$TS" in
    ''|*[!0-9a-f]*) refuse "TS must be lowercase hex" ;;
esac
[ "${#TS}" = 64 ] || refuse "TS must be 64 characters"
if [ "$MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    _h=$(head -n 1 "$STARTF")
    case "$_h" in
        *"gate10 (startA) ->"*|*"gate10 (startB) ->"*) ;;
        *) refuse "start file header is not a gate10 start" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi
SR7="S4R7_RECHECK_GATE_R8_M1A4_AUDIT2_$(printf '%s' "$NAMEPART" | tr 'a-z' 'A-Z').tsv"
case "$SR7" in
    S4R7_RECHECK_GATE_R8_M1A4_AUDIT2_*.tsv) ;;
    *) refuse "derived recheck name is not accepted" ;;
esac
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
AEND="$EV/GATE_R8_M1a4_AUDIT2_END_A.txt"
ST_FILE="$EV/tmp/status_now_$NAMEPART.txt"
: > "$OUT"
printf '# P05-S4 R8 M1a CONT3a audit part 2 gate10 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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
recval() {
    awk -F'\t' -v k="$2" '$1=="RECORD" && $2==k {sub(/^value=/, "", $3); print $3}' "$1" | head -n 1
}
prefix_check() {
    _hs=$(head -c "$2" "$3" | sha256sum | cut -d' ' -f1)
    check "$1" "$4" "$_hs"
}

# ---- branch, HEAD, trees, judge ----
BASE=fbc46681cecf2a056b17ef77cfac3a1c946e2334
BASEP=331c022c3d9944cff8e7e63e16c24d33253ce847
HEAD_NOW=$(git rev-parse HEAD 2>&1)
PARENT_NOW=$(git rev-parse HEAD^ 2>&1)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current 2>&1)"
case "$MODE" in
    startA)
        check HEAD_IS_BASE "$BASE" "$HEAD_NOW"
        check HEAD_PARENT_IS_331C022 "$BASEP" "$PARENT_NOW" ;;
    startB)
        check HEAD_PARENT_IS_BASE "$BASE" "$PARENT_NOW"
        check HEAD_IS_NOT_BASE yes "$( [ "$HEAD_NOW" = "$BASE" ] && echo no || echo yes )" ;;
    end)
        check HEAD_EQ_START "$(recval "$STARTF" HEAD)" "$HEAD_NOW"
        check HEAD_PARENT_EQ_START "$(recval "$STARTF" HEAD_PARENT)" "$PARENT_NOW" ;;
esac
record HEAD "$HEAD_NOW"
record HEAD_PARENT "$PARENT_NOW"
record START_MODE "$MODE"
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_F2_F3_FOUR_FILES "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"
check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003 2>&1)"
check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_BASE "" "$(git diff --name-only --diff-filter=MD "$BASE" HEAD -- testing/d003 2>&1)"

# ---- RULINGS, ERRATA_8, PRERUN: historical prefixes and mode-specific values ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
PRE=checkpoints/p05/evidence/p05-s4r8/PRERUN_CHECKS_R8_M1a.txt
prefix_check ERRATA_8_FIRST_13990_BYTES_SHA256 13990 "$ERR" 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551
prefix_check ERRATA_8_FIRST_37669_BYTES_SHA256 37669 "$ERR" ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725
prefix_check PRERUN_PREFIX_5603 5603 "$PRE" 8eb5c81a07ba467d36c8b6a760cc72e1d817887fe956638c7e598e754d43687d
check RULINGS_LINES_NOT_5_FIELDS 0 "$(awk -F'\t' '/^#/{next} NF!=5{n++} END{print n+0}' "$RUL")"
case "$MODE" in
    startA)
        check RULINGS_BYTES_START_A 68691 "$(wc -c < "$RUL" | tr -d ' ')"
        check RULINGS_SHA256_START_A 55359d8c35a7124acc2ccf63c5be3adcc2844a43231aeee5affc3f01584e0215 "$(sha256sum "$RUL" | cut -d' ' -f1)"
        check RULINGS_HEAD_BLOB_SHA256_START_A 55359d8c35a7124acc2ccf63c5be3adcc2844a43231aeee5affc3f01584e0215 "$(git show "HEAD:$RUL" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_BYTES_START_A 50547 "$(wc -c < "$ERR" | tr -d ' ')"
        check ERRATA_8_SHA256_START_A 884a5f343e897359e91bc0cbd221316f696e843c5299fc5328555130dc614e2b "$(sha256sum "$ERR" | cut -d' ' -f1)"
        check ERRATA_8_FIRST_41272_SHA256_EQ_HEAD 11574288e401e959b043dc8e8cd9fd11bc030e6147589eda8ab250d2f7046ed7 "$(head -c 41272 "$ERR" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_HEAD_BLOB_SHA256 11574288e401e959b043dc8e8cd9fd11bc030e6147589eda8ab250d2f7046ed7 "$(git show "HEAD:$ERR" | sha256sum | cut -d' ' -f1)"
        ;;
    startB)
        check A_END_PRESENT yes "$( [ -f "$AEND" ] && echo yes || echo no )"
        _ah=$(head -n 1 "$AEND" 2>&1)
        case "$_ah" in
            *"gate10 (end) ->"*) _ahv=yes ;;
            *) _ahv=no ;;
        esac
        check A_END_HEADER_IS_END yes "$_ahv"
        check A_END_LAST_LINE_FAILS0 "FAILS=0" "$(tail -n 1 "$AEND" 2>&1)"
        _rb=$(recval "$AEND" RULINGS_BYTES); _rh=$(recval "$AEND" RULINGS_SHA256)
        _eb=$(recval "$AEND" ERRATA_8_BYTES); _eh=$(recval "$AEND" ERRATA_8_SHA256)
        check RULINGS_NOW_BYTES_EQ_A_END "$_rb" "$(wc -c < "$RUL" | tr -d ' ')"
        check RULINGS_NOW_SHA256_EQ_A_END "$_rh" "$(sha256sum "$RUL" | cut -d' ' -f1)"
        check RULINGS_COMMITTED_SHA256_EQ_A_END "$_rh" "$(git show "HEAD:$RUL" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_NOW_BYTES_EQ_A_END "$_eb" "$(wc -c < "$ERR" | tr -d ' ')"
        check ERRATA_8_NOW_SHA256_EQ_A_END "$_eh" "$(sha256sum "$ERR" | cut -d' ' -f1)"
        check ERRATA_8_COMMITTED_SHA256_EQ_A_END "$_eh" "$(git show "HEAD:$ERR" | sha256sum | cut -d' ' -f1)"
        ;;
    end)
        _rb=$(recval "$STARTF" RULINGS_BYTES); _rh=$(recval "$STARTF" RULINGS_SHA256)
        _eb=$(recval "$STARTF" ERRATA_8_BYTES); _eh=$(recval "$STARTF" ERRATA_8_SHA256)
        check RULINGS_PREFIX_OF_START_UNCHANGED "$_rh" "$(head -c "$_rb" "$RUL" | sha256sum | cut -d' ' -f1)"
        check RULINGS_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$RUL" | tr -d ' ')" -ge "$_rb" ] && echo yes || echo no )"
        check ERRATA_8_PREFIX_OF_START_UNCHANGED "$_eh" "$(head -c "$_eb" "$ERR" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$ERR" | tr -d ' ')" -ge "$_eb" ] && echo yes || echo no )"
        check RULINGS_U183_TO_U187_ROWS 5 "$(awk -F'\t' '$1 ~ /^U18[3-7]$/ {n++} END{print n+0}' "$RUL")"
        check ERRATA_8_E8_66_PRESENT 1 "$(grep -c '^E8-66  ' "$ERR")"
        ;;
esac
record RULINGS_BYTES "$(wc -c < "$RUL" | tr -d ' ')"
record RULINGS_SHA256 "$(sha256sum "$RUL" | cut -d' ' -f1)"
record ERRATA_8_BYTES "$(wc -c < "$ERR" | tr -d ' ')"
record ERRATA_8_SHA256 "$(sha256sum "$ERR" | cut -d' ' -f1)"
record PRERUN_BYTES "$(wc -c < "$PRE" | tr -d ' ')"

# ---- registries: root manifest (ERRATA_8 line by prefix, others sha256sum -c), s3r4c5 manifest ----
S4R8_DIR=checkpoints/p05/registries/s4r8
check S4R8_TOTAL_LINES_25 25 "$(grep -c . "$S4R8_DIR/SHA256SUMS.txt" 2>&1)"
check S4R8_ERRATA_LINE_IS_13990_PREFIX "$(grep 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" | cut -d' ' -f1)" "$(head -c 13990 "$ERR" | sha256sum | cut -d' ' -f1)"
S4R8_NONERR=$(grep -vc 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_OK=$(grep -v 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" | (cd "$S4R8_DIR" && sha256sum -c - 2>&1) | grep -c ': OK$')
check S4R8_OTHER_LINES_ALL_OK "$S4R8_NONERR" "$S4R8_OK"
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"

# ---- M1a directory: manifests, every line checked ----
M1A_DIR=checkpoints/p05/registries/s4r8/M1a
M1A_LIST="SHA256SUMS.txt SHA256SUMS_M1a3c_A.txt SHA256SUMS_M1a3c_B.txt SHA256SUMS_M1a3c_B_END.txt SHA256SUMS_M1a4.txt SHA256SUMS_M1a4_END.txt SHA256SUMS_M1a4AUDIT.txt"
if [ "$MODE" = end ] && [ "$(recval "$STARTF" START_MODE)" = startB ]; then
    M1A_LIST="$M1A_LIST SHA256SUMS_M1a4AUDIT2.txt"
fi
for _m in $M1A_LIST; do
    _t=$(grep -c . "$M1A_DIR/$_m" 2>&1)
    _o=$(cd "$M1A_DIR" && sha256sum -c "$_m" 2>&1 | grep -c ': OK$')
    check "M1A_MANIFEST_${_m}_OK_LINES_EQ_TOTAL" "$_t" "$_o"
done

# ---- s4r7 manifests: classified recheck (same rule as gate9; output name derived from OUT) ----
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a4.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a4audit2_$NAMEPART.txt" 2>&1
check S4R7_MANIFESTS_FAILS_0 "fails=0" "$(tail -n 1 "$EV/$SR7" 2>&1)"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- phase-B start: phase-A commit list (A_commit file written after the phase-A commit) ----
if [ "$MODE" = startB ]; then
    check PHASE_A_COMMIT_FILES_EQ_A_COMMIT_LIST "$(LC_ALL=C sort testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A_commit.txt 2>&1)" "$(git diff --name-only "$BASE" HEAD 2>&1 | LC_ALL=C sort)"
fi

# ---- git status ----
git status --short > "$ST_FILE" 2>&1
case "$MODE" in
    startA)
        check ALLOW_A_LINE_COUNT_31 31 "$(grep -c . testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A.txt 2>&1)"
        awk 'BEGIN { ex["?? testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh"]=1; ex["?? testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A.txt"]=1; ex["?? testing/d003/stage_s4r8/prerun_log_r8m1a4audit2.sh"]=1; ex["?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT2.md"]=1 } length($0) > 0 && !($0 in ex) { print }' "$ST_FILE" | LC_ALL=C sort > "$EV/tmp/status_noexempt_$NAMEPART.txt"
        check STATUS_A_EQ_ALLOW_A_SORTED "$(LC_ALL=C sort testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A.txt 2>&1)" "$(LC_ALL=C sort "$EV/tmp/status_noexempt_$NAMEPART.txt")"
        while IFS= read -r _l; do record STATUS_START "$_l"; done < "$ST_FILE"
        ;;
    startB)
        check STATUS_B_ONLY_ROUND_UNTRACKED "" "$(awk '{ if (length($0) == 0) next; p = substr($0, 4); lp = tolower(p); if (substr($0, 1, 3) == "?? " && lp ~ /audit2/) next; print "NOT_ALLOWED " $0 }' "$ST_FILE")"
        while IFS= read -r _l; do record STATUS_START "$_l"; done < "$ST_FILE"
        ;;
    end)
        awk -F'\t' '$1=="RECORD" && $2=="STATUS_START" { v=$3; sub(/^value=/, "", v); print v }' "$STARTF" > "$EV/tmp/start_status_$NAMEPART.txt"
        check STATUS_END_ONLY_ALLOWED "" "$(awk 'NR==FNR { s[$0]=1; next } { if (length($0) == 0) next; if ($0 in s) next; p = substr($0, 4); lp = tolower(p); if (substr($0, 1, 3) == " M " && (p == "checkpoints/p05/STATE.md" || p == "checkpoints/p05/registries/RULINGS.tsv" || p == "checkpoints/p05/registries/s4r8/ERRATA_8.txt")) next; if (substr($0, 1, 3) == "?? " && lp ~ /audit2/) next; print "NOT_ALLOWED " $0 }' "$EV/tmp/start_status_$NAMEPART.txt" "$ST_FILE")"
        ;;
esac

# ---- temporary-area snapshot (form taken by the caller) ----
case "$MODE" in
    startA|startB)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate10_r8m1a4audit2: $MODE FAILS=$FAILS -> $OUT"
exit 0
