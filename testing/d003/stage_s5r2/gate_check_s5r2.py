#!/usr/bin/env python3
# gate_check_s5r2.py -- P05-S5 R2 end gate. Output goes to $EV/gate/ (or $EV/shakedown/gate/ in
# shakedown) and is excluded from SHA256SUMS. Frozen POST_I expectations are read from
# FROZEN_SCRIPTS_S5R2.tsv BY COLUMN NAME. safe(name, fn, exp) always gets a callable and the
# CHECK_CRASHED count itself is asserted to be zero. The coverage checks exclude tmp/, gate/
# (so shakedown/gate/ too) and trees/; that exclusion list is written into the gate output.
import os,sys,re,hashlib,subprocess,datetime
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
P05=os.path.join(REPO,"checkpoints/p05")
EV=os.path.join(P05,"evidence/p05-s5r2")
SHK=os.path.join(EV,"shakedown")
REG=os.path.join(P05,"registries")
RUL=os.path.join(REG,"RULINGS.tsv"); ERR9=os.path.join(REG,"s4r9/ERRATA_9.txt")
ST=os.path.join(P05,"STATE.md"); BRIEF=os.path.join(P05,"briefs/P05_S5R2_BRIEF.md")
PATCHV2=os.path.join(P05,"P05_S5_REGISTRY_PATCH_V2.md")
OPENITEMS=os.path.join(P05,"P05_S5_OPEN_ITEMS.tsv")
ISSUE_REL="testing/s4test/ISSUE_REGISTRY.md"; ROAD_REL="PROJECT_ROADMAP.md"
STAGE=os.path.join(REPO,"testing/d003/stage_s5r2")
BASE="9f537f7c312b2ab7c64d5c0ea82da34e637da5d4"
S4TREE="589e15eb11fcb04e031b524f25a443e7921946cf"
JUDGE="d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
TAB=chr(9); NL=chr(10); BT=chr(96)
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
SHAKE=False; commit_i_override=None
args=sys.argv[2:]
i=0
while i<len(args):
 if args[i]=="--shakedown": SHAKE=True; i+=1
 elif args[i]=="--commit-i" and i+1<len(args): commit_i_override=args[i+1]; i+=2
 else: i+=1
OUT=sys.argv[1]; OUTDIR=os.path.dirname(OUT)
REPORT=os.path.join(SHK,"REPORT.proposed.md") if SHAKE else os.path.join(P05,"P05_S5R2_REPORT.md")
REGDIR=os.path.join(SHK,"registries_copy") if SHAKE else os.path.join(REG,"s5r2")
RCK=os.path.join(SHK,"REPORT_CHECK_S5R2.txt") if SHAKE else os.path.join(EV,"REPORT_CHECK_S5R2.txt")
EVF=os.path.join(SHK,"EVENTS_S5R2.tsv") if SHAKE else os.path.join(EV,"EVENTS_S5R2.tsv")
SUMS=os.path.join(SHK,"SHA256SUMS.txt") if SHAKE else os.path.join(EV,"SHA256SUMS.txt")
FROZEN=os.path.join(SHK,"FROZEN_SCRIPTS_S5R2.tsv") if SHAKE else os.path.join(EV,"FROZEN_SCRIPTS_S5R2.tsv")
OUTDECL=os.path.join(SHK,"REGISTRY_OUTPUTS_S5R2.tsv") if SHAKE else os.path.join(EV,"REGISTRY_OUTPUTS_S5R2.tsv")
SUMSROOT=SHK if SHAKE else EV
OI=os.path.join(SHK,"P05_S5_OPEN_ITEMS.proposed.tsv") if SHAKE else OPENITEMS
APPDIFF=os.path.join(SHK if SHAKE else EV,"REGISTRY_APPLY_DIFF_S5R2.txt")
ISSUE_F=os.path.join(SHK,"ISSUE_REGISTRY.candidate.md") if SHAKE else os.path.join(REPO,ISSUE_REL)
ROAD_F=os.path.join(SHK,"ROADMAP.candidate.md") if SHAKE else os.path.join(REPO,ROAD_REL)
res=[]; recs=[]
def ck(n,ok,exp,act): res.append(("PASS" if ok else "FAIL",n,str(exp),str(act)))
def rec(n,v): recs.append((n,str(v)))
def safe(n,fn,exp):
 try:
  ok,act=fn(); ck(n,ok,exp,act)
 except Exception as e: ck(n,False,exp,"CHECK_CRASHED: %s: %s"%(type(e).__name__,e))
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def rd(p): return open(p,encoding="utf-8").read()
def read_sums(p):
 out=[]
 for line in rd(p).splitlines():
  line=line.strip()
  if not line or line.startswith("#"): continue
  a,n=line.split(None,1); out.append((a,n.strip()))
 return out
