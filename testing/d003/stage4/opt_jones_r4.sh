#!/bin/sh
# P05-S2R4 R4-4 (evidence only, read-only comparison; not committed).
# Usage: sh opt_jones_r4.sh TREE OPTION_NAME "OPTION_FLAGS"
#   TREE          A or H  (plain exports read-only from p05-s2r3/stage4/plain-TREE, built with repo default options)
#   OPTION_NAME   any label; outputs go to p05-s2r4/r4-4/opt-TREE-NAME
#   OPTION_FLAGS  the optimisation/math flags that REPLACE "-O3 -march=native -fcx-limited-range"
#                 for fmm_PolBasisJones.cpp only.  Everything else on the command line is unchanged.
# Method: identical to testing/d003/stage4/opt_jones.sh (S2R3, committed), except:
#   - the outputs go to checkpoints/p05/evidence/p05-s2r4/r4-4/ (this round's evidence directory);
#   - the plain exports are read from the S2R3 evidence directory and are NOT written.
# The default driver source and inject source are the committed HEAD sources.
# No /tmp: TMPDIR is redirected into p05-s2r4/tmp.  The script writes only inside p05-s2r4/r4-4/.
set -eu
T=$1
NAME=$2
FLAGS=$3
REPO=$(cd "$(dirname "$0")/../../.." && pwd -P)
S3="$REPO/checkpoints/p05/evidence/p05-s2r3/stage4"
R4="$REPO/checkpoints/p05/evidence/p05-s2r4/r4-4"
SRC="$S3/plain-$T"
OUT="$R4/opt-$T-$NAME"
TMPDIR="$REPO/checkpoints/p05/evidence/p05-s2r4/tmp"
export TMPDIR
mkdir -p "$TMPDIR" "$R4"
rm -rf "$OUT"
mkdir -p "$OUT/dump"
# 1. recompile Jones only, from the read-only plain source tree, into OUT
cd "$SRC"
g++ -c $FLAGS -Wall -fno-exceptions -fPIC -IS4 -IS4/RNP -IS4/kiss_fft S4/fmm/fmm_PolBasisJones.cpp -o "$OUT/fmm_PolBasisJones.o" > "$OUT/compile.log" 2>&1
echo "compile_rc=$?"
# 2. copy the default library (read-only source) and replace the Jones member only
cp "$SRC/build/libS4.a" "$OUT/libS4.a"
cd "$OUT"
ar r libS4.a fmm_PolBasisJones.o > ar.log 2>&1
ranlib libS4.a
echo "ar_member_jones_sha256=$(ar p libS4.a fmm_PolBasisJones.o | sha256sum | cut -c1-16)"
# 3. link the driver with the same source and LIBFLAGS as the default driver
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$SRC/S4" -I "$SRC/S4/fmm" "$REPO/testing/d003/src/driver_d003.cpp" "$REPO/testing/d003/src/inject_d003.cpp" -o "$OUT/driver-d003" -L "$OUT" -lS4 $LIBFLAGS > link.log 2>&1
echo "link_rc=$?"
echo "driver_sha256=$(sha256sum "$OUT/driver-d003" | cut -c1-16)"
# 4. two dump runs, each with a first-call and a retry dump
for r in 1 2; do
    env -i PATH="$PATH" LANG=C LC_ALL=C FMM_MODE=jones S4FMM_NG=9 \
        S4FMM_DUMP1="$OUT/dump/first-run$r.txt" S4FMM_DUMP="$OUT/dump/retry-run$r.txt" \
        "$OUT/driver-d003" pattern both 4 3 > "$OUT/dump/run$r.out" 2>&1
    echo "run$r driver_rc=$?"
done
# 5. read-only disassembly of the Jones member: count FMA instructions
objdump -d --no-show-raw-insn "$OUT/fmm_PolBasisJones.o" > "$OUT/jones.disasm.txt"
echo "fma_count=$(grep -cE '\b(vfmadd|vfnmadd|vfmsub|vfnmsub)[0-9a-z]*\b' "$OUT/jones.disasm.txt")"
