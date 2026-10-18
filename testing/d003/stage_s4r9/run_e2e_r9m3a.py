#!/usr/bin/env python3
# run_e2e_r9m3a.py -- E2E driver: one fresh subprocess per point step; captures rc, stdout, stderr, HIT lines,
# Python exception type/message and the Lua error text. M3a runs it in smoke mode only (no-injection controls).
# usage: python3 -I -B testing/d003/stage_s4r9/run_e2e_r9m3a.py smoke OUTDIR | formal OUTDIR
import os, sys, json, subprocess

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TREE = os.path.join(EV, "trees/E2E_F4")
PYEXT_DIR = TREE
LUA_BIN = os.path.join(TREE, "build/S4_e2e")
PY_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_python_r9m3a.py")
LUA_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_lua_r9m3a.lua")
PREREG = os.path.join(EV, "PREREG_E2E_R9M3A.tsv")
TAB = chr(9)
NL = chr(10)


def read_prereg():
    rows = []
    hdr = None
    for line in open(PREREG, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def run(cmd, env_extra):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = PYEXT_DIR
    env.pop("S4FMM_INJECT", None)
    env.pop("S4FMM_NTH", None)
    env.update(env_extra)
    p = subprocess.run(cmd, cwd=TREE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
    hits = [l for l in p.stderr.splitlines() if "S4FMM HIT" in l]
    return {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "hits": hits, "n_hits": len(hits)}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "shakedown/e2e_smoke")
    os.makedirs(outdir, exist_ok=True)
    rows = read_prereg()
    results = []
    for r in rows:
        is_control = r.get("is_control", "NO") == "YES"
        if mode == "smoke" and not is_control:
            continue
        if mode == "smoke" and r.get("frontend") != "py":
            continue
        spec = r.get("spec", "fft")
        rec = {"point_id": r["point_id"], "frontend": r["frontend"], "spec": spec, "steps": {}}
        if r["frontend"] == "py":
            inj = {}
            if not is_control:
                inj = {"S4FMM_INJECT": r.get("inject_mode", ""), "S4FMM_NTH": r.get("nth", "1")}
            rec["steps"]["run"] = run([sys.executable, "-I", "-B", PY_SCRIPT, spec], inj)
        else:
            rec["steps"]["clean"] = run([LUA_BIN, LUA_SCRIPT, spec, "clean"], {})
            if not is_control:
                rec["steps"]["inject"] = run([LUA_BIN, LUA_SCRIPT, spec, "inject"], {"S4FMM_INJECT": r.get("inject_mode", ""), "S4FMM_NTH": r.get("nth", "1")})
            rec["steps"]["fresh"] = run([LUA_BIN, LUA_SCRIPT, spec, "fresh"], {})
        results.append(rec)
        print("POINT %s frontend=%s spec=%s rc=%s" % (r["point_id"], r["frontend"], spec, rec["steps"]["run"]["rc"] if "run" in rec["steps"] else {k: v["rc"] for k, v in rec["steps"].items()}))
    outp = os.path.join(outdir, "E2E_RUN_%s.json" % mode)
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    print("WROTE " + outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
