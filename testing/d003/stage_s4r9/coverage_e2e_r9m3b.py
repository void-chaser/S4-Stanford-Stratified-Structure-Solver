#!/usr/bin/env python3
# coverage_e2e_r9m3b.py -- COVERAGE_E2E_R9M3B.tsv: the seam-only families and the existing M1/M2 coverage rows
# that reach them (U340). Every point id and verdict is read from the committed M1 registry tables. New file (r9m3b).
import os

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
REG1 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1")
REG1R3 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R3")
TAB = chr(9)
NL = chr(10)
OUT = os.path.join(EV, "COVERAGE_E2E_R9M3B.tsv")
FAMILIES = [
    ("LinearSolve A/B/B2/B2-buf", "linearsolve", "seam-only hook S4_TEST_LINEARSOLVE_AFTER (testing/d003/seam); no public-API entry"),
    ("FMM return-code family E (fmmret/fmmbuf)", "fmmret", "seam-only hook inserted into Simulation_ComputeLayerModes; no public-API entry"),
    ("allocation seam family C (alloc: 21..25)", "alloc:", "same translation unit as S4_malloc, --wrap cannot reach it; needs the seam patch"),
    ("kottke_alloc:31", "kottke_alloc:31", "seam-only S4_TEST_KOTTKE_HOOK; no public-API entry"),
]


def read_tsv(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def main():
    pre = read_tsv(os.path.join(REG1, "PREREG_M1_F4_R9M1.tsv"))
    ver = {}
    for p in (os.path.join(REG1R3, "VERDICT_M1_F4_R9M1R3.tsv"), os.path.join(REG1, "VERDICT_M1_F4_R9M1.tsv")):
        if os.path.isfile(p):
            for r in read_tsv(p):
                ver.setdefault(r.get("point_id"), r.get("verdict"))
    out = []
    for fam, token, reason in FAMILIES:
        hits = [r for r in pre if token in (r.get("env") or "")]
        refs = []
        for r in hits[:8]:
            pid = r.get("point_id")
            refs.append("%s=%s" % (pid, ver.get(pid, "NOT_IN_VERDICT_TABLE")))
        out.append((fam, "SEAM_ONLY", reason, str(len(hits)),
                    "checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv; checkpoints/p05/registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv",
                    "; ".join(refs)))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# COVERAGE_E2E_R9M3B.tsv -- families that can only be reached through a seam patch (U340)" + NL)
        fh.write("# reachable families with E2E points (CF/FFT/KT/JONES/NV/VL/EXP) are listed in E2E_API_SURVEY_R9M3B.md section 3 and in PREREG_E2E_R9M3B.tsv" + NL)
        fh.write(TAB.join(["family", "e2e_status", "reason", "m1m2_rows", "coverage_source", "coverage_rows_point_id=verdict"]) + NL)
        for r in out:
            fh.write(TAB.join(r) + NL)
    for r in out:
        print(TAB.join(r[:4]))
    print("WROTE " + OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
