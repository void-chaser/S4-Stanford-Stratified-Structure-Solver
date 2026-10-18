# P05-S4 R9 M3d 报告：修正版签收材料（红点台账 / S5 移交 / 就绪审计 / 签收草稿 v2）

> 轮次标识 r9m3d。本轮只做只读复核与修正版材料，不运行 S4 的任何程序（不跑 make、make test、E2E、d003 矩阵、gdb，不构建）。
> 不宣布任何阶段完成或签收；签收只由用户在对话中给出。

## 1 门禁

| 项 | 结果 |
|---|---|
| HEAD | c4f67071e80f8dd573f3653c04250708e7339b7f（与任务书一致） |
| HEAD:S4（冻结树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| git status --short（start 门禁时刻） | 空（tracked 无改动；未跟踪项全部在 start 允许清单内） |
| /tmp 顶层快照 | 条目数 0，sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| RULINGS.tsv（start） | 142281 字节，sha 443d8a38…（前缀断言），最大 U350 |
| ERRATA_9.txt（start） | 56754 字节，sha 9bd2933d…（前缀断言），最后 E9-66，共 66 条 |
| registries/s4r9/M3c/SHA256SUMS.txt | 全部 OK（13 项） |
| m3c 证据目录 SHA256SUMS.txt | 全部 OK（16 项） |
| 历史清单 s3r5/M0/M1/M1R2/M1R3/M1R4/M2/M2b/M2c/M3a/M3b/M3c | 全部 OK（项数 14/25/28/33/26/11/14/13/11/17/18/13，由脚本数出后断言） |
| start 门禁断言 | PASS=48 FAILS=0（total=48，无 SKIP） |

start 门禁输出：m3d/GATE_R9M3D_start.txt；start 前缀复核：m3d/GATE_R9M3D_start_RECHECK.txt（数字见附录 A）。

## 2 §3 P 项复核（AUDIT_R9M3C_R9M3D.tsv）

| 项 | 判定 | 实际值（由脚本从原文件算出） |
|---|---|---|
| P-1 | 属实 | M2-05 行 8 个（4 注入点 P0/P2/PP1/PP2 + 4 对照，含 M2-05-P0-F4-C）全部 MATCH；U245 定义 P0/P2/PP1/PP2 与 driver_r8m2a2_layers；台账 RP-R6d-14 状态 TRANSFERRED_S5、依据 U20，位置描述“two layers with a pattern; pattern layer not at position 1”与 U245 布局对应 |
| P-2 | 属实 | M3c 移交 10 个数据行，规范化去重 5 项；台账 TRANSFERRED_S5 有 7 个 id（RP-R6d-3/-6/-7/-14/-16/-17/-18）；RP-R6d-3、RP-R6d-7 无对应项（RP-R6d-14 同样无对应项，本轮由 U354 关闭，不再转 S5） |
| P-3 | 属实 | READINESS ① 写“红点行=27”，台账唯一 id 数=26，台账非注释非空行=27（含表头）；多算 1 行=台账表头（第 13 行）。成因：testing/d003/stage_s4r9/readiness_r9m3c.py 第 108–117 行的循环未跳过表头，第 117 行 ledger_rows += 1 把表头算成一行 |
| P-4 | 属实 | 签收草稿 v1“转入 S5 的项”10 条，规范化去重 5；缺 RP-R6d-3，缺 RP-R6d-7 |
| P-5 | 属实 | M1R3 G6 组 7 点（R4-CL01/02/03/04、R4-PJ01、R4-PN01、R4-PV01，树 F4）全部 MATCH，驱动 r6bseam-seamF-F4，两遍类别均 HOLD；P05_S1_S2_SIGNOFF.md §2 第 (2) 条原文存在；签收草稿 v1 未说明该移交已闭合 |
| P-6 | 属实 | READINESS 的 RP-R6d-15 行 state 仍是“…待用户审核”旧措辞；裁决列写“见 STATE 行”的行数=16（共 26 行） |

复核结论：6/6 属实。因此 U354 的前提（P-1）与 U356 的前提（P-5）成立，两条裁决状态记为“生效”。

## 3 裁决与勘误

- 裁决：append_rulings_r9m3d.py 以“旧文件 + 新行”追加 U351–U358（5 列，前缀 sha 断言通过）。RULINGS.tsv 142281 → 145103 字节，sha 443d8a38… → 21ab76d2…，RULINGS 最大 U358。
- 勘误：append_errata_r9m3d.py 追加 E9-67–E9-73（P-1…P-6 各一条 + U353 一条）。ERRATA_9.txt 56754 → 62654 字节，sha 9bd2933d… → d71543bb…，ERRATA_9.txt 最后 E9-73，共 73 条。
- U354/U356 的状态由 append_rulings 现场复核 P-1/P-5 后写入（均为“生效”）；append_errata 在写入前交叉核对 RULINGS 中的状态与 AUDIT 判定一致。

