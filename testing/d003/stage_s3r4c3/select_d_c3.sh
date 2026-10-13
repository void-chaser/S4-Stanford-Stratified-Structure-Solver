REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# select_d_c3.sh -- entry point for select_d_c3.py (new file).  Writes REGISTRY_S3R4C3_D.tsv once (refuses to overwrite).
export REPO EV
python3 "$REPO/testing/d003/stage_s3r4c3/select_d_c3.py"
