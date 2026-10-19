# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。S5R5/S5R6 门禁结果见各自报告附录 C；
> S5R7 门禁结果见 P05_S5R7_REPORT.md 附录 C（门禁后追加），本文件不预写 S5R7 门禁结果。

## 1 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r7） | 0358a06ee41f0b78984834bfdb758dd1a793296c（P05-S5 R6 (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S5 已由用户签收（带范围声明；S5 见 P05_S5_SIGNOFF.md 与 U391） |
| 当前轮次 | P05 交付轮 REL-R4（rel-r4：原版 S4 / 当前三方对照 + MPI + C API 对照；不是 P05 新阶段，S1–S5、REL-R1、REL-R2、REL-R3 历史不改；门禁结果见 P05_RELR4_REPORT.md 附录 C） |
| P05 交付轮 | REL-R1（rel-r1；修复后完整原有功能非破坏性验证；门禁结果见 P05_RELR1_REPORT.md 附录 C）、REL-R2（rel-r2；产品分支构建与上传前审查；门禁结果见 P05_RELR2_REPORT.md 附录 C）与 REL-R3（rel-r3；推送 4 个 ref 并开 Draft PR；门禁结果见 P05_RELR3_REPORT.md 附录 C）；REL-R4（rel-r4；原版 S4 / 当前三方对照 + MPI + C API 对照；门禁结果见 P05_RELR4_REPORT.md 附录 C） |

