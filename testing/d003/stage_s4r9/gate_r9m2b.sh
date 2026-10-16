REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_r9m2b.sh -- P05-S4 R9 M2b gate script. New file.
# Baseline HEAD: ebf3d007b921e64cdb838c714c0ea53299d365c9
# Evidence dir: checkpoints/p05/evidence/p05-s4r9/m2b
# Usage: sh testing/d003/safe_run.sh p05-s4r9/m2b -- sh testing/d003/stage_s4r9/gate_r9m2b.sh start
#        sh testing/d003/safe_run.sh p05-s4r9/m2b -- sh testing/d003/stage_s4r9/gate_r9m2b.sh end
set -u
refuse() { echo "gate_r9m2b: REFUSED: $1" >&2; exit 2; }
MODE=${1:-start}
case "$MODE" in
    start|end|end_R2) ;;
    *) refuse "mode must be start, end, or end_R2" ;;
esac
BASE_MODE=$MODE
case "$MODE" in
    end_R2) BASE_MODE=end ;;
esac

if [ -n "${2:-}" ]; then
    EV="$2"
    mkdir -p "$EV/tmp"
    export TMPDIR="$EV/tmp"
fi

OUTNAME="GATE_R9M2b_${MODE}.txt"
OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists: $OUTNAME"

ALLOW_START="$REPO/testing/d003/stage_s4r9/gate_allow_r9m2b_start.txt"
ALLOW_END="$REPO/testing/d003/stage_s4r9/gate_allow_r9m2b_end.txt"
STARTF="$REPO/checkpoints/p05/evidence/p05-s4r9/m2b/GATE_R9M2b_start.txt"

test -f "$ALLOW_START" || refuse "allow list (start) missing"
test -f "$ALLOW_END" || refuse "allow list (end) missing"

if [ "$BASE_MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    case "$(head -n 1 "$STARTF")" in
        *"gate_r9m2b (start) ->"*) ;;
        *) refuse "start file header is not a gate_r9m2b start" ;;
    esac
    [ "$(tail -n 1 "$STARTF")" = "FAILS=0" ] || refuse "start file last line is not FAILS=0"
fi

FAILS=0
ST_FILE="$EV/tmp/status_now_${MODE}.txt"
PY_OUT="$EV/tmp/py_checks_${MODE}.txt"
TMP_SNAP="$EV/tmp/tmp_snap_${MODE}.txt"

# Snapshot of temporary area (os.sep + 'tmp')
python3 -I -B -c '
import os, hashlib
TMP_ROOT = os.sep + "tmp"
entries = sorted(os.listdir(TMP_ROOT)) if os.path.isdir(TMP_ROOT) else []
count = len(entries)
sha = hashlib.sha256(("\n".join(entries).encode("utf-8") + (b"\n" if entries else b""))).hexdigest()
print(f"{count}\t{sha}")
' > "$TMP_SNAP"
TC=$(cut -f1 "$TMP_SNAP")
TS=$(cut -f2 "$TMP_SNAP")

: > "$OUT"
printf '# P05-S4 R9 gate_r9m2b (%s) -> %s, utc=%s\n' "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

BASE=ebf3d007b921e64cdb838c714c0ea53299d365c9
HEAD_NOW=$(git rev-parse HEAD)
check BRANCH codex/p05-d003-fft-error-propagation "$(git branch --show-current)"
if [ "$MODE" = start ]; then
    check HEAD_IS_BASE "$BASE" "$HEAD_NOW"
    check HEAD_S4_TREE 589e15eb11fcb04e031b524f25a443e7921946cf "$(git rev-parse HEAD:S4)"
else
    record HEAD_END "$HEAD_NOW"
    check HEAD_END_S4_TREE 589e15eb11fcb04e031b524f25a443e7921946cf "$(git rev-parse HEAD:S4)"
    check S4_DIR_ZERO_MODIFICATION "" "$(git diff HEAD -- S4)"
fi
record HEAD "$HEAD_NOW"
record START_MODE "$MODE"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum "$REPO/testing/d003/judge_d003.py" | cut -d' ' -f1)"
record ALLOW_START_SHA256 "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
record ALLOW_END_SHA256 "$(sha256sum "$ALLOW_END" | cut -d' ' -f1)"

case "$BASE_MODE" in
    start)
        check ALLOW_START_LINES 5 "$(wc -l < "$ALLOW_START" | tr -d ' ')"
        check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003)" ;;
    end)
        check ALLOW_START_SHA256_EQ_START "$(recval "$STARTF" ALLOW_START_SHA256)" "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
        check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START "" "$(git diff --name-only --diff-filter=MD "$BASE" -- testing/d003)" ;;
esac

# ---- git status against allow lists ----
git status --short -uall > "$ST_FILE"
case "$BASE_MODE" in
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
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m2b.py" "$MODE" "$STARTF" "$EV" > "$PY_OUT"
PY_FAILS=$?
cat "$PY_OUT" >> "$OUT"
if [ "$PY_FAILS" -ne 0 ]; then
    FAILS=$((FAILS + PY_FAILS))
fi

# ---- Record active files size and hash ----
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/ERRATA_S3R5.txt
ERR9=checkpoints/p05/registries/s4r9/ERRATA_9.txt
record RULINGS_BYTES "$(wc -c < "$REPO/$RUL" | tr -d ' ')"
record RULINGS_SHA256 "$(sha256sum "$REPO/$RUL" | cut -d' ' -f1)"
record ERRATA_S3R5_BYTES "$(wc -c < "$REPO/$ERR" | tr -d ' ')"
record ERRATA_S3R5_SHA256 "$(sha256sum "$REPO/$ERR" | cut -d' ' -f1)"
record ERRATA_9_BYTES "$(wc -c < "$REPO/$ERR9" | tr -d ' ')"
record ERRATA_9_SHA256 "$(sha256sum "$REPO/$ERR9" | cut -d' ' -f1)"

# ---- temporary-area snapshot ----
case "$BASE_MODE" in
    start)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate_r9m2b: $MODE FAILS=$FAILS -> $OUT"
exit $FAILS
