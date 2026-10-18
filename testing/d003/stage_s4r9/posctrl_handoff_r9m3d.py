#!/usr/bin/env python3
# posctrl_handoff_r9m3d.py -- positive control for the formal S5 handoff script: drop RP-R6d-7 from a ledger copy and
# require the formal script to exit non-zero (orphan TRANSFERRED_S5 id). The tampered copy and the run output are
# written under $EV/posctrl/handoff/. New file (r9m3d).
# usage: posctrl_handoff_r9m3d.py
import os, sys, subprocess
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
D = os.path.join(EV, "posctrl/handoff")
LEDGER = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
HANDOFF = os.path.join(REPO, "testing/d003/stage_s4r9/s5_handoff_r9m3d.py")
OUT = os.path.join(EV, "POSCTRL_HANDOFF_R9M3D.txt")
NL = chr(10)
TAB = chr(9)


def main():
    os.makedirs(D, exist_ok=True)
    lines = open(LEDGER, encoding="utf-8").read().splitlines()
    tampered = []
    found = 0
    for line in lines:
        if not line.strip() or line.startswith("#"):
            tampered.append(line)
            continue
        f = line.split(TAB)
        if f and f[0] == "RP-R6d-7":
            found += 1
            continue
        tampered.append(line)
    tp = os.path.join(D, "LEDGER_MISSING_R6D7.tsv")
    open(tp, "w", encoding="utf-8").write(NL.join(tampered) + NL)
    outp = os.path.join(D, "S5_HANDOFF_TAMPERED.tsv")
    p = subprocess.run([sys.executable, "-I", "-B", HANDOFF, "--ledger", tp, "--out", outp], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok = (found == 1) and p.returncode != 0 and ("RP-R6d-7" in ((p.stdout or "") + (p.stderr or "")))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_HANDOFF_R9M3D.txt -- formal handoff script on a ledger copy with RP-R6d-7 removed" + NL)
        fh.write("TAMPERED_COPY: " + os.path.relpath(tp, REPO) + " (data row RP-R6d-7 removed)" + NL)
        fh.write("FSM_RC=%d" % p.returncode + NL)
        fh.write("FSM_STDOUT_TAIL: " + (p.stdout or "").strip().splitlines()[-1][:200] if (p.stdout or "").strip() else "FSM_STDOUT_TAIL: (empty)")
        fh.write(NL)
        fh.write("RESULT: %s (required rc!=0 and a message naming RP-R6d-7)" % ("PASS" if ok else "FAIL") + NL)
    print("found=%d rc=%d -> %s" % (found, p.returncode, "PASS" if ok else "FAIL"))
    print((p.stdout or "").strip()[:300])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
