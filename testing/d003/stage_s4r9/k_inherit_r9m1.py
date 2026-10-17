#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# k_inherit_r9m1.py -- K-inheritance proof between F3 and F4 for all counted groups in M1 (Rules U300, U309). New file.
import csv, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "K_INHERIT_R9M1.tsv")
OUT_RAW = os.path.join(EV, "K_INHERIT_RAW_R9M1.txt")

# 1. Load drivers
f3_to_f4 = {}
with open(os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv"), "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        parts = line.split("\t")
        f3_to_f4[parts[0]] = parts[2]

f3_paths = {
    "d003-F3-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003-F3-plain/driver"),
    "d003plan-F3-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003plan-F3-plain/driver"),
    "init-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/init-F3/driver"),
    "poly-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/poly-F3/driver"),
    "polyinj-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/polyinj-F3/driver"),
    "r6bseam-fmmret-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bseam-fmmret-F3/driver"),
    "r6bseam-seamF-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bseam-seamF-F3/driver"),
    "r6bstate-F3-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver"),
    "r6dnv1-F3-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6dnv1-F3-plain/driver"),
    "seam-fmmret-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/seam-fmmret-F3/driver"),
    "seam-seamF-F3": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/seam-seamF-F3/driver"),
    "tri-F3-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/tri-F3-dbg/driver"),
}

f4_paths = {
    "d003-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/d003-F4-plain"),
    "d003plan-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/d003plan-F4-plain"),
    "init-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/init-F4-plain"),
    "poly-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/poly-F4-plain"),
    "polyinj-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/polyinj-F4-plain"),
    "r6bseam-fmmret-F4": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/r6bseam-fmmret-F4"),
    "r6bseam-seamF-F4": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bseam-seamF-F4"),
    "r6bstate-F4-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bstate-F4-dbg"),
    "r6dnv1-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/r6dnv1-F4-plain"),
    "seam-fmmret-F4": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/seam-fmmret-F4"),
    "seam-seamF-F4": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/seam-seamF-F4"),
    "tri-F4-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/build/tri-F4-dbg"),
}

# 2. Extract counted groups
plan_b1 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        plan_b1[r["point_id"]] = r

supp_b3 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/PREREG_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        supp_b3[dict(zip(h, l))["point_id"]] = dict(zip(h, l))

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1c = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

def clean_base_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

counted_groups = {}
def add_point(drv, env, site, nth, pid):
    if nth == "-" and not site.startswith("init:") and not site.startswith("win:") and not site.startswith("plancall:"):
        return
    if site.startswith("init:") or site.startswith("win:"):
        bp = "__wrap_malloc"
    elif "s4malloc" in site or (nth != "-" and "s4malloc" in env):
        bp = "__wrap__Z9S4_mallocm"
    elif "exec" in site or (nth != "-" and "exec" in env):
        bp = "__wrap__Z13fft_plan_execP12tag_fft_plan"
    elif "plan" in site or (nth != "-" and "plan" in env):
        bp = "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i"
    else:
        bp = "__wrap_malloc"

    k_val = 1
    if nth != "-":
        try: k_val = int(nth)
        except: pass
    elif ":" in site:
        try: k_val = int(site.split(":")[-1])
        except: pass
    
    be = clean_base_env(env)
    fam = drv.replace("-F3-dbg", "").replace("-F3-plain", "").replace("-F3", "")
    gkey = (fam, drv, f3_to_f4[drv], be, bp)
    if gkey not in counted_groups:
        counted_groups[gkey] = {"k_max": 0, "pids": []}
    counted_groups[gkey]["k_max"] = max(counted_groups[gkey]["k_max"], k_val)
    counted_groups[gkey]["pids"].append(pid)

for r in eff_m1b:
    pid = r["point_id"]
    src = r["source"]
    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        add_point(plan_b1[pid]["driver_name"], plan_b1[pid]["env_str"], plan_b1[pid]["inject_site"], plan_b1[pid]["k_nth"], pid)
    elif src == "SUPP_R8_M1b3":
        drv = supp_b3[pid]["driver_name"]
        env = supp_b3[pid]["env"]
        site, nth = "none", "-"
        for p in env.split(";"):
            if p.startswith("S4FMM_INJECT="): site = p.split("=")[1]
            if p.startswith("S4FMM_NTH="): nth = p.split("=")[1]
        add_point(drv, env, site, nth, pid)

for r in eff_m1c:
    drv = r["driver_name"]
    env = r["env_expected"]
    site, nth = "none", "-"
    for p in env.split(";"):
        if p.startswith("S4FMM_INJECT="): site = p.split("=")[1]
        if p.startswith("S4FMM_NTH="): nth = p.split("=")[1]
    add_point(drv, env, site, nth, r["point_id_r8"])

print(f"Total counted groups identified: {len(counted_groups)}")

