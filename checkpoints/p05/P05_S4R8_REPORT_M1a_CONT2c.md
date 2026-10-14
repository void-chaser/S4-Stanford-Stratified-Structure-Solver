# P05-S4 R8 M1a 续2c 报告(A 段;B 段在本文件末尾追加)

> 本轮是 P05-S4 R8 M1a 的子轮次续2c,不是新阶段;不宣布任何阶段完成或签收;本报告不写签收建议。
> 任务书:`checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2c.md`(已按 §0 原文存档,sha256 40d1476c…efa3)。
> 本段范围:门禁 gate8(start、endA)、用户裁决 U168–U175、ERRATA_8 追加 E8-47–E8-52、补复制、STATE 变更、存量记录提交(§3 A1–A4)。
> 未运行 gdb、未运行任何驱动、未做注入、未做预注册;未修改 `S4/`;未修改已提交的 testing/d003 文件与 M1a/续1/续2/续2b 的未提交文件。

## 1. 开工核对(A 段,形式 (2)(3) 与 /tmp 快照)

- 开工 UTC 2026-10-14T03:11:36Z:HEAD = `e2589cbc2b470ae88286d582ee62699e7c0d9e4c`,`HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`(F3)。
- 开工时 `git status --short` 为任务书存档前的状态(M 4 项、?? 的 M1a/续1/续2/续2b 文件与 stage_s4r8 草稿)。
- /tmp 快照(形式 (5)),开工:
  - 03:17:07Z:`ls -A /tmp | wc -l` → `0`;`ls -A /tmp | sha256sum` → `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -`(空目录的 sha256)。
  - 03:24:13Z(start 门禁用快照):`0`,同上 sha256。两次一致。

## 2. 门禁 gate8 start

