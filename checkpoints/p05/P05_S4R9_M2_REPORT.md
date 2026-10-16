# P05-S4 R9 M0+M2 执行报告：S3R5 勘误、F4 全套装置、K 继承证明、SOLN 修后验证与 M2 回归（F4）

> 轮次标识：`r9m0` / `r9m2`（P05-S4 子轮次 R9，M0 与 M2 两个里程碑，非新阶段）  
> 开工基线 HEAD：`a3a74bb32f68f4d330891394b3e660ef106ebfd1`（s3r5 收尾提交）  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 未修复基线树：B（`37a82e8`，`1d738e64…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m0/` 与 `checkpoints/p05/evidence/p05-s4r9/m2/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M0/` 与 `checkpoints/p05/registries/s4r9/M2/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M0M2.md`  
> 规范约束：严格遵循 `AGENTS.md` 与本任务书纪律。**本轮不宣布任何阶段完成，不询问是否签收。本轮是 P05-S4 在 F4 上的修后验证与回归；M1 等价重跑与 M3（make test、Python/Lua E2E）不在本轮。**

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9_start.txt`）
- **HEAD 校验**：`a3a74bb32f68f4d330891394b3e660ef106ebfd1`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_r9_start.txt` 5 项一致（PASS）；
- **s3r5 清单比对**：`checkpoints/p05/registries/s3r5/SHA256SUMS.txt` 14 项全数校验通过（PASS）；
- **s3r5 产物与 init-B-dbg sha256 核验**：
  * `lib_F4_dbg`: `6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26`（PASS）
  * `lib_F4_san`: `ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd`（PASS）
  * `lib_F4_plain`: `5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757`（PASS）
  * `init-F4-dbg`: `a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2`（PASS）
  * `init-F4-san`: `33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3`（PASS）
  * `init-F4-san-AL`: `f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e`（PASS）
  * `init-B-dbg`: `3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8`（PASS）
- **临时目录快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（PASS）；
- **构建残留基线**：扫描记录 3 项历史 pyc 残留，写入 `STRAY_BASELINE_R9.tsv`（PASS）；
- **门禁结论**：`FAILS=0`，开工门禁全数通过。

### 1.2 结束门禁（`GATE_R9_end.txt`）
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（保持不变，PASS）；
- **S4/ 源码保护**：`git diff HEAD -- S4` 为空，`S4/` 零改动（PASS）；
- **历史树与判定器**：B, F2, F3, F4 树哈希与判定器 sha256 均保持（PASS）；
- **活文件前缀保护**：`RULINGS.tsv` 与 `ERRATA_S3R5.txt` 开工前缀均保持，5 列格式全部满足（PASS）；
- **构建残留扫描**：无新增或修改的 `.pyc` 或 `.o`，`new=[] changed=[]`（PASS）；
- **STATE.md 约束**：大小为 7014 字节，满足 `<= 8192` 约束（PASS）；
- **临时目录快照**：条目数 0，sha256 与开工保持一致（PASS）；
- **门禁结论**：`FAILS=0`，结束门禁全数通过。

---

## 2. 裁决与勘误登记（S-B）

### 2.1 用户裁决（`registries/RULINGS.tsv`）
追加用户裁决 `U291` 至 `U298`（共 8 条，5 列，前缀逐字节保持）：
- **U291**：S3R5 结果采信作为 R9 输入；H-2(a)(b)(c)(d) 记为 ES3R5-1..4 追加到 `ERRATA_S3R5.txt`，不重跑已提交文件。
- **U292**：R9 分步执行规划（M0+M2 本轮；M1 另发；M3 阶段收口）；B 树与 F2 树未变，相关点引用正式判定并核对驱动 sha256。
- **U293**：SOLN F4 18 点期望规则（rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, post_call1_solution=NULL, crash_call=NONE, exp_san=0, exp_I6=HOLD）。
- **U294**：M2 回归 173 点映射规则（tree→F4，驱动与库换为 F4 对应产物，点号后缀 -F3→-F4，exp_* 原样保留，status=INFLUENCED）。
- **U295**：K 继承证明规则（按驱动族 × clean_env 分组，F3 与 F4 无注入 gdb 映射比对至 K_max+2；序列一致则沿用 K；SOLN 组引用 s3r5 K_MAP）。
- **U296**：装置对等规则（编译/链接命令行去除树路径后差异 0 项；库告警数等于 F3 对应库；seam apply 仅允许 +13 行号偏移；s3r5 产物沿用核 sha）。
- **U297**：执行顺序与停止策略（M0 提交冻结 → 阳性对照 → 冒烟单遍 → 正式两遍 → 判定 → 合并总表；冒烟非预期停在冒烟分诊）。
- **U298**：STATE.md 精简授权（历史各轮数字合并摘要，保持 <= 8192 字节）。

