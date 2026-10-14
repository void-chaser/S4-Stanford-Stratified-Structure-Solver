#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_r8m1a6.sh -- copy small tables and records to registries/s4r8/M1a/, verify sha256 and write manifests.
set -u
refuse() { echo "copy_r8m1a6: REFUSED: $1" >&2; exit 2; }

REG="$REPO/checkpoints/p05/registries/s4r8/M1a"
test -d "$REG" || refuse "REG missing: $REG"
test -d "$EV" || refuse "EV missing: $EV"

FILES="
REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv
REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv
PREREG_INPUTS_R8_M1a6.tsv
PREREG_COUNTS_R8_M1a6.tsv
PREREG_STOP_R8_M1a6.tsv
PREREG_RECORD_R8_M1a6.txt
K_SOURCE_PLANCALL58_R8_M1a6.tsv
PREREG_ROW_SOURCES_MAPPING_R8_M1a6.tsv
VERIFY_PREREG_R8_M1a6.txt
GATE_R8_M1a6_START.txt
GATE_R8_M1a6_END.txt
STATE_ITEM_CROSSWALK_R8_M1a6.tsv
STATE_PRE_R8_M1a6.md
ADDITIONS_MAPPING_22_R8_M1a6.tsv
HIST_GATE_R8_M1a5_END_R8_M1a6.txt
HIST_COMMIT_F1CBEFE_POST_R8_M1a6.txt
"

for f in $FILES; do
    src="$EV/$f"
    dst="$REG/$f"
    test -f "$src" || refuse "source missing: $src"
    if [ ! -f "$dst" ]; then
        cp "$src" "$dst"
    fi
    cmp -s "$src" "$dst" || refuse "cmp failed for $f"
done

# Write new SHA256SUMS_R8_M1a6.txt in registries/s4r8/M1a/
REG_MANIFEST="$REG/SHA256SUMS_R8_M1a6.txt"
test ! -e "$REG_MANIFEST" || refuse "REG_MANIFEST exists (U17): $REG_MANIFEST"

: > "$REG_MANIFEST"
for f in $FILES; do
    (cd "$REG" && sha256sum "$f") >> "$REG_MANIFEST"
done

# Verify manifest in registries
(cd "$REG" && sha256sum -c "$REG_MANIFEST") || refuse "registry sha256sum -c failed"

# Write evidence manifest in EV (excluding live logs, manifests, and future post files)
EV_MANIFEST="$EV/SHA256SUMS_EVIDENCE_R8_M1a6.txt"
test ! -e "$EV_MANIFEST" || refuse "EV_MANIFEST exists (U17): $EV_MANIFEST"

: > "$EV_MANIFEST"
printf '# SHA256SUMS_EVIDENCE_R8_M1a6.txt -- static evidence manifest at freeze point\n' >> "$EV_MANIFEST"
printf '# Excluded: safe_run.log (live append log), SHA256SUMS* (self-reference), FINAL_GIT* (post commit)\n' >> "$EV_MANIFEST"
for f in $FILES; do
    (cd "$EV" && sha256sum "$f") >> "$EV_MANIFEST"
done

(cd "$EV" && sha256sum -c "$EV_MANIFEST") || refuse "evidence sha256sum -c failed"

echo "copy_r8m1a6: SUCCESS, all 16 files copied and verified"
exit 0
