REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_a_c3.sh -- P05-S3R4 CONT3 self-check A entry point (new file).
# Usage (through safe_run only):
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_a_c3.sh prereg-ctrl
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_a_c3.sh ctrl
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_a_c3.sh inj
# prereg-ctrl : writes REGISTRY_S3R4C3_A_CTRL.tsv (expectations of the 6 controls) BEFORE any control run.
# ctrl        : runs the 6 no-injection controls.
# inj         : runs the 18 rows of REGISTRY_S3R4C2_A.tsv, two passes each (36 runs).
export REPO EV
PHASE=${1:?"phase: prereg-ctrl | ctrl | inj"}
case "$PHASE" in
    prereg-ctrl)
        CTRL="$EV/REGISTRY_S3R4C3_A_CTRL.tsv"
        if [ -e "$CTRL" ]; then echo "REFUSED: exists $CTRL"; exit 2; fi
        {
            printf 'combo\tmode\tNG\ttree\tpoint_id\tinj_spec\texpected_class\texpected_rc1\tstatus\n'
            for T in F2 F3; do
                printf 'closed2d-ng1\tclosed2d\t1\t%s\tCTRL\t-\tCONTROL_OK\t0\tINFLUENCED\n' "$T"
                printf 'fft-ng5\tfft\t5\t%s\tCTRL\t-\tCONTROL_OK\t0\tINFLUENCED\n' "$T"
                printf 'kottke-ng5\tkottke\t5\t%s\tCTRL\t-\tCONTROL_OK\t0\tINFLUENCED\n' "$T"
            done
        } > "$CTRL"
        echo "prereg ctrl written utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        sha256sum "$CTRL"
        ;;
    ctrl)
        python3 "$REPO/testing/d003/stage_s3r4c3/run_a_c3.py" ctrl
        ;;
    inj)
        python3 "$REPO/testing/d003/stage_s3r4c3/run_a_c3.py" inj
        ;;
    *) echo "unknown phase $PHASE"; exit 2 ;;
esac
