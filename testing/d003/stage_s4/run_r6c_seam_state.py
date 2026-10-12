#!/usr/bin/env python3
# run_r6c_seam_state.py -- P05-S4 R6c-2: two-pass state run of the 25 seam points (new file; written after the seam pre-registration).
#
# Driver: driver-r6b-seamF (driver_r6b_state.cpp linked against the -O0 -g seamF library with inject_r4_plan.cpp; built by
# the R6c-2 step, verified by a one-point trial, recorded in ERRATA_6c E6c-3).  Snapshot probe r6_probe, R6BCLM, R6CREQ from
# r6c_state.gdb.  Environment: FMM_MODE=<mode>, S4FMM_NG=9, S4FMM_INJECT=<request>; S4FMM_NTH and S4FMM_TWICE are not set
# (once route, seam requests carry their site numbers).
#
# Per point and pass: one gdb run (snapshots, call outputs via S4FMM_DUMP_DIR) and one no-gdb run.  GDB_DIVERGENT (rc1, rc2,
# hit differ) STOPS the run.  Controls: the 177-point control groups are NOT reused for the seam points (their modes and
# stacks are the same, but the seam library differs); the judge marks I2/I3/I6 UNJUDGED when no matching control exists.
#
# Usage: python3 -I -B testing/d003/stage_s4/run_r6c_seam_state.py PREREG_SEAM DRIVER EVDIR PASS
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402  (imported, not modified)

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 600
GDB_SCRIPT = os.path.join(HERE, "r6c_state.gdb")


def read_prereg(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def env_of(d):
    if d["route"] != "once" or d["inj_call"] != "1":
        raise SystemExit("STOP: seam point %s is not once/inj1" % d["point_id"])
    return {"FMM_MODE": d["mode"], "S4FMM_NG": "9", "S4FMM_INJECT": d["request"]}


def clean_env(extra):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(extra)
    return env


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: run_r6c_seam_state.py PREREG_SEAM DRIVER EVDIR PASS")
    prereg, drv, ev, pas = argv[1:5]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if not (os.path.isfile(drv) and os.access(drv, os.X_OK)):
        raise SystemExit("REFUSED: driver not executable: %s" % drv)
    out = os.path.join(ev, "STATE_SEAM_R6c_pass%s.tsv" % pas)
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    pts = read_prereg(prereg)
    if len(pts) != 25:
        raise SystemExit("REFUSED: prereg rows %d != 25" % len(pts))
    base = os.path.join(ev, "state", "seam_pass" + pas)
    dump_root = os.path.join(ev, "dump")
    rows = []
    for d in pts:
        env = env_of(d)
        pdir = os.path.join(base, d["point_id"])
        os.makedirs(pdir, exist_ok=True)
        dump = os.path.join(dump_root, "seam_" + d["point_id"], "pass" + pas)
        os.makedirs(dump, exist_ok=True)
        env_g = clean_env(env)
        env_g["S4FMM_DUMP_DIR"] = dump
        pg = subprocess.run(["gdb", "-batch", "-x", GDB_SCRIPT, "--args", drv] + GRID, env=env_g, cwd=REPO,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        gtxt = pg.stdout.decode("utf-8", errors="replace")
        with open(os.path.join(pdir, "gdb.log"), "w", encoding="utf-8") as fh:
            fh.write(gtxt)
        pn = subprocess.run([drv] + GRID, env=clean_env(env), cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        ntxt = pn.stdout.decode("utf-8", errors="replace")
        with open(os.path.join(pdir, "nogdb.out"), "w", encoding="utf-8") as fh:
            fh.write(ntxt)
        fg = J.facts_from_log(gtxt)
        fn = J.facts_from_log(ntxt)
        div = (pg.returncode != pn.returncode) or any(fg[k] != fn[k] for k in ("rc1", "rc2", "hit"))
        if div:
            print("GDB_DIVERGENT %s gdb=%s nogdb=%s" % (d["point_id"], fg, fn))
            return 3
        cls, label, reason = J.classify(pg.returncode, fg["rc1"], fg["rc2"], fg["hit"], control=False, real=True, inj_call=1)
        rows.append((d, env, pg.returncode, fg, cls, reason))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R6c-2 seam state run, pass %s (raw facts; no judgement).\n" % (os.path.basename(out), pas))
        fh.write("point_id\tlibrary\tmode\trequest\tenv_as_run\trc_gdb\trc1\trc2\thit\tclass_facts\treason\tgdb_log\tnogdb_log\n")
        for d, env, rc, f, cls, reason in rows:
            env_txt = ";".join("%s=%s" % (k, env[k]) for k in sorted(env))
            fh.write("\t".join([d["point_id"], d["library"], d["mode"], d["request"], env_txt, str(rc), str(f["rc1"]),
                                str(f["rc2"]), str(f["hit"]), cls, reason,
                                os.path.join("state", "seam_pass" + pas, d["point_id"], "gdb.log"),
                                os.path.join("state", "seam_pass" + pas, d["point_id"], "nogdb.out")]) + "\n")
    print("seam state pass=%s points=%d -> %s" % (pas, len(rows), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
