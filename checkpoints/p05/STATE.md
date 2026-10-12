# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（S3R4 续2 开工） | `0b1b4a307f9a8cfaba06ba892a91182e59d8e48e` |
| 收尾提交 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`，P05-S3R4 修复候选；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S3 子轮次 S3R4 续2**（非新阶段）：续1 在 §2 后停止（U103）；续2 提交记录（`45d17d5`、`d64c552`）、U105 删除空目录；自检 **C 多边形通过**（33 组合，99/99 IDENTICAL，驱动 rc 全 0）；**A1 映射 K 唯一确定**，A 预注册写定（18 行）但**注入运行未执行**；**B、D 未完成**；续2 因写入规则违规（U106：`link_c2.sh`、`link_init_c2.sh` 含 `2>/dev/null`）按停止条件中止。S3R4 整体未完成，等待用户审核。报告：`P05_S3R4_CLOSEOUT.md`、`P05_S3R4_CLOSEOUT_CONT1.md`、`P05_S3R4_CLOSEOUT_CONT2.md`。下一步（U92）：P05-S4 R8 在 F3 上（A、B、D 的补跑由用户指示续3）。 |
| 历史 | S3R4 首轮：修复 806、415 链路、RP-S3R4-1 冻结 F3 `8d8202a`（U91 四个文件，U96 单提交）；编译告警零新增。P05-S4 R7 完成 M1–M3（F2 回归；M3 收尾 `cc49c6b`，建议待裁决）。未签收。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁与预注册；R2 三列 45 行（34 MATCH）；R3 范围内 141 点；R4 seam 25/25 REPORTED_FAILURE；R5 等价 24/24、M=2 36 点 MATCH、V4 sanitizer 0 发现、V3 132 点 IDENTICAL | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6 | R6-1 twice NTH 12–16 在 TWICE=slab 下 48 次全 MATCH（U1）；R6-2 单点 I1 实测；R6-3 RNV1 延后（U16）；R6-4 账本于 R6c2 完成 | `P05_S4R6_REPORT.md` |
| R6b | 映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑 `6bba0bd`：177 点两遍 HOLD 177 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；seam 等价 25/25、inj_call 全为 1 | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6c2 | E6c-6 哈希勘误（前 64 行字节一致）；U18 对照 18 行；判定器自检 11/11 + 原行 3/3；seam 25 点两遍 HOLD 25 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；红点总账；修复方案（无 F_CONFIRMED 候选） | `P05_S4R6c2_REPORT_PART2.md` |
| R6d | U2 阶段表 202 点 CONSISTENT / 0 CONFLICT / 0 UNRESOLVED（a2 b197 c1 d2 e0；e 未覆盖，去向 R8）；RNV1 注入 F 72/72 CRASH（两遍）→ RP-R6d-1 **F_CONFIRMED**；账本 v2 20 行；方案 v2（S4/ 未改） | `P05_S4R6d_REPORT.md` |
| S3R3 | 修复 `a9679bc`（pattern.c，方案 R3）、注释 `a07b5ac`（U31）；冻结 F2 `e124925f…`；编译告警 62/71 零新增；自检 A：F2 RNV1 36 点 REPORTED_FAILURE 36/36（未经 S4 验证）；自检 C：F tri 3 点 CRASH、F2 3 点 REPORTED_FAILURE；B 无注入 36 项 IDENTICAL；D：nv/vl NG9 冒烟 rc 0 | `P05_S3R3_CLOSEOUT.md` |
| S3R4 | 修复 806、415、RP-S3R4-1，冻结 F3 `8d8202a`（编译告警 62/71 零新增）；自检 C 圆形/三角 117/117 IDENTICAL（首轮）；续1 停止（U103）；续2：C 多边形 99/99 IDENTICAL、驱动 rc 66/66 为 0；A1 映射 K 唯一（closed2d NG1 K=7、fft/kottke NG5 K=8，K0=6/7）；A 预注册 18 行；A、B、D **未完成**（续2 违规 U106 停止） | `P05_S3R4_CLOSEOUT.md`、`P05_S3R4_CLOSEOUT_CONT1.md`、`P05_S3R4_CLOSEOUT_CONT2.md` |
| S4R7 | M1、M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254 MATCH + 44 NOT_REACHED、G2a 50，MISMATCH 0、FLAKY 0）、M3（G5 177、G6 25，VIOLATED 0） | `P05_S4R7_REPORT_FINAL.md`、`P05_S4R7_REPORT_M2_FINAL.md` |

## 3. 开放问题（状态 · 去向 · 链接；细节见报告附录 A 与总账）

| 项 | 状态 | 去向 |
|---|---|---|
| S3-4b（失败后模式/缓存不安装） | **由用户带范围声明关闭（U29）**，只关闭此项，不代表 P05-S3/S4 签收；范围声明见 `P05_S3_4b_CLOSURE.md`；未覆盖：阶段 e、I7、双目标注入、其他层失败变体 | 转 R8（F3 上） |
| S3R4 自检 A 注入运行、B、D | 未完成（续2 写入规则违规 U106 后停止；预注册 A 与 K 已就绪） | 续3（用户指示）→ R8 前完成 |
| 806、415、RP-S3R4-1 的自检结果 | 修复已提交；自检 C（无注入）通过；注入自检未完成 | R8（F3 上） |
| RNV1（pattern malloc 无 NULL 检查，RP-R6d-1） | F 上 CRASH（R6d）；S3R3 采用方案 R3（U30，提交 `a9679bc`）；F2 自检通过，未经 S4 验证；S3R4 修复后 F3 | R8（F3 上，U92） |
| 双目标注入、I7 sanitizer | DEFERRED（U9） | R8（U25，E7-1） |
| "其他层失败"变体 | DEFERRED（U20） | R8（U25，E7-1） |
| 注释措辞 `S4/S4_internal.h:263`（U11） | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]，未测） | R8 |
| B 侧 jones/vl SILENT_SWALLOW、nv CRASH | OPEN（基线，不是修复证据） | S5 |
| Python/Lua 可见性、NB=1–8、类别 C | OPEN / DEFERRED | R8（U34，E7-1） |
| ES3R4-5(a)(b)（首个形状返回码 i+1；pattern.c:798 循环变量 i/j） | OUT_OF_SCOPE_D003（U99、U95） | S5 |
| −1…−9（Pattern_DiscretizeCell 在 FFT/Kottke 中被忽略） | OUT_OF_SCOPE_D003（U100；[源码] 说明未写） | S5 |
| 528、1164（S3R4 U90 分类） | OUT_OF_SCOPE_D003（无调用者；唯一调用点已注释） | S5 |
| D016 B 侧 rc 20 来源；B 侧 vl NG=1 rc 20 | OPEN（BASELINE_ONLY） | R7 观察 → S5 |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录；U2 部分落实（U28） | U2 覆盖见 `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | 0 点，**未覆盖** | R8 |

完整台账：`evidence/p05-s4r6c/RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`（U103–U106 已追加）。

## 4. 证据位置

证据目录 `checkpoints/p05/evidence/<轮次>/`（不提交）；小型结果表与清单 `checkpoints/p05/registries/<轮次>/`（提交）。S3R4 续2：证据 `evidence/p05-s3r4c2/`，小表与清单 `registries/s3r4c2/`。S3R4 续1：证据 `evidence/p05-s3r4c1/`（仅门禁与 safe_run 日志）。R6c2：`evidence/p05-s4r6c/`，清单 `registries/s4r6c/SHA256SUMS_closeout.txt`。R6d：`evidence/p05-s4r6d/`，小表与清单 `registries/s4r6d/`。各轮清单见各目录的 `SHA256SUMS*.txt`。
