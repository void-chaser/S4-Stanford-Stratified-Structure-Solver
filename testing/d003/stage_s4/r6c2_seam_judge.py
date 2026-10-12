#!/usr/bin/env python3
# r6c2_seam_judge.py -- P05-S4 R6c2-2 step 4 (new file): judgement of the 25 seam points with the UNCHANGED judge functions
# of r6c_judge.py (imported; judge_point, GdbLog, point_verdict, read_outs, read_table are used as they are).
#
# What this file changes against the 177-point main(): input paths and the control table only.
#   * points: REGISTRY_S4_PRE_R6c_SEAM.tsv (25 rows; columns route, inj_call, k_fail, k_preretry, k_retry, retry_call present).
#     The seam requests carry their own sites, so the NTH_or_K and M columns are written as "-" in the output (no NTH/M).
#   * states: state/seam_pass<n>/<point>/gdb.log;  controls: state/seam_pass<n>/controls/<cid>/gdb.log (U18 (a) controls).
#   * outputs: dump/seam_<point>/pass<n>/call*.txt;  control outputs: dump/seam_controls/<cid>/pass<n>/call*.txt.
#   * facts: STATE_SEAM_R6c_pass<n>.tsv (kind, id, gdb_rc2, gdb_hit, ...).
#   * the control of a point is found in REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv (the (library, mode) match, points_served).
# Outputs (refused if they exist): RESULTS_R6c_SEAM.tsv, STATE_SUMMARY_R6c_SEAM.txt.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_seam_judge.py PREREG_SEAM CONTROL_SEAM EVDIR
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6c_judge as JU  # noqa: E402  (imported, not modified)


