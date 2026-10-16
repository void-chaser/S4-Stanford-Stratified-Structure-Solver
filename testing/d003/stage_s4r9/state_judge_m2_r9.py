#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# state_judge_m2_r9.py -- P05-S4 R9 state analyzer.
import argparse
import os
import re
import sys
from collections import Counter, OrderedDict

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
D003 = os.path.join(REPO, "testing", "d003")
if D003 not in sys.path:
    sys.path.insert(0, D003)
import judge_d003 as J  # noqa: E402,F401 (imported, not modified)

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
    """Ordered parse of one gdb log. Interval (a, b] = events between the FIRST line of snapshot a and the FIRST line
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
    rc_retry: retry rc (int) from the gdb-run facts. Returns (OrderedDict inv -> (verdict, note), failing layer, req)."""
    ic = int(d["inj_call"]) if d.get("inj_call") not in (None, "", "-") else 1
    kb = int(d["k_before"]) if d.get("k_before") not in (None, "", "-") else K_BEFORE.get(ic, 0)
    kf = int(d["k_fail"]) if d.get("k_fail") not in (None, "", "-") else K_FAIL.get(ic, 1)
    kp = int(d["k_preretry"]) if d.get("k_preretry") not in (None, "", "-") else K_PRE.get(ic, 2)
    kr = int(d["k_retry"]) if d.get("k_retry") not in (None, "", "-") else K_RETRY.get(ic, 3)
    rcall = int(d["retry_call"]) if d.get("retry_call") not in (None, "", "-") else RETRY_CALL.get(ic, 2)
    out_call = int(d["output_call"]) if d.get("output_call") not in (None, "", "-") else rcall
    ctrl_out_call = int(d["control_output_call"]) if d.get("control_output_call") not in (None, "", "-") else rcall

    is_dual = (d.get("item") == "M2-04" or d.get("exp_hit2") not in (None, "", "-"))
    res = OrderedDict()
    # mode can come from mode column or env string
    mode = d.get("mode")
    if not mode:
        env_s = d.get("env", "")
        for tok in env_s.split(";"):
            if tok.startswith("FMM_MODE="):
                mode = tok.split("=", 1)[1]
                break
    n_layers = g.n_layers
    inj = g.interval(kb, kf)
    if inj is None:
        for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
            res[inv] = ("UNJUDGED", "snapshot %d or %d missing in gdb log" % (kb, kf))
        res["I7"] = ("DEFERRED", "U9") if "applicable_invariants" in d else ("N/A", "not a sanitizer point")
        return res, None, None
    failing = [ev[1] for ev in inj if ev[0] == "ret" and ev[2] not in (None, 0)]
    req = g.req_idx(ic)
    fl = failing[0] if failing else None

    # I1
    if not is_dual:
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
    else:
        # Dual failure: target 1 at kf; target 2 at kf2
        if fl is None:
            res["I1"] = ("VIOLATED", "no ComputeLayerModes RETURN != 0 inside call1 (k %d..%d)" % (kb, kf))
        else:
            s1 = g.layers.get((kf, fl))
            if s1 is None:
                res["I1"] = ("UNJUDGED", "no state line for call1 failing layer %d at k_fail" % fl)
            elif s1[0] != 1:
                res["I1"] = ("VIOLATED", "call1 failing layer %d modes_null %d at k_fail" % (fl, s1[0]))
            else:
                # Check call2 second failure
                kb2 = int(d.get("k_before2", 2)) if d.get("k_before2") not in (None, "", "-") else 2
                kf2 = int(d.get("k_fail2", 3)) if d.get("k_fail2") not in (None, "", "-") else 3
                exp_fl2 = d.get("fail_layer2")
                inj2 = g.interval(kb2, kf2)
                if inj2 is None:
                    res["I1"] = ("UNJUDGED", "snapshot %d or %d missing in gdb log for call2" % (kb2, kf2))
                else:
                    failing2 = [ev[1] for ev in inj2 if ev[0] == "ret" and ev[2] not in (None, 0)]
                    fl2 = failing2[0] if failing2 else None
                    if fl2 is None:
                        res["I1"] = ("VIOLATED", "no ComputeLayerModes failure in call2 (k %d..%d)" % (kb2, kf2))
                    elif exp_fl2 not in (None, "", "-", "UNRESOLVED") and fl2 != int(exp_fl2):
                        res["I1"] = ("VIOLATED", "call2 failing layer %d differs from exp fail_layer2 %s" % (fl2, exp_fl2))
                    else:
                        s2 = g.layers.get((kf2, fl2))
                        if s2 is None:
                            res["I1"] = ("UNJUDGED", "no state line for call2 failing layer %d at k_fail2" % fl2)
                        elif s2[0] != 1:
                            res["I1"] = ("VIOLATED", "call2 failing layer %d modes_null %d at k_fail2" % (fl2, s2[0]))
                        else:
                            res["I1"] = ("HOLD", "call1 layer %d modes_null 1 at k_fail; call2 layer %d modes_null 1 at k_fail2" % (fl, fl2))

    # I2
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
            g_cache_nodes = g.cache.get(kf, [])
            bad = [x for x in g_cache_nodes if x not in cset]
            res["I3"] = ("HOLD" if not bad else "VIOLATED",
                         "field_cache nodes at k_fail: %d; nodes with no equal control node: %d" % (len(g_cache_nodes), len(bad)))
    else:
        res["I3"] = ("N/A", "mode %s does not read or write field_cache (ERRATA_6b E6b-4)" % mode)

    # I4'
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

    # I5
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
    if out_call in outs and ctrl_out_call in couts:
        same = outs[out_call] == couts[ctrl_out_call]
        res["I6"] = ("HOLD" if same else "VIOLATED",
                     "call%d output %s control call%d" % (out_call, "byte-identical to" if same else "differs from", ctrl_out_call))
    else:
        res["I6"] = ("UNJUDGED", "call%d output missing (point %s, control %s)" % (out_call, out_call in outs, ctrl_out_call in couts))

    # I7
    if "applicable_invariants" in d:
        res["I7"] = ("DEFERRED", "U9")
    else:
        res["I7"] = ("N/A", "not a sanitizer point")

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
    if not os.path.isdir(d):
        return out
    for n in (1, 2, 3, 4):
        p = os.path.join(d, "call%d.txt" % n)
        if os.path.isfile(p):
            with open(p, "rb") as fh:
                out[n] = fh.read()
    return out


