#!/usr/bin/env python3
# r6b_prereg.py -- P05-S4 R6b-2 pre-registration generator (new file).
# Writes REGISTRY_S4_PRE_R6b_STATE.tsv: one row per point of MAP_R6b_ALL.tsv (tree F) that can be judged in R6b
# (R3 119 + R4PC 22 + R5M2 36 = 177 points), with the snapshot indices fixed by U13 (inj_call, not route).
# The 25 R4 seam points are written as UNJUDGED (see ERRATA_6b E6b-7); they are not in this table.
# The generator computes every value from the map and the rules; nothing is typed by hand.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6b_prereg.py MAP OUT_TSV
import os
import sys

# Snapshot indices by inj_call (U13).  inj_call must be 1 or 2; a once-route point with inj_call 2 is a STOP.
K_FAIL = {1: 1, 2: 3}
K_PRE = {1: 2, 2: 3}
K_RETRY = {1: 3, 2: 4}
RETRY_CALL = {1: 2, 2: 3}

INVARIANTS = {
    # invariant id -> short name; applicability is decided per point below
    "I1": "failed layer modes==NULL at k_fail",
    "I2": "other layers at k_fail: q hash, control installed, not re-entered (E6-8 option 1)",
    "I3": "field_cache subset of control at k_fail (PolBasis modes only; else N/A)",
    "I4": "request layer solved==0 at k_fail",
    "I5": "retry enters ComputeLayerModes only for modes==NULL layers at k_pre; each at most once; retry rc==0",
    "I6": "retry output byte-identical to control call of the same number",
}
POLBASIS_MODES = {"jones", "nv", "vl", "fftjones", "fftnv", "fftvl"}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: r6b_prereg.py MAP OUT_TSV")
    mp, out = argv[1], argv[2]
    header = None
    rows = []
    with open(mp, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            if d["source"] == "R4SEAM":
                continue  # UNJUDGED in R6b (ERRATA_6b E6b-7); written separately below
            rows.append(d)
    if len(rows) != 177:
        raise SystemExit("REFUSED: expected 177 judgeable points (R3 119 + R4PC 22 + R5M2 36), got %d" % len(rows))

    # counts for the header (U13 item 5): (route, inj_call)
    counts = {}
    for d in rows:
        key = (d["route"], d["inj_call"])
        counts[key] = counts.get(key, 0) + 1
    tw1 = counts.get(("twice", "1"), 0)
    if tw1 != 66:
        raise SystemExit("STOP (U13 item 5): twice & inj_call=1 is %d, expected 66" % tw1)
    for (route, ic), n in counts.items():
        if ic not in ("1", "2"):
            raise SystemExit("STOP (U13 item 1): inj_call %r for %s" % (ic, route))
        if route == "once" and ic == "2":
            raise SystemExit("STOP (U13 item 1): once-route point with inj_call 2")

    cols = ["point_id", "source", "tree", "route", "mode", "stack", "request", "NTH_or_K", "M", "inj_call", "twice",
            "k_fail", "k_preretry", "k_retry", "retry_call", "applicable_invariants", "expected", "status"]
    lines = []
    lines.append("# REGISTRY_S4_PRE_R6b_STATE.tsv -- P05-S4 R6b-2 pre-registration (S3-4b state judgement, 177 judgeable points, tree F).")
    lines.append("# Written BEFORE any R6b state run.  The map is MAP_R6b_ALL.tsv (202 points; 25 seam points are UNJUDGED, see ERRATA_6b E6b-7).")
    lines.append("# Snapshot indices by inj_call (U13): inj_call 1 -> k_fail 1, k_preretry 2, k_retry 3, retry_call 2;")
    lines.append("#                                    inj_call 2 -> k_fail 3, k_preretry 3, k_retry 4, retry_call 3.")
    lines.append("# Invariants (ERRATA_6b, U8 option 1 for I2; I7 DEFERRED U9):")
    for k, v in INVARIANTS.items():
        lines.append("#   %s: %s" % (k, v))
    lines.append("# Expected (status INFLUENCED): every applicable invariant HOLD.  Basis: the S3/S3R/S3R2 repair intent, the R6 single")
    lines.append("# point probe (closed1d malloc NTH 1 once: I1 holds at k_fail), and ruling E6-8/U8.  Status is NOT BLIND.")
    lines.append("# Counts (route, inj_call) over the 177 judgeable points:")
    for (route, ic) in sorted(counts):
        lines.append("#   %s inj_call=%s : %d" % (route, ic, counts[(route, ic)]))
    lines.append("# Stack (driver): pattern both 4 3 ; NG 9 ; twice points set S4FMM_TWICE=slab explicitly.")
    lines.append("\t".join(cols))
    n_out = 0
    for d in rows:
        route = d["route"]
        mode = d["mode"]
        ic = int(d["inj_call"])
        kf, kp, kr, rcall = K_FAIL[ic], K_PRE[ic], K_RETRY[ic], RETRY_CALL[ic]
        if d["source"] == "R3":
            nk = "NTH=%s" % d["nth"]
            mm = "-"
        else:
            nk = "K=%s" % d["nth_K"]
            mm = "M=%s" % d["M"]
        inv = ["I1", "I2", "I4", "I5", "I6"]
        if mode in POLBASIS_MODES:
            inv.insert(2, "I3")
        applicable = ",".join(inv)
        expected = "HOLD(all applicable)" if d["expect_F_source"] == "REPORTED_FAILURE" else "UNKNOWN"
        lines.append("\t".join([d["point_id"], d["source"], "F", route, mode, "pattern both 4 3", d["request"], nk, mm,
                                d["inj_call"], d["twice"], str(kf), str(kp), str(kr), str(rcall), applicable,
                                expected, "INFLUENCED"]))
        n_out += 1
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("rows=%d counts=%s" % (n_out, {"%s/%s" % k: v for k, v in counts.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
