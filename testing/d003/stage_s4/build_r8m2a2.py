#!/usr/bin/env python3
# build_r8m2a2.py -- P05-S4 R8 M2a2: Build apparatus libraries and drivers (Part F & §4.4).
# Output: checkpoints/p05/evidence/p05-s4r8/m2a2/BUILD_R8_M2a2.tsv
import datetime, hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
BUILD = os.path.join(EV, "build")
OUT_TSV = os.path.join(EV, "BUILD_R8_M2a2_R2.tsv")

F3_DBG_LIB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "build_r8", "F3-dbg", "build", "libS4.a")
F3_PLAIN_LIB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "build_r8", "F3-plain", "build", "libS4.a")
TREE_F3 = os.path.join(EV, "tree_F3", "S4")
TREE_B = os.path.join(EV, "tree_B", "S4")

S4_SRCS_CPP = [
    "S4.cpp", "rcwa.cpp", "fmm/fmm_common.cpp", "fmm/fmm_FFT.cpp", "fmm/fmm_kottke.cpp",
    "fmm/fmm_closed.cpp", "fmm/fmm_PolBasisNV.cpp", "fmm/fmm_PolBasisVL.cpp",
    "fmm/fmm_PolBasisJones.cpp", "fmm/fmm_experimental.cpp", "fmm/fft_iface.cpp",
    "RNP/Eigensystems.cpp"
]
S4_SRCS_C = [
    "pattern/pattern.c", "pattern/intersection.c", "pattern/predicates.c",
    "numalloc.c", "gsel.c", "sort.c", "kiss_fft/kiss_fft.c",
    "kiss_fft/tools/kiss_fftnd.c", "SpectrumSampler.c", "cubature.c",
    "Interpolator.c", "convert.c"
]

