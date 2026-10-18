# P05-S5 R2 任务书（s5r2）：裁决入账、S5R1 勘误、D017 清单、登记表落实、D016 公共 API 实测

## 0 定位与禁止
- 本轮是正式阶段 P05-S5 的子轮次 R2，标识 s5r2。P05 只有 S1–S5，不得出现 P05-S6。不得宣布 P05-S5 或 P05 完成或签收。
- 不改 S4/、判定器、testing/d003/ 历史装置、任何已提交的历史产物（含 registries/s5r1/、S5R1 报告与两份 S5R1 草案）。S5R1 的问题只用勘误登记。
- 允许运行：在 $EV 内由 git archive 导出的 F4 树上构建 Python 扩展与 Lua 可执行文件，运行 D016 的 Python/Lua 点。本轮不跑 make test、不跑全量 E2E、不跑 d003 矩阵（这些留到 S5R3 收口）。
- 任务书原文保存为 checkpoints/p05/briefs/P05_S5R2_BRIEF.md。

## 1 用户裁决（照录入 RULINGS.tsv，纯追加 U364–U371，原文不得改写）
- U364：M3a/M3b 的 make test 与 E2E 作为 F4 上的历史证据，可被 S5 引用；S5 收口轮（S5R3）在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点）。修复前证据不得称为修复后验证。
- U365：D016 在 S5R2 用 Python 与 Lua 公共 API 实测（VL，n_G=1）；NV 的 -10 路径触发不了，维持 [源码] 结论。
- U366：F10 历史因果（S5-B-01）、R-P05-01 的反事实通量与 allzero 设计意图（S5-B-03/B-04/C-02）保持 OPEN，转出 P05，写入 S5 范围声明，不阻塞。
- U367：F8 历史目录（S5-B-02）不授权访问，保持未验证。
- U368：S1 报告 11.2 的 5 个哈希来源（S5-B-05..09）认定为无法判定，不改写 11.2 与 EVIDENCE.sha256。
- U369：非 FMM S4_malloc 登记为 D017；登记前先只读逐点列出清单。
- U370：ES3R4-5/528/1164 与 U99 登记为 R-P05-02，U100 登记为 R-P05-03；一律写 F4 行号，旧树行号放在括号里注明。
- U371：批准本轮把补丁 v2 应用到 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md，这两个文件纳入本轮提交范围；不改 AGENTS.md。

## 2 开工门禁（start，任一项不符就停下报告）
- HEAD = 9f537f7c312b2ab7c64d5c0ea82da34e637da5d4；分支 codex/p05-d003-fft-error-propagation；git status --short 为空。
- HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- 起始文件（字节数 + sha256 前 16 位，由脚本断言）：RULINGS.tsv 146978 d33990ca2312eefc（最大编号 U363）；registries/s4r9/ERRATA_9.txt 67981 95b23f21b2e48a1c（最后一条 E9-79）；STATE.md 3075 bdd9668c162832cc；P05_S5_REGISTRY_PATCH_DRAFT.md 9358 7a5f1e72a8692335；P05_S5_PLAN_DRAFT.md 5351 ade7cf3dfaf82f59；registries/s5r1/S5_INPUTS_S5R1.tsv 7348 08e52d2f148b9fe4；S5_TRIAGE_S5R1.tsv 6455 ee5965416d319904；testing/s4test/ISSUE_REGISTRY.md 20720 ad17b768c79a3f63；PROJECT_ROADMAP.md 20905 2c8cbe18d479584a。
- registries/s5r1/SHA256SUMS.txt 逐项 OK；p05-s5r1 证据目录的 SHA256SUMS.txt 逐项 OK（项数由脚本数出）；仓库根目录下不存在 registries/；对 /tmp 顶层做快照；开工前用 test -e 断言 EV=$REPO/checkpoints/p05/evidence/p05-s5r2/ 不存在。

