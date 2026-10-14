#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate14_r8m1b1.sh -- P05-S4 R8 M1b1 gate (brief §3). New file.
# Baseline HEAD: 43c650dfe98ae3e20753ff63c0cca5a14467c6a2
# Evidence dir: checkpoints/p05/evidence/p05-s4r8/m1b1
set -u
refuse() { echo "gate14_r8m1b1: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m1b1 ] || refuse "first argument must be p05-s4r8/m1b1"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M1b1_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M1b1_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
NAMEPART=${OUTSTEM#GATE_R8_M1b1_}
case "$NAMEPART" in
    '') refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
ALLOW_START="$REPO/testing/d003/stage_s4r8/gate_allow_r8m1b1_start.txt"
ALLOW_END="$REPO/testing/d003/stage_s4r8/gate_allow_r8m1b1_end.txt"
STARTF=""
case "$MODE" in
    startA)
        [ $# -eq 5 ] || refuse "startA takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    end)
        [ $# -eq 6 ] || refuse "end takes START_FILE TC TS (6 arguments incl. mode)"
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
        *"gate14 (startA) ->"*) ;;
        *) refuse "start file header is not a gate14 startA" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi

FAILS=0
ST_FILE="$EV/tmp/status_now_$NAMEPART.txt"
: > "$OUT"
printf '# P05-S4 R8 M1b1 gate14 (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

BASE=43c650dfe98ae3e20753ff63c0cca5a14467c6a2
HEAD_NOW=$(git rev-parse HEAD)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current)"
case "$MODE" in
    startA)
        check HEAD_IS_BASE "$BASE" "$HEAD_NOW" ;;
    end)
        check HEAD_EQ_START "$(recval "$STARTF" HEAD)" "$HEAD_NOW" ;;
esac
record HEAD "$HEAD_NOW"
record START_MODE "$MODE"
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4)"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum "$REPO/testing/d003/judge_d003.py" | cut -d' ' -f1)"
record ALLOW_START_SHA256 "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
record ALLOW_END_SHA256 "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"
case "$MODE" in
    startA)
        check ALLOW_START_LINES 4 "$(wc -l < "$ALLOW_START" | tr -d ' ')"
        check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003)" ;;
    end)
        check ALLOW_START_SHA256_EQ_START "$(recval "$STARTF" ALLOW_START_SHA256)" "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
        check ALLOW_END_SHA256_EQ_START "$(recval "$STARTF" ALLOW_END_SHA256)" "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"
        check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START "" "$(git diff --name-only --diff-filter=MD HEAD -- testing/d003)" ;;
esac

# ---- git status against allow lists ----
git status --short -uall > "$ST_FILE"
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
                case "$_l" in "$_p") _ok=yes; break ;; esac
            done < "$ALLOW_END"
            if [ "$_ok" != yes ]; then _bad=$((_bad + 1)); printf 'NOT_ALLOWED\t%s\n' "$_l" >> "$OUT"; fi
        done < "$ST_FILE"
        check STATUS_END_ALL_ALLOWED 0 "$_bad" ;;
esac

# ---- Detailed python checks ----
PY_OUT="$EV/tmp/py_checks_$NAMEPART.txt"
python3 -I -B "$REPO/testing/d003/stage_s4r8/gate14_check_r8m1b1.py" "$MODE" > "$PY_OUT"
PY_FAILS=$?
cat "$PY_OUT" >> "$OUT"
if [ "$PY_FAILS" -ne 0 ]; then
    FAILS=$((FAILS + PY_FAILS))
fi

# ---- Record active files size and hash ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
record RULINGS_BYTES "$(wc -c < "$REPO/$RUL" | tr -d ' ')"
record RULINGS_SHA256 "$(sha256sum "$REPO/$RUL" | cut -d' ' -f1)"
record ERRATA_8_BYTES "$(wc -c < "$REPO/$ERR" | tr -d ' ')"
record ERRATA_8_SHA256 "$(sha256sum "$REPO/$ERR" | cut -d' ' -f1)"

# ---- temporary-area snapshot ----
case "$MODE" in
    startA)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate14_r8m1b1: $MODE FAILS=$FAILS -> $OUT"
exit 0
