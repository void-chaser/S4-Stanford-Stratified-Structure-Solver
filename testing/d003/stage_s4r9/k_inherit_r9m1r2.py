#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# k_inherit_r9m1r2.py -- K-inheritance proof between F3 and F4 for all counted groups in M1 (Rule U315). New file.
import csv, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "K_INHERIT_R9M1R2.tsv")
OUT_RAW = os.path.join(EV, "K_INHERIT_RAW_R9M1R2.txt")

# 1. Driver paths
driver_paths = {
    "r6bstate-F3-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver"),
    "r6bstate-F4-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bstate-F4-dbg"),
    "init-F3-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/m2a2/build/init-F3-dbg"),
    "init-F4-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s3r5/build/init-F4-dbg"),
    "polyinj-F3-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/m2a2/build/polyinj-F3-dbg"),
    "polyinj-F4-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/polyinj-F4-dbg"),
    "d003-F3-kmap-dbg": os.path.join(EV, "build/d003-F3-kmap-dbg"),
    "d003-F4-kmap-dbg": os.path.join(EV, "build/d003-F4-kmap-dbg"),
    "d003plan-F3-kmap-dbg": os.path.join(EV, "build/d003plan-F3-kmap-dbg"),
    "d003plan-F4-kmap-dbg": os.path.join(EV, "build/d003plan-F4-kmap-dbg"),
}

family_drivers = {
    "r6bstate": ("r6bstate-F3-dbg", "r6bstate-F4-dbg"),
    "init": ("init-F3-dbg", "init-F4-dbg"),
    "polyinj": ("polyinj-F3-dbg", "polyinj-F4-dbg"),
    "d003": ("d003-F3-kmap-dbg", "d003-F4-kmap-dbg"),
    "d003plan": ("d003plan-F3-kmap-dbg", "d003plan-F4-kmap-dbg"),
}

# 2. Load linemap
linemap = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s3r5/LINEMAP_F3_F4_S3R5.tsv"), encoding="utf-8") as f:
    for l in f:
        l = l.strip()
        if not l or l.startswith("#") or l.startswith("site_id\t"):
            continue
        parts = l.split("\t")
        linemap[int(parts[2])] = int(parts[3])

def map_lineno(fl, ln):
    if fl and os.path.basename(fl) == "S4.cpp":
        if ln <= 1759:
            return ln
        elif ln in linemap:
            return linemap[ln]
        elif ln >= 1774:
            return ln + 13
    return ln

# 3. Load groups
k_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1/K_INHERIT_R9M1.tsv")
lines = [l for l in open(k_path, encoding="utf-8") if not l.startswith("#")]
groups = list(csv.DictReader(lines, delimiter="\t"))

GRID = ["pattern", "both", "4", "3"]

def run_gdb_capture(driver_exe, env_dict, bp_symbol, target_hits):
    cmds = [
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", f"b {bp_symbol}",
        "-ex", "run " + " ".join(GRID)
    ]
    for _ in range(max(0, target_hits - 1)):
        cmds.extend(["-ex", "bt 8", "-ex", "continue"])
    cmds.extend(["-ex", "bt 8", "-ex", "quit"])
    cmd = ["gdb", "-batch"] + cmds + ["--args", driver_exe] + GRID
    r = subprocess.run(cmd, env=env_dict, cwd=REPO, capture_output=True, text=True)
    return r.stdout

def parse_hits(gdb_stdout):
    hits = []
    blocks = gdb_stdout.split("Breakpoint 1,")
    for b in blocks[1:]:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if not lines or "exited with code" in lines[0] or "exited normally" in lines[0]:
            continue
        first_line = lines[0]
        arg_val = None
        m_id_sz = re.search(r"id=(\d+),\s*size=(\d+)", first_line)
        if m_id_sz:
            arg_val = f"id={m_id_sz.group(1)},size={m_id_sz.group(2)}"
        elif "fft_plan_exec" in first_line:
            arg_val = "exec"
        elif "fft_plan_dft_2d" in first_line:
            arg_val = "plan"
        else:
            m_sz = re.search(r"(?:size|n|ID|id)=([0-9]+)", first_line)
            if m_sz:
                arg_val = m_sz.group(1)
        func_name, file_name, line_no = None, None, 0
        for l in lines[1:]:
            if not l.startswith("#"):
                continue
            m_s4 = re.search(r"in\s+([a-zA-Z0-9_:]+).*?\bat\s+([^:]+):(\d+)", l)
            if m_s4:
                fn, fl, ln = m_s4.group(1), m_s4.group(2), int(m_s4.group(3))
                # Exclude injection and driver wrappers
                if "inject_" in fl or "driver_" in fl:
                    continue
                func_name, file_name, line_no = fn, fl, ln
                break
        hits.append({"arg": arg_val, "func": func_name, "file": file_name, "line": line_no})
    return hits

raw_lines = [
    "# K_INHERIT_RAW_R9M1R2.txt -- Raw GDB and trace capture for K inheritance in P05-S4 R9 M1R2 (Rule U315)\n\n"
]

