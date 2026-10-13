REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_c3.sh -- copy the small CONT3 tables into checkpoints/p05/registries/s3r4c3/ (committed) and verify each
# copy against its original by sha256 (brief section 4).  Writes SHA256SUMS.txt (standard format) and a check record.
set -u
REG="$REPO/checkpoints/p05/registries/s3r4c3"
mkdir -p "$REG" || exit 2
for F in GATE_CONT3.txt GATE_CONT3_END.txt PRERUN_CHECKS_C3.txt \
         REGISTRY_S3R4C3_A_CTRL.tsv REGISTRY_S3R4C3_B.tsv REGISTRY_S3R4C3_D.tsv \
         RESULTS_S3R4C3_A.tsv RESULTS_S3R4C3_A_CTRL.tsv RESULTS_S3R4C3_B.tsv RESULTS_S3R4C3_B_CTRL.tsv \
         B_MAP_C3.tsv NM_CHECK_POLY_C3.txt RED_POINTS_STATUS_S3R4C3.tsv R8_ADDITIONS_S3R4C3.tsv \
         U100_SOURCE_NOTE.md D_STATUS_C3.txt SEAM_ANCHOR_CHECK_F3_C3.txt PREREG_B_RECORD_C3.txt; do
  cp "$EV/$F" "$REG/$F" || { echo "COPY FAILED $F"; exit 2; }
done
cd "$REG" || exit 2
sha256sum GATE_CONT3.txt GATE_CONT3_END.txt PRERUN_CHECKS_C3.txt \
  REGISTRY_S3R4C3_A_CTRL.tsv REGISTRY_S3R4C3_B.tsv REGISTRY_S3R4C3_D.tsv \
  RESULTS_S3R4C3_A.tsv RESULTS_S3R4C3_A_CTRL.tsv RESULTS_S3R4C3_B.tsv RESULTS_S3R4C3_B_CTRL.tsv \
  B_MAP_C3.tsv NM_CHECK_POLY_C3.txt RED_POINTS_STATUS_S3R4C3.tsv R8_ADDITIONS_S3R4C3.tsv \
  U100_SOURCE_NOTE.md D_STATUS_C3.txt SEAM_ANCHOR_CHECK_F3_C3.txt PREREG_B_RECORD_C3.txt > SHA256SUMS.txt
echo "copied and sums written"
cd "$REPO" || exit 2
sha256sum -c "$REG/SHA256SUMS.txt" > "$EV/tmp/registry_sums_check.txt" 2>&1
echo "registry sums check rc=$?"
