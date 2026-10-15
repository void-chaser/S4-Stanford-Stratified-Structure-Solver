REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_m1c_r8m1c3.sh -- P05-S4 R8 M1c3 M1c runner (brief section 5). New file (copied from run_m1c_r8m1c2.sh; original unchanged).
# Changes from the r8m1c2 version: EV is m1c3; only F3 is accepted (F2 refused); the M1C_ALLOW_F3 gate is removed;
# driver records go to DRIVER_RUN_RECORD_R8_M1c3.tsv via record_drivers_r8m1c3.py.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/run_m1c_r8m1c3.sh F3
# Order (serial, no '&'): G5 pass1 -> G5 pass2 -> r6c_judge -> seam pass1 -> seam pass2 -> r6c2_seam_judge.
# Outputs: $EV/m1c_F3/ ; stdout of each call in $EV/m1c_F3/*.stdout ;
# driver sha256 before and after each runner call appended to $EV/DRIVER_RUN_RECORD_R8_M1c3.tsv.
set -u
refuse() { echo "run_m1c_r8m1c3: REFUSED: $1" >&2; exit 2; }
TREE=${1:-}
case "$TREE" in
    F3) ;;
    *) refuse "argument must be F3 (R8 M1c3 runs F3 only)" ;;
esac
OUTDIR="$EV/m1c_$TREE"
test ! -e "$OUTDIR" || refuse "output dir exists (U17): $OUTDIR"
mkdir -p "$OUTDIR" || refuse "cannot create $OUTDIR"

PREREG_G5="$REPO/checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv"
CONTROL_G5="$REPO/checkpoints/p05/registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv"
PREREG_SEAM="$REPO/checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv"
CONTROL_SEAM="$REPO/checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv"
EVROOT="$REPO/checkpoints/p05/evidence"
DRV_STATE="$EVROOT/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver"
DRV_SEAMF="$EVROOT/p05-s4r8/drivers_r8m1/r6bseam-seamF-F3/driver"
DRV_FMMRET="$EVROOT/p05-s4r8/drivers_r8m1/r6bseam-fmmret-F3/driver"

rec() { python3 -I -B "$REPO/testing/d003/stage_s4/record_drivers_r8m1c3.py" "$TREE" "$1" || refuse "driver record failed at $1"; }

cd "$REPO" || refuse "cannot cd to repo"

rec "before_g5_pass1"
python3 -I -B testing/d003/stage_s4/run_r6c_state.py full "$PREREG_G5" "$CONTROL_G5" "$DRV_STATE" "$OUTDIR" 1 > "$OUTDIR/run_g5_pass1.stdout" 2>&1
RC_G5P1=$?
rec "after_g5_pass1"
echo "run_m1c_r8m1c3: $TREE G5 pass1 rc=$RC_G5P1"

rec "before_g5_pass2"
python3 -I -B testing/d003/stage_s4/run_r6c_state.py full "$PREREG_G5" "$CONTROL_G5" "$DRV_STATE" "$OUTDIR" 2 > "$OUTDIR/run_g5_pass2.stdout" 2>&1
RC_G5P2=$?
rec "after_g5_pass2"
echo "run_m1c_r8m1c3: $TREE G5 pass2 rc=$RC_G5P2"

rec "before_judge_g5"
python3 -I -B testing/d003/stage_s4/r6c_judge.py "$PREREG_G5" "$CONTROL_G5" "$OUTDIR" > "$OUTDIR/judge_g5.stdout" 2>&1
RC_JG5=$?
rec "after_judge_g5"
echo "run_m1c_r8m1c3: $TREE judge G5 rc=$RC_JG5"

rec "before_seam_pass1"
python3 -I -B testing/d003/stage_s4/r6c2_seam_state.py "$PREREG_SEAM" "$CONTROL_SEAM" "$DRV_SEAMF" "$DRV_FMMRET" "$OUTDIR" 1 > "$OUTDIR/run_seam_pass1.stdout" 2>&1
RC_SP1=$?
rec "after_seam_pass1"
echo "run_m1c_r8m1c3: $TREE seam pass1 rc=$RC_SP1"

rec "before_seam_pass2"
python3 -I -B testing/d003/stage_s4/r6c2_seam_state.py "$PREREG_SEAM" "$CONTROL_SEAM" "$DRV_SEAMF" "$DRV_FMMRET" "$OUTDIR" 2 > "$OUTDIR/run_seam_pass2.stdout" 2>&1
RC_SP2=$?
rec "after_seam_pass2"
echo "run_m1c_r8m1c3: $TREE seam pass2 rc=$RC_SP2"

rec "before_judge_seam"
python3 -I -B testing/d003/stage_s4/r6c2_seam_judge.py "$PREREG_SEAM" "$CONTROL_SEAM" "$OUTDIR" > "$OUTDIR/judge_seam.stdout" 2>&1
RC_JS=$?
rec "after_judge_seam"
echo "run_m1c_r8m1c3: $TREE judge seam rc=$RC_JS"

echo "run_m1c_r8m1c3: $TREE DONE g5p1=$RC_G5P1 g5p2=$RC_G5P2 jg5=$RC_JG5 sp1=$RC_SP1 sp2=$RC_SP2 js=$RC_JS"
exit 0
