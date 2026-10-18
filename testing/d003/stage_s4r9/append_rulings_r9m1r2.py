#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r9m1r2.py -- Append U312-U317 to RULINGS.tsv with prefix assertion (Step S-C). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUL_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

EXPECTED_OLD_BYTES = 127551
EXPECTED_OLD_SHA = "177d142095a2dc91a9787fc6bfc2ed5e83174b30f9e70c059622c8f221b98cba"

RULINGS_TO_APPEND = [
    (
        "U312",
        "P05-S4 R9 M1 修正轮任务书 §3",
        'r9m1 的预注册覆盖、正式运行覆盖重跑、门禁放宽、裸写，都按事实登记为勘误（E9-14 起），不改 r9m1 已提交的文件。r9m1 的 M1 F4 判定（VERDICT_M1_F4_R9M1、M1_SUMMARY_F4_R9M1）降级为"参考结果"，有效结果以本轮 r9m1r2 为准。',
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    ),
    (
        "U313",
        "P05-S4 R9 M1 修正轮任务书 §3",
        '重新冻结预注册。新脚本 prereg_r9m1r2.py 以 (section, group, point_id) 为键，期望值只从 F3 冻结表机械推导（M1b：PLAN_M1B_R8_M1b1 / PREREG_SUPP_R8_M1b3 / EFFECTIVE_M1B_R8_M1b3；M1c：PREREG_M1C_FACTS_R8_M1c2 / VERDICT_M1C_R8_M1c3），不读任何 F4 运行结果。新增列 inj_call（M1b 取 PREREG_SUPP 或 PLAN 的原值，不用 rc 推断）与 contract（M1b 的 rc2 比对口径，按 R8 M1b 合同原文引用）。断言：651 行；与 d57fcf29 版逐行比对，期望列的差异只允许出现在新增列上，若有其他差异逐行列出、照实写。状态 INFLUENCED，basis 注明"受 r9m1 冒烟与正式运行观察影响"。',
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    ),
    (
        "U314",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "判定口径冻结。verdict_r9m1r2.py 的口径在 (i) 前写入 ENGINE_COLUMNS_R9M1R2.txt：M1b 的 rc2 何时比对、M1c 中 G6c/CTRL_AUX 的 `-` 如何处理，每条都要引用历史判定脚本的文件与行号（如 verdict_m1c_r8m1c3.py:103）。不能引用历史依据的口径，按严格比对处理。",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    ),
    (
        "U315",
        "P05-S4 R9 M1 修正轮任务书 §3",
        'K 继承重做。29 组 k_max>1 的 NO_SEQ 不适用 U303。init/polyinj 组改用 R9 M0 已有的 init-F3/F4-dbg、polyinj-F3/F4-dbg 做无注入 gdb 映射。d003/d003plan 组从 F3、F4 导出树另建只用于映射的 -g 变体（命名 *-kmap-dbg，编译选项 = 对应 plain 驱动选项 + -g，BUILD_OPTION_DIFF 中只允许 -g 这一项差异）。kmap 驱动的命中总数须等于同 env 下 plain 驱动的命中总数（gdb 计数），然后按 U300 比对序列（大小 + S4 帧，行号经 LINEMAP_F3_F4_S3R5 映射，取不到帧用 bt 8）。三项都相同的记 PASS_K_INHERITED_R3；仍取不到序列的记 NO_SEQ_EVIDENCE_R3，列入"需用户裁决"；DIVERGENT 的组不进入正式运行，列入"需用户裁决"。k_max=1 的 6 组同样先试映射，失败才用 U303 替代证据。kmap 驱动不得用于判定运行。',
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    ),
    (
        "U316",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "执行顺序：start 门禁 → 取证（S-B）→ 裁决与勘误追加 → K 重做 → 预注册与口径冻结 → 记录提交 (i) → 阳性对照 → 冒烟 → 正式两遍 → 判定 → 与 r9m1 参考结果及 F3 冻结事实比对 → 合并总表 → 收尾提交 (ii)。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟，只分诊。正式运行中的 MISMATCH 或 FLAKY 照实记录，不改脚本、不重跑覆盖。",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    ),
    (
        "U317",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "F2 侧 651 行继续引用 r8 冻结判定，CITED_F2 表由 prereg_r9m1r2.py 用同一键规则重新生成，作为新文件，并核对驱动 sha256。",
        "P05-S4 R9 M1 修正轮任务书 §3",
        "生效"
    )
]

with open(RUL_PATH, "rb") as fh:
    old_bytes = fh.read()

assert len(old_bytes) == EXPECTED_OLD_BYTES, f"Size mismatch: {len(old_bytes)} != {EXPECTED_OLD_BYTES}"
old_sha = hashlib.sha256(old_bytes).hexdigest()
assert old_sha == EXPECTED_OLD_SHA, f"Sha mismatch: {old_sha} != {EXPECTED_OLD_SHA}"

# Format append lines
new_lines = ""
for u_id, src, ruling, topic, status in RULINGS_TO_APPEND:
    line = f"{u_id}\t{src}\t{ruling}\t{topic}\t{status}\n"
    assert len(line.rstrip("\n").split("\t")) == 5, f"Line does not have 5 fields: {line}"
    new_lines += line

new_bytes = old_bytes + new_lines.encode("utf-8")
assert new_bytes.startswith(old_bytes), "Prefix assertion failed!"
assert len(new_bytes) == len(old_bytes) + len(new_lines.encode("utf-8")), "Length assertion failed!"

# Write back atomically
with open(RUL_PATH, "wb") as fh:
    fh.write(new_bytes)

print(f"Successfully appended {len(RULINGS_TO_APPEND)} rulings (U312-U317) to RULINGS.tsv.")
print(f"Old size: {len(old_bytes)}, New size: {len(new_bytes)} bytes.")
