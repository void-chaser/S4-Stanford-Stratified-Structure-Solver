# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（R6c2） | `fa7a247ff6d6b92c824b7774d4032cdbdd814bab`（R6c 第 4 节 seam 部分；里程碑 `6bba0bd`） |
| 收尾提交 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`（= 冻结树 F `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | P05-S4 子轮次 **R6c2**（R6c 续，非新阶段）：**已完成 R6c 范围第 0–6 节，等待用户审核**。报告：`P05_S4R6c2_REPORT_PART2.md` |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁与预注册；R2 三列 45 行（34 MATCH）；R3 范围内 141 点；R4 seam 25/25 REPORTED_FAILURE；R5 等价 24/24、M=2 36 点 MATCH、V4 sanitizer 0 发现、V3 132 点 IDENTICAL | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6 | R6-1 twice NTH 12–16 在 TWICE=slab 下 48 次全 MATCH（U1）；R6-2 单点 I1 实测；R6-3 RNV1 延后（U16）；R6-4 账本于 R6c2 完成 | `P05_S4R6_REPORT.md` |
| R6b | 映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑 `6bba0bd`：177 点两遍 HOLD 177 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；seam 等价 25/25、inj_call 全为 1 | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6c2 | E6c-6 哈希勘误（前 64 行字节一致）；U18 对照 18 行；判定器自检 11/11 + 原行 3/3；seam 25 点两遍 HOLD 25 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；红点总账；修复方案（无 F_CONFIRMED 候选） | `P05_S4R6c2_REPORT_PART2.md` |

## 3. 开放问题（状态 · 去向 · 链接；细节见报告附录 A 与总账）

| 项 | 状态 | 去向 |
|---|---|---|
| S3-4b（失败后模式/缓存不安装） | 本装置范围内 177 点 HOLD 177 / VIOLATED 0；seam 25 点 HOLD 25；自检 11/11。**未关闭**，关闭由用户决定（U21，范围声明见报告第 9 节） | 用户裁决 |
| 双目标注入、I7 sanitizer | DEFERRED（U9） | R7 |
| "其他层失败"变体 | DEFERRED（U20） | R7 |
| RNV1（pattern malloc 无 NULL 检查） | DEFERRED（U16）；源码 [源码] `S4/pattern/pattern.c:1477,1481,1656,1660` | R7；修复方案见 `evidence/p05-s4r6c/REPAIR_PROPOSAL_R6c.md` |
| 注释措辞 `S4/S4_internal.h:263`（U11） | HARNESS_OR_PROCESS | S3 收尾修复轮（需用户批准改 S4/） |
| 张量路径 K-1 | OPEN | R7 |
| B 侧 jones/vl SILENT_SWALLOW、nv CRASH | OPEN（基线，不是修复证据） | S5 或 R7 |
| Python/Lua 可见性、NB=1–8、类别 C、D016 B 侧 rc 20 来源 | OPEN / DEFERRED | R7 |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 |
| U2、U4 原文 | 仓库中不存在 | 待用户补录（`registries/RULINGS.tsv`） |
| ERRATA_6c 哈希（E6c-6） | HARNESS_OR_PROCESS；前 64 行已核对 | 已记入 `SHA256SUMS_closeout.txt` |

完整台账：`evidence/p05-s4r6c/RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。

## 4. 证据位置

证据目录 `checkpoints/p05/evidence/<轮次>/`（不提交）；小型结果表与清单 `checkpoints/p05/registries/<轮次>/`（提交）。R6c2 的证据目录为 `evidence/p05-s4r6c/`，清单为 `registries/s4r6c/SHA256SUMS_closeout.txt`。各轮清单见各目录的 `SHA256SUMS*.txt`。
