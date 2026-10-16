REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_init_b_dbg_r8m2c.sh -- Build init-B-dbg driver for baseline comparison in r8m2c.
set -u
mkdir -p "$EV/build"
OUT_DRV="$EV/build/init-B-dbg"
LIB_B="$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2/build_R3/lib_B_dbg/libS4.a"
TREE_B="$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2/trees_R3/B/S4"
DRV_SRC="$REPO/testing/d003/stage_s4/driver_r6b_state.cpp"
INJ_SRC="$REPO/testing/d003/stage_s3r4/inject_s3r4_init.cpp"
BUILD_TSV="$EV/BUILD_R8_M2c.tsv"

CMD="g++ -O0 -g -Wall -Wno-unused-parameter -I$TREE_B -I$TREE_B/fmm $DRV_SRC $INJ_SRC $LIB_B -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -o $OUT_DRV"

$CMD
RC=$?
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [ $RC -eq 0 ]; then
    DRV_SHA=$(sha256sum "$OUT_DRV" | cut -d' ' -f1)
    DRV_SRC_SHA=$(sha256sum "$DRV_SRC" | cut -d' ' -f1)
    INJ_SRC_SHA=$(sha256sum "$INJ_SRC" | cut -d' ' -f1)
    LIB_SHA=$(sha256sum "$LIB_B" | cut -d' ' -f1)
    SRC_COMB="drv:$DRV_SRC_SHA;inj:$INJ_SRC_SHA"
    printf "# BUILD_R8_M2c -- columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\textra\n" > "$BUILD_TSV"
    printf "init-B-dbg\t%s\t%s\t%s\t%s\t%s\t%s\t%d\tbaseline_only_non_repair\n" "checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg" "$DRV_SHA" "$SRC_COMB" "$LIB_SHA" "$CMD" "$UTC" "$RC" >> "$BUILD_TSV"
    echo "build_init_b_dbg_r8m2c: SUCCESS -> $OUT_DRV ($DRV_SHA)"
else
    echo "build_init_b_dbg_r8m2c: FAILED with rc=$RC" >&2
    exit $RC
fi
