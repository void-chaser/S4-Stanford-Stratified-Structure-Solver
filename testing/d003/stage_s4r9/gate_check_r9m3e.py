#!/usr/bin/env python3
# gate_check_r9m3e.py -- P05-S4 R9 M3e end gate. Output lives in $EV/gate/ and is excluded from SHA256SUMS.
# Frozen-derived POST_I counts and script names are read from FROZEN_SCRIPTS_R9M3E.tsv (E9-59 discipline).
import os,sys,re,hashlib,subprocess,datetime
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9/m3e")
GATE=os.path.join(EV,"gate")
REG=os.path.join(REPO,"checkpoints/p05/registries")
RUL=os.path.join(REG,"RULINGS.tsv"); ERR=os.path.join(REG,"s4r9/ERRATA_9.txt"); ST=os.path.join(REPO,"checkpoints/p05/STATE.md")
REPORT=os.path.join(REPO,"checkpoints/p05/P05_S4R9_M3e_REPORT.md"); SIGNOFF=os.path.join(REPO,"checkpoints/p05/P05_S3_S4_SIGNOFF.md")
BRIEF=os.path.join(REPO,"checkpoints/p05/briefs/P05_S4R9_BRIEF_M3e.md")
REGDIR=os.path.join(REG,"s4r9/M3e"); STAGE=os.path.join(REPO,"testing/d003/stage_s4r9")
BASE="37fbc0f2b9c48010b81ad220293fe6f3af5c02bd"
TAB=chr(9); NL=chr(10)
TS=re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
OUT=sys.argv[1]; commit_i_override=None
i=2
while i<len(sys.argv):
 if sys.argv[i]=="--commit-i" and i+1<len(sys.argv): commit_i_override=sys.argv[i+1]; i+=2
 else: i+=1
res=[]; recs=[]
def ck(n,ok,exp,act):
 res.append(("PASS" if ok else "FAIL",n,str(exp),str(act)))
def rec(n,v): recs.append((n,str(v)))
def safe(n,fn,exp):
 try:
  ok,act=fn(); ck(n,ok,exp,act)
 except Exception as e: ck(n,False,exp,"CHECK_CRASHED: %s: %s"%(type(e).__name__,e))
def sh(a): return subprocess.check_output(a,cwd=REPO,text=True,stderr=subprocess.STDOUT).strip()
def shb(a): return subprocess.check_output(a,cwd=REPO,stderr=subprocess.DEVNULL)
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def read_sums(p):
 out=[]
 for line in open(p,encoding="utf-8"):
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
def tmp_snap():
 root=os.sep+"tmp"; e=sorted(os.listdir(root)) if os.path.isdir(root) else []
 return len(e),sha_b(("\n".join(e)+("\n" if e else "")).encode("utf-8"))
def start_records():
 p=os.path.join(EV,"GATE_R9M3E_start.txt"); recs={}
 if not os.path.isfile(p): return recs
 for line in open(p,encoding="utf-8"):
  f=line.rstrip(NL).split(TAB)
  if len(f)>=3 and f[0]=="RECORD":
   v=f[2]
   if v.startswith("value="): v=v[6:]
   recs[f[1]]=v
 return recs
def log_recs():
 p=os.path.join(EV,"safe_run.log"); out=[]
 if not os.path.isfile(p): return out
 for idx,line in enumerate(open(p,encoding="utf-8",errors="replace"),1):
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
 p=os.path.join(EV,"FROZEN_SCRIPTS_R9M3E.tsv"); rows=[]
 if not os.path.isfile(p): return rows
 for line in open(p,encoding="utf-8"):
  line=line.rstrip(NL)
  if not line.strip() or line.startswith("#") or line.startswith("path"+TAB): continue
  f=line.split(TAB)
  if len(f)>=2: rows.append({"path":f[0],"sha256":f[1],"expect":(f[2] if len(f)>2 else "1"),"mode":(f[3] if len(f)>3 else "-")})
 return rows
def brief_block():
 if not os.path.isfile(BRIEF): return None
 lines=open(BRIEF,encoding="utf-8").read().splitlines()
 try:
  i=lines.index("----BEGIN SIGNOFF----"); j=lines.index("----END SIGNOFF----")
 except ValueError: return None
 blk=lines[i+1:j]
 while blk and not blk[0].strip(): blk.pop(0)
 while blk and not blk[-1].strip(): blk.pop()
 return NL.join(blk)
