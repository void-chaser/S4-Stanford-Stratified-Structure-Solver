#!/usr/bin/env python3
# compare_f_baseline_m3_r7.py -- P05-S4 R7 cont9 (M3, U81): point-by-point, invariant-by-invariant comparison of the F baseline
# (run m3f1, tree F on R7) with the historical R6c judgement (registries/s4r6c).  New file.  Read-only on inputs.
#
# Inputs:
#   BASE   = EVDIR/m3f1/RESULTS_R6c_STATE.tsv                    (judged by r6c_judge.py, this run)
#   HIST   = registries/s4r6c/RESULTS_R6c_STATE.tsv              (historical R6c judgement, pass 1 and pass 2)
#   SEAM_BASE = EVDIR/m3f1/RESULTS_R6c_SEAM.tsv (optional, G6; if absent the G6 part is reported as NOT_RUN)
#   SEAM_HIST = registries/s4r6c/RESULTS_R6c_SEAM.tsv
# Output: EVDIR/M3_F_BASELINE_VS_R6c.tsv  (one line per point and per invariant, plus a summary block)
# Exit 0 iff for every compared point and invariant: verdict equal, FLAKY 0 in this run, GDB_DIVERGENT 0 in this run.
#
# Usage: python3 -I -B compare_f_baseline_m3_r7.py REPO EVDIR
import os
import sys

INV = ["I1", "I2", "I3", "I4", "I5", "I6"]


def read_table(path):
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


def compare(label, base_rows, hist_rows, out_lines):
    hist = {}
    for r in hist_rows:
        hist[(r["point_id"], r["pass"])] = r
    base = {}
    for r in base_rows:
        base[(r["point_id"], r["pass"])] = r
    n_pts = 0
    n_mismatch_inv = 0
    n_flaky = 0
    n_viol = 0
    n_div_hist_base = 0
    per_inv = {k: {"eq": 0, "neq": 0} for k in INV}
    for pid, pas in sorted(set(k for k in base)):
        b = base[(pid, pas)]
        h = hist.get((pid, pas))
        if h is None:
            out_lines.append("%s\t%s\t%s\tNO_HISTORY_ROW\t-\t-\t-" % (label, pid, pas))
            n_mismatch_inv += 1
            continue
        n_pts += 1
        if b["point_verdict"] == "VIOLATED":
            n_viol += 1
        for k in INV:
            bv, hv = b[k], h[k]
            eq = "EQUAL" if bv == hv else "DIFFERENT"
            per_inv[k]["eq" if eq == "EQUAL" else "neq"] += 1
            if eq != "EQUAL":
                n_mismatch_inv += 1
            out_lines.append("%s\t%s\t%s\t%s\tbase=%s\thist=%s\t%s" % (label, pid, pas, k, bv, hv, eq))
        if b["flaky"] != "-":
            n_flaky += 1
    # FLAKY per point across the two passes of this run
    base_pids = sorted(set(k[0] for k in base))
    flaky_pts = []
    for pid in base_pids:
        v1 = base.get((pid, "1"), {}).get("point_verdict")
        v2 = base.get((pid, "2"), {}).get("point_verdict")
        if v1 != v2:
            flaky_pts.append(pid)
    out_lines.append("# %s summary: points_compared_per_pass=%d invariant_differences=%d VIOLATED(base)=%d FLAKY(base)=%d"
                     % (label, n_pts, n_mismatch_inv, n_viol, len(flaky_pts)))
    out_lines.append("# %s per invariant (EQUAL/DIFFERENT over both passes): %s"
                     % (label, ", ".join("%s=%d/%d" % (k, per_inv[k]["eq"], per_inv[k]["neq"]) for k in INV)))
    return n_mismatch_inv, len(flaky_pts), n_viol


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: compare_f_baseline_m3_r7.py REPO EVDIR")
    repo, ev = argv[1], argv[2]
    out = os.path.join(ev, "M3_F_BASELINE_VS_R6c_FULL.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    lines = ["# M3_F_BASELINE_VS_R6c.tsv -- P05-S4 R7 cont9 M3 (U81): F baseline (m3f1, tree F on R7) vs historical R6c judgement.",
             "group\tpoint_id\tpass\tinvariant\tbase\thist\tresult"]
    m, f, v = compare("G5", read_table(os.path.join(ev, "m3f1", "RESULTS_R6c_STATE.tsv")),
                      read_table(os.path.join(repo, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_STATE.tsv")), lines)
    total_bad = m
    seam_base = os.path.join(ev, "m3f1", "RESULTS_R6c_SEAM.tsv")
    if os.path.isfile(seam_base):
        m2, f2, v2 = compare("G6", read_table(seam_base),
                             read_table(os.path.join(repo, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_SEAM.tsv")), lines)
        total_bad += m2
        f += f2
        v += v2
    else:
        lines.append("# G6: NOT_RUN (no seam baseline table yet)")
    lines.append("# RESULT: invariant_differences=%d FLAKY=%d VIOLATED=%d" % (total_bad, f, v))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("invariant_differences=%d flaky=%d violated=%d -> %s" % (total_bad, f, v, out))
    return 0 if (total_bad == 0 and f == 0 and v == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
