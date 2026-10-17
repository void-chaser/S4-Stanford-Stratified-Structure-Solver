#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_r9m1.py -- Build missing F4 seam libraries and drivers for P05-S4 R9 M1. New file.
import concurrent.futures, datetime, difflib, hashlib, os, re, subprocess, sys, tarfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

TREES = os.path.join(EV, "trees")
BLD = os.path.join(EV, "build")
os.makedirs(TREES, exist_ok=True)
os.makedirs(BLD, exist_ok=True)

OUT_BUILD_TSV = os.path.join(EV, "BUILD_R9M1.tsv")
OUT_OPTION_DIFF = os.path.join(EV, "BUILD_OPTION_DIFF_R9M1.txt")
OUT_WARN_TSV = os.path.join(EV, "WARN_COUNT_R9M1.tsv")

F4_REV = "05097a7"
F4_TREE = "589e15eb11fcb04e031b524f25a443e7921946cf"

DBG_FLAGS = "-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
PLAIN_FLAGS = "-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
CPP_BASE = ["-IS4", "-IS4/RNP", "-IS4/kiss_fft"]

SEAMF_MACROS = ["-DS4_TEST_LINEARSOLVE_SEAM", "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2", "-DS4_TEST_ALLOC_SEAM", "-DS4_TEST_KOTTKE_SEAM"]
FMMRET_MACROS = ["-DS4_TEST_FMMRET_SEAM"]

WRAP_COMMON = ["-Wl,--wrap=malloc", "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
               "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "-Wl,--wrap=_Z9S4_mallocm"]
WRAP_INIT = WRAP_COMMON + ["-Wl,--wrap=Pattern_GetContainmentTree"]
WRAP_POLY = WRAP_COMMON + ["-Wl,--wrap=Pattern_DiscretizeCell"]
WRAP_RNV1 = WRAP_COMMON + ["-Wl,--wrap=Pattern_GenerateFlowField"]

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
t_seam_plain = export_fresh("F4_seamF_plain")
t_fmmret_dbg = export_fresh("F4_fmmret_dbg")

print("--- Step 2: Applying seam patches ---")
rep_seam_plain_acd = os.path.join(TREES, "apply_F4_seamF_plain_ACD.txt")
rep_seam_plain_b2 = os.path.join(TREES, "apply_F4_seamF_plain_B2.txt")
rep_fmmret_dbg = os.path.join(TREES, "apply_F4_fmmret_dbg.txt")

subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r2.py",
                "--root", t_seam_plain, "--repo", REPO, "--families", "A,C,D", "--report", rep_seam_plain_acd], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_b2.py",
                "--root", t_seam_plain, "--repo", REPO, "--report", rep_seam_plain_b2], check=True)
subprocess.run(["python3", "-I", "-B", "testing/d003/seam/apply_seam_r5_fmmret.py",
                "--tree", "A", "--root", t_fmmret_dbg, "--repo", REPO, "--report", rep_fmmret_dbg], check=True)
print("Seam patches applied.")

print("--- Step 3: Building missing libraries ---")
built_libs = {}
# 1. lib_F4_seamF_plain (F3: 71 warnings)
p_seam_pl, s_seam_pl, c_seam_pl, rc_seam_pl, w_seam_pl = build_lib("lib_F4_seamF_plain", t_seam_plain, PLAIN_FLAGS, SEAMF_MACROS)
built_libs["lib_F4_seamF_plain"] = (p_seam_pl, s_seam_pl, c_seam_pl, rc_seam_pl, w_seam_pl, "seamF-F3-plain", "cfc31f3ff1b57934057bef4e98f308dd25b6f2fd253750b18a4cd5d8c5c07a34", 71)

