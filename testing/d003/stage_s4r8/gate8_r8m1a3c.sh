#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate8_r8m1a3c.sh -- P05-S4 R8 M1a CONT2c gate, modes start / endA / startB / endB.  New file (gate7_r8m1a3b.sh not modified).
# Usage (through safe_run; every argument is checked before any file is written; brief CONT2c A1 and section 6):
#   sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 OUT start    TC TS
#   sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 OUT endA     START_FILE TC TS
#   sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 OUT startB   TC TS
#   sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 OUT endB     STARTB_FILE TC TS
# OUT is GATE_R8_M1a3c_<name>.txt and must not exist (U17).  TC = entry count of the temporary area, TS = its sha256 (form 5 snapshot).
# The recheck output name is S4R7_RECHECK_ + upper-case OUT stem + .tsv (GATE_R8_M1a3c_START.txt -> S4R7_RECHECK_GATE_R8_M1A3C_START.tsv).
# start/endA read the sha256 table gate_hashes_r8m1a3c.txt; the start values for endA/endB come from the start file (U169).
# Output: one PASS/FAIL line per check, RECORD lines, last line FAILS=<n>.  Exit 2 = refused before any file is written.
set -u
refuse() { echo "gate8_r8m1a3c: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8 ] || refuse "first argument must be p05-s4r8"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1a3c_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a3c_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
case "$OUTSTEM" in
    GATE_R8_M1a3c_) refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
case "$MODE" in
    start|startB)
        [ $# -eq 5 ] || refuse "$MODE takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    endA|endB)
        [ $# -eq 6 ] || refuse "$MODE takes START_FILE TC TS"
        STARTF=${4:-}; TC=${5:-}; TS=${6:-} ;;
    *) refuse "mode must be start, endA, startB or endB" ;;
esac
case "$TC" in
    ''|*[!0-9]*) refuse "TC must be digits" ;;
esac
case "$TS" in
    ''|*[!0-9a-f]*) refuse "TS must be lowercase hex" ;;
esac
[ "${#TS}" = 64 ] || refuse "TS must be 64 characters"
case "$MODE" in
    endA) WANT="gate8 (start) ->" ;;
    endB) WANT="gate8 (startB) ->" ;;
    *) WANT="" ;;
esac
if [ -n "$WANT" ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    _h=$(head -n 1 "$STARTF")
    case "$_h" in
        *"$WANT"*) ;;
        *) refuse "start file header does not match mode $MODE" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi
case "$MODE" in
    start) ALLOW=testing/d003/stage_s4r8/gate_allow_r8m1a3c_start.txt ;;
    endA) ALLOW=testing/d003/stage_s4r8/gate_allow_r8m1a3c_endA.txt ;;
    startB) ALLOW="" ;;
    endB) ALLOW=testing/d003/stage_s4r8/gate_allow_r8m1a3c_endB.txt ;;
esac
if [ -n "$ALLOW" ]; then test -f "$ALLOW" || refuse "allow-list missing: $ALLOW"; fi
HT=testing/d003/stage_s4r8/gate_hashes_r8m1a3c.txt
if [ "$MODE" = start ] || [ "$MODE" = endA ]; then test -f "$HT" || refuse "hash table missing: $HT"; fi
SR7="S4R7_RECHECK_$(printf '%s' "$OUTSTEM" | tr 'a-z' 'A-Z').tsv"
case "$SR7" in
    S4R7_RECHECK_GATE_R8_M1A3C_*.tsv) ;;
    *) refuse "derived recheck name is not accepted" ;;
esac
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
: > "$OUT"
printf '# P05-S4 R8 M1a CONT2c gate8 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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
head_prefix() {
    _hn=$(wc -c < "$2" | tr -d ' ')
    _hs=$(sha256sum "$2" | cut -d' ' -f1)
    _ps=$(head -c "$_hn" "$3" | sha256sum | cut -d' ' -f1)
    check "$1" "$_hs" "$_ps"
    record "${1}_HEAD_BYTES" "$_hn"
}
same_bytes() {
    _c=$(cmp -s "$2" "$3" && echo same || echo differs)
    check "$1" same "$_c"
}

# ---- allow-lists and brief ----
if [ -n "$ALLOW" ]; then
    record ALLOW_FILE "$ALLOW"
    record ALLOW_FILE_SHA256 "$(sha256sum "$ALLOW" 2>&1 | cut -d' ' -f1)"
else
    record ALLOW_FILE "(none: startB requires an empty status)"
fi
record BRIEF_CONT2C_SHA256 "$(sha256sum checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2c.md 2>&1 | cut -d' ' -f1)"
ALLOWED_TXT=""
if [ -n "$ALLOW" ]; then ALLOWED_TXT=$(grep -v '^#' "$ALLOW" | grep -v '^[[:space:]]*$'); fi
[ -n "$WANT" ] && record START_FILE "$STARTF"

