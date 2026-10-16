#!/usr/bin/env python3
# test_fail_alloc_r8m2d.py -- Test if S4_FAIL_ALLOC_AT=3 causes init-F3-san to fail/crash.
import os, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2d"))

DRV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san")

env = os.environ.copy()
env["FMM_MODE"] = "closed2d"
env["S4FMM_NG"] = "1"
env["S4_FAIL_ALLOC_AT"] = "3"
env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
env["UBSAN_OPTIONS"] = "abort_on_error=0"
for k in list(env.keys()):
    if k.startswith("S4FMM_INJECT"):
        del env[k]

cmd = [DRV, "pattern", "both", "4", "3"]
p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print("RETURNCODE:", p.returncode)
print("STDOUT:", p.stdout[:500])
print("STDERR:", p.stderr[:500])
