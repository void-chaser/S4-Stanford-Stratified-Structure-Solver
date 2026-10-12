#!/bin/sh
# run_s3r3_noinject.sh -- P05-S3R3-2 (B): no-injection output identity, F vs F2 (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r3 -- sh testing/d003/stage_s3r3/run_s3r3_noinject.sh p05-s3r3
#
# For mode in nv, vl, fftnv, fftvl and NG in 1, 5, 9, runs the RNV1 driver (driver_r6b_state.cpp + inject_r6d_rnv1.cpp,
# no S4FMM_INJECT set: counting only) built against F and against F2, with S4FMM_DUMP_DIR set.  Then compares call1.txt,
# call2.txt, call3.txt byte by byte (cmp), and records the rc lines.  Every run is recorded; nothing is overwritten
# (each run has its own directory; the script refuses to reuse an existing directory).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_s3r3_noinject: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_s3r3_noinject.sh p05-s3r3"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/noinject"
DRV_F="$EV/drivers/s3r3-rnv1-F/driver"
DRV_F2="$EV/drivers/s3r3-rnv1-F2/driver"
RES="$OUT/RESULTS_NOINJECT_S3R3.tsv"
test -x "$DRV_F" && test -x "$DRV_F2" || { echo "drivers missing" >&2; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists (U17): $RES" >&2; exit 2; fi
mkdir -p "$OUT" || exit 2
printf 'mode\tNG\tgrid\ttree\trc_first\trc_retry\tfile\tcmp\n' > "$RES"

for MODE in nv vl fftnv fftvl; do
  for NG in 1 5 9; do
    for T in F F2; do
      if [ "$T" = F ]; then DRV="$DRV_F"; else DRV="$DRV_F2"; fi
      D="$OUT/$T/$MODE-ng$NG"
      if [ -e "$D" ]; then echo "REFUSED: exists (U17): $D" >&2; exit 2; fi
      mkdir -p "$D" || exit 2
      env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D" "$DRV" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
      RC=$?
      RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
      RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
      printf 'RUN\t%s\t%s\tpattern-both-4-3\t%s\t%s\t%s\t-\t-\n' "$MODE" "$NG" "$T" "$RF" "$RR" "$RC" >> "$RES"
    done
    for F in call1.txt call2.txt call3.txt; do
      if cmp -s "$OUT/F/$MODE-ng$NG/$F" "$OUT/F2/$MODE-ng$NG/$F"; then CMP=IDENTICAL; else CMP=NOT_IDENTICAL; fi
      printf '%s\t%s\tpattern-both-4-3\tF-vs-F2\t-\t-\t%s\t%s\n' "$MODE" "$NG" "$F" "$CMP" >> "$RES"
    done
  done
done
echo "run_s3r3_noinject: done -> $RES"
exit 0
