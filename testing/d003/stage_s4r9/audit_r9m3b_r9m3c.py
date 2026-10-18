#!/usr/bin/env python3
# audit_r9m3b_r9m3c.py -- re-verify the planner's L-1..L-6 claims against the original files. Every line number
# is computed from the file; the task-book line numbers are not copied. New file (r9m3c).
# usage: audit_r9m3b_r9m3c.py OUT.tsv
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
TAB = chr(9)
NL = chr(10)
REPORT = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3b_REPORT.md")
CLOSEOUT = os.path.join(REPO, "testing/d003/stage_s4r9/closeout_report_state_r9m3b.py")
GATE = os.path.join(REPO, "testing/d003/stage_s4r9/gate_check_r9m3b_v3.py")
MKV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/MAKETEST_VERDICT_R9M3B.tsv")
PREREG = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/PREREG_E2E_R9M3B.tsv")
FROZEN = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/FROZEN_SCRIPTS_R9M3B.tsv")
LEDGER = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b/LEDGER_CHECK_R9M3B.tsv")
RULINGS = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
REPORTCHECK = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/REPORT_CHECK_R9M3B.txt")


def lines(path):
    return open(path, encoding="utf-8").read().splitlines()


def find(lines_, needle):
    return [(i, l) for i, l in enumerate(lines_, 1) if needle in l]


