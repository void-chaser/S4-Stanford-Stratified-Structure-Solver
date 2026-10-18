#!/usr/bin/env python3
# s5r1_prep.py -- P05-S5 R1 preparation: inventory, triage, acceptance map, registry
# patch draft, plan draft, errata E9-78/E9-79, STATE, frozen script list.
import os,sys,re,hashlib,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
SHK=os.path.join(EV,"shakedown")
P05=os.path.join(REPO,"checkpoints/p05")
REG=os.path.join(P05,"registries")
TAB=chr(9); NL=chr(10); FENCE=chr(96)*3
SHAKE="--shakedown" in sys.argv[2:]

def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8").read()
def wr(p,t):
 os.makedirs(os.path.dirname(p),exist_ok=True)
 open(p,"w",encoding="utf-8").write(t)
def lines_of(rel): return rd(os.path.join(REPO,rel)).splitlines()
def find(rel,needle,occ=1):
 hits=[i+1 for i,l in enumerate(lines_of(rel)) if needle in l]
 if len(hits)<occ: raise SystemExit("LOCATOR_MISS %s in %s (occ %d)"%(needle,rel,occ))
 return hits[occ-1]
def ltext(rel,n): return lines_of(rel)[n-1]
def ex(s,n=190):
 s=" ".join(s.split())
 return s if len(s)<=n else s[:n-1]+"..."
def put(name,text):
 if SHAKE: wr(os.path.join(SHK,name),text)
 else: wr(os.path.join(EV,name),text)

HAND="checkpoints/p05/registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv"
SIG12="checkpoints/p05/P05_S1_S2_SIGNOFF.md"
ISSUE="testing/s4test/ISSUE_REGISTRY.md"
ROAD="PROJECT_ROADMAP.md"
J5="checkpoints/p05/registries/s1r2/J5_RECORDED_ITEMS.txt"
S1="checkpoints/p05/S1_BASELINE_AND_ENUMERATION.md"
S1R2="checkpoints/p05/P05_S1R2_CLOSEOUT.md"

def handoff():
 ls=lines_of(HAND); hi=[i for i,l in enumerate(ls) if l.startswith("item_id"+TAB)]
 if not hi: raise SystemExit("HANDOFF_HEADER_MISS")
 hi=hi[0]; d={}
 for i in range(hi+1,len(ls)):
  l=ls[i]
  if not l.strip() or l.startswith("#"): continue
  f=l.split(TAB)
  if len(f)<4: continue
  d[f[0]]={"line":i+1,"name":f[1],"scope":f[2],"ruling":f[3]}
 return d

def build_inventory():
 H=handoff(); rows=[]; merges=[]
 def add(iid,group,name,sf,loc,rul,status):
  rows.append({"iid":iid,"group":group,"name":name,"source_file":sf,"locator":loc,"ruling":rul,"status":status})
 AR="S5_HANDOFF_R9M3D.tsv"
 for k in ["S5-M3D-01","S5-M3D-02","S5-M3D-03","S5-M3D-04","S5-M3D-05","S5-M3D-06","S5-M3D-07"]:
  r=H[k]; rul=r["ruling"]
  if k=="S5-M3D-06": rul="U5"
  add(k,"A",r["name"],AR,"第 %d 行（第 3 列 scope）"%r["line"],rul,ex(r["scope"]))
 sigline=find(SIG12,"(3) S1 记录在案四项")
 b_items=[("S5-B-01","F10 历史因果","第 1 项：F10"),
          ("S5-B-02","F8 历史目录哈希","第 2 项：F8"),
          ("S5-B-03","反事实通量正确性（VL NB=1）","第 8 项：VL NB=1"),
          ("S5-B-04","allzero 分支设计意图","第 9 项：allzero")]
 for iid,name,needle in b_items:
  ln=find(J5,needle); st=""
  for k in (1,2):
   cand=ltext(J5,ln+k) if ln+k<=len(lines_of(J5)) else ""
   if cand.startswith("现状："): st=cand; break
  st=st.split("现状：",1)[1] if "现状：" in st else st
  add(iid,"B",name,SIG12+"; "+J5,"P05_S1_S2_SIGNOFF.md 第 (3) 条（物理行 %d）；J5_RECORDED_ITEMS.txt 物理行 %d"%(sigline,ln),"-（事实项）",ex(st))
 hashes=["logs/60-t6-results.json","logs/60-t6-main.log","logs/61-t6-diag-layer.log","logs/62-t6-repeat.log","s1_run.sh"]
 for i,h in enumerate(hashes):
  ln=find(S1,h); row=ltext(S1,ln)
  add("S5-B-%02d"%(5+i),"B","S1 报告 11.2 哈希来源："+h,S1+"; "+S1R2,"S1_BASELINE_AND_ENUMERATION.md 11.2 表物理行 %d；P05_S1R2_CLOSEOUT.md 物理行 %d（不一致 5 个之一）"%(ln,find(S1R2,"不一致（5）")),"-（事实项）",ex(row))
 d16r=find(ROAD,"**D016**"); rp=find(ROAD,"**R-P05-01**")
 d16i=find(ISSUE,"| D016 / P1")
 add("S5-C-01","C","D016 图案层零场除零（归 D003 失败传播范围）",ROAD+"; "+ISSUE,"PROJECT_ROADMAP.md 物理行 %d–%d；ISSUE_REGISTRY.md 物理行 %d"%(d16r,d16r+1,d16i),"-（事实项）",
     ex("2026-10-11 P05-S1R 实测：VL 基、n_G=1（NumBasis 1–4）时，图案层流场 max_field=0，场被写为 NaN，NaN 进入 Epsilon_inv/Epsilon2，特征值求解以 info=2 失败，公共 API 抛 RuntimeError、驱动 rc 20；B/A/H 三树一致。"))
 rpi=find(ISSUE,"| R-P05-01（P05-S1R")
 add("S5-C-02","C","R-P05-01 让 n_G=1 可计算（未验证，暂不处理）",ROAD+"; "+ISSUE,"PROJECT_ROADMAP.md 物理行 %d；ISSUE_REGISTRY.md 物理行 %d"%(rp,rpi),"-（事实项）",
     ex("VL 基在 n_G=1（NumBasis 1–4）时无法求解：图案层 allzero 到 1x1 流场网格使闭合单元上的边界通量抵消、场恒为零。该分支的设计意图未知；让 n_G=1 可计算需要改变该行为，属于行为变更而非失败传播。"))
 kt=find(SIG12,"fmm_kottke")
 add("S5-C-03","C","S2 闭合不含 fmm_kottke 除数数值安全",SIG12,"P05_S1_S2_SIGNOFF.md 物理行 %d（第 1 条）"%kt,"-（事实项）",ex(ltext(SIG12,kt)))
 d3=find(ISSUE,"| D003 / P1")
 add("S5-D-01","D","D003 FFT prepare/execute 失败处理与上层传播",ISSUE,"ISSUE_REGISTRY.md 物理行 %d（D003 行）"%d3,"-（事实项）",
     ex("checkpoint 已含 FFT wrapper/kiss FFT/网格路径的部分处理。历史六文件 FMM 候选和 runner 存在；完整候选未生产验收/集成"))
 p05lines=[i+1 for i,l in enumerate(lines_of(ISSUE)) if "P05" in l]
 extra=[n for n in p05lines if n not in (d16i,rpi)]
 for i,n in enumerate(extra):
  first=ltext(ISSUE,n).split("|")[1].strip() if ltext(ISSUE,n).startswith("|") else "ISSUE_REGISTRY 行 %d"%n
  add("S5-D-%02d"%(2+i),"D","ISSUE_REGISTRY 含 P05 的行（%s）"%ex(first,40),ISSUE,"ISSUE_REGISTRY.md 物理行 %d"%n,"-（事实项）",ex(ltext(ISSUE,n)))
 prow=find(ROAD,"| P05 | Phase 2 A")
 add("S5-D-%02d"%(2+len(extra)),"D","PROJECT_ROADMAP P05 行（验收标准与当前状态）",ROAD,"PROJECT_ROADMAP.md 物理行 %d（P05 行，第 4/5 列）"%prow,"-（事实项）",
     ex("验收：每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确。当前状态：待执行；优先复用已有候选"))
 merges=[("S5-M3D-03",["S5-M3D-03（A）","U99（C：pattern.c:798 内层循环）","U100（C：FFT/Kottke 忽略 -1..-9）"]),
         ("S5-C-01",["S5-C-01（C：PROJECT_ROADMAP D016）","ISSUE_REGISTRY 物理行 %d（D：D016 行）"%d16i]),
         ("S5-C-02",["S5-C-02（C：PROJECT_ROADMAP R-P05-01）","ISSUE_REGISTRY 物理行 %d（D：R-P05-01 行）"%rpi])]
 pre=len(rows)+sum(len(m[1])-1 for m in merges)
 return rows,merges,pre

