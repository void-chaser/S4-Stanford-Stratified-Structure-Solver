#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_r8m2e.py -- Build init-F3-san-AL driver for P05-S4 R8 M2e (U277).
import datetime, hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.path.join(REPO, EV_REL)
BUILD_DIR = os.path.join(EV, "build")
OUT_DRV = os.path.join(BUILD_DIR, "init-F3-san-AL")
BUILD_TSV = os.path.join(EV, "BUILD_R8_M2e.tsv")

LIB_F3_SAN = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "lib_F3_san", "libS4.a")
EXPECTED_LIB_SHA = "2775b9b2c279f51f1be0594c6ea9f635c96e3ba37e9d1638174fa380b45a6986"
TREE_SAN = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "trees_R3", "F3_san", "S4")
DRV_SRC = os.path.join(REPO, "testing", "d003", "stage_s4", "driver_r6b_state.cpp")
INJ_SRC = os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r8m2e_aligned.cpp")


def sha256_file(path):
    if not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    lib_sha = sha256_file(LIB_F3_SAN)
    if lib_sha != EXPECTED_LIB_SHA:
        sys.stderr.write("REFUSED: lib_F3_san sha256 %s != expected %s\n" % (lib_sha, EXPECTED_LIB_SHA))
        return 2

    drv_src_sha = sha256_file(DRV_SRC)
    inj_src_sha = sha256_file(INJ_SRC)
    src_comb = "drv:%s;inj:%s" % (drv_src_sha, inj_src_sha)

    cmd = [
        "g++", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-O0", "-g",
        "-Wall", "-Wno-unused-parameter",
        "-I" + TREE_SAN,
        "-I" + os.path.join(TREE_SAN, "fmm"),
        DRV_SRC,
        INJ_SRC,
        LIB_F3_SAN,
        "-llapack", "-lblas",
        "-Wl,--wrap=malloc",
        "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
        "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
        "-Wl,--wrap=_Z9S4_mallocm",
        "-Wl,--wrap=Pattern_GetContainmentTree",
        "-Wl,--wrap=malloc_aligned",
        "-o", OUT_DRV
    ]

    t_start = utc_now()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    cmd_str = " ".join(cmd).replace(REPO + os.sep, "")

    if r.returncode != 0:
        sys.stderr.write("DRIVER BUILD FAILED init-F3-san-AL rc=%d\n%s\n" % (r.returncode, r.stderr))
        with open(BUILD_TSV, "w", encoding="utf-8") as fh:
            fh.write("# BUILD_R8_M2e -- columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\textra\n")
            fh.write("init-F3-san-AL\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n" % (
                os.path.relpath(OUT_DRV, REPO), "BUILD_FAILED", src_comb, lib_sha, cmd_str, t_start, r.returncode, "error"
            ))
        return r.returncode

    drv_sha = sha256_file(OUT_DRV)
    warn_count = r.stderr.count("warning:")
    extra = "warnings=%d ok" % warn_count

    with open(BUILD_TSV, "w", encoding="utf-8") as fh:
        fh.write("# BUILD_R8_M2e -- columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\textra\n")
        fh.write("init-F3-san-AL\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n" % (
            os.path.relpath(OUT_DRV, REPO), drv_sha, src_comb, lib_sha, cmd_str, t_start, 0, extra
        ))

    print("build_r8m2e: SUCCESS -> %s (%s)" % (OUT_DRV, drv_sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
