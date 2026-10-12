#!/usr/bin/env python3
# run_r6c_seam.py -- P05-S4 R6c-2: equivalence check and two-pass run of the 25 R4 seam points on the -O0 -g rebuild (new file).
#
# Inputs:
#   RESULTS_R4.tsv      the R4 table (tree F rows = the 25 seam points; library column = seamF or fmmret-F)
#   DRIVER_seamF        seam_dbg/drivers/seamF/driver-d003   (the -O0 -g rebuild; sha256 recorded by the build)
#   DRIVER_fmmret       seam_dbg/drivers/fmmret-F/driver-d003
# The driver is selected by the library column of the R4 row (no other choice).  The environment of each run is
# FMM_MODE=<mode>, S4FMM_NG=9, S4FMM_INJECT=<request>; S4FMM_NTH is NOT set (R4 seam requests carry their own site numbers);
# S4FMM_TWICE is removed (every seam point is route once in R4, column twice = '-').  Anything else is a STOP.
#
# Steps:
#   1. equivalence: for each point, two runs (pass 1, pass 2) WITHOUT gdb; classify with judge_d003.classify (imported,
#      not modified; facts only: rc, rc1, rc2, hit).  The R4 F row must be equal in rc1 class: the R4 observed class
#      (obs_pass1 column) is compared with the new class.  Output: SEAM_EQUIV_R6c.tsv (one row per point).
#   2. two-pass table of raw facts: SEAM_R6c_pass1.tsv, SEAM_R6c_pass2.tsv (no judgement in them).
#   The gdb run that measures inj_call is a separate step (run_r6c_seam_gdb.sh).  Nothing here is judged as a verdict.
#
# Usage: python3 -I -B testing/d003/stage_s4/run_r6c_seam.py R4_RESULTS DRIVER_seamF DRIVER_fmmret EVDIR
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402  (imported, not modified)

TIMEOUT_S = 600
GRID = ["pattern", "both", "4", "3"]
MODES = {"fft", "kottke", "jones", "nv", "vl", "experimental", "closed2d", "closed1d", "tensor",
         "fftjones", "fftnv", "fftvl"}


def read_r4_f_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]
    header = lines[0].split("\t")
    for ln in lines[1:]:
        d = dict(zip(header, ln.split("\t")))
        if d["tree"] == "F" and d["family"] in ("A", "B2", "C", "D", "E"):
            rows.append(d)
    return rows


def env_for(d):
    # R4 seam rows carry no NTH and no route column; the request string holds the site numbers (linearsolve:S:K:info, ...).
    if d["mode"] not in MODES:
        raise SystemExit("STOP: mode %r unknown" % d["mode"])
    if not d["request"] or ":" not in d["request"]:
        raise SystemExit("STOP: request %r is not a known seam request" % d["request"])
    return {"FMM_MODE": d["mode"], "S4FMM_NG": "9", "S4FMM_INJECT": d["request"]}


def run(drv, env_extra):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(env_extra)
    try:
        p = subprocess.run([drv] + GRID, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=TIMEOUT_S)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, exc.stdout or b""
    if rc < 0:
        rc = 128 - rc
    return rc, out.decode("utf-8", errors="replace")


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: run_r6c_seam.py R4_RESULTS DRIVER_seamF DRIVER_fmmret EVDIR")
    r4, drv_s, drv_f, ev = argv[1:5]
    drivers = {"seamF": drv_s, "fmmret-F": drv_f}
    for k, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver not executable: %s" % p)
    pts = read_r4_f_rows(r4)
    if len(pts) != 25:
        raise SystemExit("REFUSED: expected 25 F seam rows, got %d" % len(pts))
    # the output files are never overwritten (U17)
    outs = [os.path.join(ev, "SEAM_EQUIV_R6c.tsv"), os.path.join(ev, "SEAM_R6c_pass1.tsv"), os.path.join(ev, "SEAM_R6c_pass2.tsv")]
    for o in outs:
        if os.path.exists(o):
            raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % o)
    facts = {"1": [], "2": []}
    for pas in ("1", "2"):
        for d in pts:
            env = env_for(d)
            rc, txt = run(drivers[d["library"]], env)
            f = J.facts_from_log(txt)
            cls, label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=False, real=True, inj_call=1)
            facts[pas].append((d, env, rc, f, cls, reason))
    for pas in ("1", "2"):
        with open(outs[1] if pas == "1" else outs[2], "w", encoding="utf-8") as fh:
            fh.write("# SEAM_R6c_pass%s.tsv -- raw facts of the 25 seam points, pass %s (no judgement).\n" % (pas, pas))
            fh.write("point_id\tlibrary\tmode\trequest\tenv_as_run\trc\trc1\trc2\thit\tclass_facts\treason\n")
            for d, env, rc, f, cls, reason in facts[pas]:
                env_txt = ";".join("%s=%s" % (k, env[k]) for k in sorted(env))
                fh.write("\t".join([d["point_id"], d["library"], d["mode"], d["request"], env_txt, str(rc),
                                    str(f["rc1"]), str(f["rc2"]), str(f["hit"]), cls, reason]) + "\n")
    # equivalence against R4 (observed class of pass 1 and pass 2 of R4 = obs_pass1 / obs_pass2 columns)
    with open(outs[0], "w", encoding="utf-8") as fh:
        fh.write("# SEAM_EQUIV_R6c.tsv -- equivalence of the -O0 -g rebuild with R4 tree F rows (25 points).  Rule: E6b-7 / brief 4.2.\n")
        fh.write("point_id\tlibrary\tr4_obs_pass1\tr4_obs_pass2\tnew_class_p1\tnew_class_p2\tr4_rc_p1\tnew_rc_p1\tnew_rc_p2\tequal\n")
        n_equal = 0
        for i, d in enumerate(pts):
            c1 = facts["1"][i][4]
            c2 = facts["2"][i][4]
            rc1 = facts["1"][i][2]
            rc2 = facts["2"][i][2]
            eq = (c1 == d["obs_pass1"] and c2 == d["obs_pass2"] and str(rc1) == d["rc_p1"])
            n_equal += 1 if eq else 0
            fh.write("\t".join([d["point_id"], d["library"], d["obs_pass1"], d["obs_pass2"], c1, c2, d["rc_p1"],
                                str(rc1), str(rc2), "EQUAL" if eq else "NOT_EQUAL"]) + "\n")
        fh.write("# summary: equal %d of %d\n" % (n_equal, len(pts)))
    print("equal %d of %d -> %s" % (n_equal, len(pts), outs[0]))
    return 0 if n_equal == len(pts) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
