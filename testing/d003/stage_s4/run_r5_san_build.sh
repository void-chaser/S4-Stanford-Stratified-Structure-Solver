#!/bin/sh
# run_r5_san_build.sh -- P05-S4 R5-5 (V4): AddressSanitizer + UBSan builds of tree F (1c11905), its seam variants
# seamF, fmmret-F, addf-F, b2buf-F, and the matching drivers.  BUILD ONLY.  Exported copies under $EV only.
# Same seam steps and macros as run_r4_seam.sh (F part); only the compile/link flags differ:
#   -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer   (LIBFLAGS keeps the --wrap options of run_r4_seam.sh)
#
#   sh testing/d003/safe_run.sh p05-s4r5 -- sh testing/d003/stage_s4/run_r5_san_build.sh p05-s4r5
#
# Output: $EV/san/build/<name>/libS4.a, $EV/san/drivers/<name>/driver-d003, $EV/san/LIBS_SAN.tsv, $EV/san/DRIVERS_SAN.tsv
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r5_san_build: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_r5_san_build.sh p05-s4r5"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
SAN="$EV/san"
H="$REPO/testing/d003"
SAFE="$H/safe_run.sh"
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
TMPDIR="$EV/tmp"
export TMPDIR
COMMIT_F=1c11905
SANFLAGS="-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/build" "$1/drivers" && : > "$1/LIBS_SAN.tsv" && : > "$1/DRIVERS_SAN.tsv"' sh "$SAN" || { echo "run_r5_san_build: cannot prepare $SAN" >&2; exit 2; }

export_to() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$1" "$REPO" "$2"
}

apply_r2() {
    sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r2.py" --root "$1" --repo "$REPO" --families "$2" --report "$SAN/apply-$3.txt" >/dev/null \
        || { echo "run_r5_san_build: apply_seam_r2 families=$2 FAILED on $3" >&2; return 1; }
}

# build_lib SRCDIR NAME MACROS : sanitizer library, then sha256
build_lib() {
    _d=$1; _n=$2; _m=$3
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2/build/build-$3.log" 2>&1 && make -j"$4" CPPFLAGS="$5 -IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="'"$SANFLAGS"' -Wall -fPIC -fcx-limited-range -fno-exceptions" CXXFLAGS="'"$SANFLAGS"' -Wall -fcx-limited-range -fno-exceptions -fPIC" build/libS4.a >> "$2/build/build-$3.log" 2>&1' \
        sh "$_d" "$SAN" "$_n" "$JOBS" "$_m" || { echo "run_r5_san_build: make FAILED for $_n (see $SAN/build/build-$_n.log)" >&2; return 1; }
    [ -f "$_d/build/libS4.a" ] || { echo "run_r5_san_build: libS4.a missing for $_n" >&2; return 1; }
    _sha=$(sha256sum "$_d/build/libS4.a" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5/LIBS_SAN.tsv"' sh "$_n" "$_sha" "$_m" "$_d" "$SAN" || return 1
    echo "$_n rc=0 sha256=$_sha"
    return 0
}

# link_driver NAME LIBDIR : link the committed driver and injector against LIBDIR/build/libS4.a with sanitizer flags
link_driver() {
    _n=$1; _ld=$2
    _bin="$SAN/drivers/$_n/driver-d003"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ '"$SANFLAGS"' -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/src/driver_d003.cpp" "$3/stage_s4/inject_r4_plan.cpp" -o "$4" -L "$2/build" -lS4 '"$LIBFLAGS" \
        sh "$SAN/drivers/$_n" "$_ld" "$H" "$_bin" || { echo "run_r5_san_build: link FAILED for driver $_n" >&2; return 1; }
    [ -x "$_bin" ] || return 1
    _dsha=$(sha256sum "$_bin" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "$1" "$2" "$3" >> "$4/DRIVERS_SAN.tsv"' sh "$_n" "$_dsha" "$_bin" "$SAN" || return 1
    echo "driver $_n sha256=$_dsha"
    return 0
}

fail_stop() { echo "run_r5_san_build: STOP: $1" >&2; exit 1; }

# plain sanitizer library (control: no seam macro)
SD="$SAN/src-plain"
export_to "$SD" "$COMMIT_F" || fail_stop "export F plain"
build_lib "$SD" "san-plain-F" "" || fail_stop "build san-plain-F"
link_driver "san-plain-F" "$SD" || fail_stop "driver san-plain-F"

# seamF: families A, C, D by apply_seam_r2.py, family B2 by apply_seam_b2.py
SD="$SAN/src-seamF"
export_to "$SD" "$COMMIT_F" || fail_stop "export F seamF"
apply_r2 "$SD" "A,C,D" "F-seamF-ACD" || fail_stop "seamF ACD"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_b2.py" --root "$SD" --repo "$REPO" --report "$SAN/apply-F-seamF-B2.txt" >/dev/null || fail_stop "seamF B2"
build_lib "$SD" "seamF" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM" || fail_stop "build seamF"
link_driver "seamF" "$SD" || fail_stop "driver seamF"

SD="$SAN/src-fmmret-F"
export_to "$SD" "$COMMIT_F" || fail_stop "export fmmret-F"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_fmmret.py" --tree A --root "$SD" --repo "$REPO" --report "$SAN/apply-F-fmmret.txt" >/dev/null || fail_stop "fmmret-F apply"
build_lib "$SD" "fmmret-F" "-DS4_TEST_FMMRET_SEAM" || fail_stop "build fmmret-F"
link_driver "fmmret-F" "$SD" || fail_stop "driver fmmret-F"

SD="$SAN/src-addf-F"
export_to "$SD" "$COMMIT_F" || fail_stop "export addf-F"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r5_addfield.py" --root "$SD" --repo "$REPO" --report "$SAN/apply-F-addf.txt" >/dev/null || fail_stop "addf-F apply"
build_lib "$SD" "addf-F" "-DS4_TEST_ADDFIELD_SEAM" || fail_stop "build addf-F"
link_driver "addf-F" "$SD" || fail_stop "driver addf-F"

SD="$SAN/src-b2buf-F"
export_to "$SD" "$COMMIT_F" || fail_stop "export b2buf-F"
sh "$SAFE" "$OUT_ARG" -- "$PY" -I -B "$H/seam/apply_seam_r4_buf.py" --root "$SD" --repo "$REPO" --report "$SAN/apply-F-b2buf.txt" >/dev/null || fail_stop "b2buf-F apply"
build_lib "$SD" "b2buf-F" "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF" || fail_stop "build b2buf-F"
link_driver "b2buf-F" "$SD" || fail_stop "driver b2buf-F"

echo "run_r5_san_build: SANITIZER BUILD DONE (no injection was run)"
exit 0
