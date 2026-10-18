#!/usr/bin/env python3
# check_e2e_wrap_r9m3a.py -- regenerate the E2E build table with an nm check that does NOT demangle.
# usage: python3 -I -B testing/d003/stage_s4r9/check_e2e_wrap_r9m3a.py OUT.tsv
import os, sys, subprocess, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TREE = os.path.join(EV, "trees/E2E_F4")
TAB = chr(9)
NL = chr(10)
WANT = ["__wrap_malloc", "__wrap__Z13fft_plan_execP12tag_fft_plan",
        "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "__wrap__Z9S4_mallocm"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "E2E_BUILD_R9M3A_v2.tsv")
    arts = [("PYEXT", os.path.join(TREE, "S4.cpython-314-x86_64-linux-gnu.so")),
            ("LUA_FRONTEND", os.path.join(TREE, "build/S4_e2e")),
            ("INJECTOR_OBJ", os.path.join(TREE, "build/inject_r9m3a.o")),
            ("LIB_S4_A", os.path.join(TREE, "build/libS4.a"))]
    rows = []
    for name, p in arts:
        rows.append((name + "_PATH", os.path.relpath(p, REPO), ""))
        rows.append((name + "_SHA256", sha(p) if os.path.isfile(p) else "MISSING", ""))
    for name, p in arts[:2]:
        syms = subprocess.check_output(["nm", p], text=True, errors="replace") if os.path.isfile(p) else ""
        defined = []
        for line in syms.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1] in ("T", "t", "D", "d"):
                if parts[2] in WANT:
                    defined.append(parts[2])
        rows.append((name + "_NM_WRAP_DEFINED", str(len(defined)) + "/4", ",".join(defined)))
        dyn = subprocess.check_output(["nm", "-D", "--defined-only", p], text=True, errors="replace") if os.path.isfile(p) else ""
        rows.append((name + "_DYNAMIC_WRAP_DEFINED", str(sum(1 for w in WANT if dyn.find(w) >= 0)) + "/4", "dynamic symbol table"))
        und = subprocess.check_output(["nm", "-u", p], text=True, errors="replace") if os.path.isfile(p) else ""
        rows.append((name + "_UNRESOLVED_REAL_FFT", str(sum(1 for w in ("_Z13fft_plan_exec", "_Z15fft_plan_dft_2d") if und.find(w) >= 0)), "raw mangled symbols still unresolved (expected 0 when wrapped)"))
    rows.append(("BUILD_LOG", "checkpoints/p05/evidence/p05-s4r9/m3a/e2e_build/build.log", "full compiler/linker output"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# E2E_BUILD_R9M3A_v2.tsv -- v2 of the E2E build table (v1 used nm -C, which demangles and hid two wrappers)" + NL)
        fh.write(TAB.join(["check", "value", "detail"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    for r in rows:
        print(TAB.join(r))
    print("WROTE " + out)
    bad = [r for r in rows if r[0].endswith("SHA256") and r[1] == "MISSING"] + [r for r in rows if "NM_WRAP_DEFINED" in r[0] and not r[1].startswith("4/")]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