## 4 修正版台账、移交与就绪审计

### 4.1 最终红点台账（RED_POINTS_LEDGER_FINAL_R9M3D.tsv）

- 唯一 id 26（数据行 26），非红点行 4，范围内仍开放 0，冲突 21 处（沿用 M3c 的冲突登记）。
- TRANSFERRED_S5=6：RP-R6d-3、RP-R6d-6、RP-R6d-7、RP-R6d-16、RP-R6d-17、RP-R6d-18。
- 变更清单（文件尾逐条登记“旧状态→新状态 | 依据裁决”）：

| id | 旧状态 → 新状态 | 依据裁决 |
|---|---|---|
| RP-R6d-14 | TRANSFERRED_S5 → CLOSED | U354（M2-05 8 点全 MATCH；范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers） |
| RP-R6d-15 | CLOSED → CLOSED（关闭依据 U345 → U345/U352） | U352（S-B 独立复核 DIFFS=0，U345 关闭条件成立） |

### 4.2 S5 移交清单（S5_HANDOFF_R9M3D.tsv，去重后）

- 唯一项 7（M3c 移交 10 行 → 5 个唯一项；按 U355 补入 RP-R6d-3、RP-R6d-7；RP-R6d-14 由 U354 关闭，不再转 S5）。S5 移交：唯一项 7。
- 双向核对：台账 6 个 TRANSFERRED_S5 id 全部出现在移交表中；移交表 7 项每项都对应台账 id 或 STATE 行，无孤项（s5_handoff 任一向有孤项即报错退出）。

| item_id | 规范化名称 | 对应台账 id | 对应 STATE 行 |
|---|---|---|---|
| S5-M3D-01 | B 侧 jones/vl SILENT、nv CRASH | RP-R6d-6 | STATE §3 B 侧行 |
| S5-M3D-02 | NB=1–8、类别 C | RP-R6d-16;RP-R6d-17 | STATE §3 NB 行 |
| S5-M3D-03 | ES3R4-5/528/1164 | 无 | STATE §3 ES3R4 行 |
| S5-M3D-04 | 非 FMM S4_malloc（约 35–43 处） | RP-R6d-18 | STATE §3 非 FMM 行 |
| S5-M3D-05 | U2 stage e（I1 特殊规则） | 无 | STATE §3 U2 stage e 行 |
| S5-M3D-06 | RP-R6d-3 no-TWICE 路径（OUT_OF_SCOPE_D003） | RP-R6d-3 | 无（台账 id 项） |
| S5-M3D-07 | RP-R6d-7 D016（B 侧 rc 来源未追踪） | RP-R6d-7 | 无（台账 id 项） |

### 4.3 就绪审计（READINESS_P05_S3S4_R9M3D.tsv）

- 共 28 行：MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=9。
- 第①条按唯一 id 去重：红点唯一 id 数=26，等于修正版台账的唯一 id 数；范围内仍开放=0。
- U357：0 行的裁决列写“见 STATE 行”；每行裁决号为 RULINGS.tsv 中真实存在的 U 编号或“-（事实项）”；RP-R6d-15 行改用 U345/U352。
- STATE 同步（U358）：开放问题表新增“其他层失败变体（RP-R6d-14）| U354 关闭”和“S1/S2 移交：七处 info=NULL seam | U356 闭合”两行，RP-R6d-15 行改为 U345/U352；STATE 6636 字节（≤8192，最终值见附录 A）。

## 5 签收草稿 v2 摘要

- 文件：checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md；首行与标题均写明“草稿，非签收；签收只由用户在对话中给出”。
- P05-S3 一节补上：806、415、RP-S3R4-1（U225）、RNV1（U25）、K-1（U274/U281 范围声明）、S3-4b（U29）、其他层失败变体（U354）。
- P05-S4 一节新增“S1/S2 签收移交项的闭合（U356）”小节：7/7 MATCH，并注明 F4 上族 B 原有的 info=NULL 锚点已不存在（P05_S4R4_REPORT.md §2 第 a 条），所以这 7 点测的是修复后的 &solve_info 路径。
- “转入 S5 的项”只列去重后的 7 个唯一项，每项注明来源裁决；“与 v1 的差异”表逐条对应 P-1…P-6。
- READINESS 无 GAP，草稿原样写明“无 GAP”。