# 2. lib_F4_fmmret_dbg (F3: 62 warnings)
p_fmm_dbg, s_fmm_dbg, c_fmm_dbg, rc_fmm_dbg, w_fmm_dbg = build_lib("lib_F4_fmmret_dbg", t_fmmret_dbg, DBG_FLAGS, FMMRET_MACROS)
built_libs["lib_F4_fmmret_dbg"] = (p_fmm_dbg, s_fmm_dbg, c_fmm_dbg, rc_fmm_dbg, w_fmm_dbg, "fmmret-F3", "309707ab1567c9273d8f44f6aa3227dc29de827f6310760b1d5cb278801f3f6e", 62)

# 3, 4. Reused base libraries
lib_f4_plain_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_plain", "libS4.a")
lib_f4_dbg_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_dbg", "libS4.a")
built_libs["lib_F4_plain"] = (lib_f4_plain_path, sha256_file(lib_f4_plain_path), "reused from s3r5", 0, 71, "lib_F3_plain", "abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de", 71)
built_libs["lib_F4_dbg"] = (lib_f4_dbg_path, sha256_file(lib_f4_dbg_path), "reused from s3r5", 0, 62, "lib_F3_dbg", "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a", 62)

warn_records = []
for ltag, (lp, ls, lc, lrc, lw, f3_tag, f3_s, f3_w) in built_libs.items():
    print(f"Library {ltag}: sha={ls[:12]}..., warnings={lw} (F3: {f3_w})")
    assert lw == f3_w, f"Library {ltag} warnings mismatch: actual={lw}, expected={f3_w}"
    warn_records.append([ltag, "library", str(lw), f3_tag, str(f3_w), "MATCH"])

