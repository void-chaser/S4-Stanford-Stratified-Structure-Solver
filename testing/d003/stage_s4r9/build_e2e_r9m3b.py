#!/usr/bin/env python3
# build_e2e_r9m3b.py -- rebuild the F4 export with the D003 injector linked into the Python extension and the Lua
# frontend (same link parameters as build_e2e_r9m3a.py), record artefact sha256, the 4 __wrap symbols and compare
# with the M3a build table. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/build_e2e_r9m3b.py [--force-make]
import os, sys, subprocess, hashlib, datetime

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TREE = os.path.join(EV, "trees/E2E_F4")
INJ = os.path.join(REPO, "testing/d003/src/inject_d003.cpp")
OUTDIR = os.path.join(EV, "e2e_build")
LOG = os.path.join(OUTDIR, "build.log")
TAB = chr(9)
NL = chr(10)
WRAP = ["-Wl,--wrap=malloc",
        "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
        "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
        "-Wl,--wrap=_Z9S4_mallocm"]
M3A = {"PYEXT_SHA256": "eae23933e6604d4ae9c67e94d5f118d9db4ff639cb4536a1bd582437cb584a47",
       "LUA_FRONTEND_SHA256": "20d43f997f2a1b5b47dcc6dd5d28c122df7ff8a980e79cc8b90ae27e50cc8fd6",
       "INJECTOR_OBJ_SHA256": "636cb15e7021982da40b950266c60d58acd6316ef06774f0ccee2c9043f476a3",
       "LIB_S4_A_SHA256": "a28eaa5d6a0ed347870c9bf9f4c38d16cac23f340cfe17cf1725854f8c6d8b8d"}
ROWS = []


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def log(msg):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(msg + NL)


