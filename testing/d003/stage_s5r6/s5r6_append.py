#!/usr/bin/env python3
# s5r6_append.py -- P05-S5 R6 pure-append corrections (task brief section 3):
#   (1) append ES5-17 to checkpoints/p05/registries/s5r2/ERRATA_S5.txt (three text corrections);
#   (2) append "appendix D (S5R6 text corrections, see ES5-17)" to P05_S5R5_REPORT.md.
# Both are pure appends: the old byte prefix and the R5 report's first 95 lines must keep their sha256.
# Writes the round evidence tables ERRATA_APPEND_S5R6.tsv and REPORT_APPEND_S5R6.tsv.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r6")
ERR = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
R5 = os.path.join(P05, "P05_S5R5_REPORT.md")
TAB = chr(9)
NL = chr(10)

EXP_ERR_BYTES = 15805
EXP_ERR_SHA = "e1f02ee80605a8eb1240fdacdf22d9b4e2e38c5a764c1fd946e5d979af8dfa33"
EXP_R5_SHA = "9f90d6f7ad390cc5ab14b6bc08bb5a4fbb95fcd98e6231081549ca4d602d91c5"
EXP_R5_FIRST95 = "8f7f96b4fc41500c616f6f931160fdd4ee7d46856ca3e4c1d0fdcb1fe138932c"
POSCTRL_SHA = "2c5e6f176885e05f1a72d8f252331b7a0516f0cd932998c83f899e447ff08cfa"

ES5_17 = [
    "ES5-17",
    "- 事实：(a) P05_S5R5_REPORT.md §6.1 表一命令列的管道符未转义：原文 `awk -F'\\t' ... | tee /dev/stderr | wc -l`"
    " 把 Markdown 表格拆成多列，正确写法是 `awk -F'\\t' ... \\| tee /dev/stderr \\| wc -l`。"
    "(b) §7 交付物列表把 POSCTRL_GATE_S5R5.txt 列入 registries/s5r5，但该文件实际只在证据目录交付："
    " checkpoints/p05/evidence/p05-s5r5/POSCTRL_GATE_S5R5.txt；registries/s5r5 清单实为 12 项。"
    "(c) 附录 A 写 `COUNTS COUNTS\\tpass=36\\tfail=0\\ttotal=36` 是 verifier 回显造成的重复，"
    "正确内容为 `COUNTS\\tpass=36\\tfail=0\\ttotal=36`。",
    "- 影响：只影响 R5 报告的文字与表格排版，不影响任何判定、证据 sha 或清单；"
    "S5R5 的 end 门禁 36/36 FAILS=0 FINAL_STATUS=COMPLETE 结论不变（P05_S5R5_REPORT.md 附录 C）。",
    "- 证据：P05_S5R5_REPORT.md 第 50、68、79 行（R6 开工基线全文件 sha256 9f90d6f7ad390cc5ab14b6bc08bb5a4fbb95fcd98e6231081549ca4d602d91c5）；"
    "checkpoints/p05/evidence/p05-s5r5/POSCTRL_GATE_S5R5.txt（sha256 2c5e6f176885e05f1a72d8f252331b7a0516f0cd932998c83f899e447ff08cfa，"
    "出现在 checkpoints/p05/evidence/p05-s5r5/SHA256SUMS.txt 第 10 行）；"
    "checkpoints/p05/registries/s5r5/SHA256SUMS.txt（sha256 b8be693b70f859c43d74764553c7dd57f11f0fcc0ae931796fcd1d33f9ec0ed9，12 条）；"
    "checkpoints/p05/evidence/p05-s5r5/shakedown/gate/GATE_S5R5_end.txt 第 44 行 `COUNTS\\tpass=36\\tfail=0\\ttotal=36`。",
    "- 处理方式：S5R6 只追加——本 ERRATA 追加 ES5-17；P05_S5R5_REPORT.md 末尾追加“附录 D（S5R6 追加：文字更正，见 ES5-17）”"
    "逐条给出更正文字；R5 报告第 1–95 行不改（前 95 行 sha256 8f7f96b4fc41500c616f6f931160fdd4ee7d46856ca3e4c1d0fdcb1fe138932c 不变），附录 A/C 不改；"
    "registries/s5r5 冻结，不把 POSCTRL_GATE_S5R5.txt 补进 registry。",
]

APP_D = [
    "",
    "## 附录 D（S5R6 追加：文字更正，见 ES5-17）",
    "",
    "> 本附录只追加，不改第 1–95 行与附录 A/C 的任何字节（前 95 行 sha256 8f7f96b4fc41500c616f6f931160fdd4ee7d46856ca3e4c1d0fdcb1fe138932c，"
    "追加前全文件 sha256 9f90d6f7ad390cc5ab14b6bc08bb5a4fbb95fcd98e6231081549ca4d602d91c5）。"
    "三条更正均只影响文字与排版，不影响任何判定、证据 sha 或 S5R5 的 36/36 FAILS=0 结论。",
    "",
    "- (a) §6.1 表一命令列：原文 `awk -F'\\t' ... | tee /dev/stderr | wc -l` 的管道符未转义，把表格拆成多列。"
    "正确写法：`awk -F'\\t' ... \\| tee /dev/stderr \\| wc -l`（同一命令、同一事件：tee 目标 /dev/stderr 不在 $REPO 下且未落盘，同一管道的 wc 输出 139）。",
    "- (b) §7 交付物列表：POSCTRL_GATE_S5R5.txt 不在 registries/s5r5，而在 evidence/p05-s5r5/POSCTRL_GATE_S5R5.txt"
    "（sha256 2c5e6f17…；checkpoints/p05/evidence/p05-s5r5/SHA256SUMS.txt 第 10 行）。"
    "为避免 registry↔posctrl 循环依赖（该文件本身就是 registry 聚合的阳性对照），不把它补进 registry；"
    "registries/s5r5/SHA256SUMS.txt 为 12 项（12/12 OK），目录含清单自身共 13 个文件。",
    "- (c) 附录 A：`COUNTS COUNTS\\tpass=36\\tfail=0\\ttotal=36` 是 verifier 回显造成的重复；"
    "正确内容为 `COUNTS\\tpass=36\\tfail=0\\ttotal=36`（checkpoints/p05/evidence/p05-s5r5/shakedown/gate/GATE_S5R5_end.txt 第 44 行即该单行）。",
]


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def first95(data):
    parts = data.split(b"\n")
    return sha_b(b"\n".join(parts[:95]) + b"\n"), len(parts)


