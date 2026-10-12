#!/bin/sh
# a1map_c2_v2.sh -- P05-S3R4 CONT2 A1 map, revised (new file; supersedes a1map_c2.sh, which mixed an ASLR-on
# counting run with an ASLR-off base address; see ERRATA ES3R4-19).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/a1map_c2_v2.sh p05-s3r4c2 F2 closed2d 1
#
# Arguments: $1 evidence dir; $2 tree (F2|F3); $3 mode; $4 NG.
# ONE gdb session (ASLR off, a1map_c2.gdb) runs the init driver with no injection: the caller addresses printed
# by the injector and the load base share one address space.  Then offset = caller - base; addr2line -f -e driver offset.
# Output in $EV/a1map2_<tree>_<mode>-ng<NG>/ : gdb.txt (session log incl. mappings), stderr.txt (injector lines,
# extracted from gdb.txt), base.txt, callers.tsv.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
OUT_ARG=${1:?"usage: a1map_c2_v2.sh p05-s3r4c2 F2|F3 mode NG"}
TREE=${2:?"tree"}
MODE=${3:?"mode"}
NG=${4:?"NG"}
DRV=$EV/drivers/init-$TREE/driver
D=$EV/a1map2_${TREE}_${MODE}-ng${NG}
GDBSCRIPT=$REPO/testing/d003/stage_s3r4c2/a1map_c2.gdb
test -x "$DRV" || { echo "driver missing: $DRV"; exit 2; }
if [ -e "$D" ]; then echo "REFUSED: exists $D"; exit 2; fi
mkdir -p "$D" || exit 2

# (1) one gdb session: counting run (no injection) + mappings at exit
env -i PATH="$PATH" FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D" gdb -batch -x "$GDBSCRIPT" --args "$DRV" pattern both 4 3 > "$D/gdb.txt" 2>&1
echo "gdb_rc=$?" > "$D/gdb_rc.txt"

# (2) the injector lines (stderr of the inferior appears in gdb.txt) and the base (segment with file offset 0)
grep '^S4FMM S3R4_' "$D/gdb.txt" > "$D/stderr.txt"
awk '/driver/ && $4 == "0x0" {print $1; exit}' "$D/gdb.txt" > "$D/base.txt"
BASE=$(cat "$D/base.txt")

# (3) distinct callers and their function names (addr2line on the driver)
sed -n 's/.*caller=\(0x[0-9a-f]*\).*/\1/p' "$D/stderr.txt" | sort -u > "$D/callers_raw.txt"
printf 'caller\toffset\tfunction\tfile_line\n' > "$D/callers.tsv"
while read C; do
    OFF=$(printf '0x%x' $(( C - BASE )))
    FN=$(addr2line -f -e "$DRV" "$OFF" | head -1)
    FL=$(addr2line -e "$DRV" "$OFF" | head -1)
    printf '%s\t%s\t%s\t%s\n' "$C" "$OFF" "$FN" "$FL" >> "$D/callers.tsv"
done < "$D/callers_raw.txt"
echo "a1map2 $TREE $MODE NG$NG done: $D"
exit 0