## 2 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| S5R3 | 裁决 U372–U377；勘误 ES5-6..8；D016 MATCH=33 MISMATCH=0 FLAKY=0；E2E 25 注入 + 17 对照；make test NO_NEW_FAILURE（unit_count=265）；独立重判缺失、readiness GAP=2、end 门禁 8 项 FAIL（见 R3 附录 C） | P05_S5R3_REPORT.md |
| S5R4 | 裁决 U378–U385；勘误 ES5-9..14；独立重判 DIFFS=0（E2E 42 点 SAME，D016 33 行为点 SAME + ROOT_CAUSE_RC NOT_JUDGED_SOURCE_RECORD）；S5R3 的 8 项门禁 FAIL 全部消解（数据 sha 不变）；readiness GAP=0；S5R3 registry 覆盖 26/26；试跑 139/139。更正（R5）：正式 end 门禁唯一 1 项 FAIL 为检查器字符串缺陷 ES5-15，FINAL_STATUS=INCOMPLETE（P05_S5R4_REPORT.md 附录 C）；R5 在 R4 冻结数据上的重判见 RECHECK_STAGING_S5R5.tsv | P05_S5R4_REPORT.md；registries/s5r4/ |
| S5R5 | 裁决 U386–U390；勘误 ES5-15/16；同类缺陷静态普查 SWEEP_ROWS=139、SELF_BRANCH_ROWS=2、VACUOUS=0；R4 冻结数据重判：修正逻辑成立、R4 原逻辑 not_staging；重判阳性对照 4/4；就绪审计见 READINESS_S5R5.tsv；end 门禁 36/36 FINAL_STATUS=COMPLETE（P05_S5R5_REPORT.md 附录 C） | P05_S5R5_REPORT.md；registries/s5r5/ |
| S5R6 | 无用户 P05-S5 签收原文：任务书第 2 节跳过，U391 未写，P05_S5_SIGNOFF.md 未创建；勘误 ES5-17（三条文字更正：(a) R5 表一命令管道符转义、(b) POSCTRL_GATE_S5R5.txt 只在证据目录交付、registries/s5r5 为 12 项、(c) R5 附录 A 的 COUNTS 重复）；R5 报告只追加附录 D（前 95 行 sha 不变）；入口同步 PROJECT_ROADMAP.md 与 ISSUE_REGISTRY.md；门禁结果见 P05_S5R6_REPORT.md 附录 C | P05_S5R6_REPORT.md；registries/s5r6/ |
| S5R7 | 用户给出 P05-S5 签收原文：checkpoints/p05/P05_S5_SIGNOFF.md §2 逐字照录（原文 sha256 c7af2fb2…；S1–S5 五行签收表）；RULINGS.tsv 追加 U391（5 字段，旧前缀 sha 不变）；STATE/ROADMAP/ISSUE 入口同步；转出项保持 OPEN；P05 五个正式阶段全部由用户签收，P06 可启动；门禁结果见 P05_S5R7_REPORT.md 附录 C | P05_S5R7_REPORT.md；registries/s5r7/ |
| REL-R1 | P05 交付轮（rel-r1）：修复后完整原有功能非破坏性验证（与 B 对照）；关键计数 SAME=317；BOTH_FAIL=12（均为既有失败）；SKIP_DECLARED=5；NEW_FAIL=0；DIFF=0；FLAKY=0；unit_count=265；各类别计数与 11 个既有失败例外清单见报告正文，门禁结果见报告附录 C | P05_RELR1_REPORT.md；registries/rel-r1/ |
| REL-R2 | P05 交付轮（rel-r2）：产品分支 p05/d003-fft-error-propagation 于独立克隆构建（2 个提交，HEAD 8e4c014，S4 树 589e15eb；仅新增 doc/P05_D003_SUMMARY.md）；V1–V6 全部与预注册一致（V5 只记录：build/S4 与 libS4.a 与 REL-R1 F4 逐字节 SAME）；免注入可达路径未找到，产品分支不含 D003 专用测试；两个附注标签与分支引用已建（待 REL-R3 推送）；上传前体积审查 A 新增 blob 3065 个共 46.1 MiB、无 ≥50 MB/≥100 MB blob，P 11 个共 0.3 MiB；敏感信息命中（只记录不改写）A：/srv/nvme/ 5789 次/155 文件、/home/ 24 次/11 文件、用户名 26 次、邮箱 12 次，P：仅上游作者邮箱 10 次；证据目录 11.38 GiB；门禁结果见报告附录 C | P05_RELR2_REPORT.md；registries/rel-r2/ |
| REL-R3 | P05 交付轮（rel-r3）：按 U393 顺序推送 4 个 ref——产品分支 8e4c014、归档分支 4607e96、标签对象 ef925cde（peel 3de6d8b）与 b42c4c16（peel c88bf30）；R1–R8 SAME（R9 空工作区由 end 门禁复测）；fork 内 Draft PR #17（OPEN、Draft、base master、commits=2、changedFiles=11）；远端克隆 HEAD 8e4c014、S4 589e15eb，make test rc=0、单元 265、无失败；补扫 token/密钥 0、无 ≥50 MB blob；门禁结果见报告附录 C | P05_RELR3_REPORT.md；registries/rel-r3/ |
| REL-R4 | P05 交付轮（rel-r4）：原版 S4 U（上游 7fd00a2）/ 当前 F4 / 未修复基线 B 三方对照 + MPI + C API 对照；U/B/F4 各为独立克隆（U 网络克隆，B/F4 本地 --revision 克隆）；C API 程序 capi_fig12_relr4.c；关键计数 T1 SAME=27 IMPROVED=2 BOTH_FAIL=10 REGRESSION=0 FLAKY=1 DIFF_WITHIN_TOL=3 DIFF_ATTRIBUTED=6；B-vs-F4 复现 SAME=38 BOTH_FAIL=11；T2 参考 9/12；MPI 三树均 With MPI support=3、MPI 一致性 12/12；T4 spec 参考 PASS=3、阳性对照 PASS=3；unit_count=265；门禁结果见报告附录 C | P05_RELR4_REPORT.md；registries/rel-r4/ |

## 3 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入 25 行的最终处置 | 落位（已转出/已登记/已关闭） | 本表为唯一入口 | checkpoints/p05/P05_S5_OPEN_ITEMS.tsv |
| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U369） | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv |
| R-P05-01 / R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U366/U370） | ISSUE_REGISTRY；registries/s5r2/ERRATA_S5.txt |
| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt |
| S5R3 遗留（独立重判缺失、readiness GAP、registry 清单不完整、8 项门禁 FAIL） | 已消解（R4） | S5R4 独立重判/recheck/readiness/registry 补齐 | P05_S5R4_REPORT.md 附录 B；registries/s5r4/ |
| R4 正式 end 门禁唯一 FAIL（检查器字符串缺陷，ES5-15） | 已重判（R5，R4 冻结数据只读） | U386/U388；R5 门禁不重跑 R4 门禁 | RECHECK_STAGING_S5R5.tsv；registries/s5r5/ |
| R5 报告文字瑕疵（ES5-17 三条） | 已更正（文字，不影响任何判定） | R6 追加勘误 ES5-17 与 R5 报告附录 D | registries/s5r2/ERRATA_S5.txt；P05_S5R5_REPORT.md 附录 D |
| S5 签收 | 已签收（U391） | 用户签收原文见 P05_S5_SIGNOFF.md §2；P05 收口，P06 可启动 | RULINGS.tsv U391；P05_S5_SIGNOFF.md |

