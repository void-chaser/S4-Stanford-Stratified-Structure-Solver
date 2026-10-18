#!/usr/bin/env python3
# report_check_r9m3c.py -- report check: negation-aware forbidden words, required sections, numeric cross-checks and
# every derived judgement sentence of appendix A recomputed from the source tables. New file (r9m3c).
# usage: report_check_r9m3c.py REPORT.md [OUT.txt]
import os, sys, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M3B = os.path.join(EV, "..", "m3b")
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
TAB = chr(9)
NL = chr(10)
FORBIDDEN = ["已修好", "静态可达", "是否签收"]
REQUIRED = ["## 1", "## 2", "## 3", "交付物", "需用户裁决", "等待用户审核", "附录 A", "附录 B"]


def read_table(path):
    rows = []
    hdr = None
    if not os.path.isfile(path):
        return rows
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def kv(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            out.setdefault(f[0], f[1])
    return out


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3c_REPORT.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "REPORT_CHECK_R9M3C.txt")
    text = open(rep, encoding="utf-8").read() if os.path.isfile(rep) else ""
    lines = []
    fails = 0

    def chk(name, ok, detail):
        nonlocal fails
        if not ok:
            fails += 1
        lines.append(("PASS" if ok else "FAIL") + TAB + name + TAB + detail)

    # forbidden words, negation aware
    bad = []
    for word in FORBIDDEN:
        for i, l in enumerate(text.splitlines(), 1):
            if word in l:
                idx = l.find(word)
                prefix = l[:idx]
                if "不" in prefix[-12:] or "禁止" in prefix[-12:]:
                    continue
                bad.append("%s@L%d" % (word, i))
    chk("FORBIDDEN_WORDS_NEGATION_AWARE", not bad, "none" if not bad else ",".join(bad[:6]))
    missing = [s for s in REQUIRED if s not in text]
    chk("REQUIRED_SECTIONS", not missing, "missing=" + str(missing) if missing else "all present")
    chk("APPENDIX_A_PLACEHOLDER_REPLACED", "APPENDIX_A_PLACEHOLDER" not in text, "placeholder absent")
    # no blank line inside a Markdown table
    rl = text.splitlines()
    split = []
    for i in range(len(rl) - 1):
        if rl[i].startswith("|") and rl[i + 1].strip() == "":
            j = i + 2
            while j < len(rl) and rl[j].strip() == "":
                j += 1
            if j < len(rl) and rl[j].startswith("|"):
                split.append(i + 1)
    chk("NO_BLANK_LINE_INSIDE_TABLES", not split, "none" if not split else str(split[:6]))

    # recomputed facts
    rul = os.path.join(REG, "RULINGS.tsv")
    rul_nums = [int(l.split(TAB)[0][1:]) for l in open(rul, encoding="utf-8")
                if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
    err = os.path.join(REG, "s4r9/ERRATA_9.txt")
    err_txt = open(err, encoding="utf-8").read()
    err_ids = re.findall(r"^(E9-\d+)", err_txt, re.M)
    state_p = sys.argv[3] if len(sys.argv) > 3 else STATE
    state_bytes = os.path.getsize(state_p) if os.path.isfile(state_p) else -1
    gs = open(os.path.join(EV, "GATE_R9M3C_start.txt"), encoding="utf-8").read() if os.path.isfile(os.path.join(EV, "GATE_R9M3C_start.txt")) else ""
    m = re.search(r"^FAILS=(\d+)", gs, re.M)
    p = re.search(r"COUNTS\tpass=(\d+)", gs)
    ver = read_table(os.path.join(M3B, "E2E_VERDICT_R9M3B.tsv"))
    cats = {}
    for r in ver:
        cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
    cmp_txt = open(os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt"), encoding="utf-8").read() if os.path.isfile(os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt")) else ""
    rej_diffs = re.search(r"^DIFFS=(\d+)", cmp_txt, re.M)
    rej_points = re.search(r"^POINTS=(\d+)", cmp_txt, re.M)
    posE = [l for l in open(os.path.join(EV, "POSCTRL_REJUDGE_R9M3C.txt"), encoding="utf-8").read().splitlines()
            if l.startswith("OVERALL_POSITIVE_CONTROL")][-1] if os.path.isfile(os.path.join(EV, "POSCTRL_REJUDGE_R9M3C.txt")) else ""
    posR = [l for l in open(os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3C.txt"), encoding="utf-8").read().splitlines()
            if l.startswith("RESULT:")][-1] if os.path.isfile(os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3C.txt")) else ""
    mk = kv(os.path.join(M3B, "MAKETEST_VERDICT_R9M3B.tsv"))
    rec = [l.rstrip(NL).split(TAB) for l in open(os.path.join(M3B, "MAKETEST_VERDICT_R9M3B.tsv"), encoding="utf-8")
           if l.startswith("reconcile" + TAB)]
    rec_ok = len(rec) == 8 and all(r[-1] == "OK" for r in rec)
    audit = read_table(os.path.join(EV, "AUDIT_R9M3B_R9M3C.tsv"))
    audit_ok = len([r for r in audit if r.get("verdict") == "属实"])
    rdy = read_table(os.path.join(EV, "READINESS_P05_S3S4_R9M3C.tsv"))
    rc = {}
    for r in rdy:
        rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
    hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3C.tsv"))
    red_lines = open(os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv"), encoding="utf-8").read().splitlines() if os.path.isfile(os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv")) else []
    red_rows = len([l for l in red_lines if l and not l.startswith("#")])
    red_open = red_conf = red_norow = 0
    for l in red_lines:
        if l.startswith("# OPEN_IN_SCOPE="):
            red_open = int(l.strip().split("=")[1])
        elif l.startswith("# CONFLICTS:"):
            red_conf = int(re.search(r"(\d+)$", l.strip()).group(1))
        elif l.startswith("# NO_RED_POINT_ROWS="):
            red_norow = int(l.strip().split("=")[1])
    rev_fails = -1
    rev_p = os.path.join(EV, "REVERIFY_R9M3B_R9M3C.tsv")
    if os.path.isfile(rev_p):
        for line in open(rev_p, encoding="utf-8"):
            if line.startswith("# FAILS="):
                rev_fails = int(line.strip().split("=")[1])
    facts = []
    facts.append(("RULINGS_MAX_U", "U%d" % max(rul_nums)))
    facts.append(("ERRATA_LAST_ID", err_ids[-1]))
    facts.append(("ERRATA_COUNT_TEXT", "共 %d 条" % len(err_ids)))
    facts.append(("STATE_BYTES", str(state_bytes)))
    if m and p:
        facts.append(("GATE_START_FAILS", "FAILS=" + m.group(1)))
        facts.append(("GATE_START_PASS", "PASS=" + p.group(1)))
    if cmp_txt:
        facts.append(("REJUDGE_DIFFS", "DIFFS=" + (rej_diffs.group(1) if rej_diffs else "?")))
        facts.append(("REJUDGE_POINTS", "REJUDGE %s 点" % (rej_points.group(1) if rej_points else "?")))
    facts.append(("E2E_CATEGORIES", "CONTROL_OK=%d, E2E_OK=%d" % (cats.get("CONTROL_OK", 0), cats.get("E2E_OK", 0))))
    facts.append(("MAKETEST_VERDICT", "verdict=" + mk.get("verdict", "?")))
    facts.append(("MAKETEST_UNIT_COUNT", "unit_count=" + mk.get("unit_count", "?")))
    facts.append(("AUDIT_SHU", "%d/%d 属实" % (audit_ok, len(audit))))
    facts.append(("READINESS_COUNTS", "MET=%d GAP=%d TRANSFERRED_S5=%d CLOSED_BY_RULING=%d" % (
        rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0))))
    facts.append(("S5_HANDOFF_COUNT", "S5 移交：%d 项" % len(hand)))
    facts.append(("REVERIFY_FAILS", "REVERIFY FAILS=%d" % rev_fails))
    if posE:
        facts.append(("POSCTRL_REJUDGE", posE))
    if posR:
        facts.append(("POSCTRL_REPORT_CHECK", posR))
    for name, value in facts:
        chk("NUM_" + name, value in text, "recomputed=%s present_in_report=%s" % (value, value in text))

    # appendix A derived judgement sentences recomputed from the source tables
    ap_m = re.search(r"### 附录 A.*?(?=### 附录 B|\Z)", text, re.S)
    ap = ap_m.group(0) if ap_m else ""
    chk("APPENDIX_A_PRESENT", bool(ap), "appendix A present")
    recon_phrase = "全部 OK" if rec_ok else "存在 FAIL"
    chk("APPX_RECONCILE_JUDGEMENT", recon_phrase in ap and ("存在 FAIL" not in ap if rec_ok else "全部 OK" not in ap),
        "recomputed reconcile_phrase=%s" % recon_phrase)
    chk("APPX_REJUDGE_DIFFS", ("DIFFS=%s" % (rej_diffs.group(1) if rej_diffs else "?")) in ap,
        "DIFFS=%s" % (rej_diffs.group(1) if rej_diffs else "?"))
    chk("APPX_RULINGS_MAX", ("RULINGS 最大 U%d" % max(rul_nums)) in ap, "U%d" % max(rul_nums))
    chk("APPX_ERRATA", ("ERRATA_9.txt 最后 %s，共 %d 条" % (err_ids[-1], len(err_ids))) in ap, err_ids[-1])
    chk("APPX_STATE_BYTES", ("STATE 最终字节数：%d" % state_bytes) in ap, str(state_bytes))
    chk("APPX_READINESS", ("READINESS 共 %d 行：MET=%d GAP=%d TRANSFERRED_S5=%d CLOSED_BY_RULING=%d" % (
        len(rdy), rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0))) in ap,
        "readiness counts")
    chk("APPX_RED_LEDGER", ("最终红点台账：%d 行（非红点行 %d），范围内仍开放 %d 个；冲突 %d 处" % (
        red_rows, red_norow, red_open, red_conf)) in ap, "red ledger line")
    chk("APPX_S5_HANDOFF", ("S5 移交：%d 项" % len(hand)) in ap, "%d" % len(hand))
    if posE:
        chk("APPX_POSCTRL_REJUDGE", posE in ap, "positive control line")
    chk("STATE_BYTES_LE_8192", state_bytes <= 8192, "bytes=%d" % state_bytes)
    body = "# REPORT_CHECK_R9M3C.txt -- report check (forbidden words, sections, numeric and appendix-A judgement cross-checks)" + NL
    body += NL.join(lines) + NL + "FAILS=%d" % fails + NL
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    sys.stdout.write(body)
    return min(fails, 255)


if __name__ == "__main__":
    sys.exit(main())
