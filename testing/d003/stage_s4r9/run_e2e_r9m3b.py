#!/usr/bin/env python3
# run_e2e_r9m3b.py -- E2E driver: one fresh process per step, reference in a separate no-injection process.
# usage: python3 -I -B testing/d003/stage_s4r9/run_e2e_r9m3b.py smoke OUTDIR
#        python3 -I -B testing/d003/stage_s4r9/run_e2e_r9m3b.py formal PASS_DIR      (resumable: finished points are skipped)
# Python points: ref (separate process) -> inject process (A first solve, B same-object retry after the
# injection env is popped, C fresh object in the same process) -> R2 fresh process.
# Lua batch points: ref process -> inject process (the process exits on the reported error) -> R2 process.
# Lua REPL points: the same stdin script in three processes; the REPL keeps running after the error.
import os, sys, json, subprocess

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TREE = os.path.join(EV, "trees/E2E_F4")
PY_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_python_r9m3b.py")
LUA_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_lua_r9m3b.lua")
REPL_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_lua_repl_r9m3b.txt")
LUA_BIN = os.path.join(TREE, "build/S4_e2e")
PREREG = os.path.join(EV, "PREREG_E2E_R9M3B.tsv")
TAB = chr(9)
NL = chr(10)
KEYS = ["point_id", "frontend", "spec", "options", "inject_mode", "nth", "target_file_line", "calib_size",
        "exp_hit", "exp_visible", "exp_retry_same", "exp_retry_fresh", "tolerance", "m12_k_group", "is_control", "note"]


def read_prereg():
    rows = []
    hdr = None
    for line in open(PREREG, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def run(argv, env_extra, stdin_path=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = TREE
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("S4FMM_INJECT", None)
    env.pop("S4FMM_NTH", None)
    env.update(env_extra)
    timed = False
    fin = open(stdin_path, "r", encoding="utf-8") if stdin_path else subprocess.DEVNULL
    try:
        p = subprocess.run(argv, cwd=TREE, env=env, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, timeout=180)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        timed, rc = True, None
        out = exc.stdout or ""
        err = exc.stderr or ""
    finally:
        if stdin_path:
            fin.close()
    hits = [ln for ln in err.splitlines() if "S4FMM HIT" in ln]
    return {"rc": rc, "stdout": out, "stderr": err, "n_hits": len(hits), "hit_lines": hits, "timed_out": timed}


def record(row):
    fe = row["frontend"]
    spec = row["spec"]
    control = row.get("is_control", "NO") == "YES"
    env = {} if control else {"S4FMM_INJECT": row["inject_mode"], "S4FMM_NTH": row["nth"]}
    rec = {"point_id": row["point_id"], "frontend": fe, "spec": spec,
           "inject_mode": row["inject_mode"], "nth": row["nth"], "calib_size": row["calib_size"],
           "target_file_line": row["target_file_line"], "is_control": row["is_control"],
           "tolerance": row["tolerance"], "steps": {}}
    if fe == "py":
        rec["steps"]["ref"] = run(["python3", "-B", PY_SCRIPT, "ref", spec], {})
        rec["steps"]["inject"] = run(["python3", "-B", PY_SCRIPT, "inject", spec], env)
        rec["steps"]["r2"] = run(["python3", "-B", PY_SCRIPT, "fresh", spec], {})
    elif fe == "lua_batch":
        rec["steps"]["ref"] = run([LUA_BIN, "-a", spec, LUA_SCRIPT], {})
        rec["steps"]["inject"] = run([LUA_BIN, "-a", spec, LUA_SCRIPT], env)
        rec["steps"]["r2"] = run([LUA_BIN, "-a", spec, LUA_SCRIPT], {})
    else:
        rec["steps"]["ref"] = run([LUA_BIN, "-a", spec], {}, stdin_path=REPL_SCRIPT)
        rec["steps"]["inject"] = run([LUA_BIN, "-a", spec], env, stdin_path=REPL_SCRIPT)
        rec["steps"]["r2"] = run([LUA_BIN, "-a", spec], {}, stdin_path=REPL_SCRIPT)
    return rec


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "shakedown/e2e_smoke")
    os.makedirs(os.path.join(outdir, "points"), exist_ok=True)
    rows = read_prereg()
    if mode == "smoke":
        rows = [r for r in rows if r.get("is_control", "NO") == "YES"]
    done = skipped = 0
    for row in rows:
        pid = row["point_id"]
        fp = os.path.join(outdir, "points", pid + ".json")
        if os.path.isfile(fp):
            skipped += 1
            continue
        rec = record(row)
        with open(fp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
        done += 1
        st = rec["steps"]
        print("POINT %-26s fe=%-9s spec=%-5s rc_ref=%s rc_inj=%s rc_r2=%s hits=%d %s" % (
            pid, row["frontend"], row["spec"], st["ref"]["rc"], st["inject"]["rc"], st["r2"]["rc"],
            st["inject"]["n_hits"], "(control)" if row.get("is_control", "NO") == "YES" else ""))
    with open(os.path.join(outdir, "E2E_RUN_%s.json" % mode), "w", encoding="utf-8") as fh:
        json.dump({"mode": mode, "outdir": outdir, "done": done, "skipped": skipped,
                   "points": [r["point_id"] for r in rows]}, fh, indent=1)
    print("DONE=%d SKIPPED=%d OUTDIR=%s" % (done, skipped, outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
