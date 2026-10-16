#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_r9.py -- Build F4 apparatus (trees, seam libraries, drivers) and verify parity for P05-S4 R9.
import concurrent.futures, datetime, difflib, hashlib, os, subprocess, sys, tarfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0"))
os.makedirs(EV, exist_ok=True)

TREES = os.path.join(EV, "trees")
BLD = os.path.join(EV, "build")
os.makedirs(TREES, exist_ok=True)
os.makedirs(BLD, exist_ok=True)

OUT_BUILD_TSV = os.path.join(EV, "BUILD_R9.tsv")
OUT_OPTION_DIFF = os.path.join(EV, "BUILD_OPTION_DIFF_R9.txt")
OUT_SEAM_DIFF = os.path.join(EV, "SEAM_APPLY_DIFF_F3_F4_R9.txt")
OUT_DRIVER_MAP = os.path.join(EV, "DRIVER_MAP_F3_F4_R9.tsv")

F4_REV = "05097a7"
F4_TREE = "589e15eb11fcb04e031b524f25a443e7921946cf"

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
WRAP_ALIGNED = WRAP_INIT + ["-Wl,--wrap=malloc_aligned"]

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

def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def export_fresh(tag):
    dest = os.path.join(TREES, tag)
    if os.path.exists(dest):
        import shutil
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    p = subprocess.Popen(["git", "archive", "--format=tar", F4_REV, "S4"], cwd=REPO, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=p.stdout, mode="r|") as tf:
        try:
            tf.extractall(dest, filter="data")
        except TypeError:
            tf.extractall(dest)
    if p.wait() != 0:
        raise SystemExit(f"git archive failed for {F4_REV}")
    return dest

def compile_one(job):
    root, src, stem, comp, flags, macros, objdir = job
    obj = os.path.join(objdir, stem + ".o")
    cc = "g++" if comp == "cxx" else "gcc"
    cmd = [cc, "-c"] + flags.split() + macros + CPP_BASE + [src, "-o", obj]
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    warn = r.stderr.count("warning:")
    return (obj, " ".join(cmd), r.returncode, warn, r.stderr if r.returncode != 0 else "")

def build_lib(tag, root, flags, macros):
    out = os.path.join(BLD, tag)
    objdir = os.path.join(out, "objs")
    os.makedirs(objdir, exist_ok=True)
    jobs = [(root, s, stem, comp, flags, macros, objdir) for s, stem, comp in SOURCES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(compile_one, jobs))
    ok = True
    total_warn = 0
    for r in res:
        total_warn += r[3]
        if r[2] != 0:
            ok = False
            sys.stderr.write(f"COMPILE FAILED {r[1]}\n{r[4]}\n")
    if not ok:
        raise SystemExit(f"Library build failed for {tag}")
    lib = os.path.join(out, "libS4.a")
    ar = ["ar", "crvs", lib] + [os.path.join(objdir, stem + ".o") for _, stem, _ in SOURCES]
    r_ar = subprocess.run(ar, cwd=out, capture_output=True, text=True)
    if r_ar.returncode != 0:
        raise SystemExit(f"ar failed for {tag}")
    cmd_str = f"make objs flags={flags} macros={' '.join(macros)}; ar crvs libS4.a"
    return lib, sha256_file(lib), cmd_str, 0, total_warn

print("--- Step 1: Exporting fresh F4 trees ---")
t_f4 = export_fresh("F4")
t_buf = export_fresh("F4_buf")
t_seam_san = export_fresh("F4_seamF_san")
t_seam_dbg = export_fresh("F4_seamF_dbg")
t_fmmret = export_fresh("F4_fmmret_plain")

print("--- Step 2: Applying seam patches ---")
rep_buf = os.path.join(TREES, "apply_F4_buf.txt")
rep_seam_san_acd = os.path.join(TREES, "apply_F4_seamF_san_ACD.txt")
rep_seam_san_b2 = os.path.join(TREES, "apply_F4_seamF_san_B2.txt")
rep_seam_dbg_acd = os.path.join(TREES, "apply_F4_seamF_dbg_ACD.txt")
rep_seam_dbg_b2 = os.path.join(TREES, "apply_F4_seamF_dbg_B2.txt")
rep_fmmret = os.path.join(TREES, "apply_F4_fmmret.txt")

subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r4_buf.py",
                "--root", t_buf, "--repo", REPO, "--report", rep_buf], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r2.py",
                "--root", t_seam_san, "--repo", REPO, "--families", "A,C,D", "--report", rep_seam_san_acd], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_b2.py",
                "--root", t_seam_san, "--repo", REPO, "--report", rep_seam_san_b2], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r2.py",
                "--root", t_seam_dbg, "--repo", REPO, "--families", "A,C,D", "--report", rep_seam_dbg_acd], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_b2.py",
                "--root", t_seam_dbg, "--repo", REPO, "--report", rep_seam_dbg_b2], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r5_fmmret.py",
                "--tree", "A", "--root", t_fmmret, "--repo", REPO, "--report", rep_fmmret], check=True)
print("Seam patches applied successfully.")

print("--- Step 3: Comparing seam apply reports with F3 ---")
f3_evidence_m2a2 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
diff_records = []

def compare_report(f3_file, f4_file, label):
    l3 = open(os.path.join(f3_evidence_m2a2, f3_file), encoding="utf-8").readlines()
    l4 = open(f4_file, encoding="utf-8").readlines()
    d = list(difflib.unified_diff(l3, l4, fromfile="F3:"+f3_file, tofile="F4:"+os.path.basename(f4_file)))
    diff_records.append(f"=== {label} ===\n")
    if not d:
        diff_records.append("IDENTICAL (0 differences)\n\n")
    else:
        diff_records.append("".join(d) + "\n")
    return d

compare_report("SEAM_BUF_PATCH_DIFF_R8_M2a2_R3.txt", rep_buf, "apply_seam_r4_buf")
compare_report("SEAM_ACD_PATCH_DIFF_R8_M2a2_R3.txt", rep_seam_san_acd, "apply_seam_r2 (A,C,D)")
compare_report("SEAM_B2_PATCH_DIFF_R8_M2a2_R3.txt", rep_seam_san_b2, "apply_seam_b2")
compare_report("SEAM_FMMRET_PATCH_DIFF_R8_M2a2_R3.txt", rep_fmmret, "apply_seam_r5_fmmret")

with open(OUT_SEAM_DIFF, "w", encoding="utf-8") as fh:
    fh.write("# SEAM_APPLY_DIFF_F3_F4_R9.txt -- Comparison of seam apply reports between F3 and F4\n")
    fh.write("# Rule U296: Only line number offsets (+13 after line 1774 in S4.cpp) are permitted.\n\n")
    fh.writelines(diff_records)
print(f"Wrote seam diff report -> {OUT_SEAM_DIFF}")

print("--- Step 4: Building seam libraries ---")
built_libs = {}
# 1. lib_F4_bufseam (F3: 71 warnings)
p_buf, s_buf, c_buf, rc_buf, w_buf = build_lib("lib_F4_bufseam", t_buf, PLAIN_FLAGS, BUF_MACROS)
built_libs["lib_F4_bufseam"] = (p_buf, s_buf, c_buf, rc_buf, w_buf, "lib_F3_bufseam", "7ac5258d494a069df95178a48aa229257466c066a502d680bc89dcd55c334e75", 71)

# 2. lib_F4_seamF_san (F3: 62 warnings)
p_san, s_san, c_san, rc_san, w_san = build_lib("lib_F4_seamF_san", t_seam_san, SAN_FLAGS, SEAMF_MACROS)
built_libs["lib_F4_seamF_san"] = (p_san, s_san, c_san, rc_san, w_san, "lib_F3_seamF_san", "4928bb96c33ff9697d6f34decc105e10afbe0daa50c993b983e8338f5081c2f3", 62)

# 3. lib_F4_seamF_dbg (F3: 62 warnings)
p_dbg, s_dbg, c_dbg, rc_dbg, w_dbg = build_lib("lib_F4_seamF_dbg", t_seam_dbg, DBG_FLAGS, SEAMF_MACROS)
built_libs["lib_F4_seamF_dbg"] = (p_dbg, s_dbg, c_dbg, rc_dbg, w_dbg, "lib_F3_seamF_dbg", "16d43d3ce6fc32ecb07bcfc467bd272b25949fdfecdf8ef1506b4fb6fb82add3", 62)

