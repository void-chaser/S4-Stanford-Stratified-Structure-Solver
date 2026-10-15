REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# progress_r8m2a2_checkpoint.sh -- P05-S4 R8 M2a2 progress checkpoint (read-only facts; writes one file under $EV).
# Records the state of the deliverables and the sha256 of the key inputs at this point of the round.
set -u
OUTF=$EV/PROGRESS_CHECKPOINT_R8_M2a2.txt
if [ -e "$OUTF" ]; then echo "progress: REFUSED exists (U17): $OUTF" >&2; exit 2; fi
{
    echo "# PROGRESS_CHECKPOINT_R8_M2a2 -- facts at this checkpoint (no S4 driver run)"
    echo "HEAD=$(git rev-parse HEAD)"
    echo "HEAD_S4=$(git rev-parse HEAD:S4)"
    echo "JUDGE_SHA=$(sha256sum testing/d003/judge_d003.py | cut -d' ' -f1)"
    echo "INJECTOR_R3_SHA=$(sha256sum testing/d003/stage_s4/inject_r8m2a2_dual_R3.cpp | cut -d' ' -f1)"
    echo "HARNESS_RESULT_FILE=checkpoints/p05/evidence/p05-s4r8/m2a2/DUAL_HARNESS_R8_M2a2.tsv"
    echo "CALLSITE_AUDIT=checkpoints/p05/evidence/p05-s4r8/m2a2/CALLSITE_AUDIT_R8_M2a2_R3_R2.tsv"
    echo "NM_CHECK_R4=checkpoints/p05/evidence/p05-s4r8/m2a2/NM_CHECK_R4_R8_M2a2.tsv"
    echo "POSCTRL_R2=checkpoints/p05/evidence/p05-s4r8/m2a2/POSCTRL_M2_R8_M2a2_R2.txt"
    echo "SAN_PROBE=checkpoints/p05/evidence/p05-s4r8/m2a2/SAN_PROBE_R8_M2a2.txt"
    echo "PENDING_SUBAGENTS=layer_order(F3,INDEX),fft_grid(M2-08),stage_e(M2-02)"
} > "$OUTF"
echo "progress: wrote $OUTF"
exit 0
