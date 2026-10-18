#!/usr/bin/env python3
# m3e_prep_r9m3e.py -- P05-S4 R9 M3e pre-freeze prep. Subcommands: rulings | errata | signoff | state | frozen.
import os,sys,re,hashlib,subprocess
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e")
SHK=os.path.join(EV,"shakedown")
REG=os.path.join(REPO,"checkpoints/p05/registries")
RUL=os.path.join(REG,"RULINGS.tsv")
ERR=os.path.join(REG,"s4r9/ERRATA_9.txt")
ST=os.path.join(REPO,"checkpoints/p05/STATE.md")
BRIEF=os.path.join(REPO,"checkpoints/p05/briefs/P05_S4R9_BRIEF_M3e.md")
SIGNOFF=os.path.join(REPO,"checkpoints/p05/P05_S3_S4_SIGNOFF.md")
STAGE=os.path.join(REPO,"testing/d003/stage_s4r9")
TAB=chr(9); NL=chr(10)
RUL_SHA="21ab76d29e8cb11392687c92bdd5ba67f18e1cace152631ec89dbbfe5d13c405"
ERR_SHA="d71543bbedeec8a00b2aa2fa3ad0197b787f8d6a83a825cdb811d3a18cf8cd87"
BLOCK="同意签收 P05-S3、P05-S4。范围声明：(a) 验证对象为冻结被测树 F4（05097a7，S4/ 树 589e15e…），不含 B 树行为，B 列观察不是修复证据；(b) M3d 修正版为签收前唯一现行版本（红点唯一 id 26、S5 移交 7 项、READINESS 28 行 GAP=0、签收草稿 v2），M3c 产物保留为历史，v1→v2 的 P-1…P-6 不逐条再确认；(c) 其他层失败变体（RP-R6d-14）只覆盖 P0/P2/PP1/PP2 四种布局、F4、driver_r8m2a2_layers（U354）；(d) S1/S2 范围声明第 (2) 条按 U356 由裁决闭合，测的是修复后的 &solve_info 路径，修前 seam 本身仍不可测；(e) seam-only 族不出 E2E 点，Lua REPL 只覆盖 cf/fft/kt/vl 四族；(f) 转 S5 的 7 项按 S5_HANDOFF_R9M3D 处理，其中 ES3R4-5/528/1164 与 U2 stage e 两项以 STATE 行对应；U354、U356 维持。"
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def shb(a): return subprocess.check_output(a,cwd=REPO,stderr=subprocess.DEVNULL)
def sums_dir(d):
 sp=os.path.join(d,"SHA256SUMS.txt")
 if not os.path.isfile(sp): return False,0,"missing"
 n=0
 for line in open(sp,encoding="utf-8"):
  line=line.strip()
  if not line or line.startswith("#"): continue
  a,name=line.split(None,1); name=name.strip()
  fp=os.path.join(d,name)
  if not os.path.isfile(fp) or sha_f(fp)!=a: return False,n,"mismatch "+name
  n+=1
 return True,n,"all %d OK"%n
def brief_block():
 lines=open(BRIEF,encoding="utf-8").read().splitlines()
 try:
  i=lines.index("----BEGIN SIGNOFF----"); j=lines.index("----END SIGNOFF----")
 except ValueError:
  raise SystemExit("HARD_STOP brief signoff markers missing")
 blk=lines[i+1:j]
 while blk and not blk[0].strip(): blk.pop(0)
 while blk and not blk[-1].strip(): blk.pop()
 return NL.join(blk)