def sha256_file(p):
    if not os.path.isfile(p):
        return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def compile_lib(tag, src_root, out_dir, cxx_flags, c_flags, extra_cpp_flags=""):
    os.makedirs(out_dir, exist_ok=True)
    obj_dir = os.path.join(out_dir, "objs")
    os.makedirs(obj_dir, exist_ok=True)
    objs = []
    
    # Compile CPP sources
    for rel in S4_SRCS_CPP:
        src = os.path.join(src_root, rel)
        stem = rel.replace("/", "_").replace(".cpp", ".o")
        obj = os.path.join(obj_dir, stem)
        objs.append(obj)
        cmd = ["g++", "-c"] + cxx_flags.split() + ["-I" + src_root, "-I" + os.path.join(src_root, "RNP"), "-I" + os.path.join(src_root, "kiss_fft")]
        if extra_cpp_flags:
            cmd += extra_cpp_flags.split()
        cmd += [src, "-o", obj]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print("FAILED:", " ".join(cmd))
            print(res.stderr)
            return None, res.returncode, " ".join(cmd)
            
    # Compile C sources
    for rel in S4_SRCS_C:
        src = os.path.join(src_root, rel)
        stem = rel.replace("/", "_").replace(".c", ".o")
        obj = os.path.join(obj_dir, stem)
        objs.append(obj)
        cmd = ["gcc", "-c"] + c_flags.split() + ["-I" + src_root, "-I" + os.path.join(src_root, "RNP"), "-I" + os.path.join(src_root, "kiss_fft")]
        if extra_cpp_flags:
            cmd += extra_cpp_flags.split()
        cmd += [src, "-o", obj]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print("FAILED:", " ".join(cmd))
            print(res.stderr)
            return None, res.returncode, " ".join(cmd)
            
    lib_path = os.path.join(out_dir, "libS4.a")
    ar_cmd = ["ar", "crvs", lib_path] + objs
    ar_res = subprocess.run(ar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if ar_res.returncode != 0:
        return None, ar_res.returncode, " ".join(ar_cmd)
        
    return lib_path, 0, "compile_lib " + tag

def main():
    if os.path.exists(OUT_TSV):
        print("build_r8m2a2: REFUSED exists (U17): %s" % OUT_TSV)
        return 2

    records = []
    # columns: artifact	path	sha256	src_sha256	lib_sha256	compile_cmd	utc	rc

    # 1. Buf Seam library (F3 with apply_seam_r4_buf.py)
    print("--- Building F3 buf seam library ---")
    tree_f3_buf = os.path.join(EV, "tree_F3_buf")
    os.makedirs(tree_f3_buf, exist_ok=True)
    if not os.path.exists(os.path.join(tree_f3_buf, "S4")):
        cmd_arch = "git archive 8d8202a S4 | tar -x -C " + tree_f3_buf
        subprocess.run(cmd_arch, shell=True, cwd=REPO, check=True)
    patch_rep = os.path.join(EV, "SEAM_BUF_PATCH_DIFF_R8_M2a2.txt")
    if not os.path.exists(patch_rep):
        seam_patch = os.path.join(REPO, "testing", "d003", "seam", "apply_seam_r4_buf.py")
        cmd_patch = ["python3", "-I", "-B", seam_patch, "--root", tree_f3_buf, "--repo", REPO, "--report", patch_rep]
        subprocess.run(cmd_patch, cwd=REPO, check=True)
    
    buf_lib, rc_buf, cmd_buf = compile_lib(
        "F3-buf-seam",
        os.path.join(tree_f3_buf, "S4"),
        os.path.join(BUILD, "seam_buf", "build"),
        "-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC",
        "-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC",
        "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF"
    )
    records.append(("F3-buf-seam-lib", buf_lib, sha256_file(buf_lib), sha256_file(patch_rep), "-", cmd_buf, utc_now(), rc_buf))

    # 2. Sanitizer library (F3 -fsanitize=address,undefined -O0 -g)
    print("--- Building F3 sanitizer library ---")
    tree_f3_san = os.path.join(EV, "tree_F3_san")
    os.makedirs(tree_f3_san, exist_ok=True)
    if not os.path.exists(os.path.join(tree_f3_san, "S4")):
        cmd_arch = "git archive 8d8202a S4 | tar -x -C " + tree_f3_san
        subprocess.run(cmd_arch, shell=True, cwd=REPO, check=True)
        
    san_lib, rc_san, cmd_san = compile_lib(
        "F3-san",
        os.path.join(tree_f3_san, "S4"),
        os.path.join(BUILD, "san", "F3-san", "build"),
        "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC",
        "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    )
    records.append(("F3-san-lib", san_lib, sha256_file(san_lib), "-", "-", cmd_san, utc_now(), rc_san))

    # 3. B dbg library (B -O0 -g)
    print("--- Building B dbg library ---")
    b_lib, rc_b, cmd_b = compile_lib(
        "B-dbg",
        TREE_B,
        os.path.join(BUILD, "B-dbg", "build"),
        "-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC",
        "-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    )
    records.append(("B-dbg-lib", b_lib, sha256_file(b_lib), "-", "-", cmd_b, utc_now(), rc_b))

    # 4. Drivers
    print("--- Building drivers ---")
    WRAP_COMMON = "-Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
    WRAP_INIT = WRAP_COMMON + " -Wl,--wrap=Pattern_GetContainmentTree"
    WRAP_POLY = WRAP_COMMON + " -Wl,--wrap=Pattern_DiscretizeCell"

    DRIVERS = [
        # (name, drv_src, inj_src, lib_path, extra_flags, wrap_flags, tree_inc)
        ("init-F3-dbg",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s3r4/inject_s3r4_init.cpp",
         F3_DBG_LIB, "-O0 -g", WRAP_INIT, TREE_F3),
        ("polyinj-F3-dbg",
         "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
         "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp",
         F3_DBG_LIB, "-O0 -g", WRAP_POLY, TREE_F3),
        ("dual-F3-dbg",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s4/inject_r8m2a2_dual.cpp",
         F3_DBG_LIB, "-O0 -g", WRAP_COMMON, TREE_F3),
        ("layers-F3-dbg",
         "testing/d003/stage_s4/driver_r8m2a2_layers.cpp",
         "testing/d003/stage_s4/inject_r4_plan.cpp",
         F3_DBG_LIB, "-O0 -g", WRAP_COMMON, TREE_F3),
        ("layers-dual-F3-dbg",
         "testing/d003/stage_s4/driver_r8m2a2_layers.cpp",
         "testing/d003/stage_s4/inject_r8m2a2_dual.cpp",
         F3_DBG_LIB, "-O0 -g", WRAP_COMMON, TREE_F3),
        ("nan-F3",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s4/inject_r8m2a2_nan.cpp",
         buf_lib, "-O1", WRAP_COMMON, os.path.join(tree_f3_buf, "S4")),
        ("r6bstate-F3-san",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s4/inject_r4_plan.cpp",
         san_lib, "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g", WRAP_COMMON, TREE_F3),
        ("init-F3-san",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s3r4/inject_s3r4_init.cpp",
         san_lib, "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g", WRAP_INIT, TREE_F3),
        ("polyinj-F3-san",
         "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
         "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp",
         san_lib, "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g", WRAP_POLY, TREE_F3),
        ("r6bstate-B-dbg",
         "testing/d003/stage_s4/driver_r6b_state.cpp",
         "testing/d003/stage_s4/inject_r4_plan.cpp",
         b_lib, "-O0 -g", WRAP_COMMON, TREE_B),
    ]

    for dname, dsrc_rel, isrc_rel, lpath, xflags, wflags, tree_inc in DRIVERS:
        dsrc = os.path.join(REPO, dsrc_rel)
        isrc = os.path.join(REPO, isrc_rel)
        if "san" in dname:
            out_exe = os.path.join(BUILD, "san", dname)
        elif "B-dbg" in lpath:
            out_exe = os.path.join(BUILD, "B-dbg", dname)
        else:
            out_exe = os.path.join(BUILD, dname)
        os.makedirs(os.path.dirname(out_exe), exist_ok=True)
        
        cmd = ["g++"] + xflags.split() + ["-Wall", "-Wno-unused-parameter",
               "-I" + tree_inc, "-I" + os.path.join(tree_inc, "fmm"),
               dsrc, isrc, lpath, "-llapack", "-lblas"] + wflags.split() + ["-o", out_exe]
        cmd_str = " ".join(cmd)
        utc_t = utc_now()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print("DRIVER BUILD FAILED:", dname)
            print(res.stderr)
            records.append((dname, out_exe, "BUILD_FAILED", sha256_file(dsrc), sha256_file(lpath), cmd_str, utc_t, res.returncode))
        else:
            print("DRIVER BUILD OK:", dname, "->", out_exe)
            records.append((dname, out_exe, sha256_file(out_exe), sha256_file(dsrc), sha256_file(lpath), cmd_str, utc_t, 0))

    # Write BUILD_R8_M2a2.tsv
    with open(OUT_TSV, "x", encoding="utf-8") as fh:
        fh.write("# BUILD_R8_M2a2.tsv -- P05-S4 R8 M2a2 section 4.4 Build Record\n")
        fh.write("# columns: artifact\tpath\tsha256\tsrc_sha256\tlib_sha256\tcompile_cmd\tutc\trc\n")
        for r in records:
            fh.write("\t".join(str(x) for x in r) + "\n")
            
    print("wrote %s with %d records" % (OUT_TSV, len(records)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
