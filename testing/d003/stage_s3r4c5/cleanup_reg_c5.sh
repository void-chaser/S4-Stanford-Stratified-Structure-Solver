REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# cleanup_reg_c5.sh -- remove the partial registry directory left by the first copy_registries_c5.sh run (only GATE_CONT5.txt,
# identical to the evidence copy, checked with cmp).  Removes exactly one named file and then the directory with rmdir.
set -u
REG="$REPO/checkpoints/p05/registries/s3r4c5"
test -d "$REG" || { echo "no directory: $REG"; exit 0; }
cmp "$EV/GATE_CONT5.txt" "$REG/GATE_CONT5.txt" || { echo "REFUSED: leftover file differs from evidence copy"; exit 2; }
rm -- "$REG/GATE_CONT5.txt" || { echo "rm failed"; exit 2; }
rmdir -- "$REG" || { echo "rmdir failed"; exit 2; }
echo "cleaned: $REG"
