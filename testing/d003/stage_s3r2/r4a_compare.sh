#!/bin/sh
# P05-S3R2 R2-4a comparison (read-only on inputs; writes only the summary given as $2).
# Usage: sh r4a_compare.sh RUNDIR SUMMARY
# For each case: byte comparison of dump1 and dump2 for (new vs start) and (start vs base),
# plus the rc lines of the three trees.  No PASS/FAIL line is read.
RUNDIR=$1
OUT=$2
echo "case	new_vs_start_dump1	new_vs_start_dump2	start_vs_base_dump1	start_vs_base_dump2	rc_new	rc_start	rc_base	tree_proc_new	tree_proc_start	tree_proc_base" > "$OUT"
cd "$RUNDIR" || exit 2
for n in *-new.out; do
  case_id=${n%-new.out}
  nd1="$case_id-new.dump1"; sd1="$case_id-start.dump1"; bd1="$case_id-base.dump1"
  nd2="$case_id-new.dump2"; sd2="$case_id-start.dump2"; bd2="$case_id-base.dump2"
  c1=same; c2=same; c3=same; c4=same
  cmp -s "$nd1" "$sd1" || c1=DIFF
  cmp -s "$nd2" "$sd2" || c2=DIFF
  cmp -s "$sd1" "$bd1" || c3=DIFF
  cmp -s "$sd2" "$bd2" || c4=DIFF
  rn=$(grep '^RC first' "$case_id-new.out" | awk '{print $3}')
  rs=$(grep '^RC first' "$case_id-start.out" | awk '{print $3}')
  rb=$(grep '^RC first' "$case_id-base.out" | awk '{print $3}')
  pn=$(cat "$case_id-new.proc")
  ps=$(cat "$case_id-start.proc")
  pb=$(cat "$case_id-base.proc")
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$case_id" "$c1" "$c2" "$c3" "$c4" "$rn" "$rs" "$rb" "$pn" "$ps" "$pb" >> "$OUT"
done
echo "compare written: $OUT"
