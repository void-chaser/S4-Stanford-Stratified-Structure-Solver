#!/usr/bin/env python3
# test_s4malloc_r8m2d.py -- Test and map S4_malloc calls across the 3 drivers and 3 combos.
import os, subprocess, sys, re

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2d"))

DRIVERS = [
    ("init-F3-san", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san")),
    ("init-F3-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-dbg")),
    ("init-B-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build", "init-B-dbg")),
]

COMBOS = [
    ("closed2d-ng1", "closed2d", "1"),
    ("fft-ng5", "fft", "5"),
    ("kottke-ng5", "kottke", "5"),
]

GDB_CMDS = """set pagination off
set confirm off
set $count = 0

break S4_malloc
commands
silent
set $count = $count + 1
printf "CALL_S4_MALLOC k=%ld\\n", $count
backtrace 3
continue
end

run pattern both 4 3
quit
"""

GDB_SCRIPT_PATH = os.path.join(EV, "tmp", "map_s4malloc.gdb")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
with open(GDB_SCRIPT_PATH, "w") as fh:
    fh.write(GDB_CMDS)

out_lines = []
out_lines.append("# S4_MALLOC MAPPING TEST OUTPUT")

for dname, dpath in DRIVERS:
    for cname, mode, ng in COMBOS:
        env = os.environ.copy()
        env["FMM_MODE"] = mode
        env["S4FMM_NG"] = ng
        env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
        env["UBSAN_OPTIONS"] = "abort_on_error=0"
        for k in list(env.keys()):
            if k.startswith("S4FMM_INJECT") or k.startswith("S4_FAIL_ALLOC"):
                del env[k]

        cmd = ["gdb", "-batch", "-x", GDB_SCRIPT_PATH, "--args", dpath, "pattern", "both", "4", "3"]
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        out_lines.append(f"\n=== DRIVER: {dname} COMBO: {cname} ===")
        # Parse output
        lines = p.stdout.splitlines()
        current_k = None
        for l in lines:
            m_k = re.match(r"^CALL_S4_MALLOC k=(\d+)", l)
            if m_k:
                current_k = m_k.group(1)
                continue
            if current_k and "#1" in l:
                out_lines.append(f"  k={current_k}: {l.strip()}")
                current_k = None

res_text = "\n".join(out_lines) + "\n"
out_path = os.path.join(EV, "TEST_S4MALLOC_MAP.txt")
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write(res_text)

print(f"Wrote {out_path}")
print(res_text[:2000])
