#!/usr/bin/env python3
# r6c_judge.py -- P05-S4 R6c-1 judge (new file; supersedes the attempted r6c_state_judge.py, which was never created).
#
# Judges I1-I6 (+ I4') for the 177 points from FACTS only.
# Facts used: the gdb log of each point and pass (R6BSTATE, R6BCLM, R6CREQ lines, in order), the gdb-run facts
# (rc1, rc2, rc3, hit) from the state tables, the call output files call1..3.txt and the control runs.
# judge_d003.py is IMPORTED and not modified.  The driver PASS/FAIL line is not read.
# Rules: REGISTRY_S4_PRE_R6b_STATE_v2.tsv (ERRATA_6c U14) with the U13 snapshot indices.
#
# Usage:  python3 -I -B testing/d003/stage_s4/r6c_judge.py PREREG_V2 CONTROL_V1 EVDIR
#   reads   EVDIR/STATE_R6c_pass{1,2}.tsv, EVDIR/state/pass{1,2}/..., EVDIR/dump/...
#   writes  EVDIR/RESULTS_R6c_STATE.tsv, EVDIR/STATE_SUMMARY_R6c.txt  (refuses to overwrite)
#
# Invariants (v2): I1 failed layer modes==NULL at k_fail.  I2 other layers == control at k_fail (q hash, installed).
# I3 field_cache nodes == control (PolBasis only; else N/A).  I4' solved[req]@k_fail == @k_before, and if that value is 1
# then modes_null(req)@k_fail == 1.  I5 retry enters ComputeLayerModes only for layers NULL at k_pre, once each; retry rc 0.
# I6 retry output byte-identical to the control's output of the same call number.  I7 DEFERRED (U9).
#
# Index rules (U13): k_before = 0 | 2;  k_fail = 1 | 3;  k_pre = 2 | 3;  k_retry = 3 | 4;  retry_call = 2 | 3 (inj_call 1 | 2).
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)
import judge_d003 as J  # noqa: E402,F401  (imported, not modified)

K_BEFORE = {1: 0, 2: 2}
K_FAIL = {1: 1, 2: 3}
K_PRE = {1: 2, 2: 3}
K_RETRY = {1: 3, 2: 4}
RETRY_CALL = {1: 2, 2: 3}
POLBASIS = {"jones", "nv", "vl", "fftjones", "fftnv", "fftvl"}
INV = ("I1", "I2", "I3", "I4", "I5", "I6")

RE_LAYER = re.compile(r"^R6BSTATE (\d+) layer (\d+) modes_null (\d) q_len (\S+) q_sha256 (\S+)\s*$")
RE_SOLVED = re.compile(r"^R6BSTATE (\d+) solution solved (.*)$")
RE_SOLVED_NULL = re.compile(r"^R6BSTATE (\d+) solution (null|solved_null)\s*$")
RE_CACHE = re.compile(r"^R6BSTATE (\d+) cache node \d+ layer (-?\d+) n \d+ plen (\d+) P_sha256 (\S+)\s*$")
RE_CACHE_NA = re.compile(r"^R6BSTATE (\d+) cache node \d+ layer -?\d+ n \d+ plen NA")
RE_NG = re.compile(r"^R6BSTATE (\d+) n_layers (\d+) n_G (\d+)\s*$")
RE_STATE_ANY = re.compile(r"^R6BSTATE (\d+) ")
RE_ENTER = re.compile(r"^R6BCLM ENTER idx (\d+) name (\S*)\s*$")
RE_RET = re.compile(r"^R6BCLM RETURN idx (\d+) name (\S*) rc (\S+)\s*$")
RE_REQ = re.compile(r"^R6CREQ (\d+) (-?\d+)\s*$")
# driver stdout (also present in the gdb log): copy field of each layer at each snapshot (U14 I4(b), copy layers)
RE_R6STATE_LAYER = re.compile(r"^R6STATE (\d+) layer (\d+) modes_null (\d) modes_ptr \S+ copy (-?\d+) nshapes \d+\s*$")


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


