#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate11_r8m1a4audit3.sh -- P05-S4 R8 M1a CONT3a audit part 3 gate (r8m1a4audit3).  New file.
# Based on gate10_r8m1a4audit2_r2.sh (not modified).  Changes: the baseline is HEAD=2a08aa5 (the phase-B record commit of
# the audit2 round, parent 86ba3a2); the stage-A allow list is replaced by the start-A rule below; the S4R7 recheck name
# is derived as S4R7_RECHECK_GATE_R8_M1A4_AUDIT3_<NAME>.tsv (matches recheck_s4r7_r8m1a4.py pattern).  The derived name is only
# reserved and checked here (U17); this gate does not create that file.  Revision note: the first version of the derivation
# omitted AUDIT3 and collided with the earlier round's S4R7_RECHECK_GATE_R8_M1A4_END.tsv at the end gate (refused, nothing written).
# Modes (through safe_run; every argument is checked before any output file is written):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/gate11_r8m1a4audit3.sh p05-s4r8 OUT startA TC TS
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/gate11_r8m1a4audit3.sh p05-s4r8 OUT end START_FILE TC TS
# OUT = GATE_R8_M1a4_AUDIT3_<name>.txt in the evidence directory; it must not exist.
# TC = entry count and TS = sha256 of the temporary-area listing, both taken by the caller with the permitted inline form.
# end reads every start value (HEAD, status, temporary area, file values) from START_FILE; no start value is passed as an argument.
# Output: one PASS/FAIL line per check, RECORD lines, FAILS=<n> as the last line.  Exit 2 = refused before any output.
set -u
refuse() { echo "gate11_r8m1a4audit3: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8 ] || refuse "first argument must be p05-s4r8"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1a4_AUDIT3_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1a4_AUDIT3_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
NAMEPART=${OUTSTEM#GATE_R8_M1a4_AUDIT3_}
case "$NAMEPART" in
    '') refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
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
if [ "$MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    case "$(head -n 1 "$STARTF")" in
        *"gate11 (startA) ->"*) ;;
        *) refuse "start file header is not a gate11 startA" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi
SR7="S4R7_RECHECK_GATE_R8_M1A4_AUDIT3_$(printf '%s' "$NAMEPART" | tr 'a-z' 'A-Z').tsv"
case "$SR7" in
    S4R7_RECHECK_GATE_R8_M1A4_*.tsv) ;;
    *) refuse "derived recheck name is not accepted" ;;
esac
test ! -e "$EV/$SR7" || refuse "exists (U17): $SR7"

# ---- all validation passed: from here on the output file is written ----
FAILS=0
AEND="$EV/GATE_R8_M1a4_AUDIT2_END_B2.txt"
ST_FILE="$EV/tmp/status_now_$NAMEPART.txt"
: > "$OUT"
printf '# P05-S4 R8 M1a CONT3a audit part 3 gate11 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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
BASE=2a08aa51797bef842a2f09c07a2eca80b22fc178
BASEP=86ba3a2c353fe0a85653542782125d9076eea835
HEAD_NOW=$(git rev-parse HEAD 2>&1)
PARENT_NOW=$(git rev-parse HEAD^ 2>&1)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current 2>&1)"
case "$MODE" in
    startA)
        check HEAD_IS_BASE "$BASE" "$HEAD_NOW"
        check HEAD_PARENT_IS_86BA3A2 "$BASEP" "$PARENT_NOW" ;;
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
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py 2>&1 | cut -d' ' -f1)"
check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003 2>&1)"
check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_BASE "" "$(git diff --name-only --diff-filter=MD 2a08aa51797bef842a2f09c07a2eca80b22fc178 HEAD -- testing/d003 2>&1)"

