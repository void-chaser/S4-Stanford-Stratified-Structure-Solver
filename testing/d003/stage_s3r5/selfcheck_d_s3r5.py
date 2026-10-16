#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# selfcheck_d_s3r5.py -- Selfcheck D: Run single-pass on 9 points in dbg on F4 (S-I, U289(D)).
# Strictly records observed facts; does not judge MATCH and does not write to any VERDICT table.
import os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
OUT_TSV = os.path.join(EV, "SELFCHECK_D_S3R5.tsv")
DRV = os.path.join(EV, "build", "init-F4-dbg")

# 3 combos x 3 sites = 9 points
# K values from K_MAP_F4_S3R5.tsv
TEST_POINTS = [
    ("SOLN-1763-closed2d-ng1-F4-dbg", "closed2d-ng1", "closed2d", "1", 1763, 9),
    ("SOLN-1764-closed2d-ng1-F4-dbg", "closed2d-ng1", "closed2d", "1", 1764, 10),
    ("SOLN-1765-closed2d-ng1-F4-dbg", "closed2d-ng1", "closed2d", "1", 1765, 11),
    ("SOLN-1763-fft-ng5-F4-dbg", "fft-ng5", "fft", "5", 1763, 10),
    ("SOLN-1764-fft-ng5-F4-dbg", "fft-ng5", "fft", "5", 1764, 11),
    ("SOLN-1765-fft-ng5-F4-dbg", "fft-ng5", "fft", "5", 1765, 12),
    ("SOLN-1763-kottke-ng5-F4-dbg", "kottke-ng5", "kottke", "5", 1763, 10),
    ("SOLN-1764-kottke-ng5-F4-dbg", "kottke-ng5", "kottke", "5", 1764, 11),
    ("SOLN-1765-kottke-ng5-F4-dbg", "kottke-ng5", "kottke", "5", 1765, 12),
]

def run_one(pid, cname, mode, ng, site, k):
    env = os.environ.copy()
    env["FMM_MODE"] = mode
    env["S4FMM_NG"] = ng
    env["S4FMM_INJECT"] = "init:%d" % k
    env.pop("S4_FAIL_ALLOC_AT", None)
    cmd = [DRV, "pattern", "both", "4", "3"]
    p = subprocess.run(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    rc1 = None
    rc2 = None
    post_call1_sol = "UNKNOWN"
    hit = 0
    crash_call = None
    signal = 0
    
    if p.returncode < 0:
        signal = -p.returncode
    elif p.returncode > 128:
        signal = p.returncode - 128
    elif p.returncode == 0:
        signal = 0
    else:
        signal = 0
        
    stdout_lines = p.stdout.splitlines()
    stderr_lines = p.stderr.splitlines()
    
    for l in stdout_lines:
        if l.startswith("RC first "):
            rc1 = int(l.split()[2])
        elif l.startswith("RC retry "):
            rc2 = int(l.split()[2])
        elif l.startswith("R6STATE 1 solution_null "):
            s_null = int(l.split()[3])
            post_call1_sol = "NULL" if s_null == 1 else "NONNULL"
        elif "S4FMM HITCOUNT 1" in l:
            hit = 1
            
    for l in stderr_lines:
        if "S4FMM HIT real malloc failure:" in l:
            hit = 1
            
    if signal != 0:
        if rc1 is None:
            crash_call = "1"
        else:
            crash_call = "2"
    else:
        crash_call = "NONE"
        
    rc1_str = str(rc1) if rc1 is not None else "MISSING"
    rc2_str = str(rc2) if rc2 is not None else "MISSING"
    
    row = (pid, cname, str(site), "init-F4-dbg", str(k), rc1_str, rc2_str, str(signal), str(hit), post_call1_sol, crash_call, str(p.returncode))
    print("Point %s: rc1=%s, rc2=%s, signal=%d, hit=%d, post_call1_sol=%s, crash_call=%s" % (pid, rc1_str, rc2_str, signal, hit, post_call1_sol, crash_call))
    return row

def main():
    if not os.path.isfile(DRV):
        sys.stderr.write("REFUSED: driver not found: %s\n" % DRV)
        return 2
    rows = []
    for pid, cname, mode, ng, site, k in TEST_POINTS:
        r = run_one(pid, cname, mode, ng, site, k)
        rows.append(r)
        
    headers = ["point_id", "combo", "defect_site", "driver", "k_fail", "rc1", "rc2", "signal", "hit", "post_call1_solution", "crash_call", "driver_exitcode"]
    with open(OUT_TSV, "w", encoding="utf-8") as fh:
        fh.write("# SELFCHECK_D_S3R5.tsv -- Selfcheck D observed facts on F4 dbg (U289(D))\n")
        fh.write("# Note: Strictly records observed facts. Not judged as MATCH, not a verification report.\n")
        fh.write("\t".join(headers) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("Wrote %s (%d rows)" % (OUT_TSV, len(rows)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
