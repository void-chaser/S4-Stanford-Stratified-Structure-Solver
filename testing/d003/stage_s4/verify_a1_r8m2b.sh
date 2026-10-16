REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# verify_a1_r8m2b.sh -- A1 audit verification: test gdb -batch exit code vs child exit code.
set -u
OUT="$EV/a1_verify.txt"
LOG="$EV/tmp/a1_gdb.log"

# Run gdb -batch running /bin/sh -c "exit 20"
# Note: we do not let failure of gdb exit the script
set +e
gdb -batch -return-child-result -ex "run" --args /bin/sh -c "exit 20" > "$LOG" 2>&1
GDB_RC_WITH_FLAG=$?

gdb -batch -ex "run" --args /bin/sh -c "exit 20" > "$LOG" 2>&1
GDB_RC_DEFAULT=$?
set -e

{
    echo "# A1 verification: gdb -batch exit code behavior"
    echo "gdb_exit_code_default=$GDB_RC_DEFAULT"
    echo "gdb_exit_code_with_return_child_result=$GDB_RC_WITH_FLAG"
    echo "--- gdb output ---"
    cat "$LOG"
} > "$OUT"

echo "verify_a1_r8m2b: wrote $OUT"
exit 0