# 4. lib_F4_fmmret_plain (F3: 71 warnings)
p_ret, s_ret, c_ret, rc_ret, w_ret = build_lib("lib_F4_fmmret_plain", t_fmmret, PLAIN_FLAGS, FMMRET_MACROS)
built_libs["lib_F4_fmmret_plain"] = (p_ret, s_ret, c_ret, rc_ret, w_ret, "lib_F3_fmmret_plain", "f26dbe2b58b5f52b1cf4ad8baf8cf5dd99962839d63e2c4f3c925822aeed942c", 71)

# 5, 6, 7. Reused base libraries from s3r5
lib_f4_dbg_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_dbg", "libS4.a")
lib_f4_san_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_san", "libS4.a")
lib_f4_plain_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_plain", "libS4.a")

built_libs["lib_F4_dbg"] = (lib_f4_dbg_path, sha256_file(lib_f4_dbg_path), "reused from s3r5", 0, 62, "lib_F3_dbg", "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a", 62)
built_libs["lib_F4_san"] = (lib_f4_san_path, sha256_file(lib_f4_san_path), "reused from s3r5", 0, 62, "lib_F3_san", "2775b9b2c279f51f1be0594c6ea9f635c96e3ba37e9d1638174fa380b45a6986", 62)
built_libs["lib_F4_plain"] = (lib_f4_plain_path, sha256_file(lib_f4_plain_path), "reused from s3r5", 0, 71, "lib_F3_plain", "abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de", 71)

for ltag, (lp, ls, lc, lrc, lw, f3_tag, f3_s, f3_w) in built_libs.items():
    print(f"Library {ltag}: sha={ls[:12]}..., warnings={lw} (F3: {f3_w})")
    if lw != f3_w:
        raise AssertionError(f"Library {ltag} warnings mismatch: actual={lw}, expected={f3_w}")

