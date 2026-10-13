# P05-S3 R4 续4(S3R4 的续轮,不是新阶段):收尾。只做记录、核对与提交,不编译、不运行 S4 驱动

你是 P05-S3 的收尾执行者。本轮记为 S3R4 续4,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议(U83)。
**本轮不修改 S4/ 下任何文件,不编译、不链接、不运行任何 S4 驱动或 gdb。**自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。

先读(按顺序):AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md、
checkpoints/p05/briefs/P05_S3R4_CONT3_BRIEF.md、checkpoints/p05/ERRATA_S3R4.txt(ES3R4-15…24)、
checkpoints/p05/registries/s3r4c3/(全部,只读)、checkpoints/p05/evidence/p05-s3r4c3/D_STATUS_C3.txt(只读)。

- 证据目录:checkpoints/p05/evidence/p05-s3r4c4/(新目录)。p05-s3r4/、p05-s3r4c2/、p05-s3r4c3/、p05-s4r7/ 只读引用,不往里面写任何东西。
- 新脚本目录:testing/d003/stage_s3r4c4/(文件名带 c4)。小型结果表:checkpoints/p05/registries/s3r4c4/。
- 报告:checkpoints/p05/P05_S3R4_CLOSEOUT_CONT4.md。勘误在 ERRATA_S3R4.txt 末尾追加,从 ES3R4-25 起编号,不改已有条目。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S3R4_CONT4_BRIEF.md。

## 0. 门禁与写入方式

### 0.1 开工门禁(任一不符就停下报告)
- HEAD = bee9420;`git rev-parse HEAD:S4` = 6cff923a02baf19e01966b2339755cbf3a5deeef(F3);
  judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb。
- `git status --short` 只允许以下 3 行(本任务书的存档是第 4 行,属于预期):
  `?? checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md`、`?? checkpoints/p05/registries/s3r4c3/`、`?? testing/d003/stage_s3r4c3/`。
- /tmp 顶层只读快照:用内联只读命令 `ls -A /tmp | wc -l` 与 `ls -A /tmp | sha256sum` 取数,
  再作为参数传给 gate_c4.sh 写入 $EV/GATE_CONT4.txt(开工)与 $EV/GATE_CONT4_END.txt(收尾)。

### 0.2 写入方式(在 U106 与续3 任务书 §0.2 的基础上,本轮再收紧)
- 仓库内的文本文件(报告、ERRATA、RULINGS、STATE、tsv、脚本)只用 write 或 edit 工具写。
- **内联 bash 命令只允许两类,并且文本中不得出现 `>` 字符(包括 `2>&1`、`>>`):**
  ① 只读的 git 命令:`git status --short`、`git log …`、`git rev-parse …`、`git show --stat …`;
  ② `sh testing/d003/safe_run.sh p05-s3r4c4 -- sh testing/d003/stage_s3r4c4/<名字>_c4.sh [参数]`。
  只读核对(查看文件、计数、比对)一律用 read / grep / glob 工具,或者写进脚本经 safe_run 运行。**不写内联的"核对用"重定向命令。**
- 其他所有写入(sha256 清单、diff、复制、门禁、git add/commit)都要先用 write 写成 testing/d003/stage_s3r4c4/<名字>_c4.sh,
  再按 ② 运行。git commit 也写进脚本(参照 testing/d003/stage_s3r4c3/commit_rec_c3.sh 的写法)。
- shell 脚本的第一段必须**逐字**是:
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
- 脚本与命令文本中一律不得出现:`/dev/null`(含 Python 的 DEVNULL、devnull)、`&` 后台启动、heredoc、`sed -i`、`python3 -c`、
  `cat >`、`tee`,以及任何以 / 开头又不在 $REPO 下的路径(包括 /tmp 和任何占位路径)。
- **运行前检查**(每个脚本、每次修改后都做):用 grep 工具在 testing/d003/stage_s3r4c4/ 中搜索正则
  `/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |(^|[^V])/tmp`
  (这个正则不会命中标准首段里的 `$EV/tmp`)。结果必须为 0 行才可以运行。
  把每次检查的结论(脚本名、UTC、命中行数 0)写进 $EV/PRERUN_CHECKS_C4.txt(经 prerun_log_c4.sh 写入)。
  未运行的草稿在检查中被发现并改正,不算违规;违规以"含禁止项的脚本或命令被执行"为准。
