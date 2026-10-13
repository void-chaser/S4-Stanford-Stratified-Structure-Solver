# P05-S4 R8 M0 重启(第 2 次开工):门禁按 U128 更正后重新开工

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 R8 的 M0,不是新阶段,不得出现 P05-S6。不得宣布任何阶段完成或签收;报告与 STATE 不写签收建议(U83)。
**不修改 S4/ 下任何文件。**

## 0. 本任务书与原任务书的关系
- 原任务书 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md`(首次开工时存档,未跟踪,sha256 `868dc6820e17e7245527cca132c4d9d0f28bbad2af5b15ffebd775ddbae80408`)**不改**。
  它的 §0.2、§0.3、§1(U121–U127)、§3–§7 **继续有效**;只有本任务书点名的条款被替换或补充。两者冲突时以本任务书为准。
- 第一步:用 write 把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md`。
- 先读(只读):AGENTS.md、STATE.md、原任务书全文、`registries/s4r7/ERRATA_7.txt` 中的 E7-12(约 :94–97)、E7-25(约 :220–224)、E7-36(约 :428–431)、
  首次开工的 `evidence/p05-s4r8/GATE_R8_M0.txt`、`testing/d003/stage_s4r8/gate_r8.sh`。
- 证据目录仍是 `evidence/p05-s4r8/`。首次开工留下的文件(GATE_R8_M0.txt、PRERUN_CHECKS_R8_M0.txt、safe_run.log)**不删、不改**;
  PRERUN_CHECKS_R8_M0.txt 与 safe_run.log 继续追加。
- `gate_r8.sh` 是首次开工已运行的脚本,**原样保留、不再运行、不修改**(它的收尾模式要求 HEAD=3ab5680、status 为空,不适用)。
  本轮门禁用新脚本 `gate2_r8.sh` 与 `check_s4r7_manifests_r8.py`。`prerun_log_r8.sh` 继续使用。

## 1. 用户裁决(追加到 RULINGS.tsv,status `生效`,来源写"R8 M0 重启任务书 §1";顺序为 U121–U127(原任务书 §1)之后接 U128、U129;同时写在 ERRATA_8.txt 开头)
- U128:原任务书 §0.1 中"registries/s4r7/SHA256SUMS*.txt 全部 `sha256sum -c` OK"一条是**规划者错误**,它没有考虑 R7 已披露的 E7-12、E7-25、E7-36。
  该条改为本任务书 §2.2 的分类核对。R7 的原件(清单、ERRATA_7、*_std.txt)一律不改,也不新建更正清单。
- U129:首次开工(2026-10-13T03:00:33Z)按原 §0.1 停止,做法正确,不算执行者违规。首次开工报告中有两处要更正:
  (a) `SHA256SUMS_M2a.txt`、`SHA256SUMS_M2pre.txt` **格式没有损坏**(两列标准格式)。不通过的只有 ERRATA_7、../RULINGS.tsv、../../STATE.md 三行,
      原因是它们记录的是写清单时的历史快照(E7-25);只有 `SHA256SUMS_M2b_run7.txt`、`SHA256SUMS_M2b_run7prep.txt` 有多余的 `copied` 列(E7-36)。
  (b) `S4_DIFF` 失败的原因是 `sort` 受 locale 影响,改动集合本身正确;新门禁用 `LC_ALL=C sort`。
  首次开工的 gate_r8.sh、GATE_R8_M0.txt 作为停止记录保留。以上记为 ERRATA_8 的 E8-1。

## 2. 开工门禁(替换原 §0.1)

### 2.1 gate2_r8.sh(新文件)
- 用法:`sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate2_r8.sh p05-s4r8 <输出名> <start|end> <tmp_count> <tmp_sha256> [<start_tmp_count> <start_tmp_sha256>]`
  开工输出 `GATE_R8_M0_R2.txt`,收尾输出 `GATE_R8_M0_R2_END.txt`(已存在就拒绝)。每项一行 PASS/FAIL,末行 `FAILS=n`。
