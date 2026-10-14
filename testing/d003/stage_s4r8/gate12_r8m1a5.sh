#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate12_r8m1a5.sh -- P05-S4 R8 M1a CONT3b1 gate (r8m1a5).  New file.
# Based on gate11_r8m1a4audit3.sh (not modified).  Changes:
#   - baseline HEAD = abf3e42 (parent 2a08aa5); evidence directory p05-s4r8/m1a5;
#   - the allow lists are frozen data files (U194, E8-69), read by start and end, recorded by sha256 at start and
#     required to be unchanged at end;
#   - end matches each status line against the end allow list (exact line or shell wildcard, read from the file);
#   - end checks the append-only live files by prefix (no truncation), the six new rulings U192–U197, and E8-68/E8-69;
#   - end reads every start value from START_FILE; no start value is passed as an argument.
# Modes (through safe_run; every argument is checked before the output file is written):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a5 -- sh testing/d003/stage_s4r8/gate12_r8m1a5.sh p05-s4r8/m1a5 GATE_R8_M1a5_START.txt startA TC TS
#   sh testing/d003/safe_run.sh p05-s4r8/m1a5 -- sh testing/d003/stage_s4r8/gate12_r8m1a5.sh p05-s4r8/m1a5 GATE_R8_M1a5_END.txt end CHECKPOINT_START_FILE TC TS
# TC = entry count and TS = sha256 of the temporary-area listing, both taken by the caller with the permitted inline form.
# Output: one PASS/FAIL line per check, RECORD lines, FAILS=<n> as the last line.  Exit 2 = refused before any output.
set -u
refuse() { echo "gate12_r8m1a5: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m1a5 ] || refuse "first argument must be p05-s4r8/m1a5"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1a5_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a5_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
NAMEPART=${OUTSTEM#GATE_R8_M1a5_}
case "$NAMEPART" in
    '') refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
ALLOW_START="$REPO/testing/d003/stage_s4r8/gate_allow_r8m1a5_start.txt"
ALLOW_END="$REPO/testing/d003/stage_s4r8/gate_allow_r8m1a5_end.txt"
STARTF=""
case "$MODE" in
    startA)
        [ $# -eq 5 ] || refuse "startA takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    end)
        [ $# -eq 6 ] || refuse "end takes START_FILE TC TS  (6 arguments incl. mode)"
        STARTF=${4:-}; TC=${5:-}; TS=${6:-} ;;
    *) refuse "mode must be startA or end" ;;
esac
case "$TC" in
    ''|*[!0-9]*) refuse "TC must be digits" ;;
esac
case "$TS" in
    ''|*[!0-9a-f]*) refuse "TS must be lowercase hex" ;;
esac
[ "${#TS}" = 64 ] || refuse "TS must be 64 characters"
test -f "$ALLOW_START" || refuse "allow list (start) missing"
test -f "$ALLOW_END" || refuse "allow list (end) missing"
if [ "$MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    case "$(head -n 1 "$STARTF")" in
        *"gate12 (startA) ->"*) ;;
        *) refuse "start file header is not a gate12 startA" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi
SR7="S4R7_RECHECK_GATE_R8_M1A4_M1A5_$(printf '%s' "$NAMEPART" | tr 'a-z' 'A-Z').tsv"
case "$SR7" in
    S4R7_RECHECK_GATE_R8_M1A4_*.tsv) ;;
    *) refuse "derived recheck name is not accepted" ;;
esac
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
ST_FILE="$EV/tmp/status_now_$NAMEPART.txt"
: > "$OUT"
printf '# P05-S4 R8 M1a CONT3b1 gate12 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

# ---- branch, HEAD, trees, judge ----
BASE=abf3e420f5ba3600e079ecf213612bc1fc2a0aad
BASEP=2a08aa51797bef842a2f09c07a2eca80b22fc178
HEAD_NOW=$(git rev-parse HEAD 2>&1)
PARENT_NOW=$(git rev-parse HEAD^ 2>&1)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current 2>&1)"
case "$MODE" in
    startA)
        check HEAD_IS_BASE "$BASE" "$HEAD_NOW"
        check HEAD_PARENT_IS_2A08AA5 "$BASEP" "$PARENT_NOW" ;;
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
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum "$REPO/testing/d003/judge_d003.py" 2>&1 | cut -d' ' -f1)"
record ALLOW_START_SHA256 "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
record ALLOW_END_SHA256 "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"
case "$MODE" in
    startA)
        check ALLOW_START_LINES 4 "$(wc -l < "$ALLOW_START" | tr -d ' ')"
        check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003 2>&1)" ;;
    end)
        check ALLOW_START_SHA256_EQ_START "$(recval "$STARTF" ALLOW_START_SHA256)" "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
        check ALLOW_END_SHA256_EQ_START "$(recval "$STARTF" ALLOW_END_SHA256)" "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"
        check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START "" "$(git diff --name-only --diff-filter=MD HEAD -- testing/d003 2>&1)" ;;
