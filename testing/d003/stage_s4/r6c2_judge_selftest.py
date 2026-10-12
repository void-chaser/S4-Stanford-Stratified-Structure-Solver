#!/usr/bin/env python3
# r6c2_judge_selftest.py -- P05-S4 R6c2-1 (U19): offline unit test of the judge r6c_judge.py (new file).
#
# NOT a run of S4.  NOT a sandbox probe.  It takes REAL gdb logs of 177-point rows (state/pass1) and their control logs,
# makes corrupted COPIES of the text (in-memory, and written only under EVDIR/selftest/), and calls the judge's own
# functions (imported from r6c_judge.py; nothing is copied or rewritten).  The original files are read, never written.
#
# Expected results are written BEFORE the judgement to EVDIR/SELFTEST_EXPECT_R6c2.tsv (with its sha256).  For each
# corrupted example the invariant named in the expectation must be VIOLATED and the point verdict VIOLATED.  For each
# unmodified original row the point verdict must be HOLD.  A failing example is a judge defect: the script reports it and
# exits 1.  The judge is NEVER edited to make the self-test pass (brief section 3).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_judge_selftest.py EVDIR
import hashlib
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r6c_judge as JU  # noqa: E402  (imported, not copied)

REPO = JU.REPO
STATE_TSV = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c", "STATE_R6c_pass1.tsv")
RESULTS_TSV = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c", "RESULTS_R6c_STATE.tsv")
PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c", "REGISTRY_S4_PRE_R6b_STATE_v2.tsv")
CONTROL = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6b", "REGISTRY_S4_PRE_R6b_CONTROL.tsv")
EV_STATE = None  # set from argv: the evidence directory holding state/ and dump/


def read_text(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def find_row(prereg_rows, pid):
    for d in prereg_rows:
        if d["point_id"] == pid:
            return d
    raise SystemExit("selftest: point %s not in prereg" % pid)


def control_of(ctrl_rows, pid):
    for c in ctrl_rows:
        if pid in [x for x in c["points_served"].split(";") if x]:
            return c
    return None


def gdb_text(ev, pid, pas="1"):
    return read_text(os.path.join(ev, "state", "pass" + pas, pid, "gdb.log"))


def ctrl_text(ev, cid, pas="1"):
    return read_text(os.path.join(ev, "state", "pass" + pas, "controls", cid, "gdb.log"))


def outs_of(ev, pid, pas="1"):
    return JU.read_outs(os.path.join(ev, "dump", pid, "pass" + pas))


def couts_of(ev, cid, pas="1"):
    return JU.read_outs(os.path.join(ev, "dump", "controls", cid, "pass" + pas))


def judge(d, gtext, ctext, outs, couts, rc_retry):
    """Run the judge's own judge_point on given texts.  Returns (res, fl, req)."""
    g = JU.GdbLog(gtext)
    c = JU.GdbLog(ctext) if ctext is not None else None
    return JU.judge_point(d, g, c, outs, couts, rc_retry)


def replace_line(text, old, new, count=1):
    """Replace the first `count` occurrences of an exact line.  Fails if the line is absent (corruption must hit)."""
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln == old]
    if len(hits) < count:
        raise SystemExit("selftest: corruption target line not found: %r" % old)
    for i in hits[:count]:
        lines[i] = new
    return "\n".join(lines)