def main():
    err0 = open(ERR, "rb").read()
    if len(err0) != EXP_ERR_BYTES or sha_b(err0) != EXP_ERR_SHA:
        print("HARD_STOP ERRATA baseline mismatch bytes=%d sha=%s" % (len(err0), sha_b(err0)))
        return 2
    ids0 = [l for l in err0.decode("utf-8").splitlines() if l.startswith("ES5-")]
    if not ids0 or ids0[-1] != "ES5-16":
        print("HARD_STOP ERRATA last entry is not ES5-16")
        return 2
    with open(ERR, "ab") as fh:
        fh.write((NL.join(ES5_17) + NL).encode("utf-8"))
    err1 = open(ERR, "rb").read()
    if err1[:EXP_ERR_BYTES] != err0 or sha_b(err1[:EXP_ERR_BYTES]) != EXP_ERR_SHA:
        print("HARD_STOP ERRATA prefix changed")
        return 2
    ids1 = [l for l in err1.decode("utf-8").splitlines() if l.startswith("ES5-")]
    if ids1[-1] != "ES5-17" or ids1.count("ES5-17") != 1:
        print("HARD_STOP ERRATA append check failed last=%s" % ids1[-1])
        return 2
    body = ["# ERRATA_APPEND_S5R6.tsv -- P05-S5 R6 pure append (ES5-17, three text corrections)",
            "# before_bytes=%d before_sha256=%s" % (EXP_ERR_BYTES, EXP_ERR_SHA),
            "# after_bytes=%d after_sha256=%s" % (len(err1), sha_b(err1)),
            "# prefix_bytes=%d prefix_sha256=%s prefix_unchanged=yes" % (EXP_ERR_BYTES, sha_b(err1[:EXP_ERR_BYTES])),
            "# last_entry=%s entries_appended=1" % ids1[-1],
            "id" + TAB + "appended",
            "ES5-17" + TAB + "yes"]
    open(os.path.join(EV, "ERRATA_APPEND_S5R6.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("ERRATA before=%d/%s after=%d/%s last=%s" % (EXP_ERR_BYTES, EXP_ERR_SHA, len(err1), sha_b(err1), ids1[-1]))

    r50 = open(R5, "rb").read()
    if sha_b(r50) != EXP_R5_SHA:
        print("HARD_STOP R5 report baseline sha mismatch: %s" % sha_b(r50))
        return 2
    f0, n0 = first95(r50)
    if f0 != EXP_R5_FIRST95:
        print("HARD_STOP R5 report first95 sha mismatch: %s" % f0)
        return 2
    with open(R5, "ab") as fh:
        fh.write((NL.join(APP_D) + NL).encode("utf-8"))
    r51 = open(R5, "rb").read()
    if not r51.startswith(r50):
        print("HARD_STOP R5 report prefix changed")
        return 2
    f1, n1 = first95(r51)
    if f1 != EXP_R5_FIRST95:
        print("HARD_STOP R5 report first95 sha changed: %s" % f1)
        return 2
    add = r51[len(r50):].decode("utf-8")
    if not all(k in add for k in ("附录 D", "ES5-17", "\\| tee /dev/stderr \\| wc -l",
                                  "POSCTRL_GATE_S5R5.txt", "2c5e6f17",
                                  "COUNTS\\tpass=36\\tfail=0\\ttotal=36")):
        print("HARD_STOP appendix D missing required fragments")
        return 2
    body = ["# REPORT_APPEND_S5R6.tsv -- P05_S5R5_REPORT.md pure append (appendix D)",
            "# before_bytes=%d before_sha256=%s" % (len(r50), sha_b(r50)),
            "# after_bytes=%d after_sha256=%s" % (len(r51), sha_b(r51)),
            "# first95_sha256_before=%s first95_sha256_after=%s unchanged=yes" % (f0, f1),
            "# total_lines_before=%d total_lines_after=%d appended_bytes=%d" % (n0, n1, len(r51) - len(r50)),
            "item" + TAB + "value",
            "appendix_D" + TAB + "appended",
            "posctrl_gate_evidence_sha256" + TAB + POSCTRL_SHA]
    open(os.path.join(EV, "REPORT_APPEND_S5R6.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("R5REPORT before=%d/%s after=%d/%s first95=%s unchanged=yes" % (len(r50), sha_b(r50), len(r51), sha_b(r51), f1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
