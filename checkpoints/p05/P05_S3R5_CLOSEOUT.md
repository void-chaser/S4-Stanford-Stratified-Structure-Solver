# P05-S3R5 收尾报告：InitSolution 分配失败清理修复、冻结 F4、F4 装置与映射、自检

> 轮次标识：`s3r5`（P05-S3 子轮次 S3R5，非新阶段）  
> 开工基线 HEAD：`73c9b7b9c3a9e008c214c7cb333212c8ca3856a5`（r8m2e 收尾提交）  
> 冻结被测树：F4（提交 `05097a75faf33597d1090fd07dcdcedfaeab937d`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 未修复基线树：B（`37a82e8`，`1d738e64…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s3r5/`  
> 小表提交目录：`checkpoints/p05/registries/s3r5/`  
> 规范约束：严格执行 `AGENTS.md` 与本轮任务书纪律。**本轮不宣布任何阶段完成，不询问是否签收。本轮的自检不是修复后验证；修后验证由 P05-S4 R9 在 F4 上完成。**  
> 任务书存档：`checkpoints/p05/briefs/P05_S3R5_BRIEF.md`。

---

## 0. 门禁核验结果

### 0.1 开工门禁（`GATE_S3R5_start.txt`）
- **HEAD 校验**：`73c9b7b9c3a9e008c214c7cb333212c8ca3856a5`（PASS）；
- **HEAD:S4 校验**：`6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 冻结树，PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_s3r5_start.txt` 5 项完全一致（PASS）；
- **r8m2e 清单比对**：`checkpoints/p05/registries/s4r8/M2/r8m2e/SHA256SUMS.txt` 33 项全数校验通过（PASS）；
- **临时目录快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（PASS）；
- **构建残留基线**：扫描记录 `testing/d003/__pycache__` 2 项历史 pyc 残留，生成 `STRAY_BASELINE_S3R5.tsv`（PASS）；
- **门禁结论**：`PYTHON_CHECKS_FAILS=0`，`FAILS=0`，开工门禁全数通过。

### 0.2 结束门禁（`GATE_S3R5_end.txt`）
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **F3/F2/B 历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：保持不变（PASS）；
- **工作区状态**：所有项均匹配 `gate_allow_s3r5_end.txt` 允许规则（PASS）；
- **活文件前缀保护**：`RULINGS.tsv` 前缀保持，5 列校验全部 PASS；`ERRATA_8.txt` 前缀保持（PASS）；
- **构建残留扫描**：无新增或修改的 `.pyc` 或 `.o` 文件，`new=[] changed=[]`（PASS）；
- **历史装置保护**：6 个历史运行器与判定器哈希自 d58bafd 以来完全一致（PASS）；
- **STATE.md 约束**：大小为 8060 字节，满足 `<= 8192` 约束（PASS）；
- **临时目录快照**：条目数 0，sha256 保持不变（PASS）；
- **门禁结论**：`PYTHON_CHECKS_FAILS=0`，`FAILS=0`，结束门禁全数通过。

---

## 1. 用户裁决与勘误（S-B）

### 1.1 用户裁决登记（`checkpoints/p05/registries/RULINGS.tsv` 追加 U283–U290）
| 编号 | 来源 | 裁决要点 | 状态 |
|---|---|---|---|
| U283 | 任务书 §3 | 批准修改 `S4/S4.cpp` 1760–1774 段修复 RP-R8-M2c-1/1b；重划 1754/1756 范围（承接 U275）；S4/ 其余不改 | 生效 |
| U284 | 任务书 §3 | 修复采用局部变量分配、全部成功后再挂到 S 的写法，保证分配顺序与次数同 F3；失败置 NULL 并清理，返回 1 | 生效 |
| U285 | 任务书 §3 | 提交分三次：(i) 记录提交；(ii) F4 提交（仅 `S4/S4.cpp`）；(iii) 收尾提交 | 生效 |
| U286 | 任务书 §3 | F4 装置从 F4 提交导出构建（dbg/san/plain 库及驱动）；B 驱动沿用产物核对 sha256；K 需按 caller 源码行重新映射 | 生效 |
| U287 | 任务书 §3 | 允许修改 `AGENTS.md` 第 6 节追加 F4 树冻结行并更新门禁树哈希 | 生效 |
| U288 | 任务书 §3 | 按 H-5 勘误不重跑：记入 E8-116 至 E8-119；新定 safe_run.log 清单记录行数与前 N 行哈希规则；本轮勘误写 `ERRATA_S3R5.txt` | 生效 |
| U289 | 任务书 §3 | 自检范围：A 编译告警无新增；B diff 严格限制与行号映射；C 无注入对照 9 组全过；D 9 点事实单遍运行不判 MATCH | 生效 |
| U290 | 任务书 §3 | R9 预注册本轮不冻结；输出 `R9_INPUTS_S3R5.tsv` 与 `REGRESSION_PLAN_F4_S3R5.tsv`，审计 gdb 脚本 | 生效 |