def signoff_block():
 if not os.path.isfile(SIGNOFF): return None
 lines=open(SIGNOFF,encoding="utf-8").read().splitlines()
 try:
  i=next(k for k,l in enumerate(lines) if l.strip().startswith("## 2."))
  j=next(k for k in range(i+1,len(lines)) if lines[k].startswith("## "))
 except StopIteration:
  return None
 blk=lines[i+1:j]
 while blk and not blk[0].strip(): blk.pop(0)
 while blk and not blk[-1].strip(): blk.pop()
 return NL.join(blk)
def parse_report_items():
 if not os.path.isfile(REPORT): return []
 insec=False; items=[]
 for line in open(REPORT,encoding="utf-8"):
  if line.strip().startswith("## 7"): insec=True; continue
  if insec and line.startswith("## "): break
  if insec:
   m=re.match(r"^\s*(\d+)\.\s+(.+?)\s*$",line)
   if m: items.append(m.group(2).strip())
 return items
def c_branch():
 b=sh(["git","branch","--show-current"]); return b=="codex/p05-d003-fft-error-propagation",b
safe("BRANCH_IS_EXPECTED",c_branch,"codex/p05-d003-fft-error-propagation")
start=start_records()
safe("START_RECORDS_PRESENT",lambda:(len(start)>0,"%d records"%len(start) if start else "missing"),"records present")
def c_s4():
 t=sh(["git","rev-parse","HEAD:S4"]); return t=="589e15eb11fcb04e031b524f25a443e7921946cf",t
safe("HEAD_S4_TREE_EQ_F4",c_s4,"589e15eb11fcb04e031b524f25a443e7921946cf")
def c_judge():
 a=sha_f(os.path.join(REPO,"testing/d003/judge_d003.py")); return a=="d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb",a
safe("JUDGE_SHA256",c_judge,"d2d04145...09eb")
def c_s4_zero():
 d=sh(["git","diff","HEAD","--","S4"]); return d=="",("S4 unmodified" if not d else d[:120])
safe("S4_DIR_ZERO_MODIFICATION",c_s4_zero,"S4 unmodified")
ALLOW_M={"checkpoints/p05/STATE.md","checkpoints/p05/registries/RULINGS.tsv","checkpoints/p05/registries/s4r9/ERRATA_9.txt","checkpoints/p05/P05_S4R9_M3e_REPORT.md"}
def c_base_status():
 lines=[l for l in sh(["git","diff","--name-status",BASE]).splitlines() if l.strip()]
 mods=[l.split(TAB)[1] for l in lines if l.startswith("M"+TAB)]
 dels=[l.split(TAB)[1] for l in lines if l.startswith("D"+TAB)]
 add=sum(1 for l in lines if l.startswith("A"+TAB))
 badm=[x for x in mods if x not in ALLOW_M]
 rec("BASE_DIFF_A",add); rec("BASE_DIFF_M",len(mods)); rec("BASE_DIFF_D",len(dels))
 return (not badm) and (not dels),("A=%d M=%d D=%d badM=%s badD=%s"%(add,len(mods),len(dels),badm[:4],dels[:4]))
safe("BASE_COMMITTED_ONLY_ALLOWED_MD",c_base_status,"only allowed M/D; new A allowed")
def c_tracked():
 d=[x for x in sh(["git","diff","--name-only","HEAD"]).splitlines() if x.strip()]
 bad=[x for x in d if x not in ALLOW_M]
 return not bad,("none" if not bad else str(bad[:6]))
safe("TRACKED_MODIFIED_WITHIN_END_ALLOW_LIST",c_tracked,"none")
rb=open(RUL,"rb").read(); eb=open(ERR,"rb").read()
rs=start.get("RULINGS_SHA256",""); rbn=int(start.get("RULINGS_BYTES","0") or 0)
es=start.get("ERRATA_9_SHA256",""); ebn=int(start.get("ERRATA_9_BYTES","0") or 0)
safe("RULINGS_PREFIX_OF_START_UNCHANGED",lambda:(sha_b(rb[:rbn])==rs,sha_b(rb[:rbn])),rs)
safe("RULINGS_NOT_TRUNCATED",lambda:(len(rb)>=rbn,len(rb)),">= %d"%rbn)
safe("ERRATA_PREFIX_OF_START_UNCHANGED",lambda:(sha_b(eb[:ebn])==es,sha_b(eb[:ebn])),es)
safe("ERRATA_NOT_TRUNCATED",lambda:(len(eb)>=ebn,len(eb)),">= %d"%ebn)
def c_rul_end():
 lines=[l for l in rb.decode("utf-8","replace").splitlines() if l.strip() and not l.strip().startswith("#")]
 ids={}
 for l in lines:
  f=l.split(TAB)
  if len(f)!=5: return False,"bad fields: "+l[:40]
  if f[0] in ids: return False,"dup "+f[0]
  ids[f[0]]=f
 ns=[int(k[1:]) for k in ids if re.match(r"^U\d+$",k)]
 rec("RULINGS_MAX_U_END","U%d"%max(ns)); rec("RULINGS_BYTES_END",len(rb))
 miss=[u for u in ("U359","U360","U361","U362","U363") if u not in ids]
 u359=ids.get("U359",["","","","",""])[2]
 ok=(max(ns)==363) and (not miss) and ("同意签收 P05-S3、P05-S4" in u359)
 return ok,"maxU=%d missing=%s"%(max(ns),miss)
