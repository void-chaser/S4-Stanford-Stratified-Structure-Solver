#!/usr/bin/env python3
# Check if any M1 table has matching env (as dict)
import os, csv

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

def parse_env(env_str):
    if not env_str:
        return {}
    parts = env_str.strip().split(";")
    d = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            d[k.strip()] = v.strip()
    return d

m2_prereg = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "PREREG_M2_EFFECTIVE_R8_M2a3.tsv")
m2_g = []
with open(m2_prereg, encoding="utf-8") as fh:
    for row in csv.DictReader(fh, delimiter="\t"):
        if row["point_id"].startswith("M2-03-G"):
            m2_g.append((row["point_id"], parse_env(row["env"])))

# Scan all tsv files in registries/s4r8/M1b and M1c and registries/s4r7
m1_files = [
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b1", "PLAN_M1B_R8_M1b1.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b1", "RESULTS_M1B_R8_M1b1.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2", "PREREG_M1C_FACTS_R8_M1c2.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3", "M1C_F3_STATE_R6c_pass1.tsv"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3", "M1C_F3_STATE_SEAM_R6c_pass1.tsv"),
]

for pid, env_d in m2_g:
    found = False
    for fpath in m1_files:
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding="utf-8") as fh:
            for lno, line in enumerate(fh, start=1):
                # quick check
                if env_d.get("FMM_MODE") in line and env_d.get("S4FMM_NG") in line:
                    parts = line.strip().split("\t")
                    for p in parts:
                        if "=" in p and parse_env(p) == env_d:
                            print(f"MATCH: {pid} in {os.path.basename(fpath)}:{lno}")
                            found = True
                            break
                if found:
                    break
        if found:
            break
    if not found:
        print(f"NO_REF: {pid} (NG={env_d.get('S4FMM_NG')}, mode={env_d.get('FMM_MODE')}, inject={env_d.get('S4FMM_INJECT')})")
