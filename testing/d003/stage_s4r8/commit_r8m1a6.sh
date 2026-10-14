#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m1a6.sh -- record commit for P05-S4 R8 M1a cont3b1 fix (r8m1a6). New file.
set -u
refuse() { echo "commit_r8m1a6: REFUSED: $1" >&2; exit 2; }

# 1. Pre-commit check
test -f "$REPO/checkpoints/p05/STATE.md" || refuse "STATE.md missing"
test -f "$REPO/checkpoints/p05/registries/RULINGS.tsv" || refuse "RULINGS.tsv missing"
test -f "$REPO/checkpoints/p05/registries/s4r8/ERRATA_8.txt" || refuse "ERRATA_8.txt missing"
test -f "$REPO/checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1_FIX.md" || refuse "report missing"
test -f "$REPO/checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1_FIX.md" || refuse "brief missing"

# 2. Path-by-path git add
git add -- \
    checkpoints/p05/STATE.md \
    checkpoints/p05/registries/RULINGS.tsv \
    checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1_FIX.md \
    checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1_FIX.md \
    checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a6_END.txt \
    checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a6_START.txt \
    checkpoints/p05/registries/s4r8/M1a/HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt \
    checkpoints/p05/registries/s4r8/M1a/HIST_GATE_R8_M1a5_END_R8_M1a6.txt \
    checkpoints/p05/registries/s4r8/M1a/K_SOURCE_PLANCALL58_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/PREREG_COUNTS_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/PREREG_INPUTS_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/PREREG_RECORD_R8_M1a6.txt \
    checkpoints/p05/registries/s4r8/M1a/PREREG_ROW_SOURCES_MAPPING_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/PREREG_STOP_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_R8_M1a6.txt \
    checkpoints/p05/registries/s4r8/M1a/STATE_ITEM_CROSSWALK_R8_M1a6.tsv \
    checkpoints/p05/registries/s4r8/M1a/STATE_PRE_R8_M1a6.md \
    checkpoints/p05/registries/s4r8/M1a/VERIFY_PREREG_R8_M1a6.txt \
    testing/d003/stage_s4r8/commit_r8m1a6.sh \
    testing/d003/stage_s4r8/compact_state_and_crosswalk_r8m1a6.py \
    testing/d003/stage_s4r8/copy_r8m1a6.sh \
    testing/d003/stage_s4r8/copy_snapshots_r8m1a6.sh \
    testing/d003/stage_s4r8/gate13_r8m1a6.sh \
    testing/d003/stage_s4r8/gate_allow_r8m1a6_end.txt \
    testing/d003/stage_s4r8/gate_allow_r8m1a6_start.txt \
    testing/d003/stage_s4r8/make_prereg_r8m1a6.py \
    testing/d003/stage_s4r8/record_prereg_r8m1a6.sh \
    testing/d003/stage_s4r8/run_compact_state_r8m1a6.sh \
    testing/d003/stage_s4r8/run_make_prereg_r8m1a6.sh \
    testing/d003/stage_s4r8/run_verify_prereg_r8m1a6.sh \
    testing/d003/stage_s4r8/verify_prereg_r8m1a6.py

# 3. Commit
MSG="P05-S4 R8 M1a cont3b1 fix: formal preregistration, baseline control contract, STATE <=8KiB, record corrections (no runs); awaiting user review"
git commit -m "$MSG"

# 4. Post-commit recording
POST_FILE="$EV/FINAL_GIT_R8_M1a6_POST.txt"
: > "$POST_FILE"
printf '# FINAL_GIT_R8_M1a6_POST.txt utc=%s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$POST_FILE"
printf '## git log -1\n' >> "$POST_FILE"
git log -1 >> "$POST_FILE"
printf '\n## git log -3 --oneline\n' >> "$POST_FILE"
git log -3 --oneline >> "$POST_FILE"
printf '\n## git status --short\n' >> "$POST_FILE"
git status --short >> "$POST_FILE"
printf '\n## git rev-parse HEAD:S4\n' >> "$POST_FILE"
git rev-parse HEAD:S4 >> "$POST_FILE"

echo "commit_r8m1a6: SUCCESS -> $POST_FILE"
exit 0