### 2.2 S3R5 勘误与 R9 勘误（`ERRATA_S3R5.txt`、`ERRATA_9.txt`）
- 在 `checkpoints/p05/ERRATA_S3R5.txt` 追加 `ES3R5-1` 至 `ES3R5-4`：
  * ES3R5-1：报告中强化词与章节错引勘误；
  * ES3R5-2：K_MAP_F4_S3R5.tsv 中 dbg 1764 内存大小口径差异说明；
  * ES3R5-3：GDB_SCRIPT_AUDIT 范围未覆盖全库勘误说明，移交 R9 S-E 审计；
  * ES3R5-4：R9_INPUTS 驱动族未覆盖 M2 回归需求说明，由 R9 S-D 补全。
- 新建 `checkpoints/p05/registries/s4r9/ERRATA_9.txt`（编号 E9-n），本轮执行中无偏离。
- 记录提交 (i)：`20d7656`（`record(p05-s4r9): brief, rulings U291-U298, errata ES3R5-1..4 & ERRATA_9, gate scripts (awaiting user review)`）。

---

## 3. 有效集抽取与计数断言（S-C）

通过 `testing/d003/stage_s4r9/effective_set_r9.py` 从 `M2_CONSOLIDATED_R8_M2e.tsv` 抽取 202 个有效点，生成 `M2_EFFECTIVE_F3_R9.tsv`。
所有 H-3 预设计数全数断言通过：
- **总有效点数**：202 行（consolidation_status 不含 SUPERSEDED）；
- **F3 树运行点**：191 点（SOLN 18 点 + 回归非 SOLN 173 点）；
- **B 树引用点**：10 点（init-B-dbg 9 点 SOLN + r6dnv1-B-dbg 1 点 M2-10）；
- **F2 树引用点**：1 点（seam-fmmret-F2 1 点 M2-09）；
- **F3 驱动族分布（16 驱动）**：
  * d003-F3-plain: 72
  * d003plan-F3-plain: 9
  * dual-F3-dbg: 2
  * init-F3-dbg: 18（SOLN 9 + 非 SOLN 9）
  * init-F3-san: 12（SOLN 6 + 非 SOLN 6）
  * init-F3-san-AL: 3（SOLN 3）
  * layers-F3-dbg: 8
  * layers-dual-F3-dbg: 2
  * nan-F3: 3
  * polyinj-F3-dbg: 17
  * polyinj-F3-san: 6
  * r6bseam-seamF-F3: 6
  * r6bstate-F3-dbg: 13
  * r6bstate-F3-san: 13
  * seam-fmmret-F3: 1
  * seamF-F3-san: 6
- **GDB 脚本分布**：
  * `testing/d003/stage_s4/r6c_state_r8m2a3.gdb`: 38 行
  * `testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb`: 18 行
  * `testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb`: 1 行（B 树）
  * 无 GDB 脚本（`-`）：145 行

---

## 4. 装置构建与对等证明（S-D）

通过 `testing/d003/stage_s4r9/build_r9.py` 完成 F4 树导出、seam 补丁应用、库构建与驱动链接，产出 `BUILD_R9.tsv`、`BUILD_OPTION_DIFF_R9.txt`、`SEAM_APPLY_DIFF_F3_F4_R9.txt`、`DRIVER_MAP_F3_F4_R9.tsv`。