# ---- HEAD ----
case "$MODE" in
    start|endA)
        check HEAD e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD 2>&1)" ;;
    startB)
        check HEAD_PARENT e2589cbc2b470ae88286d582ee62699e7c0d9e4c "$(git rev-parse HEAD^ 2>&1)"
        _subj=$(git log -1 --format=%s 2>&1)
        case "$_subj" in
            "P05-S4 R8 M1a records (cont1+cont2+cont2b"*) _sok=yes ;;
            *) _sok=no ;;
        esac
        check HEAD_SUBJECT_PREFIX yes "$_sok"
        record HEAD_B "$(git rev-parse HEAD 2>&1)" ;;
    endB)
        check HEAD_EQ_HEAD_B "$(recval "$STARTF" HEAD_B)" "$(git rev-parse HEAD 2>&1)" ;;
esac

# ---- trees and judge ----
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4 2>&1)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4 2>&1)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4 2>&1)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ 2>&1 | LC_ALL=C sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv 2>&1 | cut -d' ' -f1)"

# ---- ERRATA_8 and RULINGS (U168-U175 records; start = before this round's append, endA = append only) ----
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
RUL=checkpoints/p05/registries/RULINGS.tsv
check ERRATA_8_FIRST_13990_BYTES_SHA256 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551 "$(head -c 13990 "$ERR" | sha256sum | cut -d' ' -f1)"
check ERRATA_8_FIRST_28653_BYTES_SHA256 16024140abb1bbecfd34fc35471d74b3a94d79e75c3d50f44a98b3b43e8532b0 "$(head -c 28653 "$ERR" | sha256sum | cut -d' ' -f1)"
case "$MODE" in
    start)
        check ERRATA_8_WHOLE_SHA256_BEFORE_APPEND 60b592bb6b1530a4c8a02197f30a4fa257e7b73d90582d8972dc2363cdad91d5 "$(sha256sum "$ERR" 2>&1 | cut -d' ' -f1)"
        check ERRATA_8_BYTES_BEFORE_APPEND 34208 "$(wc -c < "$ERR" | tr -d ' ')"
        check RULINGS_WHOLE_SHA256_BEFORE_APPEND 9bd490cc36d0735a310c5eea06a33ff0342707f826e1b8f0d3c8d01db9b47f68 "$(sha256sum "$RUL" 2>&1 | cut -d' ' -f1)"
        check RULINGS_BYTES_BEFORE_APPEND 62722 "$(wc -c < "$RUL" | tr -d ' ')"
        git show "HEAD:$RUL" > "$EV/tmp/RULINGS_HEAD_gate8_start.txt" 2>&1
        head_prefix RULINGS_HEAD_IS_BYTE_PREFIX "$EV/tmp/RULINGS_HEAD_gate8_start.txt" "$RUL" ;;
    endA)
        check ERRATA_8_FIRST_34208_BYTES_SHA256 60b592bb6b1530a4c8a02197f30a4fa257e7b73d90582d8972dc2363cdad91d5 "$(head -c 34208 "$ERR" | sha256sum | cut -d' ' -f1)"
        check RULINGS_FIRST_62722_BYTES_SHA256 9bd490cc36d0735a310c5eea06a33ff0342707f826e1b8f0d3c8d01db9b47f68 "$(head -c 62722 "$RUL" | sha256sum | cut -d' ' -f1)" ;;
    startB)
        git show "HEAD:$RUL" > "$EV/tmp/RULINGS_HEAD_gate8_startB.txt" 2>&1
        same_bytes RULINGS_WORKING_EQ_HEAD "$RUL" "$EV/tmp/RULINGS_HEAD_gate8_startB.txt"
        git show "HEAD:$ERR" > "$EV/tmp/ERRATA_HEAD_gate8_startB.txt" 2>&1
        same_bytes ERRATA_8_WORKING_EQ_HEAD "$ERR" "$EV/tmp/ERRATA_HEAD_gate8_startB.txt" ;;
    endB)
        git show "HEAD:$RUL" > "$EV/tmp/RULINGS_HEAD_gate8_endB.txt" 2>&1
        same_bytes RULINGS_WORKING_EQ_HEAD "$RUL" "$EV/tmp/RULINGS_HEAD_gate8_endB.txt"
        git show "HEAD:$ERR" > "$EV/tmp/ERRATA_HEAD_gate8_endB.txt" 2>&1
        head_prefix ERRATA_8_HEAD_IS_BYTE_PREFIX "$EV/tmp/ERRATA_HEAD_gate8_endB.txt" "$ERR" ;;
esac

# ---- PRERUN (append only; first 3869 bytes fixed) ----
if [ "$MODE" = start ] || [ "$MODE" = endA ]; then
    check PRERUN_PREFIX_3869 774e150033105804eb680c9da9c83bbe9af813d987811ef3ed88754e46abaa51 "$(head -c 3869 "$EV/PRERUN_CHECKS_R8_M1a.txt" | sha256sum | cut -d' ' -f1)"
fi

