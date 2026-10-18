# P05-S5 R5 报告（s5r5）：S5 最小修正子轮——检查器字符串缺陷的同类普查、R4 冻结数据重判、门禁前不预写结果

> 轮次：P05-S5 R5（S5 最小修正子轮；不是新阶段）。本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。
> 本报告正文写普查、重判、阳性对照与两张事件表；试跑核验见附录 A；门禁结果见附录 C（门禁后追加）。
> R5 不改、不重跑 gate_check_s5r4.py，也不重跑 S5R4 的 139 项正式断言（U386）；本轮以修正重判 + 新门禁处置 R4 的唯一失败项。

## 1 裁决入账（U386–U390，纯追加）

- RULINGS.tsv 纯追加 5 行，每行 5 个 tab 字段，前缀逐字节不变：154825 B → 156852 B，最大编号 U390；原文见 registries/RULINGS.tsv 与 evidence/p05-s5r5/RULINGS_APPEND_S5R5.tsv。
- U386：R4 唯一失败项（SHAKEDOWN_USED_STAGING_ROOTS）认定为检查器字符串缺陷；R5 不重跑 R4 断言，用 s5r5_recheck_staging.py 在 R4 冻结数据上重判；其余 138 项以 R4 正式门禁文件原文为准（sha 20bb6ad0…）。
- U387：R4 的 STATE 预投影结果予以更正；R5 起门禁前写的 STATE/草稿/报告正文只写“见附录 C”，不写任何门禁结果。
- U388：R5 门禁（gate_check_s5r5.py）不出现依据“是否试跑”或“输出路径是否为自身”的分支；试跑与正式运行只差根路径参数；门禁不读取任何门禁输出文件；试跑输出由门禁之外的 s5r5_shakedown_verify.py 核验，并在提交 (i) 之前完成。
- U389：就绪审计记录 STATE 字节/sha，并断言 STATE、草稿 v3、报告正文不含 U389 规定的三类门禁结果字样，且 STATE 的 S5R4 行与 S5R4 附录 C 的 FINAL_STATUS=INCOMPLETE 一致。
- U390：新写草稿 v3（未签收），v1/v2 不改；门禁结果只写“见附录 C；若 FINAL_STATUS≠COMPLETE 则草稿无效”。

## 2 勘误 ES5-15 / ES5-16（纯追加）

- ERRATA_S5.txt 先快照到 registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt（sha 8aec8fd5…，逐字节等于追加前前缀），再纯追加两条：13848 B → 15805 B，最后条目 ES5-16。
- ES5-15：gate_check_s5r4.py:997 用 “STAGING_MODE”+TAB+“yes” 匹配 RECORD 行的三段格式，且试跑走“自身输出”分支覆盖不到正式分支；影响 = R4 正式门禁唯一 1 项失败、FINAL_STATUS=INCOMPLETE；被检数据正确；处理 = U386/U388。
- ES5-16：R4 的 STATE 在门禁前写入结果，就绪审计只核字节/sha，导致内容失真；处理 = U387/U389/U390。

## 3 同类缺陷静态普查（CHECKER_SWEEP_S5R5.tsv）

- 对象 testing/d003/stage_s5r4/gate_check_s5r4.py（sha 829f2708…），AST 枚举全部 139 个 safe() 断言（含 8 个循环生成的检查名展开）。
- 机制分类：reads_record_line=1、self_branch=2、negative_in=6、other=131；汇总 SWEEP_ROWS=139、SELF_BRANCH_ROWS=2、VACUOUS=0。
- 两条 self_branch：SHAKEDOWN_GATE_FAILS_ZERO 与 SHAKEDOWN_USED_STAGING_ROOTS（R4 试跑只走了自身分支，正式分支在试跑中未被覆盖）；其中后者同时按字符串匹配 RECORD 行（record_format_ok=no）——这正是 ES5-15。
- 每条 reads_record_line / negative_in 断言都在 R4 冻结数据上用正确格式重算：6 条否定匹配重算为非空洞（STATE 标记与关键数字、CALIB SUMMARY、READINESS CONSISTENCY、草稿 v2 未签收声明、EV4 清单 941 文件覆盖）；1 条 RECORD 行匹配重算 = 修正逻辑成立（R4 原逻辑 not_staging）。
- 结论：VACUOUS=0，未发现第二个空洞通过；R4 的 138 项原文结论不因该普查而改变。

## 4 R4 冻结数据重判与阳性对照（RECHECK_STAGING_S5R5.tsv / POSCTRL_RECHECK_STAGING_S5R5.txt）