### 4.1 Seam 补丁应用报告比对（`SEAM_APPLY_DIFF_F3_F4_R9.txt`）
- `apply_seam_r4_buf.py`（F4_buf）：与 F3 对应报告比对为 **0 行差异**；
- `apply_seam_b2.py`（F4_seamF_san / dbg）：与 F3 对应报告比对为 **0 行差异**；
- `apply_seam_r2.py`（A,C,D）：锚点位于 S4.cpp 1774 行之后的站点（id 21..25）行号均偏移 **+13**（如 2276→2289, 2310→2323, 2430→2443, 2455→2468, 4016→4029），其他文件 0 差异；
- `apply_seam_r5_fmmret.py`（tree A）：anchor 行号均偏移 **+13**（如 2391→2404, 2395→2408 等），补丁内容 0 差异；
- 结论：完全符合 U296 纪律（只允许 +13 行号偏移，无新增或缺失）。

### 4.2 库构建与告警对等核验
| 库名称 | 源码树 | 编译宏与选项 | 告警数 (F4) | F3 对应库 | 告警数 (F3) | 状态 |
|---|---|---|---|---|---|---|
| `lib_F4_dbg` | F4 | DBG_FLAGS | 62 | lib_F3_dbg | 62 | REUSED_MATCH_WARNINGS |
| `lib_F4_san` | F4 | SAN_FLAGS | 62 | lib_F3_san | 62 | REUSED_MATCH_WARNINGS |
| `lib_F4_plain` | F4 | PLAIN_FLAGS | 71 | lib_F3_plain | 71 | REUSED_MATCH_WARNINGS |
| `lib_F4_bufseam` | F4_buf | PLAIN_FLAGS + BUF_MACROS | 71 | lib_F3_bufseam | 71 | BUILT_MATCH_WARNINGS |
| `lib_F4_seamF_dbg` | F4_seamF_dbg | DBG_FLAGS + SEAMF_MACROS | 62 | lib_F3_seamF_dbg | 62 | BUILT_MATCH_WARNINGS |
| `lib_F4_seamF_san` | F4_seamF_san | SAN_FLAGS + SEAMF_MACROS | 62 | lib_F3_seamF_san | 62 | BUILT_MATCH_WARNINGS |
| `lib_F4_fmmret_plain` | F4_fmmret_plain | PLAIN_FLAGS + FMMRET_MACROS | 71 | lib_F3_fmmret_plain | 71 | BUILT_MATCH_WARNINGS |

每个 F4 库的告警数与 F3 对应库相等，0 新增告警。

### 4.3 驱动对等与编译命令行比对（`BUILD_OPTION_DIFF_R9.txt`、`DRIVER_MAP_F3_F4_R9.tsv`）
- 16 个 F4 驱动（3 个 s3r5 沿用 + 13 个本轮新链接）与 F3 对应驱动的编译/链接命令行去除树与产物路径后逐条对比：
  **16 项对比全部为 IDENTICAL（0 differences），差异 0 项**；
- 告警数：polyinj-F4-dbg/san 均为 3 处告警（与 F3 polyinj 对应驱动告警一致），其余 14 个驱动均为 0 告警；
- `DRIVER_MAP_F3_F4_R9.tsv` 记录双方 sha256，映射核验全数 VERIFIED。

---

## 5. 行号断点审计（S-E）

通过 `testing/d003/stage_s4r9/gdb_audit_r9.py` 扫描 `testing/d003/` 下全部 50 个 `.gdb` 文件及 385 个 `.py` 文件，产出 `GDB_LINE_AUDIT_R9.tsv`：
- 识别仓库历史中全部 23 处 `文件:行号` 形式的断点；
- R9 运行计划实际使用的脚本共 3 个：
  * `testing/d003/stage_s4/r6c_state_r8m2a3.gdb`：全部使用函数名断点（`r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`），0 行号断点；
  * `testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb`：全部使用函数名断点，0 行号断点；
  * `testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb`：仅在未修改的 B 树基线测试中使用（属于引用点，本轮在 F4 不运行）；
- 结论：**R9 运行计划使用的 F4 脚本 0 处使用行号断点，无需重写，审计全数通过**。

---

## 6. 无注入对照实测（S-F）

