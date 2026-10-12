#!/bin/sh
# run_r4_seam.sh -- P05-S4 R4-1: build the seam libraries on tree F (1c11905) and the baseline libraries
# on trees B (37a82e8) and A (876181c).  BUILD ONLY: this script runs no matrix and no injection.
#
#   sh testing/d003/safe_run.sh p05-s4r4 -- sh testing/d003/stage_s4/run_r4_seam.sh p05-s4r4
#
# Every library is built from a FRESH git-archive export of its commit into $EV/seam/<tree>-<family>/
# (never into the repository S4/ tree and never reusing the plain tree).  Each apply script receives the
# export as --root and the repository as --repo, so it refuses any root inside <repo>/S4/.
#
# Libraries (macros as in testing/d003/README.md section 3 and run_all.sh lines 187-202, 212-232):
#   seamF    tree F: family A (linearsolve), C (alloc), D (kottke_alloc) by apply_seam_r2.py --families A,C,D;
#            family B2 (linearsolve_null2, the seven info==NULL sites in their FIXED form on F) by apply_seam_b2.py.
#            Macros: -DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM
#   fmmret-F fmmret family by apply_seam_r5_fmmret.py --tree A (same output as --tree H on F; see SEAMDIFF_R4.txt).
#            Macro: -DS4_TEST_FMMRET_SEAM
#   addf-F   addfield family by apply_seam_r5_addfield.py.  Macro: -DS4_TEST_ADDFIELD_SEAM
#   b2buf-F  B2buf (output only) by apply_seam_r4_buf.py.  Macro: -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF
#   seamAB-B tree B: families A, B, C, D by apply_seam_r2.py --families A,B,C,D.
#            Macros: -DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM
#   fmmbuf-B tree B: fmmbuf by apply_seam_r5_fmmret.py --tree B.  Macro: -DS4_TEST_FMMBUF_SEAM
#   fmmret-A tree A: fmmret by apply_seam_r5_fmmret.py --tree A.  Macro: -DS4_TEST_FMMRET_SEAM
#
# Each library is linked with its driver (same source and LIBFLAGS as build_tree_r2.sh):
#   driver sha256 -> $EV/drivers/DRIVERS.tsv (name, sha256, path).
# Each library sha256 -> $EV/seam/LIBS_R4.tsv.
# Each seam export is compared with its clean export (git-archive) -> $EV/SEAMDIFF_R4.txt.
#
# Stops at the first failure (nothing is bypassed).  Prints one line per library: name rc sha256.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r4_seam: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_r4_seam.sh p05-s4r4"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
H="$REPO/testing/d003"
SAFE="$H/safe_run.sh"
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
COMMIT_B=37a82e8
COMMIT_A=876181c
COMMIT_F=1c11905
TMPDIR="$EV/tmp"
export TMPDIR

# every write goes through safe_run.sh; the first call creates the directories
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/seam" "$1/drivers" "$1/tmp" && : > "$1/seam/LIBS_R4.tsv" && : > "$1/drivers/DRIVERS.tsv"' sh "$EV" || { echo "run_r4_seam: cannot prepare $EV" >&2; exit 2; }

# export COMMIT DEST : fresh git archive of COMMIT into DEST (DEST is removed first)
export_to() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$1" "$REPO" "$2"
}

