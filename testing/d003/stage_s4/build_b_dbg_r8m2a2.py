#!/usr/bin/env python3
# build_b_dbg_r8m2a2.py -- P05-S4 R8 M2a2 CONT1 section 7: same-family B dbg driver for M2-10.
# The vl NG=1 control (RESULTS_R7_M1_pass1_run2.tsv, M1-G7-F2-vl-ng1-*) ran the rnv1 driver family (sha recorded there),
# i.e. driver_r6b_state.cpp + inject_r6d_rnv1.cpp (R6d-2 link recipe r6d_link_rnv1_B.sh, B tree).  r6bstate-B-dbg in the
# R8 BUILD table is driver_r6b_state.cpp + inject_r4_plan.cpp: a different family.  This script builds the same family
# on the R8 B -O0 -g library (build_R3/lib_B_dbg), verifies the library sha against the BUILD table, and records the build.
# Output: $EV/build/B-dbg/r6dnv1-B-dbg (binary), $EV/BUILD_B_DBG_R8_M2a2.tsv (supplement of BUILD_FINAL; BUILD_FINAL kept)
import hashlib
import os
import subprocess
import sys
import time

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
LIBDIR = os.path.join(EV, "build_R3", "lib_B_dbg")
SRC_TREE = os.path.join(EV, "trees_R3", "B", "S4")
BIN_DIR = os.path.join(EV, "build", "B-dbg")
BIN = os.path.join(BIN_DIR, "r6dnv1-B-dbg")
OUT = os.path.join(EV, "BUILD_B_DBG_R8_M2a2.tsv")
BUILD_FINAL = os.path.join(EV, "BUILD_FINAL_R8_M2a2.tsv")
LIBFLAGS = ["-llapack", "-lblas", "-Wl,--wrap=malloc", "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
            "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "-Wl,--wrap=_Z9S4_mallocm",
            "-Wl,--wrap=Pattern_GenerateFlowField"]
SOURCES = [os.path.join(REPO, "testing", "d003", "stage_s4", "driver_r6b_state.cpp"),
           os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r6d_rnv1.cpp")]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_record_sha(name):
    with open(BUILD_FINAL, encoding="utf-8") as fh:
        for l in fh:
            f = l.rstrip("\n").split("\t")
            if f and f[0] == name and len(f) >= 4:
                return f[3]
    return None


def main():
    if os.path.exists(OUT):
        print("build_b_dbg_r8m2a2: REFUSED exists (U17)")
        return 2
    lib = os.path.join(LIBDIR, "libS4.a")
    lib_sha = sha256_file(lib)
    lib_rec = build_record_sha("lib_B_dbg")
    lib_ok = (lib_sha == lib_rec)
    os.makedirs(BIN_DIR, exist_ok=True)
    srcs_sha = [sha256_file(s) for s in SOURCES]
    cmd = ["g++", "-O0", "-g", "-Wall", "-Wextra", "-Wno-unused-parameter",
           "-I", os.path.join(EV, "trees_R3", "B", "S4"), "-I", os.path.join(EV, "trees_R3", "B", "S4", "fmm")] + \
          SOURCES + ["-o", BIN, "-L", LIBDIR, "-lS4"] + LIBFLAGS
    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rc = 9
    stdout_path = os.path.join(BIN_DIR, "build_r6dnv1_B.stdout")
    if lib_ok:
        with open(stdout_path, "x", encoding="utf-8") as so:
            rc = subprocess.run(cmd, stdout=so, stderr=subprocess.STDOUT, cwd=REPO).returncode
    bin_sha = sha256_file(BIN) if (rc == 0 and os.path.exists(BIN)) else "-"
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# BUILD_B_DBG_R8_M2a2 -- supplement of BUILD_FINAL_R8_M2a2.tsv (CONT1 section 7); BUILD_FINAL is kept unchanged\n")
        fh.write("artifact\tpath\tlib_sha256\tlib_sha256_build_final\tlib_match\tsources_sha256\tbin_sha256\trc\tutc\tcommand\n")
        fh.write("\t".join([
            "r6dnv1-B-dbg", os.path.relpath(BIN, REPO), lib_sha, str(lib_rec), "YES" if lib_ok else "NO",
            ";".join(srcs_sha), bin_sha, str(rc), utc, " ".join(cmd)]) + "\n")
        fh.write("# LIB_MATCH=%s BUILD_RC=%d\n" % ("YES" if lib_ok else "NO", rc))
    print("build_b_dbg_r8m2a2: lib_match=%s rc=%d" % ("YES" if lib_ok else "NO", rc))
    return 0 if (lib_ok and rc == 0) else 3


if __name__ == "__main__":
    sys.exit(main())
