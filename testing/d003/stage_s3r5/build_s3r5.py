#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_s3r5.py -- Build F4 libraries and drivers for P05-S3R5 (U286).
import concurrent.futures, datetime, hashlib, os, subprocess, sys, tarfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
TREES = os.path.join(EV, "trees", "F4")
BLD = os.path.join(EV, "build")
BUILD_TSV = os.path.join(EV, "BUILD_S3R5.tsv")
WARN_DIFF_TXT = os.path.join(EV, "WARN_DIFF_F3_F4_S3R5.txt")

F4_REV = "05097a75faf33597d1090fd07dcdcedfaeab937d"
F4_TREE = "589e15eb11fcb04e031b524f25a443e7921946cf"

INIT_B_DBG = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "build", "init-B-dbg")
INIT_B_DBG_SHA = "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8"

SOURCES = [
    ("S4/S4.cpp", "S4", "cxx"), ("S4/rcwa.cpp", "rcwa", "cxx"), ("S4/fmm/fmm_common.cpp", "fmm_common", "cxx"),
    ("S4/fmm/fmm_FFT.cpp", "fmm_FFT", "cxx"), ("S4/fmm/fmm_kottke.cpp", "fmm_kottke", "cxx"),
    ("S4/fmm/fmm_closed.cpp", "fmm_closed", "cxx"), ("S4/fmm/fmm_PolBasisNV.cpp", "fmm_PolBasisNV", "cxx"),
    ("S4/fmm/fmm_PolBasisVL.cpp", "fmm_PolBasisVL", "cxx"), ("S4/fmm/fmm_PolBasisJones.cpp", "fmm_PolBasisJones", "cxx"),
    ("S4/fmm/fmm_experimental.cpp", "fmm_experimental", "cxx"), ("S4/fmm/fft_iface.cpp", "fft_iface", "cxx"),
    ("S4/pattern/pattern.c", "pattern", "cc"), ("S4/pattern/intersection.c", "intersection", "cc"),
    ("S4/pattern/predicates.c", "predicates", "cc"), ("S4/numalloc.c", "numalloc", "cc"), ("S4/gsel.c", "gsel", "cc"),
    ("S4/sort.c", "sort", "cc"), ("S4/kiss_fft/kiss_fft.c", "kiss_fft", "cc"),
    ("S4/kiss_fft/tools/kiss_fftnd.c", "kiss_fftnd", "cc"), ("S4/SpectrumSampler.c", "SpectrumSampler", "cc"),
    ("S4/cubature.c", "cubature", "cc"), ("S4/Interpolator.c", "Interpolator", "cc"), ("S4/convert.c", "convert", "cc"),
    ("S4/RNP/Eigensystems.cpp", "Eigensystems", "cxx"),
]

DBG_FLAGS = "-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
SAN_FLAGS = "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
PLAIN_FLAGS = "-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
CPP_BASE = ["-IS4", "-IS4/RNP", "-IS4/kiss_fft"]

