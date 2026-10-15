#!/usr/bin/env python3
# build_r8m2a2_R3.py -- P05-S4 R8 M2a2: version R3 of the apparatus build (Part F, brief 4.4).  Nothing is rebuilt in place:
#   * all trees are exported fresh into $EV/trees_R3/ (git archive via a pipe into tarfile; no shell), seam patches are
#     applied to those fresh exports only;
#   * all objects, libraries and drivers go to $EV/build_R3/ (the R1/R2 build directory $EV/build is not touched);
#   * every object compile command, source sha256, object sha256, rc and UTC is recorded per object.
# The registered F3 dbg library (evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a) is REUSED, not rebuilt; its sha256 is checked.
# Outputs:  BUILD_OBJECTS_R8_M2a2_R3.tsv  (one row per object compile and per ar)
#           BUILD_R8_M2a2_R3.tsv          (one row per library / driver artifact)
#           TREES_R8_M2a2_R3.tsv          (export revisions, S4 tree hashes, seam apply reports)
# No S4 driver is run.  Nothing here executes a built driver.
import concurrent.futures, datetime, hashlib, os, subprocess, sys, tarfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
TREES = os.path.join(EV, "trees_R3")
BLD = os.path.join(EV, "build_R3")
OUT_OBJ = os.path.join(EV, "BUILD_OBJECTS_R8_M2a2_R3.tsv")
OUT_ART = os.path.join(EV, "BUILD_R8_M2a2_R3.tsv")
OUT_TREES = os.path.join(EV, "TREES_R8_M2a2_R3.tsv")
ST4 = os.path.join(REPO, "testing", "d003", "stage_s4")
SEAMDIR = os.path.join(REPO, "testing", "d003", "seam")

F3_REV, F3_TREE = "8d8202a", "6cff923a02baf19e01966b2339755cbf3a5deeef"
B_REV, B_TREE = "37a82e8", "1d738e64f9864a475fdb3de34cd3601605df2c64"
F3_DBG_LIB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "build_r8", "F3-dbg", "build", "libS4.a")
F3_DBG_LIB_SHA = "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a"

# Makefile.common S4_LIBOBJS order (then Eigensystems, because LAPACK_LIB is not defined): (source, object stem, compiler)
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
SEAMF_MACROS = ["-DS4_TEST_LINEARSOLVE_SEAM", "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2", "-DS4_TEST_ALLOC_SEAM", "-DS4_TEST_KOTTKE_SEAM"]
FMMRET_MACROS = ["-DS4_TEST_FMMRET_SEAM"]
BUF_MACROS = ["-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF"]

