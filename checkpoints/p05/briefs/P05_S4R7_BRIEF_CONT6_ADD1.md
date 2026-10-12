# P05-S4 R7 续 6 补充:U68(INVALID_NOT_REACHED 的判定规则)

先用 write 把本补充原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT6_ADD1.md。
续 6 任务书(P05_S4R7_BRIEF_CONT6.md)全部有效;本补充只增加 U68 并调整 dry-run 要求。

## 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U68:v2 中 G1 的期望标签 INVALID_NOT_REACHED(44 行 = 22 个点 × F、F2)按 E7-4 的原有定义判定,v2 不改:
  当且仅当 judge_d003.classify 返回 "INVALID",且 hit == 0,且 rc 不为 None(即原因是 "injection never reached"),
  verdict 记为 NOT_REACHED_AS_EXPECTED;其他任何情况记为 MISMATCH。
  NOT_REACHED_AS_EXPECTED 单独计数,不计入 MATCH,也不计入 REGRESSION(E7-4)。
  这是已登记期望的解释规则,不是改期望。写 E7-31,并说明根因:续 6 的 dry-run 没有要求检查期望标签(规划者遗漏)。
  若某点 hit == 1,按 U58 分类(先看同一构建的 F;只有 F2 为 1 才是 REGRESSION;F 也为 1 则是 ENV_DRIFT)。
- 组内停止规则:MATCH 与 NOT_REACHED_AS_EXPECTED 都不触发停止;MISMATCH 和 FLAKY 触发停止。

## 对续 6 第 2 节的调整
1. run_m2b_all_r7.py:
   - 新增函数 verdict_of(expected, cls, rc, hit),实现 U68;其他所有 verdict 都经由它判定,不得各处分别实现。
   - summarize 中 22 个 INVALID 点的 hit 分布按 U68 统计(F、F2 各自统计),并单列 NOT_REACHED_AS_EXPECTED 的计数。
2. dry-run 增加第四项检查:每一行的 expected_class 必须属于 judge_d003.CLASSES ∪ {INVALID_NOT_REACHED}
   (judge_d003.CLASSES 必须 import,不得手写),不属于的计入无法解析。
   dry-run 的报告中写明各期望标签的计数:应为 CONTROL_OK 16 + 4(CTRL_SEAM)、INVALID_NOT_REACHED 44、REPORTED_FAILURE 其余。
3. check_env_drift_m2b_r7.py:历史类别 INVALID 与 R7 的 F 行 verdict NOT_REACHED_AS_EXPECTED 视为一致;其他情况沿用原规则。

## 执行要求
- 本补充之后,按续 6 第 2–4 节一次做完:改脚本 → dry-run → 准备提交 → M2b → 里程碑。
  除续 6 第 5 节的停止条件外,不再因"需要确认"而中途停下。
  遇到任务书未覆盖的判定问题,在 ERRATA 中写明你的处理和理由;只要不改已登记的期望、不改判定器,就继续执行,由用户事后审核。
- M2 报告中的 G1 计数格式:MATCH x、NOT_REACHED_AS_EXPECTED 44(期望值)、MISMATCH 0、FLAKY 0。