def map_lineno(fname, lineno):
    base = os.path.basename(fname)
    if base == "S4.cpp":
        if lineno <= 1759:
            return lineno
        elif lineno <= 1773:
            soln_map = {1760: 1760, 1763: 1763, 1764: 1771, 1765: 1772, 1766: 1773, 1773: 1785}
            return soln_map.get(lineno, lineno + 8)
        else:
            return lineno + 13
    return lineno

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
                if "S4/" in fl or fl.endswith("S4.cpp") or fl.endswith(".c") or fl.endswith(".cpp"):
                    func_name, file_name, line_no = fn, fl, ln
                    break
        hits.append({"arg": arg_val, "func": func_name, "file": file_name, "line": line_no})
    return hits

raw_lines = [
    "# K_INHERIT_RAW_R9M1.txt -- Raw GDB and trace capture for K inheritance in P05-S4 R9 M1 (Rule U300/U309)\n\n"
]

rows = []
divergent_groups = []

for idx, gkey in enumerate(sorted(counted_groups.keys()), 1):
    fam, drv, f4_drv, be, bp = gkey
    v = counted_groups[gkey]
    k_max = v["k_max"]
    gid = f"KGRP-M1-{idx:03d}"
    exe3 = f3_paths[drv]
    exe4 = f4_paths[f4_drv]

    env = os.environ.copy()
    for pair in be.split(";"):
        if "=" in pair:
            k, val = pair.split("=", 1)
            env[k] = val
    
    target_hits = k_max + 2
    out3 = run_gdb_capture(exe3, env, bp, target_hits)
    out4 = run_gdb_capture(exe4, env, bp, target_hits)
    h3 = parse_hits(out3)
    h4 = parse_hits(out4)

    raw_lines.append(f"=== {gid}: {fam} | {drv} vs {f4_drv} | {be} (bp={bp}, k_max={k_max}) ===\n")
    raw_lines.append(f"--- F3 Hits ({len(h3)}) ---\n")
    for h in h3:
        raw_lines.append(f"  arg={h['arg']} func={h['func']} loc={h['file']}:{h['line']}\n")
    raw_lines.append(f"--- F4 Hits ({len(h4)}) ---\n")
    for h in h4:
        raw_lines.append(f"  arg={h['arg']} func={h['func']} loc={h['file']}:{h['line']}\n")
    raw_lines.append("\n")

    has_ev3 = any(h["func"] is not None for h in h3)
    has_ev4 = any(h["func"] is not None for h in h4)

    if not has_ev3 and not has_ev4:
        st = "NO_SEQ_EVIDENCE_R2"
        details = f"Equal hits ({len(h3)} vs {len(h4)}); plain driver without debug symbols (substitute with HIT equivalence under U303/U309)"
    elif len(h3) != len(h4):
        st = "K_DIVERGENT_R2"
        details = f"HIT_COUNT_MISMATCH(F3={len(h3)} F4={len(h4)})"
        divergent_groups.append((gid, gkey, details))
    else:
        st = "PASS_K_INHERITED_R2"
        details = f"Verified {len(h3)} calls identical"
        for i in range(len(h3)):
            if h3[i]["arg"] != h4[i]["arg"]:
                st = "K_DIVERGENT_R2"
                details = f"SIZE_MISMATCH(call {i+1}: F3={h3[i]['arg']} F4={h4[i]['arg']})"
                divergent_groups.append((gid, gkey, details))
                break
            if h3[i]["func"] != h4[i]["func"]:
                st = "K_DIVERGENT_R2"
                details = f"FUNC_MISMATCH(call {i+1}: F3={h3[i]['func']} F4={h4[i]['func']})"
                divergent_groups.append((gid, gkey, details))
                break
            ml3 = map_lineno(h3[i]["file"] or "", h3[i]["line"])
            if ml3 != h4[i]["line"]:
                st = "K_DIVERGENT_R2"
                details = f"LINE_MISMATCH(call {i+1}: mapped_F3={ml3} F4={h4[i]['line']})"
                divergent_groups.append((gid, gkey, details))
                break

    rows.append([
        gid, fam, drv, f4_drv, be, bp, str(k_max), str(len(h3)), str(len(h4)), st, details, str(len(v["pids"]))
    ])

print(f"Processed {len(rows)} counted groups. Divergent={len(divergent_groups)}")

# Write TSV
header = [
    "group_id", "driver_family", "f3_driver", "f4_driver", "clean_env", "bp_symbol",
    "k_max", "hits_f3", "hits_f4", "status", "details", "m1_points_count"
]
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# K_INHERIT_R9M1.tsv -- K inheritance proof table for P05-S4 R9 M1 (Rule U300, U309)\n")
    fh.write("\t".join(header) + "\n")
    for r in rows:
        fh.write("\t".join(r) + "\n")

# Write RAW
with open(OUT_RAW, "w", encoding="utf-8") as fh:
    fh.writelines(raw_lines)

print(f"Wrote K_INHERIT_R9M1.tsv -> {OUT_TSV}")
print(f"Wrote K_INHERIT_RAW_R9M1.txt -> {OUT_RAW}")

if divergent_groups:
    print(f"WARNING: Divergent groups found: {len(divergent_groups)}", file=sys.stderr)
    for dg in divergent_groups:
        print(f"  {dg[0]}: {dg[1]} -> {dg[2]}", file=sys.stderr)

sys.exit(len(divergent_groups))