safe("RULINGS_END_MAX_U363_AND_U359_363",c_rul_end,"U363 with U359..U363 present")
def c_err_end():
 ids=re.findall(r"^(E9-\d+)",eb.decode("utf-8","replace"),re.M)
 rec("ERRATA_9_COUNT_END",len(ids)); rec("ERRATA_9_BYTES_END",len(eb))
 need=["E9-%d"%x for x in range(74,78)]
 return (ids and ids[-1]=="E9-77" and len(ids)==77 and all(x in ids for x in need)),("%s count=%d"%(ids[-1] if ids else "none",len(ids)))
safe("ERRATA_END_LAST_E9_77_COUNT_77",c_err_end,"E9-77 count=77")
def c_rul_append():
 b0=shb(["git","show",BASE+":checkpoints/p05/registries/RULINGS.tsv"])
 return rb.startswith(b0) and len(rb)>len(b0),"prefix=%s delta=%d"%(rb.startswith(b0),len(rb)-len(b0))
safe("RULINGS_BASE_PREFIX_PLUS_APPEND_ONLY",c_rul_append,"BASE content is prefix and file grew")
def c_err_append():
 b0=shb(["git","show",BASE+":checkpoints/p05/registries/s4r9/ERRATA_9.txt"])
 return eb.startswith(b0) and len(eb)>len(b0),"prefix=%s delta=%d"%(eb.startswith(b0),len(eb)-len(b0))
safe("ERRATA_BASE_PREFIX_PLUS_APPEND_ONLY",c_err_append,"BASE content is prefix and file grew")
sb=open(ST,"rb").read()
safe("STATE_BYTES_LE_8192",lambda:(0<len(sb)<=8192,len(sb)),"<= 8192")
def c_state():
 t=sb.decode("utf-8","replace")
 keys=["r9m3e","S1、S2、S3、S4 已由用户确认","S5 未开始","P05_S3_S4_SIGNOFF.md","S5_HANDOFF_R9M3D.tsv","E9-76"]
 miss=[k for k in keys if k not in t]
 return not miss,("all markers" if not miss else str(miss))
safe("STATE_MARKERS_SIGNOFF_AND_S5",c_state,"state markers present")
bt=brief_block(); sbt=signoff_block()
safe("SIGNOFF_SEC2_VERBATIM_VS_BRIEF",lambda:(bt is not None and sbt is not None and bt==sbt,"equal" if bt==sbt else "DIFF"),"verbatim equal")
def c_signoff_rows():
 t=open(SIGNOFF,encoding="utf-8").read() if os.path.isfile(SIGNOFF) else ""
 keys=["| P05-S3 | 已由用户签收 |","| P05-S4 | 已由用户签收 |","2026-10-18","| P05-S5 | 未开始 |","执行者未自行宣布任何阶段完成","S5-M3D-06","E9-76"]
 miss=[k for k in keys if k not in t]
 return not miss,("all rows" if not miss else str(miss))
safe("SIGNOFF_FILE_ROWS_AND_DECLARATION",c_signoff_rows,"rows and declaration present")
frozen=frozen_rows()
safe("FROZEN_LIST_PRESENT",lambda:(len(frozen)>0,"%d rows"%len(frozen)),"rows")
def c_frozen_cov():
 stage=set("testing/d003/stage_s4r9/"+f for f in os.listdir(STAGE) if ("r9m3e" in f) and (f.endswith(".py") or f.endswith(".sh")))
 fz=set(r["path"] for r in frozen if "/stage_s4r9/" in r["path"])
 return stage==fz,("equal" if stage==fz else "stage-frozen=%s frozen-stage=%s"%(sorted(stage-fz),sorted(fz-stage)))