WRAP_COMMON = ["-Wl,--wrap=malloc", "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
               "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "-Wl,--wrap=_Z9S4_mallocm"]
WRAP_INIT = WRAP_COMMON + ["-Wl,--wrap=Pattern_GetContainmentTree"]
WRAP_POLY = WRAP_COMMON + ["-Wl,--wrap=Pattern_DiscretizeCell"]


def sha_file(p):
    if not os.path.isfile(p):
        return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_out(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True).stdout.strip()


def export_tree(rev, want_tree, dest, rows):
    got = git_out("rev-parse", rev + ":S4")
    if got != want_tree:
        raise SystemExit("REFUSED: %s:S4 is %s, expected %s" % (rev, got, want_tree))
    os.makedirs(dest)
    p = subprocess.Popen(["git", "archive", "--format=tar", rev, "S4"], cwd=REPO, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=p.stdout, mode="r|") as tf:
        try:
            tf.extractall(dest, filter="data")
        except TypeError:
            tf.extractall(dest)
    if p.wait() != 0:
        raise SystemExit("git archive failed for %s" % rev)
    rows.append((os.path.relpath(dest, REPO), "export", rev, got, utc()))


def run_py(args, rows, label):
    r = subprocess.run(["python3", "-I", "-B"] + args, cwd=REPO, capture_output=True, text=True)
    rows.append((label, "seam_apply", " ".join(os.path.relpath(a, REPO) if os.path.isabs(a) else a for a in args), "rc=%d" % r.returncode, utc()))
    if r.returncode != 0:
        raise SystemExit("seam step failed: %s\n%s%s" % (label, r.stdout, r.stderr))


def compile_one(job):
    root, src, stem, comp, flags, macros, objdir = job
    obj = os.path.join(objdir, stem + ".o")
    cc = "g++" if comp == "cxx" else "gcc"
    cmd = [cc, "-c"] + flags.split() + macros + CPP_BASE + [src, "-o", obj]
    t = utc()
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    warn = r.stderr.count("warning:")
    return (obj, " ".join(cmd), r.returncode, t, warn, sha_file(os.path.join(root, src)), sha_file(obj), r.stderr if r.returncode else "")


def build_lib(tag, root, flags, macros, objrows):
    out = os.path.join(BLD, tag)
    objdir = os.path.join(out, "objs")
    os.makedirs(objdir)
    jobs = [(root, s, stem, comp, flags, macros, objdir) for s, stem, comp in SOURCES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(compile_one, jobs))
    ok = True
    warn = 0
    for r in res:
        objrows.append((tag, os.path.relpath(r[0], REPO), r[5], r[6], r[1], r[3], r[2], r[4]))
        warn += r[4]
        if r[2] != 0:
            ok = False
            sys.stderr.write("COMPILE FAILED %s\n%s\n" % (r[1], r[7]))
    lib = os.path.join(out, "libS4.a")
    if not ok:
        return None, "compile failed", warn
    ar = ["ar", "crvs", lib] + [os.path.join(objdir, stem + ".o") for _, stem, _ in SOURCES]
    t = utc()
    r = subprocess.run(ar, cwd=out, capture_output=True, text=True)
    objrows.append((tag, os.path.relpath(lib, REPO), "-", sha_file(lib), " ".join(os.path.relpath(a, REPO) if os.path.isabs(a) else a for a in ar), t, r.returncode, 0))
    if r.returncode != 0:
        return None, "ar failed", warn
    return lib, "ok", warn


def link_driver(name, drv, inj, lib, tree_root, xflags, wraps, out_dir, art):
    exe = os.path.join(out_dir, name)
    drv_path = os.path.join(REPO, drv) if "/" in drv else os.path.join(ST4, drv)
    cmd = ["g++"] + xflags.split() + ["-Wall", "-Wno-unused-parameter", "-I" + os.path.join(tree_root, "S4"),
           "-I" + os.path.join(tree_root, "S4", "fmm"), drv_path,
           os.path.join(REPO, inj), lib, "-llapack", "-lblas"] + wraps + ["-o", exe]
    t = utc()
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    srcsha = "drv:%s;inj:%s" % (sha_file(drv_path), sha_file(os.path.join(REPO, inj)))
    if r.returncode != 0:
        sys.stderr.write("DRIVER LINK FAILED %s\n%s\n" % (name, r.stderr))
        art.append((name, os.path.relpath(exe, REPO), "BUILD_FAILED", srcsha, sha_file(lib), " ".join(cmd).replace(REPO + os.sep, ""), t, r.returncode, ""))
    else:
        art.append((name, os.path.relpath(exe, REPO), sha_file(exe), srcsha, sha_file(lib), " ".join(cmd).replace(REPO + os.sep, ""), t, 0, "warnings=%d" % r.stderr.count("warning:")))


def main():
    for p in (OUT_OBJ, OUT_ART, OUT_TREES, TREES, BLD):
        if os.path.exists(p):
            print("build_r8m2a2_R3: REFUSED exists (U17): %s" % p)
            return 2
    if sha_file(F3_DBG_LIB) != F3_DBG_LIB_SHA:
        print("build_r8m2a2_R3: REFUSED registered F3 dbg library sha256 differs")
        return 2
    os.makedirs(TREES)
    os.makedirs(BLD)
    tr = []
    objrows, art = [], []

    # ---- fresh exports (every seam patch is applied to its own fresh export, once) ----
    for tag, rev, tree in (("F3", F3_REV, F3_TREE), ("F3_buf", F3_REV, F3_TREE), ("F3_san", F3_REV, F3_TREE),
                           ("F3_seamF_san", F3_REV, F3_TREE), ("F3_fmmret_san", F3_REV, F3_TREE), ("B", B_REV, B_TREE)):
        export_tree(rev, tree, os.path.join(TREES, tag), tr)
    rep = lambda n: os.path.join(EV, n)
    run_py([os.path.join(SEAMDIR, "apply_seam_r4_buf.py"), "--root", os.path.join(TREES, "F3_buf"), "--repo", REPO,
            "--report", rep("SEAM_BUF_PATCH_DIFF_R8_M2a2_R3.txt")], tr, "F3_buf apply_seam_r4_buf")
    run_py([os.path.join(SEAMDIR, "apply_seam_r2.py"), "--root", os.path.join(TREES, "F3_seamF_san"), "--repo", REPO,
            "--families", "A,C,D", "--report", rep("SEAM_ACD_PATCH_DIFF_R8_M2a2_R3.txt")], tr, "F3_seamF_san apply_seam_r2 A,C,D")
    run_py([os.path.join(SEAMDIR, "apply_seam_b2.py"), "--root", os.path.join(TREES, "F3_seamF_san"), "--repo", REPO,
            "--report", rep("SEAM_B2_PATCH_DIFF_R8_M2a2_R3.txt")], tr, "F3_seamF_san apply_seam_b2")
    run_py([os.path.join(SEAMDIR, "apply_seam_r5_fmmret.py"), "--tree", "A", "--root", os.path.join(TREES, "F3_fmmret_san"), "--repo", REPO,
            "--report", rep("SEAM_FMMRET_PATCH_DIFF_R8_M2a2_R3.txt")], tr, "F3_fmmret_san apply_seam_r5_fmmret A")
    with open(OUT_TREES, "x", encoding="utf-8") as fh:
        fh.write("# TREES_R8_M2a2_R3 -- columns: target\tkind\trev_or_script\ttree_or_result\tutc\n")
        for r in tr:
            fh.write("\t".join(r) + "\n")

    # ---- libraries ----
    libs = {}
    for tag, root_tag, flags, macros in (
            ("lib_F3_bufseam", "F3_buf", PLAIN_FLAGS, BUF_MACROS),
            ("lib_F3_san", "F3_san", SAN_FLAGS, []),
            ("lib_F3_seamF_san", "F3_seamF_san", SAN_FLAGS, SEAMF_MACROS),
            ("lib_F3_fmmret_san", "F3_fmmret_san", SAN_FLAGS, FMMRET_MACROS),
            ("lib_B_dbg", "B", DBG_FLAGS, [])):
        lib, st, warn = build_lib(tag, os.path.join(TREES, root_tag), flags, macros, objrows)
        libs[tag] = lib
        art.append((tag, os.path.relpath(lib, REPO) if lib else "-", sha_file(lib) if lib else "BUILD_FAILED",
                    "tree=%s" % root_tag, "-", "see BUILD_OBJECTS_R8_M2a2_R3.tsv; flags=%s %s" % (flags, " ".join(macros)), utc(),
                    0 if lib else 1, "warnings=%d %s" % (warn, st)))
    art.append(("lib_F3_dbg_REUSED", os.path.relpath(F3_DBG_LIB, REPO), sha_file(F3_DBG_LIB), "-", "-",
                "not rebuilt; BUILD_R8.tsv row F3 dbg; REUSE_CHECK_R8_M2a2_R2.tsv SAME", utc(), 0, "reused"))

    with open(OUT_OBJ, "x", encoding="utf-8") as fh:
        fh.write("# BUILD_OBJECTS_R8_M2a2_R3 -- columns: library\tpath\tsrc_sha256\tobj_or_lib_sha256\tcommand\tutc\trc\twarnings\n")
        for r in objrows:
            fh.write("\t".join(str(x) for x in r) + "\n")

    # ---- drivers ----
    drv_dir = os.path.join(BLD, "drivers")
    os.makedirs(drv_dir)
    T = lambda n: os.path.join(TREES, n)
    dbg, san = "-O0 -g", "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g"
    jobs = [
        ("init-F3-dbg", "driver_r6b_state.cpp", "testing/d003/stage_s3r4/inject_s3r4_init.cpp", F3_DBG_LIB, T("F3"), dbg, WRAP_INIT),
        ("polyinj-F3-dbg", "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp", "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp", F3_DBG_LIB, T("F3"), dbg, WRAP_POLY),
        ("dual-F3-dbg", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp", F3_DBG_LIB, T("F3"), dbg, WRAP_COMMON),
        ("layers-F3-dbg", "driver_r8m2a2_layers_R2.cpp", "testing/d003/stage_s4/inject_r4_plan.cpp", F3_DBG_LIB, T("F3"), dbg, WRAP_COMMON),
        ("layers-dual-F3-dbg", "driver_r8m2a2_layers_R2.cpp", "testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp", F3_DBG_LIB, T("F3"), dbg, WRAP_COMMON),
        ("r6bstate-B-dbg", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r4_plan.cpp", libs["lib_B_dbg"], T("B"), dbg, WRAP_COMMON),
        ("nan-F3", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r8m2a2_nan_R2.cpp", libs["lib_F3_bufseam"], T("F3_buf"), "-O1", WRAP_COMMON),
        ("r6bstate-F3-san", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r4_plan.cpp", libs["lib_F3_san"], T("F3_san"), san, WRAP_COMMON),
        ("init-F3-san", "driver_r6b_state.cpp", "testing/d003/stage_s3r4/inject_s3r4_init.cpp", libs["lib_F3_san"], T("F3_san"), san, WRAP_INIT),
        ("polyinj-F3-san", "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp", "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp", libs["lib_F3_san"], T("F3_san"), san, WRAP_POLY),
        ("seamF-F3-san", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r4_plan.cpp", libs["lib_F3_seamF_san"], T("F3_seamF_san"), san, WRAP_COMMON),
        ("fmmret-F3-san", "driver_r6b_state.cpp", "testing/d003/stage_s4/inject_r4_plan.cpp", libs["lib_F3_fmmret_san"], T("F3_fmmret_san"), san, WRAP_COMMON),
    ]
    for name, drv, inj, lib, tree_root, xflags, wraps in jobs:
        if lib is None:
            art.append((name, "-", "BUILD_FAILED", "-", "-", "library missing", utc(), 1, ""))
            continue
        link_driver(name, drv, inj, lib, tree_root, xflags, wraps, drv_dir, art)

    with open(OUT_ART, "x", encoding="utf-8") as fh:
        fh.write("# BUILD_R8_M2a2_R3 -- columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\textra\n")
        for r in art:
            fh.write("\t".join(str(x) for x in r) + "\n")
    bad = [r[0] for r in art if r[7] != 0]
    print("build_r8m2a2_R3: artifacts=%d failed=%d %s" % (len(art), len(bad), ",".join(bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