- 输入 p05-s5r4/shakedown/gate/GATE_S5R4_end.txt，sha256 3be9bed8…；S5R4 清单声明 shakedown/ 不在覆盖范围，另核对清单覆盖的 SHAKEDOWN_ITERATIONS_S5R4.txt 条目（d9637a25…）。
- 同一文件上重判 SHAKEDOWN_USED_STAGING_ROOTS：修正逻辑（逐列解析 RECORD 行，第 2 字段=STAGING_MODE、第 3 字段=value=yes）→ PASS；R4 原逻辑（子串匹配）→ not_staging，复现 R4 的失败，证明缺陷定位准确。
- 同文件另核对 EV_ROOT / P05_ROOT 为 shakedown 路径、失败数=0、检查器崩溃数=0（R4 试跑输出）。
- 重判阳性对照 4/4：真实副本→PASS；value=yes 改为 value=no→FAIL；删去 STAGING_MODE 行→FAIL；EV_ROOT 改为正式路径→FAIL。fixture 落盘在 evidence/p05-s5r5/posctrl/recheck_staging/。
- R5 门禁共 36 项检查；逐检查落盘变异阳性对照 36/36（POSCTRL_GATE_S5R5.txt：每个检查一份落盘变异，干净 staging 数据重算成立、篡改副本不成立；其中 HEAD/status 两项的 clean 夹具模拟提交 (i) 之后的分支，真实提交前分支由整轮 staging 试跑覆盖；POSCTRL_GATE 自指检查用合成两文件夹具，真实聚合值即本文件末行）。

## 5 就绪审计（U389；READINESS_S5R5.tsv）

- 就绪审计在最终 STATE、草稿 v3、本报告正文写完之后运行（顺序由链保证）；记录 STATE 字节数与 sha256、草稿 v3 与报告正文 sha256。
- 断言三处不含 U389 规定的门禁结果字样（正则原文见 READINESS_S5R5.tsv 的 # META 行与 s5r5_readiness.py），命中数为 0；并核对 STATE 的 S5R4 行与 S5R4 报告附录 C 的 FINAL_STATUS=INCOMPLETE 一致。
- 就绪项汇总见 READINESS_S5R5.tsv（GAP 计数、红点、开放项、待跑运行、一致性、make test/E2E/重判引用）；门禁逐项核对 GAP 与 STATE sha 一致。

## 6 两张事件表

### 6.1 表一：越界写入尝试

| 轮次 | 命令 | 目标 | 是否落盘 |
|---|---|---|---|
| s5r5 | awk -F'\t' ... | tee /dev/stderr | wc -l | tee 的目标 /dev/stderr（仓库外设备路径，非 $REPO 下） | 未落盘（tee 报 No such device or address；同一管道的 wc 仍输出 139） |

### 6.2 表二：工具与脚本事件

| # | 事件 | 处理/影响 |
|---|---|---|
| 1 | s5r5_checker_sweep.py 首跑 HARD_STOP：AST 只收集到 131/139 个断言（循环生成的 8 个检查名未展开） | 按 for 元组展开 % 格式的检查名，收集 139；复查无重复名 |
| 2 | s5r5_checker_sweep.py 二跑 HARD_STOP KeyError EVIDENCE_SUMS_COVERS_ALL：其 not in 出现在 os.walk 目录剪枝，被归为否定匹配但无重算器 | 补该断言在 R4 冻结数据上的重算（941 个文件逐一对照清单，结果 PASS_941_FILES），证明非空洞 |
| 3 | s5r5_checker_sweep.py 重跑时 VACUOUS=2：工作区 STATE 已是 R5 版本，否定匹配重算读不到 R4 冻结 STATE | 改为从冻结提交 1600ca1 用只读 git show 读 R4 STATE（sha 与 READINESS_S5R4 记录一致）；VACUOUS=0 |
| 4 | s5r5_recheck_staging.py formal 首跑 rc=1：输入文件不在 S5R4 SHA256SUMS.txt 中（清单声明 shakedown/ 被排除） | 改为两条诚实的清单对照：排除声明命中 + 清单覆盖的 SHAKEDOWN_ITERATIONS_S5R4.txt 条目 sha 匹配；rc=0 |
| 5 | s5r5_readiness.py 首跑 GAP=1：读 S5R4 报告的 FINAL_STATUS 时取到附录 B 的 PENDING_GATE（附录 C 的 INCOMPLETE 在其后） | 改为取最后一次出现（=附录 C 的 INCOMPLETE），GAP=0 |
| 6 | s5r5_gate_posctrl.py 首跑 32/36：4 个 clean 失败（MODIFIED 期望写成固定行数；NO_PYCACHE 把 2026-10-11 的历史 __pycache__ 计入；REGISTRY_EXPECTED 表头被当数据行；POSCTRL 自指 clean 的 --ev-root 覆盖被默认值优先） | 逐项修正：期望改为与行数无关；NO_PYCACHE 只计本轮开始后新建的 __pycache__（U388 口径）；解析跳过 rel_path 表头；clean 侧改用独立 ev 根 |
| 7 | s5r5_gate_posctrl.py 二跑 34/36：REGISTRY_EXPECTED 篡改误改表头；FROZEN 列表在 gate 脚本修改后未重建（stale） | 篡改只改数据行；重建 FROZEN 后 36/36 |
| 8 | gate_check_s5r5.py HEAD_R5_I_COMMITS_ONLY 期望原写为 ok_0_commits；提交 (i) 后会变成 ok_1_commits 而误 FAIL（若只在试跑验证就发现不了，属 ES5-15 同类覆盖缺陷） | 期望改为与提交数无关的 ok（只要求基线之后的提交主题都含 P05-S5 R5 (i)）；并在逐检查阳性对照里用 clean 夹具模拟提交 (i) 之后的分支 |
| 9 | s5r5_shakedown.py 首跑即 36/36，无 FAIL 需要归因 | 试跑门禁输出与 SHAKEDOWN_REHEARSAL.txt 落盘，由门禁之外的 s5r5_shakedown_verify.py 核验：36/36 项检查均出现且成立，失败数=0，检查器崩溃数=0 |

