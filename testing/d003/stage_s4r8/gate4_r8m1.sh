#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate4_r8m1.sh -- P05-S4 R8 M1a gate (start and end), brief R8 M1a section 3.  New file (copied from gate3_r8.sh and changed).
# Changes against gate3_r8.sh (committed, not modified):
#   (1) start and end are both supported (gate3 supports end only);
#   (2) the allowed-status lists are DATA files given as the third argument (U143), not literals in this script;
#       a line "PREFIX ?? <dir>/" allows any untracked path under <dir>/, a line with a status code allows that exact line;
#   (3) start checks HEAD = e2589cb (the M0 records commit) and HEAD:S4 = F3 tree; end checks HEAD^ = e2589cb and that
#       HEAD's subject is the M1a record commit subject given in brief section 8;
#   (4) the registries/s4r7 manifest check is run by recheck_s4r7_r8m1.py (new), which imports the committed
#       check_s4r7_manifests_r8.py functions and writes a new file;
#   (5) the sha256 of both allow-list data files and of the M1a brief is recorded in the output file.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate4_r8m1.sh p05-s4r8 GATE_R8_M1a.txt start testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt TMP_COUNT TMP_SHA256
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate4_r8m1.sh p05-s4r8 GATE_R8_M1a_END.txt end testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt TMP_COUNT TMP_SHA256 START_TMP_COUNT START_TMP_SHA256
# Each output line is PASS or FAIL (counted), or RECORD.  Last line: FAILS=<n>.  The output name must be a plain file name;
# an existing output file is refused (U17).  The temp-directory snapshot is taken by the caller (read-only inline commands).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate4_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
ALLOW=${4:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate4_r8m1: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
case "$MODE" in
    start|end) ;;
    *) echo "gate4_r8m1: REFUSED: mode must be start or end" >&2; exit 2 ;;
esac
case "$ALLOW" in
    testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt|testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt) ;;
    *) echo "gate4_r8m1: REFUSED: allow-list must be one of the two M1a data files" >&2; exit 2 ;;
esac
if [ "$MODE" = start ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt ]; then
    echo "gate4_r8m1: REFUSED: start mode needs the start allow-list" >&2; exit 2
fi
if [ "$MODE" = end ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt ]; then
    echo "gate4_r8m1: REFUSED: end mode needs the end allow-list" >&2; exit 2
fi
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate4_r8m1: REFUSED: exists (U17): $OUT" >&2; exit 2; }
TC=${5:-}
TS=${6:-}
SC=${7:-}
SS=${8:-}
if [ "$MODE" = end ]; then
    [ -n "$SC" ] && [ -n "$SS" ] || { echo "gate4_r8m1: REFUSED: end mode needs the start tmp count and sha256" >&2; exit 2; }
fi
REC_MSG="P05-S4 R8 M1a prep on F3: dbg strip equivalence (E8-9), drivers, F2-F3 line and call-sequence maps, M1b/M1c pre-registration, dry-run; M0 report wording (U137). awaiting user review"
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a gate4 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- allow-list data files: sha256 recorded (U143) ----
record ALLOW_FILE "$ALLOW"
record ALLOW_FILE_SHA256 "$(sha256sum "$ALLOW" | cut -d' ' -f1)"
record BRIEF_M1A_SHA256 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md | cut -d' ' -f1)"

# ---- HEAD (mode dependent) ----
if [ "$MODE" = start ]; then
    check HEAD e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD 2>&1)"
else
    check HEAD_PARENT e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD^ 2>&1)"
    check HEAD_SUBJECT "$REC_MSG" "$(git log -1 --format=%s 2>&1)"
fi

# ---- trees and diff (LC_ALL=C sort, U129(b)) ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"

# ---- judge and registries (unchanged) ----
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"

# ---- registries/s4r8 manifest (written by M0; covers the M0 copies and ERRATA_8 as of the M0 closing) ----
S4R8_TOTAL=$(grep -c . checkpoints/p05/registries/s4r8/SHA256SUMS.txt 2>&1)
S4R8_OK=$(cd checkpoints/p05/registries/s4r8 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S4R8_M0_SHA256SUMS_OK_LINES_EQ_TOTAL "$S4R8_TOTAL" "$S4R8_OK"

# ---- registries/s3r4c5 manifest (unchanged) ----
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"

# ---- registries/s4r7 manifests: classified check (U121, U128, U129), repeated read only ----
SR7=S4R7_RECHECK_R8_M1A_START.tsv
[ "$MODE" = end ] && SR7=S4R7_RECHECK_R8_M1A_END.tsv
test ! -e "$EV/$SR7" || { echo "gate4_r8m1: REFUSED: exists (U17): $SR7" >&2; exit 2; }
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1.py "$SR7" > "$EV/tmp/recheck_stdout_$MODE.txt" 2>&1
S4R7_LINE=$(tail -n 1 "$EV/$SR7" 2>&1)
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- the allowed status lines (U143) ----
# Read the data file: entries "PREFIX <status> <dir>" allow any untracked/modified path under <dir>; other non-empty,
# non-comment lines allow exactly that status line.  The check passes iff every status line matches an entry.
ALLOWED_TXT=$(grep -v '^#' "$ALLOW" | grep -v '^[[:space:]]*$')
ST=$(git status --short 2>&1)
BAD=$(printf '%s\n' "$ST" | awk -v allow="$ALLOWED_TXT" '
    BEGIN {
        n = split(allow, lines, "\n")
        for (i = 1; i <= n; i++) {
            l = lines[i]
            if (l ~ /^PREFIX /) { pre[++np] = substr(l, 8) }
            else { exact[l] = 1 }
        }
    }
    length($0) == 0 { next }
    {
        ok = ($0 in exact)
        if (!ok) for (j = 1; j <= np; j++) {
            # a prefix rule is "<status> <dir>/" : the status code and the path prefix must both match
            split(pre[j], pr, " "); s = pr[1]; d = pr[2]
            if (substr($0, 1, 2) == s && substr($0, 4, length(d)) == d) { ok = 1; break }
        }
        if (!ok) print "NOT_ALLOWED " $0
    }')
check GIT_STATUS_ALLOWED_ONLY "" "$BAD"
record GIT_STATUS "$ST"

# ---- top-level snapshot of the system temp directory (taken by the caller; compared with the start value at end) ----
if [ "$MODE" = start ]; then
    check TMP_SNAPSHOT_ARGS_GIVEN yes "$( [ -n "$TC" ] && [ -n "$TS" ] && echo yes || echo no)"
    record TMP_COUNT_START "$TC"
    record TMP_SHA256_START "$TS"
else
    check TMP_COUNT_END_EQ_START "$SC" "$TC"
    check TMP_SHA256_END_EQ_START "$SS" "$TS"
fi

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate4_r8m1: $MODE FAILS=$FAILS -> $OUT"
exit 0