## 3 写入纪律（在 AGENTS.md §3 之上追加，违反即披露）
1. safe_run 后面直接接 python3 -I -B 脚本或 sh 脚本，禁止 safe_run … -- bash -c。脚本内部的路径一律由 git rev-parse --show-toplevel 求得，并断言以允许的前缀开头。每条写入单独一次 safe_run，不得用 && 串联。
2. 门禁里的 safe(name, fn, exp)：fn 必须是可调用对象；CHECK_CRASHED=0 本身也是一个断言项。
3. 门禁检查器在"清单是否覆盖全部文件"一类的检查中，要同时排除 gate/、shakedown/gate/、tmp/。排除列表本身写进门禁输出。
4. 试跑期在 $EV/shakedown/ 内用 --commit-i 模拟值实跑 end 门禁，要求 CHECK_CRASHED=0、POST_I 各项计数等于"门禁时刻应有次数"、0 FAIL，然后才冻结。
5. **正式门禁之后不得手工修改任何已提交文件，不得 amend，不得 rebase。** 附录 B 由冻结脚本从门禁输出生成，写进单独的文件 checkpoints/p05/P05_S5R2_GATE_APPENDIX.md；报告正文只引用这个文件，不内嵌门禁结果。report_check 在收尾链中、写 sha_sums 之前，对最终版报告运行。如果门禁后发现报告有错，写进下一轮的勘误，本轮不改。
6. 提交 (i) 之后，(i) 中的文件不得再改动。草案和 STATE 在 (i) 之前定稿。
7. 收尾顺序：全部 $EV 写入 → sha_sums（最后一次写 $EV）→ end 门禁（输出写 $EV/gate/）→ 生成附录文件 → 提交 (ii)。脚本名从 FROZEN_SCRIPTS_S5R2.tsv 读取，读表按列名，缺列就报错退出。
8. 预注册在正式运行之前写入并记录 sha256，状态写 INFLUENCED（参考了 S1R 的观察）。之后只能新建 *_ERRATA* 文件，不得通过修改期望值来消除 MISMATCH。

## 4 S5R1 勘误（新建 checkpoints/p05/registries/s5r2/ERRATA_S5.txt，条目 ES5-1 起；以后各轮纯追加）
每条写明：事实、证据文件与行号（由脚本 grep 或读出）、影响范围、处理方式。
- ES5-1：S5-B-05/06/07/08 的 source_locator 指向全文第一次出现处（第 359/58/374/389 行），应为 S1_BASELINE_AND_ENUMERATION.md 11.2 表的第 478/479/480/481 行；current_status_text 应为表中的哈希原文。S5-B-09（第 485 行）无误。由脚本重新定位，给出更正后的 5 行（只写进勘误和新总表，不改 s5r1 产物）。
- ES5-2：补丁草案和 U99 中的 pattern.c:798 是 B/A 树的行号，F4 上是第 815 行；528 与 1164 是旧树行号，F4 上 shape_get_intersection_area 在第 474 行、fprint_double 在第 1178 行。用 git show 05097a7:S4/pattern/pattern.c 由脚本核对 B(37a82e8)、A(876181c)、F4 三棵树并列出行号。U99 原文不改。
- ES5-3：S5R1 正式门禁之后对报告和两份草案做了手工修改并 amend 了 (ii)，修改后没有重跑 report_check。本轮用新脚本对 S5R1 最终版报告做只读复核（禁用词，以及数字与源表一致），结果写入 $EV/S5R1_REPORT_RECHECK_S5R2.txt，并逐行列出 6089637..9f537f7 之间两份草案的差异。
- ES5-4：S5R1 end 门禁的 EVIDENCE_SUMS_COVERS_ALL FAIL 是检查器缺陷（没有排除 shakedown/gate/）。由脚本复算：排除该目录后，清单是否覆盖全部文件。
- ES5-5：S5R1 输入表中"约 35–43 处"从未逐点核实，以本轮 §5 的清单为准。
- 不新增 U 编号以外的裁决。ERRATA_9 本轮不改。

