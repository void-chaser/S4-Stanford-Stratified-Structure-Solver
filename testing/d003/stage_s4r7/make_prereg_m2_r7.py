#!/usr/bin/env python3
"""P05-S4 R7 M2 pre-registration generator (new file).  Writes REGISTRY_S4_PRE_R7_M2.tsv; never runs a driver.

Sources (read only; sha256 recorded in the header):
  G1   registries/s4r3/RESULTS_R3.tsv                       F rows (149: 141 injection + 8 control; 22 INVALID plan points, E7-4)
  G2a  registries/s4r4/RESULTS_R4.tsv                       F rows (25: seam families A, B2, C, D, E)
  G2b  registries/s4r4/RESULTS_R4_PLANCALL_pass{1,2}.tsv    F rows (22 each)
  G2c  registries/s4r4/REGRESS_R4.tsv (F rows, 30)  + registries/s4r4/CONTROL_R4.tsv (F-tree controls, 3; E7-14)
  G3   registries/s4r5/RESULTS_R5_PLANM_pass{1,2}.tsv       F rows (36 each)
  G4   registries/s4r6/RESULTS_R6_TWICE_pass{1,2}.tsv       F rows (12 each)
Each measured F point gives two rows: tree F (R7 build) and tree F2 (R7 build), both with expected_class = the historical F class.
Controls: F-tree control rows (G2c) give expected_class = CONTROL_OK on F and F2 with the control rc recorded in the
  expected_rc column (see the layout below), so the dry-parse can read it from a dedicated column (no M1 column error).

Layout (fixed; the runner and the dry-parse read these names):
  point_id, group, tree, mode, NG, M, nth, route, request, expected_class, expected_rc, basis, status
The dry-parse (--dry-parse) checks that every row has these 13 fields, that expected_class is one of the five categories
(CRASH, SILENT_SWALLOW, REPORTED_FAILURE, INVALID, CONTROL_OK) or the recorded 'INVALID_NOT_REACHED', and that a control row
has a parseable expected_rc.  It reports the count of unparseable rows (must be 0 before hashing).

Usage: python3 -I -B make_prereg_m2_r7.py OUT.tsv            (generate; OUT must not exist)
       python3 -I -B make_prereg_m2_r7.py --dry-parse IN.tsv (read only; prints the unparseable count)
"""
import hashlib
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
CATS = {"CRASH", "SILENT_SWALLOW", "REPORTED_FAILURE", "INVALID", "CONTROL_OK", "INVALID_NOT_REACHED"}
FIELDS = ["point_id", "group", "tree", "mode", "NG", "M", "nth", "route", "request", "inj_call", "expected_class", "expected_rc", "basis", "status"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path):
    header, rows = None, []
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


def sources():
    return {
        "G1_RESULTS_R3": os.path.join(REG, "s4r3", "RESULTS_R3.tsv"),
        "G2a_RESULTS_R4": os.path.join(REG, "s4r4", "RESULTS_R4.tsv"),
        "G2b_PLANCALL_pass1": os.path.join(REG, "s4r4", "RESULTS_R4_PLANCALL_pass1.tsv"),
        "G2b_PLANCALL_pass2": os.path.join(REG, "s4r4", "RESULTS_R4_PLANCALL_pass2.tsv"),
        "G2c_REGRESS_R4": os.path.join(REG, "s4r4", "REGRESS_R4.tsv"),
        "G2c_CONTROL_R4": os.path.join(REG, "s4r4", "CONTROL_R4.tsv"),
        "G3_PLANM_pass1": os.path.join(REG, "s4r5", "RESULTS_R5_PLANM_pass1.tsv"),
        "G3_PLANM_pass2": os.path.join(REG, "s4r5", "RESULTS_R5_PLANM_pass2.tsv"),
        "G4_TWICE_pass1": os.path.join(REG, "s4r6", "RESULTS_R6_TWICE_pass1.tsv"),
        "G4_TWICE_pass2": os.path.join(REG, "s4r6", "RESULTS_R6_TWICE_pass2.tsv"),
    }


