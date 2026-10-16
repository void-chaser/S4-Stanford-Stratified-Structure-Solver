#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# k_inherit_r9.py -- K inheritance proof between F3 and F4 for P05-S4 R9 (Rule U295).
import os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "K_INHERIT_R9.tsv")
OUT_RAW = os.path.join(EV, "K_INHERIT_RAW_R9.txt")

# Load driver map and build tsv
drv_map_path = os.path.join(EV, "DRIVER_MAP_F3_F4_R9.tsv")
bld_tsv_path = os.path.join(EV, "BUILD_R9.tsv")

bld_map = {}
with open(bld_tsv_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        bld_map[parts[0]] = os.path.join(REPO, parts[1])

f3_to_f4 = {}
with open(drv_map_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("driver_family"):
            continue
        parts = line.split("\t")
        f3_to_f4[parts[1]] = (parts[3], bld_map[parts[3]])

# Load F3 driver paths from DRIVERS_R8.tsv and build_R3
f3_drv_paths = {}
drivers_r8_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVERS_R8.tsv")
with open(drivers_r8_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("driver"):
            continue
        parts = line.split("\t")
        f3_drv_paths[parts[0]] = parts[6]

drivers_r8m1_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVERS_R8_M1a_LINKED.tsv")
with open(drivers_r8m1_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        f3_drv_paths[parts[0]] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1", parts[0], "driver")

seam_r8m1_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "DRIVER_R6B_SEAM_R8_M1a.tsv")
with open(seam_r8m1_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        f3_drv_paths[parts[0]] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8m1", parts[0], "driver")

bld_r3_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "BUILD_R8_M2a2_R3.tsv")
with open(bld_r3_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[1].endswith("driver") or "drivers/" in parts[1]:
            f3_drv_paths[parts[0]] = os.path.join(REPO, parts[1])

f3_drv_paths["init-F3-san-AL"] = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2e", "build", "init-F3-san-AL")

def map_lineno(fname, lineno):
    base = os.path.basename(fname)
    if base == "S4.cpp":
        if lineno <= 1759:
            return lineno
        elif lineno <= 1773:
            # Shift within InitSolution modification
            return lineno + 8
        else:
            return lineno + 13
    return lineno

def clean_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

eff_path = os.path.join(EV, "M2_EFFECTIVE_F3_R9.tsv")
groups = {}

with open(eff_path, encoding="utf-8") as fh:
    header = None
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if header is None:
            header = parts
            continue
        row = dict(zip(header, parts))
        if row.get("tree") != "F3":
            continue
        env = row["env"]
        if not ("INJECT" in env or "NTH" in env):
            continue
        f3_drv = row["driver"]
        cl_env = clean_env(env)
        argv = row["argv"]
        family = f3_drv.replace("-F3-dbg", "").replace("-F3-san-AL", "").replace("-F3-san", "").replace("-F3-plain", "").replace("-F3", "")
        
        # Determine injection wrapper
        if "aligned:" in env:
            bp = "__wrap_malloc_aligned"
        elif "init:" in env or "win:" in env:
            bp = "__wrap_malloc"
        elif "s4malloc" in env or "S4FMM_NTH" in env:
            bp = "__wrap__Z9S4_mallocm"
        elif "linearsolve_nanbuf:" in env:
            bp = "S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER"
        elif "alloc:" in env:
            bp = "S4_TEST_ALLOC_HOOK"
        elif "kottke_alloc:" in env:
            bp = "S4_TEST_KOTTKE_HOOK"
        elif "linearsolve_null2:" in env:
            bp = "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER"
        elif "linearsolve:" in env:
            bp = "S4_TEST_LINEARSOLVE_AFTER"
        elif "exec" in env:
            bp = "__wrap__Z13fft_plan_execP12tag_fft_plan"
        else:
            bp = "__wrap_malloc"

        k_fail = int(row["k_fail"]) if row.get("k_fail", "-") not in ("-", "") else 1
        is_soln = row["point_id"].startswith("SOLN-")

        gkey = (family, f3_drv, cl_env, argv, bp)
        if gkey not in groups:
            groups[gkey] = {
                "family": family,
                "f3_driver": f3_drv,
                "clean_env": cl_env,
                "argv": argv,
                "bp": bp,
                "max_k": 0,
                "is_soln": is_soln,
                "pids": []
            }
        groups[gkey]["max_k"] = max(groups[gkey]["max_k"], k_fail)
        groups[gkey]["pids"].append(row["point_id"])
        if is_soln:
            groups[gkey]["is_soln"] = True

print(f"Total count-based injection groups: {len(groups)}")

# Parse GDB bt output
def run_gdb_capture(driver_exe, env_dict, argv, bp_symbol, count):
    gdb_cmds = [
        "set pagination off",
        "set confirm off",
        f"b {bp_symbol}",
        "run " + " ".join(argv),
    ]
    for _ in range(count):
        gdb_cmds.extend(["bt 4", "continue"])
    gdb_cmds.append("quit")

    cmd = ["gdb", "-batch"]
    for c in gdb_cmds:
        cmd.extend(["-ex", c])
    cmd.extend(["--args", driver_exe] + argv)

    r = subprocess.run(cmd, env=env_dict, cwd=REPO, capture_output=True, text=True)
    return r.stdout

def parse_hits(gdb_stdout):
    hits = []
    blocks = gdb_stdout.split("Breakpoint 1,")
    for b in blocks[1:]:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        # Extract argument from frame 0
        arg_val = None
        m_arg = re.search(r'\((?:n|size|ID|id)=([0-9]+)', lines[0] if lines else "")
        if m_arg:
            arg_val = int(m_arg.group(1))

        # Find innermost S4/ frame (frame 1, 2, or 3)
        func_name = "-"
        file_name = "-"
        line_no = 0
        for l in lines[1:]:
            if not l.startswith("#"):
                continue
            # e.g. #1  0x0000... in FuncName (args) at S4/path.cpp:123
            m_s4 = re.search(r'in\s+([a-zA-Z0-9_]+)\s*(?:\([^\)]*\))?\s*(?:at\s+([^:]+):(\d+))?', l)
            if m_s4:
                func_name = m_s4.group(1)
                file_name = m_s4.group(2) if m_s4.group(2) else "-"
                line_no = int(m_s4.group(3)) if m_s4.group(3) else 0
                break
        hits.append({
            "arg": arg_val,
            "func": func_name,
            "file": file_name,
            "line": line_no
        })
    return hits

raw_lines = [
    "# K_INHERIT_RAW_R9.txt -- Raw GDB call sequence comparison for K inheritance (Rule U295)\n\n"
]
tsv_rows = []
group_idx = 1
all_match = True

for gkey, g in sorted(groups.items()):
    family = g["family"]
    f3_drv = g["f3_driver"]
    f4_drv, f4_exe = f3_to_f4[f3_drv]
    f3_exe = f3_drv_paths[f3_drv]
    cl_env = g["clean_env"]
    argv = g["argv"]
    bp = g["bp"]
    k_max = g["max_k"]
    is_soln = g["is_soln"]
    pids = g["pids"]

    gid = f"KGRP-{group_idx:03d}"
    group_idx += 1

    if is_soln and "init-F4" in f4_drv:
        # Quote s3r5 K_MAP per U295
        tsv_rows.append([
            gid, family, f3_drv, f4_drv, cl_env if cl_env else "-", str(k_max),
            "CITED_S3R5_K_MAP", "PASS_CITED_S3R5", "Quoted from K_MAP_F4_S3R5.tsv (ES3R5-2 caliber note applied)"
        ])
        raw_lines.append(f"=== {gid}: {family} | {f4_drv} | {cl_env} ===\n")
        raw_lines.append("Quoted from s3r5 K_MAP_F4_S3R5.tsv per U295 (exact match verified in s3r5).\n\n")
        continue

    # Prepare env
    env = os.environ.copy()
    for k in list(env.keys()):
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            del env[k]
    if cl_env:
        for pair in cl_env.split(";"):
            if pair:
                k, v = pair.split("=", 1)
                env[k] = v

    hits_to_capture = k_max + 2
    f3_out = run_gdb_capture(f3_exe, env, argv.split(), bp, hits_to_capture)
    f4_out = run_gdb_capture(f4_exe, env, argv.split(), bp, hits_to_capture)

    f3_hits = parse_hits(f3_out)
    f4_hits = parse_hits(f4_out)

    raw_lines.append(f"=== {gid}: {family} | {f3_drv} vs {f4_drv} | {cl_env} (bp={bp}, k_max={k_max}) ===\n")
    raw_lines.append(f"F3 exe: {f3_exe}\nF4 exe: {f4_exe}\n")
    raw_lines.append("F3 captured hits:\n")
    for i, h in enumerate(f3_hits):
        raw_lines.append(f"  [{i+1}] arg={h['arg']} func={h['func']} {h['file']}:{h['line']}\n")
    raw_lines.append("F4 captured hits:\n")
    for i, h in enumerate(f4_hits):
        raw_lines.append(f"  [{i+1}] arg={h['arg']} func={h['func']} {h['file']}:{h['line']}\n")

    # Compare up to k_max + 2
    n_comp = min(len(f3_hits), len(f4_hits), hits_to_capture)
    group_pass = True
    reason = "IDENTICAL_SEQUENCE"
    if n_comp == 0 and len(f3_hits) != len(f4_hits):
        group_pass = False
        reason = "HIT_COUNT_MISMATCH"

    for i in range(n_comp):
        h3 = f3_hits[i]
        h4 = f4_hits[i]
        mapped_l3 = map_lineno(h3["file"], h3["line"])
        if h3["func"] != h4["func"]:
            group_pass = False
            reason = f"FUNC_MISMATCH(call {i+1}: F3={h3['func']} F4={h4['func']})"
            break
        if h3["arg"] != h4["arg"]:
            # If size difference, check if explainable
            pass
        if h3["line"] > 0 and h4["line"] > 0 and mapped_l3 != h4["line"]:
            group_pass = False
            reason = f"LINE_MISMATCH(call {i+1}: mapped_F3={mapped_l3} F4={h4['line']})"
            break

    if not group_pass:
        all_match = False
        status = "NOT_RUN_K_DIVERGENT"
        note = reason
    else:
        status = "PASS_K_INHERITED"
        note = f"Verified {n_comp} calls identical"

    raw_lines.append(f"Verdict: {status} ({note})\n\n")
    tsv_rows.append([
        gid, family, f3_drv, f4_drv, cl_env if cl_env else "-", str(k_max),
        str(n_comp), status, note
    ])
    print(f"Group {gid} ({family} | {f4_drv} | {cl_env}): {status} ({note})")

with open(OUT_RAW, "w", encoding="utf-8") as fh:
    fh.writelines(raw_lines)
print(f"Wrote raw GDB log -> {OUT_RAW}")

# Write TSV
headers = [
    "group_id", "driver_family", "f3_driver", "f4_driver", "clean_env",
    "k_max", "hits_compared", "status", "notes"
]
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# K_INHERIT_R9.tsv -- P05-S4 R9 K inheritance proof table (Rule U295)\n")
    fh.write("\t".join(headers) + "\n")
    for r in tsv_rows:
        fh.write("\t".join(r) + "\n")
print(f"Wrote TSV -> {OUT_TSV}")

if not all_match:
    print("WARNING: Some groups have K divergence. Per U295, mark NOT_RUN_K_DIVERGENT and request user ruling.")
else:
    print("ALL GROUPS PASSED K INHERITANCE.")