def cmd_rulings(shake):
 old=open(RUL,"rb").read()
 if sha_b(old)!=RUL_SHA:
  print("HARD_STOP rulings prefix sha "+sha_b(old)); return 2
 rows=[
 ("U359","P05-S4 R9 M3e 任务书 §3","用户签收 P05-S3、P05-S4。签收块原文（逐字）："+BLOCK,"用户对话（2026-10-18）","生效"),
 ("U360","P05-S4 R9 M3e 任务书 §3","M3d 修正版（红点唯一 id 26、S5 移交 7 项、READINESS 28 行 GAP=0、签收草稿 v2）为签收前唯一现行版本；M3c 产物保留为历史。依据签收块 (b)。","用户对话（2026-10-18）","生效"),
 ("U361","P05-S4 R9 M3e 任务书 §3","v1→v2 的 P-1…P-6 差异不逐条再确认。依据签收块 (b)。","用户对话（2026-10-18）","生效"),
 ("U362","P05-S4 R9 M3e 任务书 §3","U354、U356 维持（其他层失败变体只覆盖 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers；S1/S2 第 (2) 条按 U356 由裁决闭合，测的是修复后的 &solve_info 路径）。依据签收块 (c)(d)(f)。","用户对话（2026-10-18）","生效"),
 ("U363","P05-S4 R9 M3e 任务书 §3","转 S5 的 7 项按 S5_HANDOFF_R9M3D 处理，其中无台账 id 的 2 项（ES3R4-5/528/1164、U2 stage e）以 STATE 行对应。依据签收块 (f)。","用户对话（2026-10-18）","生效"),
 ]
 add="".join(TAB.join(r)+NL for r in rows).encode("utf-8")
 new=old+add
 if shake:
  os.makedirs(SHK,exist_ok=True); open(os.path.join(SHK,"RULINGS_proposed.tsv"),"wb").write(new)
  print("SHAKEDOWN RULINGS proposed bytes %d -> %d sha %s rows %s"%(len(old),len(new),sha_b(new),",".join(r[0] for r in rows)))
 else:
  open(RUL,"wb").write(new)
  print("RULINGS bytes %d -> %d sha %s"%(len(old),len(new),sha_b(new)))
 print("APPENDED "+",".join(r[0] for r in rows))
 return 0