- 写入目标只能在 $EV/、testing/d003/stage_s3r4c4/、checkpoints/p05/ 下。不改 testing/d003/ 下已提交的任何文件,
  也不改 testing/d003/stage_s3r4c3/ 下的文件(它们在 §2 原样提交)。
- 不做拒绝性测试或沙箱探测。长输出带 head/tail,或用 read 的 offset/limit。禁止写 .git 或改工作区的 git 命令。
- **写入规则违反一次就停下**,按两张表披露。

## 1. 用户裁决(先追加到 RULINGS.tsv,status `生效`,来源写本任务书 §1;再在 ERRATA 中 ES3R4-25 之前写裁决块)
- U111:续3 的写入违规(收尾核对命令含 `> /tmp_nonexistent_placeholder 2>/dev/null`,被只读文件系统拒绝,未落盘)接受为已披露;
  续3 停止是正确的。续3 的门禁、记录提交 bee9420、A(36/36 MATCH,对照 6/6)、B(44/44 MATCH,对照 12/12)、B_MAP、
  U100 [源码] 说明、红点状态表与 R8 新增行仍然有效,不作废。根因之一是任务书允许内联核对命令,
  且 grep 正则会命中标准首段(规划者疏漏);续4 起按 §0.2 处理。
- U112:接受 ES3R4-25(任务书 n=12 是算术错误,正确值 36 = 4×3×3,pattern.c:418;实测 36)。
  B 跑 44 次(fft NG1 的 win:Mfirst 与 win:1 为同一点,标 DUPLICATE、不运行)属于预注册内的设计,接受。
- U113:**D(8 点冒烟)不在 S3R4 内补做,改为 P05-S4 R8 的第 0 步**(在 F3 全量回归之前运行),U98 中关于 D 的部分相应修改;
  A、B 仍按 U98 记为 S3R4 自检。REGISTRY_S3R4C3_D.tsv(sha256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5)
  作为 R8 第 0 步的输入预注册保留,不改。
- U114:续3 未提交的文件**原样提交,不修改**:P05_S3R4_CLOSEOUT_CONT3.md、registries/s3r4c3/(全部)、testing/d003/stage_s3r4c3/(全部)。
  其中 stage_s3r4c3/apply_seam_f3_c3.sh 是从未运行的错误草稿,标 DO NOT RUN(原因见 ES3R4-26(b))。
- U115:续3 缺的交付物(注入器与链接脚本的 diff、D 预注册记录、二进制 sha256、证据清单)由续4 以只读计算补齐,
  写入 p05-s3r4c4/,不写回 p05-s3r4c3/。
- U98–U110 继续有效(U98 按 U113 修改)。

## 2. 记录提交(先做,一个提交)
- RULINGS.tsv 追加 U111–U115。
- ERRATA 追加 U111–U115 裁决块,以及:
  · ES3R4-25:任务书 §3.2 的 n=12 → 36(U112)。
  · ES3R4-26:更正 D_STATUS_C3.txt 与续3 报告 §3.3 的 D 说明(原文件不改)。逐条写下面四点,
    **每条先用 read/grep 工具核对文件:行号,再写进去**:
    (a) R7 的 CTRL_SEAM 用 plain seam 库与 seam 驱动:build_seam_plain_s4r7.sh(-O3 -march=native)
        + link_seam_drivers_r7.sh(driver_d003.cpp + inject_d003.cpp,-O1);驱动选取见 run_m2b_all_r7.py 的 driver_for 与 seam_driver_name。
        续3 报告中的 build_seam_s4r7.sh / link_r6b_seam_r7.sh 是 G6 用的 -O0 -g seam,不是 CTRL_SEAM。
    (b) R7 的 seamF 树 = apply_seam_r2.py --families A,C,D 加上 apply_seam_b2.py(evidence/p05-s4r7/SEAM_DIFF_F_vs_F2_R7.txt 第 1 行;
        seam_r7/apply-*-seamF-B2.txt);fmmret 树 = apply_seam_r5_fmmret.py --tree A。
        草稿 apply_seam_f3_c3.sh 漏了 B2,而且注释写的"family B2 not included in R7"是错的 → DO NOT RUN。
    (c) D 的 8 点中,G2a 的 R4-ACF1-F-F、R4-SI02-F-F2 用 seamF 驱动(G2a 的 seam 规则),所以 D 的构成是
        普通驱动 4 点(G1 2 点用 d003-plain,G2c 2 点用 d003plan-plain)+ seam 驱动 4 点(CTRL_SEAM 2 点、G2a 2 点)。
    (d) G1、G2c 用 plain 驱动,不是 dbg;环境由 matrix_r2.build_env 构造(FMM_MODE、S4FMM_NG、S4FMM_INJECT、S4FMM_NTH,
        t4/ 路线另加 S4FMM_TWICE=slab;matrix_r2.py:98–109),输入是 ADD_v3 的 nth 列;CTRL_SEAM 只设 FMM_MODE 与 S4FMM_NG。
    结论句:以上供 R8 第 0 步使用;续3 没有运行 D,这些更正不影响任何已有结果。
  · ES3R4-27:B_MAP_C3.tsv 的 polygon_breakpoint_hits 列实际记录的是窗口 malloc 次数(无 -g,没有 tri 行断点);
    只能读作"窗口 malloc 次数(替代)",不是断点证据。原表不改。
  · ES3R4-28:续3 报告 §10 的说明"本报告未提交"由 U114 处理;续3 报告 §3.3 关于 D 的原因由 ES3R4-26 更正(原文不改)。
