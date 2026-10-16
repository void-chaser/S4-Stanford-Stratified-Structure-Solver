#!/usr/bin/env python3
# run_malloc_map_r8m2c.py -- P05-S4 R8 M2c malloc mapping runner.
# Executes 9 combinations (3 drivers x 3 combos) under GDB to map outside malloc calls.
import csv, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.path.join(REPO, EV_REL)
OUT_TSV = os.path.join(EV, "MALLOC_MAP_R8_M2c.tsv")

GDB_SCRIPT = os.path.join(REPO, "testing", "d003", "stage_s4", "malloc_map_r8m2c.gdb")

DRIVERS = [
    ("init-F3-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-dbg"), "F3"),
    ("init-F3-san", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "init-F3-san"), "F3"),
    ("init-B-dbg", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build", "init-B-dbg"), "B"),
]

COMBOS = [
    ("closed2d-ng1", "closed2d", "1"),
    ("fft-ng5", "fft", "5"),
    ("kottke-ng5", "kottke", "5"),
]

def run_one(driver_name, driver_path, tree, combo_name, mode, ng):
    env = os.environ.copy()
    env["FMM_MODE"] = mode
    env["S4FMM_NG"] = ng
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
    env["UBSAN_OPTIONS"] = "abort_on_error=0"
    if "S4FMM_INJECT" in env:
        del env["S4FMM_INJECT"]

    cmd = ["gdb", "-batch", "-x", GDB_SCRIPT, "--args", driver_path, "pattern", "both", "4", "3"]
    proc = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Parse stdout and stderr
    entries = []
    lines = proc.stdout.splitlines()
    
    current_entry = None
    
    for l in lines:
        m_entry = re.match(r"^MALLOC_MAP_ENTRY k=(\d+) n=(\d+)", l)
        if m_entry:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "driver": driver_name,
                "combo": combo_name,
                "tree": tree,
                "k": int(m_entry.group(1)),
                "n": int(m_entry.group(2)),
                "frames": []
            }
            continue
        m_frame = re.match(r"^#(\d+)\s+(0x[0-9a-fA-F]+\s+in\s+)?([^\s(]+).*?\s+at\s+([^:]+):(\d+)", l)
        if m_frame and current_entry is not None:
            frame_num = int(m_frame.group(1))
            if frame_num == 0:
                continue # Skip __wrap_malloc itself
            func = m_frame.group(3)
            fpath = m_frame.group(4)
            fline = int(m_frame.group(5))
            current_entry["frames"].append((frame_num, func, fpath, fline))
            
    if current_entry:
        entries.append(current_entry)
        
    # Analyze caller and tag for each entry
    records = []
    for e in entries:
        k = e["k"]
        n = e["n"]
        tree = e["tree"]
        
        caller_func = "unknown"
        caller_file = "unknown"
        caller_line = -1
        tag = "other"
        notes = "-"
        
        # Look through frames starting from frame 1
        # If frame 1 is malloc_aligned/S4_malloc, look up to find who requested it
        chosen_frame = None
        # Check if Simulation_InitSolution is in the callstack
        for fnum, func, fpath, fline in e["frames"]:
            if "Simulation_InitSolution" in func:
                chosen_frame = (func, fpath, fline)
                break
        if not chosen_frame and e["frames"]:
            # fallback to frame 1
            fnum, func, fpath, fline = e["frames"][0]
            chosen_frame = (func, fpath, fline)
            
        if chosen_frame:
            caller_func, caller_file, caller_line = chosen_frame
            # Check tags
            if tree == "F3":
                if caller_line == 1729:
                    tag = "1729_parent"
                    notes = "parent allocation (F3 S4.cpp:1729)"
                elif caller_line == 1763:
                    tag = "1763_Solution_"
                    notes = "Solution_ allocation (F3 S4.cpp:1763; RP-R8-M2c-1 site)"
                elif caller_line == 1764:
                    tag = "1764_ab"
                    notes = "S->solution->ab via S4_malloc (F3 S4.cpp:1764)"
                elif caller_line == 1765:
                    tag = "1765_solved"
                    notes = "S->solution->solved (F3 S4.cpp:1765)"
            elif tree == "B":
                if caller_line == 1729:
                    tag = "1729_parent"
                    notes = "parent allocation (B S4.cpp:1729)"
                elif caller_line == 1754:
                    tag = "1763_Solution_"
                    notes = "Solution_ allocation (B S4.cpp:1754 baseline)"
                elif caller_line == 1755:
                    tag = "1764_ab"
                    notes = "S->solution->ab via S4_malloc (B S4.cpp:1755 baseline)"
                elif caller_line == 1756:
                    tag = "1765_solved"
                    notes = "S->solution->solved (B S4.cpp:1756 baseline)"
                    
        records.append({
            "driver": driver_name,
            "combo": combo_name,
            "k": k,
            "n": n,
            "caller_file": os.path.basename(caller_file),
            "caller_line": caller_line,
            "caller_func": caller_func,
            "tag": tag,
            "notes": notes
        })
    return records

def main():
    all_records = []
    summary_key_sites = []
    
    for dname, dpath, tree in DRIVERS:
        for cname, mode, ng in COMBOS:
            print("Mapping %s on %s..." % (dname, cname))
            recs = run_one(dname, dpath, tree, cname, mode, ng)
            all_records.extend(recs)
            
            # Find key sites
            parent_k = [r["k"] for r in recs if r["tag"] == "1729_parent" and r["n"] > 0]
            soln_k = [r["k"] for r in recs if r["tag"] == "1763_Solution_"]
            ab_k = [r["k"] for r in recs if r["tag"] == "1764_ab"]
            solved_k = [r["k"] for r in recs if r["tag"] == "1765_solved"]
            summary_key_sites.append((dname, cname, parent_k, soln_k, ab_k, solved_k))

    fieldnames = ["driver", "combo", "k", "n", "caller_file", "caller_line", "caller_func", "tag", "notes"]
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in all_records:
            writer.writerow(r)
            
    print("run_malloc_map_r8m2c: wrote %d entries to %s" % (len(all_records), OUT_TSV))
    print("\n=== KEY SITES SUMMARY ===")
    print("driver\tcombo\t1729_parent_k\t1763_Solution__k\t1764_ab_k\t1765_solved_k")
    for dname, cname, pk, sk, ak, svk in summary_key_sites:
        print("%s\t%s\t%s\t%s\t%s\t%s" % (dname, cname, pk, sk, ak, svk))
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