def read_text(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main():
    parser = argparse.ArgumentParser(description="P05-S4 state analyzer")
    parser.add_argument("prereg", nargs="?", default=None, help="Pre-registration table")
    parser.add_argument("control", nargs="?", default=None, help="Control mapping or control group table")
    parser.add_argument("evdir", nargs="?", default=None, help="Evidence directory")
    parser.add_argument("--prereg", dest="opt_prereg", default=None)
    parser.add_argument("--control", dest="opt_control", default=None)
    parser.add_argument("--ev", dest="opt_ev", default=None)
    parser.add_argument("--out-res", default=None, help="Output RESULTS tsv")
    parser.add_argument("--out-sum", default=None, help="Output SUMMARY txt")
    parser.add_argument("--facts1", default=None, help="Path to pass 1 facts tsv")
    parser.add_argument("--facts2", default=None, help="Path to pass 2 facts tsv")
    parser.add_argument("--facts-dir", default=None, help="Directory containing facts tables")
    parser.add_argument("--state-dir", default=None, help="Directory containing gdb logs")
    parser.add_argument("--dumps-dir", default=None, help="Directory containing field dumps")

    args = parser.parse_args()

    prereg = args.opt_prereg or args.prereg
    control = args.opt_control or args.control
    ev = args.opt_ev or args.evdir

    if not prereg or not control or not ev:
        sys.exit("usage: state_judge_m2_r8m2d.py PREREG CONTROL EVDIR [--out-res OUT] [--out-sum OUT]")

    out_res = args.out_res or os.path.join(ev, "RESULTS_R6c_STATE.tsv")
    out_sum = args.out_sum or os.path.join(ev, "STATE_SUMMARY_R6c.txt")

    if os.path.exists(out_res) or os.path.exists(out_sum):
        sys.exit("REFUSED: result files exist; never overwritten (U17): %s or %s" % (out_res, out_sum))

    pts = read_table(prereg)
    ctrl_rows = read_table(control)
    ctrl_map = {}
    for c in ctrl_rows:
        if "control_id" in c:
            ctrl_map[c["control_id"]] = c
        elif "point_id" in c:
            ctrl_map[c["point_id"]] = c

    ctrl_of = {}
    for cid, c in ctrl_map.items():
        if "points_served" in c:
            for pid in c["points_served"].split(";"):
                if pid:
                    ctrl_of[pid] = cid
        elif "control_point_id" in c:
            ctrl_of[c["point_id"]] = c["control_point_id"]

    facts = {}
    for pas in ("1", "2"):
        explicit_f = args.facts1 if pas == "1" else args.facts2
        p_candidates = []
        if explicit_f and os.path.isfile(explicit_f):
            p_candidates.append(explicit_f)
        p_candidates.extend([
            os.path.join(args.facts_dir or ev, "STATE_R6c_pass%s.tsv" % pas),
            os.path.join(args.facts_dir or ev, "FACTS_R8_M2a4_pass%s.tsv" % pas),
            os.path.join(args.facts_dir or ev, "FACTS_pass%s.tsv" % pas),
            os.path.join(args.facts_dir or ev, "pass%s" % pas, "facts.tsv"),
        ])
        for p in p_candidates:
            if os.path.isfile(p):
                for r in read_table(p):
                    if "kind" in r and "id" in r:
                        facts[(pas, r["kind"], r["id"])] = r
                    if "point_id" in r:
                        facts[(pas, "point", r["point_id"])] = r
                        facts[(pas, r["point_id"])] = r
                break

    rows = []
    verdict = {"1": {}, "2": {}}
    for d in pts:
        pid = d["point_id"]
        if d.get("state_analyzer") in ("-", "", None):
            continue
        cid = ctrl_of.get(pid) or d.get("control_point_id")
        if cid and cid.endswith("-F3"):
            # If -F3 does not exist on disk but -F4 does, adapt to -F4
            f3_exists = any(os.path.isdir(os.path.join(base or ev, "pass1", cid))
                            for base in (args.state_dir, args.dumps_dir, ev))
            if not f3_exists:
                cid_f4 = cid.replace("-F3", "-F4")
                f4_exists = any(os.path.isdir(os.path.join(base or ev, "pass1", cid_f4))
                                for base in (args.state_dir, args.dumps_dir, ev))
                if f4_exists:
                    cid = cid_f4
        ic = int(d["inj_call"]) if d.get("inj_call") not in (None, "", "-") else 1
        rcall = int(d["retry_call"]) if d.get("retry_call") not in (None, "", "-") else RETRY_CALL.get(ic, 2)

        for pas in ("1", "2"):
            fr = facts.get((pas, "point", pid)) or facts.get((pas, pid))

            gdb_candidates = [
                os.path.join(args.state_dir or os.path.join(ev, "state"), "pass" + pas, pid, "gdb.log"),
                os.path.join(args.state_dir or os.path.join(ev, "run"), "pass" + pas, pid, "gdb.log"),
                os.path.join(args.state_dir or ev, "pass" + pas, pid, "gdb.log"),
            ]
            gp = next((p for p in gdb_candidates if os.path.isfile(p)), gdb_candidates[0])

            dump_candidates = [
                os.path.join(args.dumps_dir or os.path.join(ev, "dump"), pid, "pass" + pas),
                os.path.join(args.dumps_dir or os.path.join(ev, "run"), "pass" + pas, pid),
                os.path.join(args.dumps_dir or ev, "pass" + pas, pid),
            ]
            dp = next((p for p in dump_candidates if os.path.isdir(p)), dump_candidates[0])
            outs = read_outs(dp)

            if fr is None or (not os.path.isfile(gp) and not outs):
                verdict[pas][pid] = "UNJUDGED"
                rows.append((d, pas, cid, None, None, None, None, "UNJUDGED"))
                continue

            g = GdbLog(read_text(gp)) if os.path.isfile(gp) else GdbLog("")
            c = None
            if cid and cid not in ("-", "NA"):
                cgdb_candidates = [
                    os.path.join(args.state_dir or os.path.join(ev, "state"), "pass" + pas, "controls", cid, "gdb.log"),
                    os.path.join(args.state_dir or os.path.join(ev, "state"), "pass" + pas, cid, "gdb.log"),
                    os.path.join(args.state_dir or os.path.join(ev, "run"), "pass" + pas, cid, "gdb.log"),
                    os.path.join(args.state_dir or ev, "pass" + pas, cid, "gdb.log"),
                ]
                cgp = next((p for p in cgdb_candidates if os.path.isfile(p)), None)
                if cgp:
                    c = GdbLog(read_text(cgp))

            # (dump_candidates already resolved above)

            couts = {}
            if cid and cid not in ("-", "NA"):
                cdump_candidates = [
                    os.path.join(args.dumps_dir or os.path.join(ev, "dump"), "controls", cid, "pass" + pas),
                    os.path.join(args.dumps_dir or os.path.join(ev, "dump"), cid, "pass" + pas),
                    os.path.join(args.dumps_dir or os.path.join(ev, "run"), "pass" + pas, cid),
                    os.path.join(args.dumps_dir or ev, "pass" + pas, cid),
                ]
                cdp = next((p for p in cdump_candidates if os.path.isdir(p)), cdump_candidates[0])
                couts = read_outs(cdp)

            rc_retry = None
            for key in ("rc%d" % rcall, "gdb_rc%d" % rcall, "rc_retry", "rc3" if rcall == 3 else "rc2"):
                if fr and fr.get(key) not in (None, "None", "", "-", "MISSING"):
                    rc_retry = int(fr[key])
                    break

            res, fl, req = judge_point(d, g, c, outs, couts, rc_retry)
            hit = 0
            for key in ("hit", "gdb_hit", "exp_hit"):
                if fr and fr.get(key) not in (None, "None", "", "-", "MISSING"):
                    hit = int(fr[key])
                    break
            pv = point_verdict(res, hit)
            verdict[pas][pid] = pv
            rows.append((d, pas, cid, res, fl, req, hit, pv))

    flaky = set(pid for pid in verdict["1"] if verdict["1"][pid] != verdict["2"].get(pid))
    cols = ["point_id", "pass", "mode", "route", "inj_call", "request", "NTH_or_K", "M", "k_fail", "k_preretry",
            "k_retry", "retry_call", "control_id", "failing_layer", "req_layer", "I1", "I2", "I3", "I4", "I5", "I6",
            "I7", "hit", "point_verdict", "flaky", "notes"]

    os.makedirs(os.path.dirname(os.path.abspath(out_res)), exist_ok=True)
    with open(out_res, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R6c_STATE.tsv -- P05-S4 R6c-1 judgement of 177 points, passes 1 and 2 (facts only; rules in r6c_judge.py; v2 pre-registration).\n")
        fh.write("# I4 is I4' (U14).  I7 DEFERRED (U9).  point_verdict is per pass; flaky marks a disagreement between passes.\n")
        fh.write("\t".join(cols) + "\n")
        for item in rows:
            d, pas, cid = item[0], item[1], item[2]
            mode = d.get("mode") or d.get("item", "")
            route = d.get("route", "-")
            req_str = d.get("request", "-")
            nth_or_k = d.get("NTH_or_K", "-")
            m_val = d.get("M", "-")
            kf = d.get("k_fail", "-")
            kp = d.get("k_preretry", "-")
            kr = d.get("k_retry", "-")
            rcall = d.get("retry_call", "-")
            ic = d.get("inj_call", "-")

            if item[3] is None:
                fh.write("\t".join([d["point_id"], pas, mode, route, ic, req_str,
                                    nth_or_k, m_val, kf, kp, kr, rcall,
                                    cid or "NA", "NA", "NA"] + ["UNJUDGED"] * 7 + ["NA", "UNJUDGED", "MISSING",
                                    "no run facts"]) + "\n")
                continue
            res, fl, req, hit, pv = item[3], item[4], item[5], item[6], item[7]
            vals = [res[k][0] for k in INV] + [res["I7"][0]]
            notes = " | ".join("%s: %s" % (k, res[k][1]) for k in INV)
            fh.write("\t".join([d["point_id"], pas, mode, route, ic, req_str,
                                nth_or_k, m_val, kf, kp, kr, rcall, cid or "NA",
                                "NA" if fl is None else str(fl), "NA" if req is None else str(req)] + vals +
                               [str(hit), pv, "FLAKY" if d["point_id"] in flaky else "-", notes]) + "\n")

    pv1 = Counter(verdict["1"].values())
    pv2 = Counter(verdict["2"].values())
    with open(out_sum, "w", encoding="utf-8") as fh:
        fh.write("# STATE_SUMMARY_R6c.txt -- computed by state_judge_m2_r8m2d.py from %s\n" % os.path.basename(out_res))
        fh.write("points %d ; FLAKY (pass 1 != pass 2) %d\n" % (len(verdict["1"]), len(flaky)))
        fh.write("point verdict, pass 1: %s\n" % dict(sorted(pv1.items())))
        fh.write("point verdict, pass 2: %s\n" % dict(sorted(pv2.items())))
        fh.write("\nmode\troute\tinj_call\tinvariant\tHOLD\tVIOLATED\tN/A\tUNJUDGED\tDEFERRED\n")
        table = Counter()
        keys = set()
        for item in rows:
            d, pas = item[0], item[1]
            if pas != "1" or item[3] is None:
                continue
            m = d.get("mode") or d.get("item", "")
            r = d.get("route", "-")
            ic = d.get("inj_call", "-")
            keys.add((m, r, ic))
            for k in INV + ("I7",):
                table[(m, r, ic, k, item[3][k][0])] += 1
        for m, r, ic in sorted(keys):
            for k in INV + ("I7",):
                fh.write("%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (
                    m, r, ic, k, table[(m, r, ic, k, "HOLD")], table[(m, r, ic, k, "VIOLATED")],
                    table[(m, r, ic, k, "N/A")], table[(m, r, ic, k, "UNJUDGED")], table[(m, r, ic, k, "DEFERRED")]))
        fh.write("\nFLAKY point ids: %s\n" % (" ".join(sorted(flaky)) if flaky else "none"))
    print("judged points=%d flaky=%d -> %s , %s" % (len(verdict["1"]), len(flaky), out_res, out_sum))
    return 0


if __name__ == "__main__":
    main()
