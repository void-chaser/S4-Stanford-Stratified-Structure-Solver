#!/usr/bin/env python3
# build_rulings_r8m2a2.py -- P05-S4 R8 M2a2 section 3.1: text of the RULINGS.tsv append (U236-U247).
# New file. Writes the append text to $EV/RULINGS_APPEND_R8_M2a2.tsv (5 columns, status 生效, source per brief section 3)
# and appends it to checkpoints/p05/registries/RULINGS.tsv ONLY if the existing file is still at the start-gate state
# (92855 bytes, sha256 c1632c0f...).  Refuses if the append file exists (U17).  Append only; no existing row changes.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
RULINGS = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
APPEND = os.path.join(EV, "RULINGS_APPEND_R8_M2a2.tsv")
START_BYTES = 92855
START_SHA = "c1632c0f518ff20d3139891230b379772ad6757ef16e60cc7564abf71c19813c"
SRC = "P05-S4 R8 M2a2 任务书 §3"
STATUS = "生效"

ROWS = [
    ("U236", "接受 r8m2a（`6a4f003`）以下结果：U229–U235 与 E8-88–E8-90 已登记；A-10 交叉核对 6/6 COVERED_BY_M0，因此 M2-00 无需出点；装置盘点 8/8 SAME；F3、B 树导出哈希一致；判定阳性对照 `_R2` PASS（第一次 FAIL 原因为合成设计错误，已披露）。以下按执行偏离或违规接受，不追认为合规：`6a4f003` 在 end 门禁 FAILS=1 时提交，偏离 U158；`safe_run -- sh -c 'true'` 是违规；白名单外的内联命令（`git show`、`head/tail/wc`、`git branch`）；看到失败后三次收窄门禁扫描范围（被 U237 取代）。r8m2a 只完成了 M2a 范围的一部分，其余在 r8m2a2 完成。"),
    ("U237", "r8m2a end 门禁 `NO_STRAY_BUILD_PRODUCTS_END` 的失败是误报。`testing/d003/__pycache__/` 中两个 pyc 的 mtime 为 2026-10-11 18:28:10 与 19:19:29（+1100），早于 r8m2a start 门禁（2026-10-15 17:18:13 +1100），并且被 `.gitignore` 的 `__pycache__/` 忽略。r8m2a 的脚本用 `python3 -I -B` 运行，不写字节码。r8m2a 报告中「本轮产生（推断）」的说法不成立（E8-91）。这两个文件不删除（U17）。自 r8m2a2 起：构建产物检查采用「start 记录基线、end 只判新增或变化」；end 门禁 FAILS≠0 时不提交，停下等用户处理。"),
    ("U238", "r8m2a 的 M2-01 预注册（`PREREG_M2_R8_M2a_R2.tsv`，sha `557f568a…`）不能判定 I1–I6，原因有三：(1) G5 规则依赖 gdb 读私有状态（`r6c_judge.py` 读 R6BSTATE、R6BCLM、R6CREQ），需要 `-O0 -g` 的 F3 dbg 库与 dbg 驱动，并配合 `r6c_state.gdb`；而登记的 `init-F3`、`polyinj-F3` 链接的是 F3 plain 库；(2) 表中缺少 inj_call、k_fail、k_preretry、k_retry、k_before、argv 列；(3) 没有 I6 所需的对照组。该表的 I 列作废（E8-92）。rc 与类别列不单独重跑（M1 已覆盖，U225）。M2-01 由 r8m2a2 的新预注册取代。原文件不改。"),
    ("U239", "M2-09 不需要用户裁决。env 取自 `registries/s4r7/REGRESS_R7` 体系的 `REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv` 第 7–8 行：`FMM_MODE=fft;S4FMM_NG=9`，无注入；期望 CONTROL_OK、rc 0，标 INFLUENCED。驱动按登记意图用 fmmret 族的 plain 驱动：F3 用 `seam-fmmret-F3`（`registries/s4r8/DRIVERS_R8.tsv`），F2 用 `evidence/p05-s4r7/drivers_r7/seam-fmmret-F2/driver`（`registries/s4r7/DRIVERS_R7_SEAM.tsv` 的 fmmret-F2 行，sha 先核对）。「CTRL_SEAM 的全部 fmmret 行」就是这两行。M2-09 共 2 点（F3、F2 各 1）。F3 这一点在 R8 M0 已以 seam-fmmret-F3 跑过两遍 MATCH（`registries/s4r8/RESULTS_R8_D_pass1.tsv` 第 4 行）。M2-09 再跑一次，是为了与 F2 成对比较。G2a 中以 `fmmret:` 开头的注入行已在 M1 覆盖，M2 不重做。"),
    ("U240", "M2-06 的映射与范围。`linearsolve_null2:244` 对应 F3 `S4/fmm/fmm_closed.cpp:244–245`，依据 `testing/d003/seam/apply_seam_b2.py:19,68`，本轮在导出的 F3 树上复核锚点。该点的返回码已由 M1 的 `R4-CL04-F-F3` 覆盖（MATCH，REPORTED_FAILURE，rc1 20），M2 不重做。K-1 本身问的是有限性检查：[源码] F3 的 `fmm_closed.cpp` 没有 `isfinite`，`fmm_kottke.cpp:312/315` 有。M2-06 测的是张量路径上 solve_info=0 但 Epsilon_inv 非有限的情形：新建 `inject_r8m2a2_nan.cpp`（复制品规则，从 `inject_r4_plan.cpp` 复制，只追加一个请求 `linearsolve_nanbuf:244:K`，在 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER` 中把输出写成 NaN，原有分支逐字不变）。所需钩子是否存在于 F3 seamF 库，用 nm 脚本核对；不存在时在 `$EV` 下的导出副本上加打 `apply_seam_r4_buf.py` 另建 seam 库，不改 `S4/`。期望 [源码]：rc1=0，类别 SILENT_SWALLOW，INFLUENCED。若 M2b 实测如此，就是 K-1 红点候选，按 U4 处理。"),
    ("U241", "M2-02 阶段 e 的搜索范围。候选包括：`registries/s4r6d/U2_STAGE_R6d.tsv` 与 `SEAM_SITE_STAGE_R6d.tsv` 中的全部注入请求；以及 F3 导出树中位于 `Simulation_ComputeLayerModes` 之外、而在 FMM/FFT 失败传播链上的分配或计划调用（如 GetFieldOnGrid、通量与场缓存路径）[源码]。逐个写出位置（文件:行号）、阶段定义（ERRATA_6d 的 E6d-3 第 2 条）、是否在 D003 范围内（U5b/E6-4，以及 MEMORY 中的 D003 范围判据）。全部在范围外就写 `NOT_FOUND_IN_SCOPE`，去向由用户在审核时裁决。本轮不扩大范围。"),
    ("U242", "M2-08 类别 C 的搜索范围。模式：{closed1d、closed2d、experimental、fft、kottke、tensor、jones、nv、vl}；NG：2…8。「执行期窗口内有分配」按以下依据判断：F3 源码 [源码]；`registries/s4r3/CALLSEQ.tsv`；`registries/s4r8/M1a/CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv`。本轮不做新的运行。搜索表每行写依据（文件:行号）。找到配置就出点：rc≠0，且输出缓冲保持哨兵值或不被使用。没找到就写 `NOT_FOUND` 并附表，去向由用户在审核时裁决。"),
    ("U243", "M2-07 的网格固定如下。NG 1…8 × 模式 {closed1d、closed2d、experimental、fft、kottke、tensor、jones、nv、vl}，每格一个无注入对照（d003-F3-plain）。每个模式加一个代表性注入：`s4malloc`，NTH=1，d003plan-F3-plain，NG=5。期望：M0、M1 有同 env 观察的取观察值；没有的取 [源码] 推断，一律标 INFLUENCED。注入格的 exp_rc1 若历史上没有同 env 的确切值，允许写记号 `NZ`（表示「非零」）。判定脚本必须支持该记号。"),
    ("U244", "M2-04 双目标的语义。[源码]：第一处失败后，同一次 ComputeLayerModes 调用即返回，第二处在同一次调用里到不了。因此「一次运行两处失败」定义为：call1 失败，重试 call2 再失败，call3 恢复。(a) 两次失败在同一层；(b) 两次失败在不同层（需要 M2-05 的多层驱动）。新建 `inject_r8m2a2_dual.cpp`（复制品规则，从 `inject_r4_plan.cpp` 复制，只追加对 `S4FMM_INJECT2` 的独立解析与计数，原有分支逐字不变）。期望：call1、call2 的 rc 非零且无信号；call3 rc=0；每次失败后的 I1–I6 按 M2-01 规则成立。快照索引须由驱动源码推出并写入预注册。"),
    ("U245", "M2-05 的布局为 P0（图案层在第 0 层）、P2（图案层在第 2 层）、PP1（两个图案层，第一个失败）、PP2（两个图案层，第二个失败）。新建 `driver_r8m2a2_layers.cpp`（复制品规则，从 `driver_r6b_state.cpp` 复制），用 env `S4FMM_LAYOUT` 选布局。原布局（不设该变量时）的行为逐字不变。"),
    ("U246", "M2-03 sanitizer。先跑 `san_probe_r8m2a2.sh`：只编译运行一个不链接 S4 的探针，确认 `-fsanitize=address,undefined` 可用。可用时，在 `$EV/build/san/` 构建 F3 sanitizer 库与 M2-01、M2-03 所需驱动。点集：`registries/s4r7/REGRESS_R7_M3.tsv`（G5、G6）中每个（mode × stage × inj_kind）单元格各 1 点，加 M2-01 的 17 个修复点。判定：sanitizer 报告数为 0，且 rc 与类别与非 sanitizer 运行一致。工具链不可用时标 `BUILD_FAILED`，不出点。"),
    ("U247", "本轮为 r8m2a2。结束后停下，等用户审核预注册与 NOT_FOUND 类各项的去向。M2b 只在用户审核后开始。"),
]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    if os.path.exists(APPEND):
        print("build_rulings_r8m2a2: REFUSED exists (U17): %s" % APPEND)
        return 2
    with open(RULINGS, "rb") as fh:
        cur = fh.read()
    if len(cur) != START_BYTES or hashlib.sha256(cur).hexdigest() != START_SHA:
        print("build_rulings_r8m2a2: REFUSED RULINGS.tsv is not at the start-gate state (bytes=%d)" % len(cur))
        return 2
    lines = []
    for uid, text in ROWS:
        assert "\t" not in text and "\n" not in text, uid
        lines.append("\t".join([uid, SRC + "（于 r8m2a2 登记）", text, "P05-S4 R8 M2a2 任务书 §3.1", STATUS]))
    body = "\n".join(lines) + "\n"
    os.makedirs(EV, exist_ok=True)
    with open(APPEND, "x", encoding="utf-8") as fh:
        fh.write(body)
    with open(RULINGS, "ab") as fh:
        fh.write(body.encode("utf-8"))
    print("build_rulings_r8m2a2: appended %d rows to RULINGS.tsv; append file %s" % (len(lines), APPEND))
    return 0


if __name__ == "__main__":
    sys.exit(main())
