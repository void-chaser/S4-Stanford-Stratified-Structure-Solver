# P05-S3 R4 续2(S3R4 的续轮,不是新阶段):提交续1 记录,补完自检 C(多边形)、A、B、D,并收尾

你是 P05-S3 的自检执行者。本轮是 S3R4 的第二个续轮(记为 S3R4 续2),不得出现 P05-S6。
不得宣布任何阶段完成或签收;报告与 STATE 中不写签收建议(U83)。本轮自检不是修复后验证;
修复后验证由 P05-S4 R8 在 F3 上完成。**本轮不得修改 S4/ 下任何文件。** 如果自检表明需要改 S4/,停下报告。

先读(按顺序):AGENTS.md、checkpoints/p05/STATE.md、
checkpoints/p05/briefs/P05_S3R4_CONT1_BRIEF.md(**本轮的技术内容沿用它的 §3–§7,下文只写差异;冲突时以本任务书为准**)、
checkpoints/p05/P05_S3R4_CLOSEOUT_CONT1.md、checkpoints/p05/P05_S3R4_CLOSEOUT.md、checkpoints/p05/ERRATA_S3R4.txt、
checkpoints/p05/briefs/P05_S3R4_BRIEF.md、checkpoints/p05/evidence/p05-s3r4/map_F2_A1/stderr.txt、
testing/d003/stage_s3r4/ 下全部脚本、testing/d003/stage_s4r7/link_drivers_s4r7.sh 与 link_seam_drivers_r7.sh。

- 证据目录:checkpoints/p05/evidence/p05-s3r4c2/(新目录;不往 p05-s3r4/、p05-s3r4c1/ 写任何东西)
- 新脚本目录:testing/d003/stage_s3r4c2/(新目录;续1 任务书中带 c1 的文件名在本轮一律改为 c2,
  例如 driver_s3r4c2_poly.cpp、inject_s3r4c2_poly.cpp、link_init_c2.sh)
- 小型结果表:checkpoints/p05/registries/s3r4c2/
- 报告:checkpoints/p05/P05_S3R4_CLOSEOUT_CONT2.md
- 勘误:在 checkpoints/p05/ERRATA_S3R4.txt 末尾追加,从 ES3R4-15 起编号,不改已有条目
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_CONT2_BRIEF.md。

## 0. 门禁与操作规则

### 0.1 开工门禁(任一不符就停下报告)
- HEAD = 0b1b4a3;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3);
  judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- `git status --short` 只允许以下 4 行(本轮的任务书存档是第 5 行,属于预期):
  ` M checkpoints/p05/ERRATA_S3R4.txt`、` M checkpoints/p05/registries/RULINGS.tsv`、
  `?? checkpoints/p05/P05_S3R4_CLOSEOUT_CONT1.md`、`?? checkpoints/p05/briefs/P05_S3R4_CONT1_BRIEF.md`。
- `ls -d testing/d003/stage_s3r4c1` 存在,且 `ls -A testing/d003/stage_s3r4c1` 为空。
- /tmp 顶层只读快照(条目数与列表的 sha256),开工和收尾各做一次,写入 $EV/GATE_CONT2.txt。

### 0.2 写入方式(本轮收紧,U106)
- 仓库内的文本文件(报告、ERRATA、RULINGS、STATE、tsv、脚本、驱动源码)只用 write 或 edit 工具写。
- **其他写入(编译、链接、运行、复制、sha256 清单、门禁快照)一律分两步做:**
  ① 先用 write 工具把命令写成脚本文件 testing/d003/stage_s3r4c2/<名字>_c2.sh,
     所有重定向写在脚本里面,脚本第一段是
     `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`;
  ② 再运行 `sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/<名字>_c2.sh [参数]`。
  只有 git commit 可以写成内联:`sh testing/d003/safe_run.sh p05-s3r4c2 -- sh -c 'git add -- <文件…> && git commit -q -F "$EV/<提交信息文件>" > "$EV/<stdout 文件>" 2>&1' sh`
  (提交信息先用 write 写进 $EV;$EV 由 safe_run 设置,如不确定先读 safe_run.sh 核对)。
