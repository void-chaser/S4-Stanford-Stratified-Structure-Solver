# P05-S4 R7 续 4(同一子轮次 R7,不是新阶段):M2b 一次跑完 + M2 里程碑

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S4R7_REPORT_M2.md、
checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT3.md(第 2–6 节仍然有效)、checkpoints/p05/registries/s4r7/ERRATA_7.txt 的 E7-20..E7-22。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。本段的 run 标签用 run5。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT4.md。

## 0. 工作方式(本段的核心要求)
- 本段只允许两类命令:
  (a) 经 `sh testing/d003/safe_run.sh p05-s4r7 -- python3 -I -B testing/d003/stage_s4r7/<已提交的脚本> <参数>` 运行脚本;
  (b) 只读查看:read、grep、glob 工具,以及 `git log`、`git status`、`git show`、`ls -d`、`test -e`。
- 不写临时 shell 管道,不写 `python3 -c`,不写 `sed`、`awk`、`sort` 的重定向,任何路径都不用 `> /tmp`。
  需要核对什么,就把核对写成 stage_s4r7/ 下的脚本,先提交,再经 safe_run 运行。
- 出现第一次违反本节的情况就停下,写报告,不再继续。续 3 中这条规则被违反了 5 次却没有停下,本段不得重复。
- 执行者不逐组手工核对。结论只依据编排脚本输出的汇总表和核对脚本的退出码。

## 1. 用户裁决(追加到 ERRATA_7.txt 和 RULINGS.tsv;原有行不改)
- U54:M2b 开工。依据 safe_run.log 的时间戳:G3 一遍 72 行约 16 秒,所以 M2b 约 830 次运行只需几分钟;
  续 3 中"超出预算"的限制来自执行者的手工核对方式,不是运行时间。M2b 由一个编排脚本一次运行完。
- U55:续 3 违反第 0 节五次(两次写 /tmp、一次 sed -i /dev/null、多次 python3 -c),却没有按第 6 节停下。
  结果不受影响,这次不追溯;从本段起按第 0 节执行。写 E7-23。
- U56:STATE.md 在 M2a 提交时没有更新(最后修改在 db92648),违反 AGENTS 第 7 节。写 E7-24,本段补上。
- U57:ERRATA_7 只追加不修改,所以较早的清单(SHA256SUMS.txt、SHA256SUMS_M2pre.txt)对它必然校验失败。
  今后对只追加的文件改用前缀核对:清单中记录的 sha256 应等于当前文件前 N 字节的 sha256(N 为当时的文件长度)。
  新脚本 check_prefix_r7.py 对 ERRATA_7、RULINGS.tsv 做这项核对,结果写 E7-25,旧清单不改。
- U58:G1 的 22 个 INVALID 点:期望保持 INVALID(hit 0)。如果某点在 F2 上 hit = 1,先看同一 R7 构建的 F 上该点的 hit:
  F 也是 1,记为 ENV_DRIFT;只有 F2 是 1,记为 REGRESSION。都不改期望,全部单独列表。

## 2. 准备(运行 M2b 之前,一次提交)
1. 新编排脚本 testing/d003/stage_s4r7/run_m2b_all_r7.py:
   - 依次运行 G2c 与 G2c-control → G1 → G2a,每组 pass1 与 pass2,tree F 与 F2;内部调用 run_m2_r7.py 的同一套逻辑
     (导入,或用 subprocess 调用 `run_m2_r7.py run`),不复制判定代码。
   - 每组跑完后立即调用已有的比较脚本(compare_passes_r7.py、compare_trees_r7.py 的 v2 配对规则、
     check_env_drift 的同类检查(新文件 check_env_drift_m2b_r7.py,来源为各组源表的 F 行)),
     并生成 $EV/REGRESS_R7_M2b.tsv 与 $EV/M2B_SUMMARY_R7.txt。
   - 汇总只给计数:每组每遍的 MATCH、非 MATCH、FLAKY、F 与 F2 rc 不等的点数、ENV_DRIFT、REGRESSION、absent、
     22 个 INVALID 点的 hit 分布;非 MATCH 的点逐行列在汇总文件末尾,最多 50 行,超出部分写入单独文件。
   - 某组出现非 MATCH 时,该组两遍照常跑完,然后停止,不进入下一组,退出码非零(U58 的分类先记录,不当场裁决)。
   - 输出目录已存在时拒绝运行(U17)。
   - `--dry-run`:只解析与核对驱动和库的 sha256,不运行 S4。
2. 新脚本 check_prefix_r7.py(U57)、check_report_counts_r7.py(从汇总表读数,与报告中的数字比对;报告写完后运行)。
3. 运行 `run_m2b_all_r7.py --dry-run`,输出 $EV/DRYRUN_R7_M2b_run5.txt;要求每组行数与 v2 + ADD 一致,无法解析 0,sha256 全部一致。
4. ERRATA_7 追加 E7-23..E7-25;RULINGS 追加 U54–U58;STATE.md 补到 M2a 已完成的真实状态。
5. 提交:"P05-S4 R7 cont4 prep: M2b orchestrator and checks committed, dry-run OK; rulings U54-U58; STATE synced. awaiting user review"。
   **这次提交之前不运行任何 M2b 注入。**

## 3. 运行
- 一条命令:`sh testing/d003/safe_run.sh p05-s4r7 -- python3 -I -B testing/d003/stage_s4r7/run_m2b_all_r7.py run run5 <EV>`。
- 运行结束后只读取 M2B_SUMMARY_R7.txt 与 REGRESS_R7_M2b.tsv(read 工具,用 offset/limit 读取)。
- 期望(INFLUENCED;与 v2、ADD 中的期望一致):全部 MATCH;22 个 INVALID 点的 hit 全为 0;F 与 F2 逐点 rc 相等;ENV_DRIFT 0。

## 4. M2 里程碑提交
- 小型表(各组 RESULTS、TREES v2、REGRESS_R7_M2b、REGRESS_R7_M2(M2a 加 M2b,由脚本合并)、ENV_DRIFT_M2b、
  M2B_SUMMARY、DRYRUN、PREFIX 核对)复制到 registries/s4r7/,写 SHA256SUMS_M2b.txt 并核对。
- 报告 P05_S4R7_REPORT_M2_FINAL.md(新文件,M2 报告与 M2_PART 报告不改):
  M2a 与 M2b 的合计表(每组 × 遍的 verdict 计数);22 个 INVALID 点的 hit;F 与 F2 的 rc 差异;ENV_DRIFT;E7-23..25;
  RP-R6d-1 的状态(只依据 M1,措辞不变);需要用户裁决的事项(至少:P05-S3 是否签收(U47);M3 是否开工);违规两张表。
  报告中每个数字都必须由 check_report_counts_r7.py 核对通过(退出码 0),核对输出存为证据。
  结尾写 "本轮未完成 R7 范围(M2 已完成/未完成),等待用户审核",附 git log -3 与 git status --short。
- 更新 STATE.md(一页以内,写明 M2 的状态)。提交信息为 "P05-S4 R7 milestone M2 (M2a+M2b) ... awaiting user review"。
  提交之后停下,不进入 M3。

## 5. 停止条件
- 违反第 0 节(出现一次就停);
- dry-run 不通过;
- 第 2 节的提交完成之前就运行了 M2b;
- 编排脚本以非零退出(某组出现非 MATCH):写报告,列出 U58 的分类,等待裁决;
- 报告的数字核对不通过。
"未完成"与"不可行"必须区分。
