#!/usr/bin/env python3
# report_check_r9m3a.py -- check the report: forbidden words (negation aware), required sections, and numeric cross-checks
# recomputed from the round artefacts (the third step that r9m1r4 never reached).
# usage: python3 -I -B testing/d003/stage_s4r9/report_check_r9m3a.py REPORT.md [OUT.txt]
import os, sys, hashlib, re

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
NL = chr(10)
FORBIDDEN = ["已修好", "静态可达", "是否签收"]
REQUIRED = ["## 1", "## 2", "## 3", "交付物", "需用户裁决", "等待用户审核"]
TAB = chr(9)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3a_REPORT.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "REPORT_CHECK_R9M3A.txt")
    text = open(rep, encoding="utf-8").read() if os.path.isfile(rep) else ""
    lines = []
    fails = 0

    def chk(name, ok, detail):
        nonlocal fails
        if not ok:
            fails += 1
        lines.append("%s" % ("PASS" if ok else "FAIL") + TAB + name + TAB + detail)

    # step 1: forbidden words, negation aware (a line is accepted only if the word is inside a "不..." statement)
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

    # step 2: required sections
    missing = [s for s in REQUIRED if s not in text]
    chk("REQUIRED_SECTIONS", not missing, "missing=" + str(missing) if missing else "all present")

    # step 3: numeric cross-checks recomputed from the artefacts
    facts = []
    rul = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
    if os.path.isfile(rul):
        nums = [int(l.split(TAB)[0][1:]) for l in open(rul, encoding="utf-8") if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
        facts.append(("RULINGS_MAX_U", "U%d" % max(nums)))
    err = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
    if os.path.isfile(err):
        ids = re.findall(r"^(E9-\d+)", open(err, encoding="utf-8").read(), re.M)
        facts.append(("ERRATA_LAST_ID", ids[-1]))
        facts.append(("ERRATA_COUNT", str(len(ids))))
    st = os.path.join(REPO, "checkpoints/p05/STATE.md")
    if os.path.isfile(st):
        facts.append(("STATE_BYTES", str(os.path.getsize(st))))
    g = os.path.join(EV, "GATE_R9M3A_start.txt")
    if os.path.isfile(g):
        t = open(g, encoding="utf-8").read()
        m = re.search(r"^FAILS=(\d+)", t, re.M)
        facts.append(("GATE_START_FAILS", m.group(1) if m else "?"))
    pre = os.path.join(EV, "PREREG_E2E_R9M3A.tsv")
    if os.path.isfile(pre):
        rows = [l for l in open(pre, encoding="utf-8") if l.strip() and not l.startswith("#")]
        facts.append(("PREREG_E2E_POINTS", str(len(rows) - 1)))
    au = os.path.join(EV, "AUDIT_R9M1R4_R9M3A_v3.tsv")
    if os.path.isfile(au):
        ok = sum(1 for l in open(au, encoding="utf-8") if l.startswith("J-") and (TAB + "属实" + TAB) in l)
        facts.append(("AUDIT_ITEMS_SHU_SHI", str(ok)))
    reg = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a/SHA256SUMS.txt")
    if os.path.isfile(reg):
        facts.append(("REGISTRY_ITEMS", str(len([l for l in open(reg, encoding="utf-8") if l.strip() and not l.startswith("#")]))))
    for name, value in facts:
        chk("NUM_" + name, value in text, "recomputed=%s present_in_report=%s" % (value, value in text))

    # step 4: state budget
    if os.path.isfile(st):
        n = os.path.getsize(st)
        chk("STATE_BYTES_LE_8192", n <= 8192, "bytes=%d" % n)

    body = "# REPORT_CHECK_R9M3A.txt -- report check (forbidden words, sections, numeric cross-checks)" + NL + NL.join(lines) + NL + "FAILS=%d" % fails + NL
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    sys.stdout.write(body)
    return min(fails, 255)


if __name__ == "__main__":
    sys.exit(main())