INV,MERGES,PRE_ROWS=build_inventory()

TRIAGE=[
 ("S5-M3D-01","RECORD_ONLY_OPEN","B 列基线观察，不是修复证据（U359 范围声明 (a)）；S5 只需登记现状","S5_HANDOFF_R9M3D.tsv S5-M3D-01；P05_S3_S4_SIGNOFF.md 第 18 行","NO：B 树行为不在 P06/D004 路径上，P06 依赖 F4 修复后行为","ISSUE_REGISTRY/S5 登记表注明 B 列观察不是修复证据，保持 OPEN","NO"),
 ("S5-M3D-02","RECORD_ONLY_OPEN","M2-07 81 点全 MATCH；余下类别 C（1D+FFT 候选）无 S4 内可执行用例，转 S5 登记","S5_HANDOFF_R9M3D.tsv S5-M3D-02；RULINGS.tsv U249","NO：类别 C 不在 D004 的 solve 后选项路径","登记 NB=1–8 与类别 C 现状，保持 OPEN","NO"),
 ("S5-M3D-03","REGISTRY_ONLY","ES3R4-5/528/1164 为 OUT_OF_SCOPE_D003 的既有问题；U99/U100 已裁决交 P05-S5 登记、不在 P05-S3/S4 修复","RULINGS.tsv U90/U95/U99/U100；ERRATA_S3R4.txt ES3R4-5","NO：不在 FMM/FFT 失败传播链上","在 ISSUE_REGISTRY 登记 528、1164、ES3R4-5(a)(b)（含 pattern.c:798、Pattern_DiscretizeCell -1..-9），状态 OPEN（不在 P05 修）","NO"),
 ("S5-M3D-04","NEEDS_FIX_NEW_DEFECT","非 FMM 的约 35–43 处 S4_malloc 不在 D003 范围（用户范围决策）；须另立登记号，不在 P05 修","S5_HANDOFF_R9M3D.tsv S5-M3D-04；STATE.md 范围决策行","NO：不属模式/缓存安装路径，也不在 FMM/FFT 失败传播链","另立独立登记项（建议编号 D017）：逐点列非 FMM S4_malloc 调用位置，状态 OPEN；见注册表补丁草案 2.3","NO"),
 ("S5-M3D-05","RECORD_ONLY_OPEN","M2-02 阶段 e 在 S4 内 NOT_FOUND_IN_SCOPE，转 S5（U248）","RULINGS.tsv U248；S5_HANDOFF_R9M3D.tsv","NO：无 S4 内可执行点，不在 P06 路径","登记 NOT_FOUND_IN_SCOPE，保持 OPEN","NO"),
 ("S5-M3D-06","RECORD_ONLY_OPEN","no-TWICE 路径 OUT_OF_SCOPE_D003；来源按 E9-76 记 U5（E6-4）","E9-76；RULINGS.tsv U5；S5_HANDOFF_R9M3D.tsv","NO：no-TWICE 不在 D003 注入范围","登记范围外（U5），保持 OPEN","NO"),
 ("S5-M3D-07","RECORD_ONLY_OPEN","RP-R6d-7：D016 的 B 侧 rc 来源未追踪；F 侧归 D016/D003","S5_HANDOFF_R9M3D.tsv S5-M3D-07；M3d 报告 7","NO：B 侧基线观察，F 侧已归 D016/D003","登记 B 侧 rc 来源未追踪，保持 OPEN","NO"),
 ("S5-B-01","NEEDS_USER_RULING","F10 历史因果未确认；需历史负载原始输入或允许独立复现","J5_RECORDED_ITEMS.txt 第 1 项；P05_S1_S2_SIGNOFF.md 第 25 行","NO：D016 修法不依赖 F10 因果","保持 OPEN；需用户提供输入","YES"),
 ("S5-B-02","NEEDS_USER_RULING","F8：按 spec 不访问历史候选目录，六文件哈希未验证；需用户授权或提供比对","J5_RECORDED_ITEMS.txt 第 2 项","NO：S5 修复对象是当前仓库源码","保持未验证；不改写历史","YES"),
 ("S5-B-03","NEEDS_USER_RULING","反事实通量正确性仅有一个单点反事实（0.95890），无独立参考解","J5_RECORDED_ITEMS.txt 第 8 项；R-P05-01","NO：只影响让 n_G=1 可计算这一半","保持 OPEN；需独立参考解","YES"),
 ("S5-B-04","NEEDS_USER_RULING","allzero 到 1x1 的设计意图未知（源码无注释）","J5_RECORDED_ITEMS.txt 第 9 项；R-P05-01","NO：不阻塞 D016","保持 OPEN；需原作者/用户确认","YES"),
 ("S5-B-05","NEEDS_USER_RULING","S1 报告 11.2 记录的哈希与 EVIDENCE.sha256 不一致，来源无法判定","S1_BASELINE_AND_ENUMERATION.md 11.2；P05_S1R2_CLOSEOUT.md 第 278–283 行","NO：文档溯源问题，不影响实现","保持未验证；不改写 11.2 与清单","YES"),
 ("S5-B-06","NEEDS_USER_RULING","同上（5 个不一致哈希之一）","S1_BASELINE_AND_ENUMERATION.md 11.2；J4_SUMMARY.txt","NO","保持未验证；不改写 11.2 与清单","YES"),
 ("S5-B-07","NEEDS_USER_RULING","同上（5 个不一致哈希之一）","S1_BASELINE_AND_ENUMERATION.md 11.2；J4_SUMMARY.txt","NO","保持未验证；不改写 11.2 与清单","YES"),
 ("S5-B-08","NEEDS_USER_RULING","同上（5 个不一致哈希之一）","S1_BASELINE_AND_ENUMERATION.md 11.2；J4_SUMMARY.txt","NO","保持未验证；不改写 11.2 与清单","YES"),
 ("S5-B-09","NEEDS_USER_RULING","同上（5 个不一致哈希之一）","S1_BASELINE_AND_ENUMERATION.md 11.2；J4_SUMMARY.txt","NO","保持未验证；不改写 11.2 与清单","YES"),
 ("S5-C-01","NEEDS_TEST","D016 已在 P05-S3R2 提交 3e77aa9 实施（F4 源码确认：max_field 零/非有限返回 -10）；登记表 D016 行仍写待 P05-S3 实施，属过期文字；Python 异常文本在 S3R2 未实测","P05_S3R2_CLOSEOUT.md 第 17、38、186 行；[源码] S4/pattern/pattern.c 2210–2216","NO：D016 不在 D004 的 solve 后选项路径","更新 D016 行：已实施（3e77aa9）、F4 源码确认；Python 异常文本留 S5R2 实测；补丁草案 2.2","NO"),
 ("S5-C-02","NEEDS_USER_RULING","让 n_G=1 可计算需要先确认设计意图并取得独立参考解（J5 第 8、9 项）","ISSUE_REGISTRY.md 第 114 行；PROJECT_ROADMAP.md 第 6 节","NO：暂不处理，不阻塞 P05","登记 R-P05-01 保持 OPEN；补丁草案 2.2 注","YES"),
 ("S5-C-03","RECORD_ONLY_OPEN","S2 对 fmm_kottke 的闭合明确不含除数数值安全（签收范围声明 (1)）；S5 登记，不修","P05_S1_S2_SIGNOFF.md 第 21–22 行；U359 范围声明","NO：不在 D003 失败传播链","S5 登记表注明 S2 闭合不含除数数值安全，保持 OPEN","NO"),
 ("S5-D-01","NEEDS_TEST","D003 的三条验收标准需 S5 前端与回归实测/映射；现有证据为 S4 的 M1/M2/M3 E2E","P05_S4R9_M2_REPORT.md；P05_S4R9_M3b_REPORT.md；P05_ACCEPTANCE_MAP_S5R1.tsv","YES：P06/D004 以 P05/D003 为前置","S5R2 预注册并实测缺口点；注册表 P05 行与 D003 行状态文字见草案 2.1/2.5","YES"),
 ("S5-D-02","REGISTRY_ONLY","ISSUE_REGISTRY P04 行仍写 P05未启动，与当前阶段不符","ISSUE_REGISTRY.md 物理行 %d"%find(ISSUE,"上述有限范围关闭，P05未启动"),"NO：文字同步","更新该行为 P05 进行中（S5）","NO"),
 ("S5-D-03","REGISTRY_ONLY","R-P04-01 排期写 P05 主线之后，需与 S5 登记交叉引用","ISSUE_REGISTRY.md 物理行 %d"%find(ISSUE,"| R-P04-01 |"),"NO：排期文字","补交叉引用（见 P05-S5 登记表），不改范围","NO"),
 ("S5-D-04","REGISTRY_ONLY","R-P04-07 写默认不阻塞 P05，需与 S5 登记一致","ISSUE_REGISTRY.md 物理行 %d"%find(ISSUE,"| R-P04-07 |"),"NO：文字同步","保持原文；在 S5 登记表引用","NO"),
 ("S5-D-05","REGISTRY_ONLY","文末下一轮默认修复顺序 P05/D003 到 P06/D004 需更新为进入 S5","ISSUE_REGISTRY.md 物理行 %d"%find(ISSUE,"下一轮默认修复顺序仍为 P05/D003"),"NO：文字同步","更新为 P05 进入 S5；P05 收口后进入 P06/D004","NO"),
 ("S5-D-06","NEEDS_TEST","PROJECT_ROADMAP P05 行的验收标准需逐条映射到已提交证据；当前状态列仍写待执行","PROJECT_ROADMAP.md 物理行 %d"%find(ROAD,"| P05 | Phase 2 A"),"YES：P06/D004 以 P05 为前置","更新 P05 行状态文字（见草案 3.1）；验收映射见 P05_ACCEPTANCE_MAP_S5R1.tsv","YES"),
]
CLASSES=["REGISTRY_ONLY","NEEDS_TEST","NEEDS_FIX_NEW_DEFECT","RECORD_ONLY_OPEN","NEEDS_USER_RULING"]