- 一起提交(脚本 commit_rec_c4.sh):RULINGS.tsv、ERRATA_S3R4.txt、briefs/P05_S3R4_CONT4_BRIEF.md、
  P05_S3R4_CLOSEOUT_CONT3.md、registries/s3r4c3/、testing/d003/stage_s3r4c3/。
  提交前在脚本中把 `git status --short` 写进 $EV/status_before_rec_c4.txt;git add 只列出上述路径,不用 `git add -A` 或 `git add .`。
  提交信息(先 write 到 $EV/COMMIT_MSG_CONT4_REC.txt):
  `P05-S3R4 CONT4 rulings U111-U115, errata ES3R4-25..28; CONT3 report, registries s3r4c3 and stage_s3r4c3 committed unchanged (apply_seam_f3_c3.sh DO NOT RUN). awaiting user review`

## 3. 补齐续3 的交付物(只读计算,输出到 $EV = p05-s3r4c4)
用一个脚本 supp_c4.sh 生成以下文件。每个输出先判断"已存在就拒绝";diff 的返回码 1 表示"有差异",不是失败,把 rc 记在文件末尾。
- DIFF_INJECT_C3.txt:`diff -u testing/d003/stage_s3r4/inject_s3r4_init.cpp testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp`
- DIFF_LINK_C3.txt:`diff -u testing/d003/stage_s3r4/link_init_s3r4.sh testing/d003/stage_s3r4c3/link_poly_inj_c3.sh`
- PREREG_D_RECORD_C3.txt:evidence/p05-s3r4c3/REGISTRY_S3R4C3_D.tsv 的 sha256 与行数,以及 `stat -c %y` 的修改时间
  (注明"文件修改时间,不是登记记录;续3 未写登记记录")。
- BINARIES_C3.tsv(name、path、sha256):F2 plain 库、F3 plain 库、F3 dbg 库(evidence/p05-s3r4/build_f3/dbg/build/libS4.a)、
  init-F2 与 init-F3 驱动(p05-s3r4c2)、polyinj-F2 与 polyinj-F3 驱动(p05-s3r4c3/drivers/)。
  前五项要与续3 门禁的已知值比对,写 SAME/DIFFERENT(已知值见续3 任务书 §0.1;F3 dbg 库是首次记录,写 FIRST_RECORD)。
