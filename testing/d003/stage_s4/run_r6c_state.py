#!/usr/bin/env python3
# run_r6c_state.py -- P05-S4 R6c-1: state runner for the 177 judgeable points and the 16 control groups (new file).
#
# Inputs (hash-checked by the caller, re-checked here):
#   PREREG_V2   REGISTRY_S4_PRE_R6b_STATE_v2.tsv (177 rows; written by r6c_prereg_v2.py before any run)
#   CONTROL     REGISTRY_S4_PRE_R6b_CONTROL.tsv (16 control groups; R6b, unchanged)
#   DRIVER      driver-r6b-dbgF (the R6b build, sha256 checked against the R6b evidence)
#   GDB_SCRIPT  testing/d003/stage_s4/r6c_state.gdb (copy of r6b_state.gdb + R6CREQ, sources r6c_state_gdb.py)
#
# Per point, per pass: two runs.  (a) under gdb, with S4FMM_DUMP_DIR set (snapshots, R6BCLM, R6CREQ, call outputs);
# (b) without gdb (plain driver).  The facts rc1, rc2, rc3, hit of (a) and (b) are compared; a disagreement marks the
# point GDB_DIVERGENT and the runner STOPS (AGENTS-level stop rule of the brief).
#
# Environment of each run is computed from the table columns and written to the result table as found:
#   FMM_MODE       <- mode
#   S4FMM_NG       <- 9  (stack pattern both 4 3 is fixed; the stack column is checked to equal it)
#   S4FMM_INJECT   <- request  (points only; controls: unset)
#   S4FMM_NTH      <- nth column for R3 points (s4malloc, exec, plan); NOT set for plancall (K and M are in the request)
#   S4FMM_TWICE    <- slab for route twice (set explicitly); removed for route once (and for controls of once)
# Any other combination is a STOP: the runner does not guess.
#
# Usage: python3 -I -B testing/d003/stage_s4/run_r6c_state.py MODE PREREG CONTROL DRIVER EVDIR PASS [--subset]
#   MODE   = full | smoke   (smoke: one point per (mode, route, inj_call) + its control; results kept apart, not judged)
#   PASS   = 1 | 2
# Output (never overwritten):
#   EVDIR/state/pass<P>/<point>/{gdb.log,nogdb.out,call1.txt,call2.txt,call3.txt}
#   EVDIR/state/pass<P>/controls/<control_id>/...
#   EVDIR/STATE_R6c_pass<P>.tsv    (full)      |  EVDIR/SMOKE_R6c_pass<P>.tsv (smoke)
import hashlib
import os
import re
import subprocess
import sys

TIMEOUT_S = 600
NG = "9"
STACK = "pattern both 4 3"
REQ_OK = re.compile(r"^(s4malloc|exec|plan|plancall:[1-9][0-9]*:[1-9][0-9]*)$")
KIND_NTH = ("s4malloc", "exec", "plan")
PLANCALL_RE = re.compile(r"^plancall:([1-9][0-9]*):([1-9][0-9]*)$")
ALLOWED_MODES = ("fft", "kottke", "jones", "nv", "vl", "experimental", "closed2d", "closed1d", "tensor",
                 "fftjones", "fftnv", "fftvl")

RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_RC3 = re.compile(r"^R6CALLS 3 (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_HITLINE = re.compile(r"^S4FMM HIT ", re.M)
RE_DONE = re.compile(r"^S4FMM DRIVER_R6B DONE\s*$", re.M)


def sha256(path):
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
            if len(f) != len(header):
                raise SystemExit("REFUSED: %s: %d fields, header %d" % (path, len(f), len(header)))
            rows.append(dict(zip(header, f)))
    return rows


def env_for_point(d, twice_col):
    """Return the environment dict for one point row (only the variables the runner sets)."""
    mode = d["mode"]
    if mode not in ALLOWED_MODES:
        raise SystemExit("STOP: mode %r not in the known driver modes" % mode)
    if d["stack"] != STACK:
        raise SystemExit("STOP: stack %r differs from %r" % (d["stack"], STACK))
    req = d["request"]
    if not REQ_OK.match(req):
        raise SystemExit("STOP: request %r is outside the known environment combinations" % req)
    env = {"FMM_MODE": mode, "S4FMM_NG": NG, "S4FMM_INJECT": req}
    if req.startswith("plancall:"):
        m = PLANCALL_RE.match(req)
        if m.group(1) != d["NTH_or_K"].split("=")[1] or m.group(2) != d["M"].split("=")[1]:
            raise SystemExit("STOP: request %r disagrees with K/M columns for %s" % (req, d["point_id"]))
        # K and M are read from the request by the injector; S4FMM_NTH is not set for plancall.
    else:
        if d["NTH_or_K"].startswith("NTH="):
            env["S4FMM_NTH"] = d["NTH_or_K"].split("=")[1]
        else:
            raise SystemExit("STOP: no NTH for request %r in %s" % (req, d["point_id"]))
    if d["route"] == "twice":
        if d["twice"] != twice_col:
            raise SystemExit("STOP: twice column %r for %s" % (d["twice"], d["point_id"]))
        env["S4FMM_TWICE"] = "slab"
    elif d["route"] == "once":
        pass  # S4FMM_TWICE is removed from the inherited environment below
    else:
        raise SystemExit("STOP: route %r" % d["route"])
    return env


def control_env(c):
    mode = c["mode"]
    if mode not in ALLOWED_MODES:
        raise SystemExit("STOP: control mode %r" % mode)
    env = {"FMM_MODE": mode, "S4FMM_NG": NG}
    if c["route"] == "twice":
        env["S4FMM_TWICE"] = "slab"
    elif c["route"] != "once":
        raise SystemExit("STOP: control route %r" % c["route"])
    return env


def build_env(extra):
    env = dict(os.environ)
    for k in ("FMM_MODE", "S4FMM_NG", "S4FMM_INJECT", "S4FMM_NTH", "S4FMM_TWICE", "S4FMM_DUMP", "S4FMM_DUMP_DIR",
              "S4FMM_DUMP_RETRY"):
        env.pop(k, None)
    env.update(extra)
    return env


def facts(text):
    m1 = RE_RC1.search(text)
    m2 = RE_RC2.search(text)
    m3 = RE_RC3.search(text)
    hc = RE_HITC.search(text)
    hit = int(hc.group(1)) if hc else len(RE_HITLINE.findall(text))
    return {
        "rc1": int(m1.group(1)) if m1 else None,
        "rc2": int(m2.group(1)) if m2 else None,
        "rc3": int(m3.group(1)) if m3 else None,
        "hit": hit,
        "done": 1 if RE_DONE.search(text) else 0,
    }


def run(cmd, env, cwd, log_path, timeout=TIMEOUT_S):
    rc = None
    out = b""
    try:
        p = subprocess.run(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        rc = p.returncode
        out = p.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = exc.stdout or b""
    except OSError as exc:
        out = ("RUNNER: could not start: %s\n" % exc).encode()
    if rc is not None and rc < 0:
        rc = 128 - rc
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "wb") as fh:
        fh.write(out)
    return rc, out.decode("utf-8", errors="replace")


def pass_one(label, drv, gdb_script, env_extra, outdir, repo, pass_no, dump_dir):
    """Run one (gdb, nogdb) pair for one label.  Returns dict with both sets of facts."""
    env_g = build_env(env_extra)
    env_g["S4FMM_DUMP_DIR"] = dump_dir
    gdb_log = os.path.join(outdir, "gdb.log")
    rc_g, txt_g = run(["gdb", "-batch", "-x", gdb_script, "--args", drv, "pattern", "both", "4", "3"],
                      env_g, repo, gdb_log)
    env_n = build_env(env_extra)
    nogdb_log = os.path.join(outdir, "nogdb.out")
    rc_n, txt_n = run([drv, "pattern", "both", "4", "3"], env_n, repo, nogdb_log)
    return {"rc_g": rc_g, "rc_n": rc_n, "fg": facts(txt_g), "fn": facts(txt_n),
            "txt_g": txt_g, "txt_n": txt_n, "gdb_log": gdb_log, "nogdb_log": nogdb_log}


def main(argv):
    if len(argv) not in (7, 8):
        raise SystemExit("usage: run_r6c_state.py full|smoke PREREG CONTROL DRIVER EVDIR PASS [--subset]")
    mode, prereg, control, drv, evdir, pas = argv[1:7]
    if mode not in ("full", "smoke"):
        raise SystemExit("mode must be full or smoke")
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if not (os.path.isfile(drv) and os.access(drv, os.X_OK)):
        raise SystemExit("REFUSED: driver not executable: %s" % drv)
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    gdb_script = os.path.join(repo, "testing", "d003", "stage_s4", "r6c_state.gdb")
    rows = read_table(prereg)
    if len(rows) != 177:
        raise SystemExit("REFUSED: prereg rows %d != 177" % len(rows))
    crows = read_table(control)
    if len(crows) != 16:
        raise SystemExit("REFUSED: control rows %d != 16" % len(crows))

    if mode == "smoke":
        seen = {}
        for d in rows:
            key = (d["mode"], d["route"], d["inj_call"])
            seen.setdefault(key, d)
        rows = [seen[k] for k in sorted(seen)]
        crows = [c for c in crows if any(c["mode"] == r["mode"] and c["route"] == r["route"] for r in rows)]
        out_tsv = os.path.join(evdir, "SMOKE_R6c_pass%s.tsv" % pas)
        subdir = "smoke"
    else:
        out_tsv = os.path.join(evdir, "STATE_R6c_pass%s.tsv" % pas)
        subdir = "state"
    if os.path.exists(out_tsv):
        raise SystemExit("REFUSED: result exists, never overwritten (U17): %s" % out_tsv)

    base = os.path.join(evdir, subdir, "pass" + pas)
    dump_root = os.path.join(evdir, "dump")
    results = []
    rows_out = []
    for d in rows:
        env_extra = env_for_point(d, "slab")
        pdir = os.path.join(base, d["point_id"])
        dump = os.path.join(dump_root, d["point_id"], "pass" + pas)
        os.makedirs(dump, exist_ok=True)
        r = pass_one(d["point_id"], drv, gdb_script, env_extra, pdir, repo, pas, dump)
        div = (r["rc_g"] != r["rc_n"]) or any(r["fg"][k] != r["fn"][k] for k in ("rc1", "rc2", "rc3", "hit"))
        status = "GDB_DIVERGENT" if div else "OK"
        rows_out.append((d, env_extra, r, status))
        results.append(status)
        if div:
            print("GDB_DIVERGENT %s rc_g=%s rc_n=%s fg=%s fn=%s" % (d["point_id"], r["rc_g"], r["rc_n"], r["fg"], r["fn"]))
            break
    # controls
    ctrl_out = []
    if not any(s == "GDB_DIVERGENT" for s in results):
        for c in crows:
            env_c = control_env(c)
            cdir = os.path.join(base, "controls", c["control_id"])
            dump = os.path.join(dump_root, "controls", c["control_id"], "pass" + pas)
            os.makedirs(dump, exist_ok=True)
            r = pass_one(c["control_id"], drv, gdb_script, env_c, cdir, repo, pas, dump)
            div = (r["rc_g"] != r["rc_n"]) or any(r["fg"][k] != r["fn"][k] for k in ("rc1", "rc2", "rc3", "hit"))
            ctrl_out.append((c, env_c, r, "GDB_DIVERGENT" if div else "OK"))
            if div:
                print("GDB_DIVERGENT control %s" % c["control_id"])
                break

    # write the result table (facts only; the judgement is in r6c_state_judge.py)
    cols = ["kind", "id", "mode", "route", "twice", "inj_call", "tree", "env_as_run", "rc_gdb", "rc_nogdb",
            "gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done", "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit",
            "nogdb_done", "gdb_log_sha256", "nogdb_log_sha256", "status"]
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R6c-1 raw facts of one pass (pass %s).  Written by run_r6c_state.py (no judgement).\n"
                 % (os.path.basename(out_tsv), pas))
        fh.write("# env_as_run = environment variables the runner set (inherited FMM_* and S4FMM_* are removed first).\n")
        fh.write("\t".join(cols) + "\n")
        for d, env_e, r, st in rows_out:
            fh.write("\t".join(_row("point", d["point_id"], d["mode"], d["route"], d["twice"], d["inj_call"], d["tree"],
                                    env_e, r, st)) + "\n")
        for c, env_e, r, st in ctrl_out:
            fh.write("\t".join(_row("control", c["control_id"], c["mode"], c["route"], c["twice"], "NA", "F",
                                    env_e, r, st)) + "\n")
    print("pass=%s mode=%s points=%d controls=%d status_counts=%s -> %s" % (
        pas, mode, len(rows_out), len(ctrl_out), {s: results.count(s) for s in set(results)}, out_tsv))
    return 0 if all(s == "OK" for s in results) else 2


def _row(kind, ident, mode, route, twice, inj_call, tree, env_e, r, st):
    env_txt = ";".join("%s=%s" % (k, env_e[k]) for k in sorted(env_e))
    fg, fn = r["fg"], r["fn"]
    return [kind, ident, mode, route, twice, str(inj_call), tree, env_txt,
            str(r["rc_g"]), str(r["rc_n"]),
            str(fg["rc1"]), str(fg["rc2"]), str(fg["rc3"]), str(fg["hit"]), str(fg["done"]),
            str(fn["rc1"]), str(fn["rc2"]), str(fn["rc3"]), str(fn["hit"]), str(fn["done"]),
            sha256(r["gdb_log"]), sha256(r["nogdb_log"]), st]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