- start 模式检查:
  1. HEAD = 3ab56801e697910bdff9fbe6056807c2e41841b5;HEAD:S4 = 8d8202a:S4 = 6cff923a02baf19e01966b2339755cbf3a5deeef;a07b5ac:S4 = e124925f5b242486a913b813fa181664f665b048。
  2. `git diff --name-only a07b5ac 8d8202a -- S4/ | LC_ALL=C sort | tr '\n' ' '` = `S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c `(末尾一个空格)。
  3. judge_d003.py sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb;REGISTRY_S3R4C3_D.tsv sha256 = a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5。
  4. 首次开工文件未变:briefs/P05_S4R8_BRIEF_M0.md = 868dc6820e17e7245527cca132c4d9d0f28bbad2af5b15ffebd775ddbae80408;
     evidence/p05-s4r8/GATE_R8_M0.txt = 1c8ecdd6e8d1301fa986fa0025008a22f8a23c2c71c29068f2bf772f6e6d9725;
     stage_s4r8/gate_r8.sh = 8c997618d68da8802b6465d5b1318c730da28acc61dff6e14f58064d0cc934b7;
     stage_s4r8/prerun_log_r8.sh = a079a35e47e1243551fcee28d51e358bc31ba24ba0e6325c159805ae6ad417ca。
  5. `git status --short | grep -v 'testing/d003/stage_s4r8/' | LC_ALL=C sort` 恰好是两行:
     `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md` 与 `?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md`。
     (若 git 把两个文件折叠显示,按实际输出逐字记录;只要未跟踪项限于这两个文件和 stage_s4r8/,就判 PASS,并在 E8 中说明。)
  6. registries/s3r4c5:`sha256sum -c SHA256SUMS.txt` 全部 OK。
  7. registries/s4r7:调用 `python3 -I -B testing/d003/stage_s4r8/check_s4r7_manifests_r8.py`(§2.2),它的输出 `$EV/S4R7_MANIFEST_CHECK_R8_R2.tsv`
     中 FAIL 行数必须为 0;gate2 记一行 `S4R7_MANIFESTS fails=0`。
  8. /tmp 顶层快照(调用者用内联 `ls -A /tmp | wc -l` 与 `ls -A /tmp | sha256sum` 取数后传入)。
- end 模式检查(替换原 gate_r8.sh 不适用的条件):
  1. `git rev-parse HEAD^` = 3ab56801e697910bdff9fbe6056807c2e41841b5,且 `git log -1 --format=%s` 等于 §3 的记录提交信息;HEAD:S4 仍为 F3 树。
  2. `git status --short` 的每一行路径都在 `checkpoints/p05/` 或 `testing/d003/stage_s4r8/` 下;已跟踪且被修改(` M`)的文件只能是 `checkpoints/p05/STATE.md`;
     不得出现 `S4/` 或 `testing/d003/` 下的其他路径。
  3. 第 2.1 start 中的第 1(不含 HEAD 一项)、2、3、6、7 项重做一遍。
  4. /tmp 快照与开工值相同(条目数、sha256)。

### 2.2 check_s4r7_manifests_r8.py(新文件,python3 -I -B;只读 git 与仓库文件,只写 `$EV/S4R7_MANIFEST_CHECK_R8_R2.tsv`,已存在就拒绝)
在 `registries/s4r7/` 目录内核对。每项一行:清单名、检查项、期望、实际、PASS/FAIL。用 subprocess 调 `sha256sum -c` 与 `git show`(只读),不得 shell=True。
- (a) 下列 8 份直接 `sha256sum -c`,每行必须 `: OK`:
  SHA256SUMS_M1.txt、SHA256SUMS_M2bprep.txt、SHA256SUMS_M2b_run6prep.txt、SHA256SUMS_M2b_run7_std.txt、SHA256SUMS_M2b_run7prep_std.txt、
  SHA256SUMS_M3_prep.txt、SHA256SUMS_M3.txt、SHA256SUMS_M3_closeout.txt。
- (b) 下列 5 份**不做整份 -c**(E7-12/E7-25/E7-36)。先核对清单文件本身的 sha256 等于下表(证明原件未改),再按规则核对:

| 清单 | 自身 sha256 | 写入提交 | 规则 |
|---|---|---|---|
| SHA256SUMS.txt | 0f8f06be5bdbbed833ba09199ec79ae4b0813ff32750d16d1d9af0ca45db0a36 | 8a71b3f459b210119bbc12f71aab879f15c46c54 | 去掉 ERRATA_7 行,其余 10 行 -c OK;ERRATA_7 前缀 N=5378 |
| SHA256SUMS_M2pre.txt | 40380dd10223101e8b63adb9af5143e22ead818f629b14a640de4f8eda646fe1 | db9264887add276b68fa93e3c19f20efa5fe7262 | 去掉 3 行快照行,其余 13 行 -c OK;ERRATA_7 前缀 N=18030;RULINGS 前缀 N=16066;STATE 按提交版本 |
| SHA256SUMS_M2a.txt | f03268ee014db0a2ac064bc9a5e641584abeec4de50aa1581c5c96ba5c7525f3 | 6319a3ca75cb73d30171d87d2b944540116cb018(733d588 追加 3 行,快照行未变) | 去掉 3 行快照行,其余 16 行 -c OK;ERRATA_7 前缀 N=19434;RULINGS 前缀 N=16066;STATE 按提交版本 |
| SHA256SUMS_M2b_run7.txt | 3e189f3820263c8f1c01d62aa57cb5bb43462be30d2d810b5a0cd7fd092bfe56 | — | 每行前两列与 SHA256SUMS_M2b_run7_std.txt 逐行相同(13 行) |
| SHA256SUMS_M2b_run7prep.txt | 29ea95057b5942358b4ee1704d6fd4adb61c44f9ea7301b81faf3390f715ad44 | — | 每行前两列与 SHA256SUMS_M2b_run7prep_std.txt 逐行相同(3 行) |

  "快照行"指文件名字段恰为 `ERRATA_7.txt`、`../RULINGS.tsv`、`../../STATE.md` 的行。
  - 前缀规则(ERRATA_7、RULINGS 只追加):同时满足三项:① 清单中记录的哈希 = sha256(当前文件的前 N 字节);
    ② = sha256(`git show <写入提交>:<仓库路径>`);③ `git show` 那一版的字节数 = N。
  - STATE 规则(STATE 会被整体改写):清单中记录的哈希 = sha256(`git show <写入提交>:checkpoints/p05/STATE.md`)。不与当前 STATE 比较。
  - 去掉快照行后的 -c 输入:先写到 `$EV/tmp/<清单名>.nonlive`,再在 registries/s4r7/ 目录内对它执行 -c(cwd 设为该目录,-c 的参数用该临时文件的绝对路径)。
