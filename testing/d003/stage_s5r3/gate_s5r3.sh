#!/bin/sh
# gate_s5r3.sh -- P05-S5 R3 end gate wrapper. usage: sh testing/d003/safe_run.sh p05-s5r3 -- sh testing/d003/stage_s5r3/gate_s5r3.sh end [--commit-i SHA|HEAD] [--out PATH]
exec python3 -I -B "$(git rev-parse --show-toplevel)/testing/d003/stage_s5r3/gate_check_s5r3.py" "$@"
