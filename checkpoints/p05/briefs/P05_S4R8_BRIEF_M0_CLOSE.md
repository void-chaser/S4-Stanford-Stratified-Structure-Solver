# P05-S4 R8 M0 收尾(第 3 次开工的续轮):收尾门禁更正、复制、清单、最终提交

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 R8 的 M0,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收。**不修改 S4/。**
**本轮不做任何构建、链接、注入运行或等价运行**;M0 的运行结果已完成,不重跑、不覆盖。

## 0. 与前几份任务书的关系
- `briefs/P05_S4R8_BRIEF_M0.md`、`_RESTART.md`、`_RESTART2.md` 都不改,继续有效。冲突时以本任务书为准,其次是 RESTART2、RESTART、原任务书。
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_CLOSE.md`。
- 第二步:读 AGENTS.md、RESTART2 全文、`P05_S4R8_REPORT_M0.md`、`registries/s4r8/ERRATA_8.txt`。**读完直接写脚本**,不要用内联命令预核对。
- 写入方式、运行前检查、停止条件、内联命令白名单:照 RESTART2 §1 U132 与 §2。

## 1. 用户裁决(追加到 RULINGS.tsv,status `生效`,来源写"R8 M0 收尾任务书 §1";接在 U132 之后;同时追加到 ERRATA_8.txt 末尾)
- U133:RESTART2 §2.1 end(2)"已跟踪且被修改的文件只能是 STATE.md"是**规划者错误**:ERRATA_8.txt 已在记录提交 2875c55 中提交,收尾追加 E8-5…是合法的。
  更正:收尾时已跟踪且被修改(` M`)的文件只能是 `checkpoints/p05/STATE.md` 与 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`;
  未跟踪项(`??`)只能位于 `checkpoints/p05/` 或 `testing/d003/stage_s4r8/` 下。
  执行者不放宽门禁而停止,做法正确。`GATE_R8_M0_R2_END.txt`(sha256 a10e081742bb4df95cb4c31b31706fe992fc427be1db4e1642f81232ee2494c9)作为停止记录保留,不删、不改。
  gate2_r8.sh 已提交,不修改;新建 gate3_r8.sh 做收尾门禁。记为 E8-14。
- U134:规划者对照会话记录核对,表二还漏报以下第 3 次开工的只读内联命令(均不写入,不停止,记为 E8-15)。
  另外,报告 §13.2 第 1、2 条的 UTC 可以查到,一并补上:
  · 04:23:21Z `grep -n … checkpoints/p05/evidence/p05-s3r4c5/safe_run.log | cut -c1-160 | head -12; … wc -l …`(bash 中用 grep、cut,超出白名单)
  · 04:28:39Z `wc -l …/tmp/norm_*.txt; echo ---; head -n 6 … | cut -c1-150`(cut 超出白名单)
  · 04:29:33Z `ls … ; ls checkpoints/p05/evidence/p05-s4r7/build_r7/seam_plain/ 2>&1; sed -n 1p … 2>&1 | head -n 1`(含 `2>&1`;sed 超出白名单)
  · 报告 §13.2 第 1 条为 04:24:41Z;第 2 条为 04:23:48Z;第 3 条为 04:26:53Z;第 4 条为 04:38:49Z。
- U135:E8-10 已由 E7-34 / U74 / U75 覆盖(ADD 表的 G2c route 登记错误;运行器按历史规则得到 S4FMM_TWICE=slab,环境断言全部 PASS)。
  不另立事项,**关闭**。记为 E8-16。
- U136:E8-9(F3-dbg 库 sha256 DIFFERENT)的原因查明移到 R8 M1 第 0 步(M1 的 gdb 链路要用 dbg 库)。
  方法沿用 R7 的 U84/U87(`testing/d003/stage_s4r7/check_dbg_strip_equiv_r7.sh`、`mask_build_id_r7.py`,只读引用,在 M1 中复制为 _r8 版本)。
  M0 只记录,不查。记为 E8-17。

## 2. 收尾门禁 gate3_r8.sh(新文件)
- 复制 gate2_r8.sh 的 end 模式,只改两处:
  (1) U133 的 status 规则;
  (2) `HEAD` 等于 2875c557c6f2348bdbad3b077af4651f94eb65b2,`HEAD^` 等于 3ab56801e697910bdff9fbe6056807c2e41841b5。
  其余检查与 gate2 end 相同。另外加一项:`GATE_R8_M0_R2_END.txt` 的 sha256 等于 U133 中的值。
  `diff -u gate2_r8.sh gate3_r8.sh` 经脚本写入 `$EV/GATE3_VS_GATE2_DIFF_R8.txt`,只能出现上述改动。
