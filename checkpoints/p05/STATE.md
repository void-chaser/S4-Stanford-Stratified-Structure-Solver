# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（R7，E7-2） | `8e13729635c20dc658abc2a35e8195b26e3b9bec`（S3R3 报告状态提交；R7 开工时的 HEAD） |
| 收尾提交 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F2） | `e124925f5b242486a913b813fa181664f665b048`（F2 提交 `a07b5ac`；前一冻结树 F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | P05-S4 子轮次 **R7**（F2 回归，非新阶段）：门禁、构建、seam diff、无注入等价已完成；注入矩阵未运行；下一步 M1（RNV1 回归）。第一段见 `P05_S4R7_REPORT_PART1.md`。S3R3 报告 `P05_S3R3_CLOSEOUT.md`；S3-4b 由用户关闭（U29）。R7 未宣布任何阶段完成或签收 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁与预注册；R2 三列 45 行（34 MATCH）；R3 范围内 141 点；R4 seam 25/25 REPORTED_FAILURE；R5 等价 24/24、M=2 36 点 MATCH、V4 sanitizer 0 发现、V3 132 点 IDENTICAL | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6 | R6-1 twice NTH 12–16 在 TWICE=slab 下 48 次全 MATCH（U1）；R6-2 单点 I1 实测；R6-3 RNV1 延后（U16）；R6-4 账本于 R6c2 完成 | `P05_S4R6_REPORT.md` |
| R6b | 映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑 `6bba0bd`：177 点两遍 HOLD 177 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；seam 等价 25/25、inj_call 全为 1 | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6c2 | E6c-6 哈希勘误（前 64 行字节一致）；U18 对照 18 行；判定器自检 11/11 + 原行 3/3；seam 25 点两遍 HOLD 25 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；红点总账；修复方案（无 F_CONFIRMED 候选） | `P05_S4R6c2_REPORT_PART2.md` |
| R6d | U2 阶段表 202 点 CONSISTENT / 0 CONFLICT / 0 UNRESOLVED（a2 b197 c1 d2 e0；e 未覆盖，去向 R8）；RNV1 注入 F 72/72 CRASH（两遍）→ RP-R6d-1 **F_CONFIRMED**；账本 v2 20 行（R6c 22 条全部映射）；方案 v2（S4/ 未改） | `P05_S4R6d_REPORT.md` |
| S3R3 | 修复 `a9679bc`（pattern.c，方案 R3）、注释 `a07b5ac`（U31）；冻结 F2 `e124925f…`；编译：dbg 与 plain 告警数与 F 相同（62/71），逐条无新增；自检 A：F2 RNV1 36 点两遍 REPORTED_FAILURE 36/36（自检通过，未验证为修复后 S4 结果）；自检 C：F tri 3 点 CRASH、F2 3 点 REPORTED_FAILURE；B：无注入 F vs F2 call1–3 共 36 项 IDENTICAL；D：nv/vl NG9 冒烟 rc 0 | `P05_S3R3_CLOSEOUT.md` |

## 3. 开放问题（状态 · 去向 · 链接；细节见报告附录 A 与总账）

| 项 | 状态 | 去向 |
|---|---|---|
| S3-4b（失败后模式/缓存不安装） | **由用户带范围声明关闭（U29）**，只关闭此项，不代表 P05-S3/S4 签收；范围声明见 `P05_S3_4b_CLOSURE.md`；未覆盖：阶段 e、I7、双目标注入、其他层失败变体 | 转 R8（F2 上） |
| 双目标注入、I7 sanitizer | DEFERRED（U9） | R8（U25，E7-1） |
| "其他层失败"变体 | DEFERRED（U20） | R8（U25，E7-1） |
| RNV1（pattern malloc 无 NULL 检查，RP-R6d-1） | F 上 CRASH（R6d）；S3R3 采用方案 R3（U30，提交 `a9679bc`）；F2 自检通过（REPORTED_FAILURE），**未经 S4 验证**，R7 在 F2 上回归 | R7（F2） |
| 注释措辞 `S4/S4_internal.h:263`（U11） | 已改为 U31 措辞（提交 `a07b5ac`） | R7 回归确认 |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]，未测） | R8 |
| B 侧 jones/vl SILENT_SWALLOW、nv CRASH | OPEN（基线，不是修复证据） | S5 或 R7 |
| Python/Lua 可见性、NB=1–8、类别 C | OPEN / DEFERRED | R8（U34，E7-1） |
| D016 B 侧 rc 20 来源 | OPEN | R7（F2 回归观察；RP-R6d-7） |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录（`registries/RULINGS.tsv` 的 `-补录` 行）；U2 部分落实（U28） | U2 逐条覆盖见 `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv`；S3-4b 关闭由用户决定 |
| U2 中 stage e（I1 特殊规则） | 0 点，**未覆盖** | R8 |
| 阶段 b 依据强度（E6d-7） | 源码依据为 SITEMAP caller；日志只证明 HIT 在失败层窗口内，不是 FMM 函数边界 | 披露（不改判定） |
| B 侧 vl NG=1 rc 20 与 D016 B 侧来源 | F 侧同一路径（pattern −10）；B 侧未解释 | R7（RP-R6d-7，BASELINE_ONLY） |
| ERRATA_6c 哈希（E6c-6） | HARNESS_OR_PROCESS；前 64 行已核对 | 已记入 `SHA256SUMS_closeout.txt` |

完整台账：`evidence/p05-s4r6c/RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。

## 4. 证据位置

证据目录 `checkpoints/p05/evidence/<轮次>/`（不提交）；小型结果表与清单 `checkpoints/p05/registries/<轮次>/`（提交）。R6c2 的证据目录为 `evidence/p05-s4r6c/`，清单为 `registries/s4r6c/SHA256SUMS_closeout.txt`。R6d 的证据目录为 `evidence/p05-s4r6d/`，小型表与清单为 `registries/s4r6d/`。各轮清单见各目录的 `SHA256SUMS*.txt`。
