#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate5_r8m1a2.sh -- P05-S4 R8 M1a CONT1 gate (start and end), brief CONT1 section 3 and U150.  New file.
# Copied from gate4_r8m1.sh (committed, not modified) and changed as follows (U150(c)):
#   (1) the allow-list data files are gate_allow_r8m1a2_{start,end}.txt;
#   (2) end mode runs BEFORE the commit: HEAD must still be e2589cb (U150(b)); the check of HEAD^ and of the commit subject
#       is removed (those are written to FINAL_GIT_R8_M1a2.txt after the commit);
#   (3) ERRATA_8.txt: start mode checks the whole-file sha256 6e134aba... (20474 bytes); end mode checks that the first
#       20474 bytes still hash to 6e134aba... (append-only, U150(a));
#   (4) RULINGS.tsv: end mode checks that the HEAD version is a byte prefix of the working file (append-only);
#   (5) the s4r8 manifest check is U150(a): the ERRATA_8 line by prefix (first 13990 bytes = 72dc6aed...),
#       the other 24 lines by sha256sum -c from stdin (no temporary file);
#   (6) the sha256 of the uncommitted M1a files that this round does not touch is checked (brief section 3), in both modes;
#   (7) the sha256 of the other 11 *_r8m1.* scripts is only recorded, not compared (brief section 3).
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate5_r8m1a2.sh p05-s4r8 GATE_R8_M1a2.txt start testing/d003/stage_s4r8/gate_allow_r8m1a2_start.txt TMP_COUNT TMP_SHA256
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate5_r8m1a2.sh p05-s4r8 GATE_R8_M1a2_END.txt end testing/d003/stage_s4r8/gate_allow_r8m1a2_end.txt TMP_COUNT TMP_SHA256 START_TMP_COUNT START_TMP_SHA256
# Output: one line per check (PASS / FAIL) or RECORD; last line FAILS=<n>.  An existing output file is refused (U17).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate5_r8m1a2: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
ALLOW=${4:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate5_r8m1a2: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
case "$MODE" in
    start|end) ;;
    *) echo "gate5_r8m1a2: REFUSED: mode must be start or end" >&2; exit 2 ;;
esac
case "$ALLOW" in
    testing/d003/stage_s4r8/gate_allow_r8m1a2_start.txt|testing/d003/stage_s4r8/gate_allow_r8m1a2_end.txt) ;;
    *) echo "gate5_r8m1a2: REFUSED: allow-list must be one of the two M1a CONT1 data files" >&2; exit 2 ;;
esac
if [ "$MODE" = start ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a2_start.txt ]; then
    echo "gate5_r8m1a2: REFUSED: start mode needs the start allow-list" >&2; exit 2
fi
if [ "$MODE" = end ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a2_end.txt ]; then
    echo "gate5_r8m1a2: REFUSED: end mode needs the end allow-list" >&2; exit 2
fi
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate5_r8m1a2: REFUSED: exists (U17): $OUT" >&2; exit 2; }
TC=${5:-}
TS=${6:-}
SC=${7:-}
SS=${8:-}
if [ "$MODE" = end ]; then
    [ -n "$SC" ] && [ -n "$SS" ] || { echo "gate5_r8m1a2: REFUSED: end mode needs the start tmp count and sha256" >&2; exit 2; }
fi
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT1 gate5 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- allow-list data files and the brief: sha256 recorded ----
record ALLOW_FILE "$ALLOW"
record ALLOW_FILE_SHA256 "$(sha256sum "$ALLOW" | cut -d' ' -f1)"
record BRIEF_M1A_CONT1_SHA256 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md | cut -d' ' -f1)"

# ---- HEAD: start and end both require e2589cb (U150(b)) ----
check HEAD e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD 2>&1)"

# ---- trees and diff (LC_ALL=C sort) ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"

# ---- judge and registry ----
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"

# ---- ERRATA_8.txt: start = whole file 6e134aba (20474 bytes); end = first 20474 bytes still 6e134aba (append only) ----
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
if [ "$MODE" = start ]; then
    check ERRATA_8_WHOLE_FILE_SHA256_BEFORE_APPEND 6e134abadbc86ffe24ce4f3bb156f8c7290c107369af289094b675e4b4498f22 "$(sha256sum "$ERR" 2>&1 | cut -d' ' -f1)"
    check ERRATA_8_BYTES_BEFORE_APPEND 20474 "$(wc -c < "$ERR" 2>&1 | tr -d ' ')"
else
    check ERRATA_8_FIRST_20474_BYTES_SHA256 6e134abadbc86ffe24ce4f3bb156f8c7290c107369af289094b675e4b4498f22 "$(head -c 20474 "$ERR" | sha256sum | cut -d' ' -f1)"
fi

