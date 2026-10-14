# P05-S4 R8 M1a 续2c:新门禁 gate8、存量记录提交(A 段),映射 v3c(B 段)

你是 P05-S4 的验证执行者。本轮是 P05-S4 R8 M1a 的续2c,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议。
不修改 S4/。不修改 testing/d003/ 下已提交的文件。M1a、续1、续2、续2b 已生成但未提交的文件一律不改,在 A 段原样提交入库;更正只写新文件和 ERRATA_8(只追加)。
**本轮不运行 gdb,不运行任何驱动,不做注入,不做预注册。** 动态映射仍属续3a(U166)。
本轮分 A、B 两段,**每段结束各提交一次**。A 段提交是本轮的首要目标。工作量不是停止理由(U167)。

## 0. 开工
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2c.md`。
- 只读:AGENTS.md;STATE.md;`briefs/P05_S4R8_BRIEF_M1a_CONT2.md`(§4 映射规则)、`_CONT2b.md`;`registries/s4r8/ERRATA_8.txt`;`P05_S4R8_REPORT_M1a_CONT2.md`;
  `testing/d003/stage_s4r8/gate7_r8m1a3b.sh`、`recheck_s4r7_r8m1a3b.py`、`map_f2_f3_r8m1a3.py`、`copy_m1a_r8m1a3b.sh`、`prerun_log_r8m1.sh`;
  `evidence/p05-s4r8/GATE_R8_M1a3b_END.txt`、`LINEMAP_F2_F3_R8_M1a3.tsv`、`EXPECT_LINEMAP_R8_M1a3.txt`、`safe_run.log`(read 的 offset 读末尾)。
- 读完直接写脚本。证据目录沿用 `checkpoints/p05/evidence/p05-s4r8/`,已有文件不删、不改、不覆盖。
  本轮新文件名一律含 `r8m1a3c`(脚本、数据)或 `M1a3c`(证据、小表)。ERRATA_8 从 E8-47 起追加。本轮报告:`checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2c.md`(A、B 两段合写)。

## 1. 写入方式、内联命令、禁止项、停止规则
- shell 脚本首段逐字为
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`;Python 一律 `python3 -I -B`。
- **内联 bash 只允许 5 种形式**(其余一律写成脚本):
  (1) `date -u +%Y-%m-%dT%H:%M:%SZ; sh testing/d003/safe_run.sh p05-s4r8 -- <X>; date -u +%Y-%m-%dT%H:%M:%SZ`
      其中 <X> 只能是 `sh testing/d003/stage_s4r8/<文件>.sh <参数…>` 或 `python3 -I -B testing/d003/stage_s4r8/<文件>.py <参数…>`。
      **`sh -c`、grep、head、wc、awk、管道一律不得出现在 <X> 中**(U172)。
  (2) `date -u +%Y-%m-%dT%H:%M:%SZ; git status --short; date -u +%Y-%m-%dT%H:%M:%SZ`
  (3) `date -u +%Y-%m-%dT%H:%M:%SZ; git rev-parse HEAD HEAD:S4; date -u +%Y-%m-%dT%H:%M:%SZ`
  (4) `date -u +%Y-%m-%dT%H:%M:%SZ; sha256sum <仓库内文件…>; date -u +%Y-%m-%dT%H:%M:%SZ`(只有 sha256sum,不接 wc 或其他命令)
  (5) `date -u +%Y-%m-%dT%H:%M:%SZ; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date -u +%Y-%m-%dT%H:%M:%SZ`(只用于 /tmp 快照,本轮共 4 次:A 开工、A 收尾、B 开工、B 收尾)
  `mkdir` 只能出现在脚本首段或经 safe_run 的脚本里。
- **禁止项检查(U161,逐文件)**:每个脚本或数据文件运行前,用 grep 工具对这一个文件(path 填完整文件路径)搜索
  `/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp`,
  **必须 0 行**才能运行;记录的 grep_hits 照抄工具返回的行数,经 `prerun_log_r8m1.sh` 追加到 `$EV/PRERUN_CHECKS_R8_M1a.txt`。
  脚本、数据文件、ERRATA 文本中不写 /tmp 字面量,需要时写"根目录临时区"。
- **停止规则**:只有本任务书 §3、§5 列出的停止条件可以停。
  - A 段停止:不提交,报告写到停止处。
  - B 段停止:照常做 §6 的 B 段收尾门禁与提交,提交信息开头写 `P05-S4 R8 M1a cont2c (stopped at B§x): …`。
