REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m2a.sh -- P05-S4 R8 M2a commit.  New file.  Run through safe_run only, after the end gate reports FAILS=0.
# It checks the git status against the end allow list, adds ONLY the named paths, and commits.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a -- sh testing/d003/stage_s4/commit_r8m2a.sh p05-s4r8/m2a
set -u
[ "${1:-}" = p05-s4r8/m2a ] || { echo "commit_r8m2a: first argument must be p05-s4r8/m2a" >&2; exit 2; }
MSG="P05-S4 R8 M2a (r8m2a): U229-U235, E8-88..E8-90, A-10 control crosswalk, apparatus inventory, M2 design (12 items), M2-01 prereg frozen (17 rows), verdict posctrl on synthetic data; STOPPED at end gate NO_STRAY_BUILD_PRODUCTS_END (FAILS=1: testing/d003/__pycache__ from this round); new apparatus build and M2-02..M2-10 points not done; no S4 driver run; awaiting user review"
cd "$REPO" || exit 2
# 1. the status must contain only the allowed entries (end allow list, same as gate_allow_r8m2a_end.txt)
git status --short -uall > "$EV/tmp/status_commit_r8m2a.txt"
while IFS= read -r L; do
    [ -n "$L" ] || continue
    case "$L" in
        " M checkpoints/p05/STATE.md"|" M checkpoints/p05/registries/RULINGS.tsv"|" M checkpoints/p05/registries/s4r8/ERRATA_8.txt") ;;
        "?? checkpoints/p05/P05_S4R8_M2A_REPORT.md"|"?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md") ;;
        "?? checkpoints/p05/registries/s4r8/M2/r8m2a/"*) ;;
        "?? testing/d003/stage_s4/"*r8m2a*) ;;
        *) echo "commit_r8m2a: NOT ALLOWED status entry: $L" >&2; exit 3 ;;
    esac
done < "$EV/tmp/status_commit_r8m2a.txt"
# 2. add only the named paths (never git add -A)
git add -- checkpoints/p05/STATE.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M2A_REPORT.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md \
    checkpoints/p05/registries/s4r8/M2/r8m2a || exit 4
for F in testing/d003/stage_s4/*r8m2a*; do
    [ -e "$F" ] && git add -- "$F"
done
# 3. only the r8m2a files of testing/d003/stage_s4 may be staged: unstage anything else (safety check)
git diff --cached --name-only > "$EV/tmp/staged_commit_r8m2a.txt"
while IFS= read -r F; do
    case "$F" in
        checkpoints/p05/STATE.md|checkpoints/p05/registries/RULINGS.tsv|checkpoints/p05/registries/s4r8/ERRATA_8.txt) ;;
        checkpoints/p05/P05_S4R8_M2A_REPORT.md|checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md) ;;
        checkpoints/p05/registries/s4r8/M2/r8m2a/*) ;;
        testing/d003/stage_s4/*r8m2a*) ;;
        *) echo "commit_r8m2a: REFUSED staged path outside the allow list: $F" >&2; exit 5 ;;
    esac
done < "$EV/tmp/staged_commit_r8m2a.txt"
git commit -m "$MSG" || exit 6
echo "commit_r8m2a: committed"
exit 0
