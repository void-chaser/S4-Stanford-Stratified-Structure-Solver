# P05-S5 R1 任务书（s5r1）：S5 输入只读盘点、分类分流、登记表补丁草案

## 0 定位与禁止
- 本轮是正式阶段 P05-S5（前端与回归，仅改文档）的第一个子轮次 R1，标识 s5r1。P05 只有 S1–S5，不得出现 P05-S6。
- 只读盘点 + 文档写入。不运行 S4 的任何程序（不 make、不 make test、不跑 E2E/d003 矩阵、不构建、不用 gdb）。不改 S4/、判定器、历史装置、任何已提交的历史产物。
- 不修改 testing/s4test/ISSUE_REGISTRY.md、PROJECT_ROADMAP.md、AGENTS.md：只写补丁草案。
- 不得宣布 P05-S5 或 P05 完成或签收。
- 任务书原文保存为 checkpoints/p05/briefs/P05_S5R1_BRIEF.md。

## 1 开工门禁（start，任一不符就停下报告）
- HEAD = 59e742d5b918b9c194f3aec10148801f7839f263；分支 codex/p05-d003-fft-error-propagation；git status --short 为空。
- git rev-parse HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf（F4）；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- 起始文件（字节数 + sha256 前 16 位，由脚本断言）：
  - registries/RULINGS.tsv 146978 B d33990ca2312eefc，最大编号 U363
  - registries/s4r9/ERRATA_9.txt 65771 B 5a07fc22fd796f92，最后一条 E9-77
  - STATE.md 5318 B dc4c1083bc69284b
  - P05_S3_S4_SIGNOFF.md 2077 B 7b5b412a9fa363ad；P05_S1_S2_SIGNOFF.md 1636 B b6174b499884a593
  - registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv 1401 B 7adf17662bc47b94
  - testing/s4test/ISSUE_REGISTRY.md 20720 B ad17b768c79a3f63；PROJECT_ROADMAP.md 20905 B 2c8cbe18d479584a
- registries/s4r9/M3e/SHA256SUMS.txt 逐项 OK（项数由脚本数出）；m3e 证据 SHA256SUMS.txt 逐项 OK；仓库根 registries/ 不存在；/tmp 顶层快照（条目数 + sha256）。
- 证据目录 EV=$REPO/checkpoints/p05/evidence/p05-s5r1/，开工前 test -e 断言它不存在。

## 2 写入纪律（在 AGENTS.md §3 之上追加，违反即披露）
1. safe_run 后面直接接 python3 -c / python3 -I -B / sh 脚本，禁止 `safe_run … -- bash -c "…$REPO…$EV…"`（M3e 表一 3 次越界尝试即由此产生：外层先展开变量为空）。脚本内部的路径一律由 git rev-parse --show-toplevel 求得，并断言以允许的前缀开头。
2. 每条写入单独一次 safe_run，不得用外层 && 串联多个写入。
3. 门禁检查器里 safe(name, fn, exp) 的 fn 必须是可调用对象（M3e 的 `mkc()` 写法导致 CHECK_CRASHED）。门禁输出中 CHECK_CRASHED 计数必须为 0，这一条本身也是一个断言项。
4. 试跑期（$EV/shakedown/）必须用 --commit-i 模拟值实跑一次 end 门禁，让 POST_I 块真正执行；试跑输出里 CHECK_CRASHED=0、POST_I 各计数与“门禁时刻应有次数”一致，之后才能冻结。
5. 收尾顺序：全部 $EV 写入 → sha_sums（最后一次写 $EV）→ end 门禁（输出写 $EV/gate/，不纳入清单）。脚本名从 FROZEN_SCRIPTS_S5R1.tsv 读取，不得硬编码；读表按列名，缺列报错退出。

## 3 勘误补登（追加到 registries/s4r9/ERRATA_9.txt，纯追加）
- E9-78：M3e end 门禁 POST_I_CALL_COUNT_GATE_R9M3E_END 与 POST_I_CALL_COUNT_M3E_CHAIN_R9M3E_- 两项 FAIL 是检查器缺陷：gate_check_r9m3e.py 第 244 行把 mkc() 的返回元组当作可调用对象传入 safe()。根因是试跑期未实跑 end 门禁的 POST_I 块（m3e/shakedown/ 下无 end 门禁输出）。用脚本从 m3e/safe_run.log 复算：(i) 之后 chain 6 次（第 59–64 行）、gate end 1 次（第 65 行），并引用 GATE_R9M3E_end.txt 第 14 行 CALL_LINES_M3E_CHAIN 为空。只登记，不重跑 M3e，不改 M3e 产物。
- E9-79：M3e 表一 3 次越界写入尝试（safe_run.log 第 1、2、3 行，均未落盘）的成因是 safe_run 接 bash -c 时外层先展开变量。修正方式见本任务书 §2 第 1 条。
- 两条都写明：事实、证据文件与行号、影响范围、处理方式。不新增 U 编号（本轮没有用户新裁决）。