通过 `testing/d003/stage_s4r9/noinj_control_r9.py` 对 F4 全部驱动 × clean_env 组合（146 组）进行无注入对照单遍运行，落盘于 `probe/noinj_control_r9.txt` 与 `NOINJ_R9.tsv`：
- **142 组**：实测全部 `rc=0`，`san_reports=0`，无注入命中，状态 `PASS`；
- **4 组（NOINJ-109, 141, 142, 143）**：`d003-F4-plain` 在 `FMM_MODE=vl` 下（NG 为 1, 2, 3, 4），实测返回码非零（驱动退出码 1，`RC first 20`，`RC retry 20`），0 san 报告；
- **历史比对查实**：经在 F3 `d003-F3-plain` 驱动上复测及查询历史裁决（U243, U255, U263），此 4 组在 F3 上同样表现为 `RC first 20`（S4 原生 PolBasisVL 在 `n_G_actual=1` 时的固有失败返回码 20，非注入导致），与 F3 历史表现一致；
- 依据任务书 S-F 规则"与 F3 相同，记事实并继续"，记为 `PASS_MATCH_F3_NATIVE_FAIL`，对照全数通过。

---

## 7. K 继承证明（S-G）

依据 U295 硬规则，通过 `testing/d003/stage_s4r9/k_inherit_r9.py` 完成 73 组带计数注入的驱动族 × clean_env 分组在 F3 与 F4 上的 GDB 调用序列比对：
- **SOLN 组**：依据 U295 直接引用 s3r5 `K_MAP_F4_S3R5.tsv`（18 点实测全部一致，已注明 ES3R5-2 口径说明），状态 `PASS_CITED_S3R5`；
- **回归非 SOLN 组**：在 F3 与 F4 对应驱动上，于各注入 wrapper（`__wrap_malloc`、`__wrap__Z9S4_mallocm`、`S4_TEST_ALLOC_HOOK` 等）断点捕获直至 `K_max + 2` 的调用序列；
- F3 行号经 `LINEMAP_F3_F4_S3R5.tsv` 映射后，所有组的 (k, size, 最内层 S4 帧函数与映射行号) 序列在 F3 与 F4 之间全部一致；
- `K_INHERIT_R9.tsv` 记录 73 组全数 `PASS_K_INHERITED`，0 组发生 K 分歧（`NOT_RUN_K_DIVERGENT = 0`），K 值继承证明通过。

---

## 8. 预注册冻结与 M0 提交（S-H、S-I）

通过 `testing/d003/stage_s4r9/prereg_r9.py` 生成预注册文件与命令计划，计算 sha256 并生成时间戳：
1. **`PREREG_SOLN_F4_R9.tsv`**（18 行）：
   - sha256：`6b41d1dc9472cfa95c1500e19c306b07a030b8c70a2977bf739d41d6679ac484`；
   - 包含 dbg 9 点、san 6 点、san-AL 3 点；
   - 期望值依据 U293：rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, post_call1_solution=NULL, crash_call=NONE, exp_I6=HOLD。
2. **`PREREG_REGRESS_F4_R9.tsv`**（173 行）：
   - sha256：`66d3aa3c3c67b0fbaa58b034160c57890f79f0cd18e079f292d674c48b79a150`；
   - 期望值依据 U294，逐点继承 F3 有效预期；点号与对照点后缀换为 -F4。
3. **`PREREG_CITED_R9.tsv`**（29 行）：
   - sha256：`0c986d2348f3dac9cb052c2254ffe79d3e83b5f304da14e7ee8b6ee585148307`；
   - 包含 11 个引用的 B/F2 点及 18 个 F3 SOLN 基线对照行。
4. **`COMMAND_PLAN_R9.tsv`**（382 条命令）：
   - sha256：`17c2cb935cad43a8be9716f9150759f22931d69c9b3e2d36b11f3d9c12221c11`；
   - 路径全部为绝对路径，`$EV` 字面量检查 0 处。
5. **计数断言**：18 + 173 = 191 个运行点，各驱动族分布与 H-3 逐项相符。
6. **M0 提交 (ii)**：`bb6f1e8`（`prereg(p05-s4r9): M0 apparatus, K inheritance, preregistrations, plan (awaiting user review)`）。**正式运行在冻结提交之后进行。**

---

## 9. 阳性对照实测（S-J）

