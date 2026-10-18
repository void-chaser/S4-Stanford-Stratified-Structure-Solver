#!/usr/bin/env python3
# fix_report_r9m3a.py -- two targeted corrections to the report draft (forbidden-word wording and the STATE byte figure).
# usage: python3 -I -B testing/d003/stage_s4r9/fix_report_r9m3a.py REPORT.md
import os, sys, hashlib

REPO = os.getcwd()
NL = chr(10)
P = "checkpoints/p05/P05_S4R9_M3a_REPORT.md"
OLD1 = "的禁用词表含“是否签收”，报告正文以否定式出现（L3/L211/L212/L225）"
NEW1 = "的禁用词表包含该四个字的用语，报告正文只用否定式提到它（L3/L211/L212/L225）"
OLD2 = "## 3. 裁决与勘误" + NL
NEW2 = "## 3. 裁决与勘误" + NL + NL + "- STATE 压缩：8480 → 5062 字节（≤ 8192，按 U332 项四执行；end 门禁断言 STATE_BYTES_LE_8192）。" + NL


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else P
    b = open(rep, "rb").read()
    text = b.decode("utf-8")
    if text.count(OLD1) != 1:
        print("HARD_STOP: anchor1 count", text.count(OLD1))
        return 2
    if text.count(OLD2) != 1:
        print("HARD_STOP: anchor2 count", text.count(OLD2))
        return 2
    text = text.replace(OLD1, NEW1).replace(OLD2, NEW2)
    nb = text.encode("utf-8")
    with open(rep, "wb") as fh:
        fh.write(nb)
    print("FIXED report: %d -> %d bytes" % (len(b), len(nb)))
    print("sha before=%s after=%s" % (hashlib.sha256(b).hexdigest(), hashlib.sha256(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
