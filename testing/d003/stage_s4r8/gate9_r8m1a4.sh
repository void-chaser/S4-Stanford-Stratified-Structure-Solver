#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate9_r8m1a4.sh -- P05-S4 R8 M1a CONT3a gate, modes start and end only.  New file (gate8_r8m1a3c.sh not modified).
# Usage (through safe_run; every argument is checked before any file is written):
#   sh testing/d003/stage_s4r8/gate9_r8m1a4.sh p05-s4r8 OUT start TC TS
#   sh testing/d003/stage_s4r8/gate9_r8m1a4.sh p05-s4r8 OUT end   START_FILE TC TS
# OUT is GATE_R8_M1a4_<name>.txt and must not exist (U17).  TC = entry count of the temporary area, TS = its sha256 (form 5).
# The recheck output name is S4R7_RECHECK_ + upper-case OUT stem + .tsv (derived; never fixed).
# end reads the start values (HEAD, trees, temporary-area snapshot) from START_FILE; nothing is typed by hand.
# Output: one PASS/FAIL line per check, RECORD lines, last line FAILS=<n>.  Exit 2 = refused before any file is written.
set -u
refuse() { echo "gate9_r8m1a4: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8 ] || refuse "first argument must be p05-s4r8"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1a4_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a4_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
case "$OUTSTEM" in
    GATE_R8_M1a4_) refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
case "$MODE" in
    start)
        [ $# -eq 5 ] || refuse "start takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    end)
        [ $# -eq 6 ] || refuse "end takes START_FILE TC TS"
        STARTF=${4:-}; TC=${5:-}; TS=${6:-} ;;
    *) refuse "mode must be start or end" ;;
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
        *"gate9 (start) ->"*) ;;
        *) refuse "start file header does not match mode end" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi
SR7="S4R7_RECHECK_$(printf '%s' "$OUTSTEM" | tr 'a-z' 'A-Z').tsv"
case "$SR7" in
    S4R7_RECHECK_GATE_R8_M1A4_*.tsv) ;;
    *) refuse "derived recheck name is not accepted" ;;
esac
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT3a gate9 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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
    awk -F'\t' -v k="$2" '$1=="RECORD" && $2==k {sub(/^value=/, "", $3); print $3}' "$1"
}
prefix_check() {
    _n=$2; _f=$3
    _hs=$(head -c "$_n" "$_f" | sha256sum | cut -d' ' -f1)
    check "$1" "$4" "$_hs"
}

# ---- branch, HEAD, trees, judge ----
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current 2>&1)"
case "$MODE" in
    start)
        check HEAD 331c022c3d9944cff8e7e63e16c24d33253ce847 "$(git rev-parse HEAD 2>&1)" ;;
    end)
        check HEAD_EQ_START "$(recval "$STARTF" HEAD)" "$(git rev-parse HEAD 2>&1)" ;;
esac
record HEAD "$(git rev-parse HEAD 2>&1)"
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"
check TRACKED_TESTING_D003_CHANGES_NONE "" "$(git diff --name-only HEAD -- testing/d003 2>&1)"

# ---- RULINGS, ERRATA_8, PRERUN (start: before this round's append; end: prefixes unchanged) ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
PRE=checkpoints/p05/evidence/p05-s4r8/PRERUN_CHECKS_R8_M1a.txt
if [ "$MODE" = start ]; then
    check RULINGS_BYTES_BEFORE_APPEND 66509 "$(wc -c < "$RUL" | tr -d ' ')"
    check RULINGS_WHOLE_SHA256_BEFORE_APPEND 77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5 "$(sha256sum "$RUL" 2>&1 | cut -d' ' -f1)"
    check ERRATA_8_BYTES_BEFORE_APPEND 37669 "$(wc -c < "$ERR" | tr -d ' ')"
    check ERRATA_8_WHOLE_SHA256_BEFORE_APPEND ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725 "$(sha256sum "$ERR" 2>&1 | cut -d' ' -f1)"