print("--- Step 4: Linking drivers ---")
drivers_to_build = [
    {
        "name": "init-F4-plain",
        "f3_name": "init-F3",
        "f3_sha": "ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68",
        "f3_warn": 0,
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s3r4/inject_s3r4_init.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_INIT,
    },
    {
        "name": "poly-F4-plain",
        "f3_name": "poly-F3",
        "f3_sha": "c92e7d7a4a0ed0550dcb4d05ebe06a8d29cad697f8799052593ffe9f31fd9be7",
        "f3_warn": 3,
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "polyinj-F4-plain",
        "f3_name": "polyinj-F3",
        "f3_sha": "419cfb727932cc8d9417fd3a873c578f2f1f597f57e501041d9dd3b221ad30a9",
        "f3_warn": 3,
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp",
        "inj": "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_POLY,
    },
    {
        "name": "r6dnv1-F4-plain",
        "f3_name": "r6dnv1-F3-plain",
        "f3_sha": "a9fccfa39dd263ea6e72d605f87b01e3efc1bb7666a29fb51402dfa0e929a41d",
        "f3_warn": 0,
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r6d_rnv1.cpp",
        "lib_tag": "lib_F4_plain",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_RNV1,
    },
    {
        "name": "tri-F4-dbg",
        "f3_name": "tri-F3-dbg",
        "f3_sha": "7cd9edfad8bedb695777a9c102ef68ecf461b46cdd89638ef58f5c13b26b9be0",
        "f3_warn": 0,
        "xflags": "-O0 -g -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s3r3/driver_s3r3_tri.cpp",
        "inj": "testing/d003/stage_s4/inject_r6d_rnv1.cpp",
        "lib_tag": "lib_F4_dbg",
        "tree_tag": "F4",
        "wraps": ["-llapack", "-lblas"] + WRAP_RNV1,
    },
    {
        "name": "seam-seamF-F4",
        "f3_name": "seam-seamF-F3",
        "f3_sha": "c691acd71db3d4aabdc08f999058033228513f7049e19c3715720aab55df4ae6",
        "f3_warn": 0,
        "xflags": "-O1 -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/src/driver_d003.cpp",
        "inj": "testing/d003/src/inject_d003.cpp",
        "lib_tag": "lib_F4_seamF_plain",
        "tree_tag": "F4_seamF_plain",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
    {
        "name": "r6bseam-fmmret-F4",
        "f3_name": "r6bseam-fmmret-F3",
        "f3_sha": "e6ee5b6af6919f48f497917d3a80035c816240040bb32fc2c107bcd5d10762da",
        "f3_warn": 0,
        "xflags": "-O0 -g -Wall -Wextra -Wno-unused-parameter",
        "drv": "testing/d003/stage_s4/driver_r6b_state.cpp",
        "inj": "testing/d003/stage_s4/inject_r4_plan.cpp",
        "lib_tag": "lib_F4_fmmret_dbg",
        "tree_tag": "F4_fmmret_dbg",
        "wraps": ["-llapack", "-lblas"] + WRAP_COMMON,
    },
]

# Reused drivers from M0
reused_drivers = [
    {
        "name": "d003-F4-plain",
        "f3_name": "d003-F3-plain",
        "f3_sha": "afd4adb303acf06ddb0d34ed5e8a8de211f54d81a2c649ce946bba5c4ff7cb5c",
        "f3_warn": 0,
        "path": "checkpoints/p05/evidence/p05-s4r9/m0/build/d003-F4-plain",
        "sha": "e39e4b0f4a66b7bf6d19b558636ffbdb76b1e35eec4825c2398600eb35e0d9f6",
        "warn": 0,
        "cmd": "g++ -O1 -Wall -Wextra -Wno-unused-parameter -I<TREE>/S4 -I<TREE>/S4/fmm testing/d003/src/driver_d003.cpp testing/d003/src/inject_d003.cpp -o <EXE> -L <LIBDIR> -lS4 -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm",
        "reused": True,
    },
    {
        "name": "d003plan-F4-plain",
        "f3_name": "d003plan-F3-plain",
        "f3_sha": "be478d9063e5c49a6d703110bd89875499287f8a5d1a2de97def2ec3df5f2faf",
        "f3_warn": 0,
        "path": "checkpoints/p05/evidence/p05-s4r9/m0/build/d003plan-F4-plain",
        "sha": "41d2d579715c77d595831fde670c171880f198e37eaf52ad27477d65673292e3",
        "warn": 0,
        "cmd": "g++ -O1 -Wall -Wextra -Wno-unused-parameter -I<TREE>/S4 -I<TREE>/S4/fmm testing/d003/src/driver_d003.cpp testing/d003/stage_s4/inject_r4_plan.cpp -o <EXE> -L <LIBDIR> -lS4 -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm",
        "reused": True,
    },
    {
        "name": "r6bstate-F4-dbg",
        "f3_name": "r6bstate-F3-dbg",
        "f3_sha": "8b269be6e21f7c74fa40a268ed6226e91e481e06000523e8cf0f9942b6e06cdd",
        "f3_warn": 0,
        "path": "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bstate-F4-dbg",
        "sha": "2bce13d9f23276a0153ea8fa30464bf2cbfd99798f5d8336c1c1f8e285b15aa2",
        "warn": 0,
        "cmd": "g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I<TREE>/S4 -I<TREE>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s4/inject_r4_plan.cpp -o <EXE> -L <LIBDIR> -lS4 -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm",
        "reused": True,
    },
    {
        "name": "r6bseam-seamF-F4",
        "f3_name": "r6bseam-seamF-F3",
        "f3_sha": "4c882f730c7966f8ff2bead0ec9119ca78969ccb69c635d4c63f0c0ea46ea5f1",
        "f3_warn": 0,
        "path": "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bseam-seamF-F4",
        "sha": "e53560673269090865be502f96aa06fb693f867afdbbfdd3c109eb759547911d",
        "warn": 0,
        "cmd": "g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I<TREE>/S4 -I<TREE>/S4/fmm testing/d003/stage_s4/driver_r6b_state.cpp testing/d003/stage_s4/inject_r4_plan.cpp -o <EXE> -L <LIBDIR> -lS4 -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm",
        "reused": True,
    },
    {
        "name": "seam-fmmret-F4",
        "f3_name": "seam-fmmret-F3",
        "f3_sha": "f7d445cc2a48ef9d7fae2118c3cd3c715bffaff2de89ab795dd74613f2ea585c",
        "f3_warn": 0,
        "path": "checkpoints/p05/evidence/p05-s4r9/m0/build/seam-fmmret-F4",
        "sha": "10e4f2ce7f4df4fb688d032a2b72e784d41fccfe25337a396009a11994178b1c",
        "warn": 0,
        "cmd": "g++ -O1 -Wall -Wextra -Wno-unused-parameter -I<TREE>/S4 -I<TREE>/S4/fmm testing/d003/src/driver_d003.cpp testing/d003/src/inject_d003.cpp -o <EXE> -L <LIBDIR> -lS4 -llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm",
        "reused": True,
    },
]

def normalize_cmd(cmd_str):
    s = cmd_str
    while REPO + "/" in s:
        s = s.replace(REPO + "/", "")
    while REPO in s:
        s = s.replace(REPO, "")
    s = re.sub(r"-I\S+/S4/fmm", "-I<TREE>/S4/fmm", s)
    s = re.sub(r"-I\S+/S4", "-I<TREE>/S4", s)
    s = re.sub(r"-L\s+\S+", "-L <LIBDIR>", s)
    s = re.sub(r"\S*libS4\.a", "<LIB>", s)
    s = re.sub(r"-o\s+\S+", "-o <EXE>", s)
    return " ".join(s.split())

built_drivers = []
option_diff_lines = []

# Process reused drivers first
for d in reused_drivers:
    act_sha = sha256_file(os.path.join(REPO, d["path"]))
    assert act_sha == d["sha"], f"Reused driver {d['name']} sha mismatch: act={act_sha}, exp={d['sha']}"
    d["rc"] = 0
    built_drivers.append(d)
    norm_f3 = normalize_cmd(d["cmd"])
    norm_f4 = normalize_cmd(d["cmd"])
    diff = list(difflib.unified_diff([norm_f3 + "\n"], [norm_f4 + "\n"], fromfile=f"F3:{d['f3_name']}", tofile=f"F4:{d['name']}"))
    option_diff_lines.append(f"=== {d['f3_name']} vs {d['name']} ===\n")
    if not diff:
        option_diff_lines.append("IDENTICAL (0 differences)\n\n")
    else:
        option_diff_lines.append("".join(diff) + "\n")
    warn_records.append([d["name"], "driver", str(d["warn"]), d["f3_name"], str(d["f3_warn"]), "MATCH"])
    print(f"Driver {d['name']} (reused): sha={d['sha'][:12]}..., warnings={d['warn']}")

# Build the 7 new drivers
for d in drivers_to_build:
    name = d["name"]
    exe = os.path.join(BLD, name)
    tree_path = os.path.join(TREES, d["tree_tag"])
    lib_path, _, _, _, _, _, _, _ = built_libs[d["lib_tag"]]
    drv_rel = d["drv"]
    inj_rel = d["inj"]
    lib_dir = os.path.dirname(lib_path)

    cmd = ["g++"] + d["xflags"].split() + [
        "-I" + os.path.join(tree_path, "S4"),
        "-I" + os.path.join(tree_path, "S4", "fmm"),
        drv_rel, inj_rel, "-o", exe, "-L", lib_dir, "-lS4"
    ] + d["wraps"]

    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    warn = r.stderr.count("warning:")
    if r.returncode != 0:
        sys.stderr.write(f"DRIVER LINK FAILED {name}\n{r.stderr}\n")
        raise SystemExit(f"Link failed: {name}")

    assert warn == d["f3_warn"], f"Driver {name} warnings mismatch: actual={warn}, expected={d['f3_warn']}"

    sha = sha256_file(exe)
    cmd_str = " ".join(cmd).replace(REPO + os.sep, "")
    d["sha"] = sha
    d["cmd"] = cmd_str
    d["path"] = os.path.relpath(exe, REPO)
    d["rc"] = 0
    d["warn"] = warn
    built_drivers.append(d)
    print(f"Driver {name} (built): sha={sha[:12]}..., warnings={warn}")

    f3_cmd = "g++ " + d["xflags"] + " -I<TREE>/S4 -I<TREE>/S4/fmm " + drv_rel + " " + inj_rel + " -o <EXE> -L <LIBDIR> -lS4 " + " ".join(d["wraps"])
    norm_f3 = normalize_cmd(f3_cmd)
    norm_f4 = normalize_cmd(cmd_str)
    diff = list(difflib.unified_diff([norm_f3 + "\n"], [norm_f4 + "\n"], fromfile=f"F3:{d['f3_name']}", tofile=f"F4:{name}"))
    option_diff_lines.append(f"=== {d['f3_name']} vs {name} ===\n")
    if not diff:
        option_diff_lines.append("IDENTICAL (0 differences)\n\n")
    else:
        option_diff_lines.append("".join(diff) + "\n")
        raise AssertionError(f"Option difference detected for {name}: {diff}")
    warn_records.append([name, "driver", str(warn), d["f3_name"], str(d["f3_warn"]), "MATCH"])

# Assert total option differences is 0
diff_count = sum(1 for l in option_diff_lines if l.startswith("+") or l.startswith("-"))
print(f"Total option diff markers: {diff_count}")
assert diff_count == 0, f"BUILD_OPTION_DIFF has {diff_count} diff markers!"

# Write BUILD_OPTION_DIFF_R9M1.txt
with open(OUT_OPTION_DIFF, "w", encoding="utf-8") as fh:
    fh.write("# BUILD_OPTION_DIFF_R9M1.txt -- Comparison of F3 and F4 compiler/linker options (Rule U310)\n")
    fh.write("# Requirement: All options must be identical when tree/lib paths are stripped (0 differences).\n\n")
    fh.writelines(option_diff_lines)
print(f"Wrote option diff report -> {OUT_OPTION_DIFF}")

# Write WARN_COUNT_R9M1.tsv
with open(OUT_WARN_TSV, "w", encoding="utf-8") as fh:
    fh.write("# WARN_COUNT_R9M1.tsv -- Warning counts of F4 artifacts vs F3 equivalents\n")
    fh.write("artifact\tkind\tf4_warnings\tf3_artifact\tf3_warnings\tstatus\n")
    for r in warn_records:
        fh.write("\t".join(r) + "\n")
print(f"Wrote warning count table -> {OUT_WARN_TSV}")

# Write BUILD_R9M1.tsv
build_tsv_rows = []
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
    st = "REUSED_F4" if d.get("reused") else "BUILT_F4"
    build_tsv_rows.append([
        d["name"], d["path"], d["sha"], d["cmd"], str(d["rc"]), str(d["warn"]),
        d["f3_name"], d["f3_sha"], str(d["f3_warn"]), st
    ])

with open(OUT_BUILD_TSV, "w", encoding="utf-8") as fh:
    fh.write("# BUILD_R9M1.tsv -- P05-S4 R9 M1 apparatus build manifest\n")
    fh.write("\t".join(build_tsv_header) + "\n")
    for r in build_tsv_rows:
        fh.write("\t".join(r) + "\n")
print(f"Wrote build manifest -> {OUT_BUILD_TSV}")

# Update DRIVERS_F3_SIDE_R9M1.tsv with built sha256
inv_path = os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv")
built_map = {d["f3_name"]: d["sha"] for d in built_drivers}
new_inv_lines = []
with open(inv_path, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\r\n")
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            new_inv_lines.append(line)
            continue
        parts = line.split("\t")
        f3_d = parts[0]
        if parts[4] == "TO_BUILD":
            parts[3] = built_map[f3_d]
            parts[4] = "BUILT_VERIFIED"
        new_inv_lines.append("\t".join(parts))

with open(inv_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(new_inv_lines) + "\n")
print(f"Updated {inv_path} with built sha256 values.")
