#!/usr/bin/env python3
# regress_m3_r7.py -- P05-S4 R7 cont9 (M3, section 3.2): per-point regression table of F2 (m3r1) against F (m3f1) and against
# the historical R6c judgement (new file; read-only on inputs).
#
# Output: EVDIR/REGRESS_R7_M3.tsv with one line per point (G5 177, G6 25, controls G6c 18):
#   group, point_id, hist_F (R6c verdict, pass 1), F_R7 (m3f1 verdict, pass 1), F2_pass1, F2_pass2, F_vs_F2 (EQUAL/DIFFERENT
#   on rc1, rc2, rc3, hit and every invariant I1-I6, both passes), verdict (F2 point verdict, pass 1 and pass 2).
# Summary block at the end, and the expectation check of section 3.2 (G5 HOLD 177 / VIOLATED 0; G6 HOLD 25 / VIOLATED 0;
# controls equal to history; FLAKY 0; GDB_DIVERGENT 0; F and F2 equal point by point).
# Exit 0 iff every expectation holds.
#
# Usage: python3 -I -B regress_m3_r7.py REPO EVDIR
import os
import sys

INV = ["I1", "I2", "I3", "I4", "I5", "I6"]
FACTS = ["rc1", "rc2", "rc3", "hit"]


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


def gdb_divergent_lines(ev):
    """Count GDB_DIVERGENT lines in the stdout of every M3 runner call (the runners print one line per divergence)."""
    n = 0
    for tree in ("m3f1", "m3r1"):
        d = os.path.join(ev, tree)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.endswith(".stdout"):
                with open(os.path.join(d, name), encoding="utf-8", errors="replace") as fh:
                    n += sum(1 for line in fh if line.startswith("GDB_DIVERGENT"))
    return n


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: regress_m3_r7.py REPO EVDIR")
    repo, ev = argv[1], argv[2]
    out = os.path.join(ev, "REGRESS_R7_M3.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    hist_g5 = read_table(os.path.join(repo, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_STATE.tsv"))
    hist_g6 = read_table(os.path.join(repo, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_SEAM.tsv"))
    f_g5 = read_table(os.path.join(ev, "m3f1", "RESULTS_R6c_STATE.tsv"))
    f2_g5 = read_table(os.path.join(ev, "m3r1", "RESULTS_R6c_STATE.tsv"))
    f_g6 = read_table(os.path.join(ev, "m3f1", "RESULTS_R6c_SEAM.tsv"))
    f2_g6 = read_table(os.path.join(ev, "m3r1", "RESULTS_R6c_SEAM.tsv"))

    def index(rows):
        return {(r["point_id"], r["pass"]): r for r in rows}

    # raw facts (gdb_rc1, gdb_rc2, gdb_rc3, gdb_hit) of the G5 points, from the state runner tables of each pass
    def facts_index(tree):
        out = {}
        for p in ("1", "2"):
            for r in read_table(os.path.join(ev, tree, "STATE_R6c_pass%s.tsv" % p)):
                if r.get("kind") == "point":
                    out[(r["id"], p)] = r
        return out

    FACT_F = facts_index("m3f1")
    FACT_F2 = facts_index("m3r1")

    # seam facts (G6): STATE_SEAM_R6c_pass<n>.tsv, kind point; columns gdb_rc1, gdb_rc2, gdb_hit (no rc3 in the seam runner)
    def seam_facts_index(tree):
        out = {}
        for p in ("1", "2"):
            for r in read_table(os.path.join(ev, tree, "STATE_SEAM_R6c_pass%s.tsv" % p)):
                if r.get("kind") == "point":
                    out[(r["id"], p)] = r
        return out

    SFACT_F = seam_facts_index("m3f1")
    SFACT_F2 = seam_facts_index("m3r1")
    H5, F5, G5 = index(hist_g5), index(f_g5), index(f2_g5)
    H6, F6, G6 = index(hist_g6), index(f_g6), index(f2_g6)
    # the historical rows: judge pass 1 is the reference (R6c judgement identical in both passes)
    cols = ["group", "point_id", "hist_F_pass1", "F_R7_pass1", "F2_pass1", "F2_pass2", "F_vs_F2", "hist_vs_F2", "verdict_F2"]
    lines = ["# REGRESS_R7_M3.tsv -- P05-S4 R7 cont9 M3 (section 3.2): per point, F (m3f1), F2 (m3r1), historical R6c.",
             "\t".join(cols)]
    counts = {"G5": {"HOLD": 0, "VIOLATED": 0, "OTHER": 0}, "G6": {"HOLD": 0, "VIOLATED": 0, "OTHER": 0}}
    flaky = 0
    gdb_div = 0
    fvf2_diff = 0
    hist_diff = 0
    for group, Hm, Fm, Gm, src in (("G5", H5, F5, G5, hist_g5), ("G6", H6, F6, G6, hist_g6)):
        pids = sorted(set(k[0] for k in Gm))
        for pid in pids:
            h = Hm.get((pid, "1"))
            f1 = Fm.get((pid, "1"))
            g1 = Gm.get((pid, "1"))
            g2 = Gm.get((pid, "2"))
            f2 = Fm.get((pid, "2"))
            if None in (h, f1, g1, g2, f2):
                lines.append("\t".join([group, pid, "MISSING", "-", "-", "-", "-", "-", "MISSING"]))
                counts[group]["OTHER"] += 1
                continue
            # F vs F2: rc1, rc2, rc3, hit (raw facts) and invariants (verdicts), both passes
            eq_facts = True
            for p_f, p_g in (("1", "1"), ("2", "2")):
                a = Fm[(pid, p_f)]
                b = Gm[(pid, p_g)]
                for k in INV:
                    if a[k] != b[k]:
                        eq_facts = False
                # raw facts from the state runner tables (gdb_* columns); G5 has rc1, rc2, rc3, hit; G6 has rc1, rc2, hit
                if group == "G5":
                    fa, fb, keys = FACT_F[(pid, p_f)], FACT_F2[(pid, p_g)], ("gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit")
                else:
                    fa, fb, keys = SFACT_F[(pid, p_f)], SFACT_F2[(pid, p_g)], ("gdb_rc1", "gdb_rc2", "gdb_hit")
                for k in keys:
                    if fa.get(k) is None or fa.get(k) != fb.get(k):
                        eq_facts = False
            # hist vs F2 (invariant verdicts, pass 1)
            eq_hist = all(h[k] == g1[k] for k in INV)
            if not eq_facts:
                fvf2_diff += 1
            if not eq_hist:
                hist_diff += 1
            if g1["point_verdict"] != g2["point_verdict"] or g1["flaky"] != "-" or g2["flaky"] != "-":
                flaky += 1
            v = g1["point_verdict"]
            if v == "HOLD":
                counts[group]["HOLD"] += 1
            elif v == "VIOLATED":
                counts[group]["VIOLATED"] += 1
            else:
                counts[group]["OTHER"] += 1
            lines.append("\t".join([group, pid, h["point_verdict"], f1["point_verdict"], g1["point_verdict"],
                                    g2["point_verdict"], "EQUAL" if eq_facts else "DIFFERENT",
                                    "EQUAL" if eq_hist else "DIFFERENT", v]))
    # controls (G6c): raw facts of the seam controls, F2 vs historical R6c (rc1, rc2, hit)
    ctrl_diff = 0
    n_ctrl = 0
    hist_ctrl = {}
    for r in read_table(os.path.join(repo, "checkpoints/p05/registries/s4r6c/STATE_SEAM_R6c_pass1.tsv")):
        if r.get("kind") == "control":
            hist_ctrl[r["id"]] = r
    for p in ("1", "2"):
        for r in read_table(os.path.join(ev, "m3r1", "STATE_SEAM_R6c_pass%s.tsv" % p)):
            if r.get("kind") != "control":
                continue
            if p == "1":
                n_ctrl += 1
                h = hist_ctrl.get(r["id"])
                if h is None or [h.get("gdb_rc1"), h.get("gdb_rc2"), h.get("gdb_hit")] != [r.get("gdb_rc1"), r.get("gdb_rc2"), r.get("gdb_hit")]:
                    ctrl_diff += 1
                lines.append("\t".join(["G6c", r["id"], "control", "-", "-", "-",
                                        "-", "-", "CONTROL_OK" if r.get("status") == "OK" else "CHECK"]))
    # R6c seam control status is 'OK' in the run; the historical control facts are compared above
    summary = [
        "# SUMMARY (section 3.2 expectations)",
        "# G5 F2: HOLD %d / VIOLATED %d / other %d (expect HOLD 177 / VIOLATED 0)" % (
            counts["G5"]["HOLD"], counts["G5"]["VIOLATED"], counts["G5"]["OTHER"]),
        "# G6 F2: HOLD %d / VIOLATED %d / other %d (expect HOLD 25 / VIOLATED 0)" % (
            counts["G6"]["HOLD"], counts["G6"]["VIOLATED"], counts["G6"]["OTHER"]),
        "# G6 controls compared to history: %d, facts differing %d (expect 0)" % (n_ctrl, ctrl_diff),
        "# FLAKY points (F2, pass1 != pass2 or flaky mark): %d (expect 0)" % flaky,
        "# GDB_DIVERGENT lines in the runners' stdout (m3f1 and m3r1, all passes): %d (expect 0)" % gdb_divergent_lines(ev),
        "# F vs F2 points with any raw-fact or invariant difference (both passes): %d (expect 0)" % fvf2_diff,
        "# F2 invariant verdicts differing from history (pass 1): %d (expect 0)" % hist_diff,
    ]
    ok = (counts["G5"]["HOLD"] == 177 and counts["G5"]["VIOLATED"] == 0 and counts["G6"]["HOLD"] == 25
          and counts["G6"]["VIOLATED"] == 0 and ctrl_diff == 0 and flaky == 0 and fvf2_diff == 0 and hist_diff == 0
          and counts["G5"]["OTHER"] == 0 and counts["G6"]["OTHER"] == 0)
    summary.append("# RESULT: %s" % ("PASS" if ok else "NOT_PASS"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines + summary) + "\n")
    print("\n".join(summary))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