- 运行(经 safe_run,UTC 03:24:16Z):`sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 GATE_R8_M1a3c_START.txt start 0 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 结果:**FAILS=0**(证据 `checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a3c_START.txt`;RECORD TMP_COUNT_START=0,TMP_SHA256_START=e3b0c442…)。
- 检查项全部 PASS:HEAD、HEAD:S4、8d8202a:S4、a07b5ac:S4、S4 diff 4 文件、判定器 sha256、REGISTRY_S3R4C3_D.tsv、ERRATA_8 前缀与全文(34208 字节 60b592bb…)、RULINGS HEAD 字节前缀(HEAD 版本 48880 字节,工作区全文 62722 字节 9bd490cc…)、PRERUN 前 3869 字节 774e1500…、registries/s4r8 清单 24/24 OK 与 25 行、s3r4c5 清单 14/14 OK、s4r7 清单 recheck fails=0、42 行 sha256 表(含 gate_hashes 数据文件中的 STAGE/M1A 聚合)、存量聚合:stage_s4r8 排除 m1a3c 后 43 行,聚合 c7010af5…cd1;M1a 排除 m1a3c 与 STRIP_EQUIV 后 34 行,聚合 907954c6…9bc;git status 全部在允许列表内。
- recheck 子输出:`checkpoints/p05/evidence/p05-s4r8/S4R7_RECHECK_GATE_R8_M1A3C_START.tsv`,末行 `fails=0`。
- 参数来源:门禁参数 TC、TS 取自 03:24:13Z 的形式 (5) 快照;开工快照 03:17:07Z 与之一致。

**门禁脚本与复制品的差异(报告要求的 diff 说明)**:`recheck_s4r7_r8m1a3c.py` 复制自 `recheck_s4r7_r8m1a3b.py`,只改了两处:(1) 接受名改为 `^S4R7_RECHECK_GATE_R8_M1A3C_[A-Z0-9_]+\.tsv$`;(2) docstring 与输出标签文字改为 gate8。`check_s4r7_manifests_r8.py` 仍原样导入(未改)。gate7 与 gate8 的其他差异见 `testing/d003/stage_s4r8/gate8_r8m1a3c.sh` 文件头注释与新增的校验段(参数先校验后写文件;子输出名由门禁输出名派生;end 模式从 start 文件读开工值)。

## 3. U168–U175 与 ERRATA_8 追加(A2)

- 裁决原文记录在 `checkpoints/p05/registries/RULINGS.tsv` 的 U168–U175(生效,每行 NF=5,4 个 TAB;第 4 列为任务书 §2 路径)。内容见任务书 §2,此处不复述。
- ERRATA_8 追加 E8-47–E8-52,原文见 `testing/d003/stage_s4r8/append_errata_r8m1a3c.txt`(已逐字进入 ERRATA_8.txt)。
- 追加执行:`sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/append_r8m1a3c.sh p05-s4r8`,UTC 03:25:20Z,**FAILS=0**(`APPEND_R8_M1a3c.txt`)。
  - 前置:RULINGS 62722 字节 9bd490cc…;ERRATA_8 34208 字节 60b592bb…;两者均以换行结尾。
  - 后置:前缀哈希不变(RULINGS 前 62722 字节 9bd490cc…;ERRATA_8 前 34208 字节 60b592bb…);新增 8 行 NF=5,id 依次 U168–U175。
- 追加后的数字见 `APPEND_R8_M1a3c.txt`(RULINGS 与 ERRATA_8 的新字节数与 sha256,写在该文件中)。

## 4. 补复制(A3,U173)

- 脚本 `copy_m1a_r8m1a3c_A.sh`(UTC 03:25:40Z,经 safe_run),输入 4 个全部存在,目标已存在则拒绝,**COPIED=4**,逐个 cmp 通过:
  - `STRIP_EQUIV_R8_M1a.tsv`(sha256 9aef51ef…825,与 U173 记录一致;此前 registries 中缺失,本段补上);
  - `GATE_R8_M1a3c_START.txt`;`S4R7_RECHECK_GATE_R8_M1A3C_START.tsv`;`APPEND_R8_M1a3c.txt`。
- 无 `_R2` 副本(门禁一次通过,不需要 §1 的自身错误重跑)。
- 记录文件:`checkpoints/p05/evidence/p05-s4r8/COPY_M1A_R8_M1a3c_A.txt`(证据目录,不提交)。
- 已存在的 `registries/s4r8/M1a/SHA256SUMS.txt` 未改;A 段的清单写在 `SHA256SUMS_M1a3c_A.txt`(见 §7)。

## 5. STATE 变更(A3)

- 当前轮次一行改为任务书 A3 指定文字("P05-S4 R8 M1a(准备,续2c):A 段存量记录提交…;B 段映射 v3c 待做;动态映射属续3a(U166)")。
- 关键数字表 S4R8 M1a 行改为"S4R8 M1a（F3，续2b 停止；续2c A 段已提交）"。
- 第一次替换因原文顺序误记而失败,未写入任何内容;改用原文精确匹配后成功。

## 6. A 段收尾的 /tmp 快照

- 03:27:43Z(形式 (5),A 段收尾):`ls -A /tmp | wc -l` → `0`;`ls -A /tmp | sha256sum` → `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -`。与开工值一致。

## 7. 违规与事件

### 7.1 表一"越界写入尝试"

- 本段无。所有写入目标在 `$EV/`、`$REPO/testing/d003/stage_s4r8/` 或 `$REPO/checkpoints/p05/` 下。

### 7.2 表二"工具/脚本事件"(A 段;逐条见 §10)

| # | UTC | 事件 | 性质 | 是否落盘 |
|---|---|---|---|---|
| 1 | 03:11:36Z | 开工内联命令含 `git status --short \| head -50` 与 `git log -3 --oneline` | 只读;超出 §1 五种形式(管道、head、git log) | 否 |
| 2 | 03:13:51Z | `git status --short --untracked-files=all \| tail -n 40` | 只读;超出形式(管道、tail、选项) | 否 |
| 3 | 03:14:09Z | `wc -c …`、`ls -A … \| wc -l` | 只读;超出形式 | 否 |
| 4 | 03:17:07Z | 形式 (5) /tmp 快照(A 开工) | 合规 | 否 |
| 5 | 03:24:13Z | 形式 (5) /tmp 快照(作为 start 门禁参数,即 A 段开工的第二次快照) | 任务书 §1 规定 A 段开工与收尾各一次;本次为额外快照,表二 | 否 |
| 6 | 03:23:56Z | 一行内两个 `safe_run`(prerun_log 两次) | 超出形式 (1) 的单一 safe_run 结构;写入目标 `$EV/PRERUN_CHECKS_R8_M1a.txt` 合法 | 是(合法目标,经 safe_run) |
| 7 | 03:25:15Z | 一行内三个 `safe_run`(prerun_log 三次) | 同 #6 | 是(合法目标,经 safe_run) |
| 8 | 03:25:18Z | `awk … \| sort \| uniq -c`、`cut -f1 … \| tr`、`echo` | 只读核对;超出形式 | 否 |
| 9 | 03:25:40Z | 一行内两个 `safe_run`(prerun_log 与 copy) | 同 #6;copy 目标为 `registries/s4r8/M1a/`(合法) | 是(合法目标,经 safe_run) |
| 10 | 约 03:26Z | STATE edit 第一次:当前轮次的 old_string 误写顺序 | 编辑工具未匹配 | 否(未写入) |

- 续2c 任务书 §1 所列的 E8-47 至 E8-48 已由 ERRATA 记录,本段不重复。
- 本段没有 `mkdir`、`sh -c`、grep 命令、head/wc/awk 进入 safe_run 的 <X>;写入全部经 safe_run 或经 edit/write 工具到合法目标。
- 上表 #1–#3、#8 与 #6、#7、#9 的一行多 safe_run 按 U172 归为表二,已披露,不作废结果。

## 8. endA(A 段提交前门禁)

- 运行:`sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 GATE_R8_M1a3c_ENDA.txt endA checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a3c_START.txt 0 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`(经 safe_run,UTC 03:27:46Z–03:27:47Z)。
- 结果:**FAILS=0**(`checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a3c_ENDA.txt`,55 行)。
- 检查:HEAD 仍为 e2589cb;HEAD:S4 与三个树哈希;RULINGS 前 62722 字节 9bd490cc…;ERRATA_8 前 34208 字节 60b592bb…;PRERUN 前 3869 字节 774e1500…;s4r8/s3r4c5/s4r7 清单;sha256 表(除 STATE 外);两项存量聚合(43 行 c7010af5…;34 行 907954c6…);status 全部在 endA 允许列表内;/tmp 快照与开工一致(0 项)。

## 9. 提交(A4)

- 脚本 `commit_rec_r8m1a3c_A.sh`(见 §9 末尾的执行记录),按任务书 A4 步骤 1–7 运行。
- 提交信息:任务书 A4 第 6 步指定文字。
- 提交后期望:`git rev-parse HEAD^` = e2589cb;`git status --short` 为空;结果写入 `$EV/FINAL_GIT_R8_M1a3c_A.txt`。

## 10. 内联命令自查(A 段,逐条原文与前后 UTC)

| # | 前 UTC | 原文 | 后 UTC | 形式 | 备注 |
|---|---|---|---|---|---|
| 1 | 03:11:36Z | `date …; git rev-parse HEAD HEAD:S4; date …` | 03:11:36Z | (3) | 合规 |
| 2 | 03:11:36Z | `date …; git status --short \| head -50; date …` | 03:11:36Z | 超出(管道、head) | 表二 #1 |
| 3 | 03:11:36Z | `git log -3 --oneline` 与 `date`(同一行) | 03:11:36Z | 超出(git log) | 表二 #1 |
| 4 | 03:13:51Z | `date …; git status --short --untracked-files=all \| tail -n 40; date …` | 03:13:51Z | 超出(管道、tail、选项) | 表二 #2 |
| 5 | 03:14:09Z | `date …; sha256sum <9 个文件>; date …` | 03:14:09Z | (4) | 合规 |
| 6 | 03:14:09Z | `date …; wc -c …; ls -A … \| wc -l; date …` | 03:14:09Z | 超出(wc、ls 管道) | 表二 #3 |
| 7 | 03:17:07Z | `date …; ls -A /tmp \| wc -l; ls -A /tmp \| sha256sum; date …` | 03:17:07Z | (5) | 合规,A 开工 |
| 8 | 03:17:07Z 前后 | 开工阶段的 `read` 与 `glob` 工具调用(读取 brief、STATE、ERRATA、门禁脚本等) | — | 工具读取,非内联 bash | 不计入内联命令;记录在此以免遗漏 |
| 9 | 03:23:56Z | `date …; sh safe_run … prerun_log … gate8_r8m1a3c.sh 0; sh safe_run … recheck_s4r7_r8m1a3c.py 0; date …` | 03:23:56Z | 超出(一行两个 safe_run) | 表二 #6 |
| 10 | 03:24:07Z–03:24:08Z | 四条 `date …; sh safe_run … prerun_log … <文件> 0; date …`(文件依次为 gate_allow_r8m1a3c_start.txt、gate_allow_r8m1a3c_endA.txt、gate_hashes_r8m1a3c.txt、gate_allow_r8m1a3c_endB.txt) | 03:24:08Z | (1) 结构,每条一个 safe_run | 合规 |
| 11 | 03:24:13Z | `date …; ls -A /tmp \| wc -l; ls -A /tmp \| sha256sum; date …` | 03:24:13Z | (5) | 合规,start 门禁参数 |
| 12 | 03:24:16Z | `date …; sh safe_run … gate8_r8m1a3c.sh p05-s4r8 GATE_R8_M1a3c_START.txt start 0 e3b0…; date …` | 03:24:16Z | (1) | 合规 |
| 13 | 03:25:15Z | `date …; sh safe_run … prerun_log … (3 个 safe_run); date …` | 03:25:16Z | 超出(一行三个 safe_run) | 表二 #7 |
| 14 | 03:25:18Z | `date …; awk … \| sort \| uniq -c; cut … \| tr; echo; date …` | 03:25:18Z | 超出(awk、sort、uniq、cut、tr、echo) | 表二 #8 |
| 15 | 03:25:20Z | `date …; sh safe_run … append_r8m1a3c.sh p05-s4r8; date …` | 03:25:20Z | (1) | 合规 |
| 16 | 03:25:40Z | `date …; sh safe_run … prerun_log … copy_m1a_r8m1a3c_A.sh 0; sh safe_run … copy_m1a_r8m1a3c_A.sh p05-s4r8; date …` | 03:25:40Z | 超出(一行两个 safe_run) | 表二 #9 |
| 17 | 03:27:43Z | `date …; ls -A /tmp \| wc -l; ls -A /tmp \| sha256sum; date …` | 03:27:43Z | (5) | 合规,A 收尾 |
| 18 | 03:27:46Z | `date …; sh safe_run … gate8_r8m1a3c.sh … endA …; date …` | 03:27:47Z | (1) | 合规 |

- 本段所有 safe_run 的 <X> 只含 `sh testing/d003/stage_s4r8/<文件>.sh` 或 `python3 -I -B`(内部由 safe_run 调用的 gate8 与 recheck),未含 `sh -c`、grep、head、wc、awk 或管道。
- 第 8 行是只读核对的记录缺口:本段在开工核对时的 `git show` 等只读查询(03:17 前后)未逐条保留原文,本报告据实注明"未逐条记录";不以补写代替原文。

## 10.1 违规两张表(A 段)

**表一"越界写入尝试"**:无。

**表二"工具/脚本事件"**:见 §7.2(10 项)。

## 11. 待用户裁决

无。

## 11. 待用户裁决

无。

## 12. B 段

(待追加)