- 脚本与命令的文本中**一律不得出现** `/dev/null`(包括只读命令)、`2>/dev/null`、`&` 后台启动、heredoc、`sed -i`、
  `python3 -c`、`cat >`、`tee`,也不得出现任何以 / 开头又不在 $REPO 下的路径(包括占位路径)。
  需要忽略 stderr 时,把它重定向到 $EV/ 下的文件。
- 每写完一个脚本,用 read 工具从头读一遍再运行,确认没有上面任何一个禁止项。
- 写入目标只能在 $EV/、testing/d003/stage_s3r4c2/、checkpoints/p05/ 下。不改 testing/d003/ 下已提交的任何文件。
- 不做拒绝性测试或沙箱探测。长输出带 head/tail,或用 read 的 offset/limit。
- 禁止会写 .git 或改工作区的 git 命令(fsck、gc、prune、stash、checkout、switch、reset、clean)。
- **写入规则违反一次就停下**(U101、U103 重申),按两张表披露。

## 1. 用户裁决(先追加到 RULINGS.tsv,再写进 ERRATA ES3R4-15 之前的裁决块)
- U103:续1 的写入违规(safe_run 的 sh -c 内含 `2>/dev/null`,创建了仓库内空目录 testing/d003/stage_s3r4c1/)
  接受为已披露;续1 停止执行是正确的;续1 的开工门禁、记录修正与库哈希核对仍然有效,不作废。
- U104:续1 未提交的记录(RULINGS.tsv 追加 U96–U102、ERRATA ES3R4-10…14、续1 任务书存档、续1 报告)原样提交,
  不改内容;其中的两处错误用 ES3R4-15、ES3R4-16 追加更正。
- U105:空目录 testing/d003/stage_s3r4c1/ 删除,只能用 `rmdir`(目录非空时会失败,失败就停下报告),
  经 safe_run 的脚本运行;续2 使用 stage_s3r4c2/ 与 evidence/p05-s3r4c2/。
- U106:续2 起,除 git commit 外,所有经 safe_run 的写入都由先用 write 写好的脚本文件执行(见 §0.2);
  命令与脚本文本中不得出现 /dev/null。
- 续1 任务书 §1 的 U98–U102 继续有效。

## 2. 记录修正(先做;共两个提交)
- 提交 1(只提交续1 的原样记录,内容不改):ERRATA_S3R4.txt、registries/RULINGS.tsv、
  P05_S3R4_CLOSEOUT_CONT1.md、briefs/P05_S3R4_CONT1_BRIEF.md。
  提交信息:`P05-S3R4 CONT1 records as stopped (U104; content unchanged). awaiting user review`。
- 然后用 edit 追加,写完后作为提交 2(连同续2 任务书存档一起提交):
  · RULINGS.tsv 追加 U103–U106(status `生效`,来源写本任务书 §1)。
  · ERRATA 追加 U103–U106 裁决块,以及:
    ES3R4-15:更正 ES3R4-13。原文写"追加了一行",实际是清单(21:43:48Z)之后追加了两行:
      第 61 行(21:43:50Z,sha256sum -c 的 safe_run 记录)与第 62 行(21:44:41Z,提交命令);
      `head -n 60 safe_run.log` 的 sha256 与原清单记录一致。ES3R4-13 中的核对记录文件在续1 没有写入,
      本轮写为 $EV/SHA256SUMS_CHECK_p05-s3r4.txt(核对命令写在脚本里,先自己核实再写结论)。
    ES3R4-16:更正 ES3R4-11 最后一句"多边形部分由续1 §5 补做":续1 没有执行这一项(续1 在 §2 后停止);
      改由续2 补做,结果见 CLOSEOUT_CONT2。
    ES3R4-17:续1 的停止与 U103–U106(一句话说明,并引用续1 报告 §0、§5)。
  · 运行 U105 的 rmdir 脚本,记录前后的 `ls -d` 结果。
  提交信息:`P05-S3R4 CONT2 rulings U103-U106 and errata ES3R4-15..17; CONT2 brief archived. awaiting user review`。

