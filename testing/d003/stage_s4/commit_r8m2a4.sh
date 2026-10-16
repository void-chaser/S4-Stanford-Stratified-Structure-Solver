REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m2a4.sh -- P05-S4 R8 M2a4 commit. Run through safe_run only, after the end gate reports FAILS=0.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a4 -- sh testing/d003/stage_s4/commit_r8m2a4.sh p05-s4r8/m2a4
set -u
[ "${1:-}" = p05-s4r8/m2a4 ] || { echo "commit_r8m2a4: first argument must be p05-s4r8/m2a4" >&2; exit 2; }
MSG="P05-S4 R8 M2a4 (r8m2a4): U248..U252, E8-101..E8-103, execution chain complete (dry-run 300 rows, facts extractor, state judge, verdict v2), defect audit (12 items), effective prereg v2 (150 rows sha ee46fecf...), R6c replay 2124/2124 diff 0, posctrl 19/19 PASS, completeness 131 PASS + 19 UNJUDGED = 150; awaiting user review"
cd "$REPO" || exit 2
git status --short -uall > "$EV/tmp/status_commit_r8m2a4.txt"
while IFS= read -r L; do
    [ -n "$L" ] || continue
    case "$L" in
        " M checkpoints/p05/STATE.md"|" M checkpoints/p05/registries/RULINGS.tsv"|" M checkpoints/p05/registries/s4r8/ERRATA_8.txt") ;;
        "??"*" checkpoints/p05/P05_S4R8_M2A4_REPORT.md"|"??"*" checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a4.md") ;;
        "??"*" checkpoints/p05/registries/s4r8/M2/r8m2a4/"*) ;;
        "??"*" testing/d003/stage_s4/"*r8m2a4*) ;;
        *) echo "commit_r8m2a4: NOT ALLOWED status entry: $L" >&2; exit 3 ;;
    esac
done < "$EV/tmp/status_commit_r8m2a4.txt"

git add -- checkpoints/p05/STATE.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M2A4_REPORT.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a4.md \
    checkpoints/p05/registries/s4r8/M2/r8m2a4 || exit 4

for F in testing/d003/stage_s4/*r8m2a4*; do
    [ -e "$F" ] && git add -- "$F"
done

git diff --cached --name-only > "$EV/tmp/staged_commit_r8m2a4.txt"
while IFS= read -r F; do
    case "$F" in
        checkpoints/p05/STATE.md|checkpoints/p05/registries/RULINGS.tsv|checkpoints/p05/registries/s4r8/ERRATA_8.txt) ;;
        checkpoints/p05/P05_S4R8_M2A4_REPORT.md|checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a4.md) ;;
        checkpoints/p05/registries/s4r8/M2/r8m2a4/*) ;;
        testing/d003/stage_s4/*r8m2a4*) ;;
        *) echo "commit_r8m2a4: REFUSED staged path outside allow list: $F" >&2; exit 5 ;;
    esac
done < "$EV/tmp/staged_commit_r8m2a4.txt"

git commit -m "$MSG" || exit 6
echo "commit_r8m2a4: committed successfully"
