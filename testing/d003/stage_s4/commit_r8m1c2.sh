#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m1c2.sh -- commits the R8 M1c2 record (AGENTS.md section 4 scope: checkpoints/p05 and testing/d003).
# Checks git status against the explicit file list before staging; stages only those files (no 'git add -A').
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- sh testing/d003/stage_s4/commit_r8m1c2.sh
set -u
refuse() { echo "commit_r8m1c2: REFUSED: $1" >&2; exit 2; }
cd "$REPO" || refuse "cannot cd to repo"
[ "$(git rev-parse HEAD)" = f913b57a487f4ae64ff6f9d1d48136e99ae65e77 ] || refuse "HEAD is not the round base f913b57"

ST=$EV/tmp/commit_status_r8m1c2.txt
git status --short -uall > "$ST"
bad=0
while IFS= read -r l; do
    [ -n "$l" ] || continue
    case "$l" in
        ' M checkpoints/p05/STATE.md'|' M checkpoints/p05/registries/RULINGS.tsv'|' M checkpoints/p05/registries/s4r8/ERRATA_8.txt') ;;
        '?? checkpoints/p05/P05_S4R8_M1C2_REPORT.md'|'?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md') ;;
        '?? checkpoints/p05/registries/s4r8/M1c/r8m1c2/'*) ;;
        '?? testing/d003/stage_s4/'*r8m1c2*) ;;
        *) echo "commit_r8m1c2: NOT_ALLOWED $l"; bad=$((bad + 1)) ;;
    esac
done < "$ST"
[ "$bad" = 0 ] || refuse "status contains $bad line(s) outside the allowed commit scope"

# stage exactly the allowed paths
git add -- checkpoints/p05/STATE.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M1C2_REPORT.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c2.md \
    checkpoints/p05/registries/s4r8/M1c/r8m1c2 \
    testing/d003/stage_s4/append_end_registries_r8m1c2.py \
    testing/d003/stage_s4/append_errata_r8m1c2.sh testing/d003/stage_s4/append_rulings_r8m1c2.sh \
    testing/d003/stage_s4/build_errata_r8m1c2.py testing/d003/stage_s4/build_rulings_r8m1c2.py \
    testing/d003/stage_s4/compare_m1c_f2_r8m1c2.py testing/d003/stage_s4/copy_registries_r8m1c2.py \
    testing/d003/stage_s4/count_r7_f2_facts_r8m1c2.py testing/d003/stage_s4/count_r7_f2_facts_r8m1c2_R2.py \
    testing/d003/stage_s4/diff_gate_r8m1c2.sh \
    testing/d003/stage_s4/gate_allow_r8m1c2_end.txt testing/d003/stage_s4/gate_allow_r8m1c2_start.txt \
    testing/d003/stage_s4/gate_check_r8m1c2.py testing/d003/stage_s4/gate_r8m1c2.sh \
    testing/d003/stage_s4/make_prereg_m1c_facts_r8m1c2.py testing/d003/stage_s4/posctrl_m1c_r8m1c2.py \
    testing/d003/stage_s4/preflight_m1c_r8m1c2.py testing/d003/stage_s4/record_drivers_r8m1c2.py \
    testing/d003/stage_s4/run_m1c_r8m1c2.sh testing/d003/stage_s4/state_bytes_r8m1c2.py \
    testing/d003/stage_s4/sums_ev_r8m1c2.py testing/d003/stage_s4/commit_r8m1c2.sh \
    || refuse "git add failed"

git commit -q -m "P05-S4 R8 M1c2 (r8m1c2): U209-U217, E8-79/E8-80, M1c facts prereg, M1c F2 baseline vs R7 (DIFFS=0), posctrl; F3 deferred to r8m1c3; awaiting user review" || refuse "git commit failed"
git log -1 --format=%H%n%s
git status --short
exit 0
