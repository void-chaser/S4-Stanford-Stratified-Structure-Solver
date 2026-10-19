#!/usr/bin/env python3
# relr4_u_probe.py -- U401 ruling evidence (task brief section 1 U401):
#   1. reproduce the ORIGINAL build failure of U without the CFLAGS override: compile S4/main_lua.c with the
#      exact flags the successful build used, minus -Wno-error=int-conversion, into a scratch object under $EV.
#   2. verify that NO example calls GetAmplitudes in any of the three trees (U, B, F4): walk every .lua
#      under examples/ and search for the identifier.
# Writes only under $EV.
import os, sys, subprocess, hashlib, re

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TAB = chr(9)
NL = chr(10)
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4")}
FLAGS = ["-O3", "-Wall", "-march=native", "-fcx-limited-range", "-fno-exceptions", "-fPIC",
         "-IS4", "-IS4/RNP", "-IS4/kiss_fft", "-I/usr/include/lua5.2"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    probe = os.path.join(EV, "u_probe")
    os.makedirs(probe, exist_ok=True)
    rows = ["# U_PROBE_RELR4.tsv -- U401 ruling evidence: original failure without the CFLAGS override, and",
            "# verification that no example calls GetAmplitudes in any tree.",
            TAB.join(["item", "tree", "value", "detail"])]
    # ---- 1. compile main_lua.c WITHOUT -Wno-error=int-conversion
    tree = TREES["U"]
    outobj = os.path.join(probe, "main_lua_no_override.o")
    log = os.path.join(probe, "main_lua_no_override.log")
    cmd = ["gcc", "-c"] + FLAGS + ["S4/main_lua.c", "-o", outobj]
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# " + " ".join(cmd) + " (cwd=%s)" % os.path.relpath(tree, REPO) + NL)
        p = subprocess.run(cmd, cwd=tree, stdout=fh, stderr=subprocess.STDOUT)
    rc = p.returncode
    errs = [l.strip() for l in open(log, encoding="utf-8", errors="replace") if ": error:" in l]
    rows.append(TAB.join(["COMPILE_MAIN_LUA_WITHOUT_OVERRIDE", "U", "rc=%d" % rc,
                          errs[0][:220] if errs else "no error line"]))
    rows.append(TAB.join(["COMPILE_MAIN_LUA_WITHOUT_OVERRIDE_ERROR_LINES", "U", str(len(errs)),
                          "first error above"]))
    rows.append(TAB.join(["COMPILE_MAIN_LUA_WITHOUT_OVERRIDE_LOG", "U", os.path.relpath(log, REPO), sha_f(log)]))
    # ---- 2. no example calls GetAmplitudes, in any tree
    for name in ("U", "B", "F4"):
        t = TREES[name]
        hits = []
        lua_files = 0
        for root, dirs, files in os.walk(os.path.join(t, "examples")):
            dirs.sort()
            for f in sorted(files):
                if not f.endswith(".lua"):
                    continue
                lua_files += 1
                fp = os.path.join(root, f)
                txt = open(fp, encoding="utf-8", errors="replace").read()
                if "GetAmplitudes" in txt:
                    hits.append(os.path.relpath(fp, t))
        rows.append(TAB.join(["EXAMPLES_CALLING_GETAMPLITUDES", name, str(len(hits)), ";".join(hits) if hits else "none"]))
        rows.append(TAB.join(["EXAMPLES_LUA_COUNT", name, str(lua_files), "every .lua under examples/"]))
    # ---- 3. the only int-conversion warning the successful U build produced, quoted from its log
    ulog = os.path.join(EV, "build_logs", "U_lua_frontend.log")
    warn = [l.strip() for l in open(ulog, encoding="utf-8", errors="replace") if ": warning:" in l and "int-conversion" in l]
    rows.append(TAB.join(["U_BUILD_WARNING_INT_CONVERSION", "U", str(len(warn)), warn[0][:240] if warn else "none"]))
    rows.append(TAB.join(["U_BUILD_CFLAGS_OVERRIDE_EFFECT", "U",
                          "succeeds" if os.path.isfile(os.path.join(TREES["U"], "build", "S4")) else "missing",
                          "build/S4 present; see BUILD_RELR4.tsv"]))
    out = os.path.join(EV, "U_PROBE_RELR4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    for r in rows[3:]:
        print(r)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if rc != 0 and len(errs) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