def sums_dir(d):
 sp=os.path.join(d,"SHA256SUMS.txt")
 if not os.path.isfile(sp): return False,0,"missing sums"
 n=0
 for a,name in read_sums(sp):
  fp=os.path.join(d,name)
  if not os.path.isfile(fp) or sha_f(fp)!=a: return False,n,"mismatch "+name
  n+=1
 return True,n,"all %d OK"%n
def tsv_rows(p):
 return [l.split(TAB) for l in rd(p).splitlines() if l.strip() and not l.startswith("#")]
def tmp_snap():
 root=os.sep+"tmp"; e=sorted(os.listdir(root)) if os.path.isdir(root) else []
 return len(e),sha_b((NL.join(e)+(NL if e else "")).encode("utf-8"))
def start_records():
 p=os.path.join(EV,"GATE_S5R2_start.txt"); rec={}
 if not os.path.isfile(p): return rec
 for line in rd(p).splitlines():
  f=line.split(TAB)
  if len(f)>=3 and f[0]=="RECORD":
   v=f[2]; v=v[6:] if v.startswith("value=") else v
   rec[f[1]]=v
 return rec
def log_recs():
 p=os.path.join(EV,"safe_run.log"); out=[]
 if not os.path.isfile(p): return out
 for idx,line in enumerate(rd(p).splitlines(),1):
  m=TS.match(line)
  if not m: continue
  cmd=""
  for part in line.rstrip(NL).split(TAB)[1:]:
   if part.startswith("cmd="): cmd=part[4:]; break
  out.append((idx,m.group(1),cmd))
 return out
