REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# b_map_run_c3.sh -- P05-S3R4 CONT3 (B) pre-run map: no injection; gdb reads the cumulative window count at the first
# GetFieldPlane return (Mfirst) and at exit (Mtot).  Twelve runs: F2, F3 x {fft, kottke} x NG {1, 5, 9}.
# Output: $EV/b_map_c3/<tree>-<mode>-ng<NG>/ (gdb.txt, stderr.txt, counts.txt).  Refuses to overwrite.
# The driver and the gdb script are not changed.  Usage:
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/b_map_run_c3.sh
GDBSCRIPT=$REPO/testing/d003/stage_s3r4c3/b_map_c3.gdb
mkdir -p "$EV/b_map_c3" || exit 2
for T in F2 F3; do
  for M in fft kottke; do
    for NG in 1 5 9; do
      D="$EV/b_map_c3/$T-$M-ng$NG"
      if [ -e "$D" ]; then echo "REFUSED: exists $D"; exit 2; fi
      mkdir -p "$D" || exit 2
      env -i PATH="$PATH" FMM_MODE="$M" S4FMM_NG="$NG" gdb -batch -x "$GDBSCRIPT" --args "$EV/drivers/polyinj-$T/driver" pattern both 4 3 > "$D/gdb.txt" 2>&1
      echo "gdb_rc=$?" > "$D/gdb_rc.txt"
      grep -E '^\$[0-9]+ = |RC first|RC retry|HITCOUNT|S4FMM S3R4C3_WIN_MALLOC' "$D/gdb.txt" > "$D/counts.txt"
      grep 'S4FMM S3R4C3_WIN_MALLOC' "$D/gdb.txt" > "$D/stderr.txt"
      echo "map done $T $M NG$NG"
    done
  done
done
exit 0
