REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_c5.sh -- copy the small CONT5 tables to checkpoints/p05/registries/s3r4c5/ (committed), verify each copy
# against its original by sha256, write SHA256SUMS.txt (standard format) and check it from inside the registry directory.
set -u
REG="$REPO/checkpoints/p05/registries/s3r4c5"
test -e "$REG" && { echo "REFUSED: exists $REG"; exit 2; }
mkdir -p "$REG" || exit 2
# only files that exist in $EV (the list is fixed; a missing file stops the copy)
LIST="GATE_CONT5.txt GATE_CONT5_END.txt PRERUN_CHECKS_C5.txt DIFF_INJECT_C3.txt DIFF_LINK_C3.txt PREREG_D_RECORD_C3.txt BINARIES_C3.tsv SHA256SUMS_P05-S3R4C3.txt SHA256SUMS_P05-S3R4C3_EXCLUDED.txt SHA256SUMS_P05-S3R4C3_CHECK.txt EXPECT_RESOLUTION_C5.txt CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv status_before_rec_c5.txt commit_rec_c5_oneline.txt"
for F in $LIST; do
  test -e "$EV/$F" || { echo "MISSING $F"; exit 2; }
  cp "$EV/$F" "$REG/$F" || { echo "COPY FAILED $F"; exit 2; }
done
# verify each copy against its original (sha256 of original and copy)
: > "$EV/tmp/copy_compare_c5.txt"
for F in $LIST; do
  a=$(sha256sum "$EV/$F" | cut -d' ' -f1)
  b=$(sha256sum "$REG/$F" | cut -d' ' -f1)
  if [ "$a" = "$b" ]; then r=SAME; else r=DIFFERENT; fi
  printf '%s\t%s\t%s\t%s\n' "$F" "$a" "$b" "$r" >> "$EV/tmp/copy_compare_c5.txt"
done
cp "$EV/tmp/copy_compare_c5.txt" "$EV/COPY_COMPARE_C5.txt"
# standard-format manifest of the registry copies, then verified from inside the registry directory
cd "$REG" || exit 2
sha256sum $LIST > SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt > "$EV/SHA256SUMS_REGISTRY_S3R4C5_CHECK.txt" 2>&1
echo "registry sums check rc=$?"
cd "$REPO" || exit 2
echo "copy compare: $(awk -F'\t' '$4=="SAME"' "$EV/COPY_COMPARE_C5.txt" | wc -l) SAME of $(wc -l < "$EV/COPY_COMPARE_C5.txt")"