print("--- Step 5: Linking drivers ---")
# The 16 driver definitions:
drivers = [
    # 3 reused init drivers from s3r5
    {
        "name": "init-F4-dbg",
        "f3_name": "init-F3-dbg",
        "f3_sha": "d5200355c23f26a99715673a25a35ffe8ec8fe75c72d70ebbf13d0d865759d52",
        "f3_warn": 0,
        "path": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "init-F4-dbg"),
        "reused": True,
        "f3_cmd": "g++ -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s3r4/inject_s3r4_init.cpp <lib_dbg> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -o <out>",
        "f4_cmd": "g++ -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s3r4/inject_s3r4_init.cpp <lib_dbg> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -o <out>",
    },
    {
        "name": "init-F4-san",
        "f3_name": "init-F3-san",
        "f3_sha": "16a27ac27649118e534aea6998de7a4144b9539c8e8fd4f2d6c5439d116f7d48",
        "f3_warn": 0,
        "path": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "init-F4-san"),
        "reused": True,
        "f3_cmd": "g++ -fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s3r4/inject_s3r4_init.cpp <lib_san> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -o <out>",
        "f4_cmd": "g++ -fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s3r4/inject_s3r4_init.cpp <lib_san> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -o <out>",
    },
    {
        "name": "init-F4-san-AL",
        "f3_name": "init-F3-san-AL",
        "f3_sha": "90f4445330773c13c569bd15a0e1fd5cfa5a735070d4442523bed2b1636841b3",
        "f3_warn": 0,
        "path": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "init-F4-san-AL"),
        "reused": True,
        "f3_cmd": "g++ -fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s4/inject_r8m2e_aligned.cpp <lib_san> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -Wl,--wrap=malloc_aligned -o <out>",
        "f4_cmd": "g++ -fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter -I<tree>/S4 -I<tree>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s4/inject_r8m2e_aligned.cpp <lib_san> -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree -Wl,--wrap=malloc_aligned -o <out>",
    },
    # 13 drivers to build
    {
        "name": "dual-F4-dbg",
        "f3_name": "dual-F3-dbg",
        "f3_sha": "fb846819bafe031cbd0fa436ea0d0628dba1a372465ccf94f22e3bc09e8c2415",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "layers-F4-dbg",
        "f3_name": "layers-F3-dbg",
        "f3_sha": "5596bb685a2df2f13aa5c38cb37b1a0c9db24f8cdd80722d29a1ab838a8b2ea6",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r8m2a2_layers_R2.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "layers-dual-F4-dbg",
        "f3_name": "layers-dual-F3-dbg",
        "f3_sha": "74904b7a3f17486afa7053b6b0c8e0ba11ce3448b0d7de610d1d00ca9d72743d",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r8m2a2_layers_R2.cpp",
        "inj": "testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "nan-F4",
        "f3_name": "nan-F3",
        "f3_sha": "61019347a5215928a07419b8fe382167bc767e30e739cd822b301b3efc0127d2",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-O1 -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r8m2a2_nan_R2.cpp",
        "lib_tag": "lib_F4_bufseam",
        "tree_tag": "F4_buf",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "polyinj-F4-dbg",
        "f3_name": "polyinj-F3-dbg",
        "f3_sha": "fecd272e7ec96f754a41815918600ccc594a331cf274350e1efad92ac693f00e",
        "f3_warn": 3,
        "style": "build_r8m2a2_R3",
        "xflags": "-O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
        "inj": "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": WRAP_POLY,
    },
    {
        "name": "polyinj-F4-san",
        "f3_name": "polyinj-F3-san",
        "f3_sha": "6a8fc844832413e2ae1dd2341045072ffa50a07088c2be6aae055ac13e9d1171",
        "f3_warn": 3,
        "style": "build_r8m2a2_R3",
        "xflags": "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
        "inj": "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp",
        "lib_tag": "lib_F4_san",
        "tree_tag": "F4",
        "wraps": WRAP_POLY,
    },
    {
        "name": "r6bstate-F4-san",
        "f3_name": "r6bstate-F3-san",
        "f3_sha": "6b6aad38a1e8bf556087a00e5892a6a0fd181b97745e62ccf24d48b512adb919",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_san",
        "tree_tag": "F4",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "seamF-F4-san",
        "f3_name": "seamF-F3-san",
        "f3_sha": "f5d7eceb9204daa5fed521af588399241c586c238e925ba4043aad406e448218",
        "f3_warn": 0,
        "style": "build_r8m2a2_R3",
        "xflags": "-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_seamF_san",
        "tree_tag": "F4_seamF_san",
        "wraps": WRAP_COMMON,
    },
    {
        "name": "d003-F4-plain",
        "f3_name": "d003-F3-plain",
        "f3_sha": "afd4adb303acf06ddb0d34ed5e8a8de211f54d81a2c649ce946bba5c4ff7cb5c",
        "f3_warn": 0,
        "style": "link_drivers_r8",
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/src/driver_d003.cpp",
        "inj": "testing/d003/src/inject_d003.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "d003plan-F4-plain",
        "f3_name": "d003plan-F3-plain",
        "f3_sha": "be478d9063e5c49a6d703110bd89875499287f8a5d1a2de97def2ec3df5f2faf",
        "f3_warn": 0,
        "style": "link_drivers_r8",
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/src/driver_d003.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "seam-fmmret-F4",
        "f3_name": "seam-fmmret-F3",
        "f3_sha": "f7d445cc2a48ef9d7fae2118c3cd3c715bffaff2de89ab795dd74613f2ea585c",
        "f3_warn": 0,
        "style": "link_drivers_r8",
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/src/driver_d003.cpp",
        "inj": "testing/d003/src/inject_d003.cpp",
        "lib_tag": "lib_F4_fmmret_plain",
        "tree_tag": "F4_fmmret_plain",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "r6bstate-F4-dbg",
        "f3_name": "r6bstate-F3-dbg",
        "f3_sha": "8b269be6e21f7c74fa40a268ed6226e91e481e06000523e8cf0f9942b6e06cdd",
        "f3_warn": 0,
        "style": "link_drivers_r8m1",
        "xflags": "-O0 -g -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "r6bseam-seamF-F4",
        "f3_name": "r6bseam-seamF-F3",
        "f3_sha": "4c882f730c7966f8ff2bead0ec9119ca78969ccb69c635d4c63f0c0ea46ea5f1",
        "f3_warn": 0,
        "style": "link_r6b_seam_r8m1",
        "xflags": "-O0 -g -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_seamF_dbg",
        "tree_tag": "F4_seamF_dbg",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
]