def cmd_errata(shake):
 old=open(ERR,"rb").read()
 if sha_b(old)!=ERR_SHA:
  print("HARD_STOP errata prefix sha "+sha_b(old)); return 2
 if len(old)!=62654:
  print("HARD_STOP errata prefix bytes %d"%len(old)); return 2
 ns=[l for l in sh(["git","diff","--name-status","c4f6707","37fbc0f"]).splitlines() if l.strip()]
 A=sum(1 for l in ns if l.startswith("A"+TAB)); M=sum(1 for l in ns if l.startswith("M"+TAB)); D=sum(1 for l in ns if l.startswith("D"+TAB))
 mfiles=sorted(l.split(TAB)[1] for l in ns if l.startswith("M"+TAB))
 m_expect=["checkpoints/p05/STATE.md","checkpoints/p05/registries/RULINGS.tsv","checkpoints/p05/registries/s4r9/ERRATA_9.txt"]
 rul0=shb(["git","show","c4f6707:checkpoints/p05/registries/RULINGS.tsv"]); err0=shb(["git","show","c4f6707:checkpoints/p05/registries/s4r9/ERRATA_9.txt"])
 rul_cur=open(RUL,"rb").read(); err_cur=open(ERR,"rb").read()
 rul_app=rul_cur.startswith(rul0) and len(rul_cur)>len(rul0)
 err_app=err_cur.startswith(err0) and len(err_cur)>len(err0)
 rootreg=os.path.exists(os.path.join(REPO,"registries"))
 m3d_ok,m3d_n,m3d_d=sums_dir(os.path.join(REG,"s4r9/M3d"))
 u5=[l for l in open(RUL,encoding="utf-8") if l.startswith("U5"+TAB)]
 e6=[l for l in open(os.path.join(REG,"s4r6/ERRATA_6.txt"),encoding="utf-8") if "E6-4" in l]
 hand=[l for l in open(os.path.join(REG,"s4r9/M3d/S5_HANDOFF_R9M3D.tsv"),encoding="utf-8") if l.startswith("S5-M3D-06"+TAB)]
 facts=[
  ("E9_74_A",A),("E9_74_M",M),("E9_74_D",D),("E9_74_M_FILES",";".join(mfiles)),
  ("E9_74_M_EXPECT_MATCH",mfiles==m_expect),("E9_74_RULINGS_PURE_APPEND",rul_app),("E9_74_ERRATA_PURE_APPEND",err_app),
  ("E9_75_ROOT_REGISTRIES_ABSENT",not rootreg),("E9_75_M3D_SUMS","%s count=%d"%(m3d_d,m3d_n)),
  ("E9_76_U5_PRESENT",bool(u5)),("E9_76_U5_TEXT",(u5[0].split(TAB)[2][:160] if u5 else "missing")),
  ("E9_76_E6_4_PRESENT",bool(e6)),("E9_76_E6_4_TEXT",(e6[0].strip()[:160] if e6 else "missing")),
  ("E9_76_S5_M3D_06_SOURCE_RULING",(hand[0].split(TAB)[3] if hand else "missing")),
 ]
 fails=[k for k,v in facts if v is False]
 e74="E9-74"+NL+"- 事实：M3d end 门禁 M3C_AND_M3B_COMMITTED_FILES_UNCHANGED 的 FAIL 是检查器口径缺陷：把 M3d 新增的 A 文件算作“已提交文件被改动”。现场复核 c4f6707..37fbc0f 的 name-status：A=%d、M=%d、D=%d；M 文件只有 %s；RULINGS.tsv 纯追加=%s，ERRATA_9.txt 纯追加=%s（旧内容是新文件前缀且新文件更长）。"+NL+"- 证据文件与行号：P05_S4R9_M3d_REPORT.md 附录 B；m3d/GATE_R9M3D_end.txt；本行复核输出 m3e/ERRATA_RECHECK_R9M3E.txt。"+NL+"- 影响范围：M3d end 门禁出现一处口径型 FAIL，核验效力受损；已提交文件本身未被改动。"+NL+"- 处理方式：只登记勘误，不重跑 M3d；M3e end 门禁只对 BASE（37fbc0f）已存在的文件判 M/D，本轮新增 A 文件不算改动。"
 e74=e74%(A,M,D,"、".join(mfiles),rul_app,err_app)
 e75="E9-75"+NL+"- 事实：M3d copy_registries 的 DEST 参数多写了一级 ..，误把 11 个小表与清单写到仓库根 registries/s4r9/M3d/；已删除误写目录并在 checkpoints/p05/registries/s4r9/M3d/ 重建。现场复核：仓库根 registries/ 不存在=%s；M3d 清单 %d/%d OK（%s）。"+NL+"- 证据文件与行号：m3d/GATE_R9M3D_end.txt 的 REGISTRIES_M3D_SUMS_ALL_OK 行；本行复核输出 m3e/ERRATA_RECHECK_R9M3E.txt。"+NL+"- 影响范围：M3d 收尾路径一度写出允许写入目标之外（仍在仓库内），清单已重建且逐项一致；结果表未受影响。"+NL+"- 处理方式：只登记勘误，不重跑 M3d；M3e 的复制脚本先 realpath 解析目标目录并断言前缀再写入。"
 e75=e75%(not rootreg,m3d_n,m3d_n,m3d_d)
 e6txt=(e6[0].strip()[:200] if e6 else "missing")
 e76="E9-76"+NL+"- 事实：S5_HANDOFF_R9M3D.tsv 的 S5-M3D-06（RP-R6d-3 no-TWICE 路径）source_ruling 写为 OUT_OF_SCOPE_D003，不是 U 编号；应为 U5（E6-4：no-TWICE 路径不在范围内）。现场核对：RULINGS.tsv 的 U5 行存在且正文以 E6-3/E6-4 为引用来源；registries/s4r6/ERRATA_6.txt 的 E6-4 原文为「%s」；S5-M3D-06 当前 source_ruling=%s。"+NL+"- 证据文件与行号：checkpoints/p05/registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv（S5-M3D-06 行）；checkpoints/p05/registries/RULINGS.tsv（U5 行）；checkpoints/p05/registries/s4r6/ERRATA_6.txt（E6-4）。"+NL+"- 影响范围：M3d 移交表一行来源字段不是 U 编号；移交内容本身不变，S5 开工以本勘误为准。"+NL+"- 处理方式：不改 M3d 已提交文件，只登记勘误；S5 处理 S5-M3D-06 时以 U5（E6-4）为来源裁决。"
 e76=e76%(e6txt,(hand[0].split(TAB)[3] if hand else "missing"))
 e77="E9-77"+NL+"- 事实：M3d 门禁检查器的口径与路径问题（A 文件计入已提交改动；copy 目标多一级 ..）已由 M3e 的执行纪律修正：M3e end 门禁只对 BASE 已存在的文件判 M/D；复制/写入脚本先 realpath 解析目标目录并断言允许前缀。"+NL+"- 证据文件与行号：本任务书 §2 后两条；P05_S4R9_M3e_REPORT.md 附录 B。"+NL+"- 影响范围：仅记录 M3d 检查器与路径缺陷的修正方式，不改变 M3d 任何已提交产物。"+NL+"- 处理方式：只登记勘误，不重跑 M3d。"
 add=(NL+e74+NL+e75+NL+e76+NL+e77+NL).encode("utf-8")
 new=old+add
 os.makedirs(EV,exist_ok=True)
 rc_path=os.path.join(SHK if shake else EV,"ERRATA_RECHECK_R9M3E.txt")
 os.makedirs(os.path.dirname(rc_path),exist_ok=True)
 lines=["# ERRATA_RECHECK_R9M3E.txt -- facts recomputed for E9-74..E9-77"]
 lines+=["FACT"+TAB+k+TAB+"value="+str(v) for k,v in facts]
 lines.append("FAILS=%d"%len(fails))
 open(rc_path,"w",encoding="utf-8").write(NL.join(lines)+NL)
 print(NL.join(lines))
 if fails:
  print("HARD_STOP errata facts failed: "+",".join(fails)); return 2
 if shake:
  open(os.path.join(SHK,"ERRATA_9_proposed.txt"),"wb").write(new)
  print("SHAKEDOWN ERRATA proposed bytes %d -> %d"%(len(old),len(new)))
 else:
  open(ERR,"wb").write(new)
  print("ERRATA bytes %d -> %d last E9-77"%(len(old),len(new)))
 return 0
