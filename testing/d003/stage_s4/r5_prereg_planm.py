#!/usr/bin/env python3
# r5_prereg_planm.py -- P05-S4 R5-3 step 2: write the pre-registration of the M>=2 plan points (before any run).
# New file.  Inputs (read only): R3 CALLSEQ.tsv (in-scope plan points: caller FMMGetEpsilon_*), FIELDCALL_MAP.tsv
# (inj_call), and the discovery counts PLAN_MALLOC_COUNT_R5.tsv (m(K)).
#
#   python3 -I -B testing/d003/stage_s4/r5_prereg_planm.py EVDIR_R3 MCOUNT_DIR OUT_TSV
#
# Rule: M runs over 2..m(K) for every in-scope plan point (route, mode, K).  Every observed m(K) is 2 (R5-3 step 1),
# so M = 2 only.  Expected class: F = REPORTED_FAILURE (the F tree must report a non-zero code).  B = UNKNOWN (R5-2
# explains the K=12 M=1 case of B only; no observation of B for M=2 exists).  status = INFLUENCED for both.
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

HEADER = ["point_id", "r1_id", "tree", "route", "mode", "nth_K", "M", "request", "inj_call", "expected_class", "basis", "status"]


def read_tsv(path):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r5_prereg_planm.py EVDIR_R3 MCOUNT_DIR OUT_TSV")
    evr3, mdir, out = argv[1], argv[2], argv[3]

    callseq = read_tsv(os.path.join(evr3, "CALLSEQ.tsv"))
    fcm = read_tsv(os.path.join(evr3, "FIELDCALL_MAP.tsv"))
    fc = {}
    for r in fcm:
        fc[(r["route"], r["mode"], r["category"], r["nth"])] = r["field_call"]

    # in-scope plan points: category plan, caller FMMGetEpsilon_*, tree F, rep 1 (CALLSEQ is identical for B and F)
    pts = []
    seen = set()
    for r in callseq:
        if r.get("category") != "plan" or r.get("tree") != "F" or r.get("rep") != "1":
            continue
        if not str(r.get("caller_function", "")).startswith("FMMGetEpsilon_"):
            continue
        key = (r["route"], r["mode"], r["nth"])
        if key in seen:
            continue
        seen.add(key)
        pts.append(key)
    if len(pts) != 36:
        raise SystemExit("REFUSED: expected 36 in-scope plan points, got %d" % len(pts))

    # m(K) must be >= 2 for the point to be M>=2 (checked against the discovery file)
    mtab = {}
    for name in os.listdir(mdir):
        if not (name.startswith("mcount-F-") and name.endswith("-p1.txt")):
            continue
        parts = name[len("mcount-F-"):-len("-p1.txt")].split("-")
        mode, route = parts[0], parts[1]
        with open(os.path.join(mdir, name), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"MCOUNT k=(\d+) m=(\d+)", line)
                if m:
                    mtab[(route, mode, m.group(1))] = int(m.group(2))

    rows = []
    for route, mode, nth in pts:
        mk = mtab.get((route, mode, nth))
        if mk is None or mk < 2:
            raise SystemExit("REFUSED: m(K)<2 or missing for %s %s K=%s" % (route, mode, nth))
        ic = fc.get((route, mode, "plan", nth))
        if ic not in ("1", "2"):
            raise SystemExit("REFUSED: no field_call for %s %s plan %s" % (route, mode, nth))
        for tree in ("B", "F"):
            pid = "M2-%s-%s-plan-%s-%s" % (route, mode, nth, tree)
            exp = "REPORTED_FAILURE" if tree == "F" else "UNKNOWN"
            basis = ("[F: rule] M=2 plan point, must report non-zero" if tree == "F"
                     else "[no observation of B for M=2; R5-2 explains only K=12 M=1 (plan NULL, no check)]")
            req = "plancall:%s:2" % nth
            rows.append([pid, "-", tree, route, mode, nth, "2", req, ic, exp, basis, "INFLUENCED"])

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R5_PLANM.tsv -- P05-S4 R5-3 pre-registration (M>=2 plan points, M=2).\n")
        fh.write("# Written BEFORE any R5-3 injection run.  36 in-scope plan points x {B,F} = %d rows.\n" % len(rows))
        fh.write("# Request form plancall:K:M (the R4 injector inject_r4_plan.cpp).  Expected class: F REPORTED_FAILURE, B UNKNOWN.\n")
        fh.write("\t".join(HEADER) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("rows=%d -> %s" % (len(rows), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
