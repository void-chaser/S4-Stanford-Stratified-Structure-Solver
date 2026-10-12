# P05-S4 R7 续 2 报告(M1a 完成;M2 未完成,部分进展)

**状态:本轮未完成 R7 范围。M1a(M1 补遗)大部分完成;M2(G1–G4 rc 类回归)未完成,没有任何 M2 注入结果被判定。本段未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S4/ 未修改。**

规则依据:`AGENTS.md`;R7 原任务书;续 1;续 2 `checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT2.md`;勘误 `checkpoints/p05/registries/s4r7/ERRATA_7.txt`。

## 1. M1a(M1 补遗)

### 1.1 PolBasisJones 返回值(U45,行断点,不用 finish)— 完成
- 行号确认:`fmm_PolBasisJones.cpp:192`(`return error;`)与 `S4.cpp:2413`(`if(0 != fmm_ret){`)在 F 与 F2 中相同(两文件 F/F2 字节一致),`gdb info line` 在 F2 dbg 中可绑定。记录于 `LINEMAP_A1_R7.tsv`。
- 脚本 `testing/d003/stage_s4r7/gdb_chain_jones_line_r7.gdb`(行断点,continue)。三点实测(`GDB_CHAIN_SUMMARY_R7_A1.tsv`):

| 模式 | M | pattern 返回 | PolBasisJones error(:192) | fmm_ret 第一次(:2413) | RC first |
|---|---|---|---|---|---|
| jones | 1 | −11 | **−11** | −11 | 20 |
| jones | 3 | −11 | **−11** | −11 | 20 |
| fftjones | 1 | −11 | **−11** | −11 | 20 |

- 第二次调用(重试)的 fmm_ret = 0(无注入,正常)。
- 结论:对这三点,PolBasis 层的返回值**实测为 −11**,并逐层读到 `ComputeLayerModes` 的 rc = 20(经 `RC first`)。M1 的"未读到"限制已解除(对这三点)。
- 注意:fftjones 只测了 M=1。

### 1.2 对照离线重新判定(U44,POSTHOC)— 完成
- 脚本 `testing/d003/stage_s4r7/rejudge_ctrl_m1_r7.py`(只读 stored nogdb.out 与 stored 进程 rc,不运行驱动)。输出 `RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv`。
- 规则与原注册字符串的引用见 `REGISTRY_S4_PRE_R7_M1_ERRATA_CTRL.txt`(注册字符串原样引用,未改)。
- 结果(两遍各 18 行):**CONTROL_OK 16、BASELINE_RC_EQUAL 2(vl NG1、fftvl NG1)、NOT_EQUAL 0**。与期望一致。
- 原 RESULTS 与 REGRESS 中的 18 行仍为 MISMATCH(U44,不改)。

### 1.3 E7-12、E7-13 — 完成
- E7-12:`SHA256SUMS.txt` 未收录 ERRATA_7 的新版本;旧清单不改,在 M2 清单中收录。
- E7-13:M1 报告的"90/90"措辞错误,正确为"F2 注入点 63/63 REPORTED_FAILURE(两遍),F 注入点 27/27 CRASH(两遍)";已记入 ERRATA_7,M1 报告不改。

## 2. M2 准备(未完成)

### 2.1 plain seam 库(3.1)— 完成
- R4 seam 构建选项读自 `registries/s4r4/LIBS_R4.tsv` 与 R4 构建日志(`-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC`,告警 71)。记于 `BUILD_SEAM_PLAIN_R7.tsv`。
- 构建 `build_seam_plain_s4r7.sh`:F 的 seamF 与 fmmret 库的 sha256 与 R4 记录**逐字节相同**(`8066a098…`、`fda3d99a…`),证明选项正确。F2 库另有 sha256(告警 71)。

### 2.2 驱动复现检查(3.2)— 结论已修正两次
- 第一次结论"未复现(hit 0)"**错误**:HIT 行输出在 stderr,探针只数了 stdout。
- 第二次结论"TWICE 点 inj_call 错误"部分正确:历史 `M-twice-fft-plan-12` 的 inj_call 为 2。用 inj_call = 2 判定时,`classify()` 给出 REPORTED_FAILURE,与历史一致。用默认 inj_call 1 则为 SILENT_SWALLOW。
- 结论:`d003plan` 驱动**复现了注入**(3 个探针 HITCOUNT 1、HIT on stderr)。M2 的分类必须逐行携带源表的 inj_call。
- 记于 `DRIVER_REPRO_CHECK_M2.txt`(已写入更正版本)。

