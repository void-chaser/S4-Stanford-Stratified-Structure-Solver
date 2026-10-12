#!/usr/bin/env python3
"""P05-S4 R7 cont3 section 2.2: supplementary pre-registration ADD table for G1, G2a, G2c, G2c-control (new file).

It adds the request-level columns that v2 (REGISTRY_S4_PRE_R7_M2.tsv, sha e4dd2c87...) does not carry.  v2 is NOT changed.
Every row of ADD must match a v2 row on point_id, tree and expected_class, character for character.  Any mismatch makes
the script exit non-zero and write NOTHING (the check is done before the output file is opened).

New columns: request, nth, route, twice_env, inj_call, ng, stack, inj_call_source.
  G1 (run_r3_sweep.py:32 and :107-120):  request = {malloc: s4malloc, plan: plan, exec: exec}[category];
      nth from the point id; route = point id field 2; twice_env = slab for twice, "-" for once; ng = 9; stack = pattern;
      inj_call = FIELDCALL_MAP[(route, mode, category, nth)].  Controls (category control): request "none", inj_call "-".
  G2a (RESULTS_R4 request column): request = source request; inj_call from the source "expected"-side rule is NOT
      re-derived here: the seam rows carry their own request, and inj_call is recorded as "-" with the source note
      (run_r4_matrix.py M.inj_call_of is the R4 rule; its source is named in the header).  ng = "-" (seam rows use the
      R4 matrix settings, see RESULTS_R4 header); stack = pattern.
  G2c (REGRESS_R4 inj_call column, run_r4_regress.py): request = R3 INJECT[category]; inj_call = REGRESS_R4 inj_call column;
      twice_env "-" (REGRESS_R4 rows are once-route points, the category/route is in point_id).
  G2c-control: request "none", inj_call "-".

Usage: python3 -I -B make_prereg_m2_add_r7.py OUT.tsv   (OUT must not exist; written only if every check passes)
"""
import hashlib
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
V2 = os.path.join(EV, "REGISTRY_S4_PRE_R7_M2.tsv")
V2_SHA = "e4dd2c8779887f57044253a7e1674923a0fb34a0c6fcd437459572ae8d92ba2c"
INJECT = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}
ADD_FIELDS = ["point_id", "tree", "group", "expected_class", "request", "nth", "route", "twice_env",
              "inj_call", "ng", "stack", "inj_call_source"]


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


