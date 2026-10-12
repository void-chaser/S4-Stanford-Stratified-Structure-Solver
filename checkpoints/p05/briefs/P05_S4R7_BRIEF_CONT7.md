# P05-S4 R7 续 7(同一子轮次 R7,不是新阶段):修 S4FMM_NTH 缺陷 → 重跑整个 M2b(run6) → M2 里程碑

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收,不写签收文件。不修改 S4/、判定器,以及 testing/d003/ 下的历史装置(matrix_r2.py 只导入,不修改)。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S4R7_REPORT_M2_STOP_G1.md、
P05_S4R7_BRIEF_CONT6.md 与 CONT6_ADD1.md(操作规则与 U64–U68 仍然有效)。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。run 标签用 run6。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT7.md。
第二步:提交停止报告 P05_S4R7_REPORT_M2_STOP_G1.md 与本任务书(只提交这两个文件;信息末尾写 awaiting user review)。

## 1. 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U69:run5 的 G1、G2c 结果判为 HARNESS_INVALID(E7-32)。
  根因:run_m2b_all_r7.py:228–230 与 run_m2_r7.py:254–258 构造的环境中没有 S4FMM_NTH,
  注入器默认取第 1 次(inject_d003.cpp:38);历史运行器 matrix_r2.build_env(matrix_r2.py:98–109)会传 S4FMM_NTH。
  因此所有 nth > 1 的 s4malloc、plan、exec 点都注入在第 1 次。G1 94 行 MISMATCH(22 个 INVALID_NOT_REACHED 点 hit = 1;
  twice、inj_call = 2 的点 rc1 = 20、rc2 = 0,判为 SILENT_SWALLOW)全部由此造成;G1 的 204 行与 G2c 的 60 行 MATCH 同样无效。
  这些既不是 ENV_DRIFT,也不是 REGRESSION。run5 文件保留,不计入 M2。
  不受影响的部分:M1(请求 rnv1:M)、M2a(请求 plancall:K:M)、G2a(seam 请求自带序号)、CTRL_SEAM run5(4/4 CONTROL_OK,两遍)。
  检查缺口(规划者):dry-run 和 ENV_DRIFT 只比较类别,没有比较 rc 数值,也没有比较运行环境。
- U70:重跑整个 M2b(CTRL_SEAM → G2c → G1 → G2a),标签 run6,沿用 v2 + ADD 与 CTRL_SEAM 的已登记期望(不改)。
- U71:新增两道检查,写入编排脚本并在 dry-run 中执行:
  (a) 环境一致性:G1、G2c 每一行的环境由 matrix_r2.build_env(row) 生成(import,不复制),
      row 的 case、request、nth、mode、ng 取自 ADD;dry-run 逐行断言 nth > 1 的行环境中有 S4FMM_NTH 且值等于 ADD 的 nth,
      twice 路线的行有 S4FMM_TWICE=slab。G2a 的环境沿用 run_r4_matrix.py 的方式(同样经 build_env);若 G2a 历史上没有 nth,写明。
  (b) 数值对照:运行后,F 行的 rc、rc1(若历史表有 rc2,也比较 rc2)、hit 与历史表逐点比较:
      G1 用 registries/s4r3/RESULTS_R3.tsv,G2c 用 registries/s4r4/REGRESS_R4.tsv,G2a 用 registries/s4r4/RESULTS_R4.tsv。
      不一致的行列为 VALUE_DRIFT(类别相同但数值不同也要列出)。
- U72:ENV_DRIFT 与数值对照改为按组运行;缺少某组结果时,对该组报告 MISSING,不再整体拒绝。

## 2. 改脚本(testing/d003/stage_s4r7/,用 edit 或 write)
1. run_m2b_all_r7.py 与 run_m2_r7.py:G1、G2c、G2a 的环境改由 matrix_r2.build_env 生成(U71a);
   CTRL_SEAM 与 plancall 组的环境保持不变,但要在 dry-run 中打印每组一行示例环境。
2. dry-run 输出 "$EV/DRYRUN_R7_M2b_run6.txt",新增:
   - 环境一致性断言(U71a),失败的行计入无法解析;
   - 每组示例环境一行;
   - nth > 1 的行数:G1 210、G2c 16,与 ADD 一致。
3. 新脚本 check_values_vs_history_r7.py(U71b),以及 check_env_drift_m2b_r7.py 改为按组运行(U72)。
4. 先对 run5 的 G2c 运行一次 check_values_vs_history_r7.py,把输出存为证据。
   期望:nth > 1 的 16 行中至少有一部分出现 VALUE_DRIFT。这一步证明新检查能抓到本次缺陷;只读运行,不重新运行 S4。

## 3. 准备提交(提交之前不运行任何 run6 注入)
- 用 edit 追加 E7-32 与 U69–U72;用 edit 同步 STATE.md(M2b run5 判为 HARNESS_INVALID;run6 待运行)。
- 提交脚本、DRYRUN_run6、run5 的数值对照输出(复制到 registries/s4r7/,写 SHA256SUMS_M2b_run6prep.txt)、ERRATA、RULINGS、STATE。
- 提交信息:"P05-S4 R7 cont7 prep: S4FMM_NTH harness fix via matrix_r2.build_env (U69-U72), value check, dry-run OK; run5 G1/G2c HARNESS_INVALID. awaiting user review"。

## 4. 运行与 M2 里程碑
- 一条命令跑 run6;然后按组运行 check_values_vs_history_r7.py 与 check_env_drift_m2b_r7.py。只用 read 工具读汇总文件。
- 期望(INFLUENCED):CTRL_SEAM 4/4 CONTROL_OK;G2c 60 MATCH;
  G1 中 MATCH 254、NOT_REACHED_AS_EXPECTED 44、MISMATCH 0;G2a 50 MATCH;FLAKY 0;F 与 F2 五项相等;
  ENV_DRIFT 0;VALUE_DRIFT 0(或者逐行列出并给出解释)。
- 出现非 MATCH 或 FLAKY:按 U58 分类,写报告,停下。VALUE_DRIFT 不停下,但必须逐行列出。
- 报告 P05_S4R7_REPORT_M2_FINAL.md:M2a 加 M2b(run6)的合计;run5 作废的说明(U69);CTRL_SEAM;U65 的处理;
  22 个 INVALID 点的 hit;F 与 F2 差异;ENV_DRIFT 与 VALUE_DRIFT;E7-23..32;RP-R6d-1(只依据 M1);
  待用户裁决(P05-S3 签收按 U62;M3 按 U63);违规两张表。所有数字都要经 check_report_counts_r7.py 核对。
- 小型表复制到 registries/s4r7/,写 SHA256SUMS_M2b.txt;用 edit 更新 STATE;
  提交:"P05-S4 R7 milestone M2 (M2a+M2b run6) ... awaiting user review"。之后停下,不进入 M3。

## 5. 停止条件
沿用续 6 第 5 节,另外:
- dry-run 的环境一致性断言有任何失败;
- 第 2.4 条的 run5 数值对照对 nth > 1 的行没有报出任何 VALUE_DRIFT(说明新检查本身无效):停下并报告。
"未完成"与"不可行"必须区分。
