#!/usr/bin/env python3
# build_errata_r8m2a3.py -- P05-S4 R8 M2a3 Section 5: text of the ERRATA_8.txt append (E8-96..E8-100).
# New file. Writes the append text to $EV/ERRATA_APPEND_R8_M2a3.txt and appends it to
# checkpoints/p05/registries/s4r8/ERRATA_8.txt ONLY if the existing file is still at the start-gate state
# (68512 bytes, sha256 6f1d1366...). Append only: no existing entry is changed. Refuses if append file exists.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
APPEND = os.path.join(EV, "ERRATA_APPEND_R8_M2a3.txt")
START_BYTES = 68512
START_SHA = "6f1d1366f3340712629140dae7c4b585045113317abc05ec38b270ff3eb0149d"

BLOCKS = [
    ("E8-96\tP05-S4 R8 M2a3 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M2a3 任务书 §5）。原条目不改。\n"
     "        静态可执行性审计（PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv）指出原冻结预注册 PREREG_M2_R8_M2a2.tsv（sha256 1b60f95c...）"
     "存在 174 处可执行性缺口与冲突：(a) 49 行要求私有状态（I1..I6=HOLD）但 gdb_script=-；(b) 49 处测试行未显式绑定 control_point_id 与输出序号；"
     "(c) M2-04 双失败恢复在原表中注册为 retry_call=2、k_retry=3，但实际驱动中 call2 为第二次失败（rc2=20），最终成功恢复为 call3（k_retry=4，rc3=0），原表且缺少 exp_rc3；"
     "(d) 31 处 sanitizer 行将未在 gdb 下采集的私有状态记为 HOLD，且 I7 与 exp_san 定义重复。\n"),
    ("E8-97\tP05-S4 R8 M2a3 更正（只追加）。原条目不改。\n"
     "        有效预注册 PREREG_M2_EFFECTIVE_R8_M2a3.tsv（sha256 27e33b27...）取代原表作为 M2 执行基准；原预注册逐字节保留不变。"
     "150 个 point_id 与 60 测试/90 对照分类全部保留。新增 exp_rc3、target_layer、control_point_id、output_call、control_output_call 明确采集入口与对照绑定。\n"),
    ("E8-98\tP05-S4 R8 M2a3 更正（只追加）。原条目不改。\n"
     "        M2-04 双失败事件与恢复时序修正：明确 call1 第一次失败（k_fail=1，rc1=20）、call2 第二次失败（k_fail=3，rc2=20）、"
     "call3 最终成功恢复（k_retry=4，retry_call=3，rc3=0）。I5 与 I6 绑定至 call3，对照组亦比较 call3 输出；严禁虚构驱动未提供的快照点。\n"),
    ("E8-99\tP05-S4 R8 M2a3 更正（只追加）。原条目不改。\n"
     "        M2-03 sanitizer 行状态采集修正：明确在不挂载 gdb 的独立 sanitizer 运行中，进程私有状态 I1–I6 记为 UNOBSERVED，"
     "不冒充为 HOLD 或不适用；exp_I7=HOLD 明确定义为 exp_san == 0（无内存安全与未定义行为报告）。\n"),
    ("E8-100\tP05-S4 R8 M2a3 更正（只追加）。原条目不改。\n"
     "        M2-09-01-F2 身份补齐：依据 checkpoints/p05/registries/s4r7/DRIVERS_R7_SEAM.tsv 第 4 行，driver 明确为 seam-fmmret-F2（sha256 a4061e4c...），"
     "库 sha256 明确为 b513f840...。\n"),
]


def main():
    if os.path.exists(APPEND):
        print("build_errata_r8m2a3: REFUSED exists (U17): %s" % APPEND)
        return 2
    with open(ERRATA, "rb") as fh:
        cur = fh.read()
    if len(cur) != START_BYTES or hashlib.sha256(cur).hexdigest() != START_SHA:
        print("build_errata_r8m2a3: REFUSED ERRATA_8.txt is not at the start-gate state (bytes=%d)" % len(cur))
        return 2
    body = "\n" + "\n".join(b.rstrip("\n") for b in BLOCKS) + "\n"
    os.makedirs(EV, exist_ok=True)
    with open(APPEND, "x", encoding="utf-8") as fh:
        fh.write(body)
    with open(ERRATA, "ab") as fh:
        fh.write(body.encode("utf-8"))
    print("build_errata_r8m2a3: appended %d entries to ERRATA_8.txt; append file %s" % (len(BLOCKS), APPEND))
    return 0


if __name__ == "__main__":
    sys.exit(main())