safe("FROZEN_COVERS_ROUND_SCRIPTS",c_frozen_cov,"frozen == round scripts")
def c_frozen_sha():
 bad=[]
 for r in frozen:
  fp=os.path.join(REPO,r["path"])
  if not os.path.isfile(fp) or sha_f(fp)!=r["sha256"]: bad.append(r["path"])
 return not bad,("all %d OK"%len(frozen) if not bad else str(bad[:4]))
safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END",c_frozen_sha,"all frozen OK")
commit_i=commit_i_override or sh(["git","log","--grep=R9 M3e (i)","-1","--format=%H"] or ["true"]) if False else (commit_i_override or "")
if not commit_i:
 try: commit_i=sh(["git","log","--grep=R9 M3e (i)","-1","--format=%H"])
 except Exception: commit_i=""
safe("COMMIT_I_PRESENT",lambda:(bool(commit_i),commit_i or "missing"),"commit (i) found")
rec("COMMIT_I_SHA",commit_i)
recs_all=log_recs(); rec("LOG_RECORDS",len(recs_all))
ci_epoch=0
if commit_i:
 try: ci_epoch=int(sh(["git","log","-1","--format=%ct",commit_i]))
 except Exception: ci_epoch=0
rec("COMMIT_I_EPOCH",ci_epoch)
post=[(x,ts,cmd) for (x,ts,cmd) in recs_all if epoch(ts)>=ci_epoch]
rec("POST_I_LOG_RECORDS",len(post))
def is_call(cmd,rel,mode):
 toks=cmd.split()
 if not (toks and toks[0] in ("python3","sh","bash")): return False
 if rel not in toks: return False
 if mode and mode!="-": return mode in toks
 return True
def count_calls(rel,mode):
 return [x for (x,ts,cmd) in post if is_call(cmd,rel,mode)]
for r in frozen:
 if r["expect"]=="0": continue
 key=os.path.basename(r["path"]).replace(".py","").replace(".sh","").upper()+"_"+r["mode"].upper()
 def mkc(r=r,key=key):
  hits=count_calls(r["path"],r["mode"]); rec("CALL_LINES_"+key,",".join(str(h) for h in hits))
  exp=int(r["expect"]); return len(hits)==exp,"%d"%len(hits)
 safe("POST_I_CALL_COUNT_"+key,mkc(),r["expect"])
def c_no_d003():
 bad=[]
 for (x,ts,cmd) in post:
  if ("open('testing/d003/" in cmd) or ('open("testing/d003/' in cmd) or re.search(r">\s*testing/d003/",cmd): bad.append((x,cmd[:60]))
 return not bad,(0 if not bad else str(bad[:3]))
safe("POST_I_NO_TESTING_D003_WRITES",c_no_d003,0)
def c_events():
 ev=os.path.join(EV,"EVENTS_R9M3E.tsv")
 if not os.path.isfile(ev): return False,"missing EVENTS"
 hits=count_calls("testing/d003/stage_s4r9/m3e_chain_r9m3e.py","-")
 # anchor is the events subcommand line (last call before progress); find max line whose cmd ends with events
 ev_lines=[x for (x,ts,cmd) in post if "m3e_chain_r9m3e.py events" in cmd]
 if not ev_lines: return False,"no events call after (i)"
 anchor=max(ev_lines); rec("EVENTS_ANCHOR_LINE",anchor)
 rows={}
 for line in open(ev,encoding="utf-8"):
  if not line.strip() or line.startswith("#") or line.startswith("log_line"+TAB): continue
  f=line.rstrip(NL).split(TAB)
  if len(f)>=2 and f[0].isdigit(): rows[int(f[0])]=f[1]
 ts_of={x:ts for (x,ts,cmd) in recs_all}
 expect={}; parent=""
 raw=[l for l in open(os.path.join(EV,"safe_run.log"),encoding="utf-8",errors="replace").read().splitlines()]
 for x in range(1,anchor+1):
  if x>len(raw) or not raw[x-1].strip(): continue
  if x in ts_of: parent=ts_of[x]
  expect[x]=parent
 if set(rows)!=set(expect):
  return False,"row set differs missing=%s extra=%s"%(sorted(set(expect)-set(rows))[:4],sorted(set(rows)-set(expect))[:4])
 diff=[x for x in expect if rows[x]!=expect[x]]
 rec("EVENTS_ROWS",len(rows))
 return not diff,("rows=%d anchor=%d all match"%(len(rows),anchor) if not diff else str(diff[:4]))
