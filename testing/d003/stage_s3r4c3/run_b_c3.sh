REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_b_c3.sh -- P05-S3R4 CONT3 self-check B entry point (new file).
# Usage (through safe_run only):
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_b_c3.sh ctrl
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_b_c3.sh inj
# ctrl : 12 no-injection controls (tree x combo).  inj : 12 injection rows x 2 passes (DUPLICATE rows skipped).
export REPO EV
PHASE=${1:?"phase: ctrl | inj"}
case "$PHASE" in
    ctrl|inj) python3 "$REPO/testing/d003/stage_s3r4c3/run_b_c3.py" "$PHASE" ;;
    *) echo "unknown phase $PHASE"; exit 2 ;;
esac
