# P05-S5 R1 注册表补丁草案（P05_S5_REGISTRY_PATCH_DRAFT）

> 本文件只写草案，不应用到测试登记表与路线图。
> 行号取自本轮 git rev-parse HEAD = 59e742d5b918b9c194f3aec10148801f7839f263（P05-S4 R9 M3e (ii)）。
> 本文件不含任何阶段完成或 P05-S5 签收的字样；P05-S5 未完成、未签收。

## 1. 依据与口径

- 签收范围声明原文：checkpoints/p05/P05_S3_S4_SIGNOFF.md 第 2 节（物理行 18；逐字照录，本草案不改写）。
- S1/S2 范围声明原文：checkpoints/p05/P05_S1_S2_SIGNOFF.md 第 2 节（物理行 21–25）。
- B 列观察不是修复证据（U359 范围声明 (a)）；S5 只做前端与回归，不重跑 B 树。
- 本草案的新增登记行一律不写已修复/已验证，只写已实施（源码确认）或未验证/未实测，并注明证据。

## 2. testing/s4test/ISSUE_REGISTRY.md 逐条 unified diff 草案

### 2.1 D003 行（物理行 28）状态与关闭范围核对

依据：P05_S3_S4_SIGNOFF.md 第 2 节 (a)(f)；P05_S4R9_M2_REPORT.md（F4 正式两遍 191/191 MATCH）；P05_S4R9_M3b_REPORT.md（E2E_OK=25、CONTROL_OK=17）。

```diff
--- a/testing/s4test/ISSUE_REGISTRY.md
+++ b/testing/s4test/ISSUE_REGISTRY.md
@@ -28,1 +28,2 @@
 | D003 / P1 | FFT prepare/execute 失败处理及上层传播不完整 | checkpoint 已含 FFT wrapper/kiss FFT/网格路径的部分处理。历史六文件 FMM 候选和 runner 存在；完整候选未生产验收/集成 | 列实际计算分支、计划/执行调用点；复用候选与现有注入器，补缺口；失败不得安装模式/缓存；恢复后重试与全新对象一致；Python/Lua 报错可见 |
+> 2026-10-18 P05-S4 R9 收尾记录：S3-4b（失败后模式/缓存不安装）由 U29 在 F4 上带范围声明关闭（202 注入点 HOLD 202/VIOLATED 0）；F4 上 M2 正式两遍 191/191 MATCH、M1R3 651 点两遍全 MATCH；Python/Lua 前端由 M3b E2E 覆盖（E2E_OK=25、CONTROL_OK=17）。签收范围声明见 P05_S3_S4_SIGNOFF.md 第 2 节。D003 本身仍为 OPEN；P05-S5 是否以 S4 证据作为前端与回归证据待用户裁决（Q1）。
```

### 2.2 D016 行（物理行 41）核对结果

- 核对结论：D016 的最小修法已在 P05-S3R2 提交 3e77aa9 实施（S4/pattern/pattern.c：max_field 零/非有限时返回 -10；负值为分配失败 -11）。F4 源码位置：S4/pattern/pattern.c 物理行 2210–2216（[源码]，本轮未运行）。
- 过期文字：现行 D016 行仍写待 P05-S3 实施/实施前状态为未关闭，需更新。
- 未实测项：D016 的公共异常文本（Python）在 S3R2 未实测（P05_S3R2_CLOSEOUT.md 物理行 186、187）；列入 S5R2 NEEDS_TEST（Q2）。
- 依据：P05_S3R2_CLOSEOUT.md 物理行 17、38、104、186；S4/pattern/pattern.c 2210–2216。

```diff
@@ -41,1 +41,1 @@
 | D016 / P1（P05 期间提前登记；P05-S5 时核对） | 图案层向量场归一化遇到全零场时除以零得到 NaN 并仍返回成功 ... | 2026-10-11 P05-S1R 实测 ... | 最小修法（待 P05-S3 实施 ...）： ... 实施前状态为未关闭 |
+ | D016 / P1（P05-S5 核对完成） | 图案层向量场归一化遇到全零场时除以零得到 NaN 并仍返回成功 | 2026-10-11 P05-S1R 实测：VL 基 n_G=1 时 max_field=0，NaN 进入特征值求解，info=2、rc 20（B/A/H 三树一致）。修法已实施：P05-S3R2 提交 3e77aa9，pattern.c 的 1./max_field 之前检查 max_field 为零/非有限并返回 -10（负值为分配失败 -11）；F4 源码位置 pattern.c 2210–2216（[源码]）。公共异常文本（Python）尚未实测 | 现状：已实施（源码确认），未做 D016 的 Python 文本实测；S5R2 补测（Q2）。R-P05-01（让 n_G=1 可计算）不包含在本条，见 ISSUE_REGISTRY 第 114 行 |
```

### 2.3 非 FMM S4_malloc 另立登记项（新增行草案）

- 依据：用户范围决策（STATE.md 范围决策摘要；S5_HANDOFF_R9M3D.tsv S5-M3D-04）：分配/调用点处于模式或缓存是否被安装的验收路径或 FMM/FFT 失败传播链则纳入 D003，非 FMM 其余约 35–43 处不属 D003/P05。
- 编号：建议 D017（ISSUE_REGISTRY.md 更新规则：新缺陷追加 D016 起；具体编号请用户批准，Q7）。

