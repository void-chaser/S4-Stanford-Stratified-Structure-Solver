# P05-S4 R7 续 3(同一子轮次 R7,不是新阶段):补登记 + M2 运行(分两段提交)

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、R7 任务书与续 1、续 2(checkpoints/p05/briefs/P05_S4R7_BRIEF*.md),
checkpoints/p05/registries/s4r7/ERRATA_7.txt、checkpoints/p05/P05_S4R7_REPORT_M2_PART.md、
checkpoints/p05/evidence/p05-s4r7/DRIVER_REPRO_CHECK_M2.txt。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。本段的 run 标签用 run4。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT3.md。

## 0. 硬规则(在前几段的基础上补充)
- 所有写入经 `sh testing/d003/safe_run.sh p05-s4r7 -- sh -c '...' sh <参数>`。
- 在 `sh -c` 内部禁止 `set --`,也禁止给 $1、$2 重新赋值。循环变量用独立的变量名(例如 `for spec in ...; do m=${spec%% *}; ...`)。
  上一段 fft/probe_m2 写到仓库根,就是 `set --` 覆盖了 $1 造成的。
- 禁止 `python3 -c`(包括只读核对)。核对用提交到 stage_s4r7/ 的脚本,或用 read/grep 工具。
- `rm -rf` 只允许用于本段新建的构建目录。必须写成 `case "$1" in "$EV"/build_r7/*) rm -rf "${1:?}";; *) echo REFUSED; exit 2;; esac`。
- 每组运行之前,先用 `test -e` 确认输出目录不存在;已存在就停下(U17)。

## 1. 用户裁决(追加到 ERRATA_7.txt 和 RULINGS.tsv;原有行不改)
- U49:续 2 的 U44–U48 没有追加到 RULINGS.tsv(只读核对:grep "^U4[4-8]" 计数为 0),与 E7-7 是同一类遗漏。
  本段补上 U44–U53,并写 E7-18 记录这次遗漏。
- U50:E7-17("G1 没有注入请求,不能运行")撤销。G1 的注入请求可以确定性地重建,依据是
  testing/d003/stage_s4/run_r3_sweep.py:32 与 :111–120:
  request = {malloc: s4malloc, plan: plan, exec: exec}[category],NTH = 点 id 中的 NTH,NG = 9,stack = pattern;
  inj_call = registries/s4r3/FIELDCALL_MAP.tsv[(route, mode, category, NTH)];twice 路线设 S4FMM_TWICE=slab(case 名以 t4/ 开头)。
  规划者已只读核对:141 个 F 注入点全部能在 FIELDCALL_MAP 中查到,0 个缺失,与 RESULTS_R3 的 inj_call 列逐行一致。
  E7-17 原文只在证据目录 DRIVER_REPRO_CHECK_M2.txt 中,本段在 ERRATA_7 中补写 E7-17(原文引用)与本条撤销。
- U51:G2a(seam 25 点,rc 类别)纳入 M2。依据:F 的 plain seamF 与 fmmret 库 sha256 与 R4 逐字节相同。G5/G6 的状态判定仍在 M3。
- U52:接受 POSTHOC 对照重新判定(16 CONTROL_OK + 2 BASELINE_RC_EQUAL,两遍)作为 R7 M1 的对照结论;M1 原 MISMATCH 行保留。
  fftjones 不补测 M=3([源码]:与 jones 同为 rect 分支、同一个 cg 分配;jones M=3 已实测)。
- U53:违规分类更正:fft/probe_m2 在仓库内,归表二(路径拼错),根因是 `set --` 覆盖了 $1;
  续 2 中的 `python3 -I -B -c` 只读核对违反任务书第 0 节,补列入表二。写 E7-19,续 2 报告不改。

## 2. 第一步:补登记并提交(在任何 M2 运行之前完成)
1. ERRATA_7 追加 E7-17(引用原文)、U50 的撤销、E7-18、E7-19;RULINGS.tsv 追加 U44–U53。
2. 补充预注册 $EV/REGISTRY_S4_PRE_R7_M2_ADD.tsv,由新脚本 make_prereg_m2_add_r7.py 生成,只覆盖 G1、G2a、G2c、G2c-control:
   - 每行的 point_id、tree、expected_class 必须与 v2(REGISTRY_S4_PRE_R7_M2.tsv,sha e4dd2c87…)对应行逐字相同。
     脚本逐行比对,不同就退出非零,并且不写文件。
   - 新增列:request、nth、route、twice_env(slab 或 -)、inj_call、ng、stack、inj_call_source(FIELDCALL_MAP 行或源表列)。
   - G1:按 U50 的映射;同时核对 FIELDCALL_MAP 与 RESULTS_R3 的 inj_call 列一致,结果写进表头。
     其中 22 个 F 点在 R3 为 INVALID(未到达,E7-4),本组照常运行,期望 INVALID;它们的 plancall 版本在 G2b 中。
     G1 对照(每种模式一行)用 control=True 判定。
   - G2a:request 取 RESULTS_R4.tsv 的 request 列;inj_call 由 run_r4_matrix.py 的 M.inj_call_of 规则得到,规则来源写进表头;
     库用续 2 构建的 plain seamF 与 fmmret(F、F2)。
   - G2c:request 由 run_r4_regress.py 的规则得到(R3.INJECT[category]);inj_call 取 REGRESS_R4 的 inj_call 列。
   - 写 sha256 与 UTC 时间。v2 本身不改,也不废止。
