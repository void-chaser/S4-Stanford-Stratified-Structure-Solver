# P05-S4 R9 M3e 报告（r9m3e）

> 轮次：P05-S4 R9 M3e。只读复核 + 文档写入；未运行 S4 的任何程序（无 make / make test / E2E / d003 矩阵 / gdb / 构建）。

## 1 门禁

- 0a 自检：签收块非空、无占位符、含“签收”二字；签收日期原文为【2026-10-18】，去掉全角括号后为 YYYY-MM-DD 格式的 2026-10-18。开工前 m3e 证据目录与 brief 均不存在（test -e 断言），/tmp 顶层 0 条目。
- start 门禁：34 项 PASS、0 FAIL（GATE_R9M3E_start.txt）。HEAD=37fbc0f2…c02bd；HEAD:S4=589e15e…46cf（F4）；判定器 sha256=d2d04145…09eb；RULINGS.tsv 145103 B / sha 21ab76d2… / 最大 U358；ERRATA_9.txt 62654 B / sha d71543bb… / 最后 E9-73；STATE.md 6636 B / sha 6eeb7559…。M3d 小表 11/11 OK；m3d 证据目录 39/39 OK；历史 13 份清单全部 OK，项数由脚本数出后断言：s3r5=14、M0=25、M1=28、M1R2=33、M1R3=26、M1R4=11、M2=14、M2b=13、M2c=11、M3a=17、M3b=18、M3c=13、M3d=11；仓库根 registries/ 不存在。
- end 门禁：见附录 B（冻结期正式单次运行；输出写 $EV/gate/，不纳入 SHA256SUMS）。

## 2 裁决（U359–U363）

| 编号 | 内容摘要 | 依据 |
|---|---|---|
| U359 | 用户签收 P05-S3、P05-S4；内容列逐字引用签收块原文 | 用户对话（2026-10-18） |
| U360 | ① M3d 修正版为签收前唯一现行版本（M3c 产物保留为历史） | 签收块 (b) |
| U361 | ② v1→v2 的 P-1…P-6 差异不逐条再确认 | 签收块 (b) |
| U362 | ③ U354、U356 维持 | 签收块 (c)(d)(f) |
| U363 | ④ 无台账 id 的 2 项（ES3R4-5/528/1164、U2 stage e）以 STATE 行对应 | 签收块 (f) |

## 3 勘误（E9-74–E9-77）

- E9-74：M3d end 门禁 M3C_AND_M3B_COMMITTED_FILES_UNCHANGED 的 FAIL 是检查器口径缺陷（把新增 A 文件算作改动）。复核 c4f6707..37fbc0f 的 name-status 计数、全部 M 文件、以及 RULINGS.tsv/ERRATA_9.txt 的纯追加性质，事实见 ERRATA_RECHECK_R9M3E.txt。
- E9-75：M3d copy_registries 的 DEST 多写一级 ..；复核仓库根 registries/ 不存在、M3d 清单 11/11 OK。
- E9-76：S5_HANDOFF_R9M3D.tsv 的 S5-M3D-06 source_ruling 应为 U5（E6-4，no-TWICE 路径不在范围内）；核对 RULINGS.tsv 的 U5 行与 registries/s4r6/ERRATA_6.txt 的 E6-4 原文；不改 M3d 文件，S5 开工以本勘误为准。
- E9-77：M3d 门禁检查器口径与路径问题由 M3e 写入纪律修正（§2 后两条），只登记，不重跑 M3d。

## 4 签收文件摘要

- 新建 P05_S3_S4_SIGNOFF.md：§1 S1/S2 维持原记录（2026-10-11），S3/S4 已由用户签收（2026-10-18），S5 未开始；§2 签收块原文逐字照录；§3 S5 接收 S5_HANDOFF_R9M3D.tsv 的 7 项（S5-M3D-06 按 E9-76 记 U5）；§4 执行者声明（依据用户授权写入、未自行宣布阶段完成；P05-S5 未开始、未签收）。
- 只读断言：签收文件 §2 与任务书 BEGIN/END 之间文本逐字相同（脚本比对 PASS；end 门禁独立复核）。

## 5 事件两张表

### 5.1 表一：越界写入尝试

| # | 命令/脚本 | 目标 | 是否落盘 |
|---|---|---|---|
| 1 | 首次 start 门禁写校验脚本（命令经 bash -c 传入，内层 $REPO/$EV 被外层 shell 先展开） | /checkpoints/p05/evidence/p05-s4r9/m3e/tmp/start_gate_r9m3e.py（仓库外，路径不存在） | 否（mkdir/open 失败，rc 非零） |
| 2 | 首次 start 门禁执行命令 | mkdir -p /tmp；TMPDIR=/tmp；python3 /tmp/start_gate_r9m3e.py | 否（脚本不存在，未生成文件；/tmp 顶层保持 0 条目） |
| 3 | 清理尝试（python os.unlink(/tmp/start_gate_r9m3e.py)） | /tmp | 否（FileNotFoundError） |