# ---- RULINGS.tsv: end mode = HEAD version is a byte prefix of the working file (append only) ----
RUL=checkpoints/p05/registries/RULINGS.tsv
if [ "$MODE" = end ]; then
    git show HEAD:$RUL > "$EV/tmp/RULINGS_HEAD_for_prefix_check.tsv" 2>&1
    _hb=$(wc -c < "$EV/tmp/RULINGS_HEAD_for_prefix_check.tsv" | tr -d ' ')
    _pre=$(head -c "$_hb" "$RUL" | sha256sum | cut -d' ' -f1)
    _hsha=$(sha256sum "$EV/tmp/RULINGS_HEAD_for_prefix_check.tsv" | cut -d' ' -f1)
    check RULINGS_HEAD_IS_BYTE_PREFIX "$_hsha" "$_pre"
fi

# ---- registries/s4r8 manifest (U150(a)) ----
S4R8_DIR=checkpoints/p05/registries/s4r8
ERR_PREFIX_SHA=$(head -c 13990 "$S4R8_DIR/ERRATA_8.txt" | sha256sum | cut -d' ' -f1)
check S4R8_ERRATA_8_PREFIX_13990 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551 "$ERR_PREFIX_SHA"
S4R8_TOTAL=$(grep -c . "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_NONERR=$(grep -vc 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_OK=$(grep -v 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" | (cd "$S4R8_DIR" && sha256sum -c - 2>&1) | grep -c ': OK$')
check S4R8_OTHER_LINES_ALL_OK "$S4R8_NONERR" "$S4R8_OK"
check S4R8_TOTAL_LINES_25 25 "$S4R8_TOTAL"

# ---- registries/s3r4c5 manifest ----
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"

# ---- registries/s4r7 manifests: classified recheck (U121, U128, U129), read only, new output name ----
SR7=S4R7_RECHECK_R8_M1A2_START.tsv
[ "$MODE" = end ] && SR7=S4R7_RECHECK_R8_M1A2_END.tsv
test ! -e "$EV/$SR7" || { echo "gate5_r8m1a2: REFUSED: exists (U17): $SR7" >&2; exit 2; }
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a2.py "$SR7" > "$EV/tmp/recheck_stdout_$MODE.txt" 2>&1
S4R7_LINE=$(tail -n 1 "$EV/$SR7" 2>&1)
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- uncommitted M1a files not touched by this round: sha256 (brief section 3) ----
check SHA_REPORT_M0_UNCHANGED 1fc08a1f5dbf1340d3500979980a4f808b141515c8e1814c23da796e7deb0a0f "$(sha256sum checkpoints/p05/P05_S4R8_REPORT_M0.md 2>&1 | cut -d' ' -f1)"
check SHA_REPORT_M1A 2b1c2de19a39c7e44c6cea75e55963bb5995849ee1d19a77d1ad7b2248676c04 "$(sha256sum checkpoints/p05/P05_S4R8_REPORT_M1a.md 2>&1 | cut -d' ' -f1)"
check SHA_BRIEF_M1A a84da018b782f52e73a533d79d2224058e48d924bf817df869a94e5656686ec3 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md 2>&1 | cut -d' ' -f1)"
check SHA_gate4_r8m1 ae80a3c176cb6121c486df9fb36cd795552de8913cef8fcefdebdea700d3bece "$(sha256sum testing/d003/stage_s4r8/gate4_r8m1.sh 2>&1 | cut -d' ' -f1)"
check SHA_map_f2_f3_r8m1 746f5eb5e68835d658e842fbefa21740587b2f1a244d32860bc24d363b57e2e4 "$(sha256sum testing/d003/stage_s4r8/map_f2_f3_r8m1.py 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a_start 7df7f53e43208d0df9838a1a8eaaa8970e5e9abeb77a81511351deb57ba77128 "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a_end c0a0621cb2deb9457fe2a4f7583bb4444917ab56d6e57fe94931ac6ffc9031dc "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt 2>&1 | cut -d' ' -f1)"
for _f in testing/d003/stage_s4r8/*_r8m1.*; do
    record "SHA_OTHER_R8M1 $_f" "$(sha256sum "$_f" 2>&1 | cut -d' ' -f1)"
done

# ---- git status: every line must match the allow-list data file (U143) ----
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
            split(pre[j], pr, " "); s = pr[1]; d = pr[2]
            if (substr($0, 1, 2) == s && substr($0, 4, length(d)) == d) { ok = 1; break }
        }
        if (!ok) print "NOT_ALLOWED " $0
    }')
check GIT_STATUS_ALLOWED_ONLY "" "$BAD"
record GIT_STATUS "$ST"

# ---- temp-directory snapshot (taken by the caller) ----
if [ "$MODE" = start ]; then
    check TMP_SNAPSHOT_ARGS_GIVEN yes "$( [ -n "$TC" ] && [ -n "$TS" ] && echo yes || echo no)"
    record TMP_COUNT_START "$TC"
    record TMP_SHA256_START "$TS"
else
    check TMP_COUNT_END_EQ_START "$SC" "$TC"
    check TMP_SHA256_END_EQ_START "$SS" "$TS"
fi

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate5_r8m1a2: $MODE FAILS=$FAILS -> $OUT"
exit 0