def load_fcmap(path):
    fc = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#") or line.startswith("route\t"):
                continue
            route, mode, cat, nth, call = line.split("\t")
            fc[(route, mode, cat, int(nth))] = call
    return fc


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: make_prereg_m2_add_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    if sha256_file(V2) != V2_SHA:
        raise SystemExit("REFUSED: v2 sha256 differs from e4dd2c87...")
    v2 = {}
    for r in table(V2):
        if r["group"].endswith("control") or r["group"] in ("G1", "G2a", "G2c"):
            v2[(r["point_id"], r["tree"])] = r

    fc = load_fcmap(os.path.join(REG, "s4r3", "FIELDCALL_MAP.tsv"))
    add = []

    # G1: RESULTS_R3 F rows (141 injections + 8 controls)
    for d in table(os.path.join(REG, "s4r3", "RESULTS_R3.tsv")):
        if d["tree"] != "F":
            continue
        pid, cat = d["point_id"], d["category"]
        route = pid.split("-")[1]
        if cat == "control":
            for tree in ("F", "F2"):
                add.append([pid + "-" + tree, tree, "G1", "CONTROL_OK", "none", "-", route, "-", "-", "-", "pattern",
                            "control (no injection)"])
            continue
        nth = d["nth"]
        call = fc.get((route, d["mode"], cat, int(nth)))
        if call is None:
            raise SystemExit("REFUSED: G1 %s not in FIELDCALL_MAP" % pid)
        twice = "slab" if route == "twice" else "-"
        # expected_class is taken from v2, NOT from RESULTS_R3: for the 22 INVALID points v2 holds INVALID_NOT_REACHED (E7-4),
        # while RESULTS_R3.expected_class is REPORTED_FAILURE.  ADD must agree with v2.
        v2row = v2.get((pid + "-F", "F"))
        if v2row is None:
            raise SystemExit("REFUSED: G1 %s has no v2 row" % pid)
        for tree in ("F", "F2"):
            add.append([pid + "-" + tree, tree, "G1", v2[(pid + "-" + tree, tree)]["expected_class"], INJECT[cat], nth,
                        route, twice, call, "9", "pattern", "FIELDCALL_MAP (run_r3_sweep.py:110-112)"])

    # G2a: RESULTS_R4 F rows (25 seam points)
    for d in table(os.path.join(REG, "s4r4", "RESULTS_R4.tsv")):
        if d["tree"] != "F":
            continue
        pid = d["point_id"]
        # inj_call by the historical rule matrix_r2.inj_call_of(row) = 2 if case startswith "t4/" else 1 (run_r4_matrix.py:141).
        # The G2a seam ids carry the prefix R4- (no t4/), so inj_call is 1.  Checked in cont3: 0 of 25 F ids start with t4/.
        if pid.startswith("t4/") or "t4/" in pid:
            raise SystemExit("REFUSED: G2a id %s carries a t4/ prefix; inj_call rule would be 2" % pid)
        for tree in ("F", "F2"):
            add.append([pid + "-" + tree, tree, "G2a", d["expected"], d["request"], "-", "once", "-", "1", "9", "pattern",
                        "matrix_r2.inj_call_of rule: no t4/ prefix -> 1 (run_r4_matrix.py:141)"])

    # G2c: REGRESS_R4 F rows (30) and F-tree controls (3)
    for d in table(os.path.join(REG, "s4r4", "REGRESS_R4.tsv")):
        if d["tree"] != "F":
            continue
        pid, cat = d["point_id"], d["category"]
        req = INJECT[cat]
        for tree in ("F", "F2"):
            add.append([pid + "-" + tree, tree, "G2c", d["r4_observed"], req, d["nth"], "once", "-", d["inj_call"], "9",
                        "pattern", "REGRESS_R4 inj_call column; request = R3 INJECT[category] (run_r4_regress.py)"])
    with open(os.path.join(REG, "s4r4", "CONTROL_R4.tsv"), encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            name = raw.split("\t")[0]
            if not name.endswith("-F"):
                continue
            for tree in ("F", "F2"):
                add.append([name + "-ctrl-" + tree, tree, "G2c-control", "CONTROL_OK", "none", "-", "-", "-", "-", "-",
                            "pattern", "CONTROL_R4 F-tree control"])

    # consistency with v2: point_id, tree and expected_class must match v2 character for character
    bad = []
    for row in add:
        pid, tree, grp, exp = row[0], row[1], row[2], row[3]
        key_pid = pid
        # v2 point ids for G1/G2a/G2c are the source id + "-F" or "-F2" (v2 built them that way); controls use "-ctrl-"
        match = None
        for (vpid, vtree), vr in v2.items():
            if vtree == tree and vpid == key_pid:
                match = vr
                break
        if match is None:
            # controls and some point ids are keyed differently in v2; record and refuse rather than guess
            bad.append("no v2 row for %s (tree %s)" % (pid, tree))
            continue
        if match["expected_class"] != exp:
            bad.append("expected_class differs for %s: v2=%s add=%s" % (pid, match["expected_class"], exp))
    if bad:
        for b in bad[:20]:
            print("MISMATCH", b)
        print("REFUSED: %d ADD rows do not match v2; nothing written" % len(bad))
        return 1

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R7_M2_ADD.tsv -- P05-S4 R7 cont3 supplementary request columns for G1, G2a, G2c, G2c-control.\n")
        fh.write("# Every row matches a v2 row on point_id, tree and expected_class (checked before writing; v2 sha256 %s).\n" % V2_SHA)
        fh.write("# Request rules: G1 run_r3_sweep.py:32,107-120; G2c run_r4_regress.py (R3 INJECT); G2a RESULTS_R4 request column.\n")
        fh.write("\t".join(ADD_FIELDS) + "\n")
        for row in add:
            fh.write("\t".join(str(x) for x in row) + "\n")
    print("rows=%d -> %s" % (len(add), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
