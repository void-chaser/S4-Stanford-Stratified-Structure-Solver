#!/usr/bin/env python3
# s5r4_report_check.py -- self-check of P05_S5R4_REPORT.md (task brief section 6/9). ES5-11 lesson: every
# derived sentence must agree with the source table it cites, not only the numbers. Writes
# REPORT_CHECK_S5R4.txt with FAILS=0 and STATE_BYTES=<final state bytes>.
# usage: s5r4_report_check.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]
import os, sys, re, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
DELIVERABLES = ["GATE_S5R4_start.txt", "PREREG_REJUDGE_S5R4.tsv", "PREREG_REJUDGE_S5R4.tsv.sha256.txt",
                "REJUDGE_S5R4.tsv", "R3_GATE_RECHECK_S5R4.tsv", "READINESS_S5R4.tsv",
                "P05_ACCEPTANCE_MAP_S5R4.tsv", "POSCTRL_REJUDGE_S5R4.txt", "POSCTRL_GATE_S5R4.txt",
                "COPY_DIFF_S5R4.txt", "REGISTRY_APPLY_DIFF_S5R4.txt", "REPORT_CHECK_S5R4.txt",
                "FROZEN_SCRIPTS_S5R4.tsv", "REGISTRY_EXPECTED_S5R4.txt"]


def read_tsv(p, skip_first=("SUMMARY",)):
    rows, hdr = [], None
    if not os.path.isfile(p):
        return rows
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0] or f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def summary_kv(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                d[k] = v
    return d


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_report_check.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    txt = open(os.path.join(P05, "P05_S5R4_REPORT.md"), encoding="utf-8").read()
    st = open(os.path.join(P05, "STATE.md"), "rb").read()
    rej = summary_kv(os.path.join(EV, "REJUDGE_S5R4.tsv"))
    d16 = summary_kv(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"))
    ec = {}
    for r in read_tsv(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")):
        ec[r["verdict"]] = ec.get(r["verdict"], 0) + 1
    mt = {}
    for r in read_tsv(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv")):
        mt[r.get("item", "")] = r.get("value", "")
    r3rows = read_tsv(os.path.join(EV, "R3_GATE_RECHECK_S5R4.tsv"))
    rrows = read_tsv(os.path.join(EV, "READINESS_S5R4.tsv"))
    srec = {}
    for line in open(os.path.join(EV, "GATE_S5R4_start.txt"), encoding="utf-8"):
        if line.startswith("RECORD" + TAB):
            f = line.split(TAB)
            srec[f[1]] = f[2].replace("value=", "")
    fails = []
    lines = ["# REPORT_CHECK_S5R4.txt -- self-check of P05_S5R4_REPORT.md (derived text vs source tables)"]

    def chk(name, cond, detail=""):
        lines.append(("PASS" if cond else "FAIL") + ": " + name + ((" -- " + detail) if detail else ""))
        if not cond:
            fails.append(name)

    chk("REPORT_PRESENT", len(txt) > 4000, "bytes=%d" % len(txt.encode("utf-8")))
    chk("FINAL_STATUS_MARKER", "FINAL_STATUS=PENDING_GATE" in txt)
    chk("APPENDIX_A_PRESENT", "## 附录 A" in txt)
    chk("APPENDIX_B_PRESENT", "## 附录 B" in txt)
    chk("PRE_GATE_CLOSING_SENTENCE", "本轮 P05-S5 R4 范围证据已生成，等待 end 门禁" in txt)
    claims = txt.replace("本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。", "")
    chk("NO_SIGNED_CLAIM", not any(k in claims for k in ("已签收", "P05 完成", "P05-S5 完成")))
    chk("NO_PLACEHOLDER_DIFFS", "DIFFS=?" not in txt)
    # derived rejudge sentence vs REJUDGE SUMMARY
    chk("REJUDGE_E2E_ROWS", ("E2E_ROWS=%s" % rej.get("E2E_ROWS")) in txt, rej.get("E2E_ROWS", "?"))
    chk("REJUDGE_D016_ROWS", ("D016_RECORDED_ROWS=%s D016_REJUDGED_ROWS=%s D016_NOT_JUDGED=%s" % (
        rej.get("D016_RECORDED_ROWS"), rej.get("D016_REJUDGED_ROWS"), rej.get("D016_NOT_JUDGED"))) in txt)
    chk("REJUDGE_DIFFS", ("DIFFS=%s" % rej.get("DIFFS")) in txt, rej.get("DIFFS", "?"))
    # derived D016 / E2E / make test numbers vs R3 tables
    chk("D016_MATCH", ("MATCH=%s" % d16.get("MATCH")) in txt, d16.get("MATCH", "?"))
    chk("E2E_COUNTS", ("E2E_OK=%s" % ec.get("E2E_OK", -1)) in txt and ("CONTROL_OK=%s" % ec.get("CONTROL_OK", -1)) in txt)
    chk("MAKETEST", (mt.get("verdict", "?") in txt) and (("unit_count=%s" % mt.get("unit_count")) in txt))
    # readiness
    chk("READINESS_GAP_TEXT", "GAP=0" in txt)
    chk("READINESS_GAP_SOURCE", sum(1 for r in rrows if r.get("status") == "GAP") == 0)
    # R3 recheck table: 8 rows, all PASS, and every row name appears in the report table
    chk("R3_RECHECK_8_ROWS", len(r3rows) == 8, "rows=%d" % len(r3rows))
    chk("R3_RECHECK_TEXT", all(r.get("fail_name", "") in txt for r in r3rows))
    chk("R3_RECHECK_ALL_PASS_SOURCE", all(r.get("r4_result") == "PASS" for r in r3rows))
    # deliverable count from the registry item list
    m = re.search(r"交付物数量=(\d+)", txt)
    chk("DELIVERABLES_COUNT", bool(m) and int(m.group(1)) == len(DELIVERABLES),
        "report=%s expected=%d" % (m.group(1) if m else "MISSING", len(DELIVERABLES)))
    numbered = [l for l in txt.splitlines() if re.match(r"^\d+\. [A-Za-z0-9_.]+\.(tsv|txt|sha256\.txt)$", l)]
    chk("DELIVERABLES_LISTED", len(numbered) == len(DELIVERABLES), "listed=%d" % len(numbered))
    chk("STATE_UNSIGNED", "未签收" in txt)
    chk("SIGNOFF_V2_REF", "P05_S5_SIGNOFF_DRAFT_v2.md" in txt)
    chk("REGISTRY_COMPLETION_TEXT", "26/26" in txt)
    chk("SHAKEDOWN_TEXT", "CHECK_CRASHED=0" in txt)
    # start constants vs start gate
    chk("START_RULINGS_BYTES", ("RULINGS.tsv %s B" % srec.get("RULINGS_BYTES")) in txt, srec.get("RULINGS_BYTES", "?"))
    chk("START_BASE_HEAD", srec.get("BASE_HEAD", "?")[:16] in txt)
    lines.append("STATE_BYTES=%d" % len(st))
    lines.append("REPORT_BYTES=%d" % len(txt.encode("utf-8")))
    lines.append("FAILS=%d" % len(fails))
    out = os.path.join(EV, "REPORT_CHECK_S5R4.txt")
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for l in lines:
        print(l)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