results = []
summary_counts = {
    "PASS_K_INHERITED_R3": 0,
    "NO_SEQ_EVIDENCE_R3": 0,
    "DIVERGENT": 0
}

# Also gather HIT line equivalence for all points
# To distinguish BOTH_EMPTY vs NONEMPTY_IDENTICAL
# We load formal facts from r9m1 or run points
# For K table:
for g in groups:
    gid = g["group_id"]
    fam = g["driver_family"]
    f3_d_name, f4_d_name = family_drivers[fam]
    f3_exe = driver_paths[f3_d_name]
    f4_exe = driver_paths[f4_d_name]
    bp = g["bp_symbol"]
    env_str = g["clean_env"]
    env = os.environ.copy()
    for item in env_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            env[k.strip()] = v.strip()

    target_hits = max(int(g["hits_f3"]), int(g["hits_f4"]), int(g["k_max"]))

    out_f3 = run_gdb_capture(f3_exe, env, bp, target_hits)
    out_f4 = run_gdb_capture(f4_exe, env, bp, target_hits)

    hits_f3 = parse_hits(out_f3)
    hits_f4 = parse_hits(out_f4)

    n3, n4 = len(hits_f3), len(hits_f4)

    raw_lines.append(f"=== Group {gid} ({fam}): bp={bp}, env={env_str} ===\n")
    raw_lines.append(f"F3 ({f3_d_name}, hits={n3}):\n")
    for i, h in enumerate(hits_f3):
        raw_lines.append(f"  [{i}] arg={h['arg']} func={h['func']} loc={h['file']}:{h['line']}\n")
    raw_lines.append(f"F4 ({f4_d_name}, hits={n4}):\n")
    for i, h in enumerate(hits_f4):
        raw_lines.append(f"  [{i}] arg={h['arg']} func={h['func']} loc={h['file']}:{h['line']}\n")
    raw_lines.append("\n")

    diffs = []
    status = "UNKNOWN"
    details = ""

    if n3 != n4:
        status = "DIVERGENT"
        details = f"Hit count mismatch: F3={n3} != F4={n4}"
    elif n3 == 0:
        status = "DIVERGENT"
        details = "0 hits captured on both sides"
    else:
        # Check sequence
        no_seq = False
        seq_match = True
        for i in range(n3):
            h3 = hits_f3[i]
            h4 = hits_f4[i]
            if h3["func"] is None or h4["func"] is None:
                no_seq = True
                break
            mapped_ln3 = map_lineno(h3["file"], h3["line"])
            # Compare arg/size, func, and mapped line
            if h3["func"] != h4["func"]:
                seq_match = False
                diffs.append(f"hit{i}_func({h3['func']}!={h4['func']})")
            if mapped_ln3 != h4["line"]:
                seq_match = False
                diffs.append(f"hit{i}_line({mapped_ln3}!={h4['line']})")
            # If both args are present, compare them
            if h3["arg"] is not None and h4["arg"] is not None and h3["arg"] != h4["arg"]:
                seq_match = False
                diffs.append(f"hit{i}_arg({h3['arg']}!={h4['arg']})")

        if no_seq:
            if int(g["k_max"]) == 1:
                status = "PASS_K_INHERITED_R3"
                details = f"Equal hits ({n3} vs {n4}); k_max=1 substitute via U303/U315"
            else:
                status = "NO_SEQ_EVIDENCE_R3"
                details = f"Equal hits ({n3} vs {n4}); could not extract S4 stack frame"
        elif seq_match:
            status = "PASS_K_INHERITED_R3"
            details = f"Equal hits ({n3} vs {n4}); full trace sequence matched"
        else:
            status = "DIVERGENT"
            details = f"Trace diverged: {'; '.join(diffs)}"

    summary_counts[status] += 1
    results.append([
        gid, fam, f3_d_name, f4_d_name, env_str, bp, g["k_max"], n3, n4, status, details, g["m1_points_count"]
    ])

print("K inheritance evaluation complete across 53 groups:")
print("Summary counts:", summary_counts)

# Assertions
assert summary_counts["DIVERGENT"] == 0, f"DIVERGENT groups detected: {summary_counts['DIVERGENT']}"

# Write K_INHERIT_RAW_R9M1R2.txt
with open(OUT_RAW, "w", encoding="utf-8") as f:
    for line in raw_lines:
        f.write(line)

# Write K_INHERIT_R9M1R2.tsv
with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("# K_INHERIT_R9M1R2.tsv -- K inheritance proof table for P05-S4 R9 M1R2 (Rule U315)\n")
    f.write("group_id\tdriver_family\tf3_driver\tf4_driver\tclean_env\tbp_symbol\tk_max\thits_f3\thits_f4\tstatus\tdetails\tm1_points_count\n")
    for r in results:
        f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]}\t{r[7]}\t{r[8]}\t{r[9]}\t{r[10]}\t{r[11]}\n")

print(f"Wrote {OUT_TSV} and {OUT_RAW}.")
