REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# export_f3_c3.sh -- export the F3 tree (commit 8d8202a, S4/ = 6cff923a...) to $EV for the CTRL_SEAM anchor check.
# Read-only with respect to the repository (git archive only reads objects).  Output: $EV/f3_export/S4/...
set -u
D="$EV/f3_export"
test -e "$D" && { echo "REFUSED: exists $D"; exit 2; }
mkdir -p "$D" || exit 2
git archive 8d8202a S4 | tar -x -C "$D" > "$EV/export_f3_archive.log" 2>&1
echo "archive rc=$?"
TREE=$(git rev-parse 8d8202a:S4)
echo "F3 S4 tree=$TREE"
echo "exported S4 tree sha=$(cd "$D" && find S4 -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)"