- **门禁自身操作错误的处理(U169)**:如果 gate8 的 FAIL 项是执行者自己的参数或命令错误(不是数据不符),同一模式允许用新输出名(加 `_R2` 后缀)重跑一次。
  子输出名由门禁输出名派生,不会被 U17 拒绝。重跑要在报告和 ERRATA(B 段追加)中披露。数据不符(哈希、HEAD、status 不在列表内)不得重跑,直接停。

## 2. 用户裁决(A 段门禁通过后追加;RULINGS 每行恰 5 列、4 个 TAB;第 2 列写"R8 M1a 续2c 任务书 §2",第 4 列写 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2c.md §2`,第 5 列写 `生效`)
- U168:续2b 部分接受。
  - 接受的部分:GATE_R8_M1a3b(FAILS=0);U160–U167、E8-37–E8-46 的追加(RULINGS 62722 字节 sha256 9bd490cc36d0735a310c5eea06a33ff0342707f826e1b8f0d3c8d01db9b47f68;ERRATA_8 34208 字节 sha256 60b592bb36b1530a4c8a02197f30a4fa257e7b73d90582d8972dc2363cdad91d5);映射 v3 的全部输出(作为停止记录,不改)。
  - 映射 v3 在 ⑬(r6_probe MISSING)及其连带的 ⑫ 处停止,是正确处理,没有改规则重跑;end 门禁 FAILS=1 时不提交,也是正确处理。
- U169:续2b end 门禁 FAILS=1 有两个原因。
  - (a) 执行者把当前快照的 sha256 填进了计数位;
  - (b) 规划缺陷:end 模式要求手填 4 个位置参数;recheck 子输出名写死,U17 拒绝覆盖,门禁无法重跑。
  - 处置:GATE_R8_M1a3b_END.txt 原样保留为停止记录。新门禁 gate8_r8m1a3c.sh 从开工门禁文件读取开工快照值;参数先校验格式再写文件;子输出名由门禁输出名派生;允许 §1 规定的一次自身错误重跑。
- U170:E8-43 确认。规划者只读核对:driver_r6b_state.cpp 第 73 行为 `extern "C" __attribute__((noinline)) void r6_probe(int k){`,a07b5ac 与 8d8202a 中相同。
  - 修正:识别函数头时,先把 `__attribute__((…))`(允许内含一层括号)替换为等长空格,再做正则匹配;花括号深度计算不变。
  - 自检增加驱动文件,并检查函数名不得是 `__attribute__`、`extern`、`static`、`inline`、`const` 之一。
  - 规划者只读模拟:5 个 S4 文件在两棵树中的函数表 0 行变化;驱动文件第 73–75 行变为 r6_probe。状态 INFLUENCED。
- U171:E8-42(c)(d) 确认。used_in_m1 改为三值:
  - BP_LINE:在下列文件中有 `break/tbreak <文件>:<行>`、`LineBP("<文件>:<行>`、`gdb.Breakpoint("<文件>:<行>` 形式的引用(正则同 v3 的 collect_citations):
    · `testing/d003/stage_s4r7`、`stage_s3r4c2`、`stage_s3r4c3` 下的 .gdb/.py;
    · `testing/d003/stage_s4` 下的 .gdb/.py,但只限文件名(整词)出现在上面三个目录或 `checkpoints/p05/registries/{s4r7,s3r4c2,s3r4c3}` 的 .py/.sh/.gdb/.tsv/.txt 中的那些;
  - REGISTRY_ONLY:不是 BP_LINE,但 `registries/{s4r7,s3r4c2,s3r4c3}` 下某个 .tsv 的非注释行同时含有该文件名和该行号(整词);
  - NO:两者都没有。
  - **stage_s4r8 与任何 r8m1 文件不在查找范围内(避免自引用)。** 列值写类别加最多 3 条 `文件:行`。
  - 规划者只读模拟:BP_LINE 4(S4.cpp:2413、fmm_PolBasisJones.cpp:192、fmm_FFT.cpp:90、fmm_kottke.cpp:94),NO 1(S4.cpp:4334),其余 26 行 REGISTRY_ONLY。状态 INFLUENCED。
  - EXPECT 每一个非注释行都必须被某个比较分支接收,否则记 UNPARSED,按 MISMATCH 计。