### 1.2 勘误登记（`ERRATA_8.txt` 追加 E8-116 至 E8-119 与 `ERRATA_S3R5.txt`）
- **E8-116**：r8m2e 报告第 126 行与第 225 行强化词勘误更正为客观陈述；原报告不改。
- **E8-117**：r8m2e 中 `SUMMARY_R8_M2e.txt` 与 `FACTS_pass1/2.tsv` 标题模板残留后缀瑕疵勘误；数据正确，原文件不改。
- **E8-118**：r8m2e 执行偏离披露与证据清单规则更新：safe_run.log 改为记录清单写入时的行数 N 及前 N 行 sha256；披露 posctrl 运行 3 次、start 门禁 5 次及 m2d 目录两次误写事件。
- **E8-119**：回归清单文书勘误：更正 `REGRESSION_PLAN_F4_R8_M2e.tsv` 中关于 init:K 与 B 基线行为措辞。
- **`checkpoints/p05/ERRATA_S3R5.txt`**：本轮独立勘误表已建立。

---

## 2. 修复前源码确认（S-C，`PRE_FIX_SOURCE_S3R5.md`）

依据任务书 §4 S-C 及硬停止条件 2，已输出 `checkpoints/p05/PRE_FIX_SOURCE_S3R5.md`：
1. **F3 缺陷源码确认**：`S4/S4.cpp:1760-1773` 中，1763 行分配 `Solution_` 后，1764 行在判空前解引用 `S->solution->ab`（RP-R8-M2c-1）；1764/1765 分配失败时错误分支未清理脏内存且将悬挂野指针留在 `S->solution` 中，导致第 2 次重试调用直接跳过 InitSolution 解引用空指针崩溃（RP-R8-M2c-1b）。
2. **7 处调用点核查**：`S4.cpp:1803, 2969, 3318, 3565, 4070`、`main_lua.c:2184`、`main_python.c:1274` 逐一核验，每处调用均检查了非零返回并立即退出处理，无一处在失败后继续解引用。
3. **全仓 solution 读写检索**：全仓 24 处包含 `->solution` 的位置逐项分析，**没有任何调用方假设"InitSolution 失败后 solution 非空"** [源码]。相反，失败时保持 `S->solution == NULL` 完全满足所有调用方的正常前置假设。
4. **硬停止条件 2 判定**：未发现任何调用方依赖"失败后 solution 非空"，未发现不检查返回值的调用，未触发硬停止。记录提交 (i) 成功完成（提交 `c84f99c`）。

---

## 3. 修复方案实施与 Diff 全文（S-D）

### 3.1 Edit 修改与 SHA256 校验
修改严格使用 `edit` 工具实施于 `S4/S4.cpp`：
- **修改前代码段（F3: 1760–1773，共 14 行）sha256**：  
  `0d1e4a53b0f7be179f78a89ffed4fa9264159e8cb6d2d4dd1eb85ecff4f05722`
- **修改后代码段（F4: 1760–1786，共 27 行）sha256**：  
  `1ad69ea7cd81675b43aaf950f19ae8fadc3d7345965650a865b4ed11fea32b64`

### 3.2 变更统计与 Diff 全文
运行 `git diff --stat -- S4/`，确认**只改动了 `S4/S4.cpp` 一个文件**：
```
 S4/S4.cpp | 23 ++++++++++++++++++-----
 1 file changed, 18 insertions(+), 5 deletions(-)
```