## 5 D017 只读清单 → $EV/D017_S4MALLOC_INVENTORY_S5R2.tsv
- 在 git show 05097a7 的 S4/ 全部 .c/.cpp/.h 中逐点列出 S4_malloc 的出现位置。列：file, line, function, kind（CALL/DECL/DEF/COMMENT）, in_fmm_dir（YES/NO）, d003_scope（IN/OUT）, d003_basis（OUT 时引用用户范围决策：不在模式/缓存安装验收路径，也不在 FMM/FFT 失败传播链；IN 时给出 S3/S4 的红点或裁决编号）, null_check_present（[源码] YES/NO）, consequence_on_fail（[源码]，≤80 字）。
- 计数由脚本输出：总出现数、CALL 数、IN 数、OUT 数。OUT 部分即 D017 的范围。全部只读源码，统一标 [源码]，本轮不运行。

## 6 S5 开放项总表 → checkpoints/p05/P05_S5_OPEN_ITEMS.tsv（提交）
- S5R1 去重后的 25 行逐行落位，加上 ES5-1 的更正。列：input_id, final_disposition（REGISTERED_D016 / REGISTERED_D017 / REGISTERED_R-P05-0x / OPEN_TRANSFERRED_OUT / RECORD_ONLY_OPEN / TEST_S5R2 / TEST_S5R3）, ruling（U 编号或 S5R1 分类依据）, registry_location（文件:行号，在应用补丁之后由脚本求得）, scope_note。
- 6 行 RECORD_ONLY_OPEN（S5-M3D-01/02/05/06/07、S5-C-03）必须有落位，不能只停留在"S5 登记表"这个说法上。

## 7 登记表补丁 v2 并应用（依据 U371）
- 新写 checkpoints/p05/P05_S5_REGISTRY_PATCH_V2.md：在 S5R1 草案基础上吸收 U364–U371 与 ES5-1..5（F4 行号；D017 引用 §5 清单的计数；R-P05-02/03；D016 写"已实施（3e77aa9，[源码] F4 pattern.c 2210–2216）"，公共 API 实测结果引用本轮 §8 的结论；P05 行状态写"S1–S4 已由用户签收（带范围声明）；S5 进行中（R2）"）。
- 用一个新脚本 apply_patch_s5r2.py 应用 v2：先断言两个目标文件的起始 sha256，应用后输出 unified diff 到 $EV/REGISTRY_APPLY_DIFF_S5R2.txt，并断言只改动了 v2 列出的那些行。不得出现"P05 完成""P05-S5 已签收"之类的字样。
- D016 行的最终文字以 §8 的实测结果为准。因此 §8 必须在 apply 之前完成，并且在提交 (i) 之前定稿。

## 8 D016 公共 API 实测（F4）
- 构建：用 git archive 把 05097a7:S4 导出到 $EV/trees/F4（经 safe_run），在这里构建 Python 扩展与 Lua 可执行文件，不注入。记录 libS4.a、.so、S4 的 sha256；与 registries/s4r9/M3b/E2E_BUILD_R9M3B.tsv 对照，仅作参考，不一致不算 FAIL。
- 校准（试跑期，不算正式结果）：参考 checkpoints/p05/evidence/t6_vl_nb1.py 与 P05_S1R_O1_ATTRIBUTION.md 第 4 节，建新脚本 d016_py_s5r2.py 与 d016_lua_s5r2.lua；Lua 的 API 必须逐条对照 S4/main_lua.c 核实。**两个前端都要冒烟。** 只读源码追踪 F4 上的 -10 经 fmm_PolBasisVL → Simulation_ComputeLayerModes → 公共 API 的映射，写入 $EV/D016_TRACE_S5R2.md（文件:行号，[源码]），据此推出期望的返回码和异常文本。
- 预注册 checkpoints/p05/registries/s5r2/PREREG_D016_S5R2.tsv 加 .sha256.txt，状态写 INFLUENCED，**在正式运行之前写好，并纳入提交 (i)**。点族（每个点分别在 py 与 lua 上跑）：
  - VL NB=1、2、3、4：失败点。可见报错（期望文本来自 D016_TRACE）；不得返回成功或含 NaN 的数值；不得崩溃。stderr 是否还出现 "Layer eigensystem returned info = 2" 按源码追踪结果预注册。
  - VL NB=5、9：对照点，成功且结果有限。
  - Jones NB=1、NV NB=1：对照点，成功且结果有限（S1R 实测网格为 8×8）。
  - 恢复：同一进程中失败之后，新建对象（VL NB=9），结果与另起进程得到的参考值逐元素相对误差 ≤1e-12。同一对象用同样的选项重试，期望得到同一失败（确定性失败，不崩溃）。**不得在 solve 之后调用 SetOptions 或改 NumBasis**（那是 P06/D004 的范围）。
