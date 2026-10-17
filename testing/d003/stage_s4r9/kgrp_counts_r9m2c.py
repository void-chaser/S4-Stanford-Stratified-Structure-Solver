#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# kgrp_counts_r9m2c.py -- Group-by-group hit counts for F3/F4 in R9 M0 and M2b raw logs (Step S-C-4).
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "KGRP_HITCOUNT_R9_R9M2b.tsv")

def parse_header(line):
    line = line.strip()
    m = re.match(r"^=== (KGRP-[0-9]+): (.*) ===$", line)
    if not m:
        return None
    gid = m.group(1)
    rest = m.group(2)
    parts = [p.strip() for p in rest.split("|")]
    fam = parts[0] if len(parts) > 0 else "-"
    drv = parts[1] if len(parts) > 1 else "-"
    env = "-"
    bp = "-"
    k_max = "-"
    if len(parts) > 2:
        rem = parts[2]
        m_paren = re.search(r"\((?:bp=)?([^,]+),\s*k_max=([0-9]+)\)", rem)
        if m_paren:
            bp = m_paren.group(1).strip()
            k_max = m_paren.group(2).strip()
            rem = rem[:m_paren.start()].strip()
        env = rem.strip()
    return gid, fam, drv, env, bp, k_max

def parse_k_raw(path):
    groups = {}
    cur_grp = None
    cur_side = None
    with open(path, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            hdr = parse_header(line)
            if hdr:
                cur_grp = hdr[0]
                groups[cur_grp] = {
                    "family": hdr[1],
                    "drivers": hdr[2],
                    "env": hdr[3],
                    "bp": hdr[4],
                    "k_max": hdr[5],
                    "f3": 0,
                    "f4": 0,
                    "start": idx,
                    "end": idx
                }
                cur_side = None
                continue
            if not cur_grp:
                continue
            if "F3 captured hits:" in line:
                cur_side = "f3"
            elif "F4 captured hits:" in line:
                cur_side = "f4"
            elif cur_side and re.match(r"^[ \t]+\[[0-9]+\]", line):
                groups[cur_grp][cur_side] += 1
            elif "Verdict:" in line:
                groups[cur_grp]["end"] = idx
                cur_side = None
    return groups

p_m0 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M0", "K_INHERIT_RAW_R9.txt")
p_m2b = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2b", "K_INHERIT_RAW_R9M2b.txt")

m0_grps = parse_k_raw(p_m0)
m2b_grps = parse_k_raw(p_m2b)

all_grp_ids = sorted(list(set(list(m0_grps.keys()) + list(m2b_grps.keys()))))

with open(OUT_TSV, "w", encoding="utf-8") as out:
    out.write("# KGRP_HITCOUNT_R9_R9M2b.tsv -- Per-group hit count statistics for R9 M0 and M2b (Step S-C-4)\n")
    out.write("# KGRP-071 line intervals:\n")
    if "KGRP-071" in m0_grps:
        out.write(f"#   M0 KGRP-071 lines: {m0_grps['KGRP-071']['start']}-{m0_grps['KGRP-071']['end']}\n")
    if "KGRP-071" in m2b_grps:
        out.write(f"#   M2b KGRP-071 lines: {m2b_grps['KGRP-071']['start']}-{m2b_grps['KGRP-071']['end']}\n")
    out.write("#\n")
    out.write("group_id\tfamily\tenv\tbp\tk_max\tm0_f3_hits\tm0_f4_hits\tm0_equal\tm2b_f3_hits\tm2b_f4_hits\tm2b_equal\tm0_lines\tm2b_lines\n")
    
    for gid in all_grp_ids:
        d0 = m0_grps.get(gid, {"family": "-", "env": "-", "bp": "-", "k_max": "-", "f3": -1, "f4": -1, "start": -1, "end": -1})
        d2 = m2b_grps.get(gid, {"family": "-", "env": "-", "bp": "-", "k_max": "-", "f3": -1, "f4": -1, "start": -1, "end": -1})
        
        fam = d0.get("family") or d2.get("family")
        env = d0.get("env") or d2.get("env")
        bp = d0.get("bp") or d2.get("bp")
        k_max = d0.get("k_max") or d2.get("k_max")
        
        m0_eq = "YES" if (d0["f3"] == d0["f4"] and d0["f3"] >= 0) else "NO"
        m2b_eq = "YES" if (d2["f3"] == d2["f4"] and d2["f3"] >= 0) else "NO"
        
        m0_lines = f"{d0['start']}-{d0['end']}" if d0['start'] > 0 else "-"
        m2b_lines = f"{d2['start']}-{d2['end']}" if d2['start'] > 0 else "-"
        
        out.write(f"{gid}\t{fam}\t{env}\t{bp}\t{k_max}\t{d0['f3']}\t{d0['f4']}\t{m0_eq}\t{d2['f3']}\t{d2['f4']}\t{m2b_eq}\t{m0_lines}\t{m2b_lines}\n")

print(f"KGRP hit count complete. Total groups: {len(all_grp_ids)}")
if "KGRP-071" in m0_grps and "KGRP-071" in m2b_grps:
    print(f"KGRP-071 M0 lines: {m0_grps['KGRP-071']['start']}-{m0_grps['KGRP-071']['end']}, hits F3={m0_grps['KGRP-071']['f3']}, F4={m0_grps['KGRP-071']['f4']}")
    print(f"KGRP-071 M2b lines: {m2b_grps['KGRP-071']['start']}-{m2b_grps['KGRP-071']['end']}, hits F3={m2b_grps['KGRP-071']['f3']}, F4={m2b_grps['KGRP-071']['f4']}")
print(f"Output written to {OUT_TSV}")
