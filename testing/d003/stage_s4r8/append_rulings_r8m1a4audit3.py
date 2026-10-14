#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3): append rulings U188-U191 to RULINGS.tsv.  New file.

Appends only; the existing content is checked to be unchanged (prefix check on the recorded byte count and sha256).
Columns follow the RULINGS.tsv format: id, source, text, reference, status.  Source of every row: the part-3 brief section 0.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/append_rulings_r8m1a4audit3.py PREFIX_BYTES PREFIX_SHA256
PREFIX_BYTES and PREFIX_SHA256 are the RULINGS.tsv byte count and sha256 recorded at the start gate
(GATE_R8_M1a4_AUDIT3_START_A_R2.txt, RECORD RULINGS_BYTES / RULINGS_SHA256).  Nothing is written if the check fails.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUL = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
SRC = "R8 M1a 续3a 审核修正第三部分任务书 §〇"
ROWS = [
    ("U188",
     SRC,
     "audit2 对裸 plan 请求的语义解析有误。注入器的 plan 模式是“第 nth 次 plan 调用内的第 nth 次 malloc”"
     "（inject_r4_plan.cpp:38、79–84、587，两个计数共用 nth()），不是“第 N 次 plan 调用”。按正确语义重新分类；"
     "历史 INVALID_NOT_REACHED 若与计数一致，记 EXPECTED_NOT_REACHED。这是更正分类，不是改期望。"
     "追加 E8-67 更正 audit2 报告 §4.3 和 STATE 待裁决项 (a)。",
     "checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT3.md §〇；registries/s4r8/ERRATA_8.txt E8-67",
     "生效"),
    ("U189",
     SRC,
     "F2 的 K 来源指定为 registries/s4r7/M3_F2_RESULTS_R6c_STATE.tsv 的 NTH_or_K（键为 point_id+pass），"
     "并与 M3_F2_STATE_R6c_pass1/pass2.tsv 的 env_as_run 中的 S4FMM_NTH 交叉核对。两遍一致才采用；"
     "不一致或缺失的记 EVIDENCE_INSUFFICIENT，不得猜测。",
     "checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT3.md §〇",
     "生效"),
    ("U190",
     SRC,
     "以“逐单元 PLAN_START 与 PLAN_END、WIN_OPEN 与 WIN_CLOSE 的 seq 集合完全相等，且 trace_error=NONE”"
     "作为 out_of_scope 未发生的直接证据（依据：callseq_r8m1a4_gdb.py 每个 START 只建一个 FinishBreakpoint，"
     "建失败写 trace_error；stop 与 out_of_scope 只会发生其一）。198 单元全部满足时，补跑预注册标为 WITHDRAWN"
     "（原文件保留，不删除）；任何一个单元不满足，则这个单元所在的配对保留在补跑范围内。"
     "T6：对 198 单元实际用到的每个不同驱动（按 sha256 去重）做只读符号查询。",
     "checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT3.md §〇",
     "生效"),
    ("U191",
     SRC,
     "接受 A 段 K0 为 EVIDENCE_INSUFFICIENT；A-U96 三行 NOT_VERIFIED_K0 转入 M1b，由注入结果直接验证，"
     "本轮不加观测运行。",
     "checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT3.md §〇",
     "生效"),
]


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: append_rulings_r8m1a4audit3.py PREFIX_BYTES PREFIX_SHA256")
    pref_bytes = int(argv[1])
    pref_sha = argv[2]
    with open(RUL, "rb") as fh:
        data = fh.read()
    if len(data) < pref_bytes:
        raise SystemExit("REFUSED: RULINGS.tsv is shorter than the recorded prefix")
    if hashlib.sha256(data[:pref_bytes]).hexdigest() != pref_sha:
        raise SystemExit("REFUSED: RULINGS.tsv prefix sha256 differs from the start record")
    for row in ROWS:
        if any(("\t" + row[0] + "\t") in ln or ln.startswith(row[0] + "\t") for ln in data.decode("utf-8").splitlines()):
            raise SystemExit("REFUSED: %s already present" % row[0])
    text = "".join("\t".join(r) + "\n" for r in ROWS)
    with open(RUL, "ab") as fh:
        fh.write(text.encode("utf-8"))
    print("appended rows=%d bytes=%d" % (len(ROWS), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
