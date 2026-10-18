#!/bin/sh
# gate_s5r4.sh -- wrapper so the end gate is one frozen, logged command (task brief section 6).
# The single CHECK invocation is logged through safe_run by the caller; this wrapper only forwards args.
exec python3 -I -B testing/d003/stage_s5r4/gate_check_s5r4.py end "$@"
