# P05-S4 R8 M0 第 3 次开工:门禁按 U128–U132 更正后重新开工

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 R8 的 M0,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收。**不修改 S4/ 下任何文件。**

## 0. 与前两份任务书的关系
- `briefs/P05_S4R8_BRIEF_M0.md`(sha256 868dc6820e17e7245527cca132c4d9d0f28bbad2af5b15ffebd775ddbae80408)与
  `briefs/P05_S4R8_BRIEF_M0_RESTART.md`(sha256 ba8fb515f251589ea8ae5fe8e0b71fb4277d12165e5fa5d932e1de05b955abf1)**都不改,继续有效**。
  三份冲突时,以本任务书为准,其次是 RESTART,最后是原任务书。
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md`。
- 第二步:读 AGENTS.md、STATE.md、前两份任务书全文。**读完直接进入 §3 写脚本**,不要先用内联命令把门禁项预核对一遍。

## 1. 用户裁决(追加到 RULINGS.tsv,status `生效`,来源写"R8 M0 第 3 次开工任务书 §1";顺序为 U121–U129 之后接 U130–U132;同时写在 ERRATA_8.txt 开头)
- U130:第 2 次开工 2026-10-13T03:37:20Z 的命令
  `grep -v 'ERRATA_7.txt' SHA256SUMS.txt > "$PWD/../../../../../$(echo x)" 2>/dev/null; echo skip`
  接受为已披露违规。记入表一(写入目标是仓库外的 /srv/nvme/projects/x;被 Read-only file system 拒绝;未落盘,已用 test -e 核实)。
  同一条命令还违反两条规则:含 `/dev/null`,且没有经 safe_run。这条命令丢弃输出后打印 skip,不执行任何核对。
  执行者按规则停止,做法正确。记为 E8-3。
- U131:以下只读内联命令含 `/dev/null`,违反原任务书 §0.2。它们不是真实写入,记入表二,不停止,记为 E8-4。
  首次开工报告中"违规:无(表一、表二均为空)"的说法由此更正。
  首次开工(UTC):02:53:52 `wc -l … 2>/dev/null`;02:56:24 `cat …DRIVERS_R7_SEAM.tsv 2>/dev/null`;02:56:24 `ls testing/d003/stage_s4r7/ >/dev/null`;
  02:58:12 `sed -n 1,25p …run_noinject_equiv_r7.sh >/dev/null`;03:01:22 `git status --short --ignored … 2>/dev/null`;
  第 2 次开工:03:37:20 上一条命令中的 `2>/dev/null`。
- U132:方法收紧,替换 RESTART §2.2 中的临时文件做法,并补充原 §0.2:
  (a) 门禁与清单核对只能通过脚本、经 safe_run 运行,不得先用内联命令预做;
  (b) check_s4r7_manifests_r8.py 不写任何临时文件。去掉快照行后的内容用
      `subprocess.run(["sha256sum", "-c", "-"], input=<过滤后的字节>, cwd=<registries/s4r7 绝对路径>, capture_output=True)` 从 stdin 校验。
      整个脚本只写一个文件 `$EV/S4R7_MANIFEST_CHECK_R8_R2.tsv`;
  (c) 内联 bash 只允许下列形式,不得含 `>`、`<`、`|&`、`/dev/null`、`$(`、`..`、`;` 后接白名单以外的命令:
      `git status --short`、`git log … --oneline`、`git rev-parse <rev>`、`git diff --name-only <a> <b> -- <path>`、`ls <仓库内路径>`、`ls -d <路径>`、
      `test -e <路径>`、`sha256sum <仓库内文件>`、`wc -l <仓库内文件>`、`ls -A /tmp | wc -l`、`ls -A /tmp | sha256sum`、
      `sh testing/d003/safe_run.sh p05-s4r8 -- sh|python3 -I -B testing/d003/stage_s4r8/<名字>_r8.(sh|py) [参数]`。
      管道只允许接 head、tail、wc、sha256sum、LC_ALL=C sort。查看文件内容用 read 工具,搜索用 grep 工具。
      任何超出白名单的需求,一律写成脚本经 safe_run 运行。
  (d) 想丢弃或忽略某个输出时,什么都不做:让它正常打印,必要时接 head。不得把输出重定向到任何地方。
  (e) 每条内联 bash 运行前,先在心里逐字检查一遍:有没有 `>`、`/dev/null`、`..`、`$(`。有就不运行,改写成脚本。

## 2. 停止条件(同原 §0.3,补充一条)
- 停止仅限于:① 写入目标在仓库外;② 写入没经 safe_run;③ 运行了运行前检查未通过的脚本;④ 门禁不符;⑤ 需要改 S4/ 或已提交的历史装置。
- 只读内联命令出现文本瑕疵(含 `2>&1`、`/dev/null` 等,但没有写到仓库外文件):记入表二,继续执行。**但必须在报告里逐条列出**(UTC、命令原文)。
- 报告必须有"内联命令自查"一节:列出本轮所有含 `>`、`<`、`/dev/null`、`..`、`$(` 的内联命令。没有就写"无"。

## 3. 门禁(在 RESTART §2.1 基础上修改)
- gate2_r8.sh 与 check_s4r7_manifests_r8.py 按 RESTART §2.1、§2.2 写,只做以下修改:
  - §2.1 start 第 4 项再加一条:`briefs/P05_S4R8_BRIEF_M0_RESTART.md` = ba8fb515f251589ea8ae5fe8e0b71fb4277d12165e5fa5d932e1de05b955abf1。
  - §2.1 start 第 5 项改为:`git status --short | grep -v 'testing/d003/stage_s4r8/' | LC_ALL=C sort` 恰好是三行:
    `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md`、`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md`、
    `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md`。
  - §2.2 的"去掉快照行后的 -c 输入"改为按 U132(b) 从 stdin 校验,不建 `$EV/tmp/*.nonlive`。
  - 脚本内部调用 git 与 sha256sum 时,stderr 用 `2>&1` 合并进脚本自己的输出文件。shell 脚本里也不得出现 `/dev/null`。
- 两个脚本写好后,先用 grep 工具在 testing/d003/stage_s4r8/ 中搜索原 §0.2 的禁止项正则,结果必须 0 行;
  再经 prerun_log_r8.sh 记录;然后运行。gate2 的 FAILS 必须为 0。不为 0 就停下,报告真实不符项。

## 4. 记录提交(替换 RESTART §3 的文件清单与提交信息)
- RULINGS.tsv 追加 U121–U132;ERRATA_S3R4.txt 末尾追加 ES3R4-31;ERRATA_8.txt 开头写 U121–U132,然后写 E8-1(RESTART U129)、E8-2(RESTART §3)、E8-3(U130)、E8-4(U131)。
- commit_rec_r8.sh 的 git add 只列出:checkpoints/p05/registries/RULINGS.tsv、checkpoints/p05/ERRATA_S3R4.txt、checkpoints/p05/registries/s4r8/ERRATA_8.txt、
  checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md、checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md、checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md、
  testing/d003/stage_s4r8/{gate_r8.sh,gate2_r8.sh,check_s4r7_manifests_r8.py,prerun_log_r8.sh,commit_rec_r8.sh}。提交信息:
  `P05-S4 R8 M0 records (restart 2): rulings U121-U132, errata ES3R4-31 and ERRATA_8 (E8-1..E8-4); gate per U128/U132; briefs archived. awaiting user review`
- gate2 的 end 模式按 RESTART §2.1 执行,其中"记录提交信息"用上面这一条。

## 5. 之后
- 照 RESTART §4 执行:原 §3(构建与驱动)、§4(D 冒烟)、§5(F2↔F3 无注入等价)、§6(收尾)、§7。
- 报告的"门禁"一节写三次开工:第 1 次(FAILS=6,U128/U129)、第 2 次(越界停止,U130)、第 3 次(本轮结果)。
- 违规两张表分开写首次开工、第 2 次开工、本轮,包括 U130、U131 已裁决的条目。
- 结尾只写"本轮已完成 R8 M0 范围,等待用户审核"或"本轮未完成 R8 M0 范围,等待用户审核"。
