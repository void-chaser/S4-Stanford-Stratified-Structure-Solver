# 草稿，非签收；签收只由用户在对话中给出 — P05-S3 / P05-S4 签收范围声明（草稿 v2）

> 本文件是规划/执行侧准备的签收范围声明**草稿**，不构成签收。签收只由用户在对话中明确给出。
> 数据来源（M3d 修正版）：checkpoints/p05/evidence/p05-s4r9/m3d/ 下的 READINESS_P05_S3S4_R9M3D.tsv、
> S5_HANDOFF_R9M3D.tsv、RED_POINTS_LEDGER_FINAL_R9M3D.tsv、AUDIT_R9M3C_R9M3D.tsv；本文件由 write_signoff_v2_r9m3d.py 生成。
> 就绪计数：MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=9（共 28 行）。

## P05-S3（D003 修复范围 + S3 补充轮）

### 已验证内容
- 分配/调用点的失败清理与返回码：M1/M2 预注册矩阵与 seam 对照（证据：registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv、registries/s4r9/M2/VERDICT_R9.tsv）。
- 806、415、RP-S3R4-1：按 U225 由 M1/M2 覆盖（806=A-1/2/3，RP-S3R4-1=A-4/5/6，415 同映射规则）；状态见 READINESS 的 STATE_OPEN 行。
- RNV1（RP-R6d-1）：F2/F3/F4 全部 MATCH（U25），证据 registries/s4r6d/ 与 P05_S3R3_CLOSEOUT.md。
- K-1（RP-R6d-8）：按 U274/U281 带范围声明关闭（未复现静默吞没；张量路径范围见 U274/U281），证据 M206_DIAG_SUMMARY.txt、RESULTS_R5_K1.tsv。
- S3-4b（失败后模式/缓存不安装）：按 U29 带范围声明关闭，证据 P05_S3_4b_CLOSURE.md。
- 其他层失败变体（RP-R6d-14）：U354 关闭（M2-05 共 8 点全 MATCH，范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers；U20 的推迟由 U354 结束）。

### 证据入口
- checkpoints/p05/P05_S3R3_CLOSEOUT.md、P05_S3R4_CLOSEOUT.md、P05_S3R5_CLOSEOUT.md、P05_S3_4b_CLOSURE.md
- checkpoints/p05/registries/s4r9/M1R3/、registries/s4r9/M2/、registries/s4r9/M3d/

### 不包含内容
- 不覆盖非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）。
- 不覆盖 B 树行为（B 列不是修复证据）。
- S3 的历史自检不作为 S4 修复后验证；S4 的修后验证以 F4 上的 R9 结果为准。

## P05-S4（D003 失败传播 + Python/Lua 可见性 E2E）

### 已验证内容
- M1/M2 未修复基线对照、修复后等价与返回码：M1R3 总表与 M2 正式两遍（证据见 P05-S3 节）。
- make test 相对基线无新增失败：registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv（NO_NEW_FAILURE，8/8 reconcile 的 ok 列）。
- Python/Lua 公共 API E2E（U343/U345/U352）：E2E_OK=25、CONTROL_OK=17、其余类别 none；M3c 独立只读重判差异 0（REJUDGE_E2E_R9M3C.tsv、REJUDGE_COMPARE_R9M3C.txt）。
- 阳性对照：E2E 重判 16/16 PASS（POSCTRL_REJUDGE_R9M3C.txt）；make test 重解析 2/2 PASS。

### S1/S2 签收移交项的闭合（U356）
- S1/S2 签收范围声明第 (2) 条原文：(2) 七处 info=NULL 的 LinearSolve 修前 seam 不可测，移交 P05-S4 在冻结树上做；
- 该项移交的七处 info=NULL 的 LinearSolve 修前 seam 现以 M1R3 G6 组 R4-CL01..CL04、R4-PJ01、R4-PN01、R4-PV01（F4）的判定为闭合证据：7/7 MATCH（两遍类别 HOLD，驱动 r6bseam-seamF-F4）。
- 注意：F4 上族 B 原有的 info=NULL 锚点已不存在（P05_S4R4_REPORT.md §2 a 第 34 行：F 已把七处改为 &solve_info），所以这 7 点测的是修复后的 &solve_info 路径，不是修前 seam。
- 结论：按 U356，S1/S2 签收范围声明第 (2) 条的移交在 P05-S4 范围内已闭合。

