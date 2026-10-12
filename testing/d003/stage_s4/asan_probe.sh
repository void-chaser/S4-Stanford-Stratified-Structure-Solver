#!/bin/sh
# asan_probe.sh -- P05-S4 V0: is the ASan/UBSan toolchain usable?  Writes under $EV only.
set -u
REPO=$(git rev-parse --show-toplevel)
EV="$REPO/checkpoints/p05/evidence/p05-s4"
TMPDIR="$EV/tmp"
export TMPDIR
mkdir -p "$EV/san"
ulimit -c 0
printf '%s\n' 'int main(void){ return 0; }' > "$EV/tmp/asan_probe_ok.c"
printf '%s\n' '#include <stdio.h>' 'int main(void){ printf("probe-ok\n"); return 0; }' > "$EV/tmp/asan_probe_run.c"
gcc -std=c99 -fsanitize=address,undefined -fno-omit-frame-pointer -g -O0 -o "$EV/san/probe_bin" "$EV/tmp/asan_probe_run.c" > "$EV/san/probe_build.log" 2>&1
rc_build=$?
echo "build_rc=$rc_build"
if [ "$rc_build" -ne 0 ]; then
    echo "toolchain=UNAVAILABLE (build failed)"
    exit 0
fi
ASAN_OPTIONS="log_path=$EV/san/probe-asan" UBSAN_OPTIONS="print_stacktrace=1:log_path=$EV/san/probe-ubsan" LSAN_OPTIONS="log_path=$EV/san/probe-lsan" "$EV/san/probe_bin" > "$EV/san/probe_run.log" 2>&1
rc_run=$?
echo "run_rc=$rc_run"
cat "$EV/san/probe_run.log"
if [ "$rc_run" -eq 0 ]; then
    echo "toolchain=AVAILABLE"
else
    echo "toolchain=RUN_FAILED"
fi
