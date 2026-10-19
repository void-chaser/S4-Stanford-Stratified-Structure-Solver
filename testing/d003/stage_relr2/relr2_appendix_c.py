#!/usr/bin/env python3
# relr2_appendix_c.py -- append the formal end gate result to checkpoints/p05/P05_RELR2_REPORT.md
# as appendix C (task brief section 7).  Runs AFTER the formal gate; it only appends, it never rewrites
# the body frozen in commit (i).  If the formal gate has FAILS>0 the appendix says INCOMPLETE, as frozen.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r2")
REPORT = os.path.join(P05, "P05_RELR2_REPORT.md")
GATE = os.path.join(EV, "GATE_RELR2_end.txt")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if not os.path.isfile(GATE):
        print("HARD_STOP formal gate file missing: " + os.path.relpath(GATE, REPO))
        return 2
    text = open(REPORT, encoding="utf-8").read()
    if "## 附录 C 正式 end 门禁结果" not in text:
        print("HARD_STOP report has no appendix C heading")
        return 2
    if "### C.1 交付状态" in text:
        print("HARD_STOP appendix C already contains the result; refusing to append twice")
        return 2
    gt = open(GATE, encoding="utf-8").read()
    counts = None
    fails = None
    for line in gt.splitlines():
        if line.startswith("COUNTS" + TAB):
            counts = line.split(TAB)[1:]
        if line.startswith("FAILS="):
            fails = line.split("=", 1)[1]
    if counts is None or fails is None:
        print("HARD_STOP cannot parse the formal gate counts")
        return 2
    final = "COMPLETE" if fails == "0" else "INCOMPLETE"
    glog = subprocess.run(["git", "log", "-1"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    gstat = subprocess.run(["git", "status", "--short"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    if not gstat:
        gstat = "(empty)"
    section = [NL,
               "| 项 | 值 |",
               "|---|---|",
               "| 门禁命令 | `relr2_check.py --phase end`（正式运行一次） |",
               "| 门禁文件 | " + os.path.relpath(GATE, REPO) + " |",
               "| 门禁文件 sha256 | `" + sha_f(GATE) + "` |",
               "| 正式门禁计数 | " + " ".join(counts) + " |",
               "| FAILS | " + fails + " |",
               "| FINAL_STATUS | " + final + " |",
               "| 正式门禁预跑 | GATE_RELR2_pre.txt（同一条只读代码路径，仅 --out 不同） |",
               "",
               "### C.1 交付状态",
               "",
               "```",
               "$ git log -1",
               glog,
               "",
               "$ git status --short",
               gstat,
               "```",
               "",
               "### C.2 结论",
               ""]
    if final == "COMPLETE":
        section.append("本轮已完成 REL-R2 范围，等待用户审核。")
    else:
        section.append("本轮未完成 REL-R2 范围（正式 end 门禁 FAILS=" + fails + "，按冻结规则不修、不重跑，FINAL_STATUS=INCOMPLETE），等待用户审核。")
    out = text.rstrip(NL) + NL + NL.join(section) + NL
    open(REPORT, "w", encoding="utf-8").write(out)
    print("APPENDED appendix C: FINAL_STATUS=" + final + " FAILS=" + fails)
    print("REPORT_SHA256=" + sha_f(REPORT))
    return 0 if final == "COMPLETE" else 0


if __name__ == "__main__":
    sys.exit(main())
