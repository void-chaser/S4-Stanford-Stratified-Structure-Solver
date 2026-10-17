#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r9m2c.py -- Append U302-U305 to RULINGS.tsv with prefix assertion (Step S-B).
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUL_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

RULINGS_TO_APPEND = [
    ("U302", "P05-S4 R9 M2c 任务书 §3", "R9 M2b 的数据采信（HITSEQ、K_INHERIT_R9M2b、SOLN_SUPP_JUDGE_R9M2b），判定不变。G-1 至 G-7 记为 E9-7 至 E9-13，追加到 ERRATA_9.txt；E9-1 中\"4 vs 2\"由 E9-10 更正，原行不改；M2b 报告不改，由 M2c 报告补充更正。", "P05-S4 R9 M2c 任务书 §3", "生效"),
    ("U303", "P05-S4 R9 M2c 任务书 §3", "K 继承的替代证据。10 组 NO_SEQ_EVIDENCE_R2 采信 HIT 行等价作为替代证据，条件是 hitseq_split_r9m2c.py 断言：每组对应的注入点在两遍中都是 NONEMPTY_IDENTICAL。范围仅限 k_max=1 的这 10 组；任一组不满足，则该组保持 NO_SEQ 并列入\"需用户裁决\"。", "P05-S4 R9 M2c 任务书 §3", "生效"),
    ("U304", "P05-S4 R9 M2c 任务书 §3", "U301 生效（追加本行，U301 原行不改）。RP-R8-M2c-1/1b 带范围声明关闭。范围：F4 上 S4.cpp Simulation_InitSolution 1760–1774 段的分配失败清理；证据为 18 个 SOLN 修后验证点（1763/1764/1765 × closed2d-ng1/fft-ng5/kottke-ng5 × dbg/san/san-AL），rc1=1、重试 call2 与无注入对照相同（I6 两遍都 HOLD）、san 行报告数为 0 且无崩溃。不覆盖：非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）；Python/Lua 可见性（M3）；B 树行为（B 列不是修复证据）。", "P05-S4 R9 M2c 任务书 §3", "生效"),
    ("U305", "P05-S4 R9 M2c 任务书 §3", "门禁与活文件纪律（自本轮起生效）：①门禁 FAILS 以输出文件中 ^FAIL\\t 的行数为准，并自检一致；②已提交的门禁脚本和 allow 文件不得修改，需要变化时新建带新轮次编号的文件；③活文件只能由带前缀断言的脚本追加；④门禁发现 FAIL 时，先停下写进报告，再按任务书处理，不得先修复后重跑来掩盖。", "P05-S4 R9 M2c 任务书 §3", "生效"),
]

# Read old data
with open(RUL_PATH, "rb") as f:
    old_bytes = f.read()

# Build lines to append
append_text = ""
for u_id, source, text, basis, status in RULINGS_TO_APPEND:
    line = f"{u_id}\t{source}\t{text}\t{basis}\t{status}\n"
    fields = line.rstrip("\n").split("\t")
    assert len(fields) == 5, f"Line does not have 5 fields (got {len(fields)}): {line}"
    append_text += line

append_bytes = append_text.encode("utf-8")
new_bytes = old_bytes + append_bytes

# Enforce §1 Rule 8 assertion: new file = old bytes + new lines
assert new_bytes[:len(old_bytes)] == old_bytes, "Assertion failed: prefix mismatch!"
assert new_bytes[len(old_bytes):] == append_bytes, "Assertion failed: suffix mismatch!"
assert len(new_bytes) == len(old_bytes) + len(append_bytes), "Assertion failed: length mismatch!"

# Write to disk
with open(RUL_PATH, "wb") as f:
    f.write(new_bytes)

print(f"RULINGS.tsv updated: {len(old_bytes)} -> {len(new_bytes)} bytes (+{len(append_bytes)} bytes).")
for u_id, _, _, _, _ in RULINGS_TO_APPEND:
    print(f"  Appended {u_id}")
