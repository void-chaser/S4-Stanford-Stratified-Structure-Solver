#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate7_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b gate (start and end), brief CONT2b section 3.  New file.
# Copied from gate6_r8m1a3.sh (committed, not modified) and changed as follows:
#   (1) the allow-list data files are gate_allow_r8m1a3b_{start,end}.txt; outputs GATE_R8_M1a3b.txt / GATE_R8_M1a3b_END.txt;
#   (2) the recheck script is recheck_s4r7_r8m1a3b.py; its outputs are S4R7_RECHECK_R8_M1A3B_(START|END).tsv;
#   (3) the uncommitted-file and evidence sha256 list is read from gate_hashes_r8m1a3b.txt (brief CONT2b section 3), not written here;
#   (4) the CONT2b brief is recorded (sha256, not compared: this round writes it);
#   (5) the ERRATA_8 and RULINGS checks are the CONT2b values (ERRATA_8 28653 bytes, RULINGS 59783 bytes; end: prefix checks).
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate7_r8m1a3b.sh p05-s4r8 GATE_R8_M1a3b.txt start testing/d003/stage_s4r8/gate_allow_r8m1a3b_start.txt TMP_COUNT TMP_SHA256
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate7_r8m1a3b.sh p05-s4r8 GATE_R8_M1a3b_END.txt end testing/d003/stage_s4r8/gate_allow_r8m1a3b_end.txt TMP_COUNT TMP_SHA256 START_TMP_COUNT START_TMP_SHA256
# Output: one line per check (PASS / FAIL) or RECORD; last line FAILS=<n>.  An existing output file is refused (U17).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate7_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
ALLOW=${4:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate7_r8m1a3b: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
case "$MODE" in
    start|end) ;;
    *) echo "gate7_r8m1a3b: REFUSED: mode must be start or end" >&2; exit 2 ;;
esac
case "$ALLOW" in
    testing/d003/stage_s4r8/gate_allow_r8m1a3b_start.txt|testing/d003/stage_s4r8/gate_allow_r8m1a3b_end.txt) ;;
    *) echo "gate7_r8m1a3b: REFUSED: allow-list must be one of the two M1a CONT2b data files" >&2; exit 2 ;;
esac
if [ "$MODE" = start ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a3b_start.txt ]; then
    echo "gate7_r8m1a3b: REFUSED: start mode needs the start allow-list" >&2; exit 2
fi
if [ "$MODE" = end ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a3b_end.txt ]; then
    echo "gate7_r8m1a3b: REFUSED: end mode needs the end allow-list" >&2; exit 2
fi
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate7_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }
TC=${5:-}
TS=${6:-}
SC=${7:-}
SS=${8:-}
if [ "$MODE" = end ]; then
    [ -n "$SC" ] && [ -n "$SS" ] || { echo "gate7_r8m1a3b: REFUSED: end mode needs the start tmp count and sha256" >&2; exit 2; }
fi
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT2b gate7 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- allow-list data file and this round's brief: sha256 recorded ----
record ALLOW_FILE "$ALLOW"
record ALLOW_FILE_SHA256 "$(sha256sum "$ALLOW" | cut -d' ' -f1)"
record BRIEF_M1A_CONT2B_SHA256 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2b.md 2>&1 | cut -d' ' -f1)"

# ---- HEAD: start and end both require e2589cb ----
check HEAD e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD 2>&1)"

# ---- trees and diff (LC_ALL=C sort) ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"

# ---- judge and registry ----
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"

# ---- ERRATA_8.txt: start = whole file 28653 bytes 16024140... (before this round's append);
#      end = first 28653 bytes still 16024140... (append only) ----
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
if [ "$MODE" = start ]; then
    check ERRATA_8_WHOLE_FILE_SHA256_BEFORE_APPEND 16024140abb1bbecfd34fc35471d74b3a94d79e75c3d50f44a98b3b43e8532b0 "$(sha256sum "$ERR" 2>&1 | cut -d' ' -f1)"
    check ERRATA_8_BYTES_BEFORE_APPEND 28653 "$(wc -c < "$ERR" 2>&1 | tr -d ' ')"
else
    check ERRATA_8_FIRST_28653_BYTES_SHA256 16024140abb1bbecfd34fc35471d74b3a94d79e75c3d50f44a98b3b43e8532b0 "$(head -c 28653 "$ERR" | sha256sum | cut -d' ' -f1)"
