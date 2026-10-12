# P05-S4 R7 续 6(同一子轮次 R7,不是新阶段):修编排脚本 3 处 → 准备提交 → M2b → M2 里程碑

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收,不写签收文件。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S4R7_REPORT_CONT5_PART1.md、
checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT5.md(第 0 节操作规则 A–E 仍然有效;第 3–5 节由本任务书补充)。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。run 标签用 run5。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT6.md。

## 0. 操作规则
沿用续 5 第 0 节 A–E,另外:
- 给脚本传的输出路径一律写绝对路径 "$EV/…"(续 5 中 DRYRUN 落到仓库根,就是因为传了相对文件名)。
  编排脚本和核对脚本对输出路径做前缀检查:不在 $EV/ 下就拒绝运行。

## 1. 用户裁决(用 edit 追加到 ERRATA_7.txt 和 RULINGS.tsv)
- U64:U61 的 seam 驱动认可。seamF-F、fmmret-F 的驱动与 R4 逐字节相同;F2 的两个驱动没有历史对照,
  用 F 与 F2 的逐点比较覆盖。R4 库哈希的对照来源是 checkpoints/p05/registries/s4r4/LIBS_R4.tsv(已提交:seamF 8066a098…、fmmret-F fda3d99a…);
  check_drivers_vs_r4_r7.py 改为读取这个文件,结果应为 SAME。续 5 报告中 "NOT_IN_REGISTRY" 的说法写 E7-29 更正。