3. 运行器 testing/d003/stage_s4r7/run_m2_r7.py(新文件):
   - 读 v2,G1、G2a、G2c 的行合并 ADD 表(按 point_id 连接;连接不上就退出非零)。
   - 驱动与库从 DRIVERS_R7.tsv 和续 2 的 plain seam 构建记录中读取,运行前逐个比对 sha256。
   - 判定:judge_d003.classify(rc, rc1, rc2, hit, control, real=(category != exec), inj_call=<行内值>),只导入,不修改。
     facts 同时解析 stdout 与 stderr(HIT 行在 stderr,见 DRIVER_REPRO_CHECK_M2.txt)。
   - `--dry-parse`:不运行 S4,检查每行的 request、inj_call、驱动 sha256 是否齐全,打印每组行数和无法解析的行数。
4. dry-parse 输出写 $EV/DRYPARSE_R7_M2_run4.txt,要求无法解析 = 0。
5. 复制到 registries/s4r7/:v2 及其 sha256 和时间戳、v1(superseded)及其 sha256、ADD 表及其 sha256 和时间戳、DRYPARSE、
   GDB_CHAIN_SUMMARY_R7_A1、LINEMAP_A1_R7、RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC、REGISTRY_S4_PRE_R7_M1_ERRATA_CTRL、
   BUILD_SEAM_PLAIN_R7、DRIVER_REPRO_CHECK_M2。写 SHA256SUMS_M2pre.txt(同时收录 ERRATA_7、RULINGS.tsv、STATE.md 的当前版本),并逐个比对。
6. STATE.md 更新为"R7 进行中:M1 已提交,M1a 已完成,M2 预注册已提交(v2 + ADD),M2 未运行"。
7. 提交:"P05-S4 R7 M2 pre-registration committed (v2 + ADD, dry-parse 0), rulings U44-U53, errata E7-17..19; no M2 run. awaiting user review"。
   **在这次提交完成之前,不得运行任何 M2 注入。**

## 3. M2a:G2b、G3、G4(plancall 路线,140 个点 × F、F2 × 两遍)
- run4,pass1 与 pass2;输出 $EV/RESULTS_R7_M2_<组>_pass{1,2}_run4.tsv。
- 对比表 $EV/REGRESS_R7_M2a.tsv。verdict 定义沿用续 2 第 5 节:MATCH / REGRESSION / ENV_DRIFT / FLAKY / MISMATCH。
  另外逐项比较 F2 与 F(R7) 的 rc、rc1、rc2、hit,不一致的单独成表。
- 组内出现非 MATCH:两遍跑完后停下,不进入 M2b。
- 中间提交:小型表复制到 registries/s4r7/,写 SHA256SUMS_M2a.txt;
  提交信息为 "P05-S4 R7 M2a (G2b/G3/G4) ... awaiting user review"。
  如果剩余预算不够做 M2b,就在这里停下,写 P05_S4R7_REPORT_M2.md,标为"M2a 完成,M2b 未完成"。

## 4. M2b:G1、G2a、G2c(含对照)
- 顺序:G2c 与 G2c-control → G1 → G2a。每组两遍;输出文件与判定方式同 M2a。
- G1 的 22 个 INVALID 点:期望 INVALID 且 hit = 0。若 F2 上 hit 变为 1,记为 MISMATCH 并单独列出,不要改期望。
- G2a 用 plain seam 库;运行前比对库的 sha256 与 BUILD_SEAM_PLAIN_R7.tsv 一致。

## 5. M2 提交
- 对比表 $EV/REGRESS_R7_M2.tsv(M2a 加 M2b),写 SHA256SUMS_M2.txt。
- 写 P05_S4R7_REPORT_M2.md,须包含:补登记与 dry-parse;每组两遍结果与 verdict 计数;F2 与 F(R7) 的 rc 逐项差异;
  M1a 的结论(引用续 2 报告);RP-R6d-1 的状态(措辞只能是 "F2 回归 REPORTED_FAILURE x/y,两遍");
  需要用户裁决的事项(至少:P05-S3 是否签收(U47);M3 是否开工);违规两张表(按 U53 的分类)。
  结尾写 "本轮未完成 R7 范围(M2 已完成/未完成),等待用户审核",附 git log -3 与 git status --short。
- 更新 STATE.md(一页以内)。提交信息为 "P05-S4 R7 milestone M2 ... awaiting user review"。M2 提交之后停下,不进入 M3。

## 6. 停止条件
前几段的停止条件全部有效,另外:
- ADD 表与 v2 的 point_id、tree 或 expected_class 有任何不一致;
- dry-parse 无法解析的行数不为 0;
- 第 2 节的提交完成之前就运行了任何注入;
- 驱动或库的 sha256 与记录不一致;
- 任一组出现 REGRESSION、ENV_DRIFT、FLAKY 或 MISMATCH(该组两遍跑完后停);
- 违反第 0 节的 `set --`、`python3 -c` 或 `rm -rf` 规则(出现一次就停)。
"未完成"与"不可行"必须区分。