def dry_parse(path):
    """Return (rows, unparseable) for a generated pre-registration file (read only)."""
    rows = table(path)
    bad = []
    for r in rows:
        if set(FIELDS) - set(r.keys()):
            bad.append((r.get("point_id", "?"), "missing field"))
            continue
        if r["expected_class"] not in CATS:
            bad.append((r["point_id"], "expected_class not a category: %r" % r["expected_class"]))
        if r["group"] == "control" and not re.match(r"^rc_first=-?\d+,rc_retry=-?\d+,run_rc=-?\d+$", r["expected_rc"] or ""):
            bad.append((r["point_id"], "control expected_rc not parseable: %r" % r["expected_rc"]))
    return rows, bad


def main(argv):
    if len(argv) == 3 and argv[1] == "--dry-parse":
        rows, bad = dry_parse(argv[2])
        print("rows=%d unparseable=%d" % (len(rows), len(bad)))
        for pid, why in bad[:50]:
            print("UNPARSEABLE", pid, why)
        return 0 if not bad else 1
    if len(argv) != 2:
        raise SystemExit("usage: make_prereg_m2_r7.py OUT.tsv | --dry-parse IN.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    src = sources()
    for k, p in src.items():
        if not os.path.isfile(p):
            raise SystemExit("missing source %s: %s" % (k, p))
    sha = {k: sha256_file(p) for k, p in src.items()}
    rows = []

    def add_point(group, pid, mode, ng, m, nth, route, request, inj_call, hist, basis):
        # inj_call is carried from the SOURCE row (not derived from route: in the sources inj_call does not track route)
        for tree in ("F", "F2"):
            rows.append([pid + "-" + tree, group, tree, mode, ng, m, nth, route, request, inj_call, hist, "-", basis,
                         "INFLUENCED"])

    # G1: R3 F rows (149).  INVALID historical points are carried as INVALID (E7-4); controls as CONTROL_OK.
    for d in table(src["G1_RESULTS_R3"]):
        if d["tree"] != "F":
            continue
        if d["category"] == "control":
            # G1 controls: 14-field layout (inj_call "-"); G1 is NOT run in this round (no request in source, E7-17)
            rows.append([d["point_id"] + "-F", "G1", "F", d["mode"], "-", "-", d["nth"], d["category"], "none", "-",
                         "CONTROL_OK", "rc=0", "G1 control; historical F CONTROL_OK", "INFLUENCED"])
            rows.append([d["point_id"] + "-F2", "G1", "F2", d["mode"], "-", "-", d["nth"], d["category"], "none", "-",
                         "CONTROL_OK", "rc=0", "G1 control copied from F (F2 = F expectation)", "INFLUENCED"])
            continue
        hist = d["expected_class"]
        if d["observed_class"] == "INVALID":
            hist = "INVALID_NOT_REACHED"
        add_point("G1", d["point_id"], d["mode"], "-", "-", d["nth"], d["category"], "-", "-", hist,
                  "G1 historical F class from RESULTS_R3 (E7-4); not run (E7-17)")

    # G2a: R4 seam F rows (25)
    for d in table(src["G2a_RESULTS_R4"]):
        if d["tree"] != "F":
            continue
        add_point("G2a", d["point_id"], d["mode"], "-", "-", "-", d["family"], d["request"], "-", d["expected"],
                  "G2a seam family %s (R4 RESULTS_R4); F rows, F class copied; not run in M2 (seam path)" % d["family"])

    # G2b: R4 plancall F rows (22 each pass; pass1 point list is used, pass2 checked equal)
    p1 = {d["point_id"]: d for d in table(src["G2b_PLANCALL_pass1"]) if d["tree"] == "F"}
    p2 = {d["point_id"]: d for d in table(src["G2b_PLANCALL_pass2"]) if d["tree"] == "F"}
    if set(p1) != set(p2):
        raise SystemExit("G2b pass1 and pass2 point sets differ")
    for pid in sorted(p1):
        if p1[pid]["expected"] != p2[pid]["expected"]:
            raise SystemExit("G2b expected differs between passes for %s" % pid)
        add_point("G2b", pid, p1[pid]["mode"], "-", p1[pid]["M"], p1[pid]["nth_K"], p1[pid]["route"], p1[pid]["request"],
                  p1[pid]["inj_call"], p1[pid]["expected"], "G2b plancall F class (R4 RESULTS_R4_PLANCALL pass1 = pass2)")

    # G2c: R4 regress F rows (30) and F-tree controls (3)
    for d in table(src["G2c_REGRESS_R4"]):
        if d["tree"] != "F":
            continue
        add_point("G2c", d["point_id"], d["mode"], "-", "-", d["nth"], d["category"], "-", "-", d["r4_observed"],
                  "G2c regress F class (REGRESS_R4 r4_observed)")
    # CONTROL_R4.tsv has NO header row (first column is the control name); it is read raw, not through table().
    ctrl = []
    with open(src["G2c_CONTROL_R4"], encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            f = raw.rstrip("\n").split("\t")
            if f[0].endswith("-F"):
                ctrl.append(f[0])
    if len(ctrl) != 3:
        raise SystemExit("G2c F-tree controls %d != 3" % len(ctrl))
    for name in ctrl:
        rows.append([name + "-ctrl-F", "G2c-control", "F", name.split("-")[0], "-", "-", "-", "control", "none", "-", "CONTROL_OK",
                     "rc=0", "G2c F-tree control (CONTROL_R4, E7-14); observed CONTROL_OK in R4", "INFLUENCED"])
        rows.append([name + "-ctrl-F2", "G2c-control", "F2", name.split("-")[0], "-", "-", "-", "control", "none", "-", "CONTROL_OK",
                     "rc=0", "G2c F-tree control run on F2 (expected as F)", "INFLUENCED"])

    # G3: R5 PLANM F rows (36)
    p1 = {d["point_id"]: d for d in table(src["G3_PLANM_pass1"]) if d["tree"] == "F"}
    p2 = {d["point_id"]: d for d in table(src["G3_PLANM_pass2"]) if d["tree"] == "F"}
    if set(p1) != set(p2):
        raise SystemExit("G3 pass point sets differ")
    for pid in sorted(p1):
        if p1[pid]["expected"] != p2[pid]["expected"]:
            raise SystemExit("G3 expected differs between passes for %s" % pid)
        add_point("G3", pid, p1[pid]["mode"], "-", p1[pid]["M"], p1[pid]["nth_K"], p1[pid]["route"], p1[pid]["request"],
                  p1[pid]["inj_call"], p1[pid]["expected"], "G3 R5 M=2 F class (RESULTS_R5_PLANM pass1 = pass2)")

    # G4: R6 TWICE F rows (12)
    p1 = {d["point_id"]: d for d in table(src["G4_TWICE_pass1"]) if d["tree"] == "F"}
    p2 = {d["point_id"]: d for d in table(src["G4_TWICE_pass2"]) if d["tree"] == "F"}
    if set(p1) != set(p2):
        raise SystemExit("G4 pass point sets differ")
    for pid in sorted(p1):
        if p1[pid]["expected"] != p2[pid]["expected"]:
            raise SystemExit("G4 expected differs between passes for %s" % pid)
        add_point("G4", pid, p1[pid]["mode"], "-", p1[pid]["M"], p1[pid]["nth_K"], p1[pid]["route"], p1[pid]["request"],
                  p1[pid]["inj_call"], p1[pid]["expected"], "G4 R6 TWICE F class (RESULTS_R6_TWICE pass1 = pass2)")

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R7_M2.tsv -- P05-S4 R7 M2 pre-registration (generated by make_prereg_m2_r7.py; CONT2 section 4).\n")
        fh.write("# Status: INFLUENCED (the F classes of G1-G4 were measured before this file).\n")
        for k in src:
            fh.write("# source %s sha256=%s\n" % (k, sha[k]))
        fh.write("# Expectations are NOT changed after the runs.  Any change is a new ERRATA file.\n")
        fh.write("\t".join(FIELDS) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print("rows=%d -> %s" % (len(rows), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