**Diff 全文（`DIFF_F3_F4_S3R5.txt`）**：
```diff
--- a/S4/S4.cpp
+++ b/S4/S4.cpp
@@ -1760,17 +1760,30 @@ int Simulation_InitSolution(S4_Simulation *S){
 	if(NULL != S->solution){
 		Simulation_DestroySolution(S);
 	}
-	S->solution = (Solution_*)malloc(sizeof(Solution_));
-	S->solution->ab = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * S->n_layers * 4 * S->n_G);
-	S->solution->solved = (int*)malloc(sizeof(int) * S->n_layers);
-	if(NULL == S->solution || NULL == S->solution->ab || NULL == S->solution->solved){
+	Solution_ *sol = (Solution_*)malloc(sizeof(Solution_));
+	if(NULL == sol){
+		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution) [omega=%f]\n", S->omega[0]);
+		if(NULL != S->msg){
+			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
+		}
+		return 1;
+	}
+	sol->ab = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * S->n_layers * 4 * S->n_G);
+	sol->solved = (int*)malloc(sizeof(int) * S->n_layers);
+	if(NULL == sol->ab || NULL == sol->solved){
+		if(NULL != sol->ab){
+			S4_free(sol->ab);
+		}
+		free(sol->solved);
+		free(sol);
 		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution) [omega=%f]\n", S->omega[0]);
 		if(NULL != S->msg){
 			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
 		}
 		return 1;
 	}
-	memset(S->solution->solved, 0, sizeof(int) * S->n_layers);
+	memset(sol->solved, 0, sizeof(int) * S->n_layers);
+	S->solution = sol;
 
 	S4_TRACE("I  Simulation_InitSolution G: (%d) [omega=%f]\n", S->n_G, S->omega[0]);
```
- 修复严格遵循 U284：分配先放入局部变量 `sol`，保持原顺序调用 `S4_malloc` 和 `malloc`；任一失败时释放已分配资源并返回 1，保证 `S->solution` 保持为 NULL；全部成功后 `memset` 并赋值 `S->solution = sol`。
- 未触发硬停止条件 3：diff 范围完全处于 1760–1774 段之内，无任何其他文件被修改。

---

## 4. F4 提交与树冻结

依据 U285(ii)，F4 提交已独立完成：
- **提交信息**：`fix(p05-s3r5): InitSolution allocation failure cleanup (RP-R8-M2c-1/1b) (awaiting user review)`
- **F4 提交 Commit ID**：`05097a75faf33597d1090fd07dcdcedfaeab937d`（简写 `05097a7`）
- **F4 被测树 `HEAD:S4` 哈希**：`589e15eb11fcb04e031b524f25a443e7921946cf`
- **提交内容核实**：仅包含 `S4/S4.cpp`（1 file changed, 18 insertions(+), 5 deletions(-)）。

---

## 5. F4 装置构建与告警对比（S-E，`BUILD_S3R5.tsv`、`WARN_DIFF_F3_F4_S3R5.txt`）

依据 U286，在 `$EV/trees/F4/` 从 F4 提交（`05097a7`）导出被测树，使用 `build_s3r5.py` 完成全部装置构建：

| 产物名称 | 类型 | 路径 | sha256 | rc | 告警数 | 相对 F3 告警 diff |
|---|---|---|---|---|---|---|
| `lib_F4_dbg` | 库 | `$EV/build/lib_F4_dbg/libS4.a` | `6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26` | 0 | 62 | +0 (PASS) |
| `lib_F4_san` | 库 | `$EV/build/lib_F4_san/libS4.a` | `ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd` | 0 | 62 | +0 (PASS) |
| `lib_F4_plain` | 库 | `$EV/build/lib_F4_plain/libS4.a` | `5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757` | 0 | 71 | +0 (PASS) |
| `init-F4-dbg` | 驱动 | `$EV/build/init-F4-dbg` | `a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2` | 0 | 0 | - |
| `init-F4-san` | 驱动 | `$EV/build/init-F4-san` | `33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3` | 0 | 0 | - |
| `init-F4-san-AL` | 驱动 | `$EV/build/init-F4-san-AL` | `f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e` | 0 | 0 | - |
| `init-B-dbg` | 驱动 | `checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg` | `3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8` | 0 | - | 沿用核验 (PASS) |

- **告警对比结论（`WARN_DIFF_F3_F4_S3R5.txt`）**：dbg 模式 62 vs 62（diff 0）；san 模式 62 vs 62（diff 0）；plain 模式 71 vs 71（diff 0）。**相对 F3 无任何新增告警**。
- 未触发硬停止条件 4：所有构建均成功且无新增告警。