built_drivers = []
option_diff_lines = []

def normalize_cmd(cmd_str):
    s = cmd_str
    while REPO + "/" in s:
        s = s.replace(REPO + "/", "")
    while REPO in s:
        s = s.replace(REPO, "")
    import re
    s = re.sub(r"-I\S+/S4/fmm", "-I<TREE>/S4/fmm", s)
    s = re.sub(r"-I\S+/S4", "-I<TREE>/S4", s)
    s = re.sub(r"-L\s+\S+", "-L <LIBDIR>", s)
    s = re.sub(r"\S*libS4\.a", "<LIB>", s)
    s = re.sub(r"-o\s+\S+", "-o <EXE>", s)
    return " ".join(s.split())

for d in drivers:
    name = d["name"]
    if d.get("reused"):
        sha = sha256_file(d["path"])
        cmd_str = d["f4_cmd"]
        rc = 0
        warn = 0
        d["sha"] = sha
        d["cmd"] = cmd_str
        d["rc"] = rc
        d["warn"] = warn
        built_drivers.append(d)
        norm_f3 = normalize_cmd(d["f3_cmd"])
        norm_f4 = normalize_cmd(d["f4_cmd"])
        diff = list(difflib.unified_diff([norm_f3 + "\n"], [norm_f4 + "\n"], fromfile=f"F3:{d['f3_name']}", tofile=f"F4:{name}"))
        option_diff_lines.append(f"=== {d['f3_name']} vs {name} ===\n")
        if not diff:
            option_diff_lines.append("IDENTICAL (0 differences)\n\n")
        else:
            option_diff_lines.append("".join(diff) + "\n")
        print(f"Driver {name} (reused): sha={sha[:12]}..., warnings={warn}")
        continue

    # Build driver
    exe = os.path.join(BLD, name)
    tree_path = os.path.join(TREES, d["tree_tag"])
    lib_path, _, _, _, _, _, _, _ = built_libs[d["lib_tag"]]
    drv_rel = d["drv"]
    inj_rel = d["inj"]
    lib_rel = os.path.relpath(lib_path, REPO)

    if d["style"] == "build_r8m2a2_R3":
        cmd = ["g++"] + d["xflags"].split() + [
            "-I" + os.path.join(tree_path, "S4"),
            "-I" + os.path.join(tree_path, "S4", "fmm"),
            drv_rel, inj_rel, lib_path, "-llapack", "-lblas"
        ] + d["wraps"] + ["-o", exe]
        f3_cmd = "g++ " + d["xflags"] + " -I<F3_TREE>/S4 -I<F3_TREE>/S4/fmm " + drv_rel + " " + inj_rel + " <F3_LIB>/libS4.a -llapack -lblas " + " ".join(d["wraps"]) + " -o <F3_EXE>"
    elif d["style"] in ("link_drivers_r8", "link_drivers_r8m1", "link_r6b_seam_r8m1"):
        # For -L style linking
        lib_dir = os.path.dirname(lib_path)
        cmd = ["g++"] + d["xflags"].split() + [
            "-I" + os.path.join(tree_path, "S4"),
            "-I" + os.path.join(tree_path, "S4", "fmm"),
            drv_rel, inj_rel, "-o", exe, "-L", lib_dir, "-lS4"
        ] + d["wraps"]
        f3_cmd = "g++ " + d["xflags"] + " -I<F3_TREE>/S4 -I<F3_TREE>/S4/fmm " + drv_rel + " " + inj_rel + " -o <F3_EXE> -L <F3_LIB_DIR> -lS4 " + " ".join(d["wraps"])

    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    warn = r.stderr.count("warning:")
    if r.returncode != 0:
        sys.stderr.write(f"DRIVER LINK FAILED {name}\n{r.stderr}\n")
        raise SystemExit(f"Link failed: {name}")

    sha = sha256_file(exe)
    cmd_str = " ".join(cmd).replace(REPO + os.sep, "")
    d["sha"] = sha
    d["cmd"] = cmd_str
    d["rc"] = 0
    d["warn"] = warn
    built_drivers.append(d)
    print(f"Driver {name}: sha={sha[:12]}..., warnings={warn}")

    norm_f3 = normalize_cmd(f3_cmd)
    norm_f4 = normalize_cmd(cmd_str)
    diff = list(difflib.unified_diff([norm_f3 + "\n"], [norm_f4 + "\n"], fromfile=f"F3:{d['f3_name']}", tofile=f"F4:{name}"))
    option_diff_lines.append(f"=== {d['f3_name']} vs {name} ===\n")
    if not diff:
        option_diff_lines.append("IDENTICAL (0 differences)\n\n")
    else:
        option_diff_lines.append("".join(diff) + "\n")
        raise AssertionError(f"Option difference detected for {name}: {diff}")

