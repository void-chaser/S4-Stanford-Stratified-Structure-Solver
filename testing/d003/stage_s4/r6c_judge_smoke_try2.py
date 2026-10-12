#!/usr/bin/env python3
# r6c_judge_smoke_try2.py -- P05-S4 R6c-1 smoke check of the judge logic, second try (new file).
# Same as r6c_judge_smoke.py but writes SMOKE_JUDGE_R6c_pass1_try2.txt (U17: the first smoke output SMOKE_JUDGE_R6c_pass1.txt
# is kept, not overwritten; it was produced before the I2 / I4 / copy corrections recorded in ERRATA_6c E6c-2).
# NOT a final judgement (brief 3.1).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_judge_smoke_try2.py PREREG_V2 CONTROL_V1 EVDIR
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6c_judge as R  # noqa: E402


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6c_judge_smoke_try2.py PREREG_V2 CONTROL_V1 EVDIR")
    prereg, control, ev = argv[1:4]
    out = os.path.join(ev, "SMOKE_JUDGE_R6c_pass1_try2.txt")
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
    lines.append("# SMOKE_JUDGE_R6c_pass1_try2.txt -- smoke check of the judge logic, try 2 (NOT the final judgement).")
    lines.append("point_id\tmode\troute\tinj_call\tcontrol\tfailing_layer\treq_layer\tI1\tI2\tI3\tI4\tI5\tI6\tpoint_verdict\tnotes")
    for pid in sorted(pts):
        d = pts[pid]
        if ("point", pid) not in facts:
            continue
        cid = ctrl_of.get(pid)
        fr = facts[("point", pid)]
        g = R.GdbLog(R.read_text(os.path.join(ev, "smoke", "pass1", pid, "gdb.log")))
        c = None
        if cid and os.path.isfile(os.path.join(ev, "smoke", "pass1", "controls", cid, "gdb.log")):
            c = R.GdbLog(R.read_text(os.path.join(ev, "smoke", "pass1", "controls", cid, "gdb.log")))
        outs = R.read_outs(os.path.join(ev, "dump", pid, "pass1"))
        couts = R.read_outs(os.path.join(ev, "dump", "controls", cid, "pass1")) if cid else {}
        ic = int(d["inj_call"])
        key = "gdb_rc2" if ic == 1 else "gdb_rc3"
        rc_retry = int(fr[key]) if fr[key] not in ("None", "") else None
        res, fl, req = R.judge_point(d, g, c, outs, couts, rc_retry)
        pv = R.point_verdict(res, int(fr["gdb_hit"]))
        lines.append("\t".join([pid, d["mode"], d["route"], d["inj_call"], cid or "NA",
                                "NA" if fl is None else str(fl), "NA" if req is None else str(req)] +
                               [res[k][0] for k in R.INV] + [pv, " | ".join("%s: %s" % (k, res[k][1]) for k in R.INV)]))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("smoke judge try2 lines=%d -> %s" % (len(lines) - 2, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