class GdbLog(object):
    """Ordered parse of one gdb log.  Interval (a, b] = events between the FIRST line of snapshot a and the FIRST line
    of snapshot b (the snapshot blocks are printed in order k = 0, 1, 2, 3, 4)."""

    def __init__(self, text):
        self.first_line = {}
        self.layers = {}      # (k, i) -> (modes_null, q_sha)
        self.solved = {}      # k -> {i: v}, or None
        self.cache = {}       # k -> list of (layer_idx, P_sha)
        self.n_layers = None
        self.copy = {}        # (k, i) -> copy field from the driver's R6STATE line (-1 = not a copy layer)
        self.seq = []         # ('enter', idx, pos) / ('ret', idx, rc, pos) / ('req', call, idx, pos)
        for pos, ln in enumerate(text.splitlines()):
            m = RE_STATE_ANY.match(ln)
            if m:
                self.first_line.setdefault(int(m.group(1)), pos)
            m = RE_R6STATE_LAYER.match(ln)
            if m:
                self.copy[(int(m.group(1)), int(m.group(2)))] = int(m.group(4))
                continue
            m = RE_LAYER.match(ln)
            if m:
                self.layers[(int(m.group(1)), int(m.group(2)))] = (int(m.group(3)), m.group(5))
                continue
            m = RE_SOLVED.match(ln)
            if m:
                d = {}
                for tok in m.group(2).split():
                    a, b = tok.split("=")
                    d[int(a)] = int(b)
                self.solved[int(m.group(1))] = d
                continue
            m = RE_SOLVED_NULL.match(ln)
            if m:
                self.solved[int(m.group(1))] = None
                continue
            m = RE_CACHE.match(ln)
            if m:
                self.cache.setdefault(int(m.group(1)), []).append((int(m.group(2)), m.group(4)))
                continue
            m = RE_CACHE_NA.match(ln)
            if m:
                self.cache.setdefault(int(m.group(1)), [])
                continue
            m = RE_NG.match(ln)
            if m:
                self.n_layers = int(m.group(2))
                continue
            m = RE_ENTER.match(ln)
            if m:
                self.seq.append(("enter", int(m.group(1)), pos))
                continue
            m = RE_RET.match(ln)
            if m:
                rc = None if m.group(3) == "NA" else int(m.group(3))
                self.seq.append(("ret", int(m.group(1)), rc, pos))
                continue
            m = RE_REQ.match(ln)
            if m:
                self.seq.append(("req", int(m.group(1)), int(m.group(2)), pos))

    def interval(self, a, b):
        pa, pb = self.first_line.get(a), self.first_line.get(b)
        if pa is None or pb is None:
            return None
        return [ev for ev in self.seq if pa < ev[-1] < pb]

    def req_idx(self, call):
        for ev in self.seq:
            if ev[0] == "req" and ev[1] == call:
                return ev[2]
        return None


