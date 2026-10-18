#!/usr/bin/env python3
# s5r3_appendix.py -- post-gate step: copy the formal end gate summary into registries/s5r3/
# (documented extra, added after the end gate), append its sha256 to the registry SHA256SUMS.txt,
# and write P05_S5R3_GATE_APPENDIX.md by parsing the gate output BY COLUMN NAME (no fixed indices).
import os, sys, subprocess, hashlib, re

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r3")
REG = os.path.join(P05, "registries/s5r3")
GATE = os.path.join(EV, "gate/GATE_S5R3_end.txt")
APP = os.path.join(P05, "P05_S5R3_GATE_APPENDIX.md")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    if not os.path.isfile(GATE):
        print("HARD_STOP end gate output missing")
        return 2
    text = open(GATE, encoding="utf-8").read()
    rows = []
    records = {}
    counts = fails = crashed = None
    for line in text.splitlines():
        if line.startswith("RECORD" + TAB):
            f = line.split(TAB)
            records[f[1]] = f[2].replace("value=", "")
        elif line.startswith("COUNTS"):
            counts = line
        elif line.startswith("FAILS="):
            fails = line
        elif line.startswith(("PASS", "FAIL")):
            f = line.split(TAB)
            d = {"status": f[0], "check": f[1]}
            for x in f[2:]:
                k, _, v = x.partition("=")
                d[k] = v
            rows.append(d)
        elif line.startswith("CHECK_CRASHED="):
            crashed = line
    # column-name driven summaries
    post = [r for r in rows if r["check"].startswith("POST_I_CALL_COUNT")]
    f16 = [r for r in rows if r["check"].startswith("D016_") or r["check"].startswith("PREREG_D016")]
    f2 = [r for r in rows if r["check"].startswith(("E2E_", "PREREG_E2E", "CALIB_"))]
    f3 = [r for r in rows if r["check"].startswith(("MAKETEST_", "FROZEN_POST_I", "FROZEN_SCRIPTS"))]
    others = [r for r in rows if r not in post + f16 + f2 + f3]
    t = ["# P05-S5 R3 正式 end 门禁附录（P05_S5R3_GATE_APPENDIX.md）",
         "",
         "> 由 s5r3_appendix.py 在 end 门禁之后从 $EV/gate/GATE_S5R3_end.txt 按列名解析生成；本文件不手写数字。",
         "> end 门禁正式运行一次；本附录文件与 GATE_S5R3_end.txt 均在 sha_sums 之后追加到 registries/s5r3/（证据目录不再写入）。",
         ""]
    t.append("## 1 总览")
    t.append("")
    for k in ("END_TIME_UTC", "START_TIME_UTC", "COMMIT_I_SHA", "COMMIT_I_SUBJECT", "POST_I_LOG_RECORDS", "STATE_BYTES", "REGISTRY_ITEMS"):
        if k in records:
            t.append("- %s = %s" % (k, records[k]))
    t.append("- " + (counts or "COUNTS missing"))
    t.append("- " + (fails or "FAILS missing"))
    t.append("- " + (crashed or "CHECK_CRASHED missing"))
    t.append("")
    t.append("## 2 分组断言（原文行）")
    for name, grp in (("D016 与预注册", f16), ("E2E 与校准", f2), ("make test / FROZEN", f3), ("其它", others)):
        t.append("")
        t.append("### " + name)
        t.append("")
        for r in grp:
            t.append("- " + TAB.join("%s=%s" % (k, r.get(k, "")) for k in ("status", "check", "expected", "actual")))
    open(APP, "w", encoding="utf-8").write(NL.join(t) + NL)
    # copy the gate output into the registry and append its sha
    os.makedirs(REG, exist_ok=True)
    dst = os.path.join(REG, "GATE_S5R3_end.txt")
    open(dst, "wb").write(open(GATE, "rb").read())
    sums = os.path.join(REG, "SHA256SUMS.txt")
    lines = [l for l in open(sums, encoding="utf-8").read().splitlines() if l.strip()]
    entry = sha_f(dst) + "  GATE_S5R3_end.txt"
    if not any(l.endswith("  GATE_S5R3_end.txt") for l in lines):
        lines.append(entry)
    open(sums, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("APPENDIX written: %s" % os.path.relpath(APP, REPO))
    print("REGISTRY end gate summary appended: %s (entries=%d)" % (os.path.relpath(dst, REPO), len(lines) - 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