## 4 证据位置

- **P05-S5 R7（s5r7）**：证据 checkpoints/p05/evidence/p05-s5r7/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r7/；报告 P05_S5R7_REPORT.md（门禁结果见附录 C）；签收文件 P05_S5_SIGNOFF.md；裁决 U391。
- **P05-S5 R6（s5r6）**：证据 checkpoints/p05/evidence/p05-s5r6/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r6/；报告 P05_S5R6_REPORT.md；勘误 ES5-17 见 registries/s5r2/ERRATA_S5.txt 与 P05_S5R5_REPORT.md 附录 D。
- **P05-S5 R5（s5r5）**：证据 checkpoints/p05/evidence/p05-s5r5/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r5/（含 r4_final/）；报告 P05_S5R5_REPORT.md；签收范围声明草稿 v3 P05_S5_SIGNOFF_DRAFT_v3.md（历史，未签收）。
- **P05-S5 R4（s5r4）**：证据 checkpoints/p05/evidence/p05-s5r4/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r4/（历史）；报告 P05_S5R4_REPORT.md；草稿 v2 P05_S5_SIGNOFF_DRAFT_v2.md（历史，未签收）。
- **P05-S5 R3（s5r3）**：证据 checkpoints/p05/evidence/p05-s5r3/（只读，sha 不变）；报告 P05_S5R3_REPORT.md；草稿 v1 P05_S5_SIGNOFF_DRAFT.md（历史）。
- 裁决总表 registries/RULINGS.tsv（S5R7 追加 U391）；S5 勘误 registries/s5r2/ERRATA_S5.txt（末条 ES5-17，本轮未改）；R4 终版 ERRATA 快照 registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt。

- **P05 交付轮 REL-R2（rel-r2）**：证据 checkpoints/p05/evidence/p05-rel-r2/（SHA256SUMS.txt；含产品分支独立克隆 prod/ 与验证克隆 verifyclone/，均不入 git）；小表 checkpoints/p05/registries/rel-r2/；报告 P05_RELR2_REPORT.md（门禁结果见附录 C）；产品分支引用 p05/d003-fft-error-propagation；标签 p05-signed-20261019、p05-rel-r1-20261019。
- **P05 交付轮 REL-R3（rel-r3）**：证据 checkpoints/p05/evidence/p05-rel-r3/（SHA256SUMS.txt；remoteclone/ 不入 git）；小表 checkpoints/p05/registries/rel-r3/；报告 P05_RELR3_REPORT.md；4 个远端 ref 已推送，Draft PR #17。
（本文件由 s5r7_state.py 在正式链中生成）


（REL-R1 行由 relr1_state.py 于 2026-10-19T04:09:58Z 追加；S1–S5 内容未改）

（REL-R2 行由 relr2_state.py 于 2026-10-19T05:06:14Z 追加；S1–S5 与 REL-R1 的历史数字未改，只补 REL-R1 行计数）

（REL-R3 行由 relr3_state.py 于 2026-10-19T05:24:44Z 追加；S1–S5、REL-R1、REL-R2 的历史数字未改）
- **P05 交付轮 REL-R4（rel-r4）**：证据 checkpoints/p05/evidence/p05-rel-r4/（SHA256SUMS.txt；含上游 U 克隆 upstream/S4 与 B/F4 独立克隆 trees/，均不入 git）；小表 checkpoints/p05/registries/rel-r4/；报告 P05_RELR4_REPORT.md（门禁结果见附录 C）。

（REL-R4 行由 relr4_state.py 于 2026-10-19T09:30:59Z 追加；S1–S5、REL-R1、REL-R2、REL-R3 的历史数字未改）