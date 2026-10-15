REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m2a2.sh -- P05-S4 R8 M2a2 commit. Run through safe_run only, after the end gate reports FAILS=0.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- sh testing/d003/stage_s4/commit_r8m2a2.sh p05-s4r8/m2a2
set -u
[ "${1:-}" = p05-s4r8/m2a2 ] || { echo "commit_r8m2a2: first argument must be p05-s4r8/m2a2" >&2; exit 2; }
MSG="P05-S4 R8 M2a2 (r8m2a2): U236-U247, E8-91..E8-95, r8m2a end-gate registry backfill, baseline stray gate, M2 design v3, new apparatus build (18/0), M2 prereg frozen (150 rows incl. 90 control), posctrl A-E; stage-e/catC tables regenerated (R2), index derivation R2, deviations disclosed; no S4 driver run; awaiting user review"
cd "$REPO" || exit 2
git status --short -uall > "$EV/tmp/status_commit_r8m2a2.txt"
while IFS= read -r L; do
    [ -n "$L" ] || continue
    case "$L" in
        " M checkpoints/p05/STATE.md"|" M checkpoints/p05/registries/RULINGS.tsv"|" M checkpoints/p05/registries/s4r8/ERRATA_8.txt") ;;
        "??"*" checkpoints/p05/P05_S4R8_M2A2_REPORT.md"|"??"*" checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md") ;;
        "??"*" checkpoints/p05/registries/s4r8/M2/r8m2a2/"*) ;;
        "??"*" checkpoints/p05/registries/s4r8/M2/r8m2a/GATE_R8_M2a_end"*) ;;
        "??"*" checkpoints/p05/registries/s4r8/M2/r8m2a/POSTCOMMIT_R8_M2a.txt"|"??"*" checkpoints/p05/registries/s4r8/M2/r8m2a/SHA256SUMS_END.txt") ;;
        "??"*" testing/d003/stage_s4/"*r8m2a2*) ;;
        *) echo "commit_r8m2a2: NOT ALLOWED status entry: $L" >&2; exit 3 ;;
    esac
done < "$EV/tmp/status_commit_r8m2a2.txt"

git add -- checkpoints/p05/STATE.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M2A2_REPORT.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md \
    checkpoints/p05/registries/s4r8/M2/r8m2a2 checkpoints/p05/registries/s4r8/M2/r8m2a || exit 4

for F in testing/d003/stage_s4/*r8m2a2*; do
    [ -e "$F" ] && git add -- "$F"
done

git diff --cached --name-only > "$EV/tmp/staged_commit_r8m2a2.txt"
while IFS= read -r F; do
    case "$F" in
        checkpoints/p05/STATE.md|checkpoints/p05/registries/RULINGS.tsv|checkpoints/p05/registries/s4r8/ERRATA_8.txt) ;;
        checkpoints/p05/P05_S4R8_M2A2_REPORT.md|checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md) ;;
        checkpoints/p05/registries/s4r8/M2/r8m2a2/*|checkpoints/p05/registries/s4r8/M2/r8m2a/*) ;;
        testing/d003/stage_s4/*r8m2a2*) ;;
        *) echo "commit_r8m2a2: REFUSED staged path outside allow list: $F" >&2; exit 5 ;;
    esac
done < "$EV/tmp/staged_commit_r8m2a2.txt"

git commit -m "$MSG" || exit 6
echo "commit_r8m2a2: committed successfully"
exit 0