def cmd_signoff(shake):
 blk=brief_block()
 if blk!=BLOCK:
  print("HARD_STOP brief block != delivered signoff block"); return 2
 sig=("# P05-S3、P05-S4 签收记录"+NL+NL+
 "> 本文件只记录用户已授权的签收。它不包含任何新的验证结果,不改写 S3、S4 的历史报告。"+NL+
 "> 签收原文见 §2；P05-S5 未开始、未签收。"+NL+NL+
 "## 1. 签收"+NL+NL+
 "| 阶段 | 状态 | 签收依据 | 日期 |"+NL+
 "|---|---|---|---|"+NL+
 "| P05-S1 | 已由用户签收 | 用户在对话中授权（基于 S1R2、S3R2 之后的结果） | 2026-10-11 |"+NL+
 "| P05-S2 | 已由用户签收 | 用户在对话中授权（基于 S1R2、S3R2 之后的结果） | 2026-10-11 |"+NL+
 "| P05-S3 | 已由用户签收 | 用户在对话中给出签收原文（见 §2） | 2026-10-18 |"+NL+
 "| P05-S4 | 已由用户签收 | 用户在对话中给出签收原文（见 §2） | 2026-10-18 |"+NL+
 "| P05-S5 | 未开始 | — | — |"+NL+NL+
 "## 2. 范围声明（签收块原文，逐字照录）"+NL+NL+blk+NL+NL+
 "## 3. 对后续阶段的含义"+NL+NL+
 "- S5 接收 S5_HANDOFF_R9M3D.tsv 的 7 项（S5-M3D-01 … S5-M3D-07）；其中 S5-M3D-06 的来源裁决按 E9-76 记 U5（E6-4，no-TWICE 路径不在范围内）。"+NL+
 "- 签收范围声明 (a)–(f) 见 §2，逐字照录，不在此复述或解释。"+NL+NL+
 "## 4. 未完成声明"+NL+NL+
 "本记录由执行者依据用户授权写入，执行者未自行宣布任何阶段完成。P05-S5 未开始、未签收。"+NL)
 if shake:
  os.makedirs(SHK,exist_ok=True); open(os.path.join(SHK,"P05_S3_S4_SIGNOFF.proposed.md"),"w",encoding="utf-8").write(sig)
  print("SHAKEDOWN SIGNOFF proposed bytes %d"%len(sig.encode()))
 else:
  open(SIGNOFF,"w",encoding="utf-8").write(sig)
  print("SIGNOFF written bytes %d"%len(sig.encode()))
 chk=[("SIGNOFF_SEC2_VERBATIM",True),("SIGNOFF_S3_S4_DATE",("2026-10-18" in sig)),("SIGNOFF_S5_NOT_STARTED",("P05-S5 | 未开始" in sig)),("SIGNOFF_S5_7_ITEMS",("S5-M3D-01" in sig and "S5-M3D-07" in sig)),("SIGNOFF_E9_76",("E9-76" in sig)),("SIGNOFF_DECLARATION",("执行者未自行宣布任何阶段完成" in sig))]
 for k,v in chk: print("SIGNOFF_CHECK"+TAB+k+TAB+("PASS" if v else "FAIL"))
 return 0 if all(v for _,v in chk) else 2
