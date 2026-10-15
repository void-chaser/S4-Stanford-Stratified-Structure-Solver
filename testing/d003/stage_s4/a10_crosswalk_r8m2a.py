#!/usr/bin/env python3
# a10_crosswalk_r8m2a.py -- P05-S4 R8 M2a section 4.1: A-10 control crosswalk against M0.
# Read-only on registries; writes only under EV (argument 1 = output directory under EV, or default).
# Inputs: registries/s3r4c3/REGISTRY_S3R4C3_A_CTRL.tsv (6 rows), registries/s4r8/EXPECT_R8_NOINJECT.txt,
#         registries/s4r8/RESULTS_R8_NOINJECT_run1.tsv (sha256 pinned below).
# Output: $EV/A10_CONTROL_CROSSWALK_R8_M2a.tsv
# Status per combo: COVERED_BY_M0 (F3 rc1 = rc2 = 0 and matches expectation), MISSING_IN_M0, M0_DIFFERS.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
CTRL = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3", "REGISTRY_S3R4C3_A_CTRL.tsv")
EXPECT = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "EXPECT_R8_NOINJECT.txt")
RESULTS = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "RESULTS_R8_NOINJECT_run1.tsv")
RESULTS_SHA = "8d8effde9012b02da5c09c24e8f7ac973463fac24cb248f9694d95868cea027f"
OUT = os.path.join(EV, "A10_CONTROL_CROSSWALK_R8_M2a_R2.tsv")
# R2 (this file): the first run wrote A10_CONTROL_CROSSWALK_R8_M2a.tsv and was invalid (kept, U17):
# the call comparison was looked up by tree (M0 stores it under F2-vs-F3), so every combo read M0_DIFFERS,
# and each CTRL row was emitted twice (once per tree in the outer loop and again per tree row of the register).


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def main():
    if os.path.exists(OUT):
        print("a10_crosswalk_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    got = sha256_file(RESULTS)
    if got != RESULTS_SHA:
        print("a10_crosswalk_r8m2a: REFUSED M0 results sha256 %s != %s" % (got, RESULTS_SHA))
        return 2

    ctrl = read_rows(CTRL)
    # M0 expectation: combo-level rows from EXPECT_R8_NOINJECT.txt (mode, NG, expected rc1, rc2, call compare)
    exp = {}
    with open(EXPECT, encoding="utf-8") as fh:
        for l in fh:
            if not l.strip() or l.startswith("#") or l.startswith("mode\t"):
                continue
            p = l.rstrip("\n").split("\t")
            if len(p) >= 6:
                exp[(p[0], p[1], p[2])] = (p[3], p[4], p[5])
    # M0 observation.  Run rows: (mode, NG, lattice, tree in F2/F3) carry rc_first/rc_retry.
    # Call rows: (mode, NG, lattice, tree = "F2-vs-F3") carry call1/call2/call3 comparisons.
    obs = {}
    with open(RESULTS, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for l in fh:
            p = dict(zip(head, l.rstrip("\n").split("\t")))
            if p["file"].startswith("run_rc="):
                obs.setdefault((p["mode"], p["NG"], p["lattice"], p["tree"]), {})["rc"] = (p["rc_first"], p["rc_retry"])
            else:
                obs.setdefault((p["mode"], p["NG"], p["lattice"], "F2-vs-F3"), {})[p["file"]] = p["cmp"]

    rows = []
    rows.append(["combo", "mode", "NG", "tree", "m0_rc1", "m0_rc2", "m0_call1", "m0_call2", "m0_call3",
                 "exp_rc1", "exp_rc2", "exp_call_compare", "status", "ctrl_status_register"])
    fails = 0
    # One line per control combo (CTRL rows of the register) and per tree (F2, F3).
    seen = []
    for r in ctrl:
        if r["point_id"] != "CTRL" or r["combo"] in seen:
            continue
        seen.append(r["combo"])
        mode = r["mode"]
        ng = r["NG"]
        e = exp.get((mode, ng, "square"))
        for tree in ("F2", "F3"):
            o = obs.get((mode, ng, "square", tree))
            calls_o = obs.get((mode, ng, "square", "F2-vs-F3"), {})
            if o is None or "rc" not in o or e is None:
                status = "MISSING_IN_M0"
                m0_rc = ("-", "-")
                calls = ("-", "-", "-")
            else:
                m0_rc = o["rc"]
                calls = (calls_o.get("call1.txt", "-"), calls_o.get("call2.txt", "-"), calls_o.get("call3.txt", "-"))
                rc_ok = m0_rc[0] == e[0] and m0_rc[1] == e[1] and m0_rc[0] == "0" and m0_rc[1] == "0"
                call_ok = all(c == "IDENTICAL" for c in calls) and e[2] == "IDENTICAL"
                status = "COVERED_BY_M0" if (rc_ok and call_ok) else "M0_DIFFERS"
            if status != "COVERED_BY_M0":
                fails += 1
            rows.append([r["combo"], mode, ng, tree, m0_rc[0], m0_rc[1], calls[0], calls[1], calls[2],
                         (e[0] if e else "-"), (e[1] if e else "-"), (e[2] if e else "-"), status, r["status"]])

    os.makedirs(EV, exist_ok=True)
    with open(OUT, "x", encoding="utf-8") as fh:
        for row in rows:
            fh.write("\t".join(row) + "\n")
    print("A10_CROSSWALK rows=%d not_covered=%d out=%s" % (len(rows) - 1, fails, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