safe("EVENTS_ROW_SET_EQ_RECOMPUTATION",c_events,"row set equals recomputation")
def c_rc():
 p=os.path.join(EV,"REPORT_CHECK_R9M3E.txt")
 if not os.path.isfile(p): return False,"missing REPORT_CHECK"
 fails=None
 for line in open(p,encoding="utf-8"):
  if line.startswith("FAILS="): fails=int(line.strip().split("=")[1])
 return fails==0,"FAILS=%s"%fails
safe("REPORT_CHECK_FAILS_ZERO",c_rc,"FAILS=0")
def c_reg():
 ok,cnt,det=sums_dir(REGDIR)
 if not ok: return False,det
 items=parse_report_items(); rec("REGISTRY_M3E_ITEMS",cnt); rec("REPORT_DELIVERABLES",len(items))
 if not items: return False,"no report items"
 if cnt!=len(items)-1: return False,"sums %d != items-1 %d"%(cnt,len(items)-1)
 if items[-1]!="SHA256SUMS.txt": return False,"last item not SHA256SUMS.txt"
 return True,"%s; report items=%d"%(det,len(items))
safe("REGISTRIES_M3E_SUMS_ALL_OK_AND_REPORT_ITEMS",c_reg,"all OK matching report")
def c_sums():
 sp=os.path.join(EV,"SHA256SUMS.txt")
 if not os.path.isfile(sp): return False,"missing sums"
 lines=open(sp,encoding="utf-8").read().splitlines()
 if len(lines)<2: return False,"too short"
 m=re.search(r"up to line (\d+):\s*([0-9a-f]{64})",lines[1])
 if not m: return False,"no trunc header: "+lines[1][:60]
 trunc_line,trunc_sha=int(m.group(1)),m.group(2)
 ss=[x for (x,ts,cmd) in post if "m3e_chain_r9m3e.py sha_sums" in cmd]
 if not ss: return False,"no sha_sums call after (i)"
 anchor=max(ss); rec("SHA_SUMS_ANCHOR_LINE",anchor)
 if trunc_line!=anchor: return False,"trunc %d != anchor %d"%(trunc_line,anchor)
 log_text=NL.join(open(os.path.join(EV,"safe_run.log"),encoding="utf-8",errors="replace").read().splitlines()[:trunc_line])+NL
 if sha_b(log_text.encode("utf-8"))!=trunc_sha: return False,"log hash mismatch"
 ok,cnt,det=sums_dir(EV); rec("EVIDENCE_SUMS_ITEMS",cnt)
 return ok,"trunc line %d; %s"%(trunc_line,det)
safe("EVIDENCE_SHA256SUMS_OK",c_sums,"all OK")
def c_cov():
 sp=os.path.join(EV,"SHA256SUMS.txt")
 listed=set(n for a,n in read_sums(sp))
 ev_abs=os.path.abspath(EV); out_abs=os.path.abspath(sp); gate=os.path.join(ev_abs,"gate")
 miss=[]
 for root,dirs,files in os.walk(EV):
  dirs[:]=sorted(d for d in dirs if d!="tmp")
  for f in sorted(files):
   fp=os.path.abspath(os.path.join(root,f))
   if fp==out_abs or fp.startswith(gate+os.sep): continue
   if f in ("safe_run.log","SHA256SUMS.txt"): continue
   rel=os.path.relpath(fp,ev_abs)
   if rel not in listed: miss.append(rel)
 return not miss,("all %d covered"%len(listed) if not miss else str(miss[:6]))
safe("EVIDENCE_SUMS_COVERS_ALL",c_cov,"manifest covers every non-gate file")
def c_nowrite():
 sm=os.path.getmtime(os.path.join(EV,"SHA256SUMS.txt")); ev_abs=os.path.abspath(EV); gate=os.path.join(ev_abs,"gate"); tmpd=os.path.join(ev_abs,"tmp")
 out_abs=os.path.join(ev_abs,"SHA256SUMS.txt"); bad=[]
 for root,dirs,files in os.walk(EV):
  for f in files:
   fp=os.path.abspath(os.path.join(root,f))
   if fp==out_abs or fp.startswith(gate+os.sep) or fp.startswith(tmpd+os.sep): continue
   if f=="safe_run.log": continue
   if os.path.getmtime(fp)>sm+0.5: bad.append(os.path.relpath(fp,ev_abs))
 return not bad,("no $EV write after sha_sums" if not bad else str(sorted(bad)[:6]))
