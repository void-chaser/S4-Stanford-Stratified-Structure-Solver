# P05-S4 R7 续 8 补充 1:接受 ADD_v3,完成准备并跑 run7

先用 write 把本补充原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT8_ADD1.md。续 8 的其他条款仍然有效。

## 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U77:接受 ADD_v3 与 ADD_v2 的 92 格差异:G2c route 30、G2c twice_env 30、G1 request 16、G1 route 16、G1 nth 0。
  续 8 第 2.1 条的期望写错了(规划者):"G1 nth 16" 不对,因为 v2 中对照行的 nth 本来就是 "-";
  并且漏了 "G1 route 16"(v2 把对照行的 route 误填成 mode 名,v3 改为 control)。
  另外,续 8 写的 "30 行" 实际指 15 个点 × 2 棵树,每行改 2 格。写 E7-35。
- U78:停止规则调整(只适用于登记表差异):如果 point_id、tree、group、expected_class、inj_call 五个关键列的差异为 0,
  环境列的差异计数与任务书不同时,不停下:把实际计数和每一处偏差的来源写进 ERRATA,然后继续。
  关键列只要有 1 处差异,仍然停下。

## 继续执行(一次完成,除续 7、续 8 的停止条件外不停下)
1. 复制 ADD_v3 与 ADD_V3_VS_V2_DIFF.txt 到 registries/s4r7/,附 sha256 与 UTC 时间;
   复制时遵守 U75c(目标已存在时比对 sha256)。
2. 实现 U75b 的独立环境断言(新函数 expected_env_from_history(group, point_id, tree),只读源表与历史规则,不读 ADD):
   - G1:注入行的 category、NTH、mode 由 point_id 解析;request = {malloc: s4malloc, plan: plan, exec: exec}[category];
     route = point_id 第 2 段;case = ("t4/" if twice else "r3/") + 源 id;
     S4FMM_TWICE=slab 当且仅当 twice;S4FMM_NTH = NTH;
     对照行(CTL-*)不设 S4FMM_INJECT,也不设 S4FMM_NTH。
   - G2c:与 G1 的注入行规则相同(run_r4_regress.py:74–81)。
   - G2a:request 取 registries/s4r4/RESULTS_R4.tsv 的 request 列;不设 S4FMM_TWICE;
     其余与 run_r4_matrix.py 的 build_env 调用一致(写清引用的行号)。
   - CTRL_SEAM:FMM_MODE=fft,S4FMM_NG=9,不设 S4FMM_INJECT、S4FMM_NTH、S4FMM_TWICE。
   dry-run 对每一行断言 "实际传给驱动的环境 == expected_env_from_history",失败计入无法解析。
3. dry-run 输出 "$EV/DRYRUN_R7_M2b_run7.txt":无法解析 0;独立断言失败 0;
   示例环境至少包括 G2c 的一个 twice 点(应有 S4FMM_TWICE=slab)和 G1 的一个对照行(应没有 S4FMM_INJECT)。
4. 用 edit 追加 E7-35 与 U77、U78,同步 STATE;提交准备(脚本、ADD_v3 副本、差异文件、DRYRUN_run7、ERRATA、RULINGS、STATE)。
   提交信息:"P05-S4 R7 cont8 prep complete: ADD v3 accepted (U77), independent env assertion, dry-run OK. awaiting user review"。
5. 提交之后运行 run7,然后按续 8 第 3 节完成数值对照、ENV_DRIFT、M2 最终报告与里程碑提交,之后停下,不进入 M3。

期望不变(INFLUENCED):CTRL_SEAM 4/4 CONTROL_OK;G2c 60 MATCH;G1 中 MATCH 254(238 注入 + 16 对照)、
NOT_REACHED_AS_EXPECTED 44、MISMATCH 0;G2a 50 MATCH;FLAKY 0;F 与 F2 五项相等;ENV_DRIFT 0;VALUE_DRIFT 0(或者逐行列出并解释)。