def judge_point(d, g, c, outs, couts, rc_retry):
    """d: pre-registration row; g: GdbLog of the point; c: GdbLog of its control (or None); outs/couts: {call: bytes};
    rc_retry: retry rc (int) from the gdb-run facts.  Returns (OrderedDict inv -> (verdict, note), failing layer, req)."""
    ic = int(d["inj_call"])
    kb, kf, kp, kr = K_BEFORE[ic], K_FAIL[ic], K_PRE[ic], K_RETRY[ic]
    rcall = RETRY_CALL[ic]
    res = OrderedDict()
    mode = d["mode"]
    n_layers = g.n_layers
    inj = g.interval(kb, kf)
    if inj is None:
        for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
            res[inv] = ("UNJUDGED", "snapshot %d or %d missing in gdb log" % (kb, kf))
        res["I7"] = ("DEFERRED", "U9")
        return res, None, None
    failing = [ev[1] for ev in inj if ev[0] == "ret" and ev[2] not in (None, 0)]
    req = g.req_idx(ic)
    fl = failing[0] if failing else None

    # I1
    if fl is None:
        res["I1"] = ("N/A", "no ComputeLayerModes RETURN != 0 inside the injected call (k %d..%d)" % (kb, kf))
    else:
        s = g.layers.get((kf, fl))
        if s is None:
            res["I1"] = ("UNJUDGED", "no state line for failing layer %d at k_fail" % fl)
        elif s[0] == 1:
            res["I1"] = ("HOLD", "failing layer %d modes_null 1 at k_fail" % fl)
        else:
            res["I1"] = ("VIOLATED", "failing layer %d modes_null %d at k_fail" % (fl, s[0]))

    # I2 (E6-8 option 1 with conditions a/b/c; U8).  The KEPT layers are the non-failing layers whose modes are installed
    # (modes_null 0) at k_fail.  For each kept layer: (a) its q hash equals the control's q hash at the same snapshot,
    # (b) the control has the same layer installed at k_fail.  Layers with modes NULL at k_fail are not kept and are N/A.
    # Condition (c) is part of I5 (no re-entry in the retry interval) and is reported there.
    notes, verdict = [], "HOLD"
    if fl is None:
        verdict, notes = "N/A", ["no failing layer"]
    elif n_layers is None or c is None:
        verdict, notes = "UNJUDGED", ["control or layer count missing"]
    else:
        kept, not_kept = [], []
        for i in range(n_layers):
            if i == fl:
                continue
            gs = g.layers.get((kf, i))
            if gs is None:
                notes.append("layer %d state missing at k_fail" % i)
                verdict = "UNJUDGED" if verdict != "VIOLATED" else verdict
                continue
            (kept if gs[0] == 0 else not_kept).append(i)
        for i in kept:
            gs, cs = g.layers.get((kf, i)), c.layers.get((kf, i))
            if cs is None:
                notes.append("layer %d: control state missing at k_fail" % i)
                verdict = "UNJUDGED" if verdict != "VIOLATED" else verdict
                continue
            if cs[0] != 0:
                verdict = "VIOLATED"
                notes.append("kept layer %d not installed in control at k_fail (condition b)" % i)
            elif gs[1] != cs[1]:
                verdict = "VIOLATED"
                notes.append("kept layer %d q hash differs from control at k_fail (condition a)" % i)
        if verdict == "HOLD":
            if kept:
                notes.insert(0, "kept layers %s equal control at k_fail (q hash and installed state)" % kept)
            else:
                verdict = "N/A"
                notes.insert(0, "no kept layer at k_fail (every non-failing layer has modes NULL)")
        if not_kept:
            notes.append("layers with modes NULL at k_fail (N/A for I2): %s" % not_kept)
    res["I2"] = (verdict, "; ".join(notes))

    # I3
    if mode in POLBASIS:
        if c is None:
            res["I3"] = ("UNJUDGED", "control missing")
        else:
            cset = set(c.cache.get(kf, []))
            gc = g.cache.get(kf, [])
            bad = [x for x in gc if x not in cset]
            res["I3"] = ("HOLD" if not bad else "VIOLATED",
                         "field_cache nodes at k_fail: %d; nodes with no equal control node: %d" % (len(gc), len(bad)))
    else:
        res["I3"] = ("N/A", "mode %s does not read or write field_cache (ERRATA_6b E6b-4)" % mode)

    # I4' (U14).  solution null at a snapshot means no layer solved yet: every solved[i] is 0 (S4.cpp:1756 allocates and
    # S4.cpp:1764 zeroes; before the first solve solution is NULL).
    if req is None:
        res["I4"] = ("UNJUDGED", "no R6CREQ line for call %d" % ic)
    else:
        def solved_at(k):
            if k in g.solved and g.solved[k] is None:
                return 0 if n_layers is not None else None
            v = g.solved.get(k)
            return None if v is None else v.get(req)
        sf = solved_at(kf)
        sb = solved_at(kb)
        if sf is None or sb is None:
            res["I4"] = ("UNJUDGED", "solved not readable (k_before %s, k_fail %s)" % (sb, sf))
        else:
            ok_a = (sf == sb)
            note = "req layer %d; solved k_before %d, k_fail %d" % (req, sb, sf)
            if sf == 0:
                ok_b = True
            else:
                # (b) S4.cpp:1805: a recomputation is forced when modes==NULL (or the copied layer's modes==NULL).
                cp = g.copy.get((kf, req), None)
                if cp is None:
                    res["I4"] = ("UNJUDGED", note + "; copy field of req layer not in the driver output")
                    cp = "unknown"
                if cp != "unknown":
                    src = req if cp < 0 else cp
                    s = g.layers.get((kf, src))
                    ok_b = (s is not None and s[0] == 1)
                    note += "; solved@k_fail=1; source layer %d (copy %d) modes_null@k_fail=%s" % (
                        src, cp, s[0] if s else "NA")
                    res["I4"] = ("HOLD" if (ok_a and ok_b) else "VIOLATED", note)
            if "I4" not in res:
                res["I4"] = ("HOLD" if ok_a else "VIOLATED", note)

    # I5 (retry interval k_pre .. k_retry)
    pre_null = set()
    if n_layers is not None:
        for i in range(n_layers):
            s = g.layers.get((kp, i))
            if s is not None and s[0] == 1:
                pre_null.add(i)
    retry = g.interval(kp, kr)
    if retry is None:
        res["I5"] = ("UNJUDGED", "snapshot %d or %d missing" % (kp, kr))
    else:
        cnt = Counter(ev[1] for ev in retry if ev[0] == "enter")
        viol = []
        for i, n in sorted(cnt.items()):
            if i not in pre_null:
                viol.append("layer %d entered but modes not NULL at k_pre" % i)
            if n > 1:
                viol.append("layer %d entered %d times" % (i, n))
        if rc_retry is None:
            res["I5"] = ("UNJUDGED", "retry rc missing from facts")
        elif viol or rc_retry != 0:
            res["I5"] = ("VIOLATED", "; ".join(viol) if viol else "retry rc %d" % rc_retry)
        else:
            res["I5"] = ("HOLD", "retry enters %s; pre-NULL layers %s; retry rc 0" % (
                sorted(cnt.items()), sorted(pre_null)))

    # I6
    if rcall in outs and rcall in couts:
        same = outs[rcall] == couts[rcall]
        res["I6"] = ("HOLD" if same else "VIOLATED",
                     "call%d output %s control" % (rcall, "byte-identical to" if same else "differs from"))
    else:
        res["I6"] = ("UNJUDGED", "call%d output missing (point %s, control %s)" % (rcall, rcall in outs, rcall in couts))
    res["I7"] = ("DEFERRED", "U9")
    return res, fl, req


