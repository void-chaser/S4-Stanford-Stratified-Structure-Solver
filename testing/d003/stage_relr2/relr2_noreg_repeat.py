#!/usr/bin/env python3
# relr2_noreg_repeat.py -- REL-R2 no-injection research: determinism control for the one probe case whose
# B and F4 outputs are not byte-identical (jones_nb1).  Three repeats per tree; writes only
# $EV/NOREG_REPEAT_RELR2.tsv.  Read-only for the trees.
import os, sys, json, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
TREES = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1/trees")
CASE = os.path.join(REPO, "testing/d003/stage_relr2/relr2_noreg_case.py")
OUT = os.path.join(EV, "NOREG_REPEAT_RELR2.tsv")
TAB = chr(9)
NL = chr(10)
CASE_ID = "jones_nb1"


def main():
    lines = ["# NOREG_REPEAT_RELR2.tsv -- determinism control, 3 repeats of probe case " + CASE_ID + " per tree",
             "# Written " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(["tree", "repeat", "proc_rc", "status", "all_finite", "value"])]
    for label in ("B", "F4"):
        tdir = os.path.join(TREES, label)
        for rep in (1, 2, 3):
            p = subprocess.run([sys.executable, CASE, "--tree", tdir, "--case", CASE_ID],
                               capture_output=True, text=True, timeout=300, cwd=REPO)
            js = [l for l in p.stdout.splitlines() if l.strip().startswith("{")]
            rec = json.loads(js[-1]) if js else {}
            lines.append(TAB.join([label, str(rep), str(p.returncode), rec.get("status", "?"),
                                   str(rec.get("all_finite", "")), str(rec.get("value", ""))[:200]]))
    os.makedirs(EV, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("WROTE", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