---

## 6. 自检执行结果（A–D）

### 6.1 自检 A：编译与告警
已在第 5 节证实：三种构建模式全部构建成功（rc=0），告警数与 F3 逐项相同（0 diff），无新增告警。

### 6.2 自检 B：Diff 范围与行号映射（`LINEMAP_F3_F4_S3R5.tsv`）
- `DIFF_F3_F4_S3R5.txt` 确认 S4/ diff 仅在 `S4/S4.cpp:1760-1774`。
- 行号映射表 `LINEMAP_F3_F4_S3R5.tsv` 确认：
  - 1759 行及以前：偏移量 = 0（无变化）；
  - 1760–1773 行：修复段（14 行增至 27 行，净增 +13 行）；
  - 1774 行及以后：**偏移量恒为 +13**。关键位点映射如下：
    - F3:1775（后置 trace 首行）→ F4:1788
    - F3:1803（GetLayerSolution 调用点）→ F4:1816
    - F3:1995（原 1764 重试崩溃点）→ F4:2008
    - F3:2021（原 1765 重试崩溃点）→ F4:2034
    - F3:2969 → F4:2982
    - F3:3318 → F4:3331
    - F3:3565 → F4:3578
    - F3:4070 → F4:4083
    - F3:4219 → F4:4232

### 6.3 自检 C：无注入对照实测（`noinj_control_s3r5.txt`）
依据 U289(C)，对 3 种驱动（`init-F4-dbg`、`init-F4-san`、`init-F4-san-AL`）× 3 种组合（closed2d-ng1、fft-ng5、kottke-ng5）共 9 组进行无注入运行测试：
- **实测结果**：**9 组全部 rc=0，0 个 ASAN/UBSAN 报告，0 次注入触发（has_hit=False, has_hitcount_nz=False）**。
- 探针完整记录落盘于 `$EV/probe/noinj_control_s3r5.txt`。
- 未触发硬停止条件 5。

### 6.4 自检 D：9 点位实测事实记录（`SELFCHECK_D_S3R5.tsv`）
依据 U289(D) 与任务书措辞约束，**本节只客观陈述实测观察事实，不判定 MATCH，不写入任何 VERDICT 表，不称为"已修复"或"已验证"**：

| 点号 (point_id) | 组合 | 位点 | 驱动 | k_fail | rc1 | rc2 | signal | hit | post_call1_solution | crash_call | driver_exitcode |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOLN-1763-closed2d-ng1-F4-dbg | closed2d-ng1 | 1763 | init-F4-dbg | 9 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1764-closed2d-ng1-F4-dbg | closed2d-ng1 | 1764 | init-F4-dbg | 10 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1765-closed2d-ng1-F4-dbg | closed2d-ng1 | 1765 | init-F4-dbg | 11 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1763-fft-ng5-F4-dbg | fft-ng5 | 1763 | init-F4-dbg | 10 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1764-fft-ng5-F4-dbg | fft-ng5 | 1764 | init-F4-dbg | 11 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1765-fft-ng5-F4-dbg | fft-ng5 | 1765 | init-F4-dbg | 12 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1763-kottke-ng5-F4-dbg | kottke-ng5 | 1763 | init-F4-dbg | 10 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1764-kottke-ng5-F4-dbg | kottke-ng5 | 1764 | init-F4-dbg | 11 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |
| SOLN-1765-kottke-ng5-F4-dbg | kottke-ng5 | 1765 | init-F4-dbg | 12 | 1 | 0 | 0 | 1 | NULL | NONE | 0 |

- **自检事实小结**：
  - 自检事实：SOLN-1763-closed2d-ng1-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1764-closed2d-ng1-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1765-closed2d-ng1-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1763-fft-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1764-fft-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1765-fft-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1763-kottke-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1764-kottke-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE；
  - 自检事实：SOLN-1765-kottke-ng5-F4-dbg，rc1=1，rc2=0，signal=0，hit=1，post_call1_solution=NULL，crash_call=NONE。

---

## 7. GDB 堆栈映射与 K 值对比（S-H，`K_MAP_F4_S3R5.tsv`、`K_MAP_RAW_S3R5.txt`）

