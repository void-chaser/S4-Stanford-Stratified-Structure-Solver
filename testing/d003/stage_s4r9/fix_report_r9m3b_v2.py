#!/usr/bin/env python3
# fix_report_r9m3b_v2.py -- pre-(i) draft fix: record the closeout-chain rehearsal and the gate/sha_sums version
# revisions in the report event tables. New file (r9m3b).
import os, sys, hashlib
REP = "checkpoints/p05/P05_S4R9_M3b_REPORT.md"
EXTRA_SH = [
    "| 5 | `$EV/shakedown/`（收尾链预演） | closeout → report_check → copy_registries → events → sha_sums → end 门禁 `--commit-i HEAD` 全链预演（以 `shakedown/inj1` 的结果做临时输入） | 各脚本均成功执行；end 门禁 75 项全部执行，FAIL 项全部是试跑期必然（RULINGS/ERRATA 尚未在 (i) 提交、脚本调用次数 >1、d003 写入、ALL_STATUS 清单口径），逐项见 `GATE_R9M3B_end.txt_SHAKEDOWN2` |",
]
EXTRA_EV = [
    "| 8 | 正式 start 门禁由 `gate_r9m3b.sh`(v1)+`gate_check_r9m3b.py`(v1) 执行并通过；随后发现交付物小节解析需容忍反引号与 12.1/14.1 编号、以及 `gate_r9m3b.sh` 的后缀拼接在试跑中写出了字面 $${OUTNAME}$${1} 文件，改为 v2/v3（终止版本 `gate_r9m3b_v3.sh` + `gate_check_r9m3b_v3.py`） | start_recheck 用 v2、end 用 v3；EV 内字面文件名残留已删除；FROZEN 清单按 v3 记录 |",
    "| 9 | `sha_sums_r9m3b.py` v1 把门禁自己会改写的 `ALL_STATUS_R9M3B_end.txt` 纳入证据清单，试跑中 EVIDENCE_SHA256SUMS 因此报哈希不一致 | 新建 `_v2`：清单排除 `ALL_STATUS_*`（门禁生成的快照，不属证据表）；正式期使用 v2，并在本表披露 |",
    "| 10 | `start_recheck` 在冻结清单写定之前执行（§5 的顺序为冻结清单 → start 前缀复核 → (i)） | 照实披露：该复核只检查 RULINGS/ERRATA 前缀 sha 与已提交文件未被改动，冻结脚本不改变这两项，结论有效；其余顺序严格执行 |",
]


def main():
    data = open(REP, "rb").read()
    txt = data.decode("utf-8")
    anchor_sh = "\n三个前端都冒烟通过"
    if txt.count(anchor_sh) != 1:
        print("HARD_STOP shakedown anchor %d" % txt.count(anchor_sh))
        return 2
    txt = txt.replace(anchor_sh, "\n" + "\n".join(EXTRA_SH) + anchor_sh)
    anchor_ev = "## 13. 需用户裁决"
    if txt.count(anchor_ev) != 1:
        print("HARD_STOP event anchor %d" % txt.count(anchor_ev))
        return 2
    txt = txt.replace(anchor_ev, "\n".join(EXTRA_EV) + "\n\n" + anchor_ev)
    open(REP, "wb").write(txt.encode("utf-8"))
    print("report bytes %d -> %d sha %s" % (len(data), len(txt.encode("utf-8")),
                                            hashlib.sha256(txt.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
