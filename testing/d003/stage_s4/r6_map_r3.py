#!/usr/bin/env python3
# r6_map_r3.py -- P05-S4 R6-2a (new file).  Builds the request map for the R3 points that gave REPORTED_FAILURE on tree F.
# It reads only R3 results (RESULTS_R3.tsv) and the R3 field-call map (FIELDCALL_MAP.tsv); it writes one TSV.
# The request form is the R3 sweep form: INJECT[category] (run_r3_sweep.py), NTH from the point, inj_call from
# FIELDCALL_MAP (route, mode, category, nth), and S4FMM_TWICE=slab for the twice route (matrix_r2.build_env, case t4/).
#
#   python3 -I -B testing/d003/stage_s4/r6_map_r3.py RESULTS_R3 FIELDCALL_MAP OUT
#
# Output columns: point_id, tree, route, mode, category, nth, request, inj_call, twice, expected_class, observed_r3, match_r3
# Scope: F only.  Points that are not REPORTED_FAILURE on F (INVALID, CONTROL_OK) are not written.
import os
import sys

INJECT = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}
HEADER = ["point_id", "tree", "route", "mode", "category", "nth", "request", "inj_call", "twice",
          "expected_class", "observed_r3", "match_r3"]


def route_of(pid):
    # point ids are M-<route>-<mode>-<category>-<NTH>; the route is the second field (run_r3_sweep.py)
    return pid.split("-")[1]


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6_map_r3.py RESULTS_R3 FIELDCALL_MAP OUT")
    results, fcmap, out = argv[1:4]
    fc = {}
    with open(fcmap, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("route\t"):
                continue
            route, mode, cat, nth, call = line.rstrip("\n").split("\t")
            fc[(route, mode, cat, int(nth))] = int(call)
    rows = []
    with open(results, encoding="utf-8") as fh:
        header = None
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            if d["tree"] != "F" or d["observed_class"] != "REPORTED_FAILURE":
                continue
            pid = d["point_id"]
            route = route_of(pid)
            mode = d["mode"]
            cat = d["category"]
            nth = int(d["nth"])
            if cat not in INJECT:
                raise SystemExit("REFUSED: unknown category %r for %s" % (cat, pid))
            key = (route, mode, cat, nth)
            if key not in fc:
                raise SystemExit("REFUSED: no field call for %r" % (key,))
            inj_call = fc[key]
            # cross-check: the R3 inj_call column must agree with FIELDCALL_MAP
            if d.get("inj_call") not in (None, "", str(inj_call)):
                raise SystemExit("REFUSED: inj_call disagrees for %s: map %d vs results %s" % (pid, inj_call, d.get("inj_call")))
            request = INJECT[cat]  # the mode only; NTH is set separately as S4FMM_NTH (run_r3_sweep.py)
            rows.append([pid, "F", route, mode, cat, str(nth), request,
                         str(inj_call), "slab" if route == "twice" else "-",
                         d["expected_class"], d["observed_class"], d["match"]])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# MAP_R6_R3.tsv -- P05-S4 R6-2a: request map for the R3 REPORTED_FAILURE points on tree F (119 expected).\n")
        fh.write("# request = INJECT[category] (run_r3_sweep.py); NTH is column nth; inj_call from FIELDCALL_MAP; twice = slab for route twice.\n")
        fh.write("\t".join(HEADER) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