def run(cmd, shell=False, log_out=True):
    txt = cmd if isinstance(cmd, str) else " ".join(cmd)
    log("### " + txt)
    p = subprocess.run(cmd, cwd=REPO, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if log_out:
        log(p.stdout)
    log("### rc=" + str(p.returncode))
    return p.returncode, p.stdout


def main():
    force = "--force-make" in sys.argv
    os.makedirs(OUTDIR, exist_ok=True)
    open(LOG, "w", encoding="utf-8").write("# E2E build log r9m3b " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + NL)
    if not os.path.isdir(os.path.join(TREE, "S4")):
        os.makedirs(TREE, exist_ok=True)
        rc, _ = run("git archive HEAD | tar -x -C " + TREE, shell=True)
        ROWS.append(("EXPORT_TREE", str(rc), os.path.relpath(TREE, REPO)))
        if rc != 0:
            print("export failed")
            return 1
    else:
        ROWS.append(("EXPORT_TREE", "exists", os.path.relpath(TREE, REPO)))
    if force or not os.path.isfile(os.path.join(TREE, "build", "libS4.a")):
        rc, _ = run(["make", "-C", TREE, "-j4", "build/libS4.a", "build/S4", "PYTHON=python3"])
    else:
        rc = 0
    ROWS.append(("MAKE_LIB_AND_LUA", str(rc), "build/libS4.a + build/S4"))
    inj_obj = os.path.join(TREE, "build", "inject_r9m3b.o")
    rc, _ = run(["g++", "-O1", "-fPIC", "-c", INJ, "-I", os.path.join(TREE, "S4"), "-I", os.path.join(TREE, "S4", "fmm"), "-o", inj_obj])
    ROWS.append(("COMPILE_INJECTOR_FPIC", str(rc), "inject_r9m3b.o"))
    inc = subprocess.check_output(["python3-config", "--includes"], text=True).split()
    suffix = subprocess.check_output(["python3-config", "--extension-suffix"], text=True).strip()
    pyside = os.path.join(TREE, "S4" + suffix)
    cmd = ["gcc", "-shared", "-fPIC"] + inc + ["-I", os.path.join(TREE, "S4"), "-I", os.path.join(TREE, "S4", "RNP"),
           "-I", os.path.join(TREE, "S4", "kiss_fft"), os.path.join(TREE, "S4", "main_python.c"), inj_obj,
           os.path.join(TREE, "build", "libS4.a"), "-o", pyside, "-llapack", "-lblas", "-lstdc++"] + WRAP
    rc, _ = run(cmd)
    ROWS.append(("LINK_PYEXT_WITH_WRAP", str(rc), "same four --wrap options as build_e2e_r9m3a.py"))
    luaside = os.path.join(TREE, "build", "S4_e2e")
    cmd = ["g++", "-O2", os.path.join(TREE, "build", "S4k", "main_lua.o"), inj_obj, os.path.join(TREE, "build", "libS4.a"),
           "-o", luaside, "-llapack", "-lblas", "-llua5.2"] + WRAP
    rc, _ = run(cmd)
    ROWS.append(("LINK_LUA_WITH_WRAP", str(rc), "same four --wrap options as build_e2e_r9m3a.py"))
    art = {}
    for name, path in (("PYEXT", pyside), ("LUA_FRONTEND", luaside), ("INJECTOR_OBJ", inj_obj),
                       ("LIB_S4_A", os.path.join(TREE, "build", "libS4.a"))):
        if os.path.isfile(path):
            h = sha256_file(path)
            art[name + "_SHA256"] = h
            ROWS.append((name + "_PATH", os.path.relpath(path, REPO), ""))
            ROWS.append((name + "_SHA256", h, "compare_with_M3a=" + ("SAME" if M3A.get(name + "_SHA256") == h else "DIFFERENT")))
        else:
            ROWS.append((name + "_SHA256", "MISSING", ""))
    for name, path in (("PYEXT", pyside), ("LUA_FRONTEND", luaside)):
        if not os.path.isfile(path):
            ROWS.append((name + "_NM_WRAP_DEFINED", "MISSING_ARTIFACT", ""))
            continue
        rc, out = run(["nm", path])
        log(out)
        want = ["__wrap_malloc", "__wrap__Z13fft_plan_execP12tag_fft_plan",
                "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "__wrap__Z9S4_mallocm"]
        found = [w for w in want if any((ln.split()[-1] == w and ln.split()[1] in ("T", "W", "t", "w")) for ln in out.splitlines() if len(ln.split()) >= 3)]
        ROWS.append((name + "_NM_WRAP_DEFINED", "%d/4" % len(found), ",".join(found)))
        unresolved = [w for w in ("_Z13fft_plan_execP12tag_fft_plan", "_Z15fft_plan_dft_2dPiPSt7complexIdES2_i")
                      if any((ln.split()[0] == "U" and ln.split()[-1] == w) for ln in out.splitlines() if len(ln.split()) >= 2)]
        ROWS.append((name + "_UNRESOLVED_RAW_FFT", str(len(unresolved)), ",".join(unresolved)))
    ROWS.append(("WRAP_OPTIONS", "4", " ".join(WRAP)))
    ROWS.append(("BUILD_LOG", os.path.relpath(LOG, REPO), "full compiler/linker output"))
    with open(os.path.join(EV, "E2E_BUILD_R9M3B.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# E2E_BUILD_R9M3B.tsv -- artefacts, wrap-symbol checks and M3a sha comparison of the M3b E2E build" + NL)
        fh.write(TAB.join(["check", "value", "detail"]) + NL)
        for r in ROWS:
            fh.write(TAB.join(r) + NL)
    for r in ROWS:
        print(TAB.join(r))
    print("WROTE " + os.path.join(EV, "E2E_BUILD_R9M3B.tsv"))
    bad = [r for r in ROWS if r[0].endswith("_SHA256") and len(r[1]) != 64]
    bad += [r for r in ROWS if "NM_WRAP" in r[0] and not r[1].startswith("4/")]
    bad += [r for r in ROWS if "UNRESOLVED_RAW_FFT" in r[0] and r[1] != "0"]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
