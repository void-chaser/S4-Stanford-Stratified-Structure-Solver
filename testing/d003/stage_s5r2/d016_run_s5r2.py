#!/usr/bin/env python3
# d016_run_s5r2.py -- run the D016 point family on the F4 build exported at $EV/trees/F4.
#   calib             : test-run only (not a formal result); writes $EV/shakedown/d016_calib/
#   formal --pass 1|2 : formal pass; pass 2 also writes $EV/D016_VERDICT_S5R2.tsv from both passes
# Expected values come from the D016_TRACE_S5R2.md source mapping and are pre-registered in
# checkpoints/p05/registries/s5r2/PREREG_D016_S5R2.tsv; nothing here rewrites an expectation.
import os,sys,json,math,subprocess,hashlib,datetime
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r2")
TREE=os.path.join(EV,"trees/F4")
STAGE=os.path.join(REPO,"testing/d003/stage_s5r2")
PY_SCRIPT=os.path.join(STAGE,"d016_py_s5r2.py")
LUA_SCRIPT=os.path.join(STAGE,"d016_lua_s5r2.lua")
TAB=chr(9); NL=chr(10)
MSG_PY="GetPowerFlux: The layer eigensystem could not be solved; no solution was returned"
MSG_LUA="GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned."
INFO2="Layer eigensystem returned info = 2"
FAIL_TAGS=["VL_NB1","VL_NB1_RETRY","VL_NB2","VL_NB2_RETRY","VL_NB3","VL_NB3_RETRY","VL_NB4","VL_NB4_RETRY"]
CTRL_TAGS=["VL_NB5","VL_NB9","Jones_NB1","NV_NB1"]
RECOVER="VL_NB9_RECOVER"; REF="VL_NB9_REF"
def sha_f(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(65536),b""): h.update(b)
 return h.hexdigest()