在正式运行前，通过 `testing/d003/stage_s4r9/posctrl_r9.py` 运行合成阳性对照，落盘于 `POSCTRL_R9.txt`：
- **总用例数**：53 项（继承 r8m2e 全部 47 项 + 新增 R9 6 项）；
- **新增用例覆盖**：
  * `Case R9_1`: `post_call1_solution=NULL` 匹配预期 -> PASS (MATCH)
  * `Case R9_2`: `post_call1_solution=NONNULL` 不符预期 NULL -> PASS (MISMATCH)
  * `Case R9_3`: `crash_call=NONE` 匹配预期 -> PASS (MATCH)
  * `Case R9_4`: `crash_call=1` 不符预期 NONE -> PASS (MISMATCH)
  * `Case R9_5`: `I6=HOLD` 匹配预期 -> PASS (MATCH)
  * `Case R9_6`: `I6=VIOLATED` 不符预期 HOLD -> PASS (MISMATCH)
- **实测结果**：**53 项全部 PASS，0 失败**。判定管道对各新增期望的鉴别力均得到合成验证。

---

## 10. 冒烟运行与分诊（S-K）

依据 U297，通过 `testing/d003/stage_s4r9/run_smoke_r9.py` 进行单遍冒烟运行，落盘于 `VERDICT_SMOKE_R9.tsv` 与 `SUMMARY_SMOKE_R9.txt`：
- **运行范围**：SOLN F4 18 点全部 + 15 个回归驱动族各 1 点代表 + 匹配对照点，共 42 点；
- **实测结果**：
  * `total_points: 42`
  * `MATCH: 42`
  * `MISMATCH: 0`
  * `FLAKY: 0`
  * `GDB_DIVERGENT: 0`
  * `INVALID: 0`
  * `SCHEMA_ERROR: 0`
- **冒烟结论**：未出现 MISMATCH、GDB_DIVERGENT 或 INVALID，冒烟全数通过，依 U297 准予进入正式运行。

---

## 11. 正式两遍运行与判定（S-L）

通过 `testing/d003/stage_s4r9/run_formal_r9.py` 执行正式两遍运行（191 点 × 2 遍 = 382 次运行，dbg 点以 gdb+nogdb 方式成对执行）：
- 事实提取：`FACTS_pass1_R9.tsv`、`FACTS_pass2_R9.tsv`（各 191 行）；
- 私有状态判定：`RESULTS_STATE_R9.tsv`、`STATE_pass1_R9.tsv`、`STATE_pass2_R9.tsv`（各 23 行被判点，I1..I6 逐项判定）；
- 最终判定：`VERDICT_R9.tsv` 与 `SUMMARY_R9.txt`。

### 11.1 正式判定汇总统计（`SUMMARY_R9.txt`）
- **总运行评估点数**：191 点（有效点 191 点）
- **MATCH**：**191 点（100%）**
- **MISMATCH**：**0 点**
- **FLAKY**：**0 点**
- **GDB_DIVERGENT**：**0 点**
- **UNJUDGED_MISSING**：**0 点**
- **UNJUDGED_BY_DESIGN**：**0 点**
- **SCHEMA_ERROR**：**0 点**

### 11.2 按 item 分项统计
| Item 编号 | 类别描述 | 评估点数 | MATCH | MISMATCH | FLAKY | GDB_DIV | 状态 |
|---|---|---|---|---|---|---|---|
| SOLN-1763 | F4 InitSolution 1763 行修后验证 | 6 | 6 | 0 | 0 | 0 | 全部 MATCH |
| SOLN-1764 | F4 InitSolution 1764 行修后验证 | 6 | 6 | 0 | 0 | 0 | 全部 MATCH |
| SOLN-1765 | F4 InitSolution 1765 行修后验证 | 6 | 6 | 0 | 0 | 0 | 全部 MATCH |
| M2-01 | 多边形与 InitSolution 恢复验证 | 17 | 17 | 0 | 0 | 0 | 全部 MATCH |
| M2-01-CTRL | M2-01 对照组 | 9 | 9 | 0 | 0 | 0 | 全部 MATCH |
| M2-03 | Sanitizer 组与参考点 | 31 | 31 | 0 | 0 | 0 | 全部 MATCH |
| M2-03-SANREF | M2-03 对照组 | 19 | 19 | 0 | 0 | 0 | 全部 MATCH |
| M2-04 | 双目标注入恢复验证 | 2 | 2 | 0 | 0 | 0 | 全部 MATCH |
| M2-04-CTRL | M2-04 对照组 | 2 | 2 | 0 | 0 | 0 | 全部 MATCH |
| M2-05 | 其他层失败变体验证 | 4 | 4 | 0 | 0 | 0 | 全部 MATCH |
| M2-05-CTRL | M2-05 对照组 | 4 | 4 | 0 | 0 | 0 | 全部 MATCH |
| M2-06 | 张量路径验证 | 1 | 1 | 0 | 0 | 0 | 全部 MATCH |
| M2-06-CTRL | M2-06 对照组 | 1 | 1 | 0 | 0 | 0 | 全部 MATCH |
| M2-06-DIAG | M2-06 诊断对照 | 1 | 1 | 0 | 0 | 0 | 全部 MATCH |
| M2-07 | 网格全排列注入验证 | 9 | 9 | 0 | 0 | 0 | 全部 MATCH |
| M2-07-CTRL | M2-07 对照组 | 72 | 72 | 0 | 0 | 0 | 全部 MATCH |
| M2-09-CTRL | Seam 对照组 | 1 | 1 | 0 | 0 | 0 | 全部 MATCH |