- SHA256SUMS_P05-S3R4C3.txt:evidence/p05-s3r4c3/ 下全部非二进制证据文件的标准格式清单
  (每行"哈希 两个空格 相对 p05-s3r4c3 的路径",不混入其他行)。
  排除 safe_run.log、tmp/、f3_export/、drivers/*/driver;排除项列在单独文件 SHA256SUMS_P05-S3R4C3_EXCLUDED.txt 里。
  随后在脚本中 `cd` 到 p05-s3r4c3 运行 `sha256sum -c`,结果写进 $EV/SHA256SUMS_P05-S3R4C3_CHECK.txt(在 p05-s3r4c3 目录内校验,不在仓库根校验)。
- 用 read 工具检查两个 diff:DIFF_INJECT 应只有窗口符号、跨调用累计、计数查询函数和打印格式的差异;
  DIFF_LINK 应只有标准首段、wrap 符号、输入输出路径的差异。把差异摘要写进报告 §3。
  如果出现上述以外的差异,如实列出,不改任何文件。

## 4. 收尾
- STATE.md(用 edit,整个文件保持一页以内):
  · 当前轮次:"P05-S3 子轮次 S3R4 续4(收尾):A 36/36 MATCH、B 44/44 MATCH(F3 REPORTED_FAILURE rc1=20)、D 按 U113 转入 R8 第 0 步;
    下一步 P05-S4 R8 在 F3 上"。开工基线 HEAD 写 bee9420。
  · S3R4 关键数字行补续3 的数字:A 36/36、对照 6/6;B 44/44、对照 12/12;Mfirst(fft NG1 = 1,其余 = 64);窗口 malloc n = 36。
  · 开放问题表:"S3R4 自检 A 注入运行、B、D"一行改为"D 冒烟 8 点 → R8 第 0 步(U113;更正见 ES3R4-26)";
    "806、415、RP-S3R4-1"一行改为"注入自检通过(F3,A/B);修复后验证 → R8";
    "−1…−9"一行把"[源码] 说明未写"改为"[源码] 说明已写(registries/s3r4c3/U100_SOURCE_NOTE.md)"。不新增重复行。
  · 证据位置补 p05-s3r4c3、p05-s3r4c4 与对应的 registries 目录。
- 小型表复制到 registries/s3r4c4/(脚本 copy_registries_c4.sh):GATE_CONT4*.txt、PRERUN_CHECKS_C4.txt、DIFF_*_C3.txt、
  PREREG_D_RECORD_C3.txt、BINARIES_C3.tsv、SHA256SUMS_P05-S3R4C3*.txt、status_before_rec_c4.txt。
  写 SHA256SUMS.txt(标准格式),并在 registries/s3r4c4/ 目录内用 `sha256sum -c` 校验,结果写进 $EV。
- $EV/SHA256SUMS.txt 覆盖 p05-s3r4c4 的全部非二进制文件,标准格式;safe_run.log 不进清单,在说明文件中写"清单后追加,不参与校验"。
- 报告 P05_S3R4_CLOSEOUT_CONT4.md 包括:门禁;记录提交的哈希;U111–U115;ES3R4-25…28 的要点;§3 补齐结果与 diff 摘要;
  BINARIES 比对;STATE 的变更摘要;违规两张表(没有就写"无");待用户裁决的技术问题(没有就写"无")。
  每一项只写"完成""未完成(原因)""不可行(依据)"三者之一。结尾只写"本轮已完成 S3R4 续4 范围,等待用户审核"
  或"本轮未完成 S3R4 续4 范围,等待用户审核"其中一句,并附提交后真实的 `git log -3 --oneline` 与 `git status --short`(不得预填;
  由于报告本身要进入提交,提交后的这两项输出写进 $EV/FINAL_GIT_C4.txt,报告中引用该文件,并在对话中贴出)。
- 最后一个提交(脚本 commit_final_c4.sh)包括:STATE.md、ERRATA(如有追加)、P05_S3R4_CLOSEOUT_CONT4.md、registries/s3r4c4/、
  testing/d003/stage_s3r4c4/。提交信息:
  `P05-S3R4 CONT4 closeout: CONT3 deliverables completed read-only (diffs, binaries, manifests), D moved to R8 step 0 (U113), STATE updated. awaiting user review`
  提交后 `git status --short` 应为空;不为空就在对话中说明原因。

## 5. 停止条件
- 门禁不符;需要修改 S4/、已提交的历史装置或 stage_s3r4c3/;写入规则被违反一次 → 整轮停止,直接写报告。
- §3 中的 BINARIES 出现 DIFFERENT,或者 SHA256SUMS_P05-S3R4C3 校验不全部 OK:不停,如实记录,在报告的"待用户裁决"中列出。
- "未完成"与"不可行"必须区分。
