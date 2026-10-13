# P05-S3 R4 续5 报告(S3R4 的续轮,非新阶段):收尾(只做记录、只读核对与提交)

**状态:本轮已完成 S3R4 续5 范围,等待用户审核。**
本轮未宣布任何阶段完成或签收;P05-S3、P05-S4 未签收;报告与 STATE 中不写签收建议(U83)。自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。**本轮未修改 S4/ 下任何文件,未编译、未链接、未运行任何 S4 驱动或 gdb。**

任务书:`checkpoints/p05/briefs/P05_S3R4_CONT5_BRIEF.md`(§0 开工第一步存档,§2 之前已提交,见 §2)。
证据目录:`checkpoints/p05/evidence/p05-s3r4c5/`(不提交)。小表:`checkpoints/p05/registries/s3r4c5/`(提交)。
脚本目录:`testing/d003/stage_s3r4c5/`。

---

## 1. 门禁

| 项 | 实测 | 结果 |
|---|---|---|
| HEAD(开工) | `bee9420c23d6d65d2b6ad4b5dbef83c342f5acfe` | 通过 |
| `HEAD:S4` | `6cff923a02baf19e01966b2339755cbf3a5deeef`(F3) | 通过 |
| judge_d003.py sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` | 通过(内联只读取数;门禁文件由 gate_c5.sh 写入) |
| `git status --short`(开工) | 5 行预期项 + 本任务书存档(`briefs/P05_S3R4_CONT5_BRIEF.md`) | 通过 |
| `/tmp` 顶层(开工) | 0 条目;listing sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 通过 |
| `$EV/GATE_CONT5.txt` | 已写(`gate_c5.sh start`,经 safe_run) | 完成 |
| `/tmp` 顶层(收尾) | 0 条目;listing sha256 同上 | 通过 |
| `$EV/GATE_CONT5_END.txt` | 已写(`gate_c5.sh end`,经 safe_run) | 完成 |

---

## 2. 记录提交

| 项 | 内容 |
|---|---|
| 提交哈希 | `31915485ceb0525fde5212b97769252b070aa24f`(`3191548`) |
| 信息 | `P05-S3R4 CONT5 rulings U111-U120, errata ES3R4-25..30; CONT3/CONT4 reports, registries s3r4c3 and stage_s3r4c3 committed unchanged (apply_seam_f3_c3.sh DO NOT RUN). awaiting user review` |
| 内容 | `RULINGS.tsv`(+10 行 U111–U120)、`ERRATA_S3R4.txt`(追加 U111–U120 裁决块与 ES3R4-25…30)、`briefs/P05_S3R4_CONT4_BRIEF.md`、`briefs/P05_S3R4_CONT5_BRIEF.md`、`P05_S3R4_CLOSEOUT_CONT3.md`、`P05_S3R4_CLOSEOUT_CONT4.md`、`registries/s3r4c3/`(18 个文件)、`testing/d003/stage_s3r4c3/`(18 个文件,原样) |
| 状态提交前 | `$EV/status_before_rec_c5.txt`:`?? checkpoints/p05/registries/s3r4c3/`、`?? testing/d003/stage_s3r4c3/`、`?? P05_S3R4_CLOSEOUT_CONT3.md`、`?? P05_S3R4_CLOSEOUT_CONT4.md`、`?? briefs/P05_S3R4_CONT4_BRIEF.md`、`?? briefs/P05_S3R4_CONT5_BRIEF.md`、`M ERRATA_S3R4.txt`、`M registries/RULINGS.tsv` |

---

## 3. 裁决与勘误

### 3.1 用户裁决 U111–U120

已追加到 `checkpoints/p05/registries/RULINGS.tsv`(原文照录;U111–U115 取自续4 任务书 §1,U116–U120 取自续5 任务书 §1)。摘要:

- U111:续3 的写入违规接受为已披露;续3 的门禁、记录提交、A、B 等结果仍有效。
- U112:接受 ES3R4-25(n = 36);B 跑 44 次的设计接受。
- U113:D 不在 S3R4 补做,转入 R8 第 0 步;登记表不改。
- U114:续3 未提交文件原样提交;`apply_seam_f3_c3.sh` 标 DO NOT RUN。
- U115:续3 缺的交付物由续4 只读补齐,写入 p05-s3r4c4/(续4 未建该目录)。
- U116:续4 停止依任务书正确;两条只读 `2>&1` 接受为已披露(未落盘);续5 起停止条件按任务书 §0.3。
- U117:续4 未提交文件原样提交。
- U118:CTRL_SEAM fmmret 驱动问题登记为 ES3R4-29。
- U119:登记表不改;R8 第 0 步按登记 driver 列选驱动,并断言"登记名 = 实际名"。
- U120:续4 缺的交付物由续5 以只读计算补齐,写入 p05-s3r4c5/。

### 3.2 ERRATA_S3R4.txt 追加条目 ES3R4-25 至 ES3R4-30(原 224 行条目不改)

- **ES3R4-25**:续3 任务书 §3.2 的 n = 12 是算术错误;源码 `pattern.c:418`(同式 `:545`)为 `sizeof(int)*3*(n_vertices-2)`,n_vertices = 5 时为 36(字节);实测窗口 malloc n = 36。
- **ES3R4-26**:更正 D_STATUS_C3.txt 与续3 报告 §3.3 的 D 说明,(a)–(d) 四点(逐条核对行号后写入;原文件不改)。结论句:以上供 R8 第 0 步使用;续3 没有运行 D。
- **ES3R4-27**:B_MAP_C3.tsv 的 `polygon_breakpoint_hits` 列实为窗口 malloc 次数(无 `-g`),不是断点证据。
- **ES3R4-28**:续3 报告 §10"本报告未提交"由 U114 处理;§3.3 的 D 原因由 ES3R4-26 更正。
- **ES3R4-29**:CTRL_SEAM fmmret 驱动选取与登记不符(U118、U119)。登记表 `registries/s4r7/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv` 第 7、8 行 driver 列为 fmmret-F、fmmret-F2,实际由 `run_m2b_all_r7.py:112–131` 解析为 seamF-<tree>;该登记表**仅在 `29bc792` 提交一次**(任务书写的"自 359bf65 起未改"有误,已在 ES3R4-29 更正)。`seam_driver_name` 与 `driver_for` 的函数体在 29bc792、0432234、9c47d00、359bf65 与工作区中哈希相同,即 run5–run7 之间驱动选取逻辑未变。
- **ES3R4-30**:续4 停止记录(U116):两条只读 `2>&1`,未落盘;续4 未建任何目录(本轮只读核对:`p05-s3r4c4/`、`stage_s3r4c4/`、`registries/s3r4c4/` 均不存在)。

---

## 4. §3.1 续3 交付物补齐(只读计算,U120)

脚本:`testing/d003/stage_s3r4c5/supp_c5.sh`(运行前 grep 0 命中,经 safe_run 运行一次)。

| 产物 | 结果 |
|---|---|
| `DIFF_INJECT_C3.txt` | 完成。diff rc=1(有差异,非失败)。差异仅为:窗口符号 `GetContainmentTree` → `DiscretizeCell`;跨调用累计(去掉 `count_window=0` 重置);去掉 `init:K` 分支与 `count_outside`;增加 `s4fmm_poly_window_count()`;打印格式 `S3R4C3_*`。无其他差异。 |
| `DIFF_LINK_C3.txt` | 完成。diff rc=1。差异仅为:标准首段替换 `REPO=` 行(brief 0.2 预期);wrap 符号换为 `Pattern_DiscretizeCell`;驱动与注入器路径;输出路径 `drivers/polyinj-<TREE>`。无其他差异。 |
| `PREREG_D_RECORD_C3.txt` | 完成。`REGISTRY_S3R4C3_D.tsv` sha256 = `a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5`(与任务书一致);`wc -l` = 9(表头 1 行 + 8 点);repo 副本 sha 一致。mtime 为文件修改时间,**不是登记记录**(续3 未写登记记录)。 |
| `BINARIES_C3.tsv` | 完成。见 §5。 |
| `SHA256SUMS_P05-S3R4C3.txt` | 完成。480 行,标准格式,相对 `p05-s3r4c3/`;排除项见 `SHA256SUMS_P05-S3R4C3_EXCLUDED.txt`。 |
| `SHA256SUMS_P05-S3R4C3_CHECK.txt` | 完成。在 `p05-s3r4c3/` 内校验:480 行 OK,rc = 0。 |

注:`p05-s3r4c3/` 中实测没有顶层 `SHA256SUMS.txt`(`test -e` 与 `find` 核对);续3 的 `registries/s3r4c3/SHA256SUMS.txt` 为小表清单,不是证据清单。本轮按任务书生成 `SHA256SUMS_P05-S3R4C3.txt`,未覆盖任何已有文件。

---

## 5. BINARIES 比对

| 名称 | sha256(前缀) | 与续3 已知值 | 结论 |
|---|---|---|---|
| F2 plain 库 `p05-s3r4/build/F2-plain/build/libS4.a` | `c63d180a…c185` | `c63d180a` | **SAME** |
| F3 plain 库 `p05-s3r4/build_f3/plain/build/libS4.a` | `abbc01c7…05de` | `abbc01c7` | **SAME** |
| F3 dbg 库 `p05-s3r4/build_f3/dbg/build/libS4.a` | `10ea03b3…fa` | 无已知值 | **FIRST_RECORD** |
| init-F2 驱动 `p05-s3r4c2/drivers/init-F2/driver` | `29bb377c…1158` | `29bb377c` | **SAME** |
| init-F3 驱动 `p05-s3r4c2/drivers/init-F3/driver` | `ff66cfc1…0b68` | `ff66cfc1` | **SAME** |
| polyinj-F2 驱动 `p05-s3r4c3/drivers/polyinj-F2/driver` | `237bbefc…7559` | 无已知值 | **FIRST_RECORD** |
| polyinj-F3 驱动 `p05-s3r4c3/drivers/polyinj-F3/driver` | `419cfb72…ad30` | 无已知值 | **FIRST_RECORD** |

全部已知值 SAME,无 DIFFERENT。完整哈希见 `BINARIES_C3.tsv`。

---

## 6. §3.2 CTRL_SEAM 驱动的离线解析

**状态:完成(可行)。** 依据:`run_m2b_all_r7.py`、`run_m2_r7.py`、`expected_env_independent_r7.py`、`compare_trees_r7.py`、`matrix_r2.py`、`judge_d003.py` 的 import 时代码(顶层)只有路径计算与常量赋值;所有 `open(...,"w")`、`os.makedirs`、`subprocess` 调用都在函数体内(只读 grep 核对:`run_m2_r7.py:124、261–263、283`;`matrix_r2.py:124–140、170–177`)。import 不写文件、不启动进程。

脚本:`testing/d003/stage_s3r4c5/resolve_ctrl_seam_c5.py`(只 import `run_m2b_all_r7`,调用 `load_seam_drivers`、`ctrl_seam_points`、`driver_for("CTRL_SEAM", …)`;不调用 run;`driver_for` 只做 sha256 读取)。经 `resolve_ctrl_seam_c5.sh` 运行:先写 `EXPECT_RESOLUTION_C5.txt`(sha256 `e99a5dff…d208`),再运行解析。解析器 rc = 0,stderr 为空。

| point_id | 登记 driver | 解析 driver | sha 匹配 | 结论 |
|---|---|---|---|---|
| CTRL-SEAM-seamF-F | seamF-F | seamF-F | yes | AGREE |
| CTRL-SEAM-seamF-F2 | seamF-F2 | seamF-F2 | yes | AGREE |
| CTRL-SEAM-fmmret-F | fmmret-F | seamF-F | yes | DISAGREE |
| CTRL-SEAM-fmmret-F2 | fmmret-F2 | seamF-F2 | yes | DISAGREE |

结果与期望完全一致(seamF 两行 AGREE;fmmret 两行 DISAGREE,解析为 seamF-F、seamF-F2)。**无待裁决项。**

只读时间线核对:run7 调用 `run_m2b_all_r7.py run ... run7` 记录于 `checkpoints/p05/evidence/p05-s4r7/safe_run.log` 第 378 行,UTC `2026-10-12T19:16:00Z`(run5 为第 359 行,run6 为第 367 行)。

---

## 7. ES3R4-29 的引用

ERRATA ES3R4-29 已包含"离线解析"引用(指向 `CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv`)。解析结果与 ES3R4-29 的 [源码] 结论一致:fmmret 两行实际运行的驱动为 seamF 驱动。

---

## 8. STATE 变更摘要

| 项 | 变更 |
|---|---|
| 开工基线 HEAD | `0b1b4a3` → `bee9420` |
| 当前轮次 | 续2 描述 → 续5(收尾):A 36/36、B 44/44、D 转 R8 第 0 步、ES3R4-29 |
| 关键数字(S3R4 行) | 补 A 36/36、对照 6/6;B 44/44、对照 12/12;Mfirst;窗口 malloc n = 36;续4 停止;续5 |
| 开放问题表 | "S3R4 自检 A、B、D" 改为 "D 冒烟 8 点 → R8 第 0 步"(一行);"806、415、RP-S3R4-1" 改为注入自检通过、修复后验证 → R8(一行);"−1…−9" 改为说明已写(一行);新增 ES3R4-29 一行(无重复) |
| 裁决台账引用 | U103–U106 → U103–U120 |
| 证据位置 | 补 p05-s3r4c5 与 p05-s3r4c3 及 registries 对应目录 |

STATE 共 59 行(仍在一页以内;规则:一页以内)。

---

## 9. 清单

| 清单 | 结果 |
|---|---|
| `$EV/SHA256SUMS.txt`(覆盖 p05-s3r4c5 全部非二进制文件,24 行) | 完成;`sha256sum -c` rc = 0,24/24 OK。`safe_run.log` 与 `SHA256SUMS.txt` 本身不进清单,说明见 `SHA256SUMS_NOTE_C5.txt`(清单后追加,不参与校验) |
| `registries/s3r4c5/SHA256SUMS.txt`(14 个文件) | 完成;在 registries 目录内 `sha256sum -c`:14/14 OK,rc = 0 |
| 复制比对(原件 vs 副本) | 完成;14/14 SAME(`COPY_COMPARE_C5.txt`) |
| `p05-s3r4c3/` 清单 | 完成(§4) |

---

## 10. 违规披露(AGENTS 第 3 节,两张表)

### 表一:越界写入尝试(命令自身写了仓库外路径)

**无。** 本轮所有写入均经 safe_run 运行的脚本,目标路径均在 `$REPO` 内(`$EV/`、`testing/d003/stage_s3r4c5/`、`checkpoints/p05/`)。`/tmp` 顶层仅作只读快照(0 条目,未写入)。

### 表二:工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 处理 |
|---|---|---|---|
| CONT5 开工至 §3.2 之前 | 只读核对(`sed -n`、`ls -d`、`cut`、`grep` 等)中,若干条内联命令文本含 `2>&1`(错误输出合并,没有输出文件)。这些命令只读,没有写入目标。按任务书 §0.3 只记入表二,不停止。 | 否 | 记入表二;未造成仓库外写入、未触发停止条件 |
| CONT5 §3.1 | `supp_c5.sh` 初稿中 `find ... ! -path './tmp/*'` 命中 grep 禁止正则 `(^|[^V])/tmp`(`./tmp/*` 的 `/tmp` 子串,实为仓库内相对路径,并非 `/tmp`);运行前检查发现,未运行,已改为 `-prune` 写法后再 grep(0 命中)才运行 | 否(未运行) | 草稿改正,不算违规(运行前检查未通过的脚本从未执行) |
| CONT5 §3.1 | 脚本 `supp_c5.sh` 中 DIFF_INJECT 注释引用 `INJECTOR_DIFF_POLY_C3.txt`,该文件在 `p05-s3r4c3/` 中**不存在**(续3 报告的错误引用,并非本轮生成) | 否 | 如实记录;未改 DIFF 文件(diff 原样) |
| CONT5 §3.2 | `resolve_ctrl_seam_c5.py` 初稿直接调用 `seam_driver_name`,与任务书"调用 `driver_for`"不符;已改为调用 `driver_for`(运行前改正) | 否(未运行) | 草稿改正 |
| CONT5 §4 | `copy_registries_c5.sh` 第一次运行时,在 `MISSING GATE_CONT5_END.txt` 退出之前已 `mkdir` 并复制了 `GATE_CONT5.txt`,留下部分目录 `registries/s3r4c5/`(仅一个文件)。脚本正确拒绝了第二次运行。 | 是(目录与一个文件) | 核对该文件与 `$EV/GATE_CONT5.txt` 完全相同(cmp),经 `cleanup_reg_c5.sh`(safe_run)删除该一个文件与空目录后,重新运行成功。删除范围仅限本轮自己产生的文件,路径在仓库内。 |
| CONT5 §4 | `copy_registries_c5.sh` 的 `grep -c SAME` 会把 `DIFFERENT` 计入(子串匹配),已改为按第 4 列 `awk` 计数后运行 | 否(未运行) | 草稿改正 |
| CONT5 | `supp_c5.sh` 的 BINARIES 比对列初稿为占位 `SAME_OR_DIFF`,已改为脚本直接给出 SAME/DIFFERENT/FIRST_RECORD(未运行) | 否 | 草稿改正 |

**本轮违规判定:表一无;表二所列事件均未造成仓库外写入。** 按 §0.3 的停止条件(真实写入的①②③),本轮未触发停止。

---

## 11. 待用户裁决

**无。** 本轮 §3.2 结果与期望一致;BINARIES 全部 SAME 或 FIRST_RECORD;SHA256SUMS_P05-S3R4C3 校验 480/480 OK;无 MISMATCH。

---

## 12. 提交与收尾

- 最终提交(`commit_final_c5.sh`):STATE.md、P05_S3R4_CLOSEOUT_CONT5.md、registries/s3r4c5/、testing/d003/stage_s3r4c5/。
- 提交后真实的 `git log -3 --oneline` 与 `git status --short` 写入 `$EV/FINAL_GIT_C5.txt`(见该文件)。

本轮已完成 S3R4 续5 范围,等待用户审核。