def point_verdict(res, hit):
    if hit == 0:
        return "INVALID"
    vals = [res[k][0] for k in INV]
    if "VIOLATED" in vals:
        return "VIOLATED"
    if all(v in ("HOLD", "N/A") for v in vals):
        return "HOLD"
    return "UNJUDGED"


def read_outs(d):
    out = {}
    for n in (1, 2, 3):
        p = os.path.join(d, "call%d.txt" % n)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                out[n] = fh.read()
    return out


def read_text(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6c_judge.py PREREG_V2 CONTROL_V1 EVDIR")
    prereg, control, ev = argv[1:4]
    out_res = os.path.join(ev, "RESULTS_R6c_STATE.tsv")
    out_sum = os.path.join(ev, "STATE_SUMMARY_R6c.txt")
    if os.path.exists(out_res) or os.path.exists(out_sum):
        raise SystemExit("REFUSED: result files exist; never overwritten (U17)")
    pts = read_table(prereg)
    if len(pts) != 177:
        raise SystemExit("REFUSED: prereg rows %d" % len(pts))
    ctrl = {c["control_id"]: c for c in read_table(control)}
    ctrl_of = {}
    for cid, c in ctrl.items():
        for pid in c["points_served"].split(";"):
            if pid:
                ctrl_of[pid] = cid
    facts = {}
    for pas in ("1", "2"):
        for r in read_table(os.path.join(ev, "STATE_R6c_pass%s.tsv" % pas)):
            facts[(pas, r["kind"], r["id"])] = r

    rows = []
    verdict = {"1": {}, "2": {}}
    for d in pts:
        pid = d["point_id"]
        cid = ctrl_of.get(pid)
        ic = int(d["inj_call"])
        for pas in ("1", "2"):
            fr = facts.get((pas, "point", pid))
            gp = os.path.join(ev, "state", "pass" + pas, pid, "gdb.log")
            if fr is None or not os.path.isfile(gp):
                verdict[pas][pid] = "UNJUDGED"
                rows.append((d, pas, cid, None, None, None, None, "UNJUDGED"))
                continue
            g = GdbLog(read_text(gp))
            c = None
            cgp = os.path.join(ev, "state", "pass" + pas, "controls", cid or "NA", "gdb.log")
            if cid and os.path.isfile(cgp):
                c = GdbLog(read_text(cgp))
            outs = read_outs(os.path.join(ev, "dump", pid, "pass" + pas))
            couts = read_outs(os.path.join(ev, "dump", "controls", cid, "pass" + pas)) if cid else {}
            rc_retry = None
            key = "gdb_rc2" if ic == 1 else "gdb_rc3"
            if fr[key] not in ("None", ""):
                rc_retry = int(fr[key])
            res, fl, req = judge_point(d, g, c, outs, couts, rc_retry)
            hit = int(fr["gdb_hit"]) if fr["gdb_hit"] not in ("None", "") else 0
            pv = point_verdict(res, hit)
            verdict[pas][pid] = pv
            rows.append((d, pas, cid, res, fl, req, hit, pv))

    flaky = set(pid for pid in verdict["1"] if verdict["1"][pid] != verdict["2"].get(pid))
    cols = ["point_id", "pass", "mode", "route", "inj_call", "request", "NTH_or_K", "M", "k_fail", "k_preretry",
            "k_retry", "retry_call", "control_id", "failing_layer", "req_layer", "I1", "I2", "I3", "I4", "I5", "I6",
            "I7", "hit", "point_verdict", "flaky", "notes"]
    with open(out_res, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R6c_STATE.tsv -- P05-S4 R6c-1 judgement of 177 points, passes 1 and 2 (facts only; rules in "
                 "r6c_judge.py; v2 pre-registration).\n")
        fh.write("# I4 is I4' (U14).  I7 DEFERRED (U9).  point_verdict is per pass; flaky marks a disagreement between passes.\n")
        fh.write("\t".join(cols) + "\n")
        for item in rows:
            d, pas, cid = item[0], item[1], item[2]
            if item[3] is None:
                fh.write("\t".join([d["point_id"], pas, d["mode"], d["route"], d["inj_call"], d["request"],
                                    d["NTH_or_K"], d["M"], d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"],
                                    cid or "NA", "NA", "NA"] + ["UNJUDGED"] * 7 + ["NA", "UNJUDGED", "MISSING",
                                    "no run facts"]) + "\n")
                continue
            res, fl, req, hit, pv = item[3], item[4], item[5], item[6], item[7]
            vals = [res[k][0] for k in INV] + [res["I7"][0]]
            notes = " | ".join("%s: %s" % (k, res[k][1]) for k in INV)
            fh.write("\t".join([d["point_id"], pas, d["mode"], d["route"], d["inj_call"], d["request"], d["NTH_or_K"],
                                d["M"], d["k_fail"], d["k_preretry"], d["k_retry"], d["retry_call"], cid or "NA",
                                "NA" if fl is None else str(fl), "NA" if req is None else str(req)] + vals +
                               [str(hit), pv, "FLAKY" if d["point_id"] in flaky else "-", notes]) + "\n")

    pv1 = Counter(verdict["1"].values())
    with open(out_sum, "w", encoding="utf-8") as fh:
        fh.write("# STATE_SUMMARY_R6c.txt -- computed by r6c_judge.py from RESULTS_R6c_STATE.tsv\n")
        fh.write("points %d ; FLAKY (pass 1 != pass 2) %d\n" % (len(pts), len(flaky)))
        fh.write("point verdict, pass 1: %s\n" % dict(sorted(pv1.items())))
        fh.write("point verdict, pass 2: %s\n" % dict(sorted(Counter(verdict["2"].values()).items())))
        fh.write("\nmode\troute\tinj_call\tinvariant\tHOLD\tVIOLATED\tN/A\tUNJUDGED\tDEFERRED\n")
        table = Counter()
        keys = set()
        for item in rows:
            d, pas = item[0], item[1]
            if pas != "1" or item[3] is None:
                continue
            keys.add((d["mode"], d["route"], d["inj_call"]))
            for k in INV + ("I7",):
                table[(d["mode"], d["route"], d["inj_call"], k, item[3][k][0])] += 1
        for m, r, ic in sorted(keys):
            for k in INV + ("I7",):
                fh.write("%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (
                    m, r, ic, k, table[(m, r, ic, k, "HOLD")], table[(m, r, ic, k, "VIOLATED")],
                    table[(m, r, ic, k, "N/A")], table[(m, r, ic, k, "UNJUDGED")], table[(m, r, ic, k, "DEFERRED")]))
        fh.write("\nFLAKY point ids: %s\n" % (" ".join(sorted(flaky)) if flaky else "none"))
    print("judged points=%d flaky=%d -> %s , %s" % (len(pts), len(flaky), out_res, out_sum))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