else
    prefix_check RULINGS_FIRST_66509_BYTES_SHA256 66509 "$RUL" 77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5
    prefix_check ERRATA_8_FIRST_37669_BYTES_SHA256 37669 "$ERR" ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725
    check RULINGS_NF_ALL_5 "" "$(awk -F'\t' '/^#/{next} NF!=5{print NR}' "$RUL" | tr '\n' ' ')"
fi
prefix_check PRERUN_PREFIX_5603 5603 "$PRE" 8eb5c81a07ba467d36c8b6a760cc72e1d817887fe956638c7e598e754d43687d
prefix_check ERRATA_8_FIRST_13990_BYTES_SHA256 13990 "$ERR" 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551
record RULINGS_BYTES "$(wc -c < "$RUL" | tr -d ' ')"
record ERRATA_8_BYTES "$(wc -c < "$ERR" | tr -d ' ')"
record PRERUN_BYTES "$(wc -c < "$PRE" | tr -d ' ')"

# ---- registries: root manifest (ERRATA_8 by prefix, others sha256sum -c), s3r4c5 manifest ----
S4R8_DIR=checkpoints/p05/registries/s4r8
S4R8_TOTAL=$(grep -c . "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_NONERR=$(grep -vc 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_OK=$(grep -v 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" | (cd "$S4R8_DIR" && sha256sum -c - 2>&1) | grep -c ': OK$')
check S4R8_OTHER_LINES_ALL_OK "$S4R8_NONERR" "$S4R8_OK"
check S4R8_TOTAL_LINES_25 25 "$S4R8_TOTAL"
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"

# ---- M1a directory: manifests, every line checked ----
M1A_DIR=checkpoints/p05/registries/s4r8/M1a
M1A_LIST="SHA256SUMS.txt SHA256SUMS_M1a3c_A.txt SHA256SUMS_M1a3c_B.txt SHA256SUMS_M1a3c_B_END.txt"
if [ "$MODE" = end ]; then
    M1A_LIST="$M1A_LIST SHA256SUMS_M1a4.txt"
fi
for _m in $M1A_LIST; do
    _t=$(grep -c . "$M1A_DIR/$_m" 2>&1)
    _o=$(cd "$M1A_DIR" && sha256sum -c "$_m" 2>&1 | grep -c ': OK$')
    check "M1A_MANIFEST_${_m}_OK_LINES_EQ_TOTAL" "$_t" "$_o"
done

# ---- s4r7 manifests: classified recheck (same rule as gate8, output name derived from OUT) ----
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a4.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a4_$MODE.txt" 2>&1
check S4R7_MANIFESTS "fails=0" "$(tail -n 1 "$EV/$SR7" 2>&1)"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- git status: start = brief plus r8m1a4 untracked files only; end = allowed modified files plus r8m1a4 untracked files ----
ST=$(git status --short 2>&1)
BAD=$(printf '%s\n' "$ST" | awk -v mode="$MODE" '
    length($0) == 0 { next }
    {
        p = substr($0, 4); lp = tolower(p)
        if (mode == "start") {
            if (substr($0, 1, 3) == "?? " && (lp ~ /m1a4/ || lp ~ /cont3a/)) next
            print "NOT_ALLOWED " $0; next
        }
        if (substr($0, 1, 3) == " M " && (p == "checkpoints/p05/STATE.md" || p == "checkpoints/p05/registries/RULINGS.tsv" || p == "checkpoints/p05/registries/s4r8/ERRATA_8.txt")) next
        if (substr($0, 1, 3) == "?? " && (lp ~ /m1a4/ || lp ~ /cont3a/)) next
        print "NOT_ALLOWED " $0
    }')
check GIT_STATUS_ALLOWED_ONLY "" "$BAD"
record GIT_STATUS "$ST"

# ---- temporary-area snapshot (form 5, taken by the caller) ----
case "$MODE" in
    start)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate9_r8m1a4: $MODE FAILS=$FAILS -> $OUT"
exit 0