# build_lib DIR NAME MACROS : make the library in DIR (objdir first), then sha256 it
build_lib() {
    _d=$1; _n=$2; _m=$3
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2/seam/build-$3.log" 2>&1 && make -j"$4" CPPFLAGS="$5 -IS4 -IS4/RNP -IS4/kiss_fft" build/libS4.a >> "$2/seam/build-$3.log" 2>&1' \
        sh "$_d" "$EV" "$_n" "$JOBS" "$_m" || { echo "run_r4_seam: make FAILED for $_n (see $EV/seam/build-$_n.log)" >&2; return 1; }
    [ -f "$_d/build/libS4.a" ] || { echo "run_r4_seam: libS4.a missing for $_n" >&2; return 1; }
    _sha=$(sha256sum "$_d/build/libS4.a" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5/seam/LIBS_R4.tsv"' sh "$_n" "$_sha" "$_m" "$_d" "$EV" || return 1
    echo "$_n rc=0 sha256=$_sha"
    return 0
}

# link_driver NAME LIBDIR : link the committed driver source against LIBDIR/build/libS4.a
link_driver() {
    _n=$1; _ld=$2
    _bin="$EV/drivers/$_n/driver-d003"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/src/driver_d003.cpp" "$3/src/inject_d003.cpp" -o "$4" -L "$2/build" -lS4 '"$LIBFLAGS" \
        sh "$EV/drivers/$_n" "$_ld" "$H" "$_bin" || { echo "run_r4_seam: link FAILED for driver $_n" >&2; return 1; }
    [ -x "$_bin" ] || return 1
    _dsha=$(sha256sum "$_bin" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "$1" "$2" "$3" >> "$4/drivers/DRIVERS.tsv"' sh "$_n" "$_dsha" "$_bin" "$EV" || return 1
    echo "driver $_n sha256=$_dsha"
    return 0
}

# apply_r2 DIR FAMILIES NAME : apply_seam_r2.py for the given families to the export DIR
# (--repo is passed so that the script refuses any root inside <repo>/S4/)
apply_r2() {
    sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r2.py" --root "$1" --repo "$REPO" --families "$2" --report "$EV/seam/apply-$3.txt" >/dev/null \
        || { echo "run_r4_seam: apply_seam_r2 families=$2 FAILED on $3" >&2; return 1; }
}

fail_stop() { echo "run_r4_seam: STOP: $1" >&2; exit 1; }

# ---------------------------------------------------------------------------
# tree F: seamF, fmmret-F, addf-F, b2buf-F
# ---------------------------------------------------------------------------
SD="$EV/seam/F-seamF"
export_to "$SD" "$COMMIT_F" || fail_stop "export F-seamF"
apply_r2 "$SD" "A,C,D" "F-seamF-ACD" || fail_stop "seamF families A,C,D"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_b2.py" --root "$SD" --repo "$REPO" --report "$EV/seam/apply-F-seamF-B2.txt" >/dev/null \
    || fail_stop "seamF apply_seam_b2"
build_lib "$SD" "seamF" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM" || fail_stop "build seamF"
link_driver "seamF" "$SD" || fail_stop "driver seamF"

SD="$EV/seam/F-fmmret"
export_to "$SD" "$COMMIT_F" || fail_stop "export F-fmmret"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_fmmret.py" --tree A --root "$SD" --repo "$REPO" --report "$EV/seam/apply-F-fmmret.txt" >/dev/null \
    || fail_stop "fmmret-F apply"
build_lib "$SD" "fmmret-F" "-DS4_TEST_FMMRET_SEAM" || fail_stop "build fmmret-F"
link_driver "fmmret-F" "$SD" || fail_stop "driver fmmret-F"

SD="$EV/seam/F-addf"
export_to "$SD" "$COMMIT_F" || fail_stop "export F-addf"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_addfield.py" --root "$SD" --repo "$REPO" --report "$EV/seam/apply-F-addf.txt" >/dev/null \
    || fail_stop "addf-F apply"
build_lib "$SD" "addf-F" "-DS4_TEST_ADDFIELD_SEAM" || fail_stop "build addf-F"
link_driver "addf-F" "$SD" || fail_stop "driver addf-F"

SD="$EV/seam/F-b2buf"
export_to "$SD" "$COMMIT_F" || fail_stop "export F-b2buf"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r4_buf.py" --root "$SD" --repo "$REPO" --report "$EV/seam/apply-F-b2buf.txt" >/dev/null \
    || fail_stop "b2buf-F apply"
build_lib "$SD" "b2buf-F" "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF" || fail_stop "build b2buf-F"
link_driver "b2buf-F" "$SD" || fail_stop "driver b2buf-F"

# ---------------------------------------------------------------------------
# tree B: seamAB-B, fmmbuf-B
# ---------------------------------------------------------------------------
SD="$EV/seam/B-AB"
export_to "$SD" "$COMMIT_B" || fail_stop "export B-AB"
apply_r2 "$SD" "A,B,C,D" "B-AB-ABCD" || fail_stop "seamAB-B families A,B,C,D"
build_lib "$SD" "seamAB-B" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM" || fail_stop "build seamAB-B"
link_driver "seamAB-B" "$SD" || fail_stop "driver seamAB-B"

SD="$EV/seam/B-fmmbuf"
export_to "$SD" "$COMMIT_B" || fail_stop "export B-fmmbuf"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_fmmret.py" --tree B --root "$SD" --repo "$REPO" --report "$EV/seam/apply-B-fmmbuf.txt" >/dev/null \
    || fail_stop "fmmbuf-B apply"
build_lib "$SD" "fmmbuf-B" "-DS4_TEST_FMMBUF_SEAM" || fail_stop "build fmmbuf-B"
link_driver "fmmbuf-B" "$SD" || fail_stop "driver fmmbuf-B"

# ---------------------------------------------------------------------------
# tree A: fmmret-A
# ---------------------------------------------------------------------------
SD="$EV/seam/A-fmmret"
export_to "$SD" "$COMMIT_A" || fail_stop "export A-fmmret"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_fmmret.py" --tree A --root "$SD" --repo "$REPO" --report "$EV/seam/apply-A-fmmret.txt" >/dev/null \
    || fail_stop "fmmret-A apply"
build_lib "$SD" "fmmret-A" "-DS4_TEST_FMMRET_SEAM" || fail_stop "build fmmret-A"
link_driver "fmmret-A" "$SD" || fail_stop "driver fmmret-A"

echo "run_r4_seam: BUILD DONE (no matrix was run)"
exit 0
