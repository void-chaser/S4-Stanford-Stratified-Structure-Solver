#!/usr/bin/env python3
# report_check_r9m3b.py -- check the report: negation-aware forbidden words, required sections, and numeric
# cross-checks recomputed from the round artefacts. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/report_check_r9m3b.py REPORT.md [OUT.txt]
import os, sys, re, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
NL = chr(10)
TAB = chr(9)
FORBIDDEN = ["已修好", "静态可达", "是否签收"]
REQUIRED = ["## 1", "## 2", "## 3", "交付物", "需用户裁决", "等待用户审核"]


def read_tsv(path):
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
    rep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3b_REPORT.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "REPORT_CHECK_R9M3B.txt")
    text = open(rep, encoding="utf-8").read() if os.path.isfile(rep) else ""
    lines = []
    fails = 0

    def chk(name, ok, detail):
        nonlocal fails
        if not ok:
            fails += 1
        lines.append(("%s" % ("PASS" if ok else "FAIL")) + TAB + name + TAB + detail)

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

    facts = []
    rul = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
    if os.path.isfile(rul):
        nums = [int(l.split(TAB)[0][1:]) for l in open(rul, encoding="utf-8")
                if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
        facts.append(("RULINGS_MAX_U", "U%d" % max(nums)))
    err = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
    if os.path.isfile(err):
        ids = re.findall(r"^(E9-\d+)", open(err, encoding="utf-8").read(), re.M)
        facts.append(("ERRATA_LAST_ID", ids[-1]))
        facts.append(("ERRATA_COUNT_TEXT", "共 %d 条" % len(ids)))
    st = os.path.join(REPO, "checkpoints/p05/STATE.md")
    if os.path.isfile(st):
        facts.append(("STATE_BYTES", str(os.path.getsize(st))))
    g = os.path.join(EV, "GATE_R9M3B_start.txt")
    if os.path.isfile(g):
        t = open(g, encoding="utf-8").read()
        m = re.search(r"^FAILS=(\d+)", t, re.M)
        p = re.search(r"COUNTS\tpass=(\d+)", t)
        facts.append(("GATE_START_FAILS", "FAILS=" + (m.group(1) if m else "?")))
        facts.append(("GATE_START_PASS", "PASS=" + (p.group(1) if p else "?")))
    pre = os.path.join(EV, "PREREG_E2E_R9M3B.tsv")
    if os.path.isfile(pre):
        prow = read_tsv(pre)
        facts.append(("PREREG_E2E_POINTS", str(len(prow))))
        shaf = os.path.join(EV, "PREREG_E2E_R9M3B.sha256.txt")
        if os.path.isfile(shaf):
            s = kv(shaf).get("PREREG_E2E_R9M3B.tsv", "")
            if s:
                facts.append(("PREREG_SHA8", s[:8]))
    mkv = os.path.join(EV, "MAKETEST_VERDICT_R9M3B.tsv")
    if os.path.isfile(mkv):
        d = kv(mkv)
        facts.append(("MAKETEST_VERDICT", d.get("verdict", "?")))
        facts.append(("MAKETEST_UNIT_COUNT", d.get("unit_count", "?")))
    cal = os.path.join(EV, "CALIB_E2E_R9M3B.tsv")
    if os.path.isfile(cal):
        facts.append(("CALIB_TARGET_ROWS", str(len([l for l in open(cal, encoding="utf-8") if l.startswith("TARGET")]))))
    au = os.path.join(EV, "AUDIT_R9M3A_R9M3B.tsv")
    if os.path.isfile(au):
        a = read_tsv(au)
        facts.append(("AUDIT_SHU", "%d/%d" % (len([r for r in a if r.get("verdict") == "属实"]), len(a))))
    ver = os.path.join(EV, "E2E_VERDICT_R9M3B.tsv")
    if os.path.isfile(ver):
        cats = {}
        for r in read_tsv(ver):
            cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
        facts.append(("E2E_CATEGORIES", "CONTROL_OK=%d, E2E_OK=%d" % (cats.get("CONTROL_OK", 0), cats.get("E2E_OK", 0))))
    for name, f in (("POSCTRL_E2E", os.path.join(EV, "POSCTRL_E2E_R9M3B.txt")),
                    ("POSCTRL_MAKETEST", os.path.join(EV, "POSCTRL_MAKETEST_R9M3B.txt"))):
        if os.path.isfile(f):
            ls = [l for l in open(f, encoding="utf-8").read().splitlines() if l.startswith("OVERALL_POSITIVE_CONTROL")]
            if ls:
                facts.append((name, ls[-1]))
    reg = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b/SHA256SUMS.txt")
    if os.path.isfile(reg):
        facts.append(("REGISTRY_ITEMS", str(len([l for l in open(reg, encoding="utf-8") if l.strip() and not l.startswith("#")]))))
    for name, value in facts:
        chk("NUM_" + name, value in text, "recomputed=%s present_in_report=%s" % (value, value in text))
    if os.path.isfile(st):
        n = os.path.getsize(st)
        chk("STATE_BYTES_LE_8192", n <= 8192, "bytes=%d" % n)
    body = "# REPORT_CHECK_R9M3B.txt -- report check (forbidden words, sections, numeric cross-checks recomputed from artefacts)" + NL
    body += NL.join(lines) + NL + "FAILS=%d" % fails + NL
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    sys.stdout.write(body)
    return min(fails, 255)


if __name__ == "__main__":
    sys.exit(main())
