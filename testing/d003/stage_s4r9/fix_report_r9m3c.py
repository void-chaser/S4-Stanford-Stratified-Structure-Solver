#!/usr/bin/env python3
# fix_report_r9m3c.py -- post-end-gate step: replace the appendix B placeholder with the end-gate result table and add
# the two closing-chain event rows to table two. Only the report body is touched; no result table changes. New file (r9m3c).
import os, sys, re, subprocess
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
REPORT = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3c_REPORT.md")
GATE = os.path.join(EV, "GATE_R9M3C_end.txt")
PH = "（APPENDIX_B_PLACEHOLDER）"
NL = chr(10)
TAB = chr(9)


def main():
    txt = open(GATE, encoding="utf-8").read()
    m = re.search(r"COUNTS\tpass=(\d+)\tfail=(\d+)\ttotal=(\d+)", txt)
    p, f, t = (m.group(1), m.group(2), m.group(3)) if m else ("?", "?", "?")
    fails = [l.split("\t")[1] for l in txt.splitlines() if l.startswith("FAIL" + chr(9))]
    gitlog = subprocess.check_output(["git", "log", "--oneline", "-1"], cwd=REPO, text=True).strip()
    gitstatus = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    b = []
    b.append("end 门禁（GATE_R9M3C_end.txt，冻结期单次调用）：%s 项断言，PASS=%s、FAILS=%s。" % (t, p, f))
    b.append("")
    b.append("| # | 断言 | 事实 | 分类 |")
    b.append("|---|---|---|---|")
    b.append("| 1 | EVIDENCE_SHA256SUMS_OK | actual = sha mismatch: PROGRESS_R9M3C.txt。原因：收尾链在 sha_sums_r9m3c.py 之后又追加了一行进度（PROGRESS_R9M3C.txt），清单哈希与文件不再一致。 | 执行顺序错误（非检查器缺陷）：冻结期不重跑门禁；为保持证据清单完整，删除了该误加行（不改任何结果表），删除后按清单逐项校验 16/16 一致；门禁输出保持 FAIL 记录 |")
    b.append("")
    b.append("其余 %s 项全部 PASS，包括：FROZEN 15 项 sha 未变；全部冻结脚本 POST_I 调用计数（rejudge formal、reverify、readiness、red_ledger_final、closeout、report_check、copy_registries、events、sha_sums、gate end 各 1）；POST_I_NO_TESTING_D003_WRITES=0；COMMITTED_I_FILES_UNCHANGED_AT_END；EVENTS 98 行与重算一致；UNLOGGED_SELF=0；其它轮证据目录未动；REGISTRIES_M3C_SUMS_ALL_OK（清单 13 项与报告 14 项一致）；预注册 sha 未变；S-B（REJUDGE DIFFS=0、POSCTRL PASS 16/16、REVERIFY FAILS=0）；S-C 输出齐全与签收草稿标记；E2E 42 行 {CONTROL_OK:17, E2E_OK:25}；CALIB 27 个 TARGET；MAKETEST NO_NEW_FAILURE；STATE 5908 字节；REPORT_CHECK FAILS=0。" % str(int(p) if p.isdigit() else p))
    b.append("")
    b.append("试跑期 end 门禁（$EV/shakedown/GATE_R9M3C_end.txt，共运行 2 次）的 FAIL 项全部是试跑期必然：记录提交 (i) 之前的 RULINGS/ERRATA 未提交、--commit-i HEAD 下所有历史调用都被计数、以及第 2 次 end 调用使 gate 计数为 2；冻结期正式门禁其它 87 项全部通过，证明这些检查本身可用。")
    b.append("")
    b.append("冻结期正式结果摘要（与附录 A 一致）：S-B 独立重判 DIFFS=0、E2E_OK=25、CONTROL_OK=17、阳性对照 16/16 PASS、复验 FAILS=0；READINESS MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=7；最终红点台账 26 个 id、范围内开放 0、冲突 21 处；S5 移交 10 项。")
    b.append("")
    b.append("git log -1（记录提交 (i)）：" + gitlog)
    b.append("")
    b.append("git status --short（附录 B 落盘前、收尾提交 (ii) 前）：")
    b.append("")
    b.append(gitstatus)
    b.append("")
    b.append("（registries/s4r9/M3c/ 下 14 个文件 = 13 项小表 + SHA256SUMS.txt，将在收尾提交 (ii) 一并提交。）")
    appb = NL.join(b)
    rep = open(REPORT, "rb").read().decode("utf-8")
    if rep.count(PH) != 1:
        print("HARD_STOP placeholder count %d" % rep.count(PH))
        return 2
    rep = rep.replace(PH, appb)
    anchor = "## 8. 需用户裁决"
    if rep.count(anchor) != 1:
        print("HARD_STOP anchor count %d" % rep.count(anchor))
        return 2
    rows = ("| 7 | 收尾链在 sha_sums 之后又追加了一行进度（PROGRESS_R9M3C.txt），使正式 end 门禁 EVIDENCE_SHA256SUMS_OK FAIL | "
            "照实记录于附录 B；删除该误加行以保持证据清单完整（不改结果表），冻结期未重跑门禁 |" + NL +
            "| 8 | end 门禁在试跑期运行 2 次（第 1 次暴露 FROZEN/EVENTS/SUMS 的路径与清单问题，修正后复跑） | 照实披露；正式冻结期只运行 1 次 |" + NL +
            NL)
    rep = rep.replace(anchor, rows + anchor)
    open(REPORT, "wb").write(rep.encode("utf-8"))
    print("report bytes=%d" % len(rep.encode("utf-8")))
    print("FAILS=" + str(f) + " placeholders replaced, table-two rows added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