ACCEPT=[
 ("AC-1","每个受影响的 prepare/execute 点有正负对照","P05_S4R9_M2_REPORT.md（F4 正式两遍 191/191 MATCH；M2-07 81 点）+ registries/s4r9/M2/（VERDICT_R9.tsv、M2_CONSOLIDATED_F4_R9.tsv）；P05_S4R9_M1R3_REPORT.md + registries/s4r9/M1R3/","MET","F4 上 M2 两遍与 M1R3 651 点均有已提交判定；范围限 M2 点族与 F4，不外推到其它树/布局"),
 ("AC-2","失败后模式/缓存不安装","P05_S3_4b_CLOSURE.md（U29：202 注入点 I1–I6，HOLD 202 / VIOLATED 0）；P05_S4R9_M3c_REPORT.md + registries/s4r9/M3c/（READINESS GAP=0）","MET","U29 关闭声明与 M3c 就绪审计均在 F4 上；范围声明见 U29 原文"),
 ("AC-3","Python/Lua 可见失败，恢复重试正确","P05_S4R9_M3b_REPORT.md + registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv、PREREG_E2E_R9M3B.tsv；M3c 独立复核（U352，DIFFS=0）","NEEDS_USER_RULING","证据是 S4 的 M3a/M3b 结果；能否作为 S5 前端与回归证据需用户裁决（AC-4）"),
 ("AC-4","M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归的已提交证据","P05_S4R9_M3a_REPORT.md（make test 175 单元、NO_NEW_FAILURE）；P05_S4R9_M3b_REPORT.md（E2E_OK=25、CONTROL_OK=17、新红点 0）","NEEDS_USER_RULING","利：F4 上已跑过真实前端、有预注册与独立复核，S5 重跑成本高；弊：S5 若只引用 S4 证据，则修复前证据不得称修复后验证的界线易被模糊，且 M3b 的 Lua REPL 只覆盖 cf/fft/kt/vl 四族。执行者不自行认定"),
]

def write_tables():
 rows=INV
 hdr=["input_id","group","canonical_name","source_file","source_locator","source_ruling","current_status_text"]
 body=[TAB.join(hdr)]
 for r in rows:
  body.append(TAB.join([r["iid"],r["group"],r["name"],r["source_file"],r["locator"],r["ruling"],r["status"]]))
 put("S5_INPUTS_S5R1.tsv",NL.join(body)+NL)
 gc={}
 for r in rows: gc[r["group"]]=gc.get(r["group"],0)+1
 dd=["# S5_INPUTS_DEDUP_S5R1.txt -- P05-S5 R1 input de-duplication record","# pre-dedup rows=%d ; merged rows=%d ; unique rows=%d"%(PRE_ROWS,len(MERGES),len(rows)),""]
 for keep,parts in MERGES:
  dd.append("MERGE %s <- %s"%(keep," | ".join(parts)))
 dd+=["","GROUP_COUNTS "+" ".join("%s=%d"%(k,gc[k]) for k in sorted(gc)),
      "PRE_DEDUP_ROWS=%d"%PRE_ROWS,"MERGED_ROWS=%d"%len(MERGES),"UNIQUE_ROWS=%d"%len(rows),
      "NOTE S5-M3D-03 是去重后的合并行；U99（pattern.c:798）与 U100（Pattern_DiscretizeCell -1..-9）是同一 ES3R4-5/528/1164 移交族内的子项，其来源裁决已由 S5_HANDOFF_R9M3D.tsv 的 source_ruling（U90/U95/U99/U100）覆盖，故不另立行。"]
 put("S5_INPUTS_DEDUP_S5R1.txt",NL.join(dd)+NL)
 hdr=["input_id","class","rationale","evidence_ref","blocks_P06_D004","proposed_registry_action","needs_user_ruling"]
 body=[TAB.join(hdr)]
 for t in TRIAGE: body.append(TAB.join([t[0],t[1],t[2],t[3],t[4],t[5],t[6]]))
 put("S5_TRIAGE_S5R1.tsv",NL.join(body)+NL)
 hdr=["ac_id","acceptance_criterion","committed_evidence","status","notes"]
 body=[TAB.join(hdr)]
 for a in ACCEPT: body.append(TAB.join(list(a)))
 put("P05_ACCEPTANCE_MAP_S5R1.tsv",NL.join(body)+NL)

