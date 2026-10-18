REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_r9m1r4.sh -- P05-S4 R9 M1R4 gate script. New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
# Evidence dir: checkpoints/p05/evidence/p05-s4r9/m1r4
# Usage: sh testing/d003/safe_run.sh p05-s4r9/m1r4 -- sh testing/d003/stage_s4r9/gate_r9m1r4.sh start
#        sh testing/d003/safe_run.sh p05-s4r9/m1r4 -- sh testing/d003/stage_s4r9/gate_r9m1r4.sh end
#        sh testing/d003/safe_run.sh p05-s4r9/m1r4 -- sh testing/d003/stage_s4r9/gate_r9m1r4.sh end _R2
set -u
refuse() { echo "gate_r9m1r4: REFUSED: $1" >&2; exit 2; }
MODE=${1:-start}
case "$MODE" in
    start|end) ;;
    *) refuse "mode must be start or end" ;;
esac

TAG=${2:-}
if [ -n "$TAG" ]; then
    case "$TAG" in
        _*) OUTNAME="GATE_R9M1R4_${MODE}${TAG}.txt" ;;
        GATE_*) OUTNAME="$TAG" ;;
        *) OUTNAME="GATE_R9M1R4_${MODE}_${TAG}.txt" ;;
    esac
else
    OUTNAME="GATE_R9M1R4_${MODE}.txt"
fi

if [ -n "${3:-}" ]; then
    EV="$3"
    mkdir -p "$EV/tmp"
    export TMPDIR="$EV/tmp"
fi

OUT="$EV/$OUTNAME"
test ! -e "$OUT" || refuse "exists: $OUTNAME"

ROUND_TAG="r9m1r4"
ROUND_NAME="M1R4"
ALLOW_START="$REPO/testing/d003/stage_s4r9/gate_allow_r9m1r4_start.txt"
ALLOW_END="$REPO/testing/d003/stage_s4r9/gate_allow_r9m1r4_end.txt"
STARTF="$REPO/checkpoints/p05/evidence/p05-s4r9/m1r4/GATE_R9M1R4_start.txt"

test -f "$ALLOW_START" || refuse "allow list (start) missing"
test -f "$ALLOW_END" || refuse "allow list (end) missing"

if [ "$MODE" = end ]; then
    test -f "$STARTF" || refuse "start file missing: $STARTF"
    case "$(head -n 1 "$STARTF")" in
        *"gate_r9m1r4 (start) ->"*) ;;
        *) refuse "start file header is not a gate_r9m1r4 start" ;;
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
printf "# P05-S4 R9 gate_r9m1r4 (%s) -> %s, utc=%s\n" "$MODE" "$OUTNAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"

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

BASE=4e9ff8be523bbf52a6b11757a6e04405a4a114e9
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

case "$MODE" in
    start)
        check ALLOW_START_LINES 5 "$(wc -l < "$ALLOW_START" | tr -d ' ')"
        check TRACKED_TESTING_D003_WORKTREE_NONE "" "$(git diff --name-only HEAD -- testing/d003)" ;;
    end)
        check ALLOW_START_SHA256_EQ_START "$(recval "$STARTF" ALLOW_START_SHA256)" "$(sha256sum "$ALLOW_START" | cut -d' ' -f1)"
        check TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START "" "$(git diff --name-only --diff-filter=MD "$BASE" -- testing/d003)" ;;
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
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m1r4.py" "$MODE" "$STARTF" "$EV" > "$PY_OUT"
PY_RET=$?
cat "$PY_OUT" >> "$OUT"

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
case "$MODE" in
    start)
        record TMP_COUNT_START "$TC"
        record TMP_SHA256_START "$TS" ;;
    end)
        check TMP_COUNT_EQ_START "$(recval "$STARTF" TMP_COUNT_START)" "$TC"
        check TMP_SHA256_EQ_START "$(recval "$STARTF" TMP_SHA256_START)" "$TS" ;;
esac

# ---- FAILS verification and self-check ----
TAB=$(printf '\t')
ACTUAL_FAIL_LINES=$(grep -c "^FAIL${TAB}" "$OUT" || true)
printf 'FAILS=%s\n' "$ACTUAL_FAIL_LINES" >> "$OUT"

EXIT_CODE=$ACTUAL_FAIL_LINES
if [ "$EXIT_CODE" -gt 255 ]; then
    EXIT_CODE=255
fi

if [ "$ACTUAL_FAIL_LINES" -ne 0 ]; then
    echo "gate_r9m1r4: $MODE FAILED: fail_lines=$ACTUAL_FAIL_LINES -> $OUT" >&2
    exit "$EXIT_CODE"
fi
echo "gate_r9m1r4: $MODE PASS: FAILS=0, fail_lines=0 -> $OUT"
exit 0