# ---- registries/s4r8 manifest (ERRATA_8 line by prefix, others sha256sum -c) and s3r4c5 manifest ----
S4R8_DIR=checkpoints/p05/registries/s4r8
check S4R8_ERRATA_8_PREFIX_13990 72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551 "$(head -c 13990 "$S4R8_DIR/ERRATA_8.txt" | sha256sum | cut -d' ' -f1)"
S4R8_TOTAL=$(grep -c . "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_NONERR=$(grep -vc 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" 2>&1)
S4R8_OK=$(grep -v 'ERRATA_8.txt$' "$S4R8_DIR/SHA256SUMS.txt" | (cd "$S4R8_DIR" && sha256sum -c - 2>&1) | grep -c ': OK$')
check S4R8_OTHER_LINES_ALL_OK "$S4R8_NONERR" "$S4R8_OK"
check S4R8_TOTAL_LINES_25 25 "$S4R8_TOTAL"
S3C5_TOTAL=$(grep -c . checkpoints/p05/registries/s3r4c5/SHA256SUMS.txt 2>&1)
S3C5_OK=$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
check S3R4C5_SHA256SUMS_OK_LINES_EQ_TOTAL "$S3C5_TOTAL" "$S3C5_OK"

# ---- registries/s4r7 manifests: classified recheck (U121, U128, U129), read only, output name derived from OUT ----
python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a3c.py "$SR7" > "$EV/tmp/recheck_stdout_r8m1a3c_$MODE.txt" 2>&1
check S4R7_MANIFESTS "fails=0" "$(tail -n 1 "$EV/$SR7" 2>&1)"
record S4R7_RECHECK_FILE "checkpoints/p05/evidence/p05-s4r8/$SR7"

# ---- sha256 table (start and endA): every row must match ----
if [ "$MODE" = start ] || [ "$MODE" = endA ]; then
    grep -v '^#' "$HT" | grep -v '^[[:space:]]*$' > "$EV/tmp/hashes_r8m1a3c_$MODE.txt"
    while read -r _h _p; do
        _a=$(sha256sum "$_p" 2>&1 | cut -d' ' -f1)
        if [ "$_h" = "$_a" ]; then _r=PASS; else _r=FAIL; FAILS=$((FAILS + 1)); fi
        printf '%s\tHASH_TABLE %s\texpected=%s\tactual=%s\n' "$_r" "$_p" "$_h" "$_a" >> "$OUT"
    done < "$EV/tmp/hashes_r8m1a3c_$MODE.txt"
    # stored aggregates: untracked files of stage_s4r8 and of registries/s4r8/M1a, excluding this round's names
    git ls-files -o --exclude-standard -- testing/d003/stage_s4r8 | LC_ALL=C sort | grep -v -i r8m1a3c > "$EV/tmp/agg_stage_$MODE.txt"
    AG_STAGE_N=$(wc -l < "$EV/tmp/agg_stage_$MODE.txt" | tr -d ' ')
    AG_STAGE_H=$(xargs sha256sum < "$EV/tmp/agg_stage_$MODE.txt" | sha256sum | cut -d' ' -f1)
    check STAGE_UNTRACKED_COUNT_EXCL_M1A3C 43 "$AG_STAGE_N"
    check STAGE_UNTRACKED_AGG_SHA256 c7010af5fb76af5b1502d786c4ed0025c08eaf2681d935761886c506886cacd1 "$AG_STAGE_H"
    record STAGE_UNTRACKED_LIST "$(tr '\n' ' ' < "$EV/tmp/agg_stage_$MODE.txt")"
    git ls-files -o --exclude-standard -- checkpoints/p05/registries/s4r8/M1a | LC_ALL=C sort | grep -v -i -e m1a3c -e '/STRIP_EQUIV_R8_M1a\.tsv$' > "$EV/tmp/agg_m1a_$MODE.txt"
    AG_M1A_N=$(wc -l < "$EV/tmp/agg_m1a_$MODE.txt" | tr -d ' ')
    AG_M1A_H=$(xargs sha256sum < "$EV/tmp/agg_m1a_$MODE.txt" | sha256sum | cut -d' ' -f1)
    check M1A_UNTRACKED_COUNT_EXCL 34 "$AG_M1A_N"
    check M1A_UNTRACKED_AGG_SHA256 907954c694d3bc2e4cf7a7b916025efe81d09beb346949af30f67439de2349bc "$AG_M1A_H"
    record M1A_UNTRACKED_LIST "$(tr '\n' ' ' < "$EV/tmp/agg_m1a_$MODE.txt")"
fi

# ---- git status: every line must be in the allow-list (exact or PREFIX), empty for startB ----
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
if [ "$MODE" = endB ]; then
    BAD2=$(printf '%s\n' "$ST" | awk '/^\?\?/ && tolower($0) !~ /m1a3c/ {print}')
    check UNTRACKED_LINES_ALL_CONTAIN_M1A3C "" "$BAD2"
fi

# ---- temporary-area snapshot (form 5, taken by the caller) ----
case "$MODE" in
    start)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    startB)
        record TMP_COUNT_STARTB "$TC"
        record TMP_SHA256_STARTB "$TS" ;;
    endA)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
    endB)
        check TMP_COUNT_EQ_STARTB "$(recval "$STARTF" TMP_COUNT_STARTB)" "$TC"
        check TMP_SHA256_EQ_STARTB "$(recval "$STARTF" TMP_SHA256_STARTB)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate8_r8m1a3c: $MODE FAILS=$FAILS -> $OUT"
exit 0
