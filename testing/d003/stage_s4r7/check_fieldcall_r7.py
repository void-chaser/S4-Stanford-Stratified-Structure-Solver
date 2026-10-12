#!/usr/bin/env python3
"""P05-S4 R7 cont3 U50 evidence: check the R3 request mapping against FIELDCALL_MAP (new file; read only).

For every F row of RESULTS_R3 that is an injection (category != control), this script:
  1. builds the key (route, mode, category, nth) exactly as run_r3_sweep.py does (route = point_id field 2;
     nth = the NTH column; category = the category column);
  2. looks the key up in registries/s4r3/FIELDCALL_MAP.tsv (field_call column);
  3. compares the found value with the RESULTS_R3 inj_call column.
It reports: number of injection F rows, number missing from the map, number whose map value differs from inj_call.
Request mapping (run_r3_sweep.py:32): {malloc: s4malloc, plan: plan, exec: exec}.
Case prefix (run_r3_sweep.py:118): twice route -> "t4/" (driver S4FMM_TWICE=slab); once -> "r3/".

Usage (through safe_run; output must not exist):
  python3 -I -B testing/d003/stage_s4r7/check_fieldcall_r7.py EVDIR/CHECK_FIELDCALL_R7.tsv
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r3")
RESULTS = os.path.join(REG, "RESULTS_R3.tsv")
FCMAP = os.path.join(REG, "FIELDCALL_MAP.tsv")
INJECT = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}


def table(path, cols_header_prefix=None):
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
        raise SystemExit("usage: check_fieldcall_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    fc = load_fcmap(FCMAP)
    rows = [r for r in table(RESULTS) if r["tree"] == "F" and r["category"] != "control"]
    lines = ["# CHECK_FIELDCALL_R7.tsv -- P05-S4 R7 cont3 U50 evidence (read only).",
             "# Key = (route, mode, category, nth) as run_r3_sweep.py:107-112; value = FIELDCALL_MAP.field_call; compared with RESULTS_R3.inj_call.",
             "# Request = %s (run_r3_sweep.py:32).  Case prefix: t4/ for twice (S4FMM_TWICE=slab), r3/ for once." % INJECT,
             "point_id\troute\tmode\tcategory\tnth\trequest\ttwice_env\tfieldcall_map\tRESULTS_R3_inj_call\tstatus"]
    missing = differ = 0
    for r in rows:
        pid = r["point_id"]
        route = pid.split("-")[1]
        key = (route, r["mode"], r["category"], int(r["nth"]))
        mapped = fc.get(key)
        if mapped is None:
            missing += 1
            status = "MISSING"
        elif mapped != r["inj_call"]:
            differ += 1
            status = "DIFFER"
        else:
            status = "OK"
        lines.append("\t".join([pid, route, r["mode"], r["category"], r["nth"], INJECT[r["category"]],
                                "slab" if route == "twice" else "-", mapped if mapped is not None else "-",
                                r["inj_call"], status]))
    lines.append("# injection F rows checked: %d; missing from map: %d; map value differs from inj_call: %d" % (len(rows), missing, differ))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("rows=%d missing=%d differ=%d -> %s" % (len(rows), missing, differ, out))
    return 0 if (missing == 0 and differ == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