def facts_table(path, kind="point"):
    return {r["id"]: r for r in JU.read_table(path) if r.get("kind") == kind}


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6c2_seam_judge.py PREREG_SEAM CONTROL_SEAM EVDIR")
    prereg, control, ev = argv[1:4]
    out_res = os.path.join(ev, "RESULTS_R6c_SEAM.tsv")
    out_sum = os.path.join(ev, "STATE_SUMMARY_R6c_SEAM.txt")
    if os.path.exists(out_res) or os.path.exists(out_sum):
        raise SystemExit("REFUSED: result files exist; never overwritten (U17)")
    pts = JU.read_table(prereg)
    if len(pts) != 25:
        raise SystemExit("REFUSED: seam prereg rows %d" % len(pts))
    ctrls = JU.read_table(control)
    if len(ctrls) != 18:
        raise SystemExit("REFUSED: seam control rows %d" % len(ctrls))
    ctrl_of = {}
    for c in ctrls:
        for pid in c["points_served"].split(";"):
            if pid:
                ctrl_of[pid] = c
    if len(ctrl_of) != 25:
        raise SystemExit("REFUSED: controls serve %d points, expected 25" % len(ctrl_of))
    facts = {}
    for pas in ("1", "2"):
        facts[pas] = facts_table(os.path.join(ev, "STATE_SEAM_R6c_pass%s.tsv" % pas), "point")
        facts[pas + "c"] = facts_table(os.path.join(ev, "STATE_SEAM_R6c_pass%s.tsv" % pas), "control")
    for pas in ("1", "2"):
        for d in pts:
            if d["point_id"] not in facts[pas]:
                raise SystemExit("REFUSED: point %s missing in STATE_SEAM pass %s" % (d["point_id"], pas))

    verdict = {"1": {}, "2": {}}
    rows = []
    for d in pts:
        pid = d["point_id"]
        c = ctrl_of[pid]
        cid = c["control_id"]
        ic = int(d["inj_call"])
        for pas in ("1", "2"):
            fr = facts[pas][pid]
            gp = os.path.join(ev, "state", "seam_pass" + pas, pid, "gdb.log")
            cgp = os.path.join(ev, "state", "seam_pass" + pas, "controls", cid, "gdb.log")
            if not (os.path.isfile(gp) and os.path.isfile(cgp)):
                verdict[pas][pid] = "UNJUDGED"
                rows.append((d, pas, cid, None, None, None, None, "UNJUDGED"))
                continue
            g = JU.GdbLog(JU.read_text(gp))
            cg = JU.GdbLog(JU.read_text(cgp))
            outs = JU.read_outs(os.path.join(ev, "dump", "seam_" + pid, "pass" + pas))
            couts = JU.read_outs(os.path.join(ev, "dump", "seam_controls", cid, "pass" + pas))
            key = "gdb_rc2" if ic == 1 else "gdb_rc3"
            rc_retry = None if fr[key] in ("None", "") else int(fr[key])
            res, fl, req = JU.judge_point(d, g, cg, outs, couts, rc_retry)
            hit = int(fr["gdb_hit"]) if fr["gdb_hit"] not in ("None", "") else 0
            pv = JU.point_verdict(res, hit)
            verdict[pas][pid] = pv
            rows.append((d, pas, cid, res, fl, req, hit, pv))

    flaky = set(pid for pid in verdict["1"] if verdict["1"][pid] != verdict["2"].get(pid))
    cols = ["point_id", "pass", "library", "mode", "route", "inj_call", "request", "NTH_or_K", "M", "k_fail", "k_preretry",
            "k_retry", "retry_call", "control_id", "failing_layer", "req_layer", "I1", "I2", "I3", "I4", "I5", "I6", "I7",
            "hit", "point_verdict", "flaky", "notes"]
    with open(out_res, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R6c_SEAM.tsv -- P05-S4 R6c2-2 judgement of 25 seam points, passes 1 and 2 (judge functions of "
                 "r6c_judge.py, unchanged; seam controls of U18 (a)).\n")
        fh.write("# I4 is I4' (U14).  I7 DEFERRED (U9).  NTH_or_K and M are '-' for seam points (requests carry their sites).\n")
        fh.write("\t".join(cols) + "\n")
        for item in rows:
            d, pas, cid = item[0], item[1], item[2]
            if item[3] is None:
                fh.write("\t".join([d["point_id"], pas, d["library"], d["mode"], d["route"], d["inj_call"], d["request"],
                                    "-", "-", d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"], cid, "NA", "NA"]
                                   + ["UNJUDGED"] * 7 + ["NA", "UNJUDGED", "MISSING", "no run facts"]) + "\n")
                continue
            res, fl, req, hit, pv = item[3], item[4], item[5], item[6], item[7]
            vals = [res[k][0] for k in JU.INV] + [res["I7"][0]]
            notes = " | ".join("%s: %s" % (k, res[k][1]) for k in JU.INV)
            fh.write("\t".join([d["point_id"], pas, d["library"], d["mode"], d["route"], d["inj_call"], d["request"],
                                "-", "-", d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"], cid,
                                "NA" if fl is None else str(fl), "NA" if req is None else str(req)] + vals +
                               [str(hit), pv, "FLAKY" if d["point_id"] in flaky else "-", notes]) + "\n")

    pv1 = Counter(verdict["1"].values())
    with open(out_sum, "w", encoding="utf-8") as fh:
        fh.write("# STATE_SUMMARY_R6c_SEAM.txt -- computed by r6c2_seam_judge.py (judge functions of r6c_judge.py) from "
                 "RESULTS_R6c_SEAM.tsv\n")
        fh.write("points %d ; FLAKY (pass 1 != pass 2) %d\n" % (len(pts), len(flaky)))
        fh.write("point verdict, pass 1: %s\n" % dict(sorted(pv1.items())))
        fh.write("point verdict, pass 2: %s\n" % dict(sorted(Counter(verdict["2"].values()).items())))
        fh.write("\nmode\tlibrary\troute\tinj_call\tinvariant\tHOLD\tVIOLATED\tN/A\tUNJUDGED\tDEFERRED\n")
        table = Counter()
        keys = set()
        for item in rows:
            d, pas = item[0], item[1]
            if pas != "1" or item[3] is None:
                continue
            keys.add((d["library"], d["mode"], d["route"], d["inj_call"]))
            for k in JU.INV + ("I7",):
                table[(d["library"], d["mode"], d["route"], d["inj_call"], k, item[3][k][0])] += 1
        for lib, m, r, ic in sorted(keys):
            for k in JU.INV + ("I7",):
                fh.write("%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (
                    m, lib, r, ic, k, table[(lib, m, r, ic, k, "HOLD")], table[(lib, m, r, ic, k, "VIOLATED")],
                    table[(lib, m, r, ic, k, "N/A")], table[(lib, m, r, ic, k, "UNJUDGED")],
                    table[(lib, m, r, ic, k, "DEFERRED")]))
        fh.write("\nFLAKY point ids: %s\n" % (" ".join(sorted(flaky)) if flaky else "none"))
    print("seam judged points=%d flaky=%d -> %s , %s" % (len(pts), len(flaky), out_res, out_sum))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
