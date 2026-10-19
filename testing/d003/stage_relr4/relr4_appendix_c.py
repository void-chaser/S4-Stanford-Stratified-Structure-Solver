#!/usr/bin/env python3
# relr4_appendix_c.py -- append appendix C to checkpoints/p05/P05_RELR4_REPORT.md AFTER the formal end gate
# (task brief section 8).  It records the formal gate file and its sha256, the FINAL_STATUS and FAILS count,
# git log -1 and git status --short of the delivered state, and the closing sentence.  It refuses to append twice.
import os, sys, hashlib, subprocess

REPO = os.getcwd()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r4")
REPORT = os.path.join(P05, "P05_RELR4_REPORT.md")
GATE = os.path.join(EV, "GATE_RELR4_end.txt")
TAB = chr(9)
NL = chr(10)
BT = chr(96)


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sh(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True).stdout.strip()


def main():
    rep = open(REPORT, encoding="utf-8").read()
    if "## 附录 C" in rep:
        print("HARD_STOP appendix C already present; it is append-only and never rewritten")
        return 2
    if not os.path.isfile(GATE):
        print("HARD_STOP formal gate file missing: " + GATE)
        return 2
    gate = open(GATE, encoding="utf-8").read()
    facts = {}
    for line in gate.splitlines():
        if line.startswith("COUNTS" + TAB):
            for f in line.split(TAB)[1:]:
                k, _, v = f.partition("=")
                facts[k] = v
        if line.startswith("FAILS="):
            facts["FAILS"] = line.split("=")[1]
        if line.startswith("FINAL_STATUS="):
            facts["FINAL_STATUS"] = line.split("=")[1]
    complete = facts.get("FINAL_STATUS") == "COMPLETE" and facts.get("FAILS") == "0"
    fence = BT + BT + BT
    log1 = sh(["git", "log", "-1", "--format=%H%n%s%n%ci"])
    status = sh(["git", "status", "--short"]) or "(empty)"
    blocks = ["", "## 附录 C 正式 end 门禁结果（门禁后只追加）", "",
              "本附录由 relr4_appendix_c.py 在提交 (i) 之后、按任务书第 8 节正式运行一次 " + BT + "relr4_check.py --phase end" + BT + " 的结果追加；",
              "正式门禁若 FAILS>0 不修、不重跑，照实写 INCOMPLETE。", "",
              "| 项 | 值 |", "|---|---|",
              "| 门禁文件 | checkpoints/p05/evidence/p05-rel-r4/GATE_RELR4_end.txt |",
              "| 门禁文件 sha256 | " + BT + sha_f(GATE) + BT + " |",
              "| 正式门禁计数 | pass=%s fail=%s total=%s |" % (facts.get("pass"), facts.get("fail"), facts.get("total")),
              "| FAILS | %s |" % facts.get("FAILS"),
              "| FINAL_STATUS | %s |" % facts.get("FINAL_STATUS"),
              "| 正式门禁预跑 | GATE_RELR4_pre.txt（同一条只读代码路径，仅 --out 不同） |", "",
              "### C.1 交付状态", "", fence,
              "$ git log -1", log1, "",
              "$ git status --short", status,
              fence, "",
              "### C.2 结论", "",
              ("本轮已完成 P05 交付轮 REL-R4 范围，等待用户审核。" if complete else
               "本轮未完成 P05 交付轮 REL-R4 范围（正式 end 门禁 FAILS=%s，按规则不修、不重跑），等待用户审核。" % facts.get("FAILS")),
              ""]
    open(REPORT, "ab").write((NL.join(blocks)).encode("utf-8"))
    print("appended appendix C; FINAL_STATUS=%s FAILS=%s" % (facts.get("FINAL_STATUS"), facts.get("FAILS")))
    print("REPORT_SHA256=" + sha_f(REPORT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
