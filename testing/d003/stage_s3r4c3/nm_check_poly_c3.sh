REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# nm_check_poly_c3.sh -- nm check of the wrap symbols in the two polygon-injection drivers (read only; output in $EV).
OUT="$EV/NM_CHECK_POLY_C3.txt"
{
  echo "nm check utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for T in F2 F3; do
    D="$EV/drivers/polyinj-$T/driver"
    echo "=== tree $T driver $D"
    nm "$D" | grep -E 'Pattern_DiscretizeCell' 
  done
  echo "=== library symbol side (lib refers to Pattern_DiscretizeCell)"
  for T in F2 F3; do
    if [ "$T" = F2 ]; then L="$REPO/checkpoints/p05/evidence/p05-s3r4/build/F2-plain/build"; else L="$REPO/checkpoints/p05/evidence/p05-s3r4/build_f3/plain/build"; fi
    echo "--- $T"
    for O in fmm_FFT.o fmm_kottke.o pattern.o; do
      printf '%s: ' "$O"
      nm -A "$L/libS4.a" > "$EV/tmp/nm_lib_$T.txt" 2>&1; grep -F "$O" "$EV/tmp/nm_lib_$T.txt" | grep 'Pattern_DiscretizeCell' | head -3
      echo
    done
  done
} > "$OUT" 2>&1
echo "nm check written: $OUT"
