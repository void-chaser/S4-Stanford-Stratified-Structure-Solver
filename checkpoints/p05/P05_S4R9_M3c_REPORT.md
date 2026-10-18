# P05-S4 R9 M3c 报告（轮次标识 r9m3c）——M3b 偏差/勘误落账 + M3b 正式结果独立只读复核 + P05-S3/P05-S4 签收就绪审计

> 规则依据仓库根 AGENTS.md 与本轮任务书（checkpoints/p05/briefs/P05_S4R9_BRIEF_M3c.md）。本轮全程只读复核：不跑 make/make test、不跑 E2E、不跑 d003 矩阵、不跑 gdb、不构建。本轮不改 S4/、判定器与历史装置，不修改任何已提交文件（RULINGS.tsv 与 ERRATA_9.txt 只追加）。
> 本报告不宣布任何阶段完成或签收；签收只由用户在对话中给出。

## 1. 门禁

开工门禁逐项核对（GATE_R9M3C_start.txt，46 项断言，PASS=46 FAILS=0）：

| 项 | 期望 | 实际 |
|---|---|---|
| HEAD | 01fd3c0e4cf436aef5780486c8b8327c25849713 | 一致 |
| HEAD:S4（F4） | 589e15eb11fcb04e031b524f25a443e7921946cf | 一致 |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb | 一致 |
| git status --short（开工） | 仅本轮允许文件 | 22 行，全部在允许清单内 |
| /tmp 顶层快照 | 条目数与 sha256 写入 GATE_R9M3C_start.txt | 条目数 0，sha e3b0c442…b855 |
| RULINGS.tsv | 139934 字节，sha 4bcebe60…631a，最大 U342 | 一致 |
| ERRATA_9.txt | 51809 字节，sha 2d32e4f1…2716，最后 E9-57，共 57 条 | 一致 |
| STATE.md | 5534 字节，sha a6aa2c49…d5b2 | 一致 |
| registries/s4r9/M3b/SHA256SUMS.txt | sha 4a802924…dc59，18 项全部 OK | 一致 |
| m3b 证据目录 SHA256SUMS.txt | sha da6ae764…e118，全部 OK | 一致 |
| M3b 报告 | sha 788417e8…1467 | 一致 |
| 历史清单 | 全部 OK，项数由脚本数出 | s3r5 14 / M0 25 / M1 28 / M1R2 33 / M1R3 26 / M1R4 11 / M2 14 / M2b 13 / M2c 11 / M3a 17 / M3b 18 |
| M3b 预注册 sha256 | 9e3895bb…31da | 一致 |

正式 start 前缀复核：GATE_R9M3C_start_RECHECK.txt。试跑与正式 end 门禁结果见附录 B。

## 2. L 项复核（AUDIT_R9M3B_R9M3C.tsv）

规划者 L-1…L-6 全部复核为“属实”（6/6）。行号全部由脚本从原文件算出，未照抄任务书行号：

| 项 | 结论 | 脚本算出的关键事实 |
|---|---|---|
| L-1 | 属实 | 报告 L189 的 make test 句写“存在 FAIL”；8 行 reconcile 最后一列都是 OK；closeout L82 的 recon_bad 用 r[6]（实际 ok 列下标为 7，r[6] 是 skipped 期望列）；REPORT_CHECK_R9M3B.txt 为 FAILS=0 |
| L-2 | 属实 | gate_check_r9m3b_v3.py L670 写死 sha_sums_r9m3b.py；FROZEN 清单为 sha_sums_r9m3b_v2.py |
| L-3 | 属实 | 报告 §9 表格在 4 行后 L108 出现空行、§12.2 表格在 7 行后 L141 出现空行（即第 5 行/第 8 行之前） |
| L-4 | 属实 | 报告 §13 第 5 项 L152 问是否另立 M3a 门禁更正件；end 门禁缺陷只在附录 B（L205）；对话摘要不在仓库内 |
| L-5 | 属实 | LEDGER_CHECK L3 写“待用户裁决是否关闭”；L4 判 RP-R8-M2c-1b 在 STATE 无行；U304 已关闭；STATE L45 用合并行 RP-R8-M2c-1/1b |
| L-6 | 属实 | lua_repl 仅 cf/fft/kt/vl 四个注入点；jones/nv/exp 无 REPL 点（py 与 lua_batch 有对应族） |