---

## 12. 合并总表（S-M）

通过 `testing/d003/stage_s4r9/consolidate_r9.py` 生成 `M2_CONSOLIDATED_F4_R9.tsv`：
- **总行数**：259 行；
- **有效行数**：**202 行全部为 ACTIVE，判定全部为 MATCH**；
- **有效行来源**：191 行来源于本轮正式两遍（`formal_r9m2`），11 行来源于历史有效正式判定（`formal_r8m2b` / `formal_r8m2e`，未修改的 B 与 F2 树基线点）；**有效行中 0 处来源于 smoke，100% formal 来源**；
- **历史记录继承**：57 行历史被替代点保持 `SUPERSEDED` 记录，superseded_by 关系完整；
- 每行均注明 F3 对应点的点号及历史判定结果，追溯链路完整。

---

## 13. 红点台账追加（S-M）

在 `RED_POINTS_LEDGER_APPEND_R9.tsv` 中追加 RP-R8-M2c-1、1b 及 K-1 记录（严格遵守纪律，只写实测事实与判定类别，是否关闭由用户裁决）：

| 缺陷编号 | 涉及源码位置 | 被测树 | 事实记录类别 | 实测事实与点号证据 | 状态 | 建议去向 |
|---|---|---|---|---|---|---|
| RP-R8-M2c-1 | S4/S4.cpp:1763–1773 (F4: 1763–1786) | F4 | 修后验证事实 | R9 M2 正式两遍实测 6 点全 MATCH: SOLN-1763-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san}；实测 rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, post_call1_solution=NULL, crash_call=NONE, I6=HOLD；调用1返回分配失败码1，未挂接损坏解，重试成功。 | 修后验证事实：6 点实测 REPORTED_FAILURE 判定 MATCH；是否关闭待用户裁决 | 待用户裁决是否关闭 |
| RP-R8-M2c-1b | S4/S4.cpp:1764,1765 (F4: 1771,1772; 1995->2008, 2021->2034) | F4 | 修后验证事实 | R9 M2 正式两遍实测 12 点全 MATCH: 1764行 6点 (SOLN-1764-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san-AL})，1765行 6点 (SOLN-1765-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san})；实测全部 rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, post_call1_solution=NULL, crash_call=NONE, I6=HOLD；调用1分配失败均正确清理并返回1，未挂接损坏解，重试成功；未再发生历史重试崩溃（1995/2021）。 | 修后验证事实：12 点实测 REPORTED_FAILURE 判定 MATCH，未再发生重试崩溃；是否关闭待用户裁决 | 待用户裁决是否关闭 |
| K-1 | fmm_closed.cpp:244 / S4.cpp:2474-2478 | F4 | CLOSED | U274/U281 关闭维持；R9 回归点 M2-06-01-F4-C 实测 MATCH (rc1=20, REPORTED_FAILURE)；无静默吞没。 | CLOSED (维持 U274 关闭) | 已关闭 |

---

## 14. 违规与执行偏离记录