def counts():
 gc={}
 for r in INV: gc[r["group"]]=gc.get(r["group"],0)+1
 cc={}
 for t in TRIAGE: cc[t[1]]=cc.get(t[1],0)+1
 yes=sum(1 for t in TRIAGE if t[6]=="YES")
 blk=sum(1 for t in TRIAGE if t[4].startswith("YES"))
 ac={}
 for a in ACCEPT: ac[a[3]]=ac.get(a[3],0)+1
 return gc,cc,yes,blk,ac

GC,CC,YES,BLK,AC=counts()

def draft_patch():
 d16i=find(ISSUE,"| D016 / P1")
 d3=find(ISSUE,"| D003 / P1")
 p04=find(ISSUE,"上述有限范围关闭，P05未启动")
 rp0401=find(ISSUE,"| R-P04-01 |")
 rp0407=find(ISSUE,"| R-P04-07 |")
 nxt=find(ISSUE,"下一轮默认修复顺序仍为 P05/D003")
 rpi=find(ISSUE,"| R-P05-01（P05-S1R")
 prow=find(ROAD,"| P05 | Phase 2 A")
 d16r=find(ROAD,"**D016**")
 t=[]
 t.append("# P05-S5 R1 注册表补丁草案（P05_S5_REGISTRY_PATCH_DRAFT）")
 t.append("")
 t.append("> 本文件只写草案，不应用到测试登记表与路线图。")
 t.append("> 行号取自本轮 git rev-parse HEAD = 59e742d5b918b9c194f3aec10148801f7839f263（P05-S4 R9 M3e (ii)）。")
 t.append("> 本文件不含 P05 完成、已签收 P05-S5 之类字样；P05-S5 未完成、未签收。")
 t.append("")
 t.append("## 1. 依据与口径")
 t.append("")
 t.append("- 签收范围声明原文：checkpoints/p05/P05_S3_S4_SIGNOFF.md 第 2 节（物理行 18；逐字照录，本草案不改写）。")
 t.append("- S1/S2 范围声明原文：checkpoints/p05/P05_S1_S2_SIGNOFF.md 第 2 节（物理行 21–25）。")
 t.append("- B 列观察不是修复证据（U359 范围声明 (a)）；S5 只做前端与回归，不重跑 B 树。")
 t.append("- 本草案的新增登记行一律不写已修复/已验证，只写已实施（源码确认）或未验证/未实测，并注明证据。")
 t.append("")
 t.append("## 2. testing/s4test/ISSUE_REGISTRY.md 逐条 unified diff 草案")
 t.append("")
 t.append("### 2.1 D003 行（物理行 %d）状态与关闭范围核对"%d3)
 t.append("")
 t.append("依据：P05_S3_S4_SIGNOFF.md 第 2 节 (a)(f)；P05_S4R9_M2_REPORT.md（F4 正式两遍 191/191 MATCH）；P05_S4R9_M3b_REPORT.md（E2E_OK=25、CONTROL_OK=17）。")
 t.append("")
 t.append(FENCE+"diff")
 t.append("--- a/testing/s4test/ISSUE_REGISTRY.md")
 t.append("+++ b/testing/s4test/ISSUE_REGISTRY.md")
 t.append("@@ -%d,1 +%d,2 @@"%(d3,d3))
 t.append(" | D003 / P1 | FFT prepare/execute 失败处理及上层传播不完整 | checkpoint 已含 FFT wrapper/kiss FFT/网格路径的部分处理。历史六文件 FMM 候选和 runner 存在；完整候选未生产验收/集成 | 列实际计算分支、计划/执行调用点；复用候选与现有注入器，补缺口；失败不得安装模式/缓存；恢复后重试与全新对象一致；Python/Lua 报错可见 |")
 t.append("+> 2026-10-18 P05-S4 R9 收尾记录：S3-4b（失败后模式/缓存不安装）由 U29 在 F4 上带范围声明关闭（202 注入点 HOLD 202/VIOLATED 0）；F4 上 M2 正式两遍 191/191 MATCH、M1R3 651 点两遍全 MATCH；Python/Lua 前端由 M3b E2E 覆盖（E2E_OK=25、CONTROL_OK=17）。签收范围声明见 P05_S3_S4_SIGNOFF.md 第 2 节。D003 本身仍为 OPEN；P05-S5 是否以 S4 证据作为前端与回归证据待用户裁决（Q1）。")
 t.append(FENCE)
 t.append("")
 t.append("### 2.2 D016 行（物理行 %d）核对结果"%d16i)
 t.append("")
 t.append("- 核对结论：D016 的最小修法已在 P05-S3R2 提交 3e77aa9 实施（S4/pattern/pattern.c：max_field 零/非有限时返回 -10；负值为分配失败 -11）。F4 源码位置：S4/pattern/pattern.c 物理行 2210–2216（[源码]，本轮未运行）。")
 t.append("- 过期文字：现行 D016 行仍写待 P05-S3 实施/实施前状态为未关闭，需更新。")
 t.append("- 未实测项：D016 的公共异常文本（Python）在 S3R2 未实测（P05_S3R2_CLOSEOUT.md 物理行 186、187）；列入 S5R2 NEEDS_TEST（Q2）。")
 t.append("- 依据：P05_S3R2_CLOSEOUT.md 物理行 17、38、104、186；S4/pattern/pattern.c 2210–2216。")
 t.append("")
 t.append(FENCE+"diff")
 t.append("@@ -%d,1 +%d,1 @@"%(d16i,d16i))
 t.append(" | D016 / P1（P05 期间提前登记；P05-S5 时核对） | 图案层向量场归一化遇到全零场时除以零得到 NaN 并仍返回成功 ... | 2026-10-11 P05-S1R 实测 ... | 最小修法（待 P05-S3 实施 ...）： ... 实施前状态为未关闭 |")
 t.append("+ | D016 / P1（P05-S5 核对完成） | 图案层向量场归一化遇到全零场时除以零得到 NaN 并仍返回成功 | 2026-10-11 P05-S1R 实测：VL 基 n_G=1 时 max_field=0，NaN 进入特征值求解，info=2、rc 20（B/A/H 三树一致）。修法已实施：P05-S3R2 提交 3e77aa9，pattern.c 的 1./max_field 之前检查 max_field 为零/非有限并返回 -10（负值为分配失败 -11）；F4 源码位置 pattern.c 2210–2216（[源码]）。公共异常文本（Python）尚未实测 | 现状：已实施（源码确认），未做 D016 的 Python 文本实测；S5R2 补测（Q2）。R-P05-01（让 n_G=1 可计算）不包含在本条，见 ISSUE_REGISTRY 第 %d 行 |"%rpi)
 t.append(FENCE)
 t.append("")
 t.append("### 2.3 非 FMM S4_malloc 另立登记项（新增行草案）")
 t.append("")
 t.append("- 依据：用户范围决策（STATE.md 范围决策摘要；S5_HANDOFF_R9M3D.tsv S5-M3D-04）：分配/调用点处于模式或缓存是否被安装的验收路径或 FMM/FFT 失败传播链则纳入 D003，非 FMM 其余约 35–43 处不属 D003/P05。")
 t.append("- 编号：建议 D017（ISSUE_REGISTRY.md 更新规则：新缺陷追加 D016 起；具体编号请用户批准，Q7）。")
 t.append("")
 t.append(FENCE+"diff")
 t.append("@@ -%d,0 +%d,1 @@ （在 D016 行之后插入）"%(d16i,d16i+2))
 t.append("+| D017 / P2（P05-S5 期间登记；不在 P05 修） | 非 FMM 路径的 S4_malloc 失败未逐点检查/未统一传播（约 35–43 处，非 D003 范围） | 用户范围决策：只有处于模式/缓存是否被安装验收路径或 FMM/FFT 失败传播链上的分配点纳入 D003；非 FMM 其余分配点不属 D003/P05。未验证：未逐点列出调用位置与失败行为 | S5 登记：逐点列出函数:行号、调用者与失败后果；按 P0/P1/P2 风险分级；不在 P05 修，不阻塞 P06 |")
 t.append(FENCE)
 t.append("")
 t.append("### 2.4 ES3R4-5/528/1164、U99、U100 登记（新增行草案）")
 t.append("")
 t.append("- 依据：RULINGS.tsv U90（528/1164 OUT_OF_SCOPE_D003 转 P05-S5）、U95（ES3R4-5(a)(b)）、U99（pattern.c:798 内层循环用 i 而非 j；修它会改变正常路径）、U100（FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9，仅 -12 被处理）；ERRATA_S3R4.txt ES3R4-5、ES3R4-8。")
 t.append("- 共同点：均不在 D003 的失败传播链上，不属 P05 修复范围；只在登记表写明现状。")
 t.append("")
 t.append(FENCE+"diff")
 t.append("@@ -%d,0 +%d,1 @@ （在 D016/D017 之后插入；具体位置按最终编号顺序）"%(d16i,d16i+3))
 t.append("+| R-P05-02（P05-S5 期间登记，2026-10-18） | ES3R4-5/528/1164 既有问题（OUT_OF_SCOPE_D003）：(a) pattern_get_containment_tree 第一个形状无效时返回 i+1=1，被 InitSolution 上报为内存分配失败；(b) pattern.c:798 内层循环 for(j = i+1; i < nshapes; ++i) 用 i 作条件与自增，nshapes>1 时只有 shape 0 被检查（U95/U99）；528 shape_get_intersection_area 无调用者（死代码）；1164 fprint_double 唯一调用点被注释（U90） | 未验证/未修复：U99 明确修它会改变正常路径（既有输入可能新报错），故不在 P05-S3/S4 修。pattern.c:798 为 [源码] 事实 | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |")
 t.append("+| R-P05-03（P05-S5 期间登记，2026-10-18） | FFT/Kottke 忽略 Pattern_DiscretizeCell 的 -1..-9 返回值：fmm_FFT.cpp 与 fmm_kottke.cpp 只在返回 -12 时设 ret=1 并 goto cleanup，其余负值保持原行为（ES3R4-8；U100） | 未验证：U100 只要求写 [源码] 说明各返回码经公共 API 的可达性（文件:行号），未运行 | S5 登记，保持 OPEN；不在 P05 修，不阻塞 P06 |")
 t.append(FENCE)
 t.append("")
 t.append("### 2.5 P05 相关状态文字同步（ISSUE_REGISTRY 物理行 %d、%d、%d、%d）"%(p04,rp0401,rp0407,nxt))
 t.append("")
 t.append(FENCE+"diff")
 t.append("@@ -%d,1 +%d,1 @@"%(p04,p04))
 t.append("- ... 主测试total257/pass256/skip1 ...；上述有限范围关闭，P05未启动 |")
 t.append("+ ... 主测试total257/pass256/skip1 ...；上述有限范围关闭；P05 已启动，当前处于 P05-S5（前端与回归，仅改文档）。 |")
 t.append("@@ -%d,1 +%d,1 @@"%(rp0401,rp0401))
 t.append("- ... | P05 主线之后安排 RNP 防御专项；若正常受支持输入可达内存破坏则提前 |")
 t.append("+ ... | P05 收口之后安排 RNP 防御专项（P05-S5 登记表引用本条）；若正常受支持输入可达内存破坏则提前 |")
 t.append("@@ -%d,1 +%d,1 @@"%(nxt,nxt))
 t.append("- 下一轮默认修复顺序仍为 P05/D003 到 P06/D004；P05 应核对实际 FMM/FFT 失败传播和已登记 VL NB1 可达性。")
 t.append("+ 下一轮默认修复顺序：P05 进入 S5 收口（前端与回归），随后 P06/D004；P05 的 FMM/FFT 失败传播与 VL NB1 可达性已在 S3/S4 登记。")
 t.append(FENCE)
 t.append("")
 t.append("## 3. PROJECT_ROADMAP.md 逐条 unified diff 草案")
 t.append("")
 t.append("### 3.1 P05 行（物理行 %d）当前状态文字"%prow)
 t.append("")
 t.append("依据：PROJECT_ROADMAP.md P05 行第 4 列（验收和交付物）与第 5 列（当前状态）；P05_ACCEPTANCE_MAP_S5R1.tsv；P05_S3_S4_SIGNOFF.md 第 2 节。")
 t.append("")
 t.append(FENCE+"diff")
 t.append("@@ -%d,1 +%d,1 @@"%(prow,prow))
 t.append(" | P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | 待执行；优先复用已有候选 |")
 t.append("+ | P05 | Phase 2 A：D003 | 核对现有六文件 FMM 候选和 checkpoint 差异；针对实际启用的 FFT/Jones/NV/VL 等分支完成失败传播/清理/重试验证 | 每个受影响的 prepare/execute 点有正负对照；失败后模式/缓存不安装；Python/Lua 可见失败，恢复重试正确 | P04；固定选项、全新对象避免依赖 D004 | P05-S1 至 S4 已由用户签收（带范围声明，见 P05_S3_S4_SIGNOFF.md 第 2 节）；P05-S5 进行中（R1 输入盘点与分类）；验收映射见 checkpoints/p05/registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv |")
 t.append(FENCE)
 t.append("")
 t.append("### 3.2 D016 与 R-P05-01（物理行 %d 至 %d）"%(d16r,d16r+2))
 t.append("")
 t.append("- D016：路线图文字最小修法进入 P05-S3，具体改动需用户批准；见登记表 已过期——修法已于 P05-S3R2 提交 3e77aa9 实施；P05-S5 只核对，不改写历史。")
 t.append("- R-P05-01：保持未验证，暂不处理，在 S5 登记表保持 OPEN；不在 S5 修。")
 t.append("")
 t.append("## 4. 不在本草案范围")
 t.append("")
 t.append("- 不改写 P05_S3_S4_SIGNOFF.md 第 2 节签收原文、不改写 RULINGS.tsv、不改写任何历史报告。")
 t.append("- 不加新 U 编号（本轮没有用户新裁决）。")
 t.append("- 不宣布 P05-S5 或 P05 完成；不写已签收 P05-S5。")
 t.append("")
 return NL.join(t)+NL

