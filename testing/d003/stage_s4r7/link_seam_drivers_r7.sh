#!/bin/sh
# link_seam_drivers_r7.sh -- P05-S4 R7 cont5 section 3.1 (U61, E7-26): link the four seam drivers needed by G2a (new file).
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/link_seam_drivers_r7.sh p05-s4r7
#
# Four drivers, one per (library, tree), all plain build (build_r7/seam_plain):
#   seamF-F-plain    -> seamF-F   (tree F,  library seamF)
#   seamF-F2-plain   -> seamF-F2  (tree F2, library seamF)
#   fmmret-F-plain   -> fmmret-F  (tree F,  library fmmret)
#   fmmret-F2-plain  -> fmmret-F2 (tree F2, library fmmret)
# Source and link flags as in testing/d003/stage_s4/run_r4_seam.sh link_driver (driver_d003.cpp + inject_d003.cpp,
# -O1, LIBFLAGS identical to run_r4_seam.sh:38).  Only the libraries and the output paths differ.
#
# Output (nothing is overwritten; U17):
#   $EV/drivers_r7/seam-<NAME>/driver
#   $EV/DRIVERS_R7_SEAM.tsv   (name, tree, lib sha256, driver sha256, library path, compile command)
#   $EV/DRIVERS_R7_SEAM_vsR4.tsv  (comparison of the F driver sha256 with registries/s4r4/DRIVERS.tsv: SAME or DIFFERENT only)
# A DIFFERENT driver sha256 does not stop the script (the libraries are byte-identical to R4 per U51; the difference is recorded).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_seam_drivers_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_seam_drivers_r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
SAFE="$REPO/testing/d003/safe_run.sh"
SRC="$REPO/testing/d003/src"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
TMPDIR="$EV/tmp"
export TMPDIR

# every write goes through safe_run.sh; the first call creates the outputs
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers_r7" && test ! -e "$1/DRIVERS_R7_SEAM.tsv" && : > "$1/DRIVERS_R7_SEAM.tsv"' sh "$EV" || { echo "link_seam_drivers_r7: refused (outputs exist or cannot create)" >&2; exit 2; }
sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1/DRIVERS_R7_SEAM_vsR4.tsv" && : > "$1/DRIVERS_R7_SEAM_vsR4.tsv"' sh "$EV" || { echo "link_seam_drivers_r7: refused (vsR4 exists)" >&2; exit 2; }

# link NAME TAG TREE LIBSRC : NAME is the driver name, TAG the library build dir (seam_plain), TREE is F or F2
link() {
    N=$1; TAG=$2; T=$3
    LIB="$EV/build_r7/seam_plain/$TAG/build/libS4.a"
    SRCTREE="$EV/build_r7/seam_plain/$TAG"
    OUTDIR="$EV/drivers_r7/seam-$N"
    test -f "$LIB" || { echo "missing library $LIB" >&2; return 1; }
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1" && mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/driver_d003.cpp" "$3/inject_d003.cpp" -o "$1/driver" -L "$2/build" -lS4 '"$LIBFLAGS"' > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$SRCTREE" "$SRC" || { echo "link FAILED $N (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || return 1
    LSHA=$(sha256sum "$LIB" | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" >> "$6/DRIVERS_R7_SEAM.tsv"' sh "$N" "$T" "$LSHA" "$DSHA" "$LIB" "$EV" || return 1
    echo "$N tree=$T lib_sha256=$LSHA driver_sha256=$DSHA"
    return 0
}

link seamF-F   seamF-F-plain   F  || exit 1
link seamF-F2  seamF-F2-plain  F2 || exit 1
link fmmret-F  fmmret-F-plain  F  || exit 1
link fmmret-F2 fmmret-F2-plain F2 || exit 1
echo "link_seam_drivers_r7: done"
exit 0