WRAP_COMMON = ["-Wl,--wrap=malloc", "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
               "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "-Wl,--wrap=_Z9S4_mallocm"]
WRAP_INIT = WRAP_COMMON + ["-Wl,--wrap=Pattern_GetContainmentTree"]
WRAP_INIT_AL = WRAP_INIT + ["-Wl,--wrap=malloc_aligned"]

DRV_SRC = os.path.join(REPO, "testing", "d003", "stage_s4", "driver_r6b_state.cpp")
INJ_INIT_SRC = os.path.join(REPO, "testing", "d003", "stage_s3r4", "inject_s3r4_init.cpp")
INJ_ALIGNED_SRC = os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r8m2e_aligned.cpp")

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

def export_f4_tree():
    got_tree = subprocess.check_output(["git", "rev-parse", F4_REV + ":S4"], cwd=REPO, text=True).strip()
    if got_tree != F4_TREE:
        raise SystemExit("REFUSED: F4 rev %s S4 tree is %s, expected %s" % (F4_REV, got_tree, F4_TREE))
    os.makedirs(TREES, exist_ok=True)
    p = subprocess.Popen(["git", "archive", "--format=tar", F4_REV, "S4"], cwd=REPO, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=p.stdout, mode="r|") as tf:
        try:
            tf.extractall(TREES, filter="data")
        except TypeError:
            tf.extractall(TREES)
    if p.wait() != 0:
        raise SystemExit("git archive failed for %s" % F4_REV)
    print("Exported F4 tree to %s (tree %s)" % (TREES, got_tree))

def compile_one(job):
    root, src, stem, comp, flags, objdir = job
    obj = os.path.join(objdir, stem + ".o")
    cc = "g++" if comp == "cxx" else "gcc"
    cmd = [cc, "-c"] + flags.split() + CPP_BASE + [src, "-o", obj]
    t = utc_now()
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    warn = r.stderr.count("warning:")
    return (stem, obj, " ".join(cmd), r.returncode, t, warn, sha256_file(os.path.join(root, src)), sha256_file(obj), r.stderr)

def build_library(tag, flags):
    out = os.path.join(BLD, tag)
    objdir = os.path.join(out, "objs")
    os.makedirs(objdir, exist_ok=True)
    jobs = [(TREES, s, stem, comp, flags, objdir) for s, stem, comp in SOURCES]
    total_warn = 0
    all_stderr = []
    obj_files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(compile_one, j) for j in jobs]
        for f in concurrent.futures.as_completed(futures):
            stem, obj, cmd, rc, t, warn, s_sha, o_sha, err = f.result()
            if rc != 0:
                raise SystemExit("Compile failed for %s (%s):\n%s" % (stem, tag, err))
            total_warn += warn
            if err:
                all_stderr.append(err)
            obj_files.append(obj)
    lib_path = os.path.join(out, "libS4.a")
    ar_cmd = ["ar", "rcs", lib_path] + sorted(obj_files)
    ar_res = subprocess.run(ar_cmd, cwd=out, capture_output=True, text=True)
    if ar_res.returncode != 0:
        raise SystemExit("ar failed for %s:\n%s" % (tag, ar_res.stderr))
    lib_sha = sha256_file(lib_path)
    print("Built library %s -> %s (sha256=%s, warnings=%d)" % (tag, lib_path, lib_sha, total_warn))
    return lib_path, lib_sha, total_warn, "\n".join(all_stderr)

def link_driver(name, drv_src, inj_src, lib_path, xflags, wraps):
    out_drv = os.path.join(BLD, name)
    tree_s4 = os.path.join(TREES, "S4")
    tree_fmm = os.path.join(tree_s4, "fmm")
    cmd = ["g++"] + xflags.split() + [
        "-I" + tree_s4,
        "-I" + tree_fmm,
        drv_src,
        inj_src,
        lib_path,
        "-llapack", "-lblas"
    ] + wraps + ["-o", out_drv]
    t_start = utc_now()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("Driver link failed for %s:\n%s" % (name, r.stderr))
    drv_sha = sha256_file(out_drv)
    warn_count = r.stderr.count("warning:")
    cmd_str = " ".join(cmd).replace(REPO + os.sep, "")
    print("Built driver %s -> %s (sha256=%s, warnings=%d)" % (name, out_drv, drv_sha, warn_count))
    return out_drv, drv_sha, cmd_str, t_start, 0, warn_count, r.stderr