- (c) 目录中的 SHA256SUMS*.txt 必须恰好是上述 13 份,多了或少了都判 FAIL。
- 期望全部 PASS。任一 FAIL:gate2 判 FAIL,停下报告(这才是真实不符)。

## 3. 记录提交(替换原 §2 的文件清单与提交信息;其余照原 §2)
- RULINGS.tsv 追加 U121–U129;ERRATA_S3R4.txt 末尾追加 ES3R4-31(按原 U121);新建 registries/s4r8/ERRATA_8.txt,开头写 U121–U129,然后写:
  - E8-1:首次开工停止与更正(U129 全文要点;引用 GATE_R8_M0.txt 的 sha256 与 safe_run.log 行号)。
  - E8-2(观察,不改原件):E7-12 写"SHA256SUMS_M2.txt (M2) lists ERRATA_7 and STATE.md",但 registries/s4r7/ 中没有 SHA256SUMS_M2.txt,
    实际起这个作用的是 SHA256SUMS_M2pre.txt 与 SHA256SUMS_M2a.txt。
- commit_rec_r8.sh 的 git add 只列出:checkpoints/p05/registries/RULINGS.tsv、checkpoints/p05/ERRATA_S3R4.txt、checkpoints/p05/registries/s4r8/ERRATA_8.txt、
  checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md、checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md、
  testing/d003/stage_s4r8/{gate_r8.sh,gate2_r8.sh,check_s4r7_manifests_r8.py,prerun_log_r8.sh,commit_rec_r8.sh}。
  先把 `git status --short` 写入 `$EV/status_before_rec_r8.txt`。提交信息:
  `P05-S4 R8 M0 records (restart): rulings U121-U129, errata ES3R4-31 and ERRATA_8 (E8-1 first-start stop, E8-2); gate corrected per U128; briefs archived. awaiting user review`

## 4. 之后的步骤
- 原 §3(构建与驱动)、§4(D 冒烟)、§5(F2↔F3 无注入等价)、§6(收尾)、§7 照原任务书执行,只做以下替换:
  - 收尾门禁用 `gate2_r8.sh … GATE_R8_M0_R2_END.txt end …`,在 copy_registries_r8.sh 之前运行。
  - registries/s4r8/ 的复制清单中,`GATE_R8_M0*.txt` 包括 GATE_R8_M0.txt(首次)、GATE_R8_M0_R2.txt、GATE_R8_M0_R2_END.txt;另加 S4R7_MANIFEST_CHECK_R8_R2.tsv。
  - 报告的"门禁"一节分别写首次开工(停止,FAILS=6,U128/U129 已裁决)与重启开工的结果。
  - 原 §6 STATE 中"开工基线 HEAD 写 3ab5680"保持不变。
- 运行前检查、写入方式、停止条件照原 §0.2、§0.3。新增的 gate2_r8.sh、check_s4r7_manifests_r8.py、commit_rec_r8.sh 运行前都要用 grep 工具查禁止项,
  并经 prerun_log_r8.sh 记录。注意:Python 中的临时路径写成 `os.path.join(EV, "tmp", ...)`,不要出现字面量 `/tmp`。
- 只读的内联命令不得含 `>` 字符(包括 `2>&1`);需要输出的核对一律写成脚本,经 safe_run 运行。
- 结尾只写"本轮已完成 R8 M0 范围,等待用户审核"或"本轮未完成 R8 M0 范围,等待用户审核"。
