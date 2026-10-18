# 草稿，非签收；签收只由用户在对话中给出 — P05-S3 / P05-S4 签收范围声明（草稿）

> 本文件是规划/执行侧准备的签收范围声明草稿，不构成签收。签收只由用户在对话中明确给出。
> 数据来源：checkpoints/p05/evidence/p05-s4r9/m3c/READINESS_P05_S3S4_R9M3C.tsv（只读复算）与 S5_HANDOFF_R9M3C.tsv。
> 就绪计数：MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=7（共 26 行）。

## P05-S3（D003 修复范围 + S3 补充轮）

### 已验证内容
- 分配/调用点的失败清理与返回码：M1/M2 预注册矩阵与 seam 对照（证据：registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv、registries/s4r9/M2/VERDICT_R9.tsv、registries/s4r9/M1R3/POSCTRL_M1_R9M1R3.txt）。
- 失败后模式/缓存不安装（S3-4b）：按 U29 带范围声明关闭（证据：P05_S3_4b_CLOSURE.md）。
- I2 注释与 S4_internal.h:263 措辞：按 U8/U11/U31 关闭（证据：F2/F3/F4 树与 M1R3 判定）。

### 证据入口
- checkpoints/p05/P05_S3R3_CLOSEOUT.md、P05_S3R4_CLOSEOUT.md、P05_S3R5_CLOSEOUT.md、P05_S3_4b_CLOSURE.md
- checkpoints/p05/registries/s4r9/M1R3/、registries/s4r9/M2/

### 不包含内容
- 不覆盖非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）。
- 不覆盖 B 树行为（B 列不是修复证据）。
- S3 的历史自检不作为 S4 修复后验证；S4 的修后验证以 F4 上的 R9 结果为准。

## P05-S4（D003 失败传播 + Python/Lua 可见性 E2E）

### 已验证内容
- M1/M2 未修复基线对照、修复后等价与返回码：M1R3 总表与 M2 正式两遍（证据见上）。
- make test 相对基线无新增失败：registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv（NO_NEW_FAILURE，8/8 reconcile 的 ok 列）。
- Python/Lua 公共 API E2E（U343/U345）：E2E_OK=25、CONTROL_OK=17、其余类别 none；本轮独立只读重判差异 0（REJUDGE_E2E_R9M3C.tsv、REJUDGE_COMPARE_R9M3C.txt）。
- 阳性对照：E2E 重判 16/16 PASS（POSCTRL_REJUDGE_R9M3C.txt）；make test 重解析 2/2 PASS。

### 证据入口
- checkpoints/p05/registries/s4r9/M3b/（E2E 正式两遍、make test 判定、预注册、校准）
- checkpoints/p05/registries/s4r9/M3c/（本轮独立复核、复验、就绪审计、最终红点台账、冻结清单）
- checkpoints/p05/P05_S4R9_M3b_REPORT.md、P05_S4R9_M3c_REPORT.md

### 不包含内容
- seam-only 族（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31）不出 E2E 点，由 M1/M2 覆盖行代替（U344）。
- Lua REPL 仅覆盖 cf/fft/kt/vl 四族；jones/nv/exp 无 REPL 点（范围事实，E9-63）。
- 不含 B 树行为。

### 转入 S5 的项
- B 侧 jones/vl SILENT、nv CRASH → S5（来源：STATE.md:46）
- NB=1–8、类别 C → S5（来源：STATE.md:47）
- ES3R4-5/528/1164 → S5（来源：STATE.md:50）
- 非 FMM `S4_malloc`（约 35–43 处） → S5（来源：STATE.md:52）
- U2 stage e（I1 特殊规则） → S5（来源：STATE.md:54）
- B 侧 jones/vl SILENT_SWALLOW、nv CRASH → S5（基线观察，不是修复证据）（来源：P05_S1R_O1_ATTRIBUTION.md）
- NB=1–8、类别 C（M2-08） → S5（U249）（来源：registries/RULINGS.tsv U249）
- ES3R4-5/528/1164 → S5（U90/U95/U99/U100，OUT_OF_SCOPE_D003）（来源：registries/RULINGS.tsv）
- 非 FMM S4_malloc（约 35–43 处） → S5（范围决策）（来源：PROJECT_ROADMAP.md）
- U2 stage e（I1 特殊规则） → S5（U248，NOT_FOUND_IN_SCOPE）（来源：registries/RULINGS.tsv）

### GAP 明细（原样列出，不得隐去）
- 无 GAP（READINESS 复算 GAP=0）。

> 再次声明：本文件是草稿，非签收；签收只由用户在对话中给出。
