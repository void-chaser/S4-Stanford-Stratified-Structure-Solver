#!/bin/sh
# a1map_c2.sh -- P05-S3R4 CONT2 A1 map: for one tree and one combination, count the malloc calls (no injection)
# and resolve each caller to a function name with addr2line (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/a1map_c2.sh p05-s3r4c2 F2 closed2d 1
#
# Arguments: $1 evidence dir; $2 tree (F2|F3); $3 mode; $4 NG.
# Steps: (1) run the init driver with no injection (S4FMM_INJECT unset) and keep its stderr (counting lines);
#        (2) run it under gdb (a1map_c2.gdb: break at exit, info proc mappings) to get the load base;
#        (3) for each distinct caller address c: offset = c - base; addr2line -f -e driver offset.
# Output in $EV/a1map_<tree>_<mode>-ng<NG>/ : stderr.txt, gdb.txt, base.txt, callers.tsv (caller, offset, function).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
OUT_ARG=${1:?"usage: a1map_c2.sh p05-s3r4c2 F2|F3 mode NG"}
TREE=${2:?"tree"}
MODE=${3:?"mode"}
NG=${4:?"NG"}
DRV=$EV/drivers/init-$TREE/driver
D=$EV/a1map_${TREE}_${MODE}-ng${NG}
test -x "$DRV" || { echo "driver missing: $DRV"; exit 2; }
if [ -e "$D" ]; then echo "REFUSED: exists $D"; exit 2; fi
mkdir -p "$D" || exit 2
GDBSCRIPT=$REPO/testing/d003/stage_s3r4c2/a1map_c2.gdb

# (1) counting run, no injection
env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D" "$DRV" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
echo "count_run_rc=$?" > "$D/count_rc.txt"

# (2) base address under gdb (ASLR off)
env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D/gdb_out" gdb -batch -x "$GDBSCRIPT" --args "$DRV" pattern both 4 3 > "$D/gdb.txt" 2>&1
grep -m1 "$(basename "$DRV")" "$D/gdb.txt" > "$D/base_line.txt"
awk '/driver/ && $4 == "0x0" {print $1; exit}' "$D/gdb.txt" > "$D/base.txt"

# (3) distinct callers and their function names
sed -n 's/.*caller=\(0x[0-9a-f]*\).*/\1/p' "$D/stderr.txt" | sort -u > "$D/callers_raw.txt"
printf 'caller\toffset\tfunction\tfile_line\n' > "$D/callers.tsv"
BASE=$(cat "$D/base.txt")
while read C; do
    OFF=$(printf '0x%x' $(( C - BASE )))
    FN=$(addr2line -f -e "$DRV" "$OFF" | head -1)
    FL=$(addr2line -e "$DRV" "$OFF" | head -1)
    printf '%s\t%s\t%s\t%s\n' "$C" "$OFF" "$FN" "$FL" >> "$D/callers.tsv"
done < "$D/callers_raw.txt"
echo "a1map $TREE $MODE NG$NG done: $D"
exit 0
