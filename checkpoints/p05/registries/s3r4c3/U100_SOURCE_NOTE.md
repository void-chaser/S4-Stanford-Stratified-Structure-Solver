# U100 [源码] 说明:Pattern_DiscretizeCell 的返回码 −1…−9(P05-S3R4 CONT3,仅源码,未运行)

依据:U100(FFT/Kottke 忽略 −1…−9,交 P05-S5 登记);本说明只写 [源码],不运行。树:F3(`8d8202a`,S4/ = `6cff923a…`),行号以 F3 导出物 `checkpoints/p05/evidence/p05-s3r4c3/f3_export/S4/` 为准。

## 1. 调用链

- 包装函数:`Pattern_DiscretizeCell`,`S4/pattern/pattern.c:1166`;它直接调用 `pattern_discretize_cell(…)`(`pattern.c:1064`),返回值原样转发(`pattern.c:1173`)。
- 声明:`S4/pattern/pattern.h:248`(`pattern_discretize_cell`)、`pattern.h:258`(`Pattern_DiscretizeCell`)。
- **唯一调用者**:`S4/fmm/fmm_FFT.cpp:101` 与 `S4/fmm/fmm_kottke.cpp:105`。两者都只判断 `-12 == …`,其余返回值(包括 −1…−9)**被忽略**(这是 U100 所述的行为)。`-12` 才会 `ret = 1; goto cleanup`。

## 2. 逐个返回码(`pattern_discretize_cell`,pattern.c:1064 起)

| 码 | 来源(F3 文件:行号) | 触发条件 | 经公共 API 可达性([源码],未运行) |
|---|---|---|---|
| −1 | pattern.c:1077 `if(nshapes < 0){ return -1; }` | `nshapes < 0` | 不可达:`nshapes` 来自 `p->nshapes`(Pattern 构造),由 `S4_Layer_SetRegion*` 内部设置,非负;[源码] 判断为不可达 |
| −2 | pattern.c:1078 `if(nshapes != 0 && NULL == shapes){ return -2; }`;另有 pattern.c:1099 `if(RECTANGLE != s->type){ return -2; }` | `shapes` 为 NULL 且 nshapes≠0;或形状类型非 RECTANGLE(在 `closed1d`/区间分支) | 第一处不可达(`shapes` 来自 Pattern 自身);第二处:`closed1d` 只接受 INTERVAL/RECTANGLE 区域(S2R3 T2 注释),[源码] 判断经 `S4_Layer_SetRegion*` 的 RECTANGLE 路径可达,但需要 `Pattern` 形状类型与模式的组合,未运行验证 |
| −3 | pattern.c:1079 `if(NULL == parent){ return -3; }` | `parent` 为 NULL | 不可达:`parent` 由 `Pattern_GetContainmentTree` 生成,在 S 的层构建中总是非 NULL([源码]) |
| −4 | pattern.c:1081 `if(2 == dim && 0 == det){ return -4; }` | 2D 且 det(L)=0 | 可达条件依赖 L(晶格向量)。[源码] 判断:经 `S4_Simulation_SetLattice` 可设退化晶格,若未被拒绝则可达;未运行 |
| −5 | pattern.c:1082 `if(nu < 1){ return -5; }` | `nu < 1` | 不可达:`nu` 由 FFT/Kottke 的 `ngrid[0]` 给出,调用前已判 >0([源码],需确认 fmm_FFT.cpp 调用前的检查,未核实) |
| −6 | pattern.c:1083 `if(nv < 1){ return -6; }` | `nv < 1` | 同 −5(`ngrid[1]`) |
| −7 | pattern.c:1084 `if(iu < 0 || iu >= nu){ return -7; }` | 网格索引越界 | 不可达:`ii[0]` 由调用者的循环 `0..ngrid[0]-1` 给出([源码]) |
| −8 | pattern.c:1085 `if(iv < 0 || iv >= nv){ return -8; }` | 网格索引越界 | 不可达:同 −7(`ii[1]`) |
| −9 | pattern.c:1086 `if(NULL == value){ return -9; }` | `value` 为 NULL | 不可达:`discval` 由调用者在循环前分配(fmm_FFT.cpp / fmm_kottke.cpp,[源码]);−9 与 pattern.c:2212 注释"−9 is taken by pattern_discretize_cell"一致 |

## 3. 结论(仅 [源码],未运行)

- 调用者只处理 −12;−1…−9 在 FFT 与 Kottke 中被忽略。**其中 −2(区间/形状类型分支)与 −4(退化晶格)是需要进一步判断的码**;其余码在 [源码] 层面由调用者的循环与分配保证不可达。
- 本说明不作"可达性已验证"的结论。若要判定 −2、−4 的公共 API 可达性,需要运行(未在 CONT3 范围内)。
- 处理:按 U100,交 P05-S5 登记,不在 P05-S3/S4 修复。

## 4. 标注

- 行号以 F3 为准(F2 行号不同,例如 tri 分配行为 415 vs 418)。
- "不可达"一词仅指 [源码] 层面判断,不是实测结论,不得写入 R8 或 S5 的"已验证"栏。