依据 U286 硬规则，F4 上所有 SOLN 的 K 均在 F4 驱动上通过 GDB 下断点打 `bt 4`，按 caller 源码行重新映射。原始日志落盘于 `$EV/K_MAP_RAW_S3R5.txt` 与 `$EV/probe/map_k_s3r5.txt`。

映射与 F3 并列比对结果如下（`K_MAP_F4_S3R5.tsv`）：

| 组合 (combo) | 位点 | 驱动 (driver) | F4 caller 行 | F4 k | F4 大小 (B) | F3 caller 行 | F3 k | F3 大小 (B) | k 一致性 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| closed2d-ng1 | 1763 | init-F4-dbg | S4.cpp:1763 | 9 | 16 | S4.cpp:1763 | 9 | 16 | True | PASS_EXACT_MATCH |
| closed2d-ng1 | 1764 | init-F4-dbg | S4.cpp:1771 | 10 | 215 | S4.cpp:1764 | 10 | 192 | True | PASS_EXACT_MATCH |
| closed2d-ng1 | 1765 | init-F4-dbg | S4.cpp:1772 | 11 | 12 | S4.cpp:1765 | 11 | 12 | True | PASS_EXACT_MATCH |
| closed2d-ng1 | 1763 | init-F4-san | S4.cpp:1763 | 7 | 16 | S4.cpp:1763 | 7 | 16 | True | PASS_EXACT_MATCH |
| closed2d-ng1 | 1765 | init-F4-san | S4.cpp:1772 | 8 | 12 | S4.cpp:1765 | 8 | 12 | True | PASS_EXACT_MATCH |
| closed2d-ng1 | 1764 | init-F4-san-AL | S4.cpp:1771 | 3 | 192 | S4.cpp:1764 | 3 | 192 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1763 | init-F4-dbg | S4.cpp:1763 | 10 | 16 | S4.cpp:1763 | 10 | 16 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1764 | init-F4-dbg | S4.cpp:1771 | 11 | 983 | S4.cpp:1764 | 11 | 960 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1765 | init-F4-dbg | S4.cpp:1772 | 12 | 12 | S4.cpp:1765 | 12 | 12 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1763 | init-F4-san | S4.cpp:1763 | 8 | 16 | S4.cpp:1763 | 8 | 16 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1765 | init-F4-san | S4.cpp:1772 | 9 | 12 | S4.cpp:1765 | 9 | 12 | True | PASS_EXACT_MATCH |
| fft-ng5 | 1764 | init-F4-san-AL | S4.cpp:1771 | 3 | 960 | S4.cpp:1764 | 3 | 960 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1763 | init-F4-dbg | S4.cpp:1763 | 10 | 16 | S4.cpp:1763 | 10 | 16 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1764 | init-F4-dbg | S4.cpp:1771 | 11 | 983 | S4.cpp:1764 | 11 | 960 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1765 | init-F4-dbg | S4.cpp:1772 | 12 | 12 | S4.cpp:1765 | 12 | 12 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1763 | init-F4-san | S4.cpp:1763 | 8 | 16 | S4.cpp:1763 | 8 | 16 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1765 | init-F4-san | S4.cpp:1772 | 9 | 12 | S4.cpp:1765 | 9 | 12 | True | PASS_EXACT_MATCH |
| kottke-ng5 | 1764 | init-F4-san-AL | S4.cpp:1771 | 3 | 960 | S4.cpp:1764 | 3 | 960 | True | PASS_EXACT_MATCH |

- **结论**：18 个映射项均找到了**唯一匹配的 caller 行**，且各点 K 值与 F3 **完全保持一致**（正如 U284 保留分配顺序与次数的设计预期）。
- 未触发硬停止条件 6。

---

## 8. R9 输入与回归计划（S-J）

