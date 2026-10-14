#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate6_r8m1a3.sh -- P05-S4 R8 M1a CONT2 gate (start and end), brief CONT2 section 3 and U150.  New file.
# Copied from gate5_r8m1a2.sh (committed, not modified) and changed as follows:
#   (1) the allow-list data files are gate_allow_r8m1a3_{start,end}.txt;
#   (2) the recheck script is recheck_s4r7_r8m1a3.py and the output names are S4R7_RECHECK_R8_M1A3_(START|END).tsv;
#   (3) the M1a CONT1 sha256 list of brief CONT2 section 3 is checked (CONT1 report is now a file; its sha256 is recorded);
#   (4) the brief CONT2 itself is recorded (sha256, not compared: it is written by this round).
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate6_r8m1a3.sh p05-s4r8 GATE_R8_M1a3.txt start testing/d003/stage_s4r8/gate_allow_r8m1a3_start.txt TMP_COUNT TMP_SHA256
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate6_r8m1a3.sh p05-s4r8 GATE_R8_M1a3_END.txt end testing/d003/stage_s4r8/gate_allow_r8m1a3_end.txt TMP_COUNT TMP_SHA256 START_TMP_COUNT START_TMP_SHA256
# Output: one line per check (PASS / FAIL) or RECORD; last line FAILS=<n>.  An existing output file is refused (U17).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate6_r8m1a3: first argument must be p05-s4r8" >&2; exit 2; }
OUTNAME=${2:-}
MODE=${3:-}
ALLOW=${4:-}
case "$OUTNAME" in
    ""|*/*|*..*) echo "gate6_r8m1a3: REFUSED: output name must be a plain file name" >&2; exit 2 ;;
esac
case "$MODE" in
    start|end) ;;
    *) echo "gate6_r8m1a3: REFUSED: mode must be start or end" >&2; exit 2 ;;
esac
case "$ALLOW" in
    testing/d003/stage_s4r8/gate_allow_r8m1a3_start.txt|testing/d003/stage_s4r8/gate_allow_r8m1a3_end.txt) ;;
    *) echo "gate6_r8m1a3: REFUSED: allow-list must be one of the two M1a CONT2 data files" >&2; exit 2 ;;
esac
if [ "$MODE" = start ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a3_start.txt ]; then
    echo "gate6_r8m1a3: REFUSED: start mode needs the start allow-list" >&2; exit 2
fi
if [ "$MODE" = end ] && [ "$ALLOW" != testing/d003/stage_s4r8/gate_allow_r8m1a3_end.txt ]; then
    echo "gate6_r8m1a3: REFUSED: end mode needs the end allow-list" >&2; exit 2
fi
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || { echo "gate6_r8m1a3: REFUSED: exists (U17): $OUT" >&2; exit 2; }
TC=${5:-}
TS=${6:-}
SC=${7:-}
SS=${8:-}
if [ "$MODE" = end ]; then
    [ -n "$SC" ] && [ -n "$SS" ] || { echo "gate6_r8m1a3: REFUSED: end mode needs the start tmp count and sha256" >&2; exit 2; }
fi
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT2 gate6 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- allow-list data file and the briefs: sha256 recorded ----
record ALLOW_FILE "$ALLOW"
record ALLOW_FILE_SHA256 "$(sha256sum "$ALLOW" | cut -d' ' -f1)"
record BRIEF_M1A_CONT2_SHA256 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2.md | cut -d' ' -f1)"

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

# ---- ERRATA_8.txt: start = whole file (23046 bytes, 93b2aba6...) before this round's append;
#      end = first 23046 bytes still 93b2aba6... (append only; U150(a), brief CONT2 section 3) ----
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
if [ "$MODE" = start ]; then
    check ERRATA_8_WHOLE_FILE_SHA256_BEFORE_APPEND 93b2aba6037d4b171e6b0c1f70d18fbbbc1d1b7e65b33bbd1ffff38e31f5a109 "$(sha256sum "$ERR" 2>&1 | cut -d' ' -f1)"
    check ERRATA_8_BYTES_BEFORE_APPEND 23046 "$(wc -c < "$ERR" 2>&1 | tr -d ' ')"
else
    check ERRATA_8_FIRST_23046_BYTES_SHA256 93b2aba6037d4b171e6b0c1f70d18fbbbc1d1b7e65b33bbd1ffff38e31f5a109 "$(head -c 23046 "$ERR" | sha256sum | cut -d' ' -f1)"
fi
check ERRATA_8_FIRST_13990_BYTES_SHA256 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551 "$(head -c 13990 "$ERR" | sha256sum | cut -d' ' -f1)"
check ERRATA_8_FIRST_20474_BYTES_SHA256 6e134abadbc86ffe24ce4f3bb156f8c7290c107369af289094b675e4b4498f22 "$(head -c 20474 "$ERR" | sha256sum | cut -d' ' -f1)"

# ---- RULINGS.tsv: start = whole file 55304 bytes a3030e47... (before this round's append);
#      end = HEAD version (48880 bytes) is a byte prefix; first 55304 bytes still a3030e47... (append only) ----
RUL=checkpoints/p05/registries/RULINGS.tsv
if [ "$MODE" = start ]; then
    check RULINGS_WHOLE_FILE_SHA256_BEFORE_APPEND a3030e47509a519213e46cd57b4170dbfbbb899269c1b2b3e1e3eb3eaef156df "$(sha256sum "$RUL" 2>&1 | cut -d' ' -f1)"
    check RULINGS_BYTES_BEFORE_APPEND 55304 "$(wc -c < "$RUL" 2>&1 | tr -d ' ')"
else
    git show HEAD:$RUL > "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3.tsv" 2>&1
    _hb=$(wc -c < "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3.tsv" | tr -d ' ')
    _pre=$(head -c "$_hb" "$RUL" | sha256sum | cut -d' ' -f1)
    _hsha=$(sha256sum "$EV/tmp/RULINGS_HEAD_for_prefix_check_r8m1a3.tsv" | cut -d' ' -f1)
    check RULINGS_HEAD_IS_BYTE_PREFIX "$_hsha" "$_pre"
    check RULINGS_FIRST_55304_BYTES_SHA256 a3030e47509a519213e46cd57b4170dbfbbb899269c1b2b3e1e3eb3eaef156df "$(head -c 55304 "$RUL" | sha256sum | cut -d' ' -f1)"
fi

# ---- registries/s4r8 manifest (U150(a)): ERRATA_8 line by prefix (13990 bytes), the other lines by sha256sum -c from stdin ----
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
SR7=S4R7_RECHECK_R8_M1A3_START.tsv
[ "$MODE" = end ] && SR7=S4R7_RECHECK_R8_M1A3_END.tsv
test ! -e "$EV/$SR7" || { echo "gate6_r8m1a3: REFUSED: exists (U17): $SR7" >&2; exit 2; }
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a3.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a3_$MODE.txt" 2>&1
S4R7_LINE=$(tail -n 1 "$EV/$SR7" 2>&1)
check S4R7_MANIFESTS "fails=0" "$S4R7_LINE"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- uncommitted M1a/CONT1 files not touched by this round: sha256 (brief CONT2 section 3) ----
check SHA_REPORT_M0_UNCHANGED 1fc08a1f5dbf1340d3500979980a4f808b141515c8e1814c23da796e7deb0a0f "$(sha256sum checkpoints/p05/P05_S4R8_REPORT_M0.md 2>&1 | cut -d' ' -f1)"
check SHA_REPORT_M1A 2b1c2de19a39c7e44c6cea75e55963bb5995849ee1d19a77d1ad7b2248676c04 "$(sha256sum checkpoints/p05/P05_S4R8_REPORT_M1a.md 2>&1 | cut -d' ' -f1)"
check SHA_BRIEF_M1A a84da018b782f52e73a533d79d2224058e48d924bf817df869a94e5656686ec3 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md 2>&1 | cut -d' ' -f1)"
record SHA_BRIEF_M1A_CONT1 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md 2>&1 | cut -d' ' -f1)"
check SHA_gate4_r8m1 ae80a3c176cb6121c486df9fb36cd795552de8913cef8fcefdebdea700d3bece "$(sha256sum testing/d003/stage_s4r8/gate4_r8m1.sh 2>&1 | cut -d' ' -f1)"
check SHA_map_f2_f3_r8m1 746f5eb5e68835d658e842fbefa21740587b2f1a244d32860bc24d363b57e2e4 "$(sha256sum testing/d003/stage_s4r8/map_f2_f3_r8m1.py 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a_start 7df7f53e43208d0df9838a1a8eaaa8970e5e9abeb77a81511351deb57ba77128 "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a_start.txt 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a_end c0a0621cb2deb9457fe2a4f7583bb4444917ab56d6e57fe94931ac6ffc9031dc "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a_end.txt 2>&1 | cut -d' ' -f1)"
check SHA_gate5_r8m1a2 4824e584291d08e76217d5636c8683c72b92ad6d68c74f7db163947ccdf14230 "$(sha256sum testing/d003/stage_s4r8/gate5_r8m1a2.sh 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a2_start 04ce8778d414157807cbb3213f3e81d12b226bc3bff3c04d9f76f41a5a4861af "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a2_start.txt 2>&1 | cut -d' ' -f1)"
check SHA_gate_allow_r8m1a2_end 7daf90aceb3b66f07cafd659608c0906e7becb98d43e35749cea11f195e31b16 "$(sha256sum testing/d003/stage_s4r8/gate_allow_r8m1a2_end.txt 2>&1 | cut -d' ' -f1)"
check SHA_map_f2_f3_r8m1a2 8e4910b8b9fb848a8e88f58086551ea77c3dbd9b042d6bc992bc4bdf842582da "$(sha256sum testing/d003/stage_s4r8/map_f2_f3_r8m1a2.py 2>&1 | cut -d' ' -f1)"
check SHA_recheck_s4r7_r8m1a2 b6db2d12cadc9def3fb49c7d01dbaedc697829d1bf8b663a9ef8bf72b89e5c51 "$(sha256sum testing/d003/stage_s4r8/recheck_s4r7_r8m1a2.py 2>&1 | cut -d' ' -f1)"
check SHA_runner_diff_r8m1a2 58c6296ed77b5cd907e8ed54da6a34f91f525955669235530796fc757e02f32b "$(sha256sum testing/d003/stage_s4r8/runner_diff_r8m1a2.sh 2>&1 | cut -d' ' -f1)"
check SHA_export_f2_s4cpp_r8m1a2 66ba39e9715ef9693c82e9100a8dfd6a5213c9daa75f2b036f37e2349d0e47b2 "$(sha256sum testing/d003/stage_s4r8/export_f2_s4cpp_r8m1a2.sh 2>&1 | cut -d' ' -f1)"
check SHA_LINEMAP_F2_F3_R8_M1a2 9888edb28a5e2006445be68433fb5f2a5fc8282e44c7bfdecd2cdc1d66ad8757 "$(sha256sum checkpoints/p05/evidence/p05-s4r8/LINEMAP_F2_F3_R8_M1a2.tsv 2>&1 | cut -d' ' -f1)"
check SHA_EXPECT_LINEMAP_R8_M1a2 bf71ccdce7bb3e4d569119dc785d35d7103d2bffc93ed1b724f6380c1ac2e24b "$(sha256sum checkpoints/p05/evidence/p05-s4r8/EXPECT_LINEMAP_R8_M1a2.txt 2>&1 | cut -d' ' -f1)"
check SHA_GATE_R8_M1a2 4d4b51b60b1b72c5152a8fcee94373ff38cf3fc55ef1de563b2c43765aaa5454 "$(sha256sum checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a2.txt 2>&1 | cut -d' ' -f1)"
check SHA_GATE_R8_M1a2_R2 155ecbfd3c3d3e2435409253022905b58683f51327f339e7ae1caf740213339e "$(sha256sum checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a2_R2.txt 2>&1 | cut -d' ' -f1)"
check SHA_RUNNER_DIFF_R8_M1a 119722a7f7349acc19fbe45b5fd34bd57a587dccae184475e5e5db1f2ef79283 "$(sha256sum checkpoints/p05/evidence/p05-s4r8/RUNNER_DIFF_R8_M1a.txt 2>&1 | cut -d' ' -f1)"
check SHA_F2_S4CPP_TXT e287fbc70025e2dcda66c3aa3e9b48df585a4e279c3fcd7620eb19003880ce87 "$(sha256sum checkpoints/p05/evidence/p05-s4r8/F2_S4.cpp.txt 2>&1 | cut -d' ' -f1)"
check SHA_PRERUN_PREFIX_1926 38e3f1652908aa080c20218dd1439270c5a884c5cd98abe0c082f56e6976e248 "$(head -c 1926 checkpoints/p05/evidence/p05-s4r8/PRERUN_CHECKS_R8_M1a.txt | sha256sum | cut -d' ' -f1)"
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
echo "gate6_r8m1a3: $MODE FAILS=$FAILS -> $OUT"
exit 0
