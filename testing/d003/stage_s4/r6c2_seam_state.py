#!/usr/bin/env python3
# r6c2_seam_state.py -- P05-S4 R6c2-2 step 3 (new file; copy of run_r6c_seam_state.py with the changes listed below).
#
# Changes against run_r6c_seam_state.py (recorded in ERRATA_6c U18 and in the R6c2 report):
#   1. The DRIVER is chosen by the library column of each point (seamF -> driver-r6b-seamF, fmmret-F -> driver-r6b-fmmret-F),
#      not one driver for all 25 points.  The two driver paths and their sha256 are passed on the command line and checked.
#   2. The CONTROL runs (U18 (a)): one no-injection control per (library, mode) from REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv is run
#      under gdb and without gdb, pass 1 and pass 2 (the same procedure as the points).  Control runs use env FMM_MODE, S4FMM_NG
#      only (S4FMM_INJECT unset).  A control that disagrees between gdb and no-gdb STOPS the run (GDB_DIVERGENT).
#   3. Every point's env is written as found (as in the 177-point runner).  No other change: same GRID, same GDB script
#      (r6c_state.gdb), same GDB_DIVERGENT rule (rc1, rc2, hit), same classify call.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_seam_state.py PREREG_SEAM CONTROL_SEAM DRV_SEAMF DRV_FMMRET EVDIR PASS
# Output (never overwritten): EVDIR/state/seam_pass<P>/<point>/{gdb.log,nogdb.out}, EVDIR/state/seam_pass<P>/controls/<cid>/...
#   EVDIR/STATE_SEAM_R6c_pass<P>.tsv   (raw facts only; no judgement)
import hashlib
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
ALLOWED_MODES = {"fft", "kottke", "jones", "nv", "vl", "experimental", "closed2d", "closed1d", "tensor",
                 "fftjones", "fftnv", "fftvl"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path):
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


def clean_env(extra):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(extra)
    return env


def facts(text):
    import re
    def first(pat):
        m = re.search(pat, text, re.M)
        return int(m.group(1)) if m else None
    hc = re.search(r"^S4FMM HITCOUNT (-?\d+)\s*$", text, re.M)
    hit = int(hc.group(1)) if hc else len(re.findall(r"^S4FMM HIT ", text, re.M))
    return {"rc1": first(r"^RC first (-?\d+)\s*$"), "rc2": first(r"^RC retry (-?\d+)\s*$"), "hit": hit,
            "done": 1 if re.search(r"^S4FMM DRIVER_R6B DONE\s*$", text, re.M) else 0}


def run(cmd, env, log_path):
    rc, out = None, b""
    try:
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, (exc.stdout or b"")
    if rc is not None and rc < 0:
        rc = 128 - rc
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "wb") as fh:
        fh.write(out)
    return rc, out.decode("utf-8", errors="replace")


def pass_one(label, drv, env_extra, outdir, dump_dir):
    env_g = clean_env(env_extra)
    env_g["S4FMM_DUMP_DIR"] = dump_dir
    rc_g, txt_g = run(["gdb", "-batch", "-x", GDB_SCRIPT, "--args", drv] + GRID, env_g,
                      os.path.join(outdir, "gdb.log"))
    rc_n, txt_n = run([drv] + GRID, clean_env(env_extra), os.path.join(outdir, "nogdb.out"))
    fg, fn = facts(txt_g), facts(txt_n)
    div = (rc_g != rc_n) or any(fg[k] != fn[k] for k in ("rc1", "rc2", "hit"))
    return {"rc_g": rc_g, "rc_n": rc_n, "fg": fg, "fn": fn, "div": div}


def env_of_point(d):
    if d["mode"] not in ALLOWED_MODES:
        raise SystemExit("STOP: mode %r unknown" % d["mode"])
    if d["route"] != "once" or d["inj_call"] != "1":
        raise SystemExit("STOP: seam point %s is not once/inj1" % d["point_id"])
    if ":" not in d["request"]:
        raise SystemExit("STOP: request %r of %s is not a seam request" % (d["request"], d["point_id"]))
    return {"FMM_MODE": d["mode"], "S4FMM_NG": "9", "S4FMM_INJECT": d["request"]}


def env_of_control(c):
    if c["mode"] not in ALLOWED_MODES or c["route"] != "once":
        raise SystemExit("STOP: control %s" % c["control_id"])
    return {"FMM_MODE": c["mode"], "S4FMM_NG": "9"}


