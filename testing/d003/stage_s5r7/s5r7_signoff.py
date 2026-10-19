#!/usr/bin/env python3
# s5r7_signoff.py -- P05-S5 R7 task brief section 2.1: write checkpoints/p05/P05_S5_SIGNOFF.md.
# The user gave the P05-S5 sign-off text in the conversation (task brief section 1); this script records it
# verbatim.  Section 2 is built from s5r7_signoff_text.txt and asserted byte-equal to it (same sha256).
# It also writes the evidence table SIGNON_S5R7.tsv.  Nothing else is touched.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
TEXTFILE = os.path.join(REPO, "testing/d003/stage_s5r7/s5r7_signoff_text.txt")
OUT = os.path.join(P05, "P05_S5_SIGNOFF.md")
TAB = chr(9)
NL = chr(10)

EXP_TEXT_BYTES = 1063
EXP_TEXT_SHA = "c7af2fb22c9cc9f9ec04d4bfb83cce73478b0a2019ce951f12b1c0804df3f65e"

HEAD = """# P05-S5 签收记录

> 本文件只记录用户在对话中给出的 P05-S5 签收原文。它不包含任何新的验证结果，不改写任何历史报告。
> 签收原文见 §2（逐字照录，sha256 %s）；P05 随 S5 签收收口。本文件由执行者依据用户授权写入。

## 1 签收表

| 阶段 | 状态 | 签收依据 | 日期 |
|---|---|---|---|
| P05-S1 | 已由用户签收 | 用户在对话中授权（基于 S1R2、S3R2 之后的结果） | 2026-10-11 |
| P05-S2 | 已由用户签收 | 用户在对话中授权（基于 S1R2、S3R2 之后的结果） | 2026-10-11 |
| P05-S3 | 已由用户签收 | 用户在对话中给出签收原文（P05_S3_S4_SIGNOFF.md §2） | 2026-10-18 |
| P05-S4 | 已由用户签收 | 用户在对话中给出签收原文（P05_S3_S4_SIGNOFF.md §2） | 2026-10-18 |
| P05-S5 | 已由用户签收 | 用户在对话中给出签收原文（见 §2） | 2026-10-19 |

## 2 范围声明（签收原文，逐字照录）

"""

TAIL = """
## 3 对后续的含义

- P05 五个正式阶段（S1–S5）全部由用户在对话中签收；本轮只把用户给出的 P05-S5 签收原文入账，执行者未自行宣布任何阶段完成。
- 转出项按签收原文 (e) 处理：D017、R-P05-01 / R-P05-02 / R-P05-03、F10、F8、反事实通量、allzero、S1 报告 11.2 的五个哈希保持 OPEN 或未验证，不在 P05 修，不阻塞 P06（U366–U370）；清单入口 checkpoints/p05/P05_S5_OPEN_ITEMS.tsv。
- P06 可启动（前置 P05 已由用户签收）。
- 历史说明：P05_S3_S4_SIGNOFF.md 中“P05-S5 未开始、未签收”的记录写于 S5 开始前，是当时状态的历史说明；本轮不改动该文件。

## 4 未完成声明

本记录由执行者依据用户授权写入，执行者未自行宣布任何阶段完成。
"""


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def main():
    text = open(TEXTFILE, "rb").read()
    if len(text) != EXP_TEXT_BYTES or sha_b(text) != EXP_TEXT_SHA:
        print("HARD_STOP sign-off anchor mismatch bytes=%d sha=%s" % (len(text), sha_b(text)))
        return 2
    short = EXP_TEXT_SHA[:8] + "…"
    doc = (HEAD % short).encode("utf-8") + text + TAIL.encode("utf-8")
    if os.path.exists(OUT):
        cur = open(OUT, "rb").read()
        if cur != doc:
            print("HARD_STOP sign-off file exists with different content")
            return 2
        print("sign-off file already up to date")
    else:
        with open(OUT, "wb") as fh:
            fh.write(doc)
    data = open(OUT, "rb").read()
    sec2_head = ("## 2 范围声明（签收原文，逐字照录）" + NL + NL).encode("utf-8")
    sec3_head = (NL + "## 3 ").encode("utf-8")
    if sec2_head not in data or sec3_head not in data:
        print("HARD_STOP section markers missing in written file")
        return 2
    sec2 = data.split(sec2_head, 1)[1].split(sec3_head, 1)[0]
    if sec2 != text:
        print("HARD_STOP written section 2 is not byte-equal to the anchor text")
        return 2
    rows = ["# SIGNON_S5R7.tsv -- P05-S5 R7 sign-off entry (task brief section 1 text, verbatim)",
            "# signoff_file=checkpoints/p05/P05_S5_SIGNOFF.md",
            "# signoff_bytes=%d signoff_sha256=%s" % (len(data), sha_b(data)),
            "# section2_bytes=%d section2_sha256=%s" % (len(sec2), sha_b(sec2)),
            "# anchor_file=" + os.path.relpath(TEXTFILE, REPO),
            "# anchor_sha256=%s anchor_bytes=%d section2_byte_equal=yes" % (EXP_TEXT_SHA, EXP_TEXT_BYTES),
            "key" + TAB + "value",
            "SIGNOFF_FILE" + TAB + "P05_S5_SIGNOFF.md",
            "SIGNOFF_SHA256" + TAB + sha_b(data),
            "SIGNOFF_BYTES" + TAB + str(len(data)),
            "SECTION2_SHA256" + TAB + sha_b(sec2),
            "SECTION2_BYTES" + TAB + str(len(sec2)),
            "DATE" + TAB + "2026-10-19"]
    open(os.path.join(EV, "SIGNON_S5R7.tsv"), "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("SIGNOFF bytes=%d sha=%s section2_sha=%s byte_equal=yes" % (len(data), sha_b(data), sha_b(sec2)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
