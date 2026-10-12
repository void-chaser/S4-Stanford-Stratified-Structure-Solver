# P05-S3 R4 续2 报告(S3R4 的续轮,非新阶段):**中途停止(写入规则违规,U106)**

**状态:本轮未完成 S3R4 续2 范围。** 已完成:开工门禁、记录修正两个提交(`45d17d5`、`d64c552`)、U105 空目录删除、C(多边形无注入逐字节比较)、A1 映射(K 唯一确定)、A 的预注册(注入运行前写定)。**未完成:A 的注入运行、B、D。** 未完成的原因是本轮违反写入规则(U106)一次,按任务书 §5 停止;不是不可行。
本轮未宣布任何阶段完成或签收;P05-S3、P05-S4 未签收;报告与 STATE 中不写签收建议(U83)。自检不是修复后验证;修复后验证由 P05-S4 R8 在 F3 上完成。**本轮未修改 S4/ 下任何文件。**

任务书:`checkpoints/p05/briefs/P05_S3R4_CONT2_BRIEF.md`(已存档,提交 `d64c552`)。

---

## 0. 门禁

| 项 | 实测 | 结果 |
|---|---|---|
| HEAD(开工) | `0b1b4a3` | 通过 |
| `HEAD:S4` | `6cff923a02baf19e01966b2339755cbf3a5deeef`(F3) | 通过 |
| judge_d003.py sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` | 通过 |
| `git status --short`(开工) | 4 行(ERRATA、RULINGS、CONT1 报告、CONT1 任务书),与任务书一致 | 通过 |
| `testing/d003/stage_s3r4c1` | 存在,空 | 通过 |
| `/tmp` 顶层(开工) | 0 条目;listing sha256 `e3b0c442…b855` | 通过 |
| 门禁文件 | `evidence/p05-s3r4c2/GATE_CONT2.txt` | 已写 |
| `/tmp` 顶层(收尾) | 见 §10 | 见 §10 |

---

## 1. 记录修正(两个提交)

| 提交 | 哈希 | 内容 |
|---|---|---|
| 1 | `45d17d5` | `P05-S3R4 CONT1 records as stopped (U104; content unchanged). awaiting user review`:ERRATA、RULINGS、CONT1 报告、CONT1 任务书(原样,未改内容) |
| 2 | `d64c552` | `P05-S3R4 CONT2 rulings U103-U106 and errata ES3R4-15..17; CONT2 brief archived. awaiting user review`:RULINGS U103–U106;ERRATA ES3R4-15…17 及 U103–U106 裁决块;续2 任务书存档;`testing/d003/stage_s3r4c2/` 脚本 |

- U105:`testing/d003/stage_s3r4c1/` 经 `rmdir` 删除(`evidence/p05-s3r4c2/RMDIR_C1_U105.txt`:删除前 `ls -d` 存在、0 条目,`rmdir` rc 0,删除后 `ls -d` 失败)。
- ES3R4-15(更正 ES3R4-13):`check_sha_s3r4_c2.sh` 核实:safe_run.log 共 62 行;`head -n 60` 的 sha256 `8e0844d0…2aec` 与清单记录一致;第 61、62 行是清单之后追加的两行(sha256sum -c 记录与提交命令)。核对记录写在 `evidence/p05-s3r4c2/SHA256SUMS_CHECK_p05-s3r4.txt`。
- ES3R4-16(更正 ES3R4-11):多边形部分未由续1 执行,改由续2 补做(本报告 §4)。
- ES3R4-17:续1 停止与 U103–U106 的说明。

---

## 2. 库哈希核对(§3.1)

| 库 | sha256 | 与任务书一致 |
|---|---|---|
| F2 `evidence/p05-s3r4/build/F2-plain/build/libS4.a` | `c63d180aff6c5b5e443faefeb6de44abce430dafbb846db434ac15da85fbc185` | 是 |
| F3 `evidence/p05-s3r4/build_f3/plain/build/libS4.a` | `abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de` | 是 |

F2-dbg 库只读引用,用于 A 的 `info line` 佐证:**未运行**(A 注入未进行;A1 映射用的是 F2/F3 驱动的 gdb 映射,不需要 dbg 库)。

---

## 3. C:多边形无注入逐字节比较 — **通过(33 组合,99/99 IDENTICAL,rc 对全部一致)**

**驱动与差异:**
- `testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp`,从 `testing/d003/stage_s4/driver_r6b_state.cpp` 复制,唯一改动在 pattern 分支(`S4_Layer_SetRegionHalfwidths` 调用换为 `S4_Layer_SetRegionVertices(…, S4_REGION_TYPE_POLYGON, 5, pent, …)`,正五边形半径 0.25,逆时针,中心 (0,0))。
- 逐行 diff:`evidence/p05-s3r4c2/POLY_DRIVER_DIFF.txt`:1 个 hunk,删 2 行,增 10 行,全部在 pattern 分支;摘要 `POLY_DRIVER_DIFF_SUMMARY.txt`。
- 链接:`link_c2.sh`(链接 `inject_r4_plan.cpp`,与 C 中 state 驱动相同);F2 库 `c63d180a…`,F3 库 `abbc01c7…`。驱动 sha256(完整值):`poly-F2` `e9b75ca249a9dbf8622624b117ec3f91b157fa8c121bd6a6de053c80400dec86`;`poly-F3` `c92e7d7a4a0ed0550dcb4d05ebe06a8d29cad697f8799052593ffe9f31fd9be7`。
- 链接选项 diff:**未单独写出**(本轮链接脚本是 S3R4 `link_s3r4.sh` 的逐字复制,只改驱动源与输出目录;差异仅为驱动源文件,已由 diff 证明)。

**预注册:** `REGISTRY_S3R4C2_C_POLY.tsv`,33 行(11 模式 × NG 1、5、9),sha256 `4513c8cdfaa7cb732f0e72306321d2ec87f689400e2c4d658cca100fe97cca2e`,UTC `2026-10-12T22:35:29Z`,写定于运行之前。期望:F2 与 F3 的 call1–3 dump 全部 IDENTICAL;rc 对全部一致。

**运行:**
- 第一次运行(`run_c_poly_c2.sh`)的结果表 `RESULTS_S3R4C2_C_POLY.tsv` 有格式缺陷(ES3R4-18):printf 说明符少一个,66 行伪记录,run_rc 列丢失。**数据文件(dump)未受影响。** 该表原样保留,不用于判定。
- 第二次运行(`run_c_poly_c2_run2.sh`,仅修正 printf)`RESULTS_S3R4C2_C_POLY_run2.tsv`:**66 个驱动行的 rc_first、rc_retry、run_rc 全部为 0;99 个比较行全部 IDENTICAL(call1、call2、call3 × 33 组合)。**
- 诊断 `diag_one_c2.sh`(closed2d NG1 F2)确认 RC first 0、RC retry 0,sed 提取正确。

**判定:C 通过。** 正常路径在 11 个模式、NG 1/5/9 下,F2 与 F3 的多边形驱动输出逐字节相同。F2 与 F3 的 rc 对全部为 0(F2 上的 rc 不要求为 0,实测也是 0)。

结果表:`registries/s3r4c2/RESULTS_S3R4C2_C_POLY_run2.tsv`(小表),第一次运行表 `RESULTS_S3R4C2_C_POLY.tsv` 也已复制,并在 ES3R4-18 中标注为缺陷版本。

---

## 4. A1 映射(806 与 1729)— **K 唯一确定**

**方法(第二版,ES3R4-19):** `a1map_c2_v2.sh` + `a1map_c2.gdb`:单个 gdb 会话(ASLR 关闭)中运行 init 驱动(无注入),在 `exit` 处 `info proc mappings` 取基址(offset 0 段),stderr 中每个 `caller` 减基址后用 `addr2line -f -e <driver>` 解析函数名。第一版(`a1map_c2.sh`,计数运行 ASLR 开启、基址另取)地址空间不一致,结果作废(目录 `a1map_F2_closed2d-ng1/`,保留不用)。

**结果**(`registries/s3r4c2/A1_MAP_SUMMARY_S3R4C2.tsv`):

| 树 | 组合 | 基址 | 窗口外分配数 | WIN_OPEN | 窗口内 malloc | K_init(n=4) | K0(n=0) | K 的函数 |
|---|---|---|---|---|---|---|---|---|
| F2 | closed2d NG1 | 0x555555554000 | 104 | 3 | 1 | **7** | 6 | Simulation_InitSolution |
| F2 | fft NG5 | 同上 | 116 | 3 | 1 | **8** | 7 | Simulation_InitSolution |
| F2 | kottke NG5 | 同上 | 116 | 3 | 1 | **8** | 7 | Simulation_InitSolution |
| F3 | closed2d NG1 | 同上 | 104 | 3 | 1 | **7** | 6 | Simulation_InitSolution |
| F3 | fft NG5 | 同上 | 116 | 3 | 1 | **8** | 7 | Simulation_InitSolution |
| F3 | kottke NG5 | 同上 | 116 | 3 | 1 | **8** | 7 | Simulation_InitSolution |

- K 的判据(任务书 §3.3):第二次 WIN_OPEN(nshapes=1 的层)之前最后一次窗口外 malloc,n = 4×nshapes = 4,caller 为 Simulation_InitSolution。每个组合中只有一个这样的分配(k=7 或 k=8)。
- 窗口内 malloc 为 n=8、caller `pattern_get_containment_tree`(806 的 area),在 F2 与 F3 上均为唯一一次。
- F2 与 F3 的 K 相同;组合间 K 不同(NG5 下多一次窗口外分配),已按组合分别确定,不是假设。
- 与任务书预计(K=7、K0=6 或 8)的差异:fft/kottke 的 K0=7、K=8,以映射为准;已记入 ES3R4-20。

**预注册:** `REGISTRY_S3R4C2_A.tsv`(18 行,sha256 `3f08fd8b86d2a5164b272cf3881729b3fbda04dca52e7b8d96dd64c586e5845d`,UTC `2026-10-12T22:39:14Z`),写定于任何 A 注入运行之前:
- A-806 `win:1`:F2 期望 CRASH;F3 期望 REPORTED_FAILURE,rc1 = 1。
- A-1729 `init:K`:F2 期望 REPORTED_FAILURE,rc1 = −3;F3 期望 REPORTED_FAILURE,rc1 = 1。
- A-U96 `init:K0`(BOUNDARY_U96_BY_DESIGN):F2、F3 期望 rc1 = 0,SILENT_SWALLOW。
- 副观察:F3 的 A-806、A-1729 与 F2 的 A-1729 的 rc2 期望 0。

**A 注入运行:未执行。** 原因:写入规则违规后停止(§8)。
- 注:`run_a_c2.sh` 是一份未完成的草稿(末行含 `2>/dev/null`,只有一个 stub 调用),**从未运行**(safe_run.log 无记录,无产物),不得使用。

**A 的状态:未完成(原因:违规停止)。** 不是不可行:映射已唯一确定,预注册已写定,只差注入运行。

---

## 5. B:415 多边形注入 — **未完成(原因:违规停止,未进入)**

未做:注入器 `inject_s3r4c2_poly.cpp`、`nm` 核对、前置核对(gdb 确认 POLYGON 分支、Mtot、n=12 的 [源码] 依据)、预注册 `REGISTRY_S3R4C2_B.tsv`、运行。
未得出任何 B 结果。

---

## 6. D:冒烟 — **未完成(原因:违规停止,未进入)**

未做:从 registries/s4r7 选取 8 点、预注册 `REGISTRY_S3R4C2_D.tsv`、链接与运行。
本报告中不写"冒烟通过"。

---

## 7. U100 的 [源码] 说明(Pattern_DiscretizeCell 的 −1…−9)

**未完成(原因:写入规则违规后停止,§8)。** 本节不依赖运行,原则上可做;本轮未写,留给续3 或 S5 登记。

---

## 8. 违规披露(AGENTS.md 第 3 节,两张表)

### 表一:越界写入尝试(命令自身写了仓库外路径)

无。所有写入目标在仓库内(`checkpoints/p05/`、`testing/d003/`、`evidence/p05-s3r4c2/`)。

### 表二:工具/脚本事件

| 轮次 | 时间(UTC) | 命令/脚本 | 事件 | 是否落盘 | 处理 |
|---|---|---|---|---|---|
| CONT2 | 22:35:18Z、22:37:35–36Z | `testing/d003/stage_s3r4c2/link_c2.sh`(两次)、`link_init_c2.sh`(两次) 第 13/14 行 `REPO=$(git rev-parse --show-toplevel 2>/dev/null)` | **违反 U106:脚本文本含 `2>/dev/null`(违规一次,触发停止)**。该行从历史脚本 stage_s3r4 的 link 脚本带入;执行者写 `link_init_c2.sh` 时称"逐字重写",没有逐行检查禁止项。链接成功;stderr 丢弃;目标在仓库内;无仓库外写入 | 是(合规的链接产物,位于 `drivers/`) | 停止;如实披露;不掩盖 |
| CONT2 | 22:33–22:39 | `run_c_poly_c2.sh`(第一次运行) | printf 格式缺陷:7 说明符 / 8 参数,66 行伪记录,run_rc 丢失(ES3R4-18)。数据文件未受影响 | 是 | 保留原表;run2 重跑;记录于 ES3R4-18 |
| CONT2 | 22:37 | `a1map_c2.sh`(第一版) | 计数运行与基址运行地址空间不一致,offset 无效(ES3R4-19) | 是 | 作废目录保留;v2 修正;记录于 ES3R4-19 |
| CONT2 | 写脚本时 | `run_a_c2.sh`(草稿) | 文本含 `2>/dev/null`;末行 stub;**从未运行** | 是(草稿文件仍在仓库中) | 不运行;保留并披露(ES3R4-21);不删除 |
| CONT2 | 22:34 | `set -- $COMBO` 在 shell 中的本地位置参数 | 只改本地变量,无写入 | 否 | 无 |
| CONT2 | 22:39 | `a1map` 循环中第四次 `safe_run` 调用对已存在目录 `a1map2_F2_closed2d-ng1` 的拒绝(REFUSED,exit 2) | 执行者多跑一次同一组合(循环的重复),脚本正确拒绝覆盖;无写入 | 否(拒绝记录在 safe_run 日志) | 无数据损失;如实记录 |
| CONT2 | 收尾 | 命令 `sha256sum -c SHA256SUMS.txt > tmp/check_final_out.txt`(只读校验,输出写入 `$EV/tmp/`) | 写输出文件的重定向未经 safe_run(目标在 `$EV/` 内,合规路径) | 是(`$EV/tmp/check_final_out.txt`) | 如实披露;违反 AGENTS §3 的"经 safe_run"要求;不掩盖 |
| CONT2 | 收尾 | 提交前扫描发现三个脚本含 `/dev/null`(`link_c2.sh`、`link_init_c2.sh`、`run_a_c2.sh`) | 未提交(留在工作区,未跟踪);其余合规文件提交于 `33f8ea8` | 否(未入库) | 披露(ES3R4-21);等待用户裁决是否删除或修正 |
| CONT2 | — | 写入方式 | 仓库内文本全部经 write/edit;其他写入经 safe_run 脚本;末次 git commit 与复制、校验经脚本 | 合规 | 无 |

说明:表二第一行是本轮的停止事件。这是执行者的过失(文本规则未逐行检查),不是框架事件。

---

## 9. 待用户裁决的技术问题(不含签收)

1. **是否在续3 中完成 A 注入运行、B、D**:A 的预注册与 K 已就绪;B 需新注入器;D 需 CTRL_SEAM 链接方式的核对。请用户指示续3 的范围。
2. **`run_a_c2.sh` 草稿与两个链接脚本中的 `2>/dev/null`**:建议续3 先在新脚本中修正并逐行检查(不改已运行的脚本,按 U17 不覆盖);是否同意。
3. **K0 与任务书预计的差异**(fft/kottke K0=7,closed2d K0=6):映射为准,已记入 ES3R4-20;请确认 A-U96 的 `init:K0` 点按映射定义。
4. **ES3R4-5(a)(b)、−1…−9(U100)**:按 U99、U100 交 P05-S5 登记;U100 的 [源码] 说明未写(§7),留给续3 或 S5。

---

## 10. 结尾与提交后核对

本轮**已完成**:门禁、记录修正两个提交、U105、ERRATA/RULINGS、C 多边形(通过)、A1 映射(K 唯一)、A 的预注册。
本轮**未完成**:A 注入运行、B、D、U100 [源码] 说明、红点状态表与 R8 新增行、STATE 的完整更新(见 §11)。
未完成的原因是写入规则违规(U106)后按任务书 §5 停止;这是停止原因,不是不可行。

本轮已完成/未完成 S3R4 续2 范围,等待用户审核。P05-S3、P05-S4 未签收。

提交后核对(提交 `33f8ea8` 时的真实结果):

```
33f8ea8 P05-S3R4 CONT2 partial (stopped by U106 write-rule violation): self-check C polygon passed (99/99 IDENTICAL); A1 map K unique; A pre-registered, not run; B and D not done; STATE, CONT2 report, registries s3r4c2, scripts stage_s3r4c2. awaiting user review
d64c552 P05-S3R4 CONT2 rulings U103-U106 and errata ES3R4-15..17; CONT2 brief archived. awaiting user review
45d17d5 P05-S3R4 CONT1 records as stopped (U104; content unchanged). awaiting user review
```

`git status --short`(提交 `33f8ea8` 之后):

```
?? testing/d003/stage_s3r4c2/link_c2.sh
?? testing/d003/stage_s3r4c2/link_init_c2.sh
?? testing/d003/stage_s3r4c2/run_a_c2.sh
```

上面三个文件含 `/dev/null`,按 ES3R4-21 未入库(待用户裁决)。本报告的 §10 与 §8 的最后修订在 `33f8ea8` 之后,因此本报告文件本身在该提交之后仍有未提交修改,将在最终一次提交中一并提交(见下一条)。

---

## 11. 收尾记录

- 收尾门禁:`evidence/p05-s3r4c2/GATE_CONT2_END.txt`(末次运行,提交前)。
- 小表与清单:`registries/s3r4c2/`(含 `SHA256SUMS.txt`;逐个校验 OK,见 `REGISTRY_COPY_CHECK.txt`)。
- `evidence/p05-s3r4c2/SHA256SUMS.txt`:覆盖全部非二进制证据文件;`safe_run.log` 单列为"清单后追加",不参与校验。