safe("EV_NO_WRITE_AFTER_SHA_SUMS",c_nowrite,"sha_sums last $EV write")
def c_unlogged():
 sep=epoch(start.get("START_TIME_UTC","")) if start.get("START_TIME_UTC") else 0
 logtxt=open(os.path.join(EV,"safe_run.log"),encoding="utf-8",errors="replace").read() if os.path.isfile(os.path.join(EV,"safe_run.log")) else ""
 decl=set()
 mp=os.path.join(EV,"REGISTRY_OUTPUTS_R9M3E.tsv")
 if os.path.isfile(mp):
  for line in open(mp,encoding="utf-8"):
   if line.strip() and not line.startswith("#"): decl.add(line.strip())
 decl.update([os.path.relpath(SIGNOFF,REPO),os.path.relpath(REPORT,REPO),"checkpoints/p05/registries/RULINGS.tsv","checkpoints/p05/registries/s4r9/ERRATA_9.txt","checkpoints/p05/STATE.md"])
 bad=[]
 targets=[os.path.join(REPO,"checkpoints","p05"),STAGE]
 for target in targets:
  for root,dirs,files in os.walk(target):
   if "evidence" in root.split(os.sep): continue
   for f in files:
    fp=os.path.join(root,f); rel=os.path.relpath(fp,REPO)
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
 for r in ("m0","m1","m1r2","m1r3","m1r4","m2","m2b","m2c","m3a","m3b","m3c","m3d"):
  p=os.path.join(REPO,"checkpoints/p05/evidence/p05-s4r9",r)
  if not os.path.isdir(p): continue
  for root,dirs,files in os.walk(p):
   for f in files:
    fp=os.path.join(root,f)
    if sep and int(os.path.getmtime(fp))>sep: bad.append(os.path.relpath(fp,REPO))
 return not bad,("none" if not bad else str(bad[:6]))
safe("OTHER_ROUND_EVIDENCE_UNTOUCHED",c_other,"none")
def c_rootreg():
 e=os.path.exists(os.path.join(REPO,"registries")); return not e,("absent" if not e else "EXISTS")
safe("ROOT_REGISTRIES_ABSENT",c_rootreg,"absent")
tc,ts=tmp_snap(); rec("TMP_COUNT_END",tc); rec("TMP_SHA256_END",ts); rec("TMP_COUNT_START",start.get("TMP_COUNT","?"))
safe("TMP_SNAPSHOT_RECORDED",lambda:(tc>=0,"count=%d sha=%s"%(tc,ts)),"recorded")
def c_audit():
 files=[f for f in os.listdir(STAGE) if ("r9m3e" in f) and (f.endswith(".py") or f.endswith(".sh"))]
 bad=[f for f in files if re.search(r"_v[0-9]+\\.(py|sh)$",f)]
 foreign=[f for f in files if re.search(r"r9m3[abc]",f)]
 return (not bad and not foreign),("%d r9m3e files; nonfinal=%s foreign=%s"%(len(files),bad,foreign))
safe("SCRIPT_NAME_AUDIT",c_audit,"no non-final/foreign r9m3e names")
now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
lines=["# P05-S4 R9 M3e end gate "+os.path.basename(OUT)+" ("+now+")"]
lines+=["RECORD"+TAB+k+TAB+"value="+v for k,v in recs]
lines+=["%s\t%s\texpected=%s\tactual=%s"%(s,n,e,a) for s,n,e,a in res]
fails=sum(1 for r in res if r[0]=="FAIL")
lines.append("COUNTS\tpass=%d\tfail=%d\tskip=0\ttotal=%d"%(sum(1 for r in res if r[0]=="PASS"),fails,len(res)))
lines.append("FAILS=%d"%fails)
body=NL.join(lines)+NL
os.makedirs(GATE,exist_ok=True)
open(OUT,"w",encoding="utf-8").write(body)
open(os.path.join(GATE,"ALL_STATUS_R9M3E_end.txt"),"w",encoding="utf-8").write(sh(["git","status","--short","-uall"])+NL+"HEAD"+TAB+sh(["git","rev-parse","HEAD"])+NL)
print(body)
sys.exit(min(fails,255))