def draft_plan():
 t=[]
 t.append("# P05-S5 计划草案（P05_S5_PLAN_DRAFT）")
 t.append("")
 t.append("> 本文件是 S5R2 及收口的计划草案，不表示任何阶段完成或签收。")
 t.append("> 输入：checkpoints/p05/registries/s5r1/S5_INPUTS_S5R1.tsv、S5_TRIAGE_S5R1.tsv、P05_ACCEPTANCE_MAP_S5R1.tsv。")
 t.append("")
 t.append("## 1. S5R2 范围（NEEDS_TEST 项）")
 t.append("")
 t.append("本轮分类统计：REGISTRY_ONLY=%d、NEEDS_TEST=%d、NEEDS_FIX_NEW_DEFECT=%d、RECORD_ONLY_OPEN=%d、NEEDS_USER_RULING=%d；needs_user_ruling=YES 共 %d 行；blocks_P06_D004=YES 共 %d 行。"%(CC.get("REGISTRY_ONLY",0),CC.get("NEEDS_TEST",0),CC.get("NEEDS_FIX_NEW_DEFECT",0),CC.get("RECORD_ONLY_OPEN",0),CC.get("NEEDS_USER_RULING",0),YES,BLK))
 t.append("")
 t.append("NEEDS_TEST 项（S5R2 预注册并实测）：")
 t.append("")
 t.append("| 编号 | 事项 | 期望值登记方式 |")
 t.append("|---|---|---|")
 t.append("| S5-C-01 | D016 的 Python 公共异常文本（n_G=1 零场） | 运行前写 PREREG_S5R2_D016.tsv 并记录 sha256；期望：公共 API 抛 RuntimeError、驱动 rc 20、根因处返回 -10（源码映射） |")
 t.append("| S5-D-01 | D003 验收标准的前端观测（Python/Lua 可见失败、恢复重试） | 运行前写 PREREG_S5R2_E2E.tsv + sha256；期望：注入点 rc 非零且 Python/Lua 可见同一错误；同对象重试等于参考值；新对象/新进程重试等于参考值 |")
 t.append("| S5-D-06 | PROJECT_ROADMAP P05 行验收标准的逐条映射 | 映射表本身在 S5R1 已提交（P05_ACCEPTANCE_MAP_S5R1.tsv），S5R2 只做增量核对；不改写验收标准 |")
 t.append("")
 t.append("## 2. 需要的驱动与前端")
 t.append("")
 t.append("- Python：公共 API 正常路径 + 注入失败路径 + 同对象重试 + 新进程重试；覆盖 FFT/Jones/NV/VL 点族（沿用 testing/d003/stage_s4r9/e2e_python_r9m3b.py 的装置思路，新脚本按 S5R2 编号另建，不改历史装置）。")
 t.append("- Lua：REPL 覆盖 cf/fft/kt/vl 四族（与 U345/U359(e) 的范围声明一致）；失败、可见报错、重试恢复。")
 t.append("- 预注册：所有期望值必须先写入预注册 tsv 并记录 sha256；受历史观察影响的标 INFLUENCED；不得事后改期望（只允许新建 *_ERRATA*）。")
 t.append("")
 t.append("## 3. 预计运行量")
 t.append("")
 t.append("- S5R2 前端点族：Python 每族正常/失败/同对象重试/新进程重试 4 类，5 族约 20 点；Lua REPL 4 族约 8 点；合计约 28 点，两遍约 56 次运行。")
 t.append("- 若 Q1 裁决为需独立复跑以作 S5 证据，则追加 M3b E2E 的 25 点两遍（约 50 次）。")
 t.append("- 复用既有驱动/库时先核对 sha256，不重建 S4 产物（S5 只读 F4 冻结树）。")
 t.append("")
 t.append("## 4. S5 收口条件（草案，待用户确认）")
 t.append("")
 t.append("1. NEEDS_TEST 项全部完成预注册 + 正式实测，预期值一致（MISMATCH 0）。")
 t.append("2. NEEDS_USER_RULING 项全部经用户裁决，或明确保持开放并写入 S5 报告的范围声明。")
 t.append("3. P05_ACCEPTANCE_MAP_S5R1.tsv 的 GAP 行清零或经用户裁决；NEEDS_USER_RULING 行（AC-3/AC-4）有裁决结论。")
 t.append("4. 仅改文档/登记表的项（REGISTRY_ONLY、RECORD_ONLY_OPEN、NEEDS_FIX_NEW_DEFECT）写入登记表草案并落实。")
 t.append("5. STATE.md 不超过 8192 B；门禁 CHECK_CRASHED=0；证据 SHA256SUMS 全 OK。")
 t.append("6. 不宣布 P05 完成；P05-S5 签收只由用户在对话中给出。")
 t.append("")
 t.append("## 5. 需用户裁决的问题（Q1..Q8，附推荐）")
 t.append("")
 t.append("| 编号 | 问题 | 推荐选项与理由 |")
 t.append("|---|---|---|")
 t.append("| Q1 | M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归的已提交证据？ | 推荐：可引用，但 S5R2 至少复跑一遍前端 E2E。理由：M3b 在 F4 上有预注册与 U352 独立复核（DIFFS=0），完全重审成本高；但修复前证据不得称修复后验证，S5 若零运行只引用旧证据，界线会模糊。 |")
 t.append("| Q2 | D016 的 Python 公共异常文本是否需在 S5R2 实测？ | 推荐：需要。理由：S3R2 只做了源码映射与驱动级观测（P05_S3R2_CLOSEOUT.md 186/187 行），而 P05 验收含 Python/Lua 可见失败，D016 正是可见失败点。 |")
 t.append("| Q3 | F10 历史因果（S5-B-01）是否需在 S5 补历史输入？ | 推荐：不需要，保持 OPEN 并转后续。理由：D016 修法不依赖 F10 因果；提供历史负载输入的成本高且不在 S5 范围。 |")
 t.append("| Q4 | F8 历史候选目录哈希（S5-B-02）是否授权访问历史目录？ | 推荐：不授权，保持未验证。理由：S5 修复对象是当前仓库源码，不引用历史候选目录的 bit 级一致性。 |")
 t.append("| Q5 | R-P05-01 的反事实通量正确性 + allzero 设计意图是否在 S5 处理？ | 推荐：不在 S5 处理，保持 OPEN。理由：需独立参考解与设计意图确认，属行为变更而非失败传播；S5 只登记。 |")
 t.append("| Q6 | S1 报告 11.2 的 5 个哈希来源（S5-B-05..09）如何处置？ | 推荐：用户确认来源或明确保持未验证，不改写 11.2 与 EVIDENCE.sha256。理由：现有证据无法区分抄写错误与较早时刻内容。 |")
 t.append("| Q7 | 非 FMM S4_malloc（S5-M3D-04）另立登记号是否用 D017？ | 推荐：D017。理由：ISSUE_REGISTRY 更新规则规定新缺陷从 D016 起追加；D016 已被占用。 |")
 t.append("| Q8 | ES3R4-5/528/1164、U99、U100（S5-M3D-03）登记为独立 R-P05-02/R-P05-03 是否可接受？ | 推荐：可接受。理由：它们均 OUT_OF_SCOPE_D003，不是 P05 修复项，独立登记可保持 D003 范围清晰。 |")
 t.append("")
 t.append("## 6. 预注册与文件命名")
 t.append("")
 t.append("- 预注册文件：checkpoints/p05/registries/s5r2/PREREG_S5R2_*.tsv + .sha256.txt，在正式运行之前提交。")
 t.append("- 运行脚本：testing/d003/stage_s5r2/，文件名带 s5r2；门禁与收尾链同 S5R1 结构。")
 t.append("- 证据目录：checkpoints/p05/evidence/p05-s5r2/；小表复制到 checkpoints/p05/registries/s5r2/。")
 t.append("")
 return NL.join(t)+NL

