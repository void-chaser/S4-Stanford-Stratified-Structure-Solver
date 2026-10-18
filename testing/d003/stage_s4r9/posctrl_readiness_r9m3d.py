#!/usr/bin/env python3
# posctrl_readiness_r9m3d.py -- positive control for the formal readiness script: add header-style rows to a ledger copy
# and require the recomputed criterion 1 count to stay equal to the unique id count. The tampered copy and the run
# output are written under $EV/posctrl/readiness/. New file (r9m3d).
# usage: posctrl_readiness_r9m3d.py
import os, sys, subprocess, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
D = os.path.join(EV, "posctrl/readiness")
LEDGER = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
READY = os.path.join(REPO, "testing/d003/stage_s4r9/readiness_r9m3d.py")
OUT = os.path.join(EV, "POSCTRL_READINESS_R9M3D.txt")
NL = chr(10)
TAB = chr(9)


def main():
    os.makedirs(D, exist_ok=True)
    lines = open(LEDGER, encoding="utf-8").read().splitlines()
    hdr_line = ""
    data_idx = []
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            continue
        if hdr_line == "":
            hdr_line = line
            continue
        data_idx.append(i)
    if not hdr_line or len(data_idx) < 6:
        print("POSCTRL_READINESS: FAIL (cannot locate header/data rows)")
        if os.path.isfile(OUT):
            os.remove(OUT)
        open(OUT, "w", encoding="utf-8").write("# POSCTRL_READINESS_R9M3D.txt" + NL + "RESULT: FAIL (structure)" + NL)
        return 1
    insert_after = data_idx[2]
    new = []
    for i, line in enumerate(lines):
        new.append(line)
        if i == insert_after:
            new.append(hdr_line)
            new.append(hdr_line)
    new.append(hdr_line)
    tp = os.path.join(D, "LEDGER_EXTRA_HEADER_ROWS.tsv")
    open(tp, "w", encoding="utf-8").write(NL.join(new) + NL)
    outp = os.path.join(D, "READINESS_TAMPERED.tsv")
    p = subprocess.run([sys.executable, "-I", "-B", READY, "--ledger", tp, "--out", outp], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    count = -1
    uniq = -1
    if os.path.isfile(outp):
        hdr = None
        for line in open(outp, encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                m = re.search(r"# LEDGER_UNIQUE_IDS=(\d+)", line)
                if m:
                    uniq = int(m.group(1))
                continue
            f = line.rstrip("\r\n").split(TAB)
            if hdr is None:
                hdr = f
                continue
            r = dict(zip(hdr, f))
            if r.get("item", "").startswith("①"):
                m = re.search(r"红点唯一 id 数=(\d+)", r.get("recomputed", ""))
                count = int(m.group(1)) if m else -1
    ok = p.returncode == 0 and count == uniq and count > 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_READINESS_R9M3D.txt -- formal readiness script on a ledger copy with extra header-style rows" + NL)
        fh.write("TAMPERED_COPY: " + os.path.relpath(tp, REPO) + " (3 extra header lines inserted)" + NL)
        fh.write("FSM_RC=%d" % p.returncode + NL)
        fh.write("CRITERION1_UNIQUE_IDS=%d LEDGER_UNIQUE_IDS=%d" % (count, uniq) + NL)
        fh.write("RESULT: %s (required rc=0 and criterion-1 count == unique id count)" % ("PASS" if ok else "FAIL") + NL)
    print("rc=%d count=%d uniq=%d -> %s" % (p.returncode, count, uniq, "PASS" if ok else "FAIL"))
    if not ok:
        print((p.stdout or "").strip()[:300])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
