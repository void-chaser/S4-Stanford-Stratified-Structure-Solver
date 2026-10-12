# P05-S4 R7 续 5(同一子轮次 R7,不是新阶段):收尾续 4 + seam 驱动 + M2b + M2 里程碑

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收(包括 P05-S3;不得写签收文件)。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S4R7_REPORT_M2.md、
checkpoints/p05/P05_S4R7_REPORT_CONT4_STOP2.md、checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT4.md(第 1–4 节仍然有效,第 0 节和第 5 节由本任务书取代)、
checkpoints/p05/registries/s4r7/ERRATA_7.txt 的 E7-20 至 E7-26。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。run 标签用 run5。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT5.md。

## 0. 操作规则(取代续 4 第 0 节)
A. 写入(任何会生成或修改文件的操作):
   - 仓库文件(报告、ERRATA、RULINGS、STATE、脚本)只用 edit 或 write 工具;
   - 其他写入一律经 `sh testing/d003/safe_run.sh p05-s4r7 -- <命令>`,写入目标只能在 $EV/、testing/d003/stage_s4r7/、checkpoints/p05/ 下;
   - 不用 `>`、`>>`、`tee`、`sed -i`、`printf >>` 写任何文件(safe_run 调用的脚本内部除外);任何路径都不写 /tmp,也不写 /dev/null。
B. 只读 bash 白名单(可以不经 safe_run,可以接 `| head`、`| tail` 截断输出):
   git status / log / show / diff / rev-parse / ls-files;ls;ls -d;test -e;sha256sum(不带重定向);wc;cat 小文件。
   不在白名单里的只读需求,用 read、grep、glob 工具。
C. git add 与 git commit 是本任务书要求的操作,允许使用(只提交 checkpoints/p05/ 与 testing/d003/stage_s4r7/)。
D. 只有违反 A(写入)时才立即停下;违反 B 的只读事件记入表二,不停下。
E. 核对类结论只依据已提交脚本的输出和退出码;不在 shell 里手工拼核对。

## 1. 用户裁决(追加到 ERRATA_7.txt 和 RULINGS.tsv;用 edit 工具,原有行不改)
- U59:续 4 第 0 节把 git rev-parse、wc 等只读命令和 git add/commit 都排除在外,无法执行(规划者错误)。
  续 4 第一次停止的根因记为任务书问题;由本任务书第 0 节取代。写 E7-27。
- U60:续 4 中用 `printf >> RULINGS.tsv` 追加的 U54–U58 五行,内容接受为有效裁决,不重写;写入方式违规,记入表二(E7-28)。
- U61:E7-26(G2a 缺 seam 驱动)确认。按 run_r4_matrix.py:55–70 的 library_for 和 run_r4_seam.sh 的 link_driver
  (testing/d003/src/driver_d003.cpp + inject_d003.cpp,LIBFLAGS 与 run_r4_seam.sh:38 相同)链接 4 个驱动:
  seamF-F、seamF-F2、fmmret-F、fmmret-F2,分别链接 build_r7/seam_plain 下对应的库。
  seamAB-B、seamAB-A 不需要(M2 只运行 F 行)。G2a 留在 M2b。
- U62:"全部同意"中的 P05-S3 签收不由执行者落实。签收由用户在 M2 里程碑之后在对话中给出,规划者另行记录。
  本段不写签收文件,也不在 STATE 中写 "S3 已签收"。
- U63:M3 在 M2 里程碑提交后开工(另发任务书)。

## 2. 第一步:收尾续 4(一次提交)
1. 用 edit 追加 E7-27、E7-28 与 U59–U63。
2. 提交续 4 的留存文件(CONT4 任务书、两份 STOP 报告、ERRATA_7、RULINGS),以及本任务书 CONT5。
   提交信息:"P05-S4 R7 cont4 stop records and rulings U54-U63 (U54-U58 content accepted, method violation recorded); no run. awaiting user review"。