def cmd_drafts():
 p1=draft_patch(); p2=draft_plan()
 if SHAKE:
  wr(os.path.join(SHK,"P05_S5_REGISTRY_PATCH_DRAFT.proposed.md"),p1)
  wr(os.path.join(SHK,"P05_S5_PLAN_DRAFT.proposed.md"),p2)
 else:
  wr(os.path.join(P05,"P05_S5_REGISTRY_PATCH_DRAFT.md"),p1)
  wr(os.path.join(P05,"P05_S5_PLAN_DRAFT.md"),p2)
 print("DRAFTS patch=%d bytes plan=%d bytes shake=%s"%(len(p1.encode()),len(p2.encode()),SHAKE))

def errata_recheck():
 p=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e/safe_run.log")
 lines=rd(p).splitlines()
 def ln_of(s):
  for i in range(len(lines),0,-1):
   if s in lines[i-1]: return i
  return 0
 names=["report","report_check","copy","events","progress","sha_sums"]
 found={}
 for i in range(len(lines),0,-1):
  l=lines[i-1]
  if "m3e_chain_r9m3e.py " in l:
   sub=l.split("m3e_chain_r9m3e.py ",1)[1].split()[0]
   if sub in names and sub not in found: found[sub]=i
 chain=[found.get(n,0) for n in names]
 gate=ln_of("gate_r9m3e.sh end")
 gatefile=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e/gate/GATE_R9M3E_end.txt")
 gl=rd(gatefile).splitlines()
 call14=[l for l in gl if "CALL_LINES_M3E_CHAIN_R9M3E_-" in l]
 call14v=(call14[0].split(TAB)[2] if call14 else "MISSING")
 out=["# ERRATA_RECHECK_S5R1.txt -- independent read-only recomputation for E9-78/E9-79 (no M3e rerun, no M3e product change)","",
      "M3E_SAFE_RUN_LOG_LINES=%d"%len(lines),
      "CHAIN_CALL_LINES="+",".join(str(x) for x in chain),
      "CHAIN_CALL_COUNT=%d"%sum(1 for x in chain if x>0),
      "GATE_END_CALL_LINE=%d"%gate,
      "GATE_R9M3E_end_LINE14="+(call14[0] if call14 else "MISSING"),
      "GATE_LINE14_VALUE="+call14v,
      "LINE1_HEAD="+lines[0][:200],
      "LINE2_HEAD="+lines[1][:200],
      "LINE3_HEAD="+lines[2][:200],
      "GATE_CHECK_LINE244_REF=gate_check_r9m3e.py:244 safe(POST_I_CALL_COUNT_+key,mkc(),r[expect]) -> tuple not callable",
      "CONCLUSION=E9-78 tuple-not-callable checker defect; E9-79 safe_run bash -c outer expansion. Registered only; M3e not rerun."]
 return out