### 证据入口
- checkpoints/p05/registries/s4r9/M3b/（E2E 正式两遍、make test 判定、预注册、校准）
- checkpoints/p05/registries/s4r9/M3d/（修正版最终红点台账、去重 S5 移交、就绪审计、P 项复核、冻结清单）
- checkpoints/p05/P05_S4R9_M3b_REPORT.md、P05_S4R9_M3c_REPORT.md、P05_S4R9_M3d_REPORT.md

### 不包含内容
- seam-only 族（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31）不出 E2E 点，由 M1/M2 覆盖行代替（U344）。
- Lua REPL 仅覆盖 cf/fft/kt/vl 四族；jones/nv/exp 无 REPL 点（范围事实，E9-63）。
- 不含 B 树行为。

### 转入 S5 的项（去重后的唯一项，U355）
- B 侧 jones/vl SILENT、nv CRASH → S5（基线观察，不是修复证据）；来源裁决：-（事实项：B 列不是修复证据）；对应台账 id：RP-R6d-6；对应 STATE：STATE §3「B 侧 jones/vl SILENT、nv CRASH」
- NB=1–8、类别 C → S5（M2-07 81 点全 MATCH；M2-08 转 S5）；来源裁决：U249；对应台账 id：RP-R6d-16;RP-R6d-17；对应 STATE：STATE §3「NB=1–8、类别 C」
- ES3R4-5/528/1164 → S5（OUT_OF_SCOPE_D003）；来源裁决：U90/U95/U99/U100；对应台账 id：-；对应 STATE：STATE §3「ES3R4-5/528/1164」
- 非 FMM S4_malloc（约 35–43 处） → S5（范围决策）；来源裁决：-（事实项：范围决策）；对应台账 id：RP-R6d-18；对应 STATE：STATE §3「非 FMM S4_malloc（约 35–43 处）」
- U2 stage e（I1 特殊规则） → S5（NOT_FOUND_IN_SCOPE）；来源裁决：U248；对应台账 id：-；对应 STATE：STATE §3「U2 stage e（I1 特殊规则）」
- RP-R6d-3 no-TWICE 路径（OUT_OF_SCOPE_D003） → S5（OUT_OF_SCOPE_D003）；来源裁决：OUT_OF_SCOPE_D003；对应台账 id：RP-R6d-3；对应 STATE：-
- RP-R6d-7 D016（B 侧 rc 来源未追踪） → S5（B 侧基线观察；F 侧归 D016/D003）；来源裁决：-（事实项：B 侧基线）；对应台账 id：RP-R6d-7；对应 STATE：-

### GAP 明细（原样列出，不得隐去）
- 无 GAP（READINESS 复算 GAP=0；台账唯一 id=26，范围内仍开放=0，TRANSFERRED_S5=6，移交唯一项=7）。

## 与 v1 的差异（逐条对应 P-1…P-6）

| 项 | v1 的问题 | v2 的修正 |
|---|---|---|
| P-1 | 台账把 RP-R6d-14 记为 TRANSFERRED_S5（依据 U20），与 M2-05 的 8 点全 MATCH 不一致 | v2 按 U354 把 RP-R6d-14 记为已关闭（M2-05 8 点全 MATCH；范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers）（复核：属实） |
| P-2 | S5 移交表 10 行去重后仅 5 项，且缺 RP-R6d-3、RP-R6d-7；台账 TRANSFERRED_S5 有 7 个 id | v2 的转入 S5 只列去重后的 7 个唯一项，并按 U355 双向核对（补入 RP-R6d-3、RP-R6d-7）（复核：属实） |
| P-3 | READINESS ① 写红点行=27（把台账表头算成数据行），台账唯一 id 是 26 | v2 的 READINESS ① 按唯一 id 去重（=26），与修正版台账一致（复核：属实） |
| P-4 | 签收草稿 v1 的转入 S5 项 10 条含重复，且缺 RP-R6d-3、RP-R6d-7 | v2 的转入 S5 项每项注明来源裁决，无重复、无缺项（复核：属实） |
| P-5 | v1 未说明 S1/S2 范围声明第 (2) 条的 info=NULL seam 移交已闭合 | v2 新增“S1/S2 签收移交项的闭合（U356）”一节，注明 F4 上 info=NULL 锚点已不存在（复核：属实） |
| P-6 | v1 的 READINESS 中 RP-R6d-15 行仍是“待用户审核”旧措辞，裁决列写“见 STATE 行” | v2 的 READINESS 每行裁决号为真实 U 编号或“-（事实项）”，RP-R6d-15 行改用 U345/U352，无“见 STATE 行”（复核：属实） |

> 再次声明：本文件是**草稿，非签收**；签收只由用户在对话中给出。
