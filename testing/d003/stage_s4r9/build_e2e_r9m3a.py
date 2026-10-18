#!/usr/bin/env python3
# build_e2e_r9m3a.py -- build the F4 export with the D003 injector linked into the Python extension and the Lua frontend.
# usage: python3 -I -B testing/d003/stage_s4r9/build_e2e_r9m3a.py OUTDIR OUT.tsv
import os, sys, subprocess, hashlib, datetime

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TREE = os.path.join(EV, "trees/E2E_F4")
INJ = os.path.join(REPO, "testing/d003/src/inject_d003.cpp")
WRAP = ["-Wl,--wrap=malloc",
        "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
        "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
        "-Wl,--wrap=_Z9S4_mallocm"]
TAB = chr(9)
NL = chr(10)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def run(cmd, logpath, cwd=None, shell=False):
    with open(logpath, "a", encoding="utf-8") as fh:
        fh.write("### " + (cmd if isinstance(cmd, str) else " ".join(cmd)) + NL)
        p = subprocess.run(cmd, cwd=cwd or REPO, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        fh.write(p.stdout)
        fh.write("### rc=" + str(p.returncode) + NL)
    return p.returncode, p.stdout


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "e2e_build")
    out_tsv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "E2E_BUILD_R9M3A.tsv")
    os.makedirs(outdir, exist_ok=True)
    log = os.path.join(outdir, "build.log")
    open(log, "w", encoding="utf-8").write("# E2E build log " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + NL)
    rows = []
    if not os.path.isdir(TREE):
        os.makedirs(TREE, exist_ok=True)
        rc, _ = run("git archive HEAD | tar -x -C " + TREE, log, shell=True)
        rows.append(("EXPORT_TREE", str(rc), TREE))
        if rc != 0:
            raise SystemExit("export failed")
    rc, _ = run(["make", "-C", TREE, "-j4", "build/libS4.a", "build/S4", "PYTHON=python3"], log)
    rows.append(("MAKE_LIB_AND_LUA", str(rc), "build/libS4.a + build/S4"))
    inj_obj = os.path.join(TREE, "build", "inject_r9m3a.o")
    rc, _ = run(["g++", "-O1", "-fPIC", "-c", INJ, "-I", os.path.join(TREE, "S4"), "-I", os.path.join(TREE, "S4", "fmm"), "-o", inj_obj], log)
    rows.append(("COMPILE_INJECTOR_FPIC", str(rc), inj_obj))
    inc = subprocess.check_output(["python3-config", "--includes"], text=True).split()
    suffix = subprocess.check_output(["python3-config", "--extension-suffix"], text=True).strip()
    pyside = os.path.join(TREE, "S4" + suffix)
    cmd = ["gcc", "-shared", "-fPIC"] + inc + ["-I", os.path.join(TREE, "S4"), "-I", os.path.join(TREE, "S4", "RNP"), "-I", os.path.join(TREE, "S4", "kiss_fft"),
           os.path.join(TREE, "S4", "main_python.c"), inj_obj, os.path.join(TREE, "build", "libS4.a"), "-o", pyside,
           "-llapack", "-lblas", "-lstdc++"] + WRAP
    rc, _ = run(cmd, log)
    rows.append(("LINK_PYEXT_WITH_WRAP", str(rc), pyside))
    luaside = os.path.join(TREE, "build", "S4_e2e")
    cmd = ["g++", "-O2", os.path.join(TREE, "build", "S4k", "main_lua.o"), inj_obj, os.path.join(TREE, "build", "libS4.a"), "-o", luaside,
           "-llapack", "-lblas", "-llua5.2"] + WRAP
    rc, _ = run(cmd, log)
    rows.append(("LINK_LUA_WITH_WRAP", str(rc), luaside))
    for name, path, expect in (("PYEXT", pyside, None), ("LUA_FRONTEND", luaside, None), ("INJECTOR_OBJ", inj_obj, None)):
        if os.path.isfile(path):
            rows.append((name + "_SHA256", sha256_file(path), os.path.relpath(path, REPO)))
    for name, path in (("PYEXT", pyside), ("LUA_FRONTEND", luaside)):
        if not os.path.isfile(path):
            rows.append((name + "_NM_WRAP_SYMBOLS", "MISSING_ARTIFACT", ""))
            continue
        rc, out = run(["nm", "-C", path], log)
        found = [w for w in ("__wrap_malloc", "__wrap_fft_plan_exec", "__wrap_fft_plan_dft_2d", "__wrap__Z9S4_mallocm") if (" " + w) in out or out.find(w) >= 0]
        rows.append((name + "_NM_WRAP_SYMBOLS", str(len(found)) + "/4", ",".join(found)))
        rc2, out2 = run(["nm", "-D", "--defined-only", path], log)
        dyn = out2.count("__wrap_")
        rows.append((name + "_DYNAMIC_WRAP_COUNT", str(dyn), "symbols visible in the dynamic table"))
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# E2E_BUILD_R9M3A.tsv -- artefacts and wrap-symbol checks of the E2E build (S-D step 2)" + NL)
        fh.write(TAB.join(["check", "value", "detail"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    for r in rows:
        print(TAB.join(r))
    print("WROTE " + out_tsv)
    bad = [r for r in rows if r[0].endswith("_SHA256") and len(r[1]) != 64] + [r for r in rows if "NM_WRAP" in r[0] and not r[1].startswith("4/")]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