### 8.1 R9 输入清单（`R9_INPUTS_S3R5.tsv`，33 行）
依据 U290，本轮不冻结 R9 预注册，输出 `R9_INPUTS_S3R5.tsv`，集中提供 R9 所需的全部输入：
1. **F4 库哈希**：dbg（`6a711fbb…`）、san（`ce057b50…`）、plain（`5a4bfa60…`）；
2. **F4 驱动哈希**：init-F4-dbg（`a4643e7e…`）、init-F4-san（`33a23002…`）、init-F4-san-AL（`f14c536e…`）、init-B-dbg（`3ccc2897…`）；
3. **F4 K 映射表**：18 项精确映射值；
4. **F4 行号映射规则**：S4.cpp 1774 行之后偏移量恒为 +13；
5. **GDB 脚本审计结果**：
   - `r6c_state_bt_r8m2d.gdb`：使用符号/函数名断点，无行号断点；
   - `r6c_state_gdb_r8m2a3.py`：使用符号断点（`r6_probe`、`Simulation_ComputeLayerModes`、`Simulation_GetLayerSolution`）；
   - `malloc_map_r8m2c.gdb`：断点在 `inject_s3r4_init.cpp:79`（位于注入器内，非 S4/ 内部行）；
   - 审计结论：**无需按行号重写任何已有的 GDB 脚本**。

### 8.2 F4 回归计划更新（`REGRESSION_PLAN_F4_S3R5.tsv`，31 行）
在 `REGRESSION_PLAN_F4_R8_M2e.tsv` 基础上完成勘误与更新：
1. 所有 F4 行 K 均标记为"取 `K_MAP_F4_S3R5.tsv`"；
2. F4 行期望明确定义为：`rc1=1, rc2=0, post_call1_solution=NULL, crash_call=NONE`，调用 2 的输出与无注入对照中对应调用逐字节一致（I6 断言）；
3. 改正 H-5(f) 措辞，更正为客观描述；
4. 追加登记 M2 健康 175 点在 F4 上回归、M1 在 F3 与 F4 之间等价对比两项（只登记，待 R9 运行）；
5. 保留两项收口测试（`make test` 在 `$EV` 导出树上运行；Python/Lua E2E 并入 M3）。

---

## 9. 证据文件与 Registries 校验

### 9.1 Registries 小表比对
`checkpoints/p05/registries/s3r5/` 下共 14 项文件，`sha256sum -c SHA256SUMS.txt` 比对全部一致通过：
1. `BUILD_S3R5.tsv`
2. `WARN_DIFF_F3_F4_S3R5.txt`
3. `DIFF_F3_F4_S3R5.txt`
4. `LINEMAP_F3_F4_S3R5.tsv`
5. `K_MAP_F4_S3R5.tsv`
6. `K_MAP_RAW_S3R5.txt`
7. `SELFCHECK_D_S3R5.tsv`
8. `R9_INPUTS_S3R5.tsv`
9. `REGRESSION_PLAN_F4_S3R5.tsv`
10. `STRAY_BASELINE_S3R5.tsv`
11. `GATE_S3R5_start.txt`
12. `GATE_S3R5_end.txt`
13. `noinj_control_s3r5.txt`
14. `map_k_s3r5.txt`

### 9.2 证据目录清单
`checkpoints/p05/evidence/p05-s3r5/SHA256SUMS.txt` 覆盖全部非二进制证据文件，比对通过。依 U288 新规则，清单记录了 safe_run.log 在清单写入时的行数（16 行）及其前 16 行 sha256。

---

## 10. 事件两张表

### 表一：越界写入尝试表
| 轮次 | 命令 | 是否落盘 | 处置说明 |
|---|---|---|---|
| s3r5 | 无 | 否 | 全程无任何越界写入尝试 |

### 表二：工具与脚本事件表
| 轮次 | 命令 / 事件 | safe_run.log 行号 | 是否落盘 | 处置说明 |
|---|---|---|---|---|
| s3r5 | `python3 -I -B testing/d003/stage_s3r5/build_s3r5.py` | 7 | 否 | JS 模板字面量未转义 `\n` 导致 Python SyntaxError（line 108 unterminated string literal）。使用 `node:fs` 重写脚本后在第 8 行重跑成功。 |
| s3r5 | `python3 -I -B testing/d003/stage_s3r5/gen_diff_linemap_s3r5.py` | 9 | 否 | 元组列表第 37 行漏写逗号引发 SyntaxWarning/TypeError。补齐逗号后在第 10 行重跑成功。 |
| s3r5 | DSH PTC 运行时框架落盘 `/tmp/dsh-spill-*` | - | 是 | Harness 框架输出长文本自动截断落盘机制，属框架事件，非执行者违规。 |

---

## 11. 需用户裁决

本轮无规划者无法从仓库查到的事项。所有依据均已给出确切的来源行号、提交号与裁决编号（U283–U290）。

---

本轮已完成 S3R5 范围，等待用户审核。