- 用法:`sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate3_r8.sh p05-s4r8 GATE_R8_M0_R3_END.txt end <tmp_count> <tmp_sha256> 0 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  (`/tmp` 快照用白名单里的两条内联命令取得。)
- **顺序:**
  (a) 先用 edit 把 §1 的 U133–U136 追加到 RULINGS.tsv 与 ERRATA_8.txt(E8-14…E8-17);
  (b) 再写 gate3_r8.sh;用 grep 工具查禁止项,结果必须 0 行;经 prerun_log_r8.sh 记录;
  (c) 运行 gate3。FAILS 必须为 0,不为 0 就停下报告。
  注意:RULINGS.tsv 是已跟踪文件,追加后会是 ` M`,所以 U133 的允许列表**加上** `checkpoints/p05/registries/RULINGS.tsv`(即共三个文件可以是 ` M`)。

## 3. 复制与清单(照原任务书 §6,补充以下内容)
- 复制前先确认全部输入存在,再建目录。copy_registries_r8.sh 复制到 `registries/s4r8/`:
  GATE_R8_M0.txt、GATE_R8_M0_R2.txt、GATE_R8_M0_R2_END.txt、GATE_R8_M0_R3_END.txt、GATE3_VS_GATE2_DIFF_R8.txt、S4R7_MANIFEST_CHECK_R8_R2.tsv、
  S4R7_MANIFEST_CHECK_R8_R2_END.tsv、S4R7_MANIFEST_CHECK_R8_R3_END.tsv(若 gate3 生成)、PRERUN_CHECKS_R8_M0.txt、TREE_CHECK_R8.txt、BUILD_R8.tsv、
  SEAM_DIFF_F2_vs_F3_R8.txt、DRIVERS_R8.tsv、DRIVERS_R8_F2_REUSED.tsv、DRIVER_MAP_R8_D.tsv、D_PREPARE_CHECK_R8.tsv、EXPECT_R8_D.txt、
  RESULTS_R8_D_pass1.tsv、RESULTS_R8_D_pass2.tsv、D_SUMMARY_R8.txt、EXPECT_R8_NOINJECT.txt、RESULTS_R8_NOINJECT_run1.tsv、RUNNER_DIFF_R8_M0.txt、
  status_before_rec_r8.txt。任一文件超过 1 MB 就不复制,只在 SHA256SUMS 中记录它的 sha256,并写入 E8。
- 然后在 `registries/s4r8/` 写 SHA256SUMS.txt,覆盖复制件与 ERRATA_8.txt。注意:ERRATA_8.txt 是只追加文件,**在写清单之前**完成对它的全部追加。
  在该目录内 `sha256sum -c`,并逐个比对副本与原件,结果写入 `$EV/COPY_CHECK_R8_M0.txt`。
- manifest_r8.sh(已写,未运行)写 `$EV/SHA256SUMS.txt` 与 `SHA256SUMS_EXCLUDED_R8_M0.txt`。运行前做禁止项检查。

## 4. 报告与 STATE
- `P05_S4R8_REPORT_M0.md` 用 edit 修改:
  · §2 增加 §2.4"收尾门禁":R2_END FAILS=1(U133,规划者错误)、R3_END 的实际结果;
  · §11 改为:三项均已裁决(U133、U136、U135);
  · §13.2 补上 U134 的三条命令与四个 UTC;§14 同步更新;
  · §10 按实际情况更新;
  · 结尾按实际结果写"本轮已完成 R8 M0 范围,等待用户审核"或"本轮未完成 R8 M0 范围,等待用户审核"。
- STATE.md 用 edit 修改,保持一页以内:
  · 当前轮次补"收尾门禁 R3_END FAILS=…;下一步 R8 M1(含 dbg 库 strip 等价,U136)";
  · 开放问题表新增一行"F3-dbg 库 sha256 DIFFERENT(E8-9)| 记录 | R8 M1 第 0 步(U136)";
  · 证据位置写明 `registries/s4r8/SHA256SUMS.txt`。

## 5. 最终提交
- commit_final_r8_m0.sh:先把 `git status --short` 写入 `$EV/status_before_final_r8.txt`;git add 逐个列出:
  STATE.md、P05_S4R8_REPORT_M0.md、briefs/P05_S4R8_BRIEF_M0_CLOSE.md、registries/RULINGS.tsv、registries/s4r8/(整个目录)、
  testing/d003/stage_s4r8/ 下全部未跟踪脚本(逐个列出文件名,不用 -A 或 .)。
  提交信息(先写入 `$EV/COMMIT_MSG_R8_M0_FINAL.txt`):
  `P05-S4 R8 M0 on F3: builds, seam plain, D smoke 8/8 MATCH (U113/U119/U124), F2-F3 no-injection 117/117 IDENTICAL, closeout gate per U133, rulings U133-U136, STATE updated. awaiting user review`
- 提交后,把真实的 `git log -3 --oneline` 与 `git status --short` 写入 `$EV/FINAL_GIT_R8_M0.txt`,并在对话中原样贴出。status 应为空,不为空就说明原因。
- 违规两张表照规则写;本轮的内联命令自查也要写(没有就写"无")。