```diff
@@ -41,0 +43,1 @@ （在 D016 行之后插入）
+| D017 / P2（P05-S5 期间登记；不在 P05 修） | 非 FMM 路径的 S4_malloc 失败未逐点检查/未统一传播（约 35–43 处，非 D003 范围） | 用户范围决策：只有处于模式/缓存是否被安装验收路径或 FMM/FFT 失败传播链上的分配点纳入 D003；非 FMM 其余分配点不属 D003/P05。未验证：未逐点列出调用位置与失败行为 | S5 登记：逐点列出函数:行号、调用者与失败后果；按 P0/P1/P2 风险分级；不在 P05 修，不阻塞 P06 |
```

### 2.4 ES3R4-5/528/1164、U99、U100 登记（新增行草案）

- 依据：RULINGS.tsv U90（528/1164 OUT_OF_SCOPE_D003 转 P05-S5）、U95（ES3R4-5(a)(b)）、U99（pattern.c:798 内层循环用 i 而非 j；修它会改变正常路径）、U100（FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9，仅 -12 被处理）；ERRATA_S3R4.txt ES3R4-5、ES3R4-8。
- 共同点：均不在 D003 的失败传播链上，不属 P05 修复范围；只在登记表写明现状。

```diff
@@ -41,0 +44,1 @@ （在 D016/D017 之后插入；具体位置按最终编号顺序）
+| R-P05-02（P05-S5 期间登记，2026-10-18） | ES3R4-5/528/1164 既有问题（OUT_OF_SCOPE_D003）：(a) pattern_get_containment_tree 第一个形状无效时返回 i+1=1，被 InitSolution 上报为内存分配失败；(b) pattern.c:798 内层循环 for(j = i+1; i < nshapes; ++i) 用 i 作条件与自增，nshapes>1 时只有 shape 0 被检查（U95/U99）；528 shape_get_intersection_area 无调用者（死代码）；1164 fprint_double 唯一调用点被注释（U90） | 未验证/未修复：U99 明确修它会改变正常路径（既有输入可能新报错），故不在 P05-S3/S4 修。pattern.c:798 为 [源码] 事实 | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |
+| R-P05-03（P05-S5 期间登记，2026-10-18） | FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9 返回值：fmm_FFT.cpp 与 fmm_kottke.cpp 只在返回 -12 时设 ret=1 并 goto cleanup，其余负值保持原行为（ES3R4-8；U100） | 未验证：U100 只要求写 [源码] 说明各返回码经公共 API 的可达性（文件:行号），未运行 | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |
```

### 2.5 P05 相关状态文字同步（ISSUE_REGISTRY 物理行 85、107、113、117）

```diff
@@ -85,1 +85,1 @@
- ... 主测试total257/pass256/skip1 ...；上述有限范围关闭，P05未启动 |
+ ... 主测试total257/pass256/skip1 ...；上述有限范围关闭；P05 已启动，当前处于 P05-S5（前端与回归，仅改文档）。 |
@@ -107,1 +107,1 @@
- ... | P05 主线之后安排 RNP 防御专项；若正常受支持输入可达内存破坏则提前 |
+ ... | P05 收口之后安排 RNP 防御专项（P05-S5 登记表引用本条）；若正常受支持输入可达内存破坏则提前 |
@@ -117,1 +117,1 @@
- 下一轮默认修复顺序仍为 P05/D003 到 P06/D004；P05 应核对实际 FMM/FFT 失败传播和已登记 VL NB1 可达性。
+ 下一轮默认修复顺序：P05 进入 S5 收口（前端与回归），随后 P06/D004；P05 的 FMM/FFT 失败传播与 VL NB1 可达性已在 S3/S4 登记。
```

## 3. PROJECT_ROADMAP.md 逐条 unified diff 草案

### 3.1 P05 行（物理行 51）当前状态文字

依据：PROJECT_ROADMAP.md P05 行第 4 列（验收和交付物）与第 5 列（当前状态）；P05_ACCEPTANCE_MAP_S5R1.tsv；P05_S3_S4_SIGNOFF.md 第 2 节。

```diff
@@ -51,1 +51,1 @@
 | P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | 待执行；优先复用已有候选 |
+ | P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | P05-S1 至 S4 已由用户签收（带范围声明，见 P05_S3_S4_SIGNOFF.md 第 2 节）；P05-S5 进行中（R1 输入盘点与分类）；验收映射见 checkpoints/p05/registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv |
```

### 3.2 D016 与 R-P05-01（物理行 145 至 147）

- D016：路线图文字最小修法进入 P05-S3，具体改动需用户批准；见登记表 已过期——修法已于 P05-S3R2 提交 3e77aa9 实施；P05-S5 只核对，不改写历史。
- R-P05-01：保持未验证，暂不处理，在 S5 登记表保持 OPEN；不在 S5 修。

## 4. 不在本草案范围

- 不改写 P05_S3_S4_SIGNOFF.md 第 2 节签收原文、不改写 RULINGS.tsv、不改写任何历史报告。
- 不加新 U 编号（本轮没有用户新裁决）。
- 不宣布 P05-S5 或 P05 阶段完成；不写 P05-S5 已签收字样。