## 3. 准备(一次提交,提交之前不运行任何 M2b 注入)
1. 新脚本 testing/d003/stage_s4r7/link_seam_drivers_r7.sh:按 U61 链接 4 个驱动,输出到 $EV/drivers_r7/seam-<lib>-<tree>-plain/,
   写 $EV/DRIVERS_R7_SEAM.tsv(驱动名、树、库 sha256、驱动 sha256、编译命令)。
   附加核对:F 的 seamF 与 fmmret 驱动的 sha256 与 registries/s4r4/DRIVERS.tsv 中 seamF(e5c8c4c0…)、fmmret-F(43d2d6a5…)比较,
   结果 SAME 或 DIFFERENT 只记录;DIFFERENT 时不停下,因为库已经逐字节相同,但要在 ERRATA 中说明。
2. 新编排脚本 run_m2b_all_r7.py(与续 4 第 2.1 节要求相同):G2c 与 G2c-control → G1 → G2a;
   G2a 按 library_for 选择 DRIVERS_R7_SEAM 中的驱动;每组两遍、F 与 F2;每组跑完后做 pass 比较、tree 比较(v2 配对)、
   ENV_DRIFT 检查(新文件 check_env_drift_m2b_r7.py);输出 REGRESS_R7_M2b.tsv 与 M2B_SUMMARY_R7.txt;
   某组出现非 MATCH 时,该组两遍跑完后停下,退出码非零;U58 的分类单列;输出目录已存在就拒绝;`--dry-run` 只做解析与 sha256 核对。
3. 新脚本 check_prefix_r7.py(U57,对 ERRATA_7 与 RULINGS.tsv,输出 PREFIX_CHECK_R7_run5.txt)、
   check_report_counts_r7.py(报告写完后运行)、sync_state_r7.py 可选(STATE 也可以直接用 edit 改)。
4. 运行 dry-run,输出 $EV/DRYRUN_R7_M2b_run5.txt。要求:每组行数与 v2 + ADD 一致(G2c 60、G2c-control 6、G1 298、G2a 50),
   无法解析 0,驱动与库的 sha256 全部一致。
5. 用 edit 把 STATE.md 同步到真实状态(U56):M2a 已完成并提交(6319a3c、733d588),M2b 未运行,G2a 驱动按 U61 补齐。
6. 提交:"P05-S4 R7 cont5 prep: seam drivers (U61), M2b orchestrator, checks, dry-run OK, STATE synced. awaiting user review"。

## 4. 运行与 M2 里程碑
与续 4 第 3、4 节相同:
- 一条命令运行编排脚本(run5);只读汇总表。
- 期望(INFLUENCED):全部 MATCH;G1 中 22 个 INVALID 点的 hit 全为 0;F 与 F2 逐点 rc 相等;ENV_DRIFT 0。
- 报告 P05_S4R7_REPORT_M2_FINAL.md:M2a 与 M2b 合计;22 个 INVALID 点;seam 驱动与 R4 的比较;E7-23..28;
  RP-R6d-1(只依据 M1,措辞不变);待用户裁决(P05-S3 签收按 U62 由用户给出;M3 开工按 U63);违规两张表。
  报告中所有数字都要经 check_report_counts_r7.py 核对(退出码 0)。
- 小型表复制到 registries/s4r7/,写 SHA256SUMS_M2b.txt 并核对;更新 STATE。
- 提交:"P05-S4 R7 milestone M2 (M2a+M2b) ... awaiting user review"。之后停下,不进入 M3。

## 5. 停止条件
- 违反第 0 节 A(写入);
- dry-run 不通过,或驱动、库的 sha256 不一致;
- 第 3 节的提交完成之前就运行了 M2b;
- 编排脚本以非零退出:写报告,列出 U58 分类,等待裁决;
- 报告数字核对不通过。
违反第 0 节 B 只记录,不停下。"未完成"与"不可行"必须区分。
