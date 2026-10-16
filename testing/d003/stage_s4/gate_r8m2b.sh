REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_r8m2b.sh -- P05-S4 R8 M2b gate script. New file (copied from gate_r8m2a4.sh; original unchanged).
# Baseline HEAD: e57a2f38705e0c385eeab175a3c6a7442cab84fc
# Evidence dir: checkpoints/p05/evidence/p05-s4r8/m2b
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2b -- sh testing/d003/stage_s4/gate_r8m2b.sh p05-s4r8/m2b GATE_R8_M2b_<name>.txt start TC TS
#        sh testing/d003/safe_run.sh p05-s4r8/m2b -- sh testing/d003/stage_s4/gate_r8m2b.sh p05-s4r8/m2b GATE_R8_M2b_<name>.txt end START_FILE TC TS
set -u
refuse() { echo "gate_r8m2b: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2b ] || refuse "first argument must be p05-s4r8/m2b"
OUTNAME=${2:-}
MODE=${3:-}
case "$OUTNAME" in
    GATE_R8_M2b_*.txt) ;;
    *) refuse "OUT must be GATE_R8_M2b_<name>.txt" ;;
esac
OUTSTEM=${OUTNAME%.txt}
NAMEPART=${OUTSTEM#GATE_R8_M2b_}
case "$NAMEPART" in
    '') refuse "OUT name is empty" ;;
    *[!A-Za-z0-9_]*) refuse "OUT name has illegal characters" ;;
esac
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists (U17): $OUTNAME"
ALLOW_START="$REPO/testing/d003/stage_s4/gate_allow_r8m2b_start.txt"
ALLOW_END="$REPO/testing/d003/stage_s4/gate_allow_r8m2b_end.txt"
STARTF=""
TC=""
TS=""
case "$MODE" in
    start)
        [ $# -eq 5 ] || refuse "start takes TC TS"
        TC=${4:-}; TS=${5:-} ;;
    end)
        [ $# -eq 6 ] || refuse "end takes START_FILE TC_END TS_END (6 arguments incl. mode)"
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
test -f "$ALLOW_START" || refuse "allow list (start) missing"
test -f "$ALLOW_END" || refuse "allow list (end) missing"
if [ "$MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    case "$(head -n 1 "$STARTF")" in
        *"gate_r8m2b (start) ->"*) ;;
        *) refuse "start file header is not a gate_r8m2b start" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi

FAILS=0
ST_FILE="$EV/tmp/status_now_${OUTSTEM}.txt"
PY_OUT="$EV/tmp/py_checks_${OUTSTEM}.txt"
: > "$OUT"
printf '# P05-S4 R8 M2b gate_r8m2b (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

BASE=e57a2f38705e0c385eeab175a3c6a7442cab84fc
HEAD_NOW=$(git rev-parse HEAD)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current)"
check HEAD_IS_BASE "$BASE" "$HEAD_NOW"
record HEAD "$HEAD_NOW"
record START_MODE "$MODE"
check HEAD_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4)"
check F3_8d8202a_S4_TREE 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4)"
check F2_a07b5ac_S4_TREE e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4)"
check B_37a82e8_S4_TREE 1d738e64f9864a475fdb3de34cd3601605df2c64 "$(git rev-parse 37a82e8:S4)"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum "$REPO/testing/d003/judge_d003.py" | cut -d' ' -f1)"
record ALLOW_START_SHA256 "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
record ALLOW_END_SHA256 "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"
case "$MODE" in
    start)
        check ALLOW_START_LINES 5 "$(wc -l < "$ALLOW_START" | tr -d ' ')"
        check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003)" ;;
    end)
        check ALLOW_START_SHA256_EQ_START "$(recval "$STARTF" ALLOW_START_SHA256)" "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
        check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START "" "$(git diff --name-only --diff-filter=MD HEAD -- testing/d003)" ;;
esac

# ---- git status against allow lists ----
git status --short -uall > "$ST_FILE"
case "$MODE" in
    start)
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

# ---- Detailed python checks ----
python3 -I -B "$REPO/testing/d003/stage_s4/gate_check_r8m2b.py" "$MODE" "$STARTF" > "$PY_OUT"
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
    start)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate_r8m2b: $MODE FAILS=$FAILS -> $OUT"
exit 0
