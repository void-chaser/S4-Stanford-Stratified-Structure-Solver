#!/usr/bin/env python3
# run_r6c_seam_gdb.py -- P05-S4 R6c-2: measure inj_call of the 25 seam points under gdb (new file; read-only measurement).
#
# For each point: one gdb run with r6c_seam_gdb.gdb (R6SEAMCALL n at each S4_Simulation_GetFieldPlane entry), using the
# same driver and environment as run_r6c_seam.py.  inj_call = the R6SEAMCALL number of the last call before the first
# "S4FMM HIT" line (the injection happens inside that GetFieldPlane call).  If no HIT line: inj_call = NA.
# Also compares the gdb-run facts (RC first, RC retry, HITCOUNT) with the no-gdb facts of SEAM_R6c_pass1.tsv: a disagreement
# is GDB_DIVERGENT and the script STOPS (brief 3.1 rule, applied to seam points as well).
#
# Output: EVDIR/SEAM_INJCALL_R6c.tsv (one row per point), EVDIR/seam_dbg/injcall/<point>.gdb.log.  Refuses to overwrite.
#
# Usage: python3 -I -B testing/d003/stage_s4/run_r6c_seam_gdb.py R4_RESULTS DRIVER_seamF DRIVER_fmmret EVDIR
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import run_r6c_seam as S  # noqa: E402  (same point list, environment rule and driver selection)

GDB_SCRIPT = os.path.join(REPO, "testing", "d003", "stage_s4", "r6c_seam_gdb.gdb")
RE_CALL = re.compile(r"^R6SEAMCALL (\d+)\s*$")
RE_HIT = re.compile(r"^S4FMM HIT ")
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)


def inj_call_of(text):
    """Return (inj_call or None, number of HIT lines).  inj_call = last R6SEAMCALL before the first HIT line."""
    last = None
    first_hit = None
    n_hit = 0
    for ln in text.splitlines():
        m = RE_CALL.match(ln)
        if m:
            last = int(m.group(1))
            continue
        if RE_HIT.match(ln):
            n_hit += 1
            if first_hit is None:
                first_hit = last
    return first_hit, n_hit


def gdb_run(drv, env_extra, logpath):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(env_extra)
    cmd = ["gdb", "-batch", "-x", GDB_SCRIPT, "--args", drv] + S.GRID
    p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=S.TIMEOUT_S)
    text = p.stdout.decode("utf-8", errors="replace")
    os.makedirs(os.path.dirname(logpath), exist_ok=True)
    with open(logpath, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p.returncode, text


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: run_r6c_seam_gdb.py R4_RESULTS DRIVER_seamF DRIVER_fmmret EVDIR")
    r4, drv_s, drv_f, ev = argv[1:5]
    drivers = {"seamF": drv_s, "fmmret-F": drv_f}
    out = os.path.join(ev, "SEAM_INJCALL_R6c.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    pts = S.read_r4_f_rows(r4)
    if len(pts) != 25:
        raise SystemExit("REFUSED: expected 25 seam points")
    nopass = {}
    with open(os.path.join(ev, "SEAM_R6c_pass1.tsv"), encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("#") or ln.startswith("point_id") or not ln.strip():
                continue
            f = ln.rstrip("\n").split("\t")
            nopass[f[0]] = {"rc": f[5], "rc1": f[6], "rc2": f[7], "hit": f[8]}
    rows = []
    n_div = 0
    for d in pts:
        env = S.env_for(d)
        logp = os.path.join(ev, "seam_dbg", "injcall", d["point_id"] + ".gdb.log")
        rc_g, text = gdb_run(drivers[d["library"]], env, logp)
        m1 = RE_RC1.search(text)
        m2 = RE_RC2.search(text)
        mh = RE_HC.search(text)
        inj, n_hit = inj_call_of(text)
        base = nopass.get(d["point_id"], {})
        g_rc1 = m1.group(1) if m1 else "None"
        g_rc2 = m2.group(1) if m2 else "None"
        g_hit = mh.group(1) if mh else str(n_hit)
        div = (base.get("rc1") != g_rc1) or (base.get("rc2") != g_rc2) or (base.get("hit") != g_hit)
        if div:
            n_div += 1
            print("GDB_DIVERGENT %s gdb rc1=%s rc2=%s hit=%s vs nogdb %s" % (d["point_id"], m1 and m1.group(1), m2 and m2.group(1),
                                                                   mh and mh.group(1), base))
            break
        rows.append((d, rc_g, inj, n_hit, m1.group(1) if m1 else "NA", m2.group(1) if m2 else "NA", logp))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# SEAM_INJCALL_R6c.tsv -- inj_call of the 25 seam points measured under gdb (R6c-2 brief 4.3).\n")
        fh.write("# inj_call = R6SEAMCALL number of the GetFieldPlane call that contains the first injection HIT line.\n")
        fh.write("point_id\tlibrary\tmode\trequest\tgdb_rc\thit_lines\tinj_call\trc1_gdb\trc2_gdb\tgdb_log\n")
        for d, rc_g, inj, n_hit, r1, r2, logp in rows:
            fh.write("\t".join([d["point_id"], d["library"], d["mode"], d["request"], str(rc_g), str(n_hit),
                                "NA" if inj is None else str(inj), r1, r2, os.path.relpath(logp, REPO)]) + "\n")
        fh.write("# summary: points %d ; GDB_DIVERGENT %d\n" % (len(rows), n_div))
    print("gdb-injcall points=%d gdb_divergent=%d -> %s" % (len(rows), n_div, out))
    return 0 if n_div == 0 and len(rows) == 25 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