### 2.3 M2 预注册 — 已注册(v2),v1 已废止
- v1(`REGISTRY_S4_PRE_R7_M2_SUPERSEDED_v1.tsv`,sha `87da9ef6…`)缺 inj_call 列,未运行任何 M2 点,废止并保留。
- v2(`REGISTRY_S4_PRE_R7_M2.tsv`,sha `e4dd2c87…`,UTC `2026-10-12T11:22:26Z`):554 行,14 字段,dry-parse 0 无法解析,inj_call 来自源行(1: 80 行,2: 60 行,与源表逐组计数一致)。
- 注意:v2 是在**运行前**注册的(没有任何 M2 运行)。v1 被替换属于运行前修正,不是改期望。
- 组成:G1 149 F 点(298 行,不运行,E7-17);G2a 25 点(不运行,seam 路径);G2b 22;G2c 30 + F 对照 3;G3 36;G4 12(G2b/G3/G4 为 plancall 路径,可运行)。

## 3. 本段未完成

- **M2 runner 与 `--dry-parse`**:未写。(3.3)
- **M2 运行与判定**(§5):未开始。**没有任何 M2 结果文件。**
- **G1、G2a**:未运行(E7-17 与 seam 路径)。
- **M2 报告、里程碑提交、STATE 最终更新、SHA256SUMS_M2**:未完成。
- **U46 中"G1–G4 在 F 与 F2 上都运行"**:只完成了 G2b/G3/G4 的注册,未运行。

以上为"未完成",不是"不可行"。

## 4. 违规披露(AGENTS.md 第 3 节)

### 表一:越界写入尝试

- **`fft/probe_m2/` 写到仓库根**:驱动复现探针的第一条命令构造输出路径时,`$1/probe_m2/$2-$3` 中的 `$2`(模式名 fft)与 `$3`(含 `:` 的请求)被用于路径,且第一次探针的 `$1` 不是证据目录,输出写到了相对路径 `fft/probe_m2/`(仓库根下,不在 $EV 下)。**命令自身写了仓库内但非 $EV 的路径**;该路径不在仓库外,但违反 §3 写入目标规则。已落盘。已修正:6 个文件移入 `$EV/probe_m2_misplaced_fft/`,根目录 `fft/` 已删除(移动,未删内容)。

### 表二:工具/脚本事件

| 轮次 | 命令/工具 | 事件 | 是否落盘 |
|---|---|---|---|
| M2 | 第一次驱动探针 | 同上(表一),路径构造错误 | 是(仓库内,已移入证据目录) |
| M2 | `python3 -I -B -c` 的多次只读核对(awk/python) | awk 误判一次(已用 python 复核);一次 `grep -c` 计数误读 HIT | 是(只读,不落盘) |
| M2 | `test ! -e ... && cp ... && echo "registered v2"` | 守卫阻止了 v2 复制(因 v1 已存在),"registered v2"未打印;随后以 mv 废止 v1 并注册 v2 | 是(合规路径) |
| M2 | `make_prereg_m2_r7.py` 字段名核对 | 发现 G2c 控制行读取与 dead loop;已修正 | 不落盘(脚本) |
| M2 | 多处 `edit` 工具 "file has not been read" | 读取后重试成功 | 不适用 |

说明:表一的越界路径违反 AGENTS §3。执行者的过失,如实列出。

## 5. 需要用户裁决的事项

1. **是否继续 M2 运行**(G2b/G3/G4 plancall 路径,v2 已注册,runner 未写)。
2. **G1 的注入请求**:RESULTS_R3 不含请求字段,G1 不运行是否可接受,或需要用户指定请求映射来源(E7-17)。
3. **G2a(seam 路径)**:是否在 M2 中运行,还是交 M3 / R8。
4. **P05-S3 是否签收**(U47):M2 未完成,签收决定仍待 M2 里程碑。
5. **M1 对照的 18 行**:POSTHOC 已给出 16 CONTROL_OK + 2 BASELINE_RC_EQUAL 每遍;是否接受此重新判定作为 R7 的对照结论(M1 的 MISMATCH 行保持原样)。
6. **fftjones 只测了 M=1 的 PolBasis 返回值**;是否需要 M=3。

---

本轮未完成 R7 范围(M1a 大部分完成;M2 未完成,未判定任何 M2 结果),等待用户审核。P05-S3、P05-S4 未签收。