## 3. 裁决与勘误

- 裁决追加：append_rulings_r9m3c.py 以“旧文件 + 新行”追加 U343–U350（5 列，前缀 sha 断言通过）。RULINGS.tsv 139934 → 142281 字节，sha 4bcebe60… → 443d8a38…，最大 U350。
- 勘误追加：append_errata_r9m3c.py 追加 E9-58–E9-66（L-1…L-6 各一条 + U346/U347/U348 各一条；写入前断言 L 项全属实、U346/U347/U348 事实成立）。ERRATA_9.txt 51809 → 56754 字节，sha 2d32e4f1… → 9bd2933d…，共 66 条，最后 E9-66。
- M3b 报告、M3b registries、M3b 门禁文件均未修改，由 end 门禁按前缀校验。

## 4. M3b 独立只读复核（S-B，新实现，未 import/调用任何 r9m3b 脚本）

- rejudge_e2e_r9m3c.py 直接读 m3b/runs/pass1 与 pass2 的 42 个逐点 JSON，按 PREREG_E2E_R9M3B.tsv 与 CALIB_E2E_R9M3B.tsv 独立重算类别与逐点事实（命中数、HIT 序号与 size、可见错误文本、同对象/新对象/新进程重试的最大相对误差、rc）。
- 结果：REJUDGE 42 点，DIFFS=0；类别 CONTROL_OK=17, E2E_OK=25，其他类别 none。逐点明细 REJUDGE_E2E_R9M3C.tsv，比对 REJUDGE_COMPARE_R9M3C.txt。
- 阳性对照：posctrl_rejudge_r9m3c.py 落盘 16 个篡改副本（三前端各覆盖 API_SILENT、RETRY_DIFF、HIT_OFF_TARGET、INVALID、CONTROL_BAD，加 FLAKY 1 例两个 run 文件），调用正式脚本判出，OVERALL_POSITIVE_CONTROL: PASS (16/16)。
- 复验：reverify_sums_r9m3c.py 对 m3b 证据清单 43 项与 registries/s4r9/M3b 清单 18 项逐项只读复验全部 OK，并按列名重算 8 行 reconcile 的 ok 列全部 OK；REVERIFY FAILS=0。
- 结论：独立复核与 M3b 判定完全一致，U345 的关闭条件成立。

## 5. 签收就绪审计（READINESS_P05_S3S4_R9M3C.tsv）

三组判据共 26 行：MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=7。

- PROJECT_ROADMAP.md 的 P05 验收三条：每个受影响的 prepare/execute 点有正负对照（MET）；失败后模式/缓存不安装（CLOSED_BY_RULING，U29）；Python/Lua 可见失败、恢复重试正确（MET，U343/U345）。
- “无可做”七条：①MET ②MET ③MET ④MET ⑤MET ⑥MET ⑦MET。
- STATE.md §3 开放问题表 16 行逐行给出状态与去向；无 GAP。
- 转入 S5 的 10 项见 S5_HANDOFF_R9M3C.tsv，并原样列入签收范围声明草稿。
- 签收范围声明草稿：checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md（标题与首行写明“草稿，非签收；签收只由用户在对话中给出”）。

## 6. 最终红点台账摘要（RED_POINTS_LEDGER_FINAL_R9M3C.tsv）

- 输入 7 个已提交红点台账；按 id 去重（R6c 的 legacy id 按 R6d 台账显式映射合并）后 26 个红点 id。
- 冲突 21 处（同一 id 在不同台账的原始状态不同，均为历史演进/别名措辞），以最新裁决解决并在文件尾部逐条列出。
- 范围内仍开放红点 0；非红点行（observation 等）与转入 S5 的项分别标注。RP-R8-M2c-1/1b 按 U304 记为已关闭，U350 确认；RP-R6d-15 按 U345（条件满足）带范围声明关闭。

## 7. 事件两张表

### 7.1 表一：越界写入尝试

| 轮次 | 命令 | 是否落盘 | 说明 |
|---|---|---|---|
| r9m3c | 只读侦察命令中误含 mktemp -d（无参数） | 是（创建了一个 /tmp 临时目录） | 执行者违规：命令自身写仓库外路径。start 门禁快照时 /tmp 条目数为 0（环境已清理该目录）。此后所有写入均经 safe_run 且目标在仓库内 |

