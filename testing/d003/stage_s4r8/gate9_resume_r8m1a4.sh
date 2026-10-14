#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate9_resume_r8m1a4.sh -- P05-S4 R8 M1a CONT3a resume gate check.  New file.
# Usage (through safe_run; every argument is checked before any file is written):
#   sh testing/d003/stage_s4r8/gate9_resume_r8m1a4.sh p05-s4r8 OUT TC TS
# OUT must be GATE_R8_M1a4_RESUME.txt and must not exist (U17).
# TC = entry count of the temporary area, TS = its sha256 (form 5 snapshot).
# Recheck output: S4R7_RECHECK_GATE_R8_M1A4_RESUME.tsv.
# Output: one PASS/FAIL line per check, RECORD lines, last line FAILS=<n>.  Exit 2 = refused before any file is written.
set -u
refuse() { echo "gate9_resume_r8m1a4: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8 ] || refuse "first argument must be p05-s4r8"
OUTNAME=${2:-}
case "$OUTNAME" in
    GATE_R8_M1a4_RESUME.txt|GATE_R8_M1a4_RESUME_R2.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a4_RESUME*.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"

[ $# -eq 4 ] || refuse "usage: gate9_resume_r8m1a4.sh p05-s4r8 OUT TC TS"
TC=${3:-}; TS=${4:-}
case "$TC" in
    ''|*[!0-9]*) refuse "TC must be digits" ;;
esac
case "$TS" in
    ''|*[!0-9a-f]*) refuse "TS must be lowercase hex" ;;
esac
[ "${#TS}" = 64 ] || refuse "TS must be 64 characters"

STARTF="$EV/GATE_R8_M1a4_START.txt"
test -f "$STARTF" || refuse "start file missing: $STARTF"
[ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
[ "$(wc -l < "$STARTF" | tr -d ' ')" = 34 ] || refuse "start file line count is not 34"

SR7="S4R7_RECHECK_$(printf '%s' "$OUTSTEM" | tr 'a-z' 'A-Z').tsv"
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT3a resume gate9 -> %s, utc=%s\n' "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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
prefix_check() {
    _n=$2; _f=$3
    _hs=$(head -c "$_n" "$_f" | sha256sum | cut -d' ' -f1)
    check "$1" "$4" "$_hs"
}

# ---- branch, HEAD, trees, judge ----
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current 2>&1)"
check HEAD 331c022c3d9944cff8e7e63e16c24d33253ce847 "$(git rev-parse HEAD 2>&1)"
record HEAD "$(git rev-parse HEAD 2>&1)"
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"
check TRACKED_TESTING_D003_CHANGES_NONE "" "$(git diff --name-only HEAD -- testing/d003 2>&1)"

# ---- start gate file check ----
check START_FILE_EXISTS yes "$([ -f "$STARTF" ] && echo yes || echo no)"
check START_FILE_LINES 34 "$(wc -l < "$STARTF" | tr -d ' ')"
check START_FILE_FAILS_0 FAILS=0 "$(tail -n 1 "$STARTF")"

# ---- RULINGS, ERRATA_8, PRERUN prefixes and append contents ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
PRE=checkpoints/p05/evidence/p05-s4r8/PRERUN_CHECKS_R8_M1a.txt

prefix_check RULINGS_FIRST_66509_BYTES_SHA256 66509 "$RUL" 77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5
prefix_check ERRATA_8_FIRST_37669_BYTES_SHA256 37669 "$ERR" ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725
prefix_check ERRATA_8_FIRST_13990_BYTES_SHA256 13990 "$ERR" 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551
prefix_check PRERUN_PREFIX_5603 5603 "$PRE" 8eb5c81a07ba467d36c8b6a760cc72e1d817887fe956638c7e598e754d43687d

check RULINGS_NF_ALL_5 "" "$(awk -F'\t' '/^#/{next} NF!=5{print NR}' "$RUL" | tr '\n' ' ')"
check RULINGS_APPENDED_IDS "U176 U177 U178 U179 U180 U181 U182 " "$(tail -n 7 "$RUL" | cut -f1 | tr '\n' ' ')"
check ERRATA_8_APPENDED_ENTRIES "E8-56 E8-57 E8-58 E8-59 E8-60 " "$(tail -c +37670 "$ERR" | grep -o '^E8-[0-9]*' | tr '\n' ' ')"

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

# ---- M1a directory: the four manifests, every line checked ----
M1A_DIR=checkpoints/p05/registries/s4r8/M1a
for _m in SHA256SUMS.txt SHA256SUMS_M1a3c_A.txt SHA256SUMS_M1a3c_B.txt SHA256SUMS_M1a3c_B_END.txt; do
    _t=$(grep -c . "$M1A_DIR/$_m" 2>&1)
    _o=$(cd "$M1A_DIR" && sha256sum -c "$_m" 2>&1 | grep -c ': OK$')
    check "M1A_MANIFEST_${_m}_OK_LINES_EQ_TOTAL" "$_t" "$_o"
done

# ---- s4r7 manifests: classified recheck ----
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a4.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a4_resume.txt" 2>&1
check S4R7_MANIFESTS "fails=0" "$(tail -n 1 "$EV/$SR7" 2>&1)"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- git status: authorized resume working tree ----
ST=$(git status --short 2>&1)
BAD=$(printf '%s\n' "$ST" | awk '
    length($0) == 0 { next }
    {
        p = substr($0, 4); lp = tolower(p)
        if (substr($0, 1, 3) == " M " && (p == "checkpoints/p05/registries/RULINGS.tsv" || p == "checkpoints/p05/registries/s4r8/ERRATA_8.txt")) next
        if (substr($0, 1, 3) == "?? " && (lp ~ /m1a4/ || lp ~ /cont3a/)) next
        print "NOT_ALLOWED " $0
    }')
check GIT_STATUS_ALLOWED_ONLY "" "$BAD"
record GIT_STATUS "$ST"

# ---- temporary-area snapshot ----
record TMP_COUNT_RESUME "$TC"
record TMP_SHA256_RESUME "$TS"

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate9_resume_r8m1a4: FAILS=$FAILS -> $OUT"
exit 0
