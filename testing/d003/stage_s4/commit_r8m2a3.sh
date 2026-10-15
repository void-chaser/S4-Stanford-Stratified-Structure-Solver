REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m2a3.sh -- P05-S4 R8 M2a3 commit. Run through safe_run only, after the end gate reports FAILS=0.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a3 -- sh testing/d003/stage_s4/commit_r8m2a3.sh p05-s4r8/m2a3
set -u
[ "${1:-}" = p05-s4r8/m2a3 ] || { echo "commit_r8m2a3: first argument must be p05-s4r8/m2a3" >&2; exit 2; }
MSG="P05-S4 R8 M2a3 (r8m2a3): E8-96..E8-100, executability audit (174 gaps), effective prereg frozen (150 rows sha 27e33b27...), call3 recovery & dual failure indices fixed, control mapping (28 pairs), state collection plan, posctrl A-K PASS (11/11), completeness PASS; awaiting user review"
cd "$REPO" || exit 2
git status --short -uall > "$EV/tmp/status_commit_r8m2a3.txt"
while IFS= read -r L; do
    [ -n "$L" ] || continue
    case "$L" in
        " M checkpoints/p05/STATE.md"|" M checkpoints/p05/registries/s4r8/ERRATA_8.txt") ;;
        "??"*" checkpoints/p05/P05_S4R8_M2A3_REPORT.md"|"??"*" checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a3.md") ;;
        "??"*" checkpoints/p05/registries/s4r8/M2/r8m2a3/"*) ;;
        "??"*" testing/d003/stage_s4/"*r8m2a3*) ;;
        *) echo "commit_r8m2a3: NOT ALLOWED status entry: $L" >&2; exit 3 ;;
    esac
done < "$EV/tmp/status_commit_r8m2a3.txt"

git add -- checkpoints/p05/STATE.md checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M2A3_REPORT.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a3.md \
    checkpoints/p05/registries/s4r8/M2/r8m2a3 || exit 4

for F in testing/d003/stage_s4/*r8m2a3*; do
    [ -e "$F" ] && git add -- "$F"
done

git diff --cached --name-only > "$EV/tmp/staged_commit_r8m2a3.txt"
while IFS= read -r F; do
    case "$F" in
        checkpoints/p05/STATE.md|checkpoints/p05/registries/s4r8/ERRATA_8.txt) ;;
        checkpoints/p05/P05_S4R8_M2A3_REPORT.md|checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a3.md) ;;
        checkpoints/p05/registries/s4r8/M2/r8m2a3/*) ;;
        testing/d003/stage_s4/*r8m2a3*) ;;
        *) echo "commit_r8m2a3: REFUSED staged path outside allow list: $F" >&2; exit 5 ;;
    esac
done < "$EV/tmp/staged_commit_r8m2a3.txt"

git commit -m "$MSG" || exit 6
echo "commit_r8m2a3: committed successfully"
exit 0