STATE_NEW="""# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 本轮开工基线 HEAD（r9m3e） | `37fbc0f2b9c48010b81ad220293fe6f3af5c02bd`（M3d 收尾提交） |
| `HEAD:S4`（冻结被测树 F4） | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4 提交 `05097a7`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段状态 | S1、S2、S3、S4 已由用户确认（带范围声明，见签收文件）；S5 未开始 |
| 签收文件 | `P05_S3_S4_SIGNOFF.md`（§1 签收表、§2 范围声明逐字照录） |
| 当前轮次 | **P05-S4 R9 M3e（r9m3e）**：用户签收 P05-S3/P05-S4 落账（U359–U363，签收日期 2026-10-18）、勘误 E9-74–E9-77、签收文件、STATE 收尾 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | twice 48 MATCH；R6d 202 一致 | `P05_S4R6_REPORT.md` … `R6d` |
| S3R3–S3R4 | F2 36/36；F3 8d8202a 117/117 | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1/M2 MISMATCH 0；M3 G5 177、G6 25 HOLD | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1c | 830 行全覆盖；M1 总表 1302 行闭环 | `P05_S4R8_REPORT_M0.md` … `M1C3` |
| S4R8 M2a–e | 正式两遍 202 点全 MATCH | `P05_S4R8_M2A_REPORT.md` … `M2E` |
| S3R5 | 冻结 F4 `05097a7`（树 `589e15e…`）；无注入 9/9 PASS | `P05_S3R5_CLOSEOUT.md` |
| S4R9 M0+M2 | 16 驱动+7 库；无注入 146/146；正式两遍 191/191 MATCH | `P05_S4R9_M2_REPORT.md` |
| S4R9 M2b | E9-1..6（U299）；HIT 等价 173/173 | `P05_S4R9_M2b_REPORT.md` |
| S4R9 M2c | E9-7..13（U302–U305）；RP 关闭（U304） | `P05_S4R9_M2c_REPORT.md` |
| S4R9 M1/M1R2 | 参考结果（U312/U318），不作为 M1 有效结果 | `P05_S4R9_M1_REPORT.md` / `M1R2` |
| S4R9 M1R3 | 物理事实有效；651 点两遍全 MATCH；F3/F4 0 DIFFS；总表 1302 行 | `P05_S4R9_M1R3_REPORT.md` |
| S4R9 M1R4 | r9m1r4 复核结果经 U328 采纳；流程缺陷见 E9-35.. | `P05_S4R9_M1R4_REPORT.md` |
| S4R9 M3a | J-1..J-6 属实（E9-35..E9-44、E9-45，U328–U333）；make test 四遍 rc=0、175 单元、**NO_NEW_FAILURE**；E2E 装置+预注册 18 点 | `P05_S4R9_M3a_REPORT.md` |
| S4R9 M3b | U334–U342、E9-46–E9-57；make test NO_NEW_FAILURE；E2E 正式两遍 CONTROL_OK=17, E2E_OK=25；新红点 0 | `P05_S4R9_M3b_REPORT.md` |
| S4R9 M3c | U343–U350、E9-58–E9-66；M3b 独立复核 DIFFS=0；READINESS MET=14 GAP=0 TRANSFERRED_S5=5；S5 移交 10 项 | `P05_S4R9_M3c_REPORT.md` |
| S4R9 M3d | U351–U358、E9-67–E9-73；§3 P 项复核 6/6 属实；红点唯一 id 26、TRANSFERRED_S5=6；去重 S5 移交 7 项 | `P05_S4R9_M3d_REPORT.md` |
| S4R9 M3e | U359–U363（签收落账）；E9-74–E9-77；签收文件 §2 逐字；S5 移交 7 项按 S5_HANDOFF_R9M3D | `P05_S4R9_M3e_REPORT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-01） |
| NB=1–8、类别 C | M2-07 81 点全 MATCH；M2-08 转 S5 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-02） |
| ES3R4-5/528/1164 | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-03；E9-76） |
| 非 FMM S4_malloc（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-04） |
| U2 stage e（I1 特殊规则） | NOT_FOUND_IN_SCOPE | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-05；E9-76） |
| RP-R6d-3 no-TWICE 路径 | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-06；来源按 E9-76 记 U5） |
| RP-R6d-7 D016（B 侧 rc 来源未追踪） | B 侧基线观察；F 侧归 D016/D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-07） |

已关闭项（S3-4b、806/415/RP-S3R4-1、RNV1、双目标/sanitizer、K-1、RP-R8-M2c-1、其他层失败变体、七处 info=NULL seam、Python/Lua 可见性、ClosedForm/LinearSolve 可达性、U38 分类、ADD22、r8m2c/d SOLN 18/28 点等）压缩为一行：均已按对应 U 编号关闭，见 `P05_S3_S4_SIGNOFF.md` §1/§3 与各轮报告。

## 4. 证据位置

- **S4 R9 M3e（r9m3e）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3e/`（`SHA256SUMS.txt`）；小表 `checkpoints/p05/registries/s4r9/M3e/`（`SHA256SUMS.txt`）；报告 `P05_S4R9_M3e_REPORT.md`；签收 `P05_S3_S4_SIGNOFF.md`。
- **S4 R9 M3d（r9m3d）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3d/`；小表 `checkpoints/p05/registries/s4r9/M3d/`；报告 `P05_S4R9_M3d_REPORT.md`。
- **S4 R9 M3c/M3b/M3a**：证据 `checkpoints/p05/evidence/p05-s4r9/{m3c,m3b,m3a}/`；小表 `checkpoints/p05/registries/s4r9/{M3c,M3b,M3a}/`。
- **S4 R9 M1R4/M1R3/M1R2/M1**：证据 `checkpoints/p05/evidence/p05-s4r9/{m1r4,m1r3,m1r2,m1}/`；小表 `checkpoints/p05/registries/s4r9/{M1R4,M1R3,M1R2,M1}/`。
- 更早轮次与完整台账：各轮报告；`RED_POINTS_LEDGER_R6c.tsv`；裁决总表 `registries/RULINGS.tsv`；勘误 `registries/s4r9/ERRATA_9.txt`；S5 移交 `registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv`。
"""
def cmd_state(shake):
 if len(STATE_NEW.encode("utf-8"))>8192:
  print("HARD_STOP state too big"); return 2
 if shake:
  os.makedirs(SHK,exist_ok=True); open(os.path.join(SHK,"STATE.proposed.md"),"w",encoding="utf-8").write(STATE_NEW)
  print("SHAKEDOWN STATE proposed bytes %d"%len(STATE_NEW.encode()))
 else:
  open(ST,"w",encoding="utf-8").write(STATE_NEW)
  print("STATE written bytes %d"%len(STATE_NEW.encode()))
 mk=["r9m3e","P05_S3_S4_SIGNOFF","S5_HANDOFF_R9M3D","E9-76","2026-10-18","U359","S1、S2、S3、S4 已由用户确认"]
 miss=[m for m in mk if m not in STATE_NEW]
 print("STATE_CHECK misses=%s size=%d"%(miss,len(STATE_NEW.encode())))
 return 0 if not miss else 2