def cmd_errata():
 p=os.path.join(REG,"s4r9/ERRATA_9.txt")
 t=rd(p)
 rc=errata_recheck()
 put("ERRATA_RECHECK_S5R1.txt",NL.join(rc)+NL)
 chain=rc[3].split("=",1)[1]; gline=rc[5].split("=",1)[1]
 b78="E9-78"+NL+\
 "- 事实：M3e end 门禁的 POST_I_CALL_COUNT_GATE_R9M3E_END 与 POST_I_CALL_COUNT_M3E_CHAIN_R9M3E_- 两项 FAIL 是检查器缺陷，不是事实 FAIL：gate_check_r9m3e.py 第 244 行把 mkc() 的返回元组当作可调用对象传入 safe()，safe() 内 fn() 抛 TypeError: 'tuple' object is not callable。根因是试跑期未实跑 end 门禁的 POST_I 块（m3e/shakedown/ 下无 end 门禁输出），POST_I 计数路径从未被执行。用脚本从 m3e/safe_run.log 只读复算：提交 (i) 之后 chain 6 次（第 "+chain.split(",")[0]+"–"+chain.split(",")[-1]+" 行）、gate end 1 次（第 "+gline+" 行）；GATE_R9M3E_end.txt 第 14 行 CALL_LINES_M3E_CHAIN_R9M3E_- 为空，与检查器在写 CALL_LINES 之前崩溃一致。"+NL+\
 "- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m3e/gate/GATE_R9M3E_end.txt 第 14 行、第 49–50 行；checkpoints/p05/evidence/p05-s4r9/m3e/safe_run.log 第 "+chain.split(",")[0]+"–"+chain.split(",")[-1]+" 行（chain）、第 "+gline+" 行（gate end）；testing/d003/stage_s4r9/gate_check_r9m3e.py 第 244 行；复算见 checkpoints/p05/evidence/p05-s5r1/ERRATA_RECHECK_S5R1.txt。"+NL+\
 "- 影响范围：只影响 M3e end 门禁的两项 POST_I 调用计数结论；M3e 的提交产物与事实表不受影响。"+NL+\
 "- 处理方式：只登记勘误；不重跑 M3e，不改 M3e 任何产物。修正方式见 P05-S5 R1 任务书第 2 节第 3 条（safe(name, fn, exp) 的 fn 必须是可调用对象）与 S5R1 试跑实跑 end 门禁 POST_I 块。"
 b79="E9-79"+NL+\
 "- 事实：M3e 表一 3 次越界写入尝试（m3e/safe_run.log 第 1、2、3 行，均未落盘）的成因是 safe_run 接 bash -c 时外层 shell 先展开 $REPO/$EV，变量为空后目标变成 /checkpoints/... 与 /tmp。修正方式见 P05-S5 R1 任务书第 2 节第 1 条：safe_run 后直接接 python3 -c / python3 -I -B / sh 脚本，禁止 safe_run -- bash -c；脚本内部路径一律由 git rev-parse --show-toplevel 求得并断言允许前缀。"+NL+\
 "- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m3e/safe_run.log 第 1、2、3 行；P05_S4R9_M3e_REPORT.md 第 5.1 节表一。"+NL+\
 "- 影响范围：只记录越界尝试的成因与修正方式；不改变 M3e 任何产物，/tmp 顶层保持 0 条目。"+NL+\
 "- 处理方式：只登记勘误，不重跑 M3e。"
 if "E9-78" in t or "E9-79" in t:
  print("ERRATA already contains E9-78/E9-79; no append")
  return
 if not t.endswith(NL): t+=NL
 t=t+NL+b78+NL+NL+b79+NL
 if SHAKE: wr(os.path.join(SHK,"ERRATA_9_proposed.txt"),t)
 else: wr(p,t)
 print("ERRATA appended E9-78/E9-79; bytes=%d"%len(t.encode()))

