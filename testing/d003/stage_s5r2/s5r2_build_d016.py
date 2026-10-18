#!/usr/bin/env python3
# s5r2_build_d016.py -- export 05097a7:S4 to $EV/trees/F4 (build root; S4/ is the F4 export),
# build libS4.a + Lua S4 + the Python extension without any injector, record sha256 and compare
# with registries/s4r9/M3b/E2E_BUILD_R9M3B.tsv for reference only (differing is not FAIL).
import os,sys,subprocess,hashlib,datetime,re
REPO=subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r2")
TREE=os.path.join(EV,"trees/F4")
LOG=os.path.join(EV,"logs/d016_build.log")
TAB=chr(9); NL=chr(10)
COMMIT="05097a7"; S4_TREE_EXPECT="589e15eb11fcb04e031b524f25a443e7921946cf"
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as fh:
  for b in iter(lambda:fh.read(65536),b""): h.update(b)
 return h.hexdigest()
def run(cmd,shell=False,log_fh=None):
 txt=cmd if isinstance(cmd,str) else " ".join(cmd)
 if log_fh: log_fh.write("### "+txt+NL)
 p=subprocess.run(cmd,cwd=REPO,shell=shell,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if log_fh:
  log_fh.write(p.stdout); log_fh.write("### rc="+str(p.returncode)+NL)
 return p.returncode,p.stdout
def main():
 rows=[]
 for d in (os.path.join(EV,"trees"),os.path.join(EV,"logs")):
  os.makedirs(d,exist_ok=True)
 fh=open(LOG,"w",encoding="utf-8")
 fh.write("# D016 build log s5r2 "+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")+NL)
 rc,out=run(["git","rev-parse",COMMIT+":S4"],log_fh=fh)
 rows.append(("S4_TREE_SHA_OF_"+COMMIT,out.strip(),"expected "+S4_TREE_EXPECT))
 if out.strip()!=S4_TREE_EXPECT:
  print("HARD_STOP S4 tree hash mismatch"); return 2
 if not os.path.isdir(os.path.join(TREE,"S4")):
  os.makedirs(os.path.join(TREE,"S4"),exist_ok=True)
  rc,_=run("git archive "+COMMIT+":S4 | tar -x -C "+os.path.join(TREE,"S4"),shell=True,log_fh=fh)
  rows.append(("EXPORT_S4_RC",str(rc),"git archive "+COMMIT+":S4 -> trees/F4/S4"))
  rc,_=run("git archive "+COMMIT+" Makefile Makefile.common Makefile.Linux | tar -x -C "+TREE,shell=True,log_fh=fh)
  rows.append(("EXPORT_MAKEFILES_RC",str(rc),"same commit"))
 else:
  rows.append(("EXPORT_S4_RC","exists","tree already exported"))
 for f in ("S4/main_python.c","S4/main_lua.c","S4/pattern/pattern.c","S4/S4.cpp","S4/fmm/fmm_PolBasisVL.cpp","Makefile.common"):
  rows.append(("EXPORTED_"+f.replace("/","_"),"present" if os.path.isfile(os.path.join(TREE,f)) else "MISSING",""))
 rc,out=run(["make","-C",TREE,"-j4","build/libS4.a","build/S4","PYTHON=python3"],log_fh=fh)
 rows.append(("MAKE_LIB_AND_LUA_RC",str(rc),"build/libS4.a + build/S4 (no injector)"))
 lib=os.path.join(TREE,"build/libS4.a"); lua=os.path.join(TREE,"build/S4")
 suffix=subprocess.check_output(["python3-config","--extension-suffix"],text=True).strip()
 inc=subprocess.check_output(["python3-config","--includes"],text=True).split()
 pyext=os.path.join(TREE,"S4"+suffix)
 cmd=["gcc","-shared","-fPIC"]+inc+["-I",os.path.join(TREE,"S4"),"-I",os.path.join(TREE,"S4","RNP"),
      "-I",os.path.join(TREE,"S4","kiss_fft"),os.path.join(TREE,"S4","main_python.c"),lib,
      "-o",pyext,"-llapack","-lblas","-lstdc++"]
 rc,_=run(cmd,log_fh=fh)
 rows.append(("LINK_PYEXT_RC",str(rc),"no --wrap, no injector"))
 rows.append(("PYTHON_VERSION",subprocess.check_output(["python3","--version"],text=True).strip(),""))
 rows.append(("EXTENSION_SUFFIX",suffix,""))
 arts={}
 for name,path in (("LIB_S4_A",lib),("PYEXT",pyext),("LUA_FRONTEND",lua)):
  if os.path.isfile(path):
   h=sha256_file(path); arts[name]=h
   rows.append((name+"_PATH",os.path.relpath(path,REPO),""))
   rows.append((name+"_BYTES",str(os.path.getsize(path)),""))
   rows.append((name+"_SHA256",h,""))
  else:
   rows.append((name+"_SHA256","MISSING",""))
 ref=os.path.join(REPO,"checkpoints/p05/registries/s4r9/M3b/E2E_BUILD_R9M3B.tsv")
 refd={}
 if os.path.isfile(ref):
  hdr=None
  for line in open(ref,encoding="utf-8"):
   line=line.rstrip(NL)
   if not line.strip() or line.startswith("#"): continue
   f=line.split(TAB)
   if hdr is None: hdr=f; continue
   d=dict(zip(hdr,f)); refd[d.get("check","")]=d.get("value","")
 for k in ("LIB_S4_A","PYEXT","LUA_FRONTEND"):
  rv=refd.get(k+"_SHA256","MISSING_REF")
  cmp="SAME" if rv==arts.get(k) else "DIFFERENT"
  rows.append(("REF_M3B_"+k,"ref="+rv,"comparison="+cmp+" (reference only; not FAIL)"))
 rows.append(("BUILD_LOG",os.path.relpath(LOG,REPO),"full output"))
 fh.close()
 out=os.path.join(EV,"D016_BUILD_S5R2.tsv")
 with open(out,"w",encoding="utf-8") as of:
  of.write("# D016_BUILD_S5R2.tsv -- F4 build of the D016 public-API test (no injector)"+NL)
  of.write(TAB.join(["check","value","detail"])+NL)
  for r in rows: of.write(TAB.join(r)+NL)
 for r in rows: print(TAB.join(r))
 print("WROTE "+os.path.relpath(out,REPO))
 bad=[r for r in rows if r[0].endswith("_SHA256") and len(r[1])!=64]
 bad+=[r for r in rows if r[0].startswith("EXPORTED_") and r[1]!="present"]
 bad+=[r for r in rows if r[0].endswith("_RC") and r[1]!="0"]
 return 0 if not bad else 1
if __name__=="__main__": sys.exit(main())