fi
check ERRATA_8_FIRST_13990_BYTES_SHA256 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551 "$(head -c 13990 "$ERR" | sha256sum | cut -d' ' -f1)"
check ERRATA_8_FIRST_23046_BYTES_SHA256 93b2aba6037d4b171e6b0c1f70d18fbbbc1d1b7e65b33bbd1ffff38e31f5a109 "$(head -c 23046 "$ERR" | sha256sum | cut -d' ' -f1)"

# ---- RULINGS.tsv: start = whole file 59783 bytes a314446b... (before this round's append);
#      end = HEAD version (48880 bytes) is a byte prefix; first 59783 bytes still a314446b... (append only) ----
RUL=checkpoints/p05/registries/RULINGS.tsv
if [ "$MODE" = start ]; then
    check RULINGS_WHOLE_FILE_SHA256_BEFORE_APPEND a314446b80e82dd47c09ff70c4b2f05b92c62f530367fe14ee6b1fc9a932e4f0 "$(sha256sum "$RUL" 2>&1 | cut -d' ' -f1)"
    check RULINGS_BYTES_BEFORE_APPEND 59783 "$(wc -c < "$RUL" 2>&1 | tr -d ' ')"
else
    git show HEAD:$RUL > "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3b.tsv" 2>&1
    _hb=$(wc -c < "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3b.tsv" | tr -d ' ')
    _pre=$(head -c "$_hb" "$RUL" | sha256sum | cut -d' ' -f1)
    _hsha=$(sha256sum "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3b.tsv" | cut -d' ' -f1)
    check RULINGS_HEAD_IS_BYTE_PREFIX "$_hsha" "$_pre"
    check RULINGS_FIRST_59783_BYTES_SHA256 a314446b80e82dd47c09ff70c4b2f05b92c62f530367fe14ee6b1fc9a932e4f0 "$(head -c 59783 "$RUL" | sha256sum | cut -d' ' -f1)"
fi
check RULINGS_FIRST_55304_BYTES_SHA256 a3030e47509a519213e46cd57b4170dbfbbb899269c1b2b3e1e3eb3eaef156df "$(head -c 55304 "$RUL" | sha256sum | cut -d' ' -f1)"

# ---- PRERUN_CHECKS_R8_M1a.txt: first 2562 bytes unchanged (append only) ----
check PRERUN_PREFIX_2562 3b25492ca41c187009a467e96720e88050e7e33e45d016b01346d8fbb80216eb "$(head -c 2562 checkpoints/p05/evidence/p05-s4r8/PRERUN_CHECKS_R8_M1a.txt | sha256sum | cut -d' ' -f1)"

# ---- registries/s4r8 manifest: ERRATA_8 line by prefix (13990 bytes), the other lines by sha256sum -c ----
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
SR7=S4R7_RECHECK_R8_M1A3B_START.tsv
[ "$MODE" = end ] && SR7=S4R7_RECHECK_R8_M1A3B_END.tsv
test ! -e "$EV/$SR7" || { echo "gate7_r8m1a3b: REFUSED: exists (U17): $SR7" >&2; exit 2; }
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a3b.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a3b_$MODE.txt" 2>&1
S4R7_LINE=$(tail -n 1 "$EV/$SR7" 2>&1)
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- uncommitted and evidence files: sha256 table (brief CONT2b section 3); every row must match ----
HT=testing/d003/stage_s4r8/gate_hashes_r8m1a3b.txt
grep -v '^#' "$HT" | grep -v '^[[:space:]]*$' | sed 's|@S4R8DIR@|testing/d003/stage_s4r8/|' > "$EV/tmp/hashes_r8m1a3b_$MODE.txt"
while read -r _h _p; do
    _a=$(sha256sum "$_p" 2>&1 | cut -d' ' -f1)
    if [ "$_h" = "$_a" ]; then _r=PASS; else _r=FAIL; FAILS=$((FAILS + 1)); fi
    printf '%s\tHASH_TABLE %s\texpected=%s\tactual=%s\n' "$_r" "$_p" "$_h" "$_a" >> "$OUT"
done < "$EV/tmp/hashes_r8m1a3b_$MODE.txt"
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

# ---- temp-directory snapshot (taken by the caller, form (5)) ----
if [ "$MODE" = start ]; then
    check TMP_SNAPSHOT_ARGS_GIVEN yes "$( [ -n "$TC" ] && [ -n "$TS" ] && echo yes || echo no)"
    record TMP_COUNT_START "$TC"
    record TMP_SHA256_START "$TS"
else
    check TMP_COUNT_END_EQ_START "$SC" "$TC"
    check TMP_SHA256_END_EQ_START "$SS" "$TS"
fi

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate7_r8m1a3b: $MODE FAILS=$FAILS -> $OUT"
exit 0