- U65:G2c-control 的预注册有误(E7-30)。v2 中 6 行的 mode 写成了 R4 的库名 addf、b2buf、fmmret。
  驱动只接受 FMM 模式,FMM_MODE=addf 会以 rc 2 退出;R4 的这三个对照实际是在各自的 seam 库上用 mode=fft 运行的
  (p05-s4r4/matrix_r4/control_runs/*.log:"DRIVER actual mode=fft");R7 也没有构建 addf、b2buf 库。
  处理:
  (a) G2c-control 这 6 行不运行,在结果中记为 NOT_RUN_REGISTRY_ERROR,不当作 MISMATCH,v2 不改;
  (b) 新增一份对照预注册 $EV/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv(运行前登记 sha256 和 UTC 时间,状态 INFLUENCED):
      驱动 seamF-F、seamF-F2、fmmret-F、fmmret-F2,mode=fft,NG 9,无注入,期望 CONTROL_OK(依据 CONTROL_R4.tsv 中 seamF、fmmret-F 两行);
      共 4 行。addf、b2buf 不补(库不在 M2 范围内)。
  (c) G1 自带的 CTL-* 对照(16 行)照常运行。
- U66:每组跑完后,必须逐点做 pass1 与 pass2 的比较(class、verdict、rc、rc1、rc2、hit),不一致的记为 FLAKY;
  F 与 F2 的配对必须 import compare_trees_r7.base_id,不得另写剥后缀规则。
- U67:M2b 的组顺序改为 CTRL_SEAM → G2c → G1 → G2a。停止规则不变:某组出现非 MATCH 或 FLAKY,该组两遍跑完后停下。

## 2. 改脚本(都在 testing/d003/stage_s4r7/,用 edit 或 write)
1. run_m2b_all_r7.py:
   - GROUP_ORDER = ("CTRL_SEAM", "G2c", "G1", "G2a");G2c-control 不进入运行,汇总里写 NOT_RUN_REGISTRY_ERROR(U65a)。
   - CTRL_SEAM 的行从新预注册读取;驱动按 (name, tree) 从 DRIVERS_R7_SEAM.tsv 选;判定用 J.classify(control=True)。
   - summarize:`from compare_trees_r7 import base_id`;为每组新增逐点的 pass1 与 pass2 比较(U66),
     列出 FLAKY 数;F 与 F2 比较 rc、rc1、rc2、hit、class 五项(不只是 rc)。
   - dry-run 增加三项检查:mode 必须属于驱动接受的 12 个模式;每个要用的驱动文件都存在且 sha256 一致;
     每个输出路径都在 $EV 下。G2c-control 在 dry-run 中报告为 EXCLUDED_U65(不计入无法解析)。
2. 新脚本 make_ctrl_seam_prereg_r7.py:生成 U65b 的 4 行预注册,并登记 sha256 和时间戳。
3. 新脚本 check_env_drift_m2b_r7.py:G2c 的历史 F 类别来自 registries/s4r4/REGRESS_R4.tsv(r4_observed);
   G1 来自 registries/s4r3/RESULTS_R3.tsv(F 行 observed_class);G2a 来自 registries/s4r4/RESULTS_R4.tsv(F 行 obs_pass1、obs_pass2)。
   用 base_id 去掉树后缀后,再去掉源 id 的 "-F" 后缀进行匹配;按 E7-21(h) 用 (point_id, group) 区分 G1 与 G2c 的共享 id。
   输出 points、env_drift、absent 三个计数,absent 必须为 0,否则退出非零。
4. check_drivers_vs_r4_r7.py:库哈希改为读 registries/s4r4/LIBS_R4.tsv(U64)。
5. check_prefix_r7.py:先运行(写 $EV/PREFIX_CHECK_R7_run5.txt)。
6. 运行 dry-run,输出 "$EV/DRYRUN_R7_M2b_run5b.txt"。要求:
   CTRL_SEAM 4、G2c 60、G1 298、G2a 50;G2c-control 6 EXCLUDED_U65;无法解析 0;模式非法 0;驱动 sha256 全部一致。

## 3. 准备提交
- 用 edit 追加 E7-29、E7-30 与 U64–U67;用 edit 把 STATE.md 同步(M2a 已提交;M2b 未运行;G2c-control 的处理按 U65)。
- 提交:续 5 第一部分报告、本任务书、全部新增或修改的脚本、ERRATA_7、RULINGS、STATE,
  以及复制到 registries/s4r7/ 的 DRIVERS_R7_SEAM.tsv、CTRL_SEAM 预注册(含 sha256 和时间戳)、DRYRUN_run5b、PREFIX_CHECK(写 SHA256SUMS_M2bprep.txt)。
- 提交信息:"P05-S4 R7 cont6 prep: orchestrator fixes (U65 control registry error, U66 pass/tree compare), CTRL_SEAM prereg, dry-run OK. awaiting user review"。
  **这次提交完成之前,不运行任何 M2b 注入。**

## 4. 运行与 M2 里程碑
- 一条命令:`sh testing/d003/safe_run.sh p05-s4r7 -- python3 -I -B testing/d003/stage_s4r7/run_m2b_all_r7.py run "$EV" run5`;
  然后运行 check_env_drift_m2b_r7.py。只用 read 工具读汇总文件。
- 期望(INFLUENCED):CTRL_SEAM 4 行 CONTROL_OK;其余全部 MATCH;FLAKY 0;F 与 F2 五项逐点相等;
  G1 中 22 个 INVALID 点的 hit 全为 0;ENV_DRIFT 0。
- 出现非 MATCH 或 FLAKY:按 U58 分类列表,停下,写报告,不改期望。
- 报告 P05_S4R7_REPORT_M2_FINAL.md:M2a 与 M2b 合计(按组、遍、verdict 计数);CTRL_SEAM;U65 的处理;
  22 个 INVALID 点;F 与 F2 差异;ENV_DRIFT;seam 驱动和库与 R4 的比较;E7-23..30;
  RP-R6d-1(只依据 M1,措辞不变);待用户裁决(P05-S3 签收按 U62;M3 按 U63);违规两张表。
  报告中所有数字都要经 check_report_counts_r7.py 核对(退出码 0)。
- 小型表复制到 registries/s4r7/,写 SHA256SUMS_M2b.txt;用 edit 更新 STATE。
- 提交:"P05-S4 R7 milestone M2 (M2a+M2b) ... awaiting user review"。然后停下,不进入 M3。

## 5. 停止条件
- 违反续 5 第 0 节 A(写入);
- dry-run 不满足第 2.6 条;
- 准备提交完成之前就运行了 M2b;
- 编排脚本以非零退出,或 ENV_DRIFT 检查的 absent 不为 0;
- 报告数字核对不通过。
"未完成"与"不可行"必须区分。