def read_table(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def l1():
    rep = lines(REPORT)
    hits = find(rep, "4 遍 × 2 段对账")
    ok = len(hits) == 1
    ln, txt = hits[0] if hits else (None, "")
    says_fail = "存在 FAIL" in txt
    # the four listed rows' last column in the appendix sentence
    rows = [r for r in read_table(MKV) if r.get("item") == "reconcile"]
    # find the actual column where OK lives in a reconcile raw row
    raw = [l.rstrip(NL).split(TAB) for l in open(MKV, encoding="utf-8") if l.startswith("reconcile" + TAB)]
    ok_idx = None
    if raw:
        ok_idx = raw[0].index("OK") if "OK" in raw[0] else None
    last_ok = all(r[-1] if False else (l.rstrip(NL).split(TAB)[-1] == "OK") for l in open(MKV, encoding="utf-8") if l.startswith("reconcile" + TAB))
    co = find(lines(CLOSEOUT), "recon_bad")
    co_ln, co_txt = co[0] if co else (None, "")
    uses_r6 = "r[6]" in co_txt
    rc = lines(REPORTCHECK)
    fails = [l for l in rc if l.startswith("FAILS=")]
    fails_v = fails[-1] if fails else "MISSING"
    fact = ("appendix-A make-test sentence at report L%s says 存在 FAIL=%s; the 8 reconcile rows' last column is OK=%s; "
            "closeout recon_bad at L%s uses r[6]=%s; actual OK column index in the raw reconcile row is %s (r[6]=%s); "
            "REPORT_CHECK_R9M3B.txt last line %s" % (ln, says_fail, last_ok, co_ln, uses_r6, ok_idx,
                                                       (raw[0][6] if raw else "?"), fails_v))
    verdict = "属实" if (ln and says_fail and last_ok and uses_r6 and ok_idx == 7 and fails_v == "FAILS=0") else "规划者事实有误"
    refs = "P05_S4R9_M3b_REPORT.md:%s; MAKETEST_VERDICT_R9M3B.tsv reconcile rows; closeout_report_state_r9m3b.py:%s; REPORT_CHECK_R9M3B.txt" % (ln, co_ln)
    return ("L-1", verdict, fact, refs)


def l2():
    g = lines(GATE)
    hits = find(g, "sha_sums_r9m3b.py")
    ln, txt = hits[0] if hits else (None, "")
    frozen = read_table(FROZEN)
    names = [r.get("path", "") for r in frozen if "sha_sums" in os.path.basename(r.get("path", ""))]
    fname = os.path.basename(names[0]) if names else "MISSING"
    hard = bool(re.search(r"sha_sums_r9m3b\.py", txt))
    fact = ("gate_check_r9m3b_v3.py L%s hardcodes sha_sums_r9m3b.py (%s); FROZEN lists %s" % (ln, hard, fname))
    verdict = "属实" if (hard and fname == "sha_sums_r9m3b_v2.py") else "规划者事实有误"
    return ("L-2", verdict, fact, "gate_check_r9m3b_v3.py:%s; FROZEN_SCRIPTS_R9M3B.tsv path=%s" % (ln, fname))


def table_gap_start(rep, heading, header_prefix):
    """return (heading_line, blank_line, data_rows_before_blank) for the first table after heading."""
    h = None
    for i, l in enumerate(rep, 1):
        if l.startswith(heading):
            h = i
            break
    if h is None:
        return (None, None, 0)
    j = h
    while j < len(rep) and not rep[j].startswith(header_prefix):
        if rep[j].startswith("## ") or rep[j].startswith("### ") and j > h:
            break
        j += 1
    if j >= len(rep) or not rep[j].startswith(header_prefix):
        return (h, None, 0)
    k = j + 2  # skip header and separator
    n = 0
    while k < len(rep):
        if rep[k].strip() == "":
            return (h, k + 1, n)
        if not rep[k].startswith("|"):
            return (h, None, n)
        n += 1
        k += 1
    return (h, None, n)


def l3():
    rep = lines(REPORT)
    h9, b9, n9 = table_gap_start(rep, "## 9.", "| 序号")
    h12, b12, n12 = table_gap_start(rep, "### 12.2", "| # |")
    fact = ("section 9 table starts L%s, first blank line inside the table at L%s after %d data rows; "
            "section 12.2 table starts L%s, first blank at L%s after %d data rows (claim: blank before row 5 and row 8)"
            % (h9, b9, n9, h12, b12, n12))
    verdict = "属实" if (n9 == 4 and n12 == 7) else "规划者事实有误"
    return ("L-3", verdict, fact, "P05_S4R9_M3b_REPORT.md:%s; P05_S4R9_M3b_REPORT.md:%s" % (b9, b12))


def l4():
    rep = lines(REPORT)
    h = None
    for i, l in enumerate(rep, 1):
        if l.startswith("## 13."):
            h = i
            break
    items = []
    if h:
        for i in range(h, len(rep)):
            m = re.match(r"^(\d+)\.\s+(.*)$", rep[i])
            if m:
                items.append((int(m.group(1)), i + 1, m.group(2)))
            if rep[i].startswith("## ") and i + 1 > h:
                break
    item5 = [x for x in items if x[0] == 5]
    i5_ln, i5_txt = (item5[0][1], item5[0][2]) if item5 else (None, "")
    ab = [i for i, l in enumerate(rep, 1) if "附录 B" in l]
    endg = find(rep, "EVIDENCE_SHA256SUMS_OK")
    eg_ln = endg[0][0] if endg else None
    # the end-gate defect must appear only in appendix B (after its heading)
    only_ab = eg_ln is not None and ab and eg_ln > ab[0]
    concern_m3a = ("M3a" in i5_txt) or ("更正件" in i5_txt)
    fact = ("report §13 item 5 at L%s concerns M3a gate correction=%s (text: %s); appendix B starts L%s; "
            "end-gate defect EVIDENCE_SHA256SUMS_OK appears at L%s and only in appendix B=%s; the executor chat summary is not in the repository"
            % (i5_ln, concern_m3a, i5_txt[:80], ab[0] if ab else None, eg_ln, only_ab))
    verdict = "属实" if (item5 and concern_m3a and only_ab) else "规划者事实有误"
    return ("L-4", verdict, fact, "P05_S4R9_M3b_REPORT.md:%s; P05_S4R9_M3b_REPORT.md:%s" % (i5_ln, eg_ln))


def l5():
    led = read_table(LEDGER)
    lns = lines(LEDGER)
    rows = {r.get("ledger_id"): r for r in led}
    r1 = rows.get("RP-R8-M2c-1")
    r1b = rows.get("RP-R8-M2c-1b")
    d1 = (r1 or {}).get("destination", "")
    says_pending = "待用户裁决是否关闭" in d1
    b_no = (r1b or {}).get("state_has_row") == "NO"
    ln1 = [i for i, l in enumerate(lns, 1) if l.startswith("RP-R8-M2c-1" + TAB)]
    ln1b = [i for i, l in enumerate(lns, 1) if l.startswith("RP-R8-M2c-1b" + TAB)]
    rul = [l for l in open(RULINGS, encoding="utf-8") if l.startswith("U304" + TAB)]
    u304 = rul[0].split(TAB)[2] if rul else "MISSING"
    st = lines(STATE)
    st_hit = [(i, l) for i, l in enumerate(st, 1) if "RP-R8-M2c-1/1b" in l]
    st_ln = st_hit[0][0] if st_hit else None
    fact = ("LEDGER_CHECK L%s RP-R8-M2c-1 destination says 待用户裁决是否关闭=%s; L%s RP-R8-M2c-1b state_has_row=NO=%s; "
            "U304 summary=%s; STATE uses the merged id RP-R8-M2c-1/1b at L%s"
            % (ln1[0] if ln1 else None, says_pending, ln1b[0] if ln1b else None, b_no, u304, st_ln))
    verdict = "属实" if (says_pending and b_no and "关闭" in u304 and st_ln) else "规划者事实有误"
    return ("L-5", verdict, fact, "LEDGER_CHECK_R9M3B.tsv:%s,%s; RULINGS.tsv U304; STATE.md:%s" % (ln1[0] if ln1 else None, ln1b[0] if ln1b else None, st_ln))


def l6():
    rows = read_table(PREREG)
    out = []
    bad = False
    for fe in ("py", "lua_batch", "lua_repl"):
        for spec in ("jones", "nv", "exp"):
            n = len([r for r in rows if r.get("frontend") == fe and r.get("spec") == spec])
            out.append("%s/%s=%d" % (fe, spec, n))
    lr = [r for r in rows if r.get("frontend") == "lua_repl"]
    lr_specs = sorted(set(r.get("spec") for r in lr))
    lr_inj = [r for r in lr if r.get("is_control") == "NO"]
    claim_ok = (len([r for r in lr if r.get("spec") in ("jones", "nv", "exp")]) == 0) and (len(lr_inj) == 4)
    fact = ("per frontend x spec counts: " + ", ".join(out) + "; lua_repl specs=" + ",".join(lr_specs)
            + " lua_repl injection rows=%d; claim (no jones/nv/exp REPL rows) holds=%s" % (len(lr_inj), claim_ok))
    verdict = "属实" if claim_ok else "规划者事实有误"
    return ("L-6", verdict, fact, "PREREG_E2E_R9M3B.tsv frontend/spec columns")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "AUDIT_R9M3B_R9M3C.tsv")
    rows = [l1(), l2(), l3(), l4(), l5(), l6()]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# AUDIT_R9M3B_R9M3C.tsv -- planner L-1..L-6 re-verification; line numbers computed from the original files" + NL)
        fh.write(TAB.join(["item", "verdict", "computed_fact", "file_line_refs"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    for r in rows:
        print(TAB.join([r[0], r[1]]))
    print("SHU=%d/%d" % (len([r for r in rows if r[1] == "属实"]), len(rows)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
