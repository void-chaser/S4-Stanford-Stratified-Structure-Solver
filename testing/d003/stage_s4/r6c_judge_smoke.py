#!/usr/bin/env python3
# r6c_judge_smoke.py -- P05-S4 R6c-1 smoke check of the judge logic (new file).  NOT a final judgement (AGENTS / brief 3.1).
# Applies r6c_judge.judge_point to the smoke batch (SMOKE_R6c_pass1.tsv and smoke/pass1/...) and writes
# SMOKE_JUDGE_R6c_pass1.txt (a single new file).  Its purpose: check that the judge logic reads the gdb logs, the
# snapshot intervals and the R6CREQ lines correctly before the full run.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_judge_smoke.py PREREG_V2 CONTROL_V1 EVDIR
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6c_judge as R  # noqa: E402


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6c_judge_smoke.py PREREG_V2 CONTROL_V1 EVDIR")
    prereg, control, ev = argv[1:4]
    out = os.path.join(ev, "SMOKE_JUDGE_R6c_pass1.txt")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten: %s" % out)
    pts = {d["point_id"]: d for d in R.read_table(prereg)}
    ctrl = {c["control_id"]: c for c in R.read_table(control)}
    ctrl_of = {}
    for cid, c in ctrl.items():
        for pid in c["points_served"].split(";"):
            if pid:
                ctrl_of[pid] = cid
    facts = {}
    for r in R.read_table(os.path.join(ev, "SMOKE_R6c_pass1.tsv")):
        facts[(r["kind"], r["id"])] = r
    lines = []
    lines.append("# SMOKE_JUDGE_R6c_pass1.txt -- smoke check of the judge logic (NOT the final judgement).")
    lines.append("point_id\tmode\troute\tinj_call\tcontrol\tfailing_layer\treq_layer\tI1\tI2\tI3\tI4\tI5\tI6\tpoint_verdict\tnotes")
    for pid in sorted(pts):
        d = pts[pid]
        if ("point", pid) not in facts:
            continue
        cid = ctrl_of.get(pid)
        fr = facts[("point", pid)]
        gpath = os.path.join(ev, "smoke", "pass1", pid, "gdb.log")
        g = R.GdbLog(R.read_text(gpath))
        c = None
        if cid:
            cg = os.path.join(ev, "smoke", "pass1", "controls", cid, "gdb.log")
            if os.path.isfile(cg):
                c = R.GdbLog(R.read_text(cg))
        outs = R.read_outs(os.path.join(ev, "dump", pid, "pass1"))
        couts = R.read_outs(os.path.join(ev, "dump", "controls", cid, "pass1")) if cid else {}
        ic = int(d["inj_call"])
        key = "gdb_rc2" if ic == 1 else "gdb_rc3"
        rc_retry = int(fr[key]) if fr[key] not in ("None", "") else None
        res, fl, req = R.judge_point(d, g, c, outs, couts, rc_retry)
        hit = int(fr["gdb_hit"])
        pv = R.point_verdict(res, hit)
        lines.append("\t".join([pid, d["mode"], d["route"], d["inj_call"], cid or "NA",
                                "NA" if fl is None else str(fl), "NA" if req is None else str(req)] +
                               [res[k][0] for k in R.INV] + [pv, " | ".join("%s: %s" % (k, res[k][1]) for k in R.INV)]))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("smoke judge lines=%d -> %s" % (len(lines) - 2, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
