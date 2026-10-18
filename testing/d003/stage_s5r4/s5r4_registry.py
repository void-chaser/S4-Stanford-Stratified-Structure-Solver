#!/usr/bin/env python3
# s5r4_registry.py -- build registries/s5r4/ and registries/s5r4/s5r3_completion/ and their SHA256SUMS.txt
# (task brief section 8). registries/s5r3/ and evidence/p05-s5r3/ are never written.
# usage: s5r4_registry.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]
import os, sys, shutil, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
ITEMS = ["GATE_S5R4_start.txt", "PREREG_REJUDGE_S5R4.tsv", "PREREG_REJUDGE_S5R4.tsv.sha256.txt",
         "REJUDGE_S5R4.tsv", "R3_GATE_RECHECK_S5R4.tsv", "READINESS_S5R4.tsv",
         "P05_ACCEPTANCE_MAP_S5R4.tsv", "POSCTRL_REJUDGE_S5R4.txt", "POSCTRL_GATE_S5R4.txt",
         "COPY_DIFF_S5R4.txt", "REGISTRY_APPLY_DIFF_S5R4.txt", "REPORT_CHECK_S5R4.txt",
         "FROZEN_SCRIPTS_S5R4.tsv", "REGISTRY_EXPECTED_S5R4.txt"]
R3_DELIVERED = ["GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
                "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
                "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
                "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
                "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
                "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
                "s5r2_supplement/D016_BUILD_S5R2.tsv"]
