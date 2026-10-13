REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prereg_b_c3.sh -- record sha256 and UTC of the B pre-registration BEFORE any B injection run (read only; writes a record).
REG="$EV/REGISTRY_S3R4C3_B.tsv"
test -f "$REG" || { echo "missing $REG"; exit 2; }
{
  echo "prereg B record utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sha256sum "$REG"
  echo "rows=$(wc -l < "$REG")"
} > "$EV/PREREG_B_RECORD_C3.txt"
cat "$EV/PREREG_B_RECORD_C3.txt"