- 正式运行两遍。判定只依据事实（rc、异常类型和文本、数值是否有限、与参考值的误差），输出 $EV/D016_VERDICT_S5R2.tsv：MATCH / MISMATCH / FLAKY。如有 MISMATCH 照实报告，不修，不改期望值。
- 措辞：D016 的结论只写"在 F4 上、在该输入下经公共 API 可见失败且恢复正确"，不写"已修好"。

## 9 收尾
- 更新 STATE.md（≤8192 B，在提交 (i) 前定稿）：当前轮次 P05-S5 R2；开放问题指向 P05_S5_OPEN_ITEMS.tsv；新增 S5R3 收口待办（make test、E2E 重跑、就绪审计）。
- 小表复制到 registries/s5r2/：GATE_S5R2_start.txt、ERRATA_S5.txt、D017_S4MALLOC_INVENTORY_S5R2.tsv、PREREG_D016_S5R2.tsv(+sha256)、D016_VERDICT_S5R2.tsv、D016_TRACE_S5R2.md、REGISTRY_APPLY_DIFF_S5R2.txt、S5R1_REPORT_RECHECK_S5R2.txt、REPORT_CHECK_S5R2.txt、FROZEN_SCRIPTS_S5R2.tsv，再写 SHA256SUMS.txt 并逐项比对。
- 报告 P05_S5R2_REPORT.md，按以下顺序：门禁 → 裁决入账 → 勘误 ES5-1..5 → D017 清单计数 → 开放项总表计数 → 登记表应用 diff 摘要 → D016 结果（两遍） → 事件两张表 → 下一轮（S5R3）建议 → 交付物（条目不加反引号，项数与 SHA256SUMS 一致）→ 附录 A（试跑门禁摘要）→ 附录 B 见 P05_S5R2_GATE_APPENDIX.md。结尾写"本轮已完成/未完成 P05-S5 R2 范围，等待用户审核"，附 git log -1 与 git status --short。
- 新脚本放在 testing/d003/stage_s5r2/，文件名带 s5r2。
- 顺序：0a 自检 → start 门禁 → 保存任务书 → 裁决与勘误脚本试跑 → D017 清单 → 构建与 D016 校准（试跑）→ D016 预注册 → 收尾链与 end 门禁试跑（shakedown，模拟 commit-i，0 FAIL）→ 冻结 FROZEN_SCRIPTS_S5R2.tsv → 冻结期 D016 正式两遍 → 应用补丁 v2，写开放项总表和 STATE → 提交 (i)（brief、RULINGS、ERRATA_S5、预注册、补丁 v2、两个登记文件、开放项总表、STATE、冻结脚本）→ 收尾链 → end 门禁 → 生成附录文件 → 提交 (ii)（报告、附录文件、registries/s5r2）。
- **注意：D016 正式运行在提交 (i) 之前进行，所以预注册的时间先后要靠 safe_run.log 的时间戳和预注册的 sha256 来证明。** 门禁里加一项断言：PREREG 的写入行号小于第一条正式 D016 运行的行号。
- 冻结期不修脚本、不重跑；门禁 FAIL 照实写入附录。提交信息格式：P05-S5 R2 (i|ii): … ; awaiting user review。提交范围限于 checkpoints/p05/、testing/d003/，以及依据 U371 的 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md。