def insert_after(text, anchor, new_line):
    lines = text.split("\n")
    idx = [i for i, ln in enumerate(lines) if ln == anchor]
    if not idx:
        raise SystemExit("selftest: anchor not found: %r" % anchor)
    lines.insert(idx[0] + 1, new_line)
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: r6c2_judge_selftest.py EVDIR")
    ev = argv[1]
    sdir = os.path.join(ev, "selftest_v2")  # run 1 wrote os.path.join(ev, "selftest"); not overwritten (U17)
    os.makedirs(sdir, exist_ok=True)
    # v2 names: run 1 (no notes column, structurally defective script) keeps SELFTEST_EXPECT_R6c2.tsv and
    # SELFTEST_R6c2.tsv; this run writes the _v2 files (U17: no overwrite).
    expect_path = os.path.join(ev, "SELFTEST_EXPECT_R6c2_v2.tsv")
    result_path = os.path.join(ev, "SELFTEST_R6c2_v2.tsv")
    if os.path.exists(expect_path) or os.path.exists(result_path):
        raise SystemExit("REFUSED: self-test files exist; never overwritten (U17)")

    prereg = JU.read_table(PREREG)
    ctrls = JU.read_table(CONTROL)
    # STATE_R6c_pass1.tsv: columns kind, id, ...; point rows have kind == "point" and id == point_id
    state = {r["id"]: r for r in JU.read_table(STATE_TSV) if r.get("kind") == "point"}
    # real points used for the corruptions (chosen by id; each one exists in the prereg and in the state table)
    P_LAYER1 = "M-once-closed1d-malloc-1"     # once, inj 1, closed1d (no PolBasis): I1, I2, I4 (solved@k_fail=0), I5, I6
    P_TWICE2 = None                           # twice, inj 2: I4' (b) branch (solved@k_fail = 1); chosen below
    P_JONES = "M-once-jones-exec-1"           # PolBasis, once, inj 1: I3 (field cache)
    for d in prereg:
        if d["point_id"].startswith("M-twice-") and d["inj_call"] == "2":
            P_TWICE2 = d["point_id"]
            break
    for pid in (P_LAYER1, P_TWICE2, P_JONES):
        if pid is None or pid not in state:
            raise SystemExit("selftest: real point missing: %s" % pid)

    examples = []   # (label, point_id, corruption, invariant that must be VIOLATED, expect_note)

    # ---- originals first: every real row must be HOLD (the control of the judgement) ----
    originals = []
    for pid in (P_LAYER1, P_JONES, P_TWICE2):
        d = find_row(prereg, pid)
        c = control_of(ctrls, pid)
        cid = c["control_id"] if c else None
        rc_retry = _rc_retry(state[pid], d)
        res, fl, req = judge(d, gdb_text(ev, pid), ctrl_text(ev, cid) if cid else None,
                             outs_of(ev, pid), couts_of(ev, cid) if cid else {}, rc_retry)
        originals.append((pid, res))

    # ---- corrupted examples ----
    corruptions = []

    # I1: failing layer modes_null at k_fail set to 0 (layer 1 at k_fail = 1)
    d = find_row(prereg, P_LAYER1)
    g = gdb_text(ev, P_LAYER1)
    g_bad = replace_line(g, "R6BSTATE 1 layer 1 modes_null 1 q_len NA q_sha256 NA",
                         "R6BSTATE 1 layer 1 modes_null 0 q_len 18 q_sha256 cde5cf822f5e45519d9f82227524f26a1562aed685452ec59f25bbaa9d81987b")
    corruptions.append(("I1-a", P_LAYER1, "k_fail(1) layer 1 modes_null 1 -> 0", "I1", g_bad, None, d))

    # I2 (a): a kept layer's q hash differs from the control at k_fail.  Kept layer = layer 0 (installed at k_fail).
    g_bad = replace_line(g, "R6BSTATE 1 layer 0 modes_null 0 q_len 18 q_sha256 66aeac42a4865249856747b3743025aefcd8e2934803daac67974d430c410ab8",
                         "R6BSTATE 1 layer 0 modes_null 0 q_len 18 q_sha256 0000000000000000000000000000000000000000000000000000000000000000")
    corruptions.append(("I2-a", P_LAYER1, "k_fail kept layer 0 q hash changed (differs from control)", "I2", g_bad, None, d))

    # I2 (b): the control does not have the kept layer installed at k_fail (control layer 0 set to uninstalled).
    cid = control_of(ctrls, P_LAYER1)["control_id"]
    ctrl = ctrl_text(ev, cid)
    ctrl_bad = replace_line(ctrl, "R6BSTATE 1 layer 0 modes_null 0 q_len 18 q_sha256 66aeac42a4865249856747b3743025aefcd8e2934803daac67974d430c410ab8",
                            "R6BSTATE 1 layer 0 modes_null 1 q_len NA q_sha256 NA")
    corruptions.append(("I2-b", P_LAYER1, "control layer 0 not installed at k_fail (condition b)", "I2", g, ctrl_bad, d))

    # I3: a field-cache node at k_fail that the control does not have (PolBasis point)
    d = find_row(prereg, P_JONES)
    g = gdb_text(ev, P_JONES)
    g_bad = insert_after(g, "R6BSTATE 1 cache_count 0 cache_layers none",
                         "R6BSTATE 1 cache node 0 layer 1 n 9 plen 342 P_sha256 1111111111111111111111111111111111111111111111111111111111111111")
    corruptions.append(("I3-a", P_JONES, "k_fail extra cache node not in control", "I3", g_bad, None, d))

    # I3 (b): the node exists in both, but its P hash differs from the control's node at k_fail
    g_bad = insert_after(g, "R6BSTATE 1 cache_count 0 cache_layers none",
                         "R6BSTATE 1 cache node 0 layer 1 n 9 plen 342 P_sha256 2222222222222222222222222222222222222222222222222222222222222222")
    corruptions.append(("I3-b", P_JONES, "k_fail cache node P hash differs from control", "I3", g_bad, None, d))

    # I4' (a): solved[req] changes from 0 (k_before) to 1 at k_fail for a once/inj1 point (req layer 1)
    d = find_row(prereg, P_LAYER1)
    g_bad = replace_line(g_for(ev, P_LAYER1), "R6BSTATE 1 solution solved 0=0 1=0 2=0",
                         "R6BSTATE 1 solution solved 0=0 1=1 2=0")
    corruptions.append(("I4-a", P_LAYER1, "solved[req] 0 at k_before, 1 at k_fail (I4' (a))", "I4", g_bad, None, d))

    # I4' (b): twice/inj2 point (real data: solved@k_fail(=3) for layer 1 is 1, and the request layer 1 has modes_null 1 at k=3).
    # The real row is HOLD (I4' (b): modes NULL forces the recomputation).  The corruption sets the request layer's
    # modes_null at k_fail to 0 while solved[req]@k_fail stays 1: then the forced recomputation is absent -> VIOLATED.
    d = find_row(prereg, P_TWICE2)
    gt = gdb_text(ev, P_TWICE2)
    gl = JU.GdbLog(gt)
    req_idx = gl.req_idx(2)
    if req_idx is None or gl.solved.get(3, {}).get(req_idx) != 1:
        raise SystemExit("selftest: P_TWICE2 does not show solved@k_fail=1 for the request layer (I4' (b) branch absent)")
    if gl.layers.get((3, req_idx), (None,))[0] != 1:
        raise SystemExit("selftest: P_TWICE2 request layer is not NULL at k_fail in the real row")
    g_bad2 = replace_line(gt, "R6BSTATE 3 layer %d modes_null 1 q_len NA q_sha256 NA" % req_idx,
                          "R6BSTATE 3 layer %d modes_null 0 q_len 18 q_sha256 cde5cf822f5e45519d9f82227524f26a1562aed685452ec59f25bbaa9d81987b" % req_idx)
    corruptions.append(("I4-b", P_TWICE2, "solved@k_fail=1 and request layer modes_null 1 -> 0 at k_fail", "I4",
                        g_bad2, None, d))

    # I5 (a): a layer enters ComputeLayerModes twice in the retry interval (k_pre..k_retry)
    d = find_row(prereg, P_LAYER1)
    g = gdb_text(ev, P_LAYER1)
    g_bad = insert_after(g, "R6BCLM ENTER idx 2 name Below", "R6BCLM ENTER idx 2 name Below")
    corruptions.append(("I5-a", P_LAYER1, "layer 2 enters ComputeLayerModes twice in the retry interval", "I5", g_bad, None, d))

    # I5 (b): the retry interval enters a layer that was installed at k_pre (layer 0; modes_null 0 at k_pre = 2)
    g_bad = insert_after(g, "R6BCLM ENTER idx 2 name Below", "R6BCLM ENTER idx 0 name Above")
    corruptions.append(("I5-b", P_LAYER1, "retry enters layer 0 that was installed at k_pre", "I5", g_bad, None, d))

    # I5 (c): retry rc != 0 (the R6CALLS/RC retry fact is passed as rc_retry; corrupt that fact)
    corruptions.append(("I5-c", P_LAYER1, "retry rc 1 instead of 0", "I5", None, None, d, None, 1))

    # I6: the retry output differs by one byte (call 2 of the point's dump)
    d = find_row(prereg, P_LAYER1)
    outs_bad = dict(outs_of(ev, P_LAYER1))
    b = outs_bad.get(2, b"")
    if not b:
        raise SystemExit("selftest: call2 output empty for %s" % P_LAYER1)
    ch = bytes([(b[0] ^ 0x01)]) + b[1:]
    outs_bad[2] = ch
    corruptions.append(("I6-a", P_LAYER1, "retry output (call 2) changed by one byte", "I6", None, None, d,
                        outs_bad, None))

    # normalise every corruption to 9 fields: (label, pid, desc, inv, gtxt, ctxt, d, outs_override, rc_override)
    norm = []
    for c in corruptions:
        c = list(c)
        while len(c) < 9:
            c.append(None)
        norm.append(tuple(c))
    corruptions = norm

    # ----- expectations written BEFORE the judgement (sha256 recorded) -----
    exp_lines = ["# SELFTEST_EXPECT_R6c2_v2.tsv -- expected judge results, written BEFORE judgement (U19, R6c2-1).",
                 "# Each corrupted example: the named invariant must be VIOLATED and the point verdict VIOLATED.",
                 "# Each original row: point verdict HOLD (I3 N/A/HOLD allowed; I7 DEFERRED).",
                 "example\tpoint_id\tcorruption\tmust_violate\texpect_point_verdict",
                 ]
    for label, pid, desc, inv, *_ in corruptions:
        exp_lines.append("\t".join([label, pid, desc, inv, "VIOLATED"]))
    for pid, _res in originals:
        exp_lines.append("\t".join(["ORIG", pid, "unmodified original row", "-", "HOLD"]))
    exp_text = "\n".join(exp_lines) + "\n"
    with open(expect_path, "w", encoding="utf-8") as fh:
        fh.write(exp_text)
    exp_sha = sha256_text(exp_text)
    with open(os.path.join(ev, "SELFTEST_EXPECT_R6c2_v2.sha256"), "w", encoding="utf-8") as fh:
        fh.write("%s  SELFTEST_EXPECT_R6c2_v2.tsv\n" % exp_sha)

    # ----- judgement with the judge's own functions -----
    rows = []
    fails = []
    for pid, res in originals:
        d = find_row(prereg, pid)
        pv = JU.point_verdict(res, 1)
        ok = (pv == "HOLD")
        rows.append(["ORIG", pid, "-", "-", pv, "HOLD", "OK" if ok else "FAIL"] +
                    [res[k][0] for k in JU.INV] + [notes_of(res)])
        if not ok:
            fails.append(("ORIG", pid, pv))
    for label, pid, desc, inv, gtxt, ctxt, d, outs_override, rc_override in corruptions:
        if gtxt is None:
            gtxt = gdb_text(ev, pid)
        cid = control_of(ctrls, pid)
        if ctxt is None and cid is not None:
            ctxt = ctrl_text(ev, cid["control_id"])
        rc_retry = rc_override if rc_override is not None else _rc_retry(state[pid], d)
        couts = couts_of(ev, cid["control_id"]) if cid else {}
        outs = outs_override if outs_override is not None else outs_of(ev, pid)
        res, fl, req = judge(d, gtxt, ctxt, outs, couts, rc_retry)
        pv = JU.point_verdict(res, 1)
        got_inv = res[inv][0]
        ok = (got_inv == "VIOLATED" and pv == "VIOLATED")
        rows.append([label, pid, desc, inv, pv, "VIOLATED", "OK" if ok else "FAIL"] +
                    [res[k][0] for k in JU.INV] + [notes_of(res)])
        if not ok:
            fails.append((label, pid, got_inv + "/" + pv))
        # write the corrupted text under EV/selftest/ (copy only, never the original)
        tag = label.replace("/", "_")
        with open(os.path.join(sdir, tag + "_gdb.log"), "w", encoding="utf-8") as fh:
            fh.write(gtxt)

    cols = ["example", "point_id", "corruption", "must_violate", "point_verdict", "expect_point_verdict", "check",
            "I1", "I2", "I3", "I4", "I5", "I6", "notes"]
    with open(result_path, "w", encoding="utf-8") as fh:
        fh.write("# SELFTEST_R6c2_v2.tsv -- judge self-test result (U19, run 2).  Judge functions imported from r6c_judge.py.\n")
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        n_ex = len(corruptions)
        n_ok_ex = sum(1 for r in rows if r[0] != "ORIG" and r[6] == "OK")
        n_ok_orig = sum(1 for r in rows if r[0] == "ORIG" and r[6] == "OK")
        fh.write("# summary: corrupted examples %d ; the named invariant VIOLATED and point VIOLATED in %d ; "
                 "originals HOLD %d of %d ; failures %d\n" % (n_ex, n_ok_ex, n_ok_orig, len(originals), len(fails)))
    print("selftest: examples=%d failures=%d -> %s" % (len(corruptions), len(fails), result_path))
    if fails:
        for f in fails:
            print("FAIL %s" % (f,))
        return 1
    return 0


def g_for(ev, pid):
    return gdb_text(ev, pid)


def notes_of(res):
    """The judge's own notes for each invariant (text returned by judge_point), joined for the result table."""
    return " | ".join("%s: %s" % (k, res[k][1]) for k in JU.INV)


def _rc_retry(srow, d):
    """Retry rc from the gdb-run facts of the state table (same rule as r6c_judge.main)."""
    ic = int(d["inj_call"])
    key = "gdb_rc2" if ic == 1 else "gdb_rc3"
    v = srow[key]
    return None if v in ("None", "") else int(v)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