## 3. 执行顺序与技术内容(沿用续1 任务书 §3–§6,以下为差异)
顺序:**(C 多边形)→(A)→(B)→(D)**。C 证明正常路径没变,先做;C 出现任何不同就停下,不进入注入运行。

### 3.1 共同前置
- 只读核对(结果写入 $EV/LIB_CHECK_C2.txt):F2 库 evidence/p05-s3r4/build/F2-plain/build/libS4.a 的 sha256 =
  c63d180aff6c5b5e443faefeb6de44abce430dafbb846db434ac15da85fbc185;F3 库 evidence/p05-s3r4/build_f3/plain/build/libS4.a 的 sha256 =
  abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de。不一致就停下。
  F2-dbg 库只用于 A 的 `info line` 佐证,同样记录 sha256。
- 本轮所有驱动都在 $EV/drivers/ 下重新链接,每个都记录 sha256。链接脚本从既有脚本复制到 stage_s3r4c2/ 并改名,
  只改输出目录和库路径;每个复制品都写一份与原件的 diff 到 $EV/,证明没有其他改动。

### 3.2 (C) 多边形无注入逐字节比较 —— 续1 §5
- 先按续1 §4 写出 poly 驱动 driver_s3r4c2_poly.cpp(从 stage_s4/driver_r6b_state.cpp 复制,只改 pattern 分支一处),
  并写出与原驱动的逐行 diff($EV/POLY_DRIVER_DIFF.txt),diff 只能有这一处。
- 预注册 $EV/REGISTRY_S3R4C2_C_POLY.tsv(写定后记录 sha256 与 UTC 时间,再开始运行):11 个模式 × NG 1、5、9 = 33 个组合;
  期望 F2 与 F3 的 call1–3 dump 全部 IDENTICAL,rc 对全部一致。F2 上的 rc 不要求为 0,如实记录。
- 链接方式与 S3R4 C 中的 state 驱动相同(链接 inject_r4_plan.cpp),写出链接选项的 diff。
- 结果表 $EV/RESULTS_S3R4C2_C_POLY.tsv。出现任何不同就停下。

### 3.3 (A) 806 与 1729 —— 续1 §3
- 内容同续1 §3(A1 映射 → 预注册 REGISTRY_S3R4C2_A.tsv → 36 次注入运行 + 6 次无注入对照)。
- gdb 与 addr2line 的命令写在 stage_s3r4c2/ 的 .gdb 或 .sh 文件里,经 safe_run 运行,输出到 $EV/a1map_<tree>_<combo>/。
- K 不能唯一确定就停下这一项(记"未完成",写清原因),继续 B 和 D。
- MISMATCH:两遍跑完后停下 A,不改期望,也不改修复;继续 B 和 D。

### 3.4 (B) 415 —— 续1 §4
- 内容同续1 §4。注入器 inject_s3r4c2_poly.cpp,用 --wrap=Pattern_DiscretizeCell 开窗;链接后用 nm 核对 __wrap_/__real_ 符号,
  结果写 $EV/NM_CHECK_POLY.txt。
- 前置核对(gdb 确认进入 POLYGON 分支;Mtot 与每次 n;n=12 的 [源码] 依据)全部完成后,再写预注册 REGISTRY_S3R4C2_B.tsv。
- 前置核对不满足(F2 不注入时 rc 不为 0,或者没有进入 POLYGON 分支):停下这一项,不得换几何体凑结果。
- MISMATCH 的处理同 A。

### 3.5 (D) 冒烟 —— 续1 §6
- 从 registries/s4r7/RESULTS_R7_{CTRL_SEAM,G2c,G1,G2a}_pass1_run7.tsv 中,每组按 point_id 排序取第一个和最后一个点,共 8 点;
  期望 = run7 的 class 与 rc1。先写 REGISTRY_S3R4C2_D.tsv,再运行。