## 6 事件两张表

### 6.1 表一：越界写入尝试

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| r9m3d | 无 | 否 | 本轮所有含写入的命令均经 safe_run，写入目标全部在仓库内（$EV/、stage_s4r9/、checkpoints/p05/） |

### 6.2 表二：工具与脚本事件

| # | 事件 | 处理 |
|---|---|---|
| 1 | 门禁与收尾脚本在 start 门禁之前写好（运行 start 门禁本身需要这些脚本） | 照实披露；start 门禁在其时刻的开工不变量全部成立（PASS=48 FAILS=0）；此后严格按 §5 顺序执行 |
| 2 | 收尾链试跑在冻结清单写定之前运行（§5 要求“收尾链试跑 → 冻结清单”） | 照实披露；试跑期 end 门禁的 FROZEN 来源检查（POST_I 调用计数、EVENTS 锚点、证据清单截断头、冻结 sha）标 SKIP，正式冻结期 end 门禁从 FROZEN 读取并全部执行 |
| 3 | append_errata_r9m3d.py v1 存在 5 元组解包错误（运行即退出，未写入任何字节） | 照实披露；修正后通过，ERRATA 前缀 sha 断言仍通过、落账 E9-67–E9-73 |
| 4 | 框架落盘：/tmp/dsh-spill-* 属框架，不算执行者违规 | 单列，不计入表一；start/end 门禁各记录一次 /tmp 快照 |

## 7 需用户裁决

1. 修正版材料（红点唯一 id 26、S5 移交唯一项 7、READINESS 28 行 MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=9、签收草稿 v2）是否作为签收前的唯一现行版本（U358）。
2. M3c 已提交产物保持不改（U358）；签收草稿 v1→v2 的 P-1…P-6 六条差异是否需要用户逐条确认。
3. P-1/P-5 复核均属实，U354/U356 记为“生效”；若用户对 M2-05 的 8 点范围或 7 点 seam 覆盖有不同意见，可另行裁决（本轮不改判）。
4. S5 移交 7 项中有 2 项（ES3R4-5/528/1164、U2 stage e）没有台账 id，按 U355 以 STATE 行为对应；请确认该对应方式。
5. 本轮不宣布 P05-S3/P05-S4 完成或签收；签收草稿 v2 仅作范围声明材料。

## 8 本轮状态与结论

- 本轮只做只读复核，未运行 S4 的任何程序；S4/、判定器、历史装置、M3c 已提交产物均未修改（由 end 门禁按 BASE 前缀校验）。
- P 项复核 6/6 属实；U351–U358 落账；E9-67–E9-73 落账。
- 本轮已完成 R9 M3d 范围，等待用户审核。

## 9 交付物清单

### 9.1 小表交付物

以下 12 项复制到 checkpoints/p05/registries/s4r9/M3d/（前 11 项 + SHA256SUMS.txt 清单），与 m3d/ 下的原件逐项比对 sha256 一致。

1. AUDIT_R9M3C_R9M3D.tsv
2. FROZEN_SCRIPTS_R9M3D.tsv
3. GATE_R9M3D_start.txt
4. GATE_R9M3D_start_RECHECK.txt
5. POSCTRL_HANDOFF_R9M3D.txt
6. POSCTRL_READINESS_R9M3D.txt
7. POSCTRL_REPORT_CHECK_R9M3D.txt
8. READINESS_P05_S3S4_R9M3D.tsv
9. RED_POINTS_LEDGER_FINAL_R9M3D.tsv
10. REPORT_CHECK_R9M3D.txt
11. S5_HANDOFF_R9M3D.tsv
12. SHA256SUMS.txt

### 9.2 证据目录与其它产物

- 证据目录：checkpoints/p05/evidence/p05-s4r9/m3d/（SHA256SUMS.txt 覆盖全部非二进制证据，仅 m3d/gate/ 与 tmp/ 除外；end 门禁输出在 m3d/gate/，不纳入清单）。
- 报告：checkpoints/p05/P05_S4R9_M3d_REPORT.md；签收草稿：checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md；任务书：checkpoints/p05/briefs/P05_S4R9_BRIEF_M3d.md。
- 轮次脚本：testing/d003/stage_s4r9/ 下 21 个 r9m3d 脚本（清单见 FROZEN_SCRIPTS_R9M3D.tsv）。

### 附录 A（closeout 由表计算生成）

（APPENDIX_A_PLACEHOLDER）

### 附录 B（end 门禁）

（APPENDIX_B_PLACEHOLDER）