- U172:E8-47(02:29:41Z 内联 `mkdir`,目标在仓库内,已落盘,未经 safe_run)、E8-48(经 safe_run 的 `sh -c` 包裹,至少 4 次)、续2b 的非白名单内联只读命令(git show 管道、wc -c、awk 管道),都接受为已披露的表二事件。从本轮起按 §1 执行。
- U173:E8-49 记录错误。
  - (a) 复制脚本的通配 `STRIP_EQUIV_*_R8_M1a.*` 匹配不到 `strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv`(sha256 9aef51ef8864b72043993d594213925551636478a4205220d80b7d337a010825),主表没有进入 registries;报告 2.5"已复制"只对 SUMMARY 成立。
  - (b) 复制清单中 GATE_R8_M1a3b.txt 与 GATE_R8_M1a3b_END.txt 各出现两次,COPIED=35 实际对应 33 个不同文件。
  - 处置:A 段补复制主表;已存在的 `M1a/SHA256SUMS.txt` 不改,另写 `SHA256SUMS_M1a3c_A.txt`。
- U174:本轮分 A、B 两段:A = 门禁、裁决、补复制、存量记录提交;B = 映射 v3c 与第二次提交。续3a = 动态映射;续3b = 预注册、dry-run、M1b/M1c 运行器与 M1a 收尾(同 U166)。
- U175:续2b 报告的"待用户裁决"四项由 U169–U173 处理完毕。P05_S4R8_REPORT_M1a_CONT2.md 原样提交,不改。

同时追加到 ERRATA_8(新文件 `append_errata_r8m1a3c.txt`):
- E8-47:内联 mkdir(同 U172);
- E8-48:`sh -c` 包裹(同 U172);
- E8-49:STRIP_EQUIV 主表与复制计数(同 U173);
- E8-50:U169 的 (a)(b);
- E8-51:规划缺陷。
  - (a) 续2 任务书 U154(b) 的自检没有包含驱动文件,所以 E8-43 没有被自检发现;
  - (b) 续2 任务书 §4.1 的期望项没有规定统一的行格式,用"used_in_m1 NO"写进站点行,导致比较分支与 EXPECT 不一致(E8-42(d));
  - (c) U154(d) 的 used_in_m1 定义把 stage_s4r8 也纳入了查找,引起自引用。
- E8-52:U170、U171 的期望来自规划者只读模拟,状态 INFLUENCED。

## 3. A 段
### A1 门禁 gate8_r8m1a3c.sh(新文件;gate7 不改)
- 调用形式(参数个数固定):
  `sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 <OUT> start <TC> <TS>`
  `sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 <OUT> endA <START_FILE> <TC> <TS>`
  `sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 <OUT> startB <TC> <TS>`
  `sh testing/d003/stage_s4r8/gate8_r8m1a3c.sh p05-s4r8 <OUT> endB <STARTB_FILE> <TC> <TS>`
- **写任何文件之前**先做以下校验,任一不符就 exit 2,不写文件:
  - `<OUT>` 匹配 `^GATE_R8_M1a3c_[A-Za-z0-9_]+\.txt$`,且该文件不存在;
  - `<TC>` 全是数字,`<TS>` 是 64 位小写十六进制;
  - `<START_FILE>`/`<STARTB_FILE>` 存在,模式行与本模式配对,最后一行是 `FAILS=0`。
  end 模式从该文件的 `RECORD TMP_COUNT_START`、`RECORD TMP_SHA256_START` 行读出开工值,与本次 TC、TS 比较。
- recheck:复制 `recheck_s4r7_r8m1a3b.py` 为 `recheck_s4r7_r8m1a3c.py`。只改两处:接受名改为正则 `^S4R7_RECHECK_GATE_R8_M1A3C_[A-Z0-9_]+\.tsv$`;标签文字。
  gate8 用 `S4R7_RECHECK_` 加上 `<OUT>` 去掉 `.txt` 后转大写,再加 `.tsv` 作为子输出名(例如 GATE_R8_M1a3c_START.txt → S4R7_RECHECK_GATE_R8_M1A3C_START.tsv),要求 fails=0。复制品的 diff 写进报告。