### 7.2 表二：工具与脚本事件

| # | 事件 | 处理 |
|---|---|---|
| 1 | 门禁与收尾脚本在 start 门禁之前写好（运行 start 门禁本身需要这些脚本） | 照实披露；start 门禁在其时刻的开工不变量全部成立（PASS=46 FAILS=0）；此后严格按 §5 顺序 |
| 2 | FROZEN_SCRIPTS_R9M3C.tsv 在收尾试跑链之前先写定一次，使 end 门禁试跑能校验“从冻结清单读取脚本名”的检查 | 照实披露；试跑后用 write_frozen 复算并与该文件逐字节相同，正式冻结清单即此文件 |
| 3 | S-C 内 readiness 先运行一次（此时最终红点台账尚未生成，①/② 暂为 GAP），随后运行 red_ledger_final 并重跑 readiness | 照实披露；最终草稿 GAP=0，正式冻结期 readiness 只运行一次 |
| 4 | rejudge v1 把逐点 JSON 当作预注册记录传入，取不到 exp_visible，25 个注入点误判 API_SILENT | 试跑期脚本迭代：修正为 prereg+point 合并后 DIFFS=0；冻结期未再改脚本 |
| 5 | append_errata v1 的 U346 断言字符串与报告表二带反引号的文本不一致，写入前 HARD_STOP（未落盘） | 修正断言后通过；ERRATA 前缀 sha 断言仍通过 |
| 6 | 框架落盘：本会话的 /tmp/dsh-spill-* 属框架，不算执行者违规；end 门禁记录 /tmp 快照 | 单列，不计入表一 |

## 8. 需用户裁决

1. U343–U350 八条裁决是否按“旧文件 + 新行”落账为生效（RULINGS 最大 U350；ERRATA 最后 E9-66，共 66 条）。
2. S-B 独立只读复核结果（DIFFS=0、E2E_OK=25、CONTROL_OK=17、阳性对照 16/16、复验 FAILS=0）是否接受，从而 U345 的 RP-R6d-15 带范围声明关闭生效。
3. 签收就绪审计结果（MET=14 GAP=0 TRANSFERRED_S5=5 CLOSED_BY_RULING=7）与 P05_S3_S4_SIGNOFF_DRAFT.md 是否作为后续签收前的范围声明材料。
4. 最终红点台账（26 个 id、21 处冲突以最新裁决解决、范围内开放 0）与 S5 移交 10 项是否接受。
5. 本轮表二的顺序偏差（第 1、2、3 条）是否接受，只登记勘误。

## 9. 交付物清单（与 registries/s4r9/M3c/SHA256SUMS.txt 项数一致）

### 9.1 小表交付物（checkpoints/p05/registries/s4r9/M3c/）

1. GATE_R9M3C_start.txt
2. GATE_R9M3C_start_RECHECK.txt
3. AUDIT_R9M3B_R9M3C.tsv
4. REJUDGE_E2E_R9M3C.tsv
5. REJUDGE_COMPARE_R9M3C.txt
6. POSCTRL_REJUDGE_R9M3C.txt
7. REVERIFY_R9M3B_R9M3C.tsv
8. READINESS_P05_S3S4_R9M3C.tsv
9. S5_HANDOFF_R9M3C.tsv
10. RED_POINTS_LEDGER_FINAL_R9M3C.tsv
11. FROZEN_SCRIPTS_R9M3C.tsv
12. REPORT_CHECK_R9M3C.txt
13. POSCTRL_REPORT_CHECK_R9M3C.txt
14. SHA256SUMS.txt

## 10. 结论

本轮完成 R9 M3c 范围（裁决/勘误落账 + M3b 独立只读复核 + 签收就绪审计 + 最终红点台账 + 签收范围声明草稿），不宣布阶段完成；等待用户审核。

### 附录 A（收尾时由 closeout 写入正式结果）

（APPENDIX_A_PLACEHOLDER）

### 附录 B（end 门禁之后追加；只追加，不改正文）

（APPENDIX_B_PLACEHOLDER）