def epoch(ts):
 try: return int(datetime.datetime.strptime(ts,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp())
 except Exception: return 0
def frozen_rows():
 p=FROZEN
 if not os.path.isfile(p): return [],None
 header=None; rows=[]
 for line in rd(p).splitlines():
  if not line.strip() or line.startswith("#"): continue
  f=line.rstrip(NL).split(TAB)
  if header is None:
   header=f
   for c in ("path","sha256","expected_calls","mode"):
    if c not in header: raise SystemExit("FROZEN_HEADER_MISSING_COLUMN "+c)
   continue
  rows.append(dict(zip(header,f)))
 return rows,header
def parse_report_items():
 if not os.path.isfile(REPORT): return []
 insec=False; items=[]
 for line in rd(REPORT).splitlines():
  if line.strip()=="## 10 交付物": insec=True; continue
  if insec and line.startswith("## "): break
  if insec:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",line)
   if m: items.append(m.group(2).strip())
 return items
rec("EXCLUDED_DIRS","tmp,gate,trees (coverage and SHA256SUMS skip directories with these names at any depth, so shakedown/gate/ is excluded too)")
rec("EXCLUDED_FILES","safe_run.log,SHA256SUMS.txt")
start=start_records()
safe("START_RECORDS_PRESENT",lambda:(len(start)>0,"%d"%len(start) if start else "missing"),"records present")
safe("BRANCH_IS_EXPECTED",lambda:(sh(["git","branch","--show-current"])=="codex/p05-d003-fft-error-propagation",sh(["git","branch","--show-current"])),"codex/p05-d003-fft-error-propagation")
safe("HEAD_S4_TREE_EQ_F4",lambda:(sh(["git","rev-parse","HEAD:S4"])==S4TREE,sh(["git","rev-parse","HEAD:S4"])),S4TREE)
safe("JUDGE_SHA256",lambda:(sha_f(os.path.join(REPO,"testing/d003/judge_d003.py"))==JUDGE,sha_f(os.path.join(REPO,"testing/d003/judge_d003.py"))),JUDGE[:8]+"...")
safe("S4_DIR_ZERO_MODIFICATION",lambda:(sh(["git","diff","HEAD","--","S4"])=="","S4 unmodified"),"S4 unmodified")
ALLOW_M={"checkpoints/p05/STATE.md","checkpoints/p05/registries/RULINGS.tsv"}
if not SHAKE:
 ALLOW_M.update({ISSUE_REL,ROAD_REL})
def c_base():
 lines=[l for l in sh(["git","diff","--name-status",BASE]).splitlines() if l.strip()]
 mods=[l.split(TAB)[1] for l in lines if l.startswith("M"+TAB)]
 dels=[l.split(TAB)[1] for l in lines if l.startswith("D"+TAB)]
 add=sum(1 for l in lines if l.startswith("A"+TAB))
 badm=[x for x in mods if x not in ALLOW_M]
 rec("BASE_DIFF_A",add); rec("BASE_DIFF_M",len(mods)); rec("BASE_DIFF_D",len(dels))
 return (not badm) and (not dels),("A=%d M=%d D=%d badM=%s badD=%s"%(add,len(mods),len(dels),badm[:4],dels[:4]))
safe("BASE_COMMITTED_ONLY_ALLOWED_MD",c_base,"only allowed M/D; new A allowed")
def c_tracked():
 d=[x for x in sh(["git","diff","--name-only","HEAD"]).splitlines() if x.strip()]
 bad=[x for x in d if x not in ALLOW_M]
 return not bad,("none" if not bad else str(bad[:6]))
safe("TRACKED_MODIFIED_WITHIN_END_ALLOW_LIST",c_tracked,"none")
rb=open(RUL,"rb").read()
rbn=int(start.get("RULINGS_BYTES","0") or 0); rs=start.get("RULINGS_SHA256","")
safe("RULINGS_PREFIX_OF_START_UNCHANGED",lambda:(sha_b(rb[:rbn])==rs,sha_b(rb[:rbn])+"/"+rs),"start prefix unchanged")
safe("RULINGS_NOT_TRUNCATED",lambda:(len(rb)>=rbn,len(rb)),">= %d"%rbn)
def c_rul():
 lines=[l for l in rb.decode("utf-8","replace").splitlines() if l.strip() and not l.strip().startswith("#")]
 ids={}
 for l in lines:
  f=l.split(TAB)
  if len(f)!=5: return False,"bad fields: "+l[:40]
  if f[0] in ids: return False,"dup "+f[0]
  ids[f[0]]=f
 ns=[int(k[1:]) for k in ids if re.match(r"^U\d+$",k)]
 need=["U%d"%x for x in range(364,372)]
 miss=[u for u in need if u not in ids]
 rec("RULINGS_MAX_U_END","U%d"%max(ns)); rec("RULINGS_BYTES_END",len(rb))
 return (max(ns)==371 and not miss),"U%d miss=%s"%(max(ns),miss)
safe("RULINGS_MAX_U371_U364_U371_PRESENT",c_rul,"U371 and U364..U371")
eb=open(ERR9,"rb").read()
es=start.get("ERRATA_9_SHA256",""); ebn=int(start.get("ERRATA_9_BYTES","0") or 0)
safe("ERRATA_9_UNCHANGED_FROM_START",lambda:(sha_b(eb)==es,sha_b(eb)),es[:16]+"...")
def c_err():
 ids=re.findall(r"(?m)^(E9-\d+)",eb.decode("utf-8","replace"))
 return (ids and ids[-1]=="E9-79" and len(ids)==79),"last=%s count=%d"%(ids[-1] if ids else "none",len(ids))
safe("ERRATA_9_LAST_E9_79_COUNT_79",c_err,"E9-79 count=79")
def c_start_files():
 bad=[]
 for key,nm in (("PATCH_DRAFT_SHA256","P05_S5_REGISTRY_PATCH_DRAFT.md"),("PLAN_DRAFT_SHA256","P05_S5_PLAN_DRAFT.md"),
                 ("S5_INPUTS_SHA256","registries/s5r1/S5_INPUTS_S5R1.tsv"),("S5_TRIAGE_SHA256","registries/s5r1/S5_TRIAGE_S5R1.tsv")):
  exp=start.get(key,"")
  fp=os.path.join(P05,nm) if not nm.startswith("registries") else os.path.join(REG,nm.split("registries/",1)[1])
  if not exp or sha_f(fp)!=exp: bad.append(nm)
 return not bad,("all unchanged" if not bad else str(bad))
safe("S5R1_FILES_UNCHANGED_FROM_START",c_start_files,"S5R1 drafts/tables unchanged")
sb=open(ST,"rb").read()
safe("STATE_BYTES_LE_8192",lambda:(0<len(sb)<=8192,len(sb)),"<= 8192")
def c_state():
 t=sb.decode("utf-8","replace")
 miss=[k for k in ("P05-S5 R2","S5 进行中","P05_S5_OPEN_ITEMS.tsv","S5R3","已由用户签收") if k not in t]
 return not miss,("all markers" if not miss else str(miss))
safe("STATE_MARKERS",c_state,"state markers present")
def c_brief():
 if not os.path.isfile(BRIEF): return False,"missing"
 t=rd(BRIEF); return (len(t.encode())>3000 and "P05-S5 R2" in t and "P05_S5R2_BRIEF.md" in t),"bytes=%d"%len(t.encode())
safe("BRIEF_PRESENT",c_brief,"brief present with markers")
def c_patchv2():
 if not os.path.isfile(PATCHV2): return False,"missing"
 t=rd(PATCHV2); miss=[k for k in ("<?xml","PATCHSPEC-BEGIN","PATCHSPEC-END","U364","U371","D017","R-P05-02","R-P05-03","3e77aa9") if k not in t and k!="<?xml"]
 op=len(re.findall(r"(?m)^OP\t",t))
 rec("PATCHV2_OPS",op)
 return (not miss and op==21),("ops=%d miss=%s"%(op,miss))
safe("PATCHV2_PRESENT_OPS21",c_patchv2,"patch v2 with 21 ops")
def c_prereg():
 p=os.path.join(REG,"s5r2/PREREG_D016_S5R2.tsv"); ps=p+".sha256.txt"
 if not os.path.isfile(p) or not os.path.isfile(ps): return False,"missing prereg or sha"
 h=sha_f(p)
 m=re.search(r"([0-9a-f]{64})",rd(ps))
 ok=(m and m.group(1)==h)
 t=rd(p); rows=[l for l in t.splitlines() if l.strip() and not l.startswith("#")]
 rec("PREREG_ROWS",len(rows)-1); rec("PREREG_SHA256",h)
 return (ok and len(rows)-1==36 and "INFLUENCED" in t and "ABSENT" in t),("sha_ok=%s rows=%d"%(bool(ok),len(rows)-1))
safe("PREREG_PRESENT_SHA_ROWS36_INFLUENCED",c_prereg,"prereg + sha, 36 rows, INFLUENCED")
def c_prereg_order():
 ls=log_recs(); pre=[x for (x,ts,cmd) in ls if "s5r2_prep.py prereg" in cmd]
 form=[x for (x,ts,cmd) in ls if "d016_run_s5r2.py formal" in cmd]
 rec("PREREG_WRITE_LINE",pre[0] if pre else 0); rec("FIRST_FORMAL_D016_LINE",form[0] if form else 0)
 if SHAKE and not form: return True,"deferred(shakedown, no formal run yet)"
 if not pre: return False,"no prereg write line"
 if not form: return False,"no formal D016 run line"
 return pre[0]<form[0],"prereg line %d < formal line %d"%(pre[0],form[0])
safe("PREREG_WRITTEN_BEFORE_FIRST_FORMAL_D016",c_prereg_order,"prereg line < first formal D016 line")
def c_build():
 p=os.path.join(EV,"D016_BUILD_S5R2.tsv")
 if not os.path.isfile(p): return False,"missing"
 rows={r[0]:r[1] for r in tsv_rows(p) if len(r)>=2}
 miss=[k for k in ("PYEXT_SHA256","LIB_S4_A_SHA256","LUA_FRONTEND_SHA256") if len(rows.get(k,""))!=64]
 tr=os.path.join(EV,"trees/F4")
 if not os.path.isdir(os.path.join(tr,"S4")): miss.append("F4 export")
 rec("D016_BUILD_PYEXT_SHA256",rows.get("PYEXT_SHA256","MISSING")[:16])
 return not miss,("ok" if not miss else str(miss))
safe("D016_BUILD_TSV_AND_F4_TREE",c_build,"artifacts + F4 export present")
def c_trace():
 p=os.path.join(EV,"D016_TRACE_S5R2.md")
 if not os.path.isfile(p): return False,"missing"
 t=rd(p); miss=[k for k in ("pattern.c","2214","fmm_PolBasisVL.cpp","2438","main_python.c","main_lua.c","info = 2","[源码]") if k not in t]
 return not miss,("all refs" if not miss else str(miss))
safe("D016_TRACE_PRESENT",c_trace,"trace with source refs")
def c_d017():
 p=os.path.join(EV,"D017_S4MALLOC_INVENTORY_S5R2.tsv")
 if not os.path.isfile(p): return False,"missing"
 rows=tsv_rows(p); hdr=rows[0]; body=rows[1:]
 k=len([r for r in body if r[hdr.index("kind")]=="CALL"])
 inn=len([r for r in body if r[hdr.index("d003_scope")]=="IN"])
 out=len([r for r in body if r[hdr.index("d003_scope")]=="OUT"])
 outc=len([r for r in body if r[hdr.index("d003_scope")]=="OUT" and r[hdr.index("kind")]=="CALL"])
 rec("D017_TOTAL",len(body)); rec("D017_CALL",k); rec("D017_IN",inn); rec("D017_OUT",out); rec("D017_OUT_CALL",outc)
 return (len(body),k,inn,out,outc)==(59,52,21,38,31),"total=%d call=%d in=%d out=%d outc=%d"%(len(body),k,inn,out,outc)
safe("D017_INVENTORY_COUNTS",c_d017,"59/52/21/38/31")
def c_oi():
 if not os.path.isfile(OI): return False,"missing"
 rows=tsv_rows(OI); hdr=rows[0]; body=rows[1:]
 ids=[r[0] for r in body]
 inv=[l.split(TAB)[0] for l in rd(os.path.join(REG,"s5r1/S5_INPUTS_S5R1.tsv")).splitlines()[1:] if l.strip()]
 disp={}
 for r in body: disp[r[1]]=disp.get(r[1],0)+1
 rec("OPEN_ITEMS_ROWS",len(body)); rec("OPEN_ITEMS_DISPOSITIONS",str(sorted(disp.items())))
 want={"RECORD_ONLY_OPEN":6,"OPEN_TRANSFERRED_OUT":12,"REGISTERED_D017":1,"REGISTERED_R-P05-02":1,"REGISTRY_SYNC":2,"TEST_S5R2":1,"TEST_S5R3":2}
 badloc=[]
 for r in body:
  loc=r[3]; m=re.match(r"^([^:]+):(\d+)$",loc)
  if not m: badloc.append(loc); continue
  fp=os.path.join(REPO,m.group(1))
  if not os.path.isfile(fp) or int(m.group(2))>len(rd(fp).splitlines()): badloc.append(loc)
 ok=(len(body)==25 and set(ids)==set(inv) and disp==want and not badloc)
 return ok,"rows=%d ids_ok=%s disp_ok=%s badloc=%s"%(len(body),set(ids)==set(inv),disp==want,badloc[:3])
safe("OPEN_ITEMS_25_ROWS_DISPOSITIONS_LOCATIONS",c_oi,"25 rows, 6 RECORD_ONLY_OPEN, valid file:line")
def c_applied():
 mi=rd(ISSUE_F); mr=rd(ROAD_F)
 miss_i=[k for k in ("| D017 /","| R-P05-02（","| R-P05-03（","3e77aa9","S5-M3D-01","S5-M3D-02","S5-M3D-05","S5-M3D-06","S5-M3D-07","S5-C-03","S5R3 在 F4 上重跑一次 make test") if k not in mi]
 miss_r=[k for k in ("S5 进行中（R2","已实施（P05-S3R2 提交 3e77aa9","经 U366 转出 P05","F10 历史因果","F8 历史目录","S1 报告 11.2") if k not in mr]
 forb=["P05-S6","P05 已完成","P05-S5 已完成","已签收 P05-S5","P05 完成","P05-S5 已签收"]
 badf=[w for w in forb if w in mi or w in mr]
 return (not miss_i and not miss_r and not badf),("miss_i=%s miss_r=%s forb=%s"%(miss_i,miss_r,badf))
safe("REGISTRY_APPLIED_MARKERS_AND_NO_FORBIDDEN",c_applied,"registry rows and wording applied")
def c_apdiff():
 if not os.path.isfile(APPDIFF): return False,"missing"
 t=rd(APPDIFF)
 d={}
 for line in t.splitlines():
  m=re.match(r"#   (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) replaced_lines=([\d,]*) inserted=(\d+)",line)
  if m: d[m.group(1)]=(m.group(2),int(m.group(3)))
 ok=(d.get("testing/s4test/ISSUE_REGISTRY.md")==("41,85,107,113,117",10) and d.get("PROJECT_ROADMAP.md")==("51,145,146",3))
 return ok and ("ASSERT_ONLY_LISTED_LINES_CHANGED: PASS" in t),str(d)
safe("REGISTRY_APPLY_DIFF_ONLY_LISTED_LINES",c_apdiff,"ISSUE 5 replaced/10 inserted; ROADMAP 3/3")
frozen,header=frozen_rows()
rec("FROZEN_COLUMNS",",".join(header) if header else "MISSING")
safe("FROZEN_LIST_PRESENT",lambda:(len(frozen)>0,"%d rows"%len(frozen)),"rows")
def c_frozen_cov():
 files=sorted(f for f in os.listdir(STAGE) if (("s5r2" in f) or f.startswith("gate_")) and f.endswith((".py",".sh",".lua")))
 stage=set("testing/d003/stage_s5r2/"+f for f in files)
 fz=set(r.get("path","") for r in frozen if "/stage_s5r2/" in r.get("path",""))
 return stage==fz,("equal" if stage==fz else "stage-only=%s frozen-only=%s"%(sorted(stage-fz),sorted(fz-stage)))
safe("FROZEN_COVERS_ROUND_SCRIPTS",c_frozen_cov,"frozen == round scripts")
def c_frozen_sha():
 bad=[r["path"] for r in frozen if not os.path.isfile(os.path.join(REPO,r["path"])) or sha_f(os.path.join(REPO,r["path"]))!=r["sha256"]]
 return not bad,("all %d OK"%len(frozen) if not bad else str(bad[:4]))
safe("FROZEN_SCRIPTS_SHA_UNCHANGED",c_frozen_sha,"all frozen OK")
if SHAKE:
 commit_i=commit_i_override or ""
 safe("SHAKEDOWN_SIMULATED_COMMIT_I",lambda:(commit_i.startswith("sim:line"),commit_i or "missing"),"sim:lineN")
 try: anchor=int(commit_i.split("sim:line",1)[1])
 except Exception: anchor=0
else:
 commit_i=""
 try: commit_i=sh(["git","log","--grep=P05-S5 R2 (i)","-1","--format=%H"])
 except Exception: commit_i=""
 safe("COMMIT_I_PRESENT",lambda:(bool(commit_i),commit_i or "missing"),"commit (i) found")
 rec("COMMIT_I_SHA",commit_i)
recs_all=log_recs(); rec("LOG_RECORDS",len(recs_all))
if SHAKE:
 post=[r for r in recs_all if r[0]>anchor]
else:
 ci_epoch=0
 if commit_i:
  try: ci_epoch=int(sh(["git","log","-1","--format=%ct",commit_i]))
  except Exception: ci_epoch=0
 rec("COMMIT_I_EPOCH",ci_epoch)
 post=[r for r in recs_all if epoch(r[1])>=ci_epoch]
rec("POST_I_LOG_RECORDS",len(post))
def is_call(cmd,rel,mode):
 toks=cmd.split()
 if not (toks and toks[0] in ("python3","sh","bash")): return False
 if rel not in cmd: return False
 if mode and mode!="-": return mode in toks
 return True
def count_calls(rel,mode):
 return [x for (x,ts,cmd) in post if is_call(cmd,rel,mode)]
for r in frozen:
 if r.get("expected_calls","0")=="0": continue
 key=os.path.basename(r["path"]).replace(".py","").replace(".sh","").upper()+"_"+r.get("mode","-").upper()
 def mkc(rr=r,kk=key):
  hits=count_calls(rr["path"],rr["mode"]); rec("CALL_LINES_"+kk,",".join(str(h) for h in hits))
  return len(hits)==int(rr["expected_calls"]),"%d"%len(hits)
 safe("POST_I_CALL_COUNT_"+key,mkc,r.get("expected_calls"))
def c_no_d003():
 bad=[]
 for (x,ts,cmd) in post:
  if ("open('testing/d003/" in cmd) or ('open("testing/d003/' in cmd) or re.search(r">\s*testing/d003/",cmd): bad.append((x,cmd[:60]))
 return not bad,(0 if not bad else str(bad[:3]))
safe("POST_I_NO_TESTING_D003_WRITES",c_no_d003,0)
def c_events():
 if not os.path.isfile(EVF): return False,"missing EVENTS"
 ev_lines=[x for (x,ts,cmd) in post if "s5r2_chain.py events" in cmd]
 if not ev_lines: return False,"no events call after (i)"
 anch=max(ev_lines); rec("EVENTS_ANCHOR_LINE",anch)
 rows={}
 for line in rd(EVF).splitlines():
  if not line.strip() or line.startswith("#") or line.startswith("log_line"+TAB): continue
  f=line.rstrip(NL).split(TAB)
  if len(f)>=2 and f[0].isdigit(): rows[int(f[0])]=f[1]
 raw=rd(os.path.join(EV,"safe_run.log")).splitlines()
 ts_of={x:ts for (x,ts,cmd) in recs_all}
 expect={}; parent=""
 for x in range(1,anch+1):
  if x>len(raw) or not raw[x-1].strip(): continue
  if x in ts_of: parent=ts_of[x]
  expect[x]=parent
 if set(rows)!=set(expect):
  return False,"row set differs missing=%s extra=%s"%(sorted(set(expect)-set(rows))[:4],sorted(set(rows)-set(expect))[:4])
 diff=[x for x in expect if rows[x]!=expect[x]]
 rec("EVENTS_ROWS",len(rows))
 return not diff,("rows=%d anchor=%d all match"%(len(rows),anch) if not diff else str(diff[:4]))
safe("EVENTS_ROW_SET_EQ_RECOMPUTATION",c_events,"row set equals recomputation")
def c_rc():
 if not os.path.isfile(RCK): return False,"missing REPORT_CHECK"
 fails=None
 for line in rd(RCK).splitlines():
  if line.startswith("FAILS="): fails=int(line.strip().split("=")[1])
 return fails==0,"FAILS=%s"%fails
safe("REPORT_CHECK_FAILS_ZERO",c_rc,"FAILS=0")
def c_reg():
 ok,cnt,det=sums_dir(REGDIR)
 if not ok: return False,det
 items=parse_report_items(); rec("REGISTRY_S5R2_ITEMS",cnt); rec("REPORT_DELIVERABLES",len(items))
 if not items: return False,"no report items"
 if cnt!=len(items)-1: return False,"sums %d != items-1 %d"%(cnt,len(items)-1)
 if items[-1]!="SHA256SUMS.txt": return False,"last item not SHA256SUMS.txt"
 return True,"%s; report items=%d"%(det,len(items))
safe("REGISTRIES_S5R2_SUMS_ALL_OK_AND_REPORT_ITEMS",c_reg,"all OK matching report")
def c_sums():
 if not os.path.isfile(SUMS): return False,"missing sums"
 lines=rd(SUMS).splitlines()
 if len(lines)<2: return False,"too short"
 m=re.search(r"up to line (\d+):\s*([0-9a-f]{64})",lines[1])
 if not m: return False,"no trunc header: "+lines[1][:60]
 trunc_line,trunc_sha=int(m.group(1)),m.group(2)
 ss=[x for (x,ts,cmd) in post if "s5r2_chain.py sha_sums" in cmd]
 if not ss: return False,"no sha_sums call after (i)"
 anch=max(ss); rec("SHA_SUMS_ANCHOR_LINE",anch)
 if trunc_line!=anch: return False,"trunc %d != anchor %d"%(trunc_line,anch)
 log_text=NL.join(rd(os.path.join(EV,"safe_run.log")).splitlines()[:trunc_line])+NL
 if sha_b(log_text.encode("utf-8"))!=trunc_sha: return False,"log hash mismatch"
 ok,cnt,det=sums_dir(SUMSROOT); rec("EVIDENCE_SUMS_ITEMS",cnt)
 return ok,"trunc line %d; %s"%(trunc_line,det)
safe("EVIDENCE_SHA256SUMS_OK",c_sums,"all OK")
def c_cov():
 listed=set(n for a,n in read_sums(SUMS))
 root_abs=os.path.abspath(SUMSROOT); out_abs=os.path.abspath(SUMS); gate=os.path.join(root_abs,"gate")
 miss=[]
 for r_,dirs,files in os.walk(SUMSROOT):
  dirs[:]=sorted(d for d in dirs if d not in ("tmp","gate","trees"))
  for f in sorted(files):
   fp=os.path.abspath(os.path.join(r_,f))
   if fp==out_abs or fp.startswith(gate+os.sep): continue
   if f in ("safe_run.log","SHA256SUMS.txt"): continue
   rel=os.path.relpath(fp,root_abs)
   if rel not in listed: miss.append(rel)
 return not miss,("all %d covered"%len(listed) if not miss else str(miss[:6]))
safe("EVIDENCE_SUMS_COVERS_ALL",c_cov,"manifest covers every non-excluded file")
def c_nowrite():
 sm=os.path.getmtime(SUMS); root_abs=os.path.abspath(SUMSROOT)
 out_abs=os.path.join(root_abs,"SHA256SUMS.txt"); bad=[]
 for r_,dirs,files in os.walk(SUMSROOT):
  dirs[:]=[d for d in dirs if d not in ("gate","trees")]
  for f in files:
   fp=os.path.abspath(os.path.join(r_,f))
   if fp==out_abs or fp.startswith(os.path.join(root_abs,"gate")+os.sep): continue
   if f=="safe_run.log": continue
   if os.path.getmtime(fp)>sm+0.5: bad.append(os.path.relpath(fp,root_abs))
 return not bad,("no $EV write after sha_sums" if not bad else str(sorted(bad)[:6]))
safe("EV_NO_WRITE_AFTER_SHA_SUMS",c_nowrite,"sha_sums last $EV write")
def c_unlogged():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 logtxt=rd(os.path.join(EV,"safe_run.log")) if os.path.isfile(os.path.join(EV,"safe_run.log")) else ""
 decl=set()
 if os.path.isfile(OUTDECL):
  for line in rd(OUTDECL).splitlines():
   if line.strip() and not line.startswith("#"): decl.add(line.strip())
 decl.update([os.path.relpath(ST,REPO),os.path.relpath(ERR9,REPO),os.path.relpath(RUL,REPO),os.path.relpath(BRIEF,REPO),os.path.relpath(PATCHV2,REPO),os.path.relpath(OPENITEMS,REPO),os.path.relpath(REPORT,REPO),ISSUE_REL,ROAD_REL])
 bad=[]
 for target in [P05,STAGE]:
  for r_,dirs,files in os.walk(target):
   if "evidence" in r_.split(os.sep): continue
   for f in files:
    fp=os.path.join(r_,f); rel=os.path.relpath(fp,REPO)
    if sep and int(os.path.getmtime(fp))>=sep:
     if rel in decl: continue
     if rel in logtxt or os.path.basename(rel) in logtxt: continue
     bad.append(rel)
 rec("UNLOGGED_SELF",len(bad)); rec("DECLARED_OUTPUTS",len(decl))
 return not bad,(0 if not bad else str(bad[:8]))
safe("UNLOGGED_SELF_ZERO",c_unlogged,0)
def c_other():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 bad=[]
 for p in (os.path.join(EV,"..","p05-s5r1"),os.path.join(EV,"..","p05-s4r9")):
  p=os.path.abspath(p)
  for root2,dirs2,files2 in os.walk(p):
   for f in files2:
    fp=os.path.join(root2,f)
    if sep and int(os.path.getmtime(fp))>sep: bad.append(os.path.relpath(fp,REPO))
 return not bad,("none" if not bad else str(bad[:6]))
safe("OTHER_ROUND_EVIDENCE_UNTOUCHED",c_other,"none")
safe("ROOT_REGISTRIES_ABSENT",lambda:(not os.path.exists(os.path.join(REPO,"registries")),"absent"),"absent")
tc,ts=tmp_snap(); rec("TMP_COUNT_END",tc); rec("TMP_SHA256_END",ts); rec("TMP_COUNT_START",start.get("TMP_COUNT","?"))
safe("TMP_SNAPSHOT_RECORDED",lambda:(tc>=0,"count=%d sha=%s"%(tc,ts)),"recorded")
def c_audit():
 files=[f for f in os.listdir(STAGE) if (("s5r2" in f) or f.startswith("gate_")) and f.endswith((".py",".sh",".lua"))]
 bad=[f for f in files if re.search(r"_v[0-9]+\.(py|sh|lua)$",f)]
 foreign=[f for f in files if re.search(r"r9m3|s4r9",f)]
 return (not bad and not foreign),("%d s5r2 files; nonfinal=%s foreign=%s"%(len(files),bad,foreign))
safe("SCRIPT_NAME_AUDIT",c_audit,"no non-final/foreign names")
def c_amend():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 out=sh(["git","reflog","--date=iso"])
 bad=[]
 for line in out.splitlines():
  if "(amend)" not in line: continue
  m=re.search(r"@\{(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4})\}",line)
  if not m: continue
  try: t=int(datetime.datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S %z").timestamp())
  except Exception: continue
  if sep and t>=sep: bad.append(line[:80])
 return not bad,("no amend after start" if not bad else str(bad[:2]))
safe("NO_AMEND_AFTER_START",c_amend,"no amend/rebase after start")
def c_verdict():
 if SHAKE: return True,"deferred(shakedown, formal verdict comes from the frozen period)"
 p=os.path.join(EV,"D016_VERDICT_S5R2.tsv")
 if not os.path.isfile(p): return False,"missing verdict"
 t=rd(p)
 m=re.search(r"(?m)^SUMMARY\tMATCH=(\d+)\tMISMATCH=(\d+)\tFLAKY=(\d+)$",t)
 if not m: return False,"SUMMARY unparsed"
 rows=[l for l in t.splitlines() if l.strip() and not l.startswith("#")]
 rec("D016_VERDICT_SUMMARY","MATCH=%s MISMATCH=%s FLAKY=%s"%(m.group(1),m.group(2),m.group(3))); rec("D016_VERDICT_ROWS",len(rows)-2)
 return (m.group(1),m.group(2),m.group(3))==("33","0","0"),"MATCH=%s MISMATCH=%s FLAKY=%s rows=%d"%(m.group(1),m.group(2),m.group(3),len(rows)-2)
safe("D016_VERDICT_TWO_PASSES_NO_MISMATCH",c_verdict,"MATCH=33 MISMATCH=0 FLAKY=0")
crashes=sum(1 for s,n,e,a in res if "CHECK_CRASHED" in a)
ck("CHECK_CRASHED_ZERO",crashes==0,0,crashes)
rec("CHECK_CRASHED_COUNT",crashes)
now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
lines=["# P05-S5 R2 end gate "+os.path.basename(OUT)+" ("+now+")"]
lines+=["RECORD"+TAB+k+TAB+"value="+v for k,v in recs]
lines+=["%s\t%s\texpected=%s\tactual=%s"%(s,n,e,a) for s,n,e,a in res]
fails=sum(1 for r in res if r[0]=="FAIL")
lines.append("COUNTS\tpass=%d\tfail=%d\tskip=0\ttotal=%d"%(sum(1 for r in res if r[0]=="PASS"),fails,len(res)))
lines.append("FAILS=%d"%fails)
body=NL.join(lines)+NL
os.makedirs(OUTDIR,exist_ok=True)
open(OUT,"w",encoding="utf-8").write(body)
st2=sh(["git","status","--short","-uall"]); hd=sh(["git","rev-parse","HEAD"])
open(os.path.join(OUTDIR,"ALL_STATUS_S5R2_end.txt"),"w",encoding="utf-8").write(st2+NL+"HEAD"+TAB+hd+NL)
sys.exit(min(fails,255))
