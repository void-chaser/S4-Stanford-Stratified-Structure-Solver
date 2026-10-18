#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r9m1r3.py -- Append U318-U322 to RULINGS.tsv with prefix assertion (Step S-C). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUL_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

EXPECTED_OLD_BYTES = 130798
EXPECTED_OLD_SHA = "84d3871c2dabdc609c365b09ae58a4b7fb40a10a8ec450af77ede20ec64b5729"

RULINGS_TO_APPEND = [
    (
        "U318",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "r9m1r2 的冻结后换脚本、多次调用、原地改写重跑、裸写、收尾顺序问题按事实登记为勘误（E9-21 起），不改 r9m1r2 已提交的文件。r9m1r2 的 VERDICT/F3_F4_EQUIV/M1_SUMMARY 降级为'参考结果二'，有效结果以 r9m1r3 为准。r9m1r2 的 K 继承结果（K_INHERIT_R9M1R2，k_inherit 只在 L16/L17 写入并运行一次）、预注册的期望列与 ENGINE_COLUMNS 可以引用，但须经 U321 补核。",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "生效"
    ),
    (
        "U319",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "未运行行一律记为未运行：rc/rc1/rc2/rc3/hit 为 '-'，class 为 NOT_RUN_REGISTRY_ERROR，verdict 为 NOT_RUN_AS_EXPECTED；不得填入任何数值或 CONTROL_OK。比对时这类行单列为 NOT_RUN，不计入 EQUIVALENT。",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "生效"
    ),
    (
        "U320",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "M1c G6 的 I1–I6 与 point_verdict 必须进入判定和 F3/F4 比对：F4 侧取本轮 RESULTS_R6c_SEAM 中两遍的值；F3 侧取 r8m1c3 的 M1C_F3_RESULTS_R6c_SEAM.tsv；期望取 PREREG_M1_F4_R9M1R2（或本轮新预注册）中的 exp_I1..I6。三方逐字段比对；G5 同理（F3 侧取 M1C_F3_RESULTS_R6c_STATE.tsv）。",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "生效"
    ),
    (
        "U321",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "K 补核：对 26 个 d003/d003plan 组，在各组自己的 clean_env 与断点符号下，用 gdb 分别数 plain 与 kmap 的命中数，要求相等（只读复用 m1r2/build 下的 kmap 驱动，核对 sha256 与 BUILD_KMAP_R9M1R2 一致）。另出 K_COVERAGE_R9M1R3.tsv：651 行每行所属的 K 组（或'不需要 K'及理由），组内点数之和与 416 对账。命中数不等的组列入'需用户裁决'，其点照常运行但在总表中单列。",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "生效"
    ),
    (
        "U322",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "执行顺序：start 门禁 → 取证复核 G-1..G-8 → 裁决与勘误追加 → K 补核 → 试跑期（新脚本全部写好，在 $EV/shakedown/ 下跑通全流程：posctrl、smoke、formal 全量、verdict、compare、summarize）→ 预注册与口径冻结 → 冻结清单 → start 门禁复核 → 记录提交 (i) → 冻结期：posctrl → smoke → formal → verdict → compare → 收尾（§1-6）→ 收尾提交 (ii)。冻结期每个脚本只调用一次。",
        "P05-S4 R9 M1 第二修正轮任务书 §3",
        "生效"
    )
]

def main():
    with open(RUL_PATH, "rb") as f:
        old_bytes = f.read()
    
    assert len(old_bytes) == EXPECTED_OLD_BYTES, f"Bytes mismatch: {len(old_bytes)} != {EXPECTED_OLD_BYTES}"
    actual_old_sha = hashlib.sha256(old_bytes).hexdigest()
    assert actual_old_sha == EXPECTED_OLD_SHA, f"SHA mismatch: {actual_old_sha} != {EXPECTED_OLD_SHA}"

    new_lines = []
    for uid, topic, dec, src, st in RULINGS_TO_APPEND:
        assert uid not in old_bytes.decode("utf-8"), f"Duplicate ruling ID {uid}"
        new_lines.append(f"{uid}\t{topic}\t{dec}\t{src}\t{st}\n")

    new_content = old_bytes.decode("utf-8") + "".join(new_lines)
    assert new_content.startswith(old_bytes.decode("utf-8")), "Prefix assertion failed"

    with open(RUL_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    with open(RUL_PATH, "rb") as f:
        final_bytes = f.read()
    final_sha = hashlib.sha256(final_bytes).hexdigest()
    print(f"Appended {len(RULINGS_TO_APPEND)} rulings (U318-U322). New bytes={len(final_bytes)}, sha={final_sha}.")

if __name__ == "__main__":
    main()