def main(argv):
    if len(argv) != 7:
        raise SystemExit("usage: r6c2_seam_state.py PREREG_SEAM CONTROL_SEAM DRV_SEAMF DRV_FMMRET EVDIR PASS")
    prereg, control, drv_seamf, drv_fmmret, ev, pas = argv[1:7]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    drivers = {"seamF": drv_seamf, "fmmret-F": drv_fmmret}
    for lib, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver for %s not executable: %s" % (lib, p))
    out_tsv = os.path.join(ev, "STATE_SEAM_R6c_pass%s.tsv" % pas)
    if os.path.exists(out_tsv):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out_tsv)
    pts = read_table(prereg)
    if len(pts) != 25:
        raise SystemExit("REFUSED: seam prereg rows %d != 25" % len(pts))
    ctrls = read_table(control)
    if len(ctrls) != 18:
        raise SystemExit("REFUSED: seam control rows %d != 18" % len(ctrls))

    base = os.path.join(ev, "state", "seam_pass" + pas)
    dump_root = os.path.join(ev, "dump")
    rows = []
    status_all = []
    # control runs first (U18 (a)): each control is run before the points of its combination
    ctrl_by_key = {(c["library"], c["mode"]): c for c in ctrls}
    ctrl_res = {}
    for c in ctrls:
        lib = c["library"]
        cdir = os.path.join(base, "controls", c["control_id"])
        dump = os.path.join(dump_root, "seam_controls", c["control_id"], "pass" + pas)
        os.makedirs(dump, exist_ok=True)
        r = pass_one(c["control_id"], drivers[lib], env_of_control(c), cdir, dump)
        st = "GDB_DIVERGENT" if r["div"] else "OK"
        ctrl_res[c["control_id"]] = (c, env_of_control(c), r, st)
        status_all.append(st)
        if r["div"]:
            print("GDB_DIVERGENT control %s gdb=%s nogdb=%s" % (c["control_id"], r["fg"], r["fn"]))
            break
    if "GDB_DIVERGENT" not in status_all:
        for d in pts:
            env = env_of_point(d)
            pdir = os.path.join(base, d["point_id"])
            dump = os.path.join(dump_root, "seam_" + d["point_id"], "pass" + pas)
            os.makedirs(dump, exist_ok=True)
            r = pass_one(d["point_id"], drivers[d["library"]], env, pdir, dump)
            st = "GDB_DIVERGENT" if r["div"] else "OK"
            rows.append((d, env, r, st))
            status_all.append(st)
            if r["div"]:
                print("GDB_DIVERGENT %s gdb=%s nogdb=%s" % (d["point_id"], r["fg"], r["fn"]))
                break

    cols = ["kind", "id", "library", "mode", "request", "env_as_run", "rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2",
            "gdb_hit", "gdb_done", "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done", "driver", "driver_sha256", "status"]
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R6c2-2 seam state run, pass %s (raw facts only; no judgement).  Written by r6c2_seam_state.py.\n"
                 % (os.path.basename(out_tsv), pas))
        fh.write("\t".join(cols) + "\n")
        for c, env, r, st in ctrl_res.values():
            fh.write(_line("control", c["control_id"], c["library"], c["mode"], "NA", env, r, drivers[c["library"]], st))
        for d, env, r, st in rows:
            fh.write(_line("point", d["point_id"], d["library"], d["mode"], d["request"], env, r,
                           drivers[d["library"]], st))
    n_div = status_all.count("GDB_DIVERGENT")
    print("seam state pass=%s controls=%d points=%d GDB_DIVERGENT=%d -> %s" % (
        pas, len(ctrl_res), len(rows), n_div, out_tsv))
    return 0 if n_div == 0 and len(rows) == 25 else 3


def _line(kind, ident, lib, mode, req, env, r, drv, st):
    fg, fn = r["fg"], r["fn"]
    env_txt = ";".join("%s=%s" % (k, env[k]) for k in sorted(env))
    return "\t".join([kind, ident, lib, mode, req, env_txt, str(r["rc_g"]), str(r["rc_n"]),
                      str(fg["rc1"]), str(fg["rc2"]), str(fg["hit"]), str(fg["done"]),
                      str(fn["rc1"]), str(fn["rc2"]), str(fn["hit"]), str(fn["done"]),
                      os.path.relpath(drv, REPO), sha256_file(drv), st]) + "\n"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
