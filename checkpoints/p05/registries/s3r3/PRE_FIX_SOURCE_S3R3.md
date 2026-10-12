# PRE_FIX_SOURCE_S3R3.md -- 修改前源码确认(S3R3-1 第 1 条)

树 F = HEAD:S4 = 4a6f64927a30537740dd0c8f11f9a5aae5e46ba4(门禁 GATE_S3R3.txt 已核对)。
本文件只读确认,未修改任何 S4/ 文件。[源码] = 本轮读取的源码行。

## 1. pattern.c 中的函数、行号与调用关系

| 符号 | 定义行 | 调用行 | 说明 |
|---|---|---|---|
| `cg` | 1245 | 1404(sparse_linsolve_d 的非 CHOLMOD 分支) | 返回 void;分配 `work` 于 1251;1272、1319 释放 |
| `sparse_linsolve_d` | 1327 | 1621(rect,N2)、2056(tri,N3) | 返回 void;`#ifdef HAVE_LIBCHOLMOD`(1328)与 `#else`(1403–1404) |
| `pattern_generate_flow_field_rect` | 1464 | 2133(pattern_generate_flow_field) | 返回 double;分配 `work` 1477、`iwork` 1481 无 NULL 检查;释放 1636–1637 |
| `pattern_generate_flow_field_tri` | 1643 | 2140 | 返回 double;分配 `work` 1656、`iwork` 1660 无 NULL 检查;释放 2084–2085 |
| `pattern_generate_flow_field` | 2089 | 2168(Pattern_GenerateFlowField) | 返回 int;参数检查 -1..-8 (2099–2106);`if(!(max_field>0)||!isfinite)` → -10 (2148–2150) |

- `sparse_linsolve_d` 的 rect 调用(1621)传 `_dxdy` 作 anorm;tri 调用(2056)传 `M[0]`。
- `cg` 的 1251 处 `malloc(sizeof(double)*4*n)` 无 NULL 检查,随后 1252 `p = work` 即使用。
- 注意:`cg` 与 `sparse_linsolve_d` 都返回 void,因此 R6d 的方案 R1、R2 覆盖不到 1251(见任务书 E-S3R3-A(a))。

## 2. HAVE_LIBCHOLMOD 是否在本仓库构建中定义

- `Makefile.Linux`、`Makefile.common`、`Makefile`、`setup.py` 中**没有**定义 `HAVE_LIBCHOLMOD` 的规则(grep 结果:仅 `Makefile.common:119` 的 `-DHAVE_MPI`)。
- 旧的 `Makefile.old` 中有 `ifdef CHOLMOD_LIB` → `CPPFLAGS += -DHAVE_LIBCHOLMOD`(行 87–88),但 `CHOLMOD_LIB =` 为空(行 42),且 `Makefile.old` 不是当前构建入口(当前 `Makefile.Linux`/`Makefile.common` 不引用它)。
- R5 的 `-O0 -g` 构建命令(`checkpoints/p05/evidence/p05-s4r5/dbg/STAGES.txt` 与 `build-dbg-F.log`)与 R4 的 `-O3 -march=native` 普通构建命令(`checkpoints/p05/evidence/p05-s4r4/build-plain-F.log`)中都**没有** `-DHAVE_LIBCHOLMOD`;`build-dbg-F.log` 中 `cholmod` 字样出现 0 次。
- **结论**:当前构建不定义 HAVE_LIBCHOLMOD,因此 `sparse_linsolve_d` 走 `#else` 分支(1404 调用 `cg`),CHOLMOD 分支不编译。CHOLMOD 分支没有失败返回路径(无 NULL 检查,只有 `cholmod_start`、`cholmod_allocate_*` 等的返回值未检查);本轮的修复不改 CHOLMOD 分支,只在分支末尾返回 0,并注释说明(见任务书第 3 节第 2 条)。

## 3. −11 在 S4/ 中的使用

`grep -n -- "-11"` 与 `grep -n "\-11\b"` 在 S4/ 中**无匹配**(本轮 grep 工具两次检查,结果均为 No matches found)。
`return -9`(pattern.c:1066,`pattern_discretize_cell`),`return -10`(pattern.c:2149,D016;intersection.c:254 另有 `return -10`,属于另一函数)。
因此 `-11` 在 S4/ 中**未被占用**;R3 的 `-11` 可用。

## 4. 三个调用者对非零返回的处理

| 调用者 | 调用行 | 非零处理行 | 处理内容 |
|---|---|---|---|
| fmm_PolBasisNV.cpp | 140 | 144–149 | `if(0 != error)`:S4_TRACE(行 145),释放 vfield/work/ivalues(146–148),`return error`(149) |
| fmm_PolBasisJones.cpp | 185 | 187–192 | `if(0 != error)`:S4_TRACE(188),释放 vfield/work/ivalues(189–191),`return error`(192) |
| fmm_PolBasisVL.cpp | 144 | 146–151 | `if(0 != error)`:S4_TRACE(147),释放 vfield/work/ivalues(148–150),`return error`(151) |

规划者给出的行号 NV:144、Jones:187、VL:146 与实测一致(分别是 `if(0 != error)` 的行)。三者都把错误原样返回。

## 5. pattern.h 的注释

- `pattern.h:314–322` 为 `pattern_generate_flow_field` 的声明;注释块(约 300–313)描述离散化与约束,**没有**返回值注释。
- 因此本轮不需要改 pattern.h。若需在 pattern.c 内的注释说明 -11,只改 pattern.c(任务书允许)。pattern.h 不在 U32 批准范围内,本轮不改。

## 6. 本轮修改计划(依据上文确认,未执行)

- pattern.c:1245 cg 改为 int 返回;1251 检查;1272、1319 的 return 改为返回 0 / 非零。
- pattern.c:1327 sparse_linsolve_d 改为 int 返回;#else 分支返回 cg 的状态;#ifdef 分支末尾返回 0(注释说明)。
- pattern.c:1464 _rect 与 1643 _tri:分配后检查,失败时释放已分配者,返回 -1.0。
- pattern.c:2089 pattern_generate_flow_field:在 2148 之前加 `if(max_field < 0){ return -11; }`(或等价判断),并加注释。
- S4_internal.h:263 注释(U31)。

## 7. 未决的小问题(记录,不影响本轮修改)

- `_rect` 与 `_tri` 当前在失败/非失败路径都返回 `max_field`(double);-1.0 作为错误标记时须确认与 max_field 的正常取值范围不冲突(max_field ≥ 0,hypot 结果非负)。
- 这一点在修改后由自检 (A)/(C) 与编译检查覆盖。
