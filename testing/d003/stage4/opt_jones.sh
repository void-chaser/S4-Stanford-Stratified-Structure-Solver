#!/bin/sh
# P05-S2R3 stage 4 (evidence only, read-only comparison; not committed).
# Usage: sh opt_jones.sh TREE OPTION_NAME "OPTION_FLAGS"
#   TREE          A or H  (plain exports under stage4/plain-TREE, built with repo default options)
#   OPTION_NAME   a | b | c | d   (the four options of the task, section 5)
#   OPTION_FLAGS  the optimisation/math flags that REPLACE "-O3 -march=native -fcx-limited-range"
#                 for fmm_PolBasisJones.cpp only.  Everything else on the command line is unchanged.
# Method: recompile fmm_PolBasisJones.cpp with the flags, replace that ONE member of a copy of the tree's
#   libS4.a with ar (then ranlib), link the same driver source with the same LIBFLAGS.  All other members are
#   the tree's own default objects.  Two dump runs per binary (first call and retry).
# No /tmp: TMPDIR is redirected into stage4/.  The script writes only inside stage4/.
set -eu
T=$1
NAME=$2
FLAGS=$3
REPO=$(cd "$(dirname "$0")/../../.." && pwd -P)
STAGE="$REPO/checkpoints/p05/evidence/p05-s2r3/stage4"
SRC="$STAGE/plain-$T"
OUT="$STAGE/opt-$T-$NAME"
TMPDIR="$OUT/tmp"
export TMPDIR
rm -rf "$OUT"
mkdir -p "$OUT/tmp" "$OUT/dump"
cd "$SRC"
# 1. recompile Jones only (default options replaced by FLAGS; the rest of the line is the repo's)
g++ -c $FLAGS -Wall -fno-exceptions -fPIC -IS4 -IS4/RNP -IS4/kiss_fft S4/fmm/fmm_PolBasisJones.cpp -o "$OUT/fmm_PolBasisJones.o" > "$OUT/compile.log" 2>&1
echo "compile_rc=$?"
# 2. copy the default library and replace the Jones member only
cp "$SRC/build/libS4.a" "$OUT/libS4.a"
cd "$OUT"
ar r libS4.a fmm_PolBasisJones.o > ar.log 2>&1
ranlib libS4.a
echo "ar_member_jones_sha256=$(ar p libS4.a fmm_PolBasisJones.o | sha256sum | cut -c1-16)"
# 3. link the driver (same source, same LIBFLAGS as the default driver)
REPO_H="$REPO/testing/d003"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$SRC/S4" -I "$SRC/S4/fmm" "$REPO_H/src/driver_d003.cpp" "$REPO_H/src/inject_d003.cpp" -o "$OUT/driver-d003" -L "$OUT" -lS4 $LIBFLAGS > link.log 2>&1
echo "link_rc=$?"
echo "driver_sha256=$(sha256sum "$OUT/driver-d003" | cut -c1-16)"
# 4. two dump runs (run1, run2), each with a first-call and a retry dump
for r in 1 2; do
    env -i PATH="$PATH" LANG=C LC_ALL=C FMM_MODE=jones S4FMM_NG=9 \
        S4FMM_DUMP1="$OUT/dump/first-run$r.txt" S4FMM_DUMP="$OUT/dump/retry-run$r.txt" \
        "$OUT/driver-d003" pattern both 4 3 > "$OUT/dump/run$r.out" 2>&1
    echo "run$r driver_rc=$?"
done