原因：命令以 bash -c 包一层传入 safe_run 时，内层 $REPO/$EV 在 safe_run 之外先被外层 shell 展开。改为 safe_run 直接传参（python3 -c / python3 -I -B）后不再发生；当前 /tmp 顶层 0 条目。

### 5.2 表二：工具与脚本事件

| # | 事件 | 影响 |
|---|---|---|
| 1 | 首次 start 门禁的两次 safe_run 调用被记为失败命令（safe_run.log 第 1–2 行） | 无仓库内写入；已在表一披露 |
| 2 | start 门禁校验脚本放在 $EV/tmp/（未提交，不纳入 FROZEN） | end 门禁只对 stage_s4r9 下 r9m3e 脚本做冻结校验 |

其余：本轮无裸跑写入、无 heredoc 残留、无框架落盘（/tmp/dsh-spill-* 未出现）、无仓库内路径拼错。

## 6 需用户裁决

- 无新增需用户裁决项：签收块字面对 §3 的 ①–④ 均有明确表态，已分别登记 U360–U363。
- M3d 报告 §7 第 5 条（不宣布完成）由本轮签收文件 §4 与本报告 §8 遵守，无需另行裁决。

## 7 交付物

复制到 checkpoints/p05/registries/s4r9/M3e/ 的小表（前 4 项 + 清单本身）：

1. GATE_R9M3E_start.txt
2. ERRATA_RECHECK_R9M3E.txt
3. REPORT_CHECK_R9M3E.txt
4. FROZEN_SCRIPTS_R9M3E.tsv
5. SHA256SUMS.txt

## 附录 B（end 门禁）

正式 end 门禁输出：$EV/gate/GATE_R9M3E_end.txt（不纳入 SHA256SUMS）。运行后由收尾在本节追加实际内容。


### 正式 end 门禁输出（冻结期单次运行，原文摘要）

```
COUNTS	pass=35	fail=2	skip=0	total=37
FAILS=2
FAIL	POST_I_CALL_COUNT_GATE_R9M3E_END	expected=1	actual=CHECK_CRASHED: TypeError: 'tuple' object is not callable
FAIL	POST_I_CALL_COUNT_M3E_CHAIN_R9M3E_-	expected=6	actual=CHECK_CRASHED: TypeError: 'tuple' object is not callable
```

两处 FAIL 均为门禁检查器自身崩溃（POST_I 调用计数辅助函数返回 tuple 而不是可调用对象，TypeError: 'tuple' object is not callable），不是本条事实 FAIL；按任务书 §2“冻结期不修脚本、不重跑”照实记录，未修复、未重跑。

独立只读重算（未改冻结脚本、未重跑门禁；仅统计提交 (i) 之后、命令以 python3/sh/bash 开头的 safe_run 记录）：

```
POST_I_RECOUNT chain_calls=6 gate_end_calls=1
  chain line 59: m3e_chain_r9m3e.py report 
  chain line 60: m3e_chain_r9m3e.py report_check 
  chain line 61: m3e_chain_r9m3e.py copy 
  chain line 62: m3e_chain_r9m3e.py events 
  chain line 63: m3e_chain_r9m3e.py progress 
  chain line 64: m3e_chain_r9m3e.py sha_sums 
  gate line 65: sh testing/d003/stage_s4r9/gate_r9m3e.sh end
```

结论：正式链各脚本在提交 (i) 之后各调用一次（chain=6、gate end=1），门禁的两处 FAIL 为检查器执行缺陷；按 M3d 先例只登记、不重跑。
## 8 本轮状态与结论

- 本轮只读复核 + 文档写入；未运行 S4 的任何程序；S4/、判定器、历史装置、M3d 已提交产物未改动（end 门禁按 BASE 前缀校验）。
- 签收只记录用户原文；执行者未自行宣布任何阶段完成或签收。P05-S5 未开始、未签收。
- 本轮已完成 R9 M3e 范围，等待用户审核。

git log -1: 8a42e1ca49e4fccdb7442ccb220be14d9b499ade P05-S4 R9 M3e (i): signoff P05-S3/S4 (U359..U363), errata E9-74..E9-77, signoff file, STATE, frozen scripts; awaiting user review
git status --short（提交 (ii) 前快照）: ?? checkpoints/p05/P05_S4R9_M3e_REPORT.md; ?? checkpoints/p05/registries/s4r9/M3e/