- 每个模式都检查:HEAD:S4 = 6cff923a02baf19e01966b2339755cbf3a5deeef;a07b5ac:S4 = e124925f5b242486a913b813fa181664f665b048;8d8202a:S4 = 6cff923a…;
  `git diff --name-only a07b5ac 8d8202a -- S4` 恰为 4 个文件(同 gate7);判定器 sha256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb;
  REGISTRY_S3R4C3_D.tsv、registries/s4r8 清单(U150(a))、s3r4c5 清单,方法同 gate7;s4r7 清单走上面的 recheck。
- start 模式:
  - HEAD = e2589cbc2b470ae88286d582ee62699e7c0d9e4c;
  - RULINGS 全文 = 9bd490cc…(62722 字节),且 HEAD 版本是它的字节前缀;ERRATA_8 全文 = 60b592bb…(34208 字节),前 13990 字节 = 72dc6aed…1551,前 28653 字节 = 16024140…32b0;
  - PRERUN_CHECKS_R8_M1a.txt 前 3869 字节 = 774e150033105804eb680c9da9c83bbe9af813d987811ef3ed88754e46abaa51;
  - 数据文件 `gate_hashes_r8m1a3c.txt`(用 write,每行"sha256 两个空格 路径")逐行比对。内容:
    ```
    1fc08a1f5dbf1340d3500979980a4f808b141515c8e1814c23da796e7deb0a0f  checkpoints/p05/P05_S4R8_REPORT_M0.md
    2b1c2de19a39c7e44c6cea75e55963bb5995849ee1d19a77d1ad7b2248676c04  checkpoints/p05/P05_S4R8_REPORT_M1a.md
    bccf1fd9755eae04dc8dee8383f843c54cb802b3b7c3106967a6fc6ca9520658  checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md
    d7b80006b29117e1592a2dc02520a883993c333b89d81ed4a81dd396b9cf188a  checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2.md
    a84da018b782f52e73a533d79d2224058e48d924bf817df869a94e5656686ec3  checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md
    debf29e1ff978450cb01e85120d347de05aeb469830ebe70689933628673bb76  checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md
    c24a1bbc76197a2fdac1cb428bc6e4def957f98cf8f768f2ddc5a0fa12b6efa3  checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2.md
    3228eead42ed2e8440c3d0b1bcf2b2df5af7653febe3fcc458ae8921642208e3  checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2b.md
    026868ba4e2ff0a658e85c69c34755e16a64f875fe6332f47a508a168894eb1a  checkpoints/p05/registries/s4r8/M1a/SHA256SUMS.txt
    f1296937c03b3d47fd23c0a42268ce107da254653642f752c780743e24f75c60  checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a3b_END.txt
    a49f42b3acb4b91ad741bc59d675f97cb021ae702f1b4339cf46e6554ef197bb  checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a3b.txt
    380dc53a9a0d4caa704e296599746141fe23e2a0731782aec5bf63f3180e6b11  checkpoints/p05/evidence/p05-s4r8/LINEMAP_F2_F3_R8_M1a3.tsv
    8f666c5eb1959c4a63792a1e3ac48627a195fb620ab749c93604ab644dc730c1  checkpoints/p05/evidence/p05-s4r8/EXPECT_LINEMAP_R8_M1a3.txt
    3e8a08ff72d52ffe71e3839658d5bce41ebf22bf315183085c11c8b36a28d3df  checkpoints/p05/evidence/p05-s4r8/LINEMAP_CHECK_R8_M1a3.txt
    8c20bfe5a73cca723a6d2b7b0a5b20623dbca2f7711e25d4068932323e67800f  checkpoints/p05/evidence/p05-s4r8/FUNC_BP_SYMBOLS_R8_M1a3.tsv
    7d368083fd973a6ffccd8195055dfecef522e5a190755bdc9498149e72f97df0  checkpoints/p05/evidence/p05-s4r8/PARSER_SELFCHECK_R8_M1a3.tsv
    25b9999f8fa75ad2ceb46702fa014fba34d87046a72ee42d1e731c0e69e5d92b  checkpoints/p05/evidence/p05-s4r8/LINEMAP_V2_V3_DIFF_R8_M1a3.txt
    59e5ab75d0056edc399c2ebb9e19f0c0e75e0aaf630952c0a0635e0ccbe660bc  checkpoints/p05/evidence/p05-s4r8/FINAL_GIT_R8_M1a3b.txt
    ba67d4e0b1c0c07b909ee7a4745aa0d3e2049266fc41d9fe45dcf9297657ca00  checkpoints/p05/evidence/p05-s4r8/SHA256SUMS_M1a.txt
    9aef51ef8864b72043993d594213925551636478a4205220d80b7d337a010825  checkpoints/p05/evidence/p05-s4r8/strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv
    db2e7a2efe29792949b7e8a30f2727a777b9e3638debb662816353ef0696c545  testing/d003/stage_s4/driver_r6b_state.cpp
    ```
  - 存量聚合哈希(在脚本内计算):
    `git ls-files -o --exclude-standard -- testing/d003/stage_s4r8 | LC_ALL=C sort | grep -v -i r8m1a3c` 共 43 行,将这些路径 `xargs sha256sum | sha256sum` 得 c7010af5fb76af5b1502d786c4ed0025c08eaf2681d935761886c506886cacd1;
    `git ls-files -o --exclude-standard -- checkpoints/p05/registries/s4r8/M1a | LC_ALL=C sort | grep -v -i -e m1a3c -e '/STRIP_EQUIV_R8_M1a\.tsv$'` 共 34 行,聚合得 907954c694d3bc2e4cf7a7b916025efe81d09beb346949af30f67439de2349bc。
    行数与聚合哈希都要比较,并用 RECORD 记下文件列表。
  - status 允许列表 `gate_allow_r8m1a3c_start.txt` 内容(用 write,# 开头为注释):
    ```
     M checkpoints/p05/P05_S4R8_REPORT_M0.md
     M checkpoints/p05/STATE.md
     M checkpoints/p05/registries/RULINGS.tsv
     M checkpoints/p05/registries/s4r8/ERRATA_8.txt
    ?? checkpoints/p05/P05_S4R8_REPORT_M1a.md
    ?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT1.md
    ?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2.md
    ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md
    ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT1.md
    ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2.md
    ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2b.md
    ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT2c.md
    ?? checkpoints/p05/registries/s4r8/M1a/
    PREFIX ?? testing/d003/stage_s4r8/
    ```
  - RECORD TMP_COUNT_START、TMP_SHA256_START。
- endA 模式(在 A 段提交前运行):
  - HEAD 仍为 e2589cb;RULINGS 前 62722 字节 = 9bd490cc…;ERRATA_8 前 34208 字节 = 60b592bb…;PRERUN 前 3869 字节不变;
  - gate_hashes 表中除 STATE 以外的各行不变;两项存量聚合不变;
  - status 只含 `gate_allow_r8m1a3c_endA.txt` 中的项(= start 列表加 `?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2c.md`);
  - /tmp 快照等于开工值。
- 停止条件 A①:start 或 endA 有数据类 FAIL。

### A2 追加
- 新建 `append_rulings_r8m1a3c.tsv`(U168–U175,8 行)、`append_errata_r8m1a3c.txt`(E8-47–E8-52)、`append_r8m1a3c.sh`。
- 前置检查:RULINGS = 9bd490cc…/62722 字节,ERRATA_8 = 60b592bb…/34208 字节,两者都以换行结尾。
- 后置检查:前缀哈希不变;新增 RULINGS 行恰 8 行,每行 NF=5,id 依次为 U168–U175。结果写入 `APPEND_R8_M1a3c.txt`,FAILS=0。
- 必须在 start 门禁 FAILS=0 之后进行。停止条件 A②:前置或后置检查不过。

### A3 补复制与 A 段记录
- `copy_m1a_r8m1a3c_A.sh`:把下列文件复制到 `registries/s4r8/M1a/`,逐个 cmp:
  `strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv`、`GATE_R8_M1a3c_START.txt`(若有 _R2 也复制)、`S4R7_RECHECK_GATE_R8_M1A3C_START.tsv`、`APPEND_R8_M1a3c.txt`。
  复制清单先去重;已有文件不覆盖(存在则拒绝)。不改已有的 `SHA256SUMS.txt`。
- STATE.md 用 edit 修改。当前轮次一行改为:
  "P05-S4 R8 M1a(准备,续2c):A 段存量记录提交(续1/续2/续2b;映射 v3 停止记录;GATE_R8_M1a3b_END FAILS=1 为停止记录,U169);B 段映射 v3c 待做;动态映射属续3a(U166)"。
  关键数字表中 S4R8 M1a 那一行把"(续2b,停止未提交)"改为"(续2b 停止;续2c A 段已提交)"。保持一页以内。
- 报告 `P05_S4R8_REPORT_M1a_CONT2c.md` 先写 A 段:门禁(含 /tmp 快照原文与 UTC);U168–U175;E8-47–E8-52;补复制;STATE 变更;违规两张表;内联命令自查(逐条原文与前后 UTC)。
- 然后运行 gate8 endA。

### A4 提交 commit_rec_r8m1a3c_A.sh(endA FAILS=0 后运行)
脚本依次做:
1. 确认 endA 门禁文件最后一行为 FAILS=0。
2. 把 endA 门禁文件复制到 `registries/s4r8/M1a/` 并 cmp。
3. 在该目录写 `SHA256SUMS_M1a3c_A.txt`,覆盖本段新增的全部文件(包括 endA 副本),然后 `sha256sum -c` 全部 OK。
4. 重新计算两项存量聚合,与 endA 记录一致。
5. 用 `git status --porcelain --untracked-files=all` 列出全部变更路径。每个路径必须以 `checkpoints/p05/` 或 `testing/d003/stage_s4r8/` 开头,否则拒绝并退出;然后逐个 `git add -- <路径>`(不用 -A,不用 `.`)。
6. 提交,提交信息:
   `P05-S4 R8 M1a records (cont1+cont2+cont2b, map v3 stopped at conditions 12/13): dbg strip equivalence closes E8-9, drivers, F2-F3 line map v3 stop record, gate7 end FAILS=1 kept as stop record (U169), new gate8; rulings U137-U175; errata to E8-52; M0 report wording (U137). awaiting user review`
7. 把 `git log -3 --oneline`、`git rev-parse HEAD HEAD^`、`git log -1 --format=%s`、`git status --short` 写入 `$EV/FINAL_GIT_R8_M1a3c_A.txt`。
   期望:HEAD^ = e2589cb,status 为空。

在对话中原样贴出 FINAL_GIT_R8_M1a3c_A.txt。

## 4. B 段开工
- 用形式 (5) 取 /tmp 快照,然后运行 gate8 startB。检查:
  - HEAD^ = e2589cbc2b470ae88286d582ee62699e7c0d9e4c;`git log -1 --format=%s` 以 `P05-S4 R8 M1a records (cont1+cont2+cont2b` 开头;`git status --short` 为空;
  - RULINGS、ERRATA_8 工作区文件与 HEAD 版本逐字节相同;
  - RECORD HEAD_B(完整哈希)。
- startB 有 FAIL 时:属于自身错误的,按 §1 重跑一次;属于数据不符的,停止(B①),报告追加后结束本轮(A 段已提交)。

## 5. B 段:映射 v3c
5.1 先写期望 `EXPECT_LINEMAP_R8_M1a3c.txt`,记录 sha256 与 UTC(形式 (4)),然后才运行映射。
    第一行 `status INFLUENCED`;出处写"续2c 任务书 U170、U171;v3 停止记录;规划者只读模拟"。
    **每个非注释行必须是下列 6 种格式之一**:
    ```
    COUNT <STATUS> <n>                 (STATUS ∈ MISSING AMBIGUOUS MODIFIED_BY_FIX SAME_LINE SHIFTED)
    CHECK PARSER_SELFCHECK_BAD <n>  |  CHECK DIFF_OFFSET_DISAGREE <n>
    USED_COUNT <BP_LINE|REGISTRY_ONLY|NO> <n>
    SITE <file> <F2行> F3 <F3行> <STATUS> <F3函数>
    USED <file> <F2行> <BP_LINE|REGISTRY_ONLY|NO>
    SYMBOL <名> F2 <行> F3 <行> PRESENT
    ```
    内容:
    ```
    COUNT MISSING 0
    COUNT AMBIGUOUS 0
    COUNT MODIFIED_BY_FIX 3
    COUNT SAME_LINE 7
    COUNT SHIFTED 21
    CHECK PARSER_SELFCHECK_BAD 0
    CHECK DIFF_OFFSET_DISAGREE 0
    USED_COUNT BP_LINE 4
    USED_COUNT REGISTRY_ONLY 26
    USED_COUNT NO 1
    SITE S4/pattern/pattern.c 415 F3 418 MODIFIED_BY_FIX shape_get_intersection_area_quad_st
    SITE S4/pattern/pattern.c 528 F3 545 SHIFTED shape_get_intersection_area
    SITE S4/fmm/fmm_FFT.cpp 98 F3 101 MODIFIED_BY_FIX FMMGetEpsilon_FFT
    SITE S4/fmm/fmm_kottke.cpp 102 F3 105 MODIFIED_BY_FIX FMMGetEpsilon_Kottke
    SITE S4/S4.cpp 2413 F3 2422 SHIFTED Simulation_ComputeLayerModes
    SITE S4/fmm/fmm_PolBasisJones.cpp 192 F3 192 SAME_LINE FMMGetEpsilon_PolBasisJones
    SITE S4/S4.cpp 4334 F3 4343 SHIFTED S4_Simulation_GetFieldPlane
    SITE S4/S4.cpp 4210 F3 4219 SHIFTED S4_Simulation_GetFieldPlane
    SITE S4/fmm/fmm_FFT.cpp 90 F3 90 SAME_LINE FMMGetEpsilon_FFT
    SITE S4/fmm/fmm_kottke.cpp 94 F3 94 SAME_LINE FMMGetEpsilon_Kottke
    SITE testing/d003/stage_s4/driver_r6b_state.cpp 73 F3 73 SAME_LINE r6_probe
    USED S4/S4.cpp 4334 NO
    USED S4/S4.cpp 2413 BP_LINE
    USED S4/fmm/fmm_PolBasisJones.cpp 192 BP_LINE
    USED S4/fmm/fmm_FFT.cpp 90 BP_LINE
    USED S4/fmm/fmm_kottke.cpp 94 BP_LINE
    SYMBOL Simulation_GetLayerSolution F2 1778 F3 1787 PRESENT
    SYMBOL Simulation_ComputeLayerModes F2 2250 F3 2259 PRESENT
    SYMBOL S4_Simulation_GetFieldPlane F2 4210 F3 4219 PRESENT
    SYMBOL r6_probe F2 73 F3 73 PRESENT
    ```
5.2 `map_f2_f3_r8m1a3c.py`:复制 `map_f2_f3_r8m1a3.py` 后修改,原件不改。**只允许下面 6 类改动**:
    (1) 输出名与文件说明;
    (2) U170 的 `__attribute__` 处理(只作用于函数头识别);
    (3) 自检:PARSED_FILES 加入 `testing/d003/stage_s4/driver_r6b_state.cpp`,两棵树各检查文件末尾深度为 0、最小深度不小于 0、第 73 行为 r6_probe;所有被解析文件的函数表中不得出现 `__attribute__`、`extern`、`static`、`inline`、`const`,出现即 BAD;
    (4) U171 的 used_in_m1 三值规则(列名不变,值写类别加最多 3 条引用);
    (5) EXPECT 的比较器:按 5.1 的 6 种格式解析;不能解析的行记为 `UNPARSED` 并计入 MISMATCH;每种格式的每一行都要在 LINEMAP_CHECK 中有一行 MATCH/MISMATCH;
    (6) 差异文件改为 v3 对 v3c:逐站点比较 F3 行、函数、状态、used_in_m1,只记录不判。预期只有 driver_r6b_state.cpp:73 的函数列(`__attribute__`→`r6_probe`)和各行的 used_in_m1 列有变化。
    站点表、状态规则、改名表、U147 核对、diff 偏移算法都不改。
    输出:`LINEMAP_F2_F3_R8_M1a3c.tsv`、`PARSER_SELFCHECK_R8_M1a3c.tsv`、`FUNC_BP_SYMBOLS_R8_M1a3c.tsv`、`LINEMAP_CHECK_R8_M1a3c.txt`、`LINEMAP_V3_V3C_DIFF_R8_M1a3c.txt`。
    另写 `diff_map_r8m1a3c.sh`,把 `git diff --no-index` 对 v3 与 v3c 两个脚本的差异写入 `MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt`。报告中逐段说明每处差异属于哪一类。
5.3 运行一次。停止条件:
    - B②:自检 BAD 大于 0;
    - B③:LINEMAP_CHECK 有 MISMATCH 或 UNPARSED;
    - B④:DISAGREE 大于 0;
    - B⑤:符号核对有 MISSING 或 MULTIPLE。
    出现时不改规则、不重跑,转 §6 收尾并提交。
5.4 映射中 used_in_m1=BP_LINE 的 `文件:行号` 断点,报告写明:M1b/M1c 使用 F3 行号的复制品,不改原件。

## 6. B 段收尾与提交(未停止时在 §5 完成后做;停止时在停止处做)
- 复制到 `registries/s4r8/M1a/`:全部 `*_M1a3c.*` 映射小表、`EXPECT_LINEMAP_R8_M1a3c.txt`、`MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt`、`GATE_R8_M1a3c_STARTB*.txt`、对应的 `S4R7_RECHECK_GATE_R8_M1A3C_STARTB*.tsv`。
  逐个 cmp 后写 `SHA256SUMS_M1a3c_B.txt`,`sha256sum -c` 全部 OK。
- `$EV/SHA256SUMS_M1a3c.txt`:覆盖本轮(A、B 两段)全部新的非二进制证据。
- 如果有 §1 的门禁自身错误重跑或新的表二事件:用 `append_errata_r8m1a3c_B.txt` 与 `append_r8m1a3c_B.sh` 追加 E8-53 起的条目,前置检查以 A 段提交后的 ERRATA_8 为准;没有事件就不追加。
- STATE.md 用 edit 修改。当前轮次写:
  "P05-S4 R8 M1a(准备,续2c):存量已提交(A 段);静态映射 v3c 31 行(MODIFIED_BY_FIX 3、SAME_LINE 7、SHIFTED 21、AMBIGUOUS 0、MISSING 0;自检 BAD 0;DISAGREE 0;符号 4/4 PRESENT;used_in_m1 BP_LINE x/REGISTRY_ONLY y/NO z);下一步 M1a 续3a 动态映射(待用户审核)"。
  停止时如实写停在哪一项。关键数字表的 S4R8 M1a 行同步更新。
- 报告追加 B 段:startB 门禁;EXPECT(sha256 与 UTC);脚本差异分类;自检;LINEMAP_CHECK 逐项;符号;used_in_m1 三类计数;v3→v3c 差异;STATE 变更;违规两张表;内联命令自查;待用户裁决(没有就写"无")。
  每项只写"完成""未完成(原因)""不可行(依据)"之一。
- 用形式 (5) 取 /tmp 快照,运行 gate8 endB(`<STARTB_FILE>` 填 startB 门禁文件)。检查:
  - HEAD 等于 startB 记录的 HEAD_B;HEAD:S4 不变;RULINGS 与 HEAD 版本相同;ERRATA_8 的 HEAD 版本是工作区文件的字节前缀;
  - status 只含 `gate_allow_r8m1a3c_endB.txt` 中的项:` M checkpoints/p05/STATE.md`、` M checkpoints/p05/P05_S4R8_REPORT_M1a_CONT2c.md`、` M checkpoints/p05/registries/s4r8/ERRATA_8.txt`、`PREFIX ?? testing/d003/stage_s4r8/`、`PREFIX ?? checkpoints/p05/registries/s4r8/M1a/`,并且所有 `??` 路径都含 `m1a3c`(不区分大小写);
  - /tmp 快照等于 startB 记录的值。
  endB FAILS=0 后运行 `commit_rec_r8m1a3c_B.sh`,结构同 A4:复制 endB 副本、补进 SHA256SUMS_M1a3c_B.txt 并 -c、路径前缀检查、逐个 add、提交。提交信息:
  `P05-S4 R8 M1a cont2c: F2-F3 line map v3c (attribute-aware parser with driver self-check, used_in_m1 BP_LINE/REGISTRY_ONLY/NO without self-reference, EXPECT parse guard); call-sequence map deferred to cont3a (U166). awaiting user review`
  (停止时开头改为 `P05-S4 R8 M1a cont2c (stopped at B§x): …`)
- 提交后写 `$EV/FINAL_GIT_R8_M1a3c_B.txt`(内容同 A4)。期望:HEAD^ 为 A 段提交,HEAD^^ = e2589cb,status 为空。在对话中原样贴出。
  提交后不再修改任何已跟踪文件。

## 7. 不停但要记录的情形
- REGISTRY_ONLY 或 NO 站点的行号变化;v3→v3c 差异中 used_in_m1 列的变化。
- 范围以外的事一律不做:不写续3a 的计数族、gdb 命令文件、callseq 草稿。
- 结尾只写"本轮已完成 R8 M1a 续2c 范围,等待用户审核"或"本轮未完成 R8 M1a 续2c 范围,等待用户审核"。