## 4 输入盘点 → $EV/S5_INPUTS_S5R1.tsv
列：input_id, group, canonical_name, source_file, source_locator（行号或节号，由脚本 grep 得出，不得照抄任务书）, source_ruling（RULINGS 中真实存在的 U 编号或“-（事实项）”）, current_status_text（原文摘录 ≤200 字）
- A 组：S5_HANDOFF_R9M3D.tsv 的 7 项 S5-M3D-01..07（S5-M3D-06 的来源按 E9-76 记 U5）。
- B 组：P05_S1_S2_SIGNOFF.md 第 (3) 条：F10 历史因果、F8 历史目录哈希、反事实通量正确性、allzero 设计意图，以及 S1 报告 11.2 的五个哈希来源（按实际条目拆行）。
- C 组：PROJECT_ROADMAP.md 中 D016 与 R-P05-01 两条（行号由脚本定位）；S1/S2 范围声明第 (1) 条“fmm_kottke 除数数值安全”；U99（pattern.c:798 内层循环）、U100（FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9）的 S5 登记要求。
- D 组：ISSUE_REGISTRY.md 中 D003、D016 行，以及任何含 “P05” 的行的现状文字；PROJECT_ROADMAP.md 中 P05 行（验收标准列）的现状文字。
- 去重：同一事项出现在多组时，保留一行，并在 source_file 中列出全部来源；在 $EV/S5_INPUTS_DEDUP_S5R1.txt 记录合并关系。

## 5 逐项分类 → $EV/S5_TRIAGE_S5R1.tsv
列：input_id, class, rationale, evidence_ref, blocks_P06_D004（YES/NO + 依据）, proposed_registry_action, needs_user_ruling（YES/NO）
- class 每项只能取一个：REGISTRY_ONLY（只需在登记表中写明现状）/ NEEDS_TEST（S5 前端与回归需要实测）/ NEEDS_FIX_NEW_DEFECT（新缺陷，另立登记号，不在 P05 修）/ RECORD_ONLY_OPEN（记录在案，保持开放）/ NEEDS_USER_RULING。
- 写“已修好”“已验证”必须有冻结树上的实测证据（注明报告名与轮次）；只读源码得到的写“[源码]”；B 列观察不是修复证据。
- 对照 P05 验收标准（PROJECT_ROADMAP P05 行：每个受影响的 prepare/execute 点正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确），单独写 $EV/P05_ACCEPTANCE_MAP_S5R1.tsv：每条标准对应的已提交证据（报告 + registries 文件）、状态 MET / GAP / NEEDS_USER_RULING。M3a/M3b 的 make test 与 E2E 结果能否作为 S5 “前端与回归”的证据，标为 NEEDS_USER_RULING 并写明利弊，不自行认定。

## 6 草案文档（提交到 checkpoints/p05/）
- P05_S5_REGISTRY_PATCH_DRAFT.md：对 ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md 的逐条 unified diff 草案（只写在本文件里，不应用）。至少覆盖：D003 状态与关闭范围（引用 P05_S3_S4_SIGNOFF.md §2 原文，不改写）；D016 核对结果；非 FMM S4_malloc 另立登记项的草稿；ES3R4-5/528/1164、U99、U100 的登记草稿；P05 行状态文字。每条注明依据文件与行号。草案里不得出现“P05 完成”“已签收 P05-S5”之类的字样。
- P05_S5_PLAN_DRAFT.md：S5R2 及收口的计划草案，内容包括 NEEDS_TEST 项的预注册思路（期望值须在运行前写入并记录 sha256）、需要的驱动和前端（Python/Lua）、预计运行量、需用户裁决的问题清单（逐条编号 Q1..Qn，每条给推荐选项和理由）。
- 本轮报告 P05_S5R1_REPORT.md，按以下顺序：门禁 → 勘误 E9-78/79 → 输入盘点计数（各组行数、去重后行数，由脚本数出）→ 分类计数 → 验收映射 → 草案摘要 → 事件两张表（越界写入尝试 / 工具与脚本事件）→ 需用户裁决 → 交付物（条目不加反引号，项数与 SHA256SUMS 一致）→ 附录 A（试跑 end 门禁摘要）→ 附录 B（正式 end 门禁原文摘要）。结尾写“本轮已完成/未完成 P05-S5 R1 范围，等待用户审核”，附 git log -1 与 git status --short。
- report_check 脚本：报告中每个数字和每句派生文字都要与源表一致；禁用词检查须对报告草稿试跑过，不得误伤合规的否定句；STATE ≤ 8192 B。

## 7 收尾
- 更新 STATE.md：当前轮次 P05-S5 R1；阶段状态写“S1–S4 已由用户签收（带范围声明），S5 进行中（R1 盘点）”；开放问题表改为指向 S5_TRIAGE_S5R1.tsv；保持一页以内。
- 小表复制到 checkpoints/p05/registries/s5r1/：GATE_S5R1_start.txt、S5_INPUTS_S5R1.tsv、S5_INPUTS_DEDUP_S5R1.txt、S5_TRIAGE_S5R1.tsv、P05_ACCEPTANCE_MAP_S5R1.tsv、REPORT_CHECK_S5R1.txt、FROZEN_SCRIPTS_S5R1.tsv，并写 SHA256SUMS.txt，逐项比对 sha256。
- 新脚本放 testing/d003/stage_s5r1/，文件名带 s5r1。
- 顺序：0a 自检 → start 门禁 → 保存任务书 → 盘点/分类/草案脚本试跑 → 收尾链与 end 门禁试跑（$EV/shakedown/，模拟 commit-i，CHECK_CRASHED=0）→ 冻结 FROZEN_SCRIPTS_S5R1.tsv → 记录提交 (i)（ERRATA、STATE、草案、brief、冻结脚本）→ 冻结期正式各跑一次 → 收尾提交 (ii)（报告、registries/s5r1）。冻结期不修脚本、不重跑；门禁 FAIL 照实写入附录 B。
- 提交信息格式：`P05-S5 R1 (i|ii): … ; awaiting user review`。提交范围限 checkpoints/p05/ 与 testing/d003/。
