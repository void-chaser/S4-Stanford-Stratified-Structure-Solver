#!/usr/bin/env python3
# relr1_state.py -- add exactly ONE line to section 1 and ONE line to section 2 of checkpoints/p05/STATE.md
# for the P05 delivery round REL-R1 (task brief section 8.3).  It never pre-writes a gate result:
# both lines point to the report's appendix C, and the end gate asserts the file contains no gate-result words.
# The S1-S5 content is not modified.  A second invocation refuses to duplicate the lines.
import os, sys, hashlib, datetime

REPO = os.getcwd()
P05 = os.path.join(REPO, "checkpoints/p05")
STATE = os.path.join(P05, "STATE.md")
NL = chr(10)
TAG = "P05 交付轮 REL-R1"
MARK = "P05_RELR1_REPORT.md"


def main():
    src = open(STATE, encoding="utf-8").read()
    if TAG in src or MARK in src:
        print("HARD_STOP STATE.md already mentions the REL-R1 round; refusing to duplicate")
        return 2
    lines = src.split(NL)
    out = []
    added1 = added2 = False
    sec = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            sec = 1 if line.startswith("## 1") else (2 if line.startswith("## 2") else 3)
        out.append(line)
        if sec == 1 and not added1 and line.startswith("| 当前轮次 |"):
            out.append("| P05 交付轮 | REL-R1（rel-r1；修复后完整原有功能非破坏性验证；不是 P05 新阶段，不改 S1–S5；门禁结果见 P05_RELR1_REPORT.md 附录 C） |")
            added1 = True
        if sec == 2 and not added2 and line.startswith("| S5R7 |"):
            out.append("| REL-R1 | P05 交付轮（rel-r1）：修复后完整原有功能非破坏性验证；各类别计数与例外清单见报告正文，门禁结果见报告附录 C | P05_RELR1_REPORT.md；registries/rel-r1/ |")
            added2 = True
    if not (added1 and added2):
        print("HARD_STOP could not find the insertion anchors in STATE.md")
        return 2
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.append("")
    out.append("（REL-R1 行由 relr1_state.py 于 %s 追加；S1–S5 内容未改）" % utc)
    open(STATE, "w", encoding="utf-8").write(NL.join(out))
    print("STATE.md updated: section 1 row added=%s section 2 row added=%s" % (added1, added2))
    print("SHA256=" + hashlib.sha256(open(STATE, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
