#!/usr/bin/env python3
# generate_s4malloc_map_r8m2d.py -- Generates S4MALLOC_MAP_R8_M2d.tsv by mapping S4_malloc across 9 combinations.
import csv
import os
import re
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2d")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
OUT_TSV = os.path.join(EV, "S4MALLOC_MAP_R8_M2d.tsv")

DRIVERS = [
    ("init-F3-san", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san"), "F3"),
    ("init-F3-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-dbg"), "F3"),
    ("init-B-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build", "init-B-dbg"), "B"),
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
printf "CALL_S4_MALLOC k=%ld size=%zu\\n", $count, size
backtrace 3
continue
end

run pattern both 4 3
quit
"""

def main():
    tmp_dir = os.path.join(EV, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    gdb_script = os.path.join(tmp_dir, "map_s4malloc.gdb")
    with open(gdb_script, "w") as fh:
        fh.write(GDB_CMDS)

    rows = []
    found_1764 = {}

    for dname, dpath, tree in DRIVERS:
        for cname, mode, ng in COMBOS:
            env = os.environ.copy()
            env["FMM_MODE"] = mode
            env["S4FMM_NG"] = ng
            env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
            env["UBSAN_OPTIONS"] = "abort_on_error=0"
            for k in list(env.keys()):
                if k.startswith("S4FMM_INJECT") or k.startswith("S4_FAIL_ALLOC"):
                    del env[k]

            cmd = ["gdb", "-batch", "-x", gdb_script, "--args", dpath, "pattern", "both", "4", "3"]
            p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            lines = p.stdout.splitlines()
            current_k = None
            current_sz = "-"

            for l in lines:
                m_call = re.match(r"^CALL_S4_MALLOC k=(\d+) size=(\d+)", l)
                if m_call:
                    current_k = int(m_call.group(1))
                    current_sz = m_call.group(2)
                    continue

                if current_k is not None and "#1" in l:
                    # Parse caller frame
                    m_frame = re.search(r"#1\s+(?:0x[0-9a-fA-F]+\s+in\s+)?([^\s(]+).*?\s+at\s+([^:]+):(\d+)", l)
                    if m_frame:
                        func = m_frame.group(1)
                        fpath = os.path.basename(m_frame.group(2))
                        fline = int(m_frame.group(3))
                    else:
                        func = "unknown"
                        fpath = "unknown"
                        fline = -1

                    tag = "other"
                    notes = "-"
                    if tree == "F3":
                        if fline == 1764:
                            tag = "1764_ab"
                            notes = "S->solution->ab via S4_malloc (F3 S4.cpp:1764; target site for -FA injection)"
                            found_1764[(dname, cname)] = current_k
                        elif fline in (311, 381):
                            tag = f"S4_Simulation_New_{fline}"
                            notes = f"lattice / grid setup in S4_Simulation_New (S4.cpp:{fline})"
                        elif fline == 2310:
                            tag = "ComputeLayerModes_2310"
                            notes = "LayerModes allocation in Simulation_ComputeLayerModes"
                    elif tree == "B":
                        if fline == 1755:
                            tag = "1755_ab"
                            notes = "S->solution->ab via S4_malloc (B S4.cpp:1755 baseline)"
                            found_1764[(dname, cname)] = current_k
                        elif fline in (311, 381):
                            tag = f"S4_Simulation_New_{fline}"
                            notes = f"lattice / grid setup in S4_Simulation_New (S4.cpp:{fline})"
                        elif fline == 2295:
                            tag = "ComputeLayerModes_2295"
                            notes = "LayerModes allocation in Simulation_ComputeLayerModes (B)"

                    rows.append({
                        "driver": dname,
                        "combo": cname,
                        "k": str(current_k),
                        "size": current_sz,
                        "caller_file": fpath,
                        "caller_line": str(fline),
                        "caller_func": func,
                        "tag": tag,
                        "notes": notes,
                    })
                    current_k = None

    # Write S4MALLOC_MAP_R8_M2d.tsv
    headers = ["driver", "combo", "k", "size", "caller_file", "caller_line", "caller_func", "tag", "notes"]
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, delimiter="\t")
        fh.write("# S4MALLOC_MAP_R8_M2d.tsv -- S4_malloc call mapping across 9 combinations\n")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} S4_malloc mapping entries -> {OUT_TSV}")
    print("\nConfirmed 1764 (ab) allocation index k across all combinations:")
    for (dname, cname), k_val in sorted(found_1764.items()):
        print(f"  {dname:<14} {cname:<14} -> k={k_val}")

    # Check that 1764 is uniquely determined for F3
    f3_k_values = set(v for (d, c), v in found_1764.items() if "F3" in d)
    if len(f3_k_values) != 1:
        sys.exit(f"STOP CONDITION: S4.cpp:1764 K could not be uniquely determined: {found_1764}")
    k_unique = list(f3_k_values)[0]
    print(f"\nSUCCESS: S4.cpp:1764 K is uniquely determined as K={k_unique}.")
    return 0


if __name__ == "__main__":
    main()
