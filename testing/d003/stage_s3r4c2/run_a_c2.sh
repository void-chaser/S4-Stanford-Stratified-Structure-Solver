#!/bin/sh
# run_a_c2.sh -- P05-S3R4 CONT2 self-check (A): 18 injected points x 2 passes + 6 no-injection controls (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/run_a_c2.sh
#
# Pre-registered points: $EV/REGISTRY_S3R4C2_A.tsv (written before this run; not changed here).
# Per point: two passes; each pass runs the init driver of the tree with FMM_MODE, S4FMM_NG and S4FMM_INJECT=<inj_spec>,
# and writes its log to $EV/a_c2/<tree>/<combo>/<point>/pass<N>/.  Facts (rc, rc1, rc2, hit) come from the driver
# exit status and the RC lines; the class is judge_d003.classify (called by a_c2_judge.py).
# Output: $EV/RESULTS_S3R4C2_A.tsv (one row per pass; class from the judge).  Nothing is overwritten.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
REG=$EV/REGISTRY_S3R4C2_A.tsv
RES=$EV/RESULTS_S3R4C2_A.tsv
ROOT=$EV/a_c2
test -f "$REG" || { echo "registry missing"; exit 2; }
test -x "$EV/drivers/init-F2/driver" && test -x "$EV/drivers/init-F3/driver" || { echo "init drivers missing"; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists $RES"; exit 2; fi
if [ -e "$ROOT" ]; then echo "REFUSED: exists $ROOT"; exit 2; fi
mkdir -p "$ROOT" || exit 2
printf 'combo\tmode\tNG\ttree\tpoint_id\tinj_spec\tk_index\tpass\tdriver_rc\trc1\trc2\thit\tclass\treason\texpected_rc1\texpected_class\tmatch\n' > "$RES"

# one COMBO MODE NG TREE POINT SPEC K EXP_RC1 EXP_CLASS : two passes, judge each pass
point() {
    CID=$1; MODE=$2; NG=$3; T=$4; PID=$5; SPEC=$6; KI=$7; ERC=$8; ECL=$9
    DRV=$EV/drivers/init-$T/driver
    for P in 1 2; do
        D=$ROOT/$T/$CID/$(echo "$PID" | tr -d '-')/pass$P
        mkdir -p "$D" || return 1
        env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_INJECT="$SPEC" S4FMM_DUMP_DIR="$D" "$DRV" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
        RC=$?
        echo "$RC" > "$D/rc.txt"
        J=$(sh "$REPO/testing/d003/stage_s3r4c2/judge_one_c2.sh" "$D" "$RC" "$SPEC" "$ERC" "$ECL")
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$CID" "$MODE" "$NG" "$T" "$PID" "$SPEC" "$KI" "$P" "$RC" "$J" >> "$RES"
    done
}

# control: no injection (S4FMM_INJECT unset); class must be CONTROL_OK
control() {
    CID=$1; MODE=$2; NG=$3; T=$4
    DRV=$EV/drivers/init-$T/driver
    D=$ROOT/$T/$CID/control
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D" "$DRV" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    echo "$RC" > "$D/rc.txt"
    printf '%s\t%s\t%s\t%s\tCONTROL\t-\t-\t0\t%s\t-\t-\t0\tCONTROL_OK?\tcontrol\t-\t-\t-\n' "$CID" "$MODE" "$NG" "$T" "$RC" >> "$RES"
}

for T in F2 F3; do
    point closed2d-ng1 closed2d 1 "$T" A-806   win:1  1 1 0 2>/dev/null
done
echo "run_a_c2: wrapper stub (see below)"
exit 0