# ---- RULINGS and ERRATA_8: prefix checks against the last recorded values ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
check RULINGS_LINES_NOT_5_FIELDS 0 "$(awk -F'\t' '/^#/{next} NF!=5{n++} END{print n+0}' "$RUL")"
case "$MODE" in
    startA)
        # at start the worktree must equal HEAD (no uncommitted change to the live files); at end they are appended, so the
        # HEAD-equality check does not apply and the prefix checks below are used instead (revision note: first end run FAILS=2).
        check RULINGS_HEAD_BLOB_EQ_WORKTREE "$(git show "HEAD:$RUL" | sha256sum | cut -d' ' -f1)" "$(sha256sum "$RUL" | cut -d' ' -f1)"
        check ERRATA_8_HEAD_BLOB_EQ_WORKTREE "$(git show "HEAD:$ERR" | sha256sum | cut -d' ' -f1)" "$(sha256sum "$ERR" | cut -d' ' -f1)"
        check RULINGS_BYTES_START_A 70888 "$(wc -c < "$RUL" | tr -d ' ')"
        check ERRATA_8_BYTES_START_A 52675 "$(wc -c < "$ERR" | tr -d ' ')"
        check RULINGS_U188_TO_U191_ROWS_NOT_YET 0 "$(awk -F'\t' '$1 ~ /^U18[89]$|^U19[01]$/ {n++} END{print n+0}' "$RUL")"
        ;;
    end)
        _rb=$(recval "$STARTF" RULINGS_BYTES); _rh=$(recval "$STARTF" RULINGS_SHA256)
        _eb=$(recval "$STARTF" ERRATA_8_BYTES); _eh=$(recval "$STARTF" ERRATA_8_SHA256)
        check RULINGS_PREFIX_OF_START_UNCHANGED "$_rh" "$(head -c "$_rb" "$RUL" | sha256sum | cut -d' ' -f1)"
        check RULINGS_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$RUL" | tr -d ' ')" -ge "$_rb" ] && echo yes || echo no )"
        check ERRATA_8_PREFIX_OF_START_UNCHANGED "$_eh" "$(head -c "$_eb" "$ERR" | sha256sum | cut -d' ' -f1)"
        check ERRATA_8_NOT_TRUNCATED_SINCE_START yes "$( [ "$(wc -c < "$ERR" | tr -d ' ')" -ge "$_eb" ] && echo yes || echo no )"
        ;;
esac
record RULINGS_BYTES "$(wc -c < "$RUL" | tr -d ' ')"
record RULINGS_SHA256 "$(sha256sum "$RUL" | cut -d' ' -f1)"
record ERRATA_8_BYTES "$(wc -c < "$ERR" | tr -d ' ')"
record ERRATA_8_SHA256 "$(sha256sum "$ERR" | cut -d' ' -f1)"

# ---- git status ----
git status --short > "$ST_FILE" 2>&1
case "$MODE" in
    startA)
        # the only permitted untracked item at start is this gate script itself (it is new in this round and not yet committed)
        check STATUS_A_ONLY_GATE_SCRIPT "" "$(grep -v '^?? testing/d003/stage_s4r8/gate11_r8m1a4audit3\.sh$' "$ST_FILE")"
        while IFS= read -r _l; do record STATUS_START "$_l"; done < "$ST_FILE"
        ;;
    end)
        awk -F'\t' '$1=="RECORD" && $2=="STATUS_START" { v=$3; sub(/^value=/, "", v); print v }' "$STARTF" > "$EV/tmp/start_status_$NAMEPART.txt"
        # end: a line is allowed when it was already in the start status, or when it is one of the three append-only live
        # files (their content is checked by prefix above), or when it is an untracked file of this round (name contains
        # AUDIT3 or m1a4audit3).  Any other change is NOT_ALLOWED.  (Rule written after the start gate; disclosed in the report.)
        check STATUS_END_ONLY_ALLOWED "" "$(awk 'NR==FNR { s[$0]=1; next } { if (length($0) == 0) next; if ($0 in s) next; p = substr($0, 4); if (substr($0, 1, 3) == " M " && (p == "checkpoints/p05/STATE.md" || p == "checkpoints/p05/registries/RULINGS.tsv" || p == "checkpoints/p05/registries/s4r8/ERRATA_8.txt")) next; if (substr($0, 1, 3) == "?? " && (p ~ /AUDIT3/ || p ~ /audit3/ || p ~ /m1a4audit3/)) next; print "NOT_ALLOWED " $0 }' "$EV/tmp/start_status_$NAMEPART.txt" "$ST_FILE")"
        ;;
esac

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
echo "gate11_r8m1a4audit3: $MODE FAILS=$FAILS -> $OUT"
exit 0
