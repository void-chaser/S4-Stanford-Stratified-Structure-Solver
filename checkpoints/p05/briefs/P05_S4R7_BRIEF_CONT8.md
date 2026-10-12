# P05-S4 R7 续 8(同一子轮次 R7,不是新阶段):修对照行与 G2c 路线 → run7 重跑整个 M2b → M2 里程碑

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收,不写签收文件。不修改 S4/、判定器,以及 testing/d003/ 下的历史装置(只导入)。
先读 AGENTS.md、STATE.md、checkpoints/p05/P05_S4R7_REPORT_M2_RUN6_STOP.md、
P05_S4R7_BRIEF_CONT7.md(操作规则与 U64–U72 仍然有效)。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。run 标签用 run7。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT8.md。
第二步:提交 run6 停止报告、run_m2b_all_r7.py 中未提交的改动(汇总文件名带 run 标签),以及本任务书。
提交信息:"P05-S4 R7 run6 stop report (G1 CTL harness error) and cont8 brief. awaiting user review"。

## 1. 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U73:run6 中 G1 的 16 行 CTL-* MISMATCH 判为 HARNESS_INVALID(E7-33)。
  根因:对照行的 request "none" 经 matrix_r2.build_env 变成 S4FMM_INJECT=none;历史上的 run_r3_sweep.py:129–133 对照行 request 为 "-"。
  run5 的 CTL 行两遍 16/16 CONTROL_OK(run5 的环境不是用 build_env 生成的),所以这个错误只出现在 run6。
  run6 的 G1 注入行(238 MATCH + 44 NOT_REACHED_AS_EXPECTED,两遍)作为辅助证据保留,但 M2 的正式结论以 run7 为准。
- U74:G2c 的路线登记错误(E7-34)。REGRESS_R4.tsv 的 30 个 F 点中有 15 个是 M-twice-*;
  历史运行器 run_r4_regress.py:76–79 用 route = R3.route_of(pid),对 twice 用 case "t4/…",并经 build_env 设 S4FMM_TWICE=slab。
  但 ADD 表把 G2c 的 60 行全部写成 route=once、twice_env=-(make_prereg_m2_add_r7.py:17 的注释 "REGRESS_R4 rows are once-route points" 是错误的)。
  因此 run5、run6 的 G2c twice 点都没有设 TWICE。规划者只读核对:run6 G2c 的 F 行 rc/rc1/rc2/hit 与 REGRESS_R4 30/30 相同
  (inj_call 都是 1,注入在第 1 次调用,TWICE 只影响两次调用之间),但运行环境与历史不同,不能作为证据。
  U71a 没有发现这个问题,因为它的期望值取自 ADD 本身(检查缺口:环境断言必须用历史规则独立推导,不能读 ADD)。
  ERRATA 中 E7-32 之后关于 "G2c nth > 1 是 once 路线" 的推测,同样是被这张错误的表误导的,一并更正。
- U75:修复方式(不改 v2,不改任何期望值;ADD 只修正环境列,作为新文件):
  (a) 新文件 REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv,由修改后的生成器(新脚本 make_prereg_m2_add_v3_r7.py)生成:
      G1、G2c 的 route 一律用 R3.route_of(point_id) 推导(import run_r3_sweep 中的函数,或复制其逻辑并在报告中给出逐字对照);
      twice_env 由 route 推导;对照行(G1 CTL-*)的 request 改为 "-"、nth 改为 "-";
      point_id、tree、group、expected_class、inj_call 与 v2/ADD_v2 逐字相同,脚本逐行比对,不同就拒绝写文件。
      ADD_v2 保留,标为被 v3 取代(只取代环境列)。
  (b) U71a 的环境断言改为独立推导:期望的 case、S4FMM_TWICE、S4FMM_NTH、S4FMM_INJECT 由历史规则从 point_id 和源表计算,
      不读 ADD;对照行断言环境中没有 S4FMM_INJECT。
  (c) 复制脚本:目标文件已存在时,只有 sha256 与源文件一致才算成功,并把 "already present, sha256 equal" 记录进复制日志;不一致就拒绝。
- U76:用 run7 重跑整个 M2b(CTRL_SEAM → G2c → G1 → G2a)。

## 2. 准备(一次提交;提交之前不运行任何 run7 注入)
1. 生成 ADD_v3,并输出它与 ADD_v2 逐列的差异计数:
   期望(INFLUENCED):G2c 有 15 × 2 = 30 行的 route/twice_env 改变;G1 有 16 行对照行的 request/nth 改变;其他列 0 处改变。
   与此不符就停下报告。
2. dry-run 输出 "$EV/DRYRUN_R7_M2b_run7.txt":独立推导的环境断言(U75b)0 失败;
   每组示例环境一行,其中必须包括 G2c 的一个 twice 点(应有 S4FMM_TWICE=slab)和 G1 的一个对照行(应没有 S4FMM_INJECT)。
3. 用 edit 追加 E7-33、E7-34 与 U73–U76;用 edit 同步 STATE.md。
4. 提交生成器、ADD_v3(复制到 registries/s4r7/,附 sha256 与时间戳)、差异计数、DRYRUN_run7、ERRATA、RULINGS、STATE。
   提交信息:"P05-S4 R7 cont8 prep: ADD v3 (G2c twice route, CTL request '-'), independent env assertion, dry-run OK. awaiting user review"。

## 3. 运行与 M2 里程碑
- 一条命令跑 run7;然后按组运行 check_values_vs_history_r7.py(run7)与 check_env_drift_m2b_r7.py(run7)。只用 read 工具读汇总文件。
- 期望(INFLUENCED):CTRL_SEAM 4/4 CONTROL_OK;G2c 60 MATCH;G1 中 MATCH 238 + 对照 16 CONTROL_OK(计入 MATCH,共 254)、
  NOT_REACHED_AS_EXPECTED 44、MISMATCH 0;G2a 50 MATCH;FLAKY 0;F 与 F2 五项相等;ENV_DRIFT 0;VALUE_DRIFT 0(或者逐行列出并解释)。
- 出现非 MATCH 或 FLAKY:按 U58 分类,写报告,停下。
- 报告 P05_S4R7_REPORT_M2_FINAL.md:M2a 加 M2b(run7)的合计;run5、run6 作废的说明(U69、U73、U74);CTRL_SEAM;U65;
  22 个 INVALID 点的 hit;F 与 F2 差异;ENV_DRIFT 与 VALUE_DRIFT;G2a 与 R4 的比较;E7-23..34;
  RP-R6d-1(只依据 M1);待用户裁决(P05-S3 签收按 U62;M3 按 U63);违规两张表。所有数字都要经 check_report_counts_r7.py 核对。
- 小型表复制到 registries/s4r7/,写 SHA256SUMS_M2b_run7.txt;用 edit 更新 STATE;
  提交:"P05-S4 R7 milestone M2 (M2a + M2b run7) ... awaiting user review"。之后停下,不进入 M3。

## 4. 停止条件
沿用续 7,另外:
- ADD_v3 与 ADD_v2 的差异计数不符合第 2.1 条;
- 独立推导的环境断言有任何失败;
- 复制时目标已存在且 sha256 不一致。
"未完成"与"不可行"必须区分。