## 7 交付物与小表

- checkpoints/p05/registries/s5r5/：GATE_S5R5_start.txt、RULINGS_APPEND_S5R5.tsv、ERRATA_APPEND_S5R5.tsv、r4_final/ERRATA_S5_R4FINAL.txt、CHECKER_SWEEP_S5R5.tsv、RECHECK_STAGING_S5R5.tsv、POSCTRL_RECHECK_STAGING_S5R5.txt、POSCTRL_GATE_S5R5.txt、READINESS_S5R5.tsv、FROZEN_SCRIPTS_S5R5.tsv、REGISTRY_EXPECTED_S5R5.txt、TMP_SNAPSHOT_S5R5.tsv、SHA256SUMS.txt；门禁文件在门禁后追加并更新清单。
- 证据目录 checkpoints/p05/evidence/p05-s5r5/（SHA256SUMS.txt 覆盖非二进制证据；tmp/、gate/、shakedown/ 按轮次惯例不纳入清单）。

FINAL_STATUS=PENDING_GATE

（FINAL_STATUS=PENDING_GATE）本轮 P05-S5 R5 范围证据在附录写入之前已生成；最终状态与收尾句由门禁后追加的附录 C 给出。

## 附录 A（试跑核验；试跑后追加）

- 试跑（staging rehearsal）在提交 (i) 之前完成，使用同一份 gate_check_s5r5.py，只换根路径参数（--ev-root / --p05-root / --out 指向 $EV/shakedown/ 下的 staging 根）。
- 试跑门禁输出：evidence/p05-s5r5/shakedown/gate/GATE_S5R5_end.txt（sha256 161d616e2e91b7fc6c6d6b5531a1f052683a98f8fc8ba12b245add7876a27a26，36 项断言）。
- 门禁之外的 s5r5_shakedown_verify.py 核验结果：COUNTS COUNTS	pass=36	fail=0	total=36；失败数=0；检查器崩溃数=0；36 项检查全部出现且为通过；EV_ROOT/P05_ROOT 均为 shakedown 路径。
- 试跑期间出现的任何失败按四类归因（缺正式产物 / 检查器缺陷 / 链顺序 / 数据缺陷），检查器缺陷在提交 (i) 之前修好并用同一脚本 sha 重跑（迭代记录见 evidence/p05-s5r5/shakedown/ 与报告事件表）。
- 试跑不替代正式门禁：正式门禁在提交 (i) 之后只运行一次，结果见附录 C。


## 附录 C（门禁后追加；只追加，不改正文）

正式 end 门禁运行一次（冻结期规则：不修、不重跑、不放宽）。以下 COUNTS/FAILS/CHECK_CRASHED/FINAL_STATUS 全部由 s5r5_appendix_c.py 从门禁文件派生：

- 门禁文件：checkpoints/p05/evidence/p05-s5r5/gate/GATE_S5R5_end.txt（sha256 1fd857449a426651c8e03a1721bd606eb502ccf8a6374623066d65565be4458f）
- COUNTS pass=36 fail=0 total=36；失败数=0；检查器崩溃数=0
- 失败项：无
- 崩溃项：无

FINAL_STATUS=COMPLETE

本轮已完成 P05-S5 R5 范围，等待用户审核。