esac

# ---- git status against the allow lists ----
git status --short > "$ST_FILE" 2>&1
case "$MODE" in
    startA)
        check STATUS_START_EQ_ALLOW_START "$(sort "$ALLOW_START")" "$(sort "$ST_FILE")"
        while IFS= read -r _l; do record STATUS_START "$_l"; done < "$ST_FILE" ;;
    end)
        _bad=0
        while IFS= read -r _l; do
            [ -n "$_l" ] || continue
            _ok=no
            while IFS= read -r _p; do
                case "$_p" in ''|'#'*) continue ;; esac
                case "$_l" in $_p) _ok=yes; break ;; esac
            done < "$ALLOW_END"
            if [ "$_ok" != yes ]; then _bad=$((_bad + 1)); printf 'NOT_ALLOWED\t%s\n' "$_l" >> "$OUT"; fi
        done < "$ST_FILE"
        check STATUS_END_ALL_ALLOWED 0 "$_bad" ;;
esac

# ---- RULINGS and ERRATA_8 ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
check RULINGS_LINES_NOT_5_FIELDS 0 "$(awk -F'\t' '/^#/{next} NF!=5{n++} END{print n+0}' "$REPO/$RUL")"
case "$MODE" in
    startA)
        check RULINGS_HEAD_BLOB_EQ_WORKTREE "$(git show "HEAD:$RUL" | sha256sum | cut -d' ' -f1)" "$(sha256sum "$REPO/$RUL" | cut -d' ' -f1)"
        check ERRATA_8_HEAD_BLOB_EQ_WORKTREE "$(git show "HEAD:$ERR" | sha256sum | cut -d' ' -f1)" "$(sha256sum "$REPO/$ERR" | cut -d' ' -f1)"
        check RULINGS_BYTES_START_A 72921 "$(wc -c < "$REPO/$RUL" | tr -d ' ')"
        check ERRATA_8_BYTES_START_A 54678 "$(wc -c < "$REPO/$ERR" | tr -d ' ')"
        check RULINGS_U192_TO_U197_ROWS_NOT_YET 0 "$(awk -F'\t' '$1 ~ /^U19[2-7]$/ {n++} END{print n+0}' "$REPO/$RUL")"
        check ERRATA_E8_68_69_NOT_YET 0 "$(awk '$1=="E8-68" || $1=="E8-69" {n++} END{print n+0}' "$REPO/$ERR")"
        ;;
    end)
        _rb=$(recval "$STARTF" RULINGS_BYTES); _rh=$(recval "$STARTF" RULINGS_SHA256)
        _eb=$(recval "$STARTF" ERRATA_8_BYTES); _eh=$(recval "$STARTF" ERRATA_8_SHA256)
        check RULINGS_PREFIX_OF_START_UNCHANGED "$_rh" "$(head -c "$_rb" "$REPO/$RUL" | sha256sum | cut -d' ' -f1)"
        check RULINGS_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$REPO/$RUL" | tr -d ' ')" -ge "$_rb" ] && echo yes || echo no )"
        check ERRATA_8_PREFIX_OF_START_UNCHANGED "$_eh" "$(head -c "$_eb" "$REPO/$ERR" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$REPO/$ERR" | tr -d ' ')" -ge "$_eb" ] && echo yes || echo no )"
        check RULINGS_U192_TO_U197_ROWS_GENERATED 6 "$(awk -F'\t' '$1 ~ /^U19[2-7]$/ && $5=="生效" {n++} END{print n+0}' "$REPO/$RUL")"
        check ERRATA_E8_68_ROWS 1 "$(awk '$1=="E8-68" {n++} END{print n+0}' "$REPO/$ERR")"
        check ERRATA_E8_69_ROWS 1 "$(awk '$1=="E8-69" {n++} END{print n+0}' "$REPO/$ERR")"
        check STATE_BYTES_LE_8192 yes "$( [ "$(wc -c < "$REPO/checkpoints/p05/STATE.md" | tr -d ' ')" -le 8192 ] && echo yes || echo no )"
        ;;
esac
record RULINGS_BYTES "$(wc -c < "$REPO/$RUL" | tr -d ' ')"
record RULINGS_SHA256 "$(sha256sum "$REPO/$RUL" | cut -d' ' -f1)"
record ERRATA_8_BYTES "$(wc -c < "$REPO/$ERR" | tr -d ' ')"
record ERRATA_8_SHA256 "$(sha256sum "$REPO/$ERR" | cut -d' ' -f1)"

# ---- temporary-area snapshot (form taken by the caller) ----
case "$MODE" in
    startA)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate12_r8m1a5: $MODE FAILS=$FAILS -> $OUT"
exit 0
