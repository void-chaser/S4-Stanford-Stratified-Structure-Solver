#!/usr/bin/env python3
# s5r1_appendix.py -- fill the formal end-gate summary into P05_S5R1_REPORT.md appendix B.
import os,sys,re
REPO=os.getcwd()
EV=os.path.join(REPO,"checkpoints/p05/evidence/p05-s5r1")
REPORT=os.path.join(REPO,"checkpoints/p05/P05_S5R1_REPORT.md")
GATE=os.path.join(EV,"gate","GATE_S5R1_end.txt")
TAB=chr(9); NL=chr(10); FENCE=chr(96)*3
def rd(p): return open(p,encoding="utf-8").read()
def wr(p,t): open(p,"w",encoding="utf-8").write(t)
def main():
 if not os.path.isfile(GATE):
  print("HARD_STOP formal gate file missing: "+GATE); return 2
 if not os.path.isfile(REPORT):
  print("HARD_STOP report missing"); return 2
 g=rd(GATE).splitlines()
 counts=[l for l in g if l.startswith("COUNTS")]
 fails=[l for l in g if l.startswith("FAILS=")]
 crashed=[l for l in g if "CHECK_CRASHED_ZERO" in l]
 post=[l for l in g if "POST_I_CALL_COUNT" in l]
 failsdetail=[l for l in g if l.startswith("FAIL"+TAB)]
 if not counts or not fails:
  print("HARD_STOP gate file lacks COUNTS/FAILS"); return 2
 if not crashed:
  print("HARD_STOP gate file lacks CHECK_CRASHED_ZERO"); return 2
 body=[FENCE]
 body+=counts
 body+=fails
 body+=crashed
 body+=post
 if failsdetail:
  body.append("# FAIL detail lines:")
  body+=failsdetail
 body.append(FENCE)
 txt=rd(REPORT)
 if "PENDING_FORMAL_END_GATE" not in txt:
  print("REPORT_APPENDIX_ALREADY_FILLED_OR_MARKER_MISSING")
 else:
  txt=txt.replace("PENDING_FORMAL_END_GATE",NL.join(body),1)
  wr(REPORT,txt)
 print("APPENDIX_B filled lines=%d report_bytes=%d"%(len(body),len(txt.encode())))
 return 0
if __name__=="__main__": sys.exit(main())