def state_text():
 t=[]
 t.append("# P05 当前状态（每轮结束更新，一页以内）")
 t.append("")
 t.append("> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。")
 t.append("")
 t.append("## 1. 当前位置")
 t.append("")
 t.append("| 项 | 值 |")
 t.append("|---|---|")
 t.append("| 分支 | codex/p05-d003-fft-error-propagation |")
 t.append("| 本轮开工基线 HEAD（s5r1） | 59e742d5b918b9c194f3aec10148801f7839f263（P05-S4 R9 M3e (ii)） |")
 t.append("| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |")
 t.append("| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |")
 t.append("| 阶段状态 | S1–S4 已由用户签收（带范围声明，见 P05_S1_S2_SIGNOFF.md、P05_S3_S4_SIGNOFF.md）；S5 进行中（R1 盘点） |")
 t.append("| 签收文件 | P05_S1_S2_SIGNOFF.md、P05_S3_S4_SIGNOFF.md（第 2 节范围声明逐字照录） |")
 t.append("| 当前轮次 | P05-S5 R1（s5r1）：S5 输入只读盘点、分类分流、登记表补丁草案、勘误 E9-78/E9-79、S5 计划草案；未运行 S4 任何程序 |")
 t.append("")
 t.append("## 2. 关键数字（每轮一行）")
 t.append("")
 t.append("| 轮 | 关键数字 | 报告/证据 |")
 t.append("|---|---|---|")
 t.append("| R1–R5 | R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24 | P05_S4R2…S4R5_REPORT.md |")
 t.append("| R6–R6d | twice 48 MATCH；R6d 202 一致 | P05_S4R6…R6d |")
 t.append("| S3R3–S3R5 | F2 36/36；F3 117/117；F4 05097a7 | S3R3/S3R4/S3R5 CLOSEOUT |")
 t.append("| S4R7–R8 | MISMATCH 0；正式两遍 202 点全 MATCH | P05_S4R7/S4R8 报告 |")
 t.append("| S4R9 M0–M2 | 无注入 146/146；正式两遍 191/191 MATCH | P05_S4R9_M2_REPORT.md |")
 t.append("| S4R9 M2b–M2c | HIT 等价 173/173；READINESS MET=14 GAP=0 | M2b/M2c 报告 |")
 t.append("| S4R9 M3a–M3b | make test 175 单元 NO_NEW_FAILURE；E2E_OK=25、CONTROL_OK=17 | M3a/M3b 报告 |")
 t.append("| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |")
 t.append("| S5R1 | 输入 %d 行（去重前 %d）；分类 REGISTRY_ONLY=%d NEEDS_TEST=%d NEEDS_FIX_NEW_DEFECT=%d RECORD_ONLY_OPEN=%d NEEDS_USER_RULING=%d；勘误 E9-78/79 | P05_S5R1_REPORT.md |"%(len(INV),PRE_ROWS,CC.get("REGISTRY_ONLY",0),CC.get("NEEDS_TEST",0),CC.get("NEEDS_FIX_NEW_DEFECT",0),CC.get("RECORD_ONLY_OPEN",0),CC.get("NEEDS_USER_RULING",0)))
 t.append("")
 t.append("## 3. 开放问题（状态 · 去向 · 详情链接）")
 t.append("")
 t.append("| 项 | 状态 | 去向 | 详情链接 |")
 t.append("|---|---|---|---|")
 t.append("| S5 输入分类（%d 行；%d 行需用户裁决） | OPEN | 用户裁决 + S5R2 | registries/s5r1/S5_TRIAGE_S5R1.tsv |"%(len(INV),YES))
 t.append("| 验收映射 AC-3/AC-4（M3a/M3b E2E 能否作 S5 证据） | NEEDS_USER_RULING | 用户裁决 | registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv |")
 t.append("| P05 收口所需 Q1–Q8 | OPEN | 用户裁决 | P05_S5_PLAN_DRAFT.md 第 5 节 |")
 t.append("| 历史已关闭项 | CLOSED | 各轮报告 | P05_S3_S4_SIGNOFF.md 第 1/3 节 |")
 t.append("")
 t.append("## 4. 证据位置")
 t.append("")
 t.append("- **P05-S5 R1（s5r1）**：证据 checkpoints/p05/evidence/p05-s5r1/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r1/（SHA256SUMS.txt）；报告 P05_S5R1_REPORT.md；草案 P05_S5_REGISTRY_PATCH_DRAFT.md、P05_S5_PLAN_DRAFT.md。")
 t.append("- **P05-S4 R9 M3e**：证据 checkpoints/p05/evidence/p05-s4r9/m3e/；小表 checkpoints/p05/registries/s4r9/M3e/；报告 P05_S4R9_M3e_REPORT.md；签收 P05_S3_S4_SIGNOFF.md。")
 t.append("- 更早轮次：各轮报告；裁决总表 registries/RULINGS.tsv；勘误 registries/s4r9/ERRATA_9.txt；S5 移交 registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv。")
 t.append("")
 return NL.join(t)+NL

def cmd_state():
 p=os.path.join(P05,"STATE.md")
 t=state_text()
 if SHAKE: wr(os.path.join(SHK,"STATE.proposed.md"),t)
 else: wr(p,t)
 print("STATE bytes=%d"%len(t.encode()))

def frozen_rows():
 st="testing/d003/stage_s5r1"
 rows=[(st+"/gate_check_s5r1.py","0","-"),(st+"/gate_s5r1.sh","1","end"),(st+"/s5r1_appendix.py","0","-"),
       (st+"/s5r1_chain.py","6","-"),(st+"/s5r1_prep.py","1","all"),(st+"/s5r1_startgate.py","0","-")]
 out=["# FROZEN_SCRIPTS_S5R1.tsv -- frozen scripts after the shakedown chain, before record commit (i).",
      "# The end gate reads POST_I call expectations from this file BY COLUMN NAME (task brief section 5).",
      TAB.join(["path","sha256","expected_calls","mode"])]
 for path,exp,mode in rows:
  fp=os.path.join(REPO,path)
  if not os.path.isfile(fp): raise SystemExit("FROZEN_MISSING "+path)
  out.append(TAB.join([path,sha_f(fp),exp,mode]))
 return out

def cmd_frozen():
 body=NL.join(frozen_rows())+NL
 if SHAKE: wr(os.path.join(SHK,"FROZEN_SCRIPTS_S5R1.proposed.tsv"),body)
 else: wr(os.path.join(EV,"FROZEN_SCRIPTS_S5R1.tsv"),body)
 print("FROZEN rows=%d shake=%s"%(len(frozen_rows())-3,SHAKE))

def cmd_all():
 write_tables(); cmd_drafts(); cmd_errata(); cmd_state(); cmd_frozen()
 print("PREP all done shake=%s"%SHAKE)

def main():
 sub=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith("--") else "all"
 {"all":cmd_all,"inventory":write_tables,"triage":write_tables,"drafts":cmd_drafts,"errata":cmd_errata,"state":cmd_state,"frozen":cmd_frozen}.get(sub,cmd_all)()
 return 0
if __name__=="__main__": sys.exit(main())