### 14.1 表一：越界写入尝试表（命令自身写了仓库外路径）
*本轮共计 0 次越界写入尝试。*

| 序号 | 轮次 | 命令 | 是否落盘 | 处理说明 |
|---|---|---|---|---|
| - | - | 无 | 否 | 严格执行路径纪律，无越界写入尝试 |

### 14.2 表二：工具与脚本事件表（裸跑写入、框架落盘、目录清理、重跑覆盖等）
| 序号 | 轮次 | 命令 / 事件 | safe_run.log 行号 | 是否落盘 | 处理说明 |
|---|---|---|---|---|---|
| 1 | r9m0 | Node PTC 框架溢出输出落盘至 `/tmp/dsh-spill-*` | 无（PTC 框架运行捕获） | 是（临时） | 框架行为，非执行者命令违规，单列披露 |
| 2 | r9m0 | `rm -rf "$EV/trees" "$EV/build"` | m0 log 第 103 行 | 是 | 初次 `build_r9.py` 运行因命令行比对归一化字符串差异失败，清理未完成目录并重跑 |
| 3 | r9m0 | `python3 -I -B testing/d003/stage_s4r9/gdb_audit_r9.py` 重跑覆盖 | m0 log 第 105 行 | 是 | 正则反斜杠在模板字符串中转义纠正后重跑覆盖 |
| 4 | r9m2 | `rm -rf "$EV/smoke"` | m2 log 第 2 行 | 是 | 初次 `run_smoke_r9.py` 因 verdict 参数名误传 (`--out` vs `--out-verdict`) 中断，清理后重跑 |
| 5 | r9m2 | `rm -rf "$EV/smoke" ...` | m2 log 第 4 行 | 是 | 冒烟运行发现 `--dumps-dir` 路径层级需指向 parent `run` 目录以正确读取 call2.txt，清理后重跑 |
| 6 | r9m2 | `python3 -I -B testing/d003/stage_s4r9/consolidate_r9.py` 重跑覆盖 | m2 log 第 5 行 | 是 | 修复合并脚本中局部变量名索引后重跑覆盖 |

---

## 15. 需用户裁决

本轮执行中，所有装置对等、K 继承、断点映射及测试结果均已由源码与测试事实闭环。以下 1 项依规范留待用户裁决：
1. **RP-R8-M2c-1 与 RP-R8-M2c-1b 是否正式关闭**：
   - **事实支撑**：F4 树上 18 个 SOLN 修后验证点已在正式两遍中全部判定为 MATCH（实测 `rc1=1`, `rc2=0`, `signal=0`, `hit=1`, `class=REPORTED_FAILURE`, `post_call1_solution=NULL`, `crash_call=NONE`, `I6=HOLD`）。
   - **点号列表**：
     * RP-R8-M2c-1: `SOLN-1763-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san}` (6点)
     * RP-R8-M2c-1b: `SOLN-1764-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san-AL}` (6点), `SOLN-1765-{closed2d-ng1,fft-ng5,kottke-ng5}-{F4-dbg,F4-san}` (6点)
   - **裁决建议**：请用户裁决是否正式关闭 RP-R8-M2c-1 与 RP-R8-M2c-1b。

---

## 16. 结论与提交信息

本轮已完成 R9 M0+M2 范围，等待用户审核。

---

## 17. 附录：Git 状态与提交记录

### 17.1 `git log -3 --oneline`
```
a7f6044 closeout(p05-s4r9): M0+M2 formal two-pass (191 MATCH), registries, STATE, report (awaiting user review)
bb6f1e8 prereg(p05-s4r9): M0 apparatus, K inheritance, preregistrations, plan (awaiting user review)
20d7656 record(p05-s4r9): brief, rulings U291-U298, errata ES3R5-1..4 & ERRATA_9, gate scripts (awaiting user review)
```

### 17.2 `git log -1`
```
commit a7f60445f4dd1702cda7afb84ca7f28645b3e6e4
Author: Ziyang Li <155395920+void-chaser@users.noreply.github.com>
Date:   Sat Oct 17 06:29:53 2026 +1100

    closeout(p05-s4r9): M0+M2 formal two-pass (191 MATCH), registries, STATE, report (awaiting user review)
```

### 17.3 `git status --short`
```

```
