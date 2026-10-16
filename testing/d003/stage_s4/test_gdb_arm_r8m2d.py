#!/usr/bin/env python3
# test_gdb_arm_r8m2d.py -- Test if GDB can arm s4_fail_alloc_armed and trip S4_FAIL_ALLOC_AT=3.
import os, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2d"))

DRV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san")

GDB_CMDS = """set pagination off
set confirm off

break main
commands
silent
set 'S4/S4.cpp'::s4_fail_alloc_armed = 1
continue
end

run pattern both 4 3
bt 24
quit
"""

GDB_SCRIPT_PATH = os.path.join(EV, "tmp", "test_arm.gdb")
with open(GDB_SCRIPT_PATH, "w") as fh:
    fh.write(GDB_CMDS)

env = os.environ.copy()
env["FMM_MODE"] = "closed2d"
env["S4FMM_NG"] = "1"
env["S4_FAIL_ALLOC_AT"] = "3"
env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
env["UBSAN_OPTIONS"] = "abort_on_error=0"
for k in list(env.keys()):
    if k.startswith("S4FMM_INJECT"):
        del env[k]

cmd = ["gdb", "-batch", "-x", GDB_SCRIPT_PATH, "--args", DRV, "pattern", "both", "4", "3"]
p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print("RETURNCODE:", p.returncode)
print("STDOUT:", p.stdout[:1000])
print("STDERR:", p.stderr[:500])
