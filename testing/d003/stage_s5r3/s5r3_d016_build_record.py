#!/usr/bin/env python3
# s5r3_d016_build_record.py -- record the F4 build used by the S5R3 D016 run into D016_BUILD_S5R3.tsv.
# The tree is $EV/trees/F4 (git archive of 05097a7). If make test has already built it, the artefacts
# are recorded as-is; otherwise the libs and the Python extension are built here (no injector).
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TREE = os.path.join(EV, "trees/F4")
LOG = os.path.join(EV, "logs/d016_build.log")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def run(cmd, shell=False, fh=None):
    txt = cmd if isinstance(cmd, str) else " ".join(cmd)
    if fh:
        fh.write("### " + txt + NL)
    p = subprocess.run(cmd, cwd=REPO, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if fh:
        fh.write(p.stdout)
        fh.write("### rc=" + str(p.returncode) + NL)
    return p.returncode


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    fh = open(LOG, "w", encoding="utf-8")
    fh.write("# D016 build record s5r3 " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + NL)
    rows = [("# D016_BUILD_S5R3.tsv -- F4 build used by the S5R3 D016 public-API run (no injector, U372)",
             "", ""),
            TAB.join(["check", "value", "detail"])]
    got = subprocess.check_output(["git", "rev-parse", "05097a7:S4"], text=True).strip()
    rows.append(("S4_TREE_05097a7", got, "expected 589e15eb11fcb04e031b524f25a443e7921946cf"))
    if got != "589e15eb11fcb04e031b524f25a443e7921946cf":
        print("HARD_STOP S4 tree mismatch")
        return 2
    if not os.path.isdir(os.path.join(TREE, "S4")):
        print("HARD_STOP tree missing; run s5r3_build_trees.py first")
        return 2
    lib = os.path.join(TREE, "build/libS4.a")
    lua = os.path.join(TREE, "build/S4")
    suffix = subprocess.check_output(["python3-config", "--extension-suffix"], text=True).strip()
    inc = subprocess.check_output(["python3-config", "--includes"], text=True).split()
    pyext = os.path.join(TREE, "S4" + suffix)
    if not (os.path.isfile(lib) and os.path.isfile(lua)):
        rc = run(["make", "-C", TREE, "-j4", "build/libS4.a", "build/S4", "PYTHON=python3"], fh=fh)
        rows.append(("MAKE_LIB_AND_LUA_RC", str(rc), "build/libS4.a + build/S4"))
        if rc != 0:
            return 1
    else:
        rows.append(("MAKE_LIB_AND_LUA_RC", "0", "artefacts already built by the shakedown make test run"))
    if not os.path.isfile(pyext):
        cmd = ["gcc", "-shared", "-fPIC"] + inc + ["-I", os.path.join(TREE, "S4"), "-I", os.path.join(TREE, "S4", "RNP"),
               "-I", os.path.join(TREE, "S4", "kiss_fft"), os.path.join(TREE, "S4", "main_python.c"), lib,
               "-o", pyext, "-llapack", "-lblas", "-lstdc++"]
        rc = run(cmd, fh=fh)
        rows.append(("LINK_PYEXT_RC", str(rc), "no --wrap, no injector"))
        if rc != 0:
            return 1
    else:
        rows.append(("LINK_PYEXT_RC", "0", "extension already present"))
    for name, path in (("LIB_S4_A", lib), ("PYEXT", pyext), ("LUA_FRONTEND", lua)):
        rows.append((name + "_PATH", os.path.relpath(path, REPO), ""))
        rows.append((name + "_SHA256", sha_f(path), ""))
    rows.append(("BUILD_LOG", os.path.relpath(LOG, REPO), "full output"))
    fh.close()
    out = os.path.join(EV, "D016_BUILD_S5R3.tsv")
    with open(out, "w", encoding="utf-8") as of:
        for r in rows:
            of.write(TAB.join(r) + NL)
    for r in rows:
        print(TAB.join(r))
    print("WROTE " + os.path.relpath(out, REPO))
    bad = [r for r in rows if r[0].endswith("_SHA256") and len(r[1]) != 64]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
