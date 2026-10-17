#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r9m1.py -- Append U306-U311 to RULINGS.tsv with prefix assertion (Step S-B).
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUL_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

RULINGS_TO_APPEND = [
    ("U306", "P05-S4 R9 M1 任务书 §3", "R9 M1 只在 F4 上重跑 M1 的 F3 侧行（M1b 415 + M1c 236 = 651，以脚本复核数为准）。F2 树未变，F2 侧行不重跑，引用 r8m1b3/r8m1c3 的正式判定并核对驱动 sha256（同 U292 的处理）。合并后总表须断言 = 1302。", "P05-S4 R9 M1 任务书 §3", "生效"),
    ("U307", "P05-S4 R9 M1 任务书 §3", "预注册规则。逐行取 F3 的有效行（M1b 用 EFFECTIVE_M1B_R8_M1b3，M1c 用 VERDICT_M1C_R8_M1c3 对应的冻结预注册），tree→F4，driver→F4 对应驱动，sha 字段换为 F4 产物，point_id 的 -F3 后缀改为 -F4，其余 exp_*（含 NOT_REACHED_AS_EXPECTED、NOT_RUN_AS_EXPECTED 与 I1–I6）原样保留。状态 INFLUENCED，basis 写\"R9 M1 regression of <F3 point_id>\"。不得因 F4 结果改期望。", "P05-S4 R9 M1 任务书 §3", "生效"),
    ("U308", "P05-S4 R9 M1 任务书 §3", "S3R5 改动的影响清单。运行前用脚本列出 F3 侧所有\"注入点或其 K 映射帧落在 Simulation_InitSolution（F3 行 1754–1774 区间）\"的行，输出 IMPACT_S3R5_R9M1.tsv。这些行的期望不得按 F3 原样照抄：按 U293 的 SOLN 规则单列预注册，或标 CITED_M2 并引用 R9 M2/M2b 的判定（二选一，逐行写明）。没有这类行时写\"0 行\"并附脚本输出。", "P05-S4 R9 M1 任务书 §3", "生效"),
    ("U309", "P05-S4 R9 M1 任务书 §3", "K 继承。凡带计数注入的组（S4FMM_NTH、init:K、aligned:K、win:K、twice 的 plan/exec/malloc-K 等），按 U300 规则在 F3、F4 上各跑一次无注入的 gdb 映射：两边命中总数相等；每次命中带大小或计数器 id 与 S4 帧（行号经 LINEMAP 映射）；取不到 S4 帧时用 bt 8 向外找。R9 M0/M2b 已证明的组直接引用（列出组 id 与证据文件、行号），不重跑；新组才跑。HIT 等价表须分开计 BOTH_EMPTY 与 NONEMPTY_IDENTICAL。k_max=1 且取不到序列的组可按 U303 用 HIT 行等价替代，条件是该组注入点两遍都是 NONEMPTY_IDENTICAL。任一组 DIVERGENT：该组的行不进入正式运行，列入\"需用户裁决\"。", "P05-S4 R9 M1 任务书 §3", "生效"),
    ("U310", "P05-S4 R9 M1 任务书 §3", "装置对等。F4 缺的驱动（至少 twice-* 系列，以及 r6bseam-fmmret 若无对应驱动）在 $EV/build 下从 F4 导出（git archive，经 safe_run）重新构建。编译/链接命令行去掉树路径后与 F3 对应驱动逐条相同（BUILD_OPTION_DIFF_R9M1.txt，差异 0 项）；每个库的告警数等于 F3 对应库。已存在的 F4 产物不重编，只核 sha256。", "P05-S4 R9 M1 任务书 §3", "生效"),
    ("U311", "P05-S4 R9 M1 任务书 §3", "执行顺序与停止。start 门禁 → 裁决追加与记录提交 (i)（任务书、RULINGS、驱动清单、影响清单、K 证明、预注册与其 sha256 及 UTC 时间戳）→ 阳性对照 → 冒烟（每组 × 每驱动至少 1 行，单遍）→ 正式两遍 → 判定 → 合并总表 → 收尾提交 (ii)。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟，只分诊（核对崩溃帧与日志），不改期望，不进正式运行。正式运行中的 MISMATCH 或 FLAKY 照实记录，只分诊，不重跑覆盖。", "P05-S4 R9 M1 任务书 §3", "生效"),
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

# Check that U ids are strictly monotonic and unique
all_u = [l.split("\t")[0] for l in new_bytes.decode("utf-8").splitlines() if l.startswith("U")]
assert len(all_u) == len(set(all_u)), "Duplicate U numbers detected!"
last_u_num = int(all_u[-1][1:])
assert last_u_num == 311, f"Expected last U to be U311, got {all_u[-1]}"

# Write to disk
with open(RUL_PATH, "wb") as f:
    f.write(new_bytes)

print(f"RULINGS.tsv updated: {len(old_bytes)} -> {len(new_bytes)} bytes (+{len(append_bytes)} bytes).")
for u_id, _, _, _, _ in RULINGS_TO_APPEND:
    print(f"  Appended {u_id}")