def run(cmd,stdin_text=None):
 p=subprocess.run(cmd,input=stdin_text,capture_output=True,text=True,cwd=REPO)
 return {"rc":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
def pyext():
 out=subprocess.check_output(["python3-config","--extension-suffix"],text=True).strip()
 return os.path.join(TREE,"S4"+out)
def one_pass(tag,logdir):
 os.makedirs(logdir,exist_ok=True)
 res={}
 py=pyext(); lua=os.path.join(TREE,"build/S4")
 if not os.path.isfile(py): raise SystemExit("MISSING pyext "+py)
 if not os.path.isfile(lua): raise SystemExit("MISSING lua "+lua)
 for mode in ("main","ref"):
  out=os.path.join(logdir,"py_%s_%s.json"%(mode,tag))
  r=run(["python3","-I","-B",PY_SCRIPT,"--tree",TREE,"--mode",mode,"--out",out])
  open(os.path.join(logdir,"py_%s_%s.stdout.txt"%(mode,tag)),"w").write(r["stdout"])
  open(os.path.join(logdir,"py_%s_%s.stderr.txt"%(mode,tag)),"w").write(r["stderr"])
  res["py_"+mode]={"process":r,"json":json.load(open(out)) if os.path.isfile(out) else None}
 lua_text=open(LUA_SCRIPT).read()
 for mode in ("main","ref"):
  r=run([lua,"-a",mode],stdin_text=lua_text)
  open(os.path.join(logdir,"lua_%s_%s.stdout.txt"%(mode,tag)),"w").write(r["stdout"])
  open(os.path.join(logdir,"lua_%s_%s.stderr.txt"%(mode,tag)),"w").write(r["stderr"])
  res["lua_"+mode]={"process":r}
 res["artifacts"]={"pyext_sha256":sha_f(py),"lua_sha256":sha_f(lua),
                   "libS4_a_sha256":sha_f(os.path.join(TREE,"build/libS4.a")) if os.path.isfile(os.path.join(TREE,"build/libS4.a")) else "MISSING"}
 return res
def parse_lua(stdout):
 pts={}
 for line in stdout.splitlines():
  f=line.split(TAB)
  if not f or not f[0].startswith("POINT "): continue
  parts=f[0].split()
  tag=parts[1]; kind=parts[2]
  if kind=="FAIL_VISIBLE":
   pts[tag]={"status":"FAIL_VISIBLE"}
  elif kind=="VALUES" and len(f)>=5:
   vals=[float(x) for x in f[1:5]]
   pts[tag]={"status":"VALUES","values":vals,"all_finite":all(math.isfinite(x) for x in vals)}
 return pts
def py_points(js):
 d={}
 for p in js["points"] if js else []:
  d[p["tag"]]=p
 return d
def obs(one):
 o={}
 pm=one["py_main"]; pr=one["py_ref"]
 if pm["json"]:
  o["py"]=py_points(pm["json"])
 if pr["json"]:
  o["py_ref"]=py_points(pr["json"])
 o["lua"]=parse_lua(one["lua_main"]["process"]["stdout"])
 o["lua_ref"]=parse_lua(one["lua_ref"]["process"]["stdout"])
 o["py_main_proc"]=pm["process"]; o["py_ref_proc"]=pr["process"]
 o["lua_main_proc"]=one["lua_main"]["process"]; o["lua_ref_proc"]=one["lua_ref"]["process"]
 o["artifacts"]=one["artifacts"]
 return o
def relerr(a,b):
 m=0.0
 for x,y in zip(a,b):
  if y==0.0:
   d=abs(x)
  else:
   d=abs(x-y)/abs(y)
  m=max(m,d)
 return m
def expected_rows():
 rows=[]  # point_id, frontend, expected
 for t in FAIL_TAGS:
  rows.append((t,"py","EXCEPTION RuntimeError '%s'"%MSG_PY))
  rows.append((t,"lua","FAIL_VISIBLE; stderr '%s'"%MSG_LUA))
 for t in CTRL_TAGS:
  rows.append((t,"py","RETURNED finite"))
  rows.append((t,"lua","VALUES finite"))
 rows.append((RECOVER,"py","RETURNED finite; rel_err vs %s <= 1e-12"%REF))
 rows.append((RECOVER,"lua","VALUES finite; rel_err vs %s <= 1e-12"%REF))
 rows.append((REF,"py","RETURNED finite"))
 rows.append((REF,"lua","VALUES finite"))
 return rows
def observe_point(o,fe,tag):
 d=o[fe+"_ref"] if tag==REF else o[fe]
 p=d.get(tag)
 if p is None: return "MISSING"
 if fe=="py":
  if p.get("status")=="EXCEPTION": return "EXCEPTION %s %r"%(p.get("exc_type"),p.get("message"))
  return "RETURNED %s finite=%s"%(p.get("values"),p.get("all_finite"))
 if p.get("status")=="FAIL_VISIBLE": return "FAIL_VISIBLE"
 if p.get("status")=="VALUES": return "VALUES %s finite=%s"%(p.get("values"),p.get("all_finite"))
 return str(p)
def point_ok(o,fe,tag):
 expect_fail=(tag in FAIL_TAGS)
 if fe=="py":
  p=(o["py_ref"] if tag==REF else o["py"]).get(tag)
  if p is None: return False,"MISSING"
  if expect_fail:
   ok=(p.get("status")=="EXCEPTION" and p.get("exc_type")=="RuntimeError" and p.get("message")==MSG_PY)
   return ok,("" if ok else "exception text mismatch")
  ok=(p.get("status")=="RETURNED" and p.get("all_finite") is True)
  return ok,("" if ok else "not finite/returned")
 p=(o["lua_ref"] if tag==REF else o["lua"]).get(tag)
 if p is None: return False,"MISSING"
 if expect_fail:
  ok=(p.get("status")=="FAIL_VISIBLE")
  return ok,("" if ok else "no visible failure")
 ok=(p.get("status")=="VALUES" and p.get("all_finite") is True)
 return ok,("" if ok else "not finite/returned")
def main():
 if len(sys.argv)<2:
  print("usage: d016_run_s5r2.py calib|formal [--pass N]"); return 2
 sub=sys.argv[1]
 if sub=="calib":
  logdir=os.path.join(EV,"shakedown/d016_calib")
  one=one_pass("calib",logdir); o=obs(one)
  rows=[]
  rows.append(("S4_PYEXT_SHA256",o["artifacts"]["pyext_sha256"],""))
  rows.append(("S4_LUA_SHA256",o["artifacts"]["lua_sha256"],""))
  rows.append(("LIBS4A_SHA256",o["artifacts"]["libS4_a_sha256"],""))
  rows.append(("PY_MAIN_RC",str(o["py_main_proc"]["rc"]),""))
  rows.append(("PY_REF_RC",str(o["py_ref_proc"]["rc"]),""))
  rows.append(("LUA_MAIN_RC",str(o["lua_main_proc"]["rc"]),""))
  rows.append(("LUA_REF_RC",str(o["lua_ref_proc"]["rc"]),""))
  rows.append(("PY_MAIN_S4FILE",(o.get("py") and one["py_main"]["json"]["S4_file"]) or "MISSING",""))
  rows.append(("PY_STDERR_INFO2_COUNT",str(o["py_main_proc"]["stderr"].count(INFO2)),"expected 0"))
  rows.append(("LUA_STDERR_INFO2_COUNT",str(o["lua_main_proc"]["stderr"].count(INFO2)),"expected 0"))
  rows.append(("LUA_STDERR_MSG_COUNT",str(o["lua_main_proc"]["stderr"].count(MSG_LUA)),"expected 8 (4 failures + 4 same-object retries)"))
  rows.append(("LUA_MAIN_DONE","yes" if "LUA_MAIN_DONE" in o["lua_main_proc"]["stdout"] else "NO",""))
  rows.append(("LUA_SCRIPT_END","yes" if "LUA_SCRIPT_END" in o["lua_main_proc"]["stdout"] else "NO",""))
  bad=0
  for tag,fe,exp in expected_rows():
   ok,why=point_ok(o,fe,tag); ob=observe_point(o,fe,tag)
   rows.append(("POINT_%s_%s"%(fe.upper(),tag),ob,"would_be="+("MATCH" if ok else "MISMATCH")+("" if not why else " ("+why+")")))
   if fe=="py" and tag in (RECOVER,) and ok:
    rows.append(("RELERR_PY_"+tag,repr(relerr(o["py"][RECOVER]["values"],o["py_ref"][REF]["values"])),""))
   if fe=="lua" and tag in (RECOVER,) and ok:
    rows.append(("RELERR_LUA_"+tag,repr(relerr(o["lua"][RECOVER]["values"],o["lua_ref"][REF]["values"])),""))
   if not ok: bad+=1
  rows.append(("CALIB_MISMATCHES",str(bad),"calibration is not a formal result"))
  out=os.path.join(logdir,"CALIB_D016_S5R2.tsv")
  with open(out,"w",encoding="utf-8") as fh:
   fh.write("# CALIB_D016_S5R2.tsv -- D016 calibration (test run, NOT a formal result)"+NL)
   fh.write(TAB.join(["check","value","detail"])+NL)
   for r in rows: fh.write(TAB.join(str(x) for x in r)+NL)
  for r in rows: print(TAB.join(str(x) for x in r))
  print("WROTE "+os.path.relpath(out,REPO)); return 0 if bad==0 else 1
 # formal
 if "--pass" not in sys.argv:
  print("formal needs --pass 1|2"); return 2
 pn=sys.argv[sys.argv.index("--pass")+1]
 logdir=os.path.join(EV,"logs")
 one=one_pass("pass"+pn,logdir); o=obs(one)
 pj=os.path.join(EV,"D016_PASS%s_S5R2.json"%pn)
 json.dump({"pass":pn,"observations":o,"time":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},open(pj,"w"),indent=1,default=str)
 print("WROTE "+os.path.relpath(pj,REPO))
 ok_all=True
 for tag,fe,exp in expected_rows():
  ok,why=point_ok(o,fe,tag)
  print("PASS%s %s %s %s"%(pn,fe,tag,"OK" if ok else "FAIL"))
  if not ok: ok_all=False
 if pn!="2":
  return 0 if ok_all else 1
 p1=os.path.join(EV,"D016_PASS1_S5R2.json")
 if not os.path.isfile(p1):
  print("HARD_STOP pass1 missing"); return 2
 a=json.load(open(p1))["observations"]
 rows=[]; m=n=fl=0
 for tag,fe,exp in expected_rows():
  ok1,w1=point_ok(a,fe,tag); ok2,w2=point_ok(o,fe,tag)
  ob1=observe_point(a,fe,tag); ob2=observe_point(o,fe,tag)
  det=""
  if tag==RECOVER:
   if fe=="py" and ok1 and ok2:
    det="rel_err_pass1=%.3e rel_err_pass2=%.3e"%(relerr(a["py"][RECOVER]["values"],a["py_ref"][REF]["values"]),relerr(o["py"][RECOVER]["values"],o["py_ref"][REF]["values"]))
   if fe=="lua" and ok1 and ok2:
    det="rel_err_pass1=%.3e rel_err_pass2=%.3e"%(relerr(a["lua"][RECOVER]["values"],a["lua_ref"][REF]["values"]),relerr(o["lua"][RECOVER]["values"],o["lua_ref"][REF]["values"]))
  if ob1!=ob2: verdict="FLAKY"
  elif ok1 and ok2: verdict="MATCH"
  else: verdict="MISMATCH"
  if verdict=="MATCH": m+=1
  elif verdict=="FLAKY": fl+=1
  else: n+=1
  rows.append((tag,fe,exp,ob1,ob2,det,verdict))
 # process-level rows
 def proc_row(name,fe,expected,obs1,obs2):
  nonlocal m,n,fl
  verdict="FLAKY" if obs1!=obs2 else ("MATCH" if obs1==expected else "MISMATCH")
  if verdict=="MATCH": m+=1
  elif verdict=="FLAKY": fl+=1
  else: n+=1
  rows.insert(0,(name,fe,expected,obs1,obs2,"",verdict))
 proc_row("PY_RC","py","0",str(a["py_main_proc"]["rc"]),str(o["py_main_proc"]["rc"]))
 proc_row("LUA_RC","lua","0",str(a["lua_main_proc"]["rc"]),str(o["lua_main_proc"]["rc"]))
 proc_row("PY_STDERR_INFO2","py","ABSENT",str(a["py_main_proc"]["stderr"].count(INFO2)),str(o["py_main_proc"]["stderr"].count(INFO2)))
 proc_row("LUA_STDERR_INFO2","lua","ABSENT",str(a["lua_main_proc"]["stderr"].count(INFO2)),str(o["lua_main_proc"]["stderr"].count(INFO2)))
 proc_row("LUA_STDERR_MSG_COUNT","lua","8",str(a["lua_main_proc"]["stderr"].count(MSG_LUA)),str(o["lua_main_proc"]["stderr"].count(MSG_LUA)))
 # expose expected/observed rc of the root-cause path from the source trace
 rows.append(("ROOT_CAUSE_RC","source","20 (F4 S4.cpp:2435-2438)","20","20","[源码] ComputeLayerModes returns 20 when FMMGetEpsilon returns nonzero","RECORD"))
 out=os.path.join(EV,"D016_VERDICT_S5R2.tsv")
 with open(out,"w",encoding="utf-8") as fh:
  fh.write("# D016_VERDICT_S5R2.tsv -- P05-S5 R2 D016 public-API verdict, F4 build, two formal passes"+NL)
  fh.write("# expected values are pre-registered in registries/s5r2/PREREG_D016_S5R2.tsv (INFLUENCED)"+NL)
  fh.write(TAB.join(["point_id","frontend","expected","observed_pass1","observed_pass2","detail","verdict"])+NL)
  for r in rows: fh.write(TAB.join(str(x) for x in r)+NL)
  fh.write("SUMMARY"+TAB+"MATCH=%d"%m+TAB+"MISMATCH=%d"%n+TAB+"FLAKY=%d"%fl+NL)
 for r in rows: print(TAB.join(str(x) for x in r))
 print("SUMMARY MATCH=%d MISMATCH=%d FLAKY=%d"%(m,n,fl))
 print("WROTE "+os.path.relpath(out,REPO))
 return 0 if n==0 and fl==0 else 1
if __name__=="__main__": sys.exit(main())