def main():
    os.makedirs(BLD, exist_ok=True)
    export_f4_tree()
    b_sha = sha256_file(INIT_B_DBG)
    if b_sha != INIT_B_DBG_SHA:
        raise SystemExit("init-B-dbg sha mismatch: got %s, expected %s" % (b_sha, INIT_B_DBG_SHA))
    print("init-B-dbg verified: %s (sha=%s)" % (INIT_B_DBG, b_sha))
    rows = []
    lib_dbg, lib_dbg_sha, warn_dbg, err_dbg = build_library("lib_F4_dbg", DBG_FLAGS)
    rows.append(("lib_F4_dbg", os.path.relpath(lib_dbg, REPO), lib_dbg_sha, "-", "-", "DBG_FLAGS=" + DBG_FLAGS, utc_now(), 0, warn_dbg, "ok"))
    lib_san, lib_san_sha, warn_san, err_san = build_library("lib_F4_san", SAN_FLAGS)
    rows.append(("lib_F4_san", os.path.relpath(lib_san, REPO), lib_san_sha, "-", "-", "SAN_FLAGS=" + SAN_FLAGS, utc_now(), 0, warn_san, "ok"))
    lib_plain, lib_plain_sha, warn_plain, err_plain = build_library("lib_F4_plain", PLAIN_FLAGS)
    rows.append(("lib_F4_plain", os.path.relpath(lib_plain, REPO), lib_plain_sha, "-", "-", "PLAIN_FLAGS=" + PLAIN_FLAGS, utc_now(), 0, warn_plain, "ok"))
    drv_dbg = "-O0 -g -Wall -Wno-unused-parameter"
    drv_san = "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter"
    comb_dbg = "drv:" + sha256_file(DRV_SRC) + ";inj:" + sha256_file(INJ_INIT_SRC)
    comb_al = "drv:" + sha256_file(DRV_SRC) + ";inj:" + sha256_file(INJ_ALIGNED_SRC)
    p1, s1, c1, t1, rc1, w1, _ = link_driver("init-F4-dbg", DRV_SRC, INJ_INIT_SRC, lib_dbg, drv_dbg, WRAP_INIT)
    rows.append(("init-F4-dbg", os.path.relpath(p1, REPO), s1, comb_dbg, lib_dbg_sha, c1, t1, rc1, w1, "ok"))
    p2, s2, c2, t2, rc2, w2, _ = link_driver("init-F4-san", DRV_SRC, INJ_INIT_SRC, lib_san, drv_san, WRAP_INIT)
    rows.append(("init-F4-san", os.path.relpath(p2, REPO), s2, comb_dbg, lib_san_sha, c2, t2, rc2, w2, "ok"))
    p3, s3, c3, t3, rc3, w3, _ = link_driver("init-F4-san-AL", DRV_SRC, INJ_ALIGNED_SRC, lib_san, drv_san, WRAP_INIT_AL)
    rows.append(("init-F4-san-AL", os.path.relpath(p3, REPO), s3, comb_al, lib_san_sha, c3, t3, rc3, w3, "ok"))
    rows.append(("init-B-dbg", os.path.relpath(INIT_B_DBG, REPO), b_sha, "-", "-", "reused (U286)", utc_now(), 0, 0, "reused"))
    with open(BUILD_TSV, "w", encoding="utf-8") as fh:
        fh.write("# BUILD_S3R5 -- columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\twarnings\textra\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print("Wrote %s" % BUILD_TSV)
    F3_WARN = {"dbg": 62, "san": 62, "plain": 71}
    F4_WARN = {"dbg": warn_dbg, "san": warn_san, "plain": warn_plain}
    diff_lines = [
        "# WARN_DIFF_F3_F4_S3R5 -- Library compile warning comparison between F3 and F4",
        "# Hard stop condition 4: F4 warnings must not exceed F3 warnings",
        "Mode\tF3_warnings\tF4_warnings\tDiff\tStatus",
    ]
    has_new_warn = False
    for mode in ["dbg", "san", "plain"]:
        f3_w = F3_WARN[mode]
        f4_w = F4_WARN[mode]
        diff = f4_w - f3_w
        st = "PASS" if diff <= 0 else "FAIL_NEW_WARNINGS"
        if diff > 0:
            has_new_warn = True
        diff_lines.append("%s\t%d\t%d\t%+d\t%s" % (mode, f3_w, f4_w, diff, st))
    diff_text = "\n".join(diff_lines) + "\n"
    with open(WARN_DIFF_TXT, "w", encoding="utf-8") as fh:
        fh.write(diff_text)
    print(diff_text)
    if has_new_warn:
        raise SystemExit("HARD STOP: New warnings detected in F4 build relative to F3!")
    print("build_s3r5: ALL BUILDS SUCCESSFUL, NO NEW WARNINGS.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
