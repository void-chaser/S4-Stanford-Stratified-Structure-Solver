#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_snapshots_r8m1a6.sh -- snapshot historical inputs into registries/s4r8/M1a/ and $EV per U201 and section 6.
set -u
refuse() { echo "copy_snapshots_r8m1a6: REFUSED: $1" >&2; exit 2; }

REG="$REPO/checkpoints/p05/registries/s4r8/M1a"
mkdir -p "$REG" "$EV"

# 1. ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv
SRC_ADD="$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv"
DST_ADD_REG="$REG/ADDITIONS_MAPPING_22_R8_M1a6.tsv"
DST_ADD_EV="$EV/ADDITIONS_MAPPING_22_R8_M1a6.tsv"
test -f "$SRC_ADD" || refuse "SRC_ADD missing: $SRC_ADD"
test ! -e "$DST_ADD_REG" || refuse "DST_ADD_REG exists (U17): $DST_ADD_REG"
test ! -e "$DST_ADD_EV" || refuse "DST_ADD_EV exists (U17): $DST_ADD_EV"
EXPECT_ADD_SHA="b7d1f86d293648cc3182f9bce7f95e26943c52885af1995384a9fd801bd2550a"
ACTUAL_ADD_SHA=$(sha256sum "$SRC_ADD" | cut -d' ' -f1)
[ "$ACTUAL_ADD_SHA" = "$EXPECT_ADD_SHA" ] || refuse "SRC_ADD sha mismatch: expected $EXPECT_ADD_SHA, got $ACTUAL_ADD_SHA"
cp "$SRC_ADD" "$DST_ADD_REG"
cp "$SRC_ADD" "$DST_ADD_EV"

# 2. STATE_PRE_R8_M1a6.md (archive current HEAD STATE.md before compaction)
SRC_STATE="$REPO/checkpoints/p05/STATE.md"
DST_STATE_REG="$REG/STATE_PRE_R8_M1a6.md"
DST_STATE_EV="$EV/STATE_PRE_R8_M1a6.md"
test -f "$SRC_STATE" || refuse "SRC_STATE missing: $SRC_STATE"
test ! -e "$DST_STATE_REG" || refuse "DST_STATE_REG exists (U17): $DST_STATE_REG"
test ! -e "$DST_STATE_EV" || refuse "DST_STATE_EV exists (U17): $DST_STATE_EV"
EXPECT_STATE_SHA="b99e2559c69dda86beea5196a47e638f2edbe97e7fe7bedecbe225ca3732e85e"
ACTUAL_STATE_SHA=$(sha256sum "$SRC_STATE" | cut -d' ' -f1)
[ "$ACTUAL_STATE_SHA" = "$EXPECT_STATE_SHA" ] || refuse "SRC_STATE sha mismatch"
cp "$SRC_STATE" "$DST_STATE_REG"
cp "$SRC_STATE" "$DST_STATE_EV"

# 3. HIST_GATE_R8_M1a5_END_R8_M1a6.txt (verbatim copy of old GATE_R8_M1a5_END.txt)
SRC_GATE="$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5/GATE_R8_M1a5_END.txt"
DST_GATE_REG="$REG/HIST_GATE_R8_M1a5_END_R8_M1a6.txt"
DST_GATE_EV="$EV/HIST_GATE_R8_M1a5_END_R8_M1a6.txt"
test -f "$SRC_GATE" || refuse "SRC_GATE missing: $SRC_GATE"
test ! -e "$DST_GATE_REG" || refuse "DST_GATE_REG exists (U17): $DST_GATE_REG"
test ! -e "$DST_GATE_EV" || refuse "DST_GATE_EV exists (U17): $DST_GATE_EV"
EXPECT_GATE_SHA="2871877df585747e2294d9eaa3e254e1e44b913cabc63b0c7cbe768e62bddad5"
ACTUAL_GATE_SHA=$(sha256sum "$SRC_GATE" | cut -d' ' -f1)
[ "$ACTUAL_GATE_SHA" = "$EXPECT_GATE_SHA" ] || refuse "SRC_GATE sha mismatch"
cp "$SRC_GATE" "$DST_GATE_REG"
cp "$SRC_GATE" "$DST_GATE_EV"

# 4. HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt (old HEAD f1cbefe commit details and post state)
DST_COMMIT_REG="$REG/HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt"
DST_COMMIT_EV="$EV/HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt"
test ! -e "$DST_COMMIT_REG" || refuse "DST_COMMIT_REG exists (U17): $DST_COMMIT_REG"
test ! -e "$DST_COMMIT_EV" || refuse "DST_COMMIT_EV exists (U17): $DST_COMMIT_EV"

INFO_FILE="$EV/tmp/commit_info.txt"
: > "$INFO_FILE"
printf '# HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt\n' >> "$INFO_FILE"
printf '# Note: Old round FAILS=2 gate end snapshot exists in HIST_GATE_R8_M1a5_END_R8_M1a6.txt.\n' >> "$INFO_FILE"
printf '# Note: Worktree state at current round start is NOT identical to post-commit state of f1cbefe.\n' >> "$INFO_FILE"
printf '# Historical clean post state is recorded in checkpoints/p05/evidence/p05-s4r8/m1a5/FINAL_GIT_R8_M1a5.txt.\n' >> "$INFO_FILE"
printf '\n## git show --stat f1cbefe84001c5957532133377f77d1d003e48c6\n' >> "$INFO_FILE"
git show --stat f1cbefe84001c5957532133377f77d1d003e48c6 >> "$INFO_FILE"
printf '\n## Historical FINAL_GIT_R8_M1a5.txt content\n' >> "$INFO_FILE"
head -n 20 "$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5/FINAL_GIT_R8_M1a5.txt" >> "$INFO_FILE"

cp "$INFO_FILE" "$DST_COMMIT_REG"
cp "$INFO_FILE" "$DST_COMMIT_EV"

# 5. Check and summarize all snapshot files
LOG="$EV/SNAPSHOTS_CHECK_R8_M1a6.txt"
: > "$LOG"
printf '# SNAPSHOTS_CHECK_R8_M1a6.txt utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
sha256sum "$DST_ADD_REG" "$DST_ADD_EV" >> "$LOG"
sha256sum "$DST_STATE_REG" "$DST_STATE_EV" >> "$LOG"
sha256sum "$DST_GATE_REG" "$DST_GATE_EV" >> "$LOG"
sha256sum "$DST_COMMIT_REG" "$DST_COMMIT_EV" >> "$LOG"

echo "copy_snapshots_r8m1a6: SUCCESS -> $LOG"
exit 0