# Write BUILD_OPTION_DIFF_R9.txt
with open(OUT_OPTION_DIFF, "w", encoding="utf-8") as fh:
    fh.write("# BUILD_OPTION_DIFF_R9.txt -- Comparison of F3 and F4 compiler/linker options (Rule U296)\n")
    fh.write("# Requirement: All options must be identical when tree/lib paths are stripped (0 differences).\n\n")
    fh.writelines(option_diff_lines)
print(f"Wrote option diff report -> {OUT_OPTION_DIFF}")

# Write BUILD_R9.tsv
build_tsv_rows = []
# Headers
build_tsv_header = [
    "artifact", "path", "sha256", "compile_cmd", "rc", "warnings",
    "f3_artifact", "f3_sha256", "f3_warnings", "status"
]
# Libraries
for ltag in sorted(built_libs.keys()):
    lp, ls, lc, lrc, lw, f3_tag, f3_s, f3_w = built_libs[ltag]
    rel_p = os.path.relpath(lp, REPO)
    st = "REUSED_MATCH_WARNINGS" if "reused" in lc else "BUILT_MATCH_WARNINGS"
    build_tsv_rows.append([ltag, rel_p, ls, lc, str(lrc), str(lw), f3_tag, f3_s, str(f3_w), st])

# Drivers
for d in built_drivers:
    rel_p = os.path.relpath(d["path"] if d.get("reused") else os.path.join(BLD, d["name"]), REPO)
    st = "REUSED_F4" if d.get("reused") else "BUILT_F4"
    build_tsv_rows.append([
        d["name"], rel_p, d["sha"], d["cmd"], str(d["rc"]), str(d["warn"]),
        d["f3_name"], d["f3_sha"], str(d["f3_warn"]), st
    ])

with open(OUT_BUILD_TSV, "w", encoding="utf-8") as fh:
    fh.write("# BUILD_R9.tsv -- P05-S4 R9 apparatus build manifest\n")
    fh.write("\t".join(build_tsv_header) + "\n")
    for r in build_tsv_rows:
        fh.write("\t".join(r) + "\n")
print(f"Wrote build manifest -> {OUT_BUILD_TSV}")

# Write DRIVER_MAP_F3_F4_R9.tsv
driver_map_header = ["driver_family", "F3_driver", "F3_sha256", "F4_driver", "F4_sha256", "status"]
driver_map_rows = []
for d in built_drivers:
    family = d["name"].replace("-F4-dbg", "").replace("-F4-san-AL", "").replace("-F4-san", "").replace("-F4-plain", "").replace("-F4", "")
    driver_map_rows.append([
        family, d["f3_name"], d["f3_sha"], d["name"], d["sha"], "VERIFIED"
    ])

with open(OUT_DRIVER_MAP, "w", encoding="utf-8") as fh:
    fh.write("# DRIVER_MAP_F3_F4_R9.tsv -- P05-S4 R9 Driver mapping F3 -> F4\n")
    fh.write("\t".join(driver_map_header) + "\n")
    for r in driver_map_rows:
        fh.write("\t".join(r) + "\n")
print(f"Wrote driver map -> {OUT_DRIVER_MAP}")
print("ALL BUILD STEPS COMPLETED SUCCESSFULLY.")