def cmd_frozen(shake):
 files=sorted(f for f in os.listdir(STAGE) if ("r9m3e" in f) and (f.endswith(".py") or f.endswith(".sh")))
 expect={"m3e_prep_r9m3e.py":("0","-"),"m3e_chain_r9m3e.py":("6","-"),"gate_r9m3e.sh":("1","end"),"gate_check_r9m3e.py":("0","-")}
 if sorted(files)!=sorted(expect):
  print("HARD_STOP stage r9m3e files unexpected: "+str(files)); return 2
 rows=[]
 for f in files:
  e,m=expect[f]; rows.append((f,sha_f(os.path.join(STAGE,f)),e,m))
 txt=["# FROZEN_SCRIPTS_R9M3E.tsv -- frozen scripts after the shakedown chain and before the record commit (i).",
      "# The end gate reads the POST_I call expectations from this file.",
      "path"+TAB+"sha256"+TAB+"expected_calls"+TAB+"mode"]
 txt+=["testing/d003/stage_s4r9/"+r[0]+TAB+r[1]+TAB+r[2]+TAB+r[3] for r in rows]
 body=NL.join(txt)+NL
 if shake:
  os.makedirs(SHK,exist_ok=True); open(os.path.join(SHK,"FROZEN_SCRIPTS_R9M3E.proposed.tsv"),"w",encoding="utf-8").write(body)
  print("SHAKEDOWN FROZEN proposed rows %d"%len(rows))
 else:
  open(os.path.join(EV,"FROZEN_SCRIPTS_R9M3E.tsv"),"w",encoding="utf-8").write(body)
  print("FROZEN written rows %d"%len(rows))
 print(body)
 return 0
def main():
 if len(sys.argv)<2: print("usage: m3e_prep_r9m3e.py <rulings|errata|signoff|state|frozen> [--shakedown]"); return 2
 sub=sys.argv[1]; shake="--shakedown" in sys.argv[2:]
 return {"rulings":cmd_rulings,"errata":cmd_errata,"signoff":cmd_signoff,"state":cmd_state,"frozen":cmd_frozen}[sub](shake)
if __name__=="__main__": sys.exit(main())