COMPLETION = [("REJUDGE_S5R3.tsv", "EV"), ("READINESS_S5R3.tsv", "EV3"),
              ("P05_ACCEPTANCE_MAP_S5R3.tsv", "EV3"), ("REGISTRY_APPLY_DIFF_S5R3.txt", "EV3"),
              ("REPORT_CHECK_S5R3.txt", "EV3"), ("COPY_DIFF_S5R3.txt", "EV3"),
              ("ERRATA_S5_R3FINAL.txt", "R3FINAL")]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sums_map(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        d[" ".join(parts[1:])] = parts[0]
    return d


def write_sums(d, rels):
    rows = ["# SHA256SUMS.txt -- P05-S5 R4 registry (" + os.path.basename(d) + ")"]
    for rel in rels:
        rows.append("%s  %s" % (sha_f(os.path.join(d, rel)), rel))
    open(os.path.join(d, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(rows) + NL)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_registry.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    reg = os.path.join(P05, "registries/s5r4")
    comp = os.path.join(reg, "s5r3_completion")
    os.makedirs(comp, exist_ok=True)
    # ---- s5r4 registry items
    miss = []
    for rel in ITEMS:
        if rel == "REGISTRY_EXPECTED_S5R4.txt":
            continue      # generated in this directory below, not an evidence file
        src = os.path.join(EV, rel)
        if not os.path.isfile(src):
            miss.append(rel)
            continue
        shutil.copyfile(src, os.path.join(reg, rel))
    # ---- expected list (all items except the list itself, so it can hold each sha)
    exp = ["# REGISTRY_EXPECTED_S5R4.txt -- registry items expected in registries/s5r4/ with their sha256"]
    for rel in ITEMS:
        if rel == "REGISTRY_EXPECTED_S5R4.txt":
            continue
        p = os.path.join(reg, rel)
        exp.append(TAB.join([rel, sha_f(p) if os.path.isfile(p) else "MISSING"]))
    open(os.path.join(reg, "REGISTRY_EXPECTED_S5R4.txt"), "w", encoding="utf-8").write(NL.join(exp) + NL)
    write_sums(reg, ITEMS)
    # ---- s5r3_completion (7 items: REJUDGE from this round, 6 copied from the R3 evidence, ERRATA from the snapshot)
    for rel, kind in COMPLETION:
        if kind == "EV":
            src = os.path.join(EV, "REJUDGE_S5R4.tsv")
        elif kind == "R3FINAL":
            src = os.path.join(EV, "r3_final/ERRATA_S5_R3FINAL.txt")
        else:
            src = os.path.join(EV3, rel)
        if not os.path.isfile(src):
            miss.append(rel)
            continue
        shutil.copyfile(src, os.path.join(comp, rel))
    sums3 = sums_map(os.path.join(EV3, "SHA256SUMS.txt"))
    reg3 = os.path.join(P05, "registries/s5r3")
    readme = ["# registries/s5r4/s5r3_completion/ -- S5R3 deliverables completed in S5R4 (U380, ES5-12)",
              "",
              "S5R3 was supposed to register 26 deliverables; the S5R3 chain copy stopped at the missing",
              "REJUDGE_S5R3.tsv (HARD_STOP), so registries/s5r3/ only holds a 10-item SHA256SUMS.txt. The",
              "S5R3 directory and its SHA256SUMS.txt are historical and are NOT rewritten. This directory",
              "completes the 7 missing items:",
              "",
              "| # | item | source | note |",
              "|---|---|---|---|",
              "| 20 | REJUDGE_S5R3.tsv | this round: REJUDGE_S5R4.tsv (byte copy) | R3 rejudge crashed (ES5-9); the S5R4 formal independent re-judge output is the S5R3 re-judge deliverable |",
              "| 21 | READINESS_S5R3.tsv | evidence/p05-s5r3/ | recovered R3 readiness audit (GAP=2 recorded there) |",
              "| 22 | P05_ACCEPTANCE_MAP_S5R3.tsv | evidence/p05-s5r3/ | recovered R3 acceptance map |",
              "| 23 | REGISTRY_APPLY_DIFF_S5R3.txt | evidence/p05-s5r3/ | recovered R3 registry patch diff |",
              "| 24 | REPORT_CHECK_S5R3.txt | evidence/p05-s5r3/ | recovered R3 report self-check |",
              "| 25 | COPY_DIFF_S5R3.txt | evidence/p05-s5r3/ | recovered R3 harness copy diff |",
              "| 26 | ERRATA_S5_R3FINAL.txt | evidence/p05-s5r4/r3_final/ | byte copy of the S5R3-final ERRATA_S5.txt (8228 B, last entry ES5-8) taken before the S5R4 append |",
              "",
              "S5R3 26/26 coverage: the 19 items already in registries/s5r3/ (each sha256 verified against",
              "evidence/p05-s5r3/SHA256SUMS.txt) plus these 7 items. p05-s5r3/ and registries/s5r3/ are unchanged",
              "(sha256 of their SHA256SUMS.txt files are recorded by the S5R4 start gate).",
              "",
              "## 26/26 mapping",
              "",
              "| S5R3 # | item | where |",
              "|---|---|---|"]
    where19 = ["GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
               "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
               "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
               "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
               "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
               "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
               "s5r2_supplement/D016_BUILD_S5R2.tsv"]
    for i, rel in enumerate(where19, 1):
        readme.append("| %d | %s | registries/s5r3/%s |" % (i, rel, rel))
    for i, (rel, kind) in enumerate(COMPLETION, 20):
        readme.append("| %d | %s | s5r3_completion/%s |" % (i, rel, rel))
    readme += ["", "Coverage=26/26 (19 already registered + 7 completed here).", ""]
    open(os.path.join(comp, "README.md"), "w", encoding="utf-8").write(NL.join(readme) + NL)
    write_sums(comp, [rel for (rel, _k) in COMPLETION] + ["README.md"])
    # ---- verify the 19 existing items against the p05-s5r3 manifest
    supp = {}
    for line in open(os.path.join(EV3, "S5R2_SUPPLEMENT_COPY_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0].endswith((".tsv", ".txt")) and len(f) >= 3 and f[1] != "sha256_source":
            supp[f[0]] = f[2]
    bad19 = []
    for rel in R3_DELIVERED:
        p = os.path.join(reg3, rel)
        want = supp.get(os.path.basename(rel)) if rel.startswith("s5r2_supplement/") else sums3.get(rel)
        if not os.path.isfile(p) or want != sha_f(p):
            bad19.append(rel)
    print("REGISTRY items=%d completion=%d bad19=%d" % (len(ITEMS), len(COMPLETION), len(bad19)))
    if miss or bad19:
        print("HARD_STOP missing=%s bad19=%s" % (miss, bad19))
        return 1
    print("REGISTRY_EXPECTED rows=%d" % (len(exp) - 1))
    print("WROTE " + os.path.relpath(reg, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