- 普通驱动复制 stage_s4r7/link_drivers_s4r7.sh;CTRL_SEAM 复制 R7 中实际使用的 seam 链接或构建脚本
  (先读 R7 报告,确认用的是哪个)。只改库路径和输出目录,写出选项 diff = 0 的核对。
- 如果 CTRL_SEAM 需要先在 F3 上重新构建 seam 库,而这一步要用到已提交历史脚本之外的改动:不做,
  这一组记为"未完成(原因)",其余 6 点照常运行;不得用别的点替代。
- 报告里写"冒烟",不写"回归"。

### 3.6 U100 的 [源码] 说明
- 逐个列出 Pattern_DiscretizeCell 的 −1…−9:来源(文件:行号)、触发条件、经公共 API(S4_Layer_SetRegion*、Python、Lua)
  是否可达(只写 [源码],不运行)。写进 CLOSEOUT_CONT2 的一节,同时写成 $EV/U100_SOURCE_NOTE.md。

## 4. 收尾(沿用续1 任务书 §7,以下为差异)
- 红点状态表 $EV/RED_POINTS_STATUS_S3R4C2.tsv:806、415、RP-S3R4-1 只写"自检通过/未通过/未完成(F3:类别、rc1)",
  不写"已修好""已验证";528、1164、ES3R4-5(a)(b)、−1…−9 写 OUT_OF_SCOPE_D003 → S5(附 U90、U99、U100)。
- R8 回归清单的新增行:A、B 的注入点与无注入对照(tree=F3,带预注册行号),写入 $EV/R8_ADDITIONS_S3R4C2.tsv。
- STATE.md:当前轮次一栏改为"P05-S3 R4 续2:续1 在 §2 后停止(U103);续2 自检 C 多边形/A/B/D 结果……;
  下一步 P05-S4 R8 在 F3 上"。S3R4 那一长段压缩成一句,并链接 P05_S3R4_CLOSEOUT.md、CLOSEOUT_CONT1、CLOSEOUT_CONT2;
  关键数字表新增 S3R4 一行(含续1、续2);开放问题表新增 ES3R4-5(a)(b) 与 −1…−9 两行(→ S5);
  RNV1 一行的去向改为"R8(F3 上)"(U92)。整个文件保持一页以内。
- 小型表(预注册及其 sha256、RESULTS、A1_MAP、NM/LIB 核对、红点表、R8 新增行、门禁、SHA256SUMS_CHECK)
  复制到 registries/s3r4c2/,写 SHA256SUMS.txt,并逐个比对与原件一致。
- $EV/SHA256SUMS.txt 覆盖全部非二进制证据文件。写完后,只剩最后一次提交还会经 safe_run 写入;
  清单中把 safe_run.log 单列为"清单后追加",不参与校验,也不得事后再对它做 sha256sum -c 并写入失败结论。
- CLOSEOUT_CONT2 报告包括:门禁;记录修正(两个提交的哈希);C 多边形、A1 映射、A、B、D 的预注册 sha256、结果表与数字;
  U100 [源码] 说明;R8 新增行;待用户裁决的技术问题;违规两张表(没有就写"无");
  每一项写"完成/未完成(原因)/不可行(依据)",三者不得混用。
  结尾写"本轮已完成/未完成 S3R4 续2 范围,等待用户审核",附提交后真实的 git log -3 --oneline 与 git status --short(不得预填)。
- 最后一个提交的信息末尾写 `awaiting user review`。

## 5. 停止条件
- 门禁不符;需要修改 S4/ 或已提交的历史装置;写入规则被违反一次 → 整轮停止,直接写报告。
- 以下情况只停对应一项,其余项照常执行,在报告中写"未完成":A1 映射不能唯一确定 K;
  B 的前置核对不满足;A 或 B 出现 MISMATCH(两遍跑完后停);D 的 CTRL_SEAM 无法按原方式链接。
- C 多边形出现任何不同 → 不做 A、B、D 的注入运行,直接收尾并报告(说明正常路径被改变了)。
- "未完成"与"不可行"必须区分。
