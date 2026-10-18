#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_kmap_r9m1r2.py -- Build -g kmap-dbg variants of d003 and d003plan for K mapping (Rule U315). New file.
import difflib, hashlib, os, subprocess, sys, tarfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

TREES = os.path.join(EV, "trees")
BLD = os.path.join(EV, "build")
os.makedirs(TREES, exist_ok=True)
os.makedirs(BLD, exist_ok=True)

OUT_BUILD_TSV = os.path.join(EV, "BUILD_KMAP_R9M1R2.tsv")
OUT_OPTION_DIFF = os.path.join(EV, "BUILD_OPTION_DIFF_KMAP_R9M1R2.txt")

F3_REV = "8d8202a"
F4_REV = "05097a7"

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

def export_tree(rev, tag):
    dest = os.path.join(TREES, tag)
    if os.path.exists(dest):
        import shutil
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    p = subprocess.Popen(["git", "archive", "--format=tar", rev, "S4"], cwd=REPO, stdout=subprocess.PIPE)
    with tarfile.open(fileobj=p.stdout, mode="r|") as tf:
        try:
            tf.extractall(dest, filter="data")
        except TypeError:
            tf.extractall(dest)
    if p.wait() != 0:
        raise SystemExit(f"git archive failed for {rev}")
    return dest

print("Exporting F3 and F4 trees...")
f3_tree = export_tree(F3_REV, "F3")
f4_tree = export_tree(F4_REV, "F4")

LIB_F3_DBG = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "build_r8", "F3-dbg", "build")
LIB_F4_DBG = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "lib_F4_dbg")

WRAP_FLAGS = [
    "-llapack", "-lblas",
    "-Wl,--wrap=malloc",
    "-Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan",
    "-Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
    "-Wl,--wrap=_Z9S4_mallocm"
]

drivers = [
    {
        "name": "d003-F3-kmap-dbg",
        "plain_name": "d003-F3-plain",
        "tree_dir": f3_tree,
        "tree_tag": "F3",
        "lib_dir": LIB_F3_DBG,
        "src_drv": os.path.join(REPO, "testing", "d003", "src", "driver_d003.cpp"),
        "src_inj": os.path.join(REPO, "testing", "d003", "src", "inject_d003.cpp"),
        "plain_exe": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8", "d003-F3-plain", "driver"),
    },
    {
        "name": "d003-F4-kmap-dbg",
        "plain_name": "d003-F4-plain",
        "tree_dir": f4_tree,
        "tree_tag": "F4",
        "lib_dir": LIB_F4_DBG,
        "src_drv": os.path.join(REPO, "testing", "d003", "src", "driver_d003.cpp"),
        "src_inj": os.path.join(REPO, "testing", "d003", "src", "inject_d003.cpp"),
        "plain_exe": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0", "build", "d003-F4-plain"),
    },
    {
        "name": "d003plan-F3-kmap-dbg",
        "plain_name": "d003plan-F3-plain",
        "tree_dir": f3_tree,
        "tree_tag": "F3",
        "lib_dir": LIB_F3_DBG,
        "src_drv": os.path.join(REPO, "testing", "d003", "src", "driver_d003.cpp"),
        "src_inj": os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r4_plan.cpp"),
        "plain_exe": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "drivers_r8", "d003plan-F3-plain", "driver"),
    },
    {
        "name": "d003plan-F4-kmap-dbg",
        "plain_name": "d003plan-F4-plain",
        "tree_dir": f4_tree,
        "tree_tag": "F4",
        "lib_dir": LIB_F4_DBG,
        "src_drv": os.path.join(REPO, "testing", "d003", "src", "driver_d003.cpp"),
        "src_inj": os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r4_plan.cpp"),
        "plain_exe": os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0", "build", "d003plan-F4-plain"),
    },
]

build_tsv_rows = []
option_diff_texts = []

# Prepare gdb script for hit count checking
tmp_cmd_file = os.path.join(EV, "tmp", "hit_count_verify.cmd")
with open(tmp_cmd_file, "w") as f:
    f.write('set pagination off\nset confirm off\nset $count = 0\nbreak __wrap__Z9S4_mallocm\ncommands\nsilent\nset $count = $count + 1\ncontinue\nend\nrun pattern both 4 3\nprintf "TOTAL_HITS=%d\\n", $count\nquit\n')

def get_malloc_hits(exe, env_dict):
    cmd = ["gdb", "-batch", "-x", tmp_cmd_file, "--args", exe, "pattern", "both", "4", "3"]
    r = subprocess.run(cmd, env=env_dict, cwd=REPO, capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if "TOTAL_HITS=" in l:
            try:
                return int(l.split("=")[1])
            except ValueError:
                pass
    return -1

for drv in drivers:
    out_exe = os.path.join(BLD, drv["name"])
    
    # 1. Compile kmap-dbg driver
    compile_cmd = [
        "g++", "-O1", "-g", "-Wall", "-Wextra", "-Wno-unused-parameter",
        f"-I{drv['tree_dir']}/S4", f"-I{drv['tree_dir']}/S4/fmm",
        drv["src_drv"], drv["src_inj"],
        "-o", out_exe,
        f"-L{drv['lib_dir']}", "-lS4"
    ] + WRAP_FLAGS
    
    r = subprocess.run(compile_cmd, cwd=REPO, capture_output=True, text=True)
    warn_count = r.stderr.count("warning:")
    if r.returncode != 0:
        sys.stderr.write(f"FAILED to build {drv['name']}: {r.stderr}\n")
        sys.exit(1)
        
    exe_sha = sha256_file(out_exe)
    print(f"Built {drv['name']}: sha256={exe_sha[:12]}..., warnings={warn_count}")

    # 2. Check BUILD_OPTION_DIFF
    plain_canon = [
        "g++", "-O1", "-Wall", "-Wextra", "-Wno-unused-parameter",
        "-I<TREE>/S4", "-I<TREE>/S4/fmm",
        drv["src_drv"], drv["src_inj"],
        "-o", "<OUT>",
        "-L<LIBDIR>", "-lS4"
    ] + WRAP_FLAGS

    kmap_canon = [
        "g++", "-O1", "-g", "-Wall", "-Wextra", "-Wno-unused-parameter",
        "-I<TREE>/S4", "-I<TREE>/S4/fmm",
        drv["src_drv"], drv["src_inj"],
        "-o", "<OUT>",
        "-L<LIBDIR>", "-lS4"
    ] + WRAP_FLAGS

    diff = list(difflib.unified_diff(plain_canon, kmap_canon, fromfile=drv["plain_name"], tofile=drv["name"]))
    added_options = [l.strip() for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed_options = [l.strip() for l in diff if l.startswith("-") and not l.startswith("---")]

    # Assert Rule §6-6: only -g is different
    assert added_options == ["+-g"], f"BUILD_OPTION_DIFF has differences other than -g: {added_options}"
    assert removed_options == [], f"BUILD_OPTION_DIFF has removed options: {removed_options}"

    diff_str = "\n".join(diff)
    option_diff_texts.append(f"=== {drv['plain_name']} vs {drv['name']} ===\n{diff_str}\nDifference is strictly '+-g' (1 added, 0 removed).\n")

    # 3. Check hit counts between kmap-dbg and plain driver
    test_modes = ["closed1d", "closed2d", "experimental", "fft", "kottke", "jones", "nv", "vl"]
    for m in test_modes:
        env = os.environ.copy()
        env["FMM_MODE"] = m
        env["S4FMM_NG"] = "9"
        hits_plain = get_malloc_hits(drv["plain_exe"], env)
        hits_kmap = get_malloc_hits(out_exe, env)
        assert hits_plain >= 0 and hits_kmap >= 0, f"Failed to get hits for {drv['name']} in mode {m}"
        assert hits_plain == hits_kmap, f"HIT COUNT MISMATCH in mode {m}: plain={hits_plain} != kmap={hits_kmap}"

    print(f"Verified all 8 mode hit counts match plain driver for {drv['name']}.")

    build_tsv_rows.append([
        drv["name"], out_exe, exe_sha, " ".join(compile_cmd), warn_count, "BUILT_VERIFIED_EQUAL_HITS"
    ])

# Write BUILD_OPTION_DIFF_KMAP_R9M1R2.txt
with open(OUT_OPTION_DIFF, "w", encoding="utf-8") as f:
    f.write("# BUILD_OPTION_DIFF_KMAP_R9M1R2.txt -- Option diff between plain and kmap-dbg drivers (Rule U315, §6-6)\n\n")
    for t in option_diff_texts:
        f.write(t + "\n")

# Write BUILD_KMAP_R9M1R2.tsv
with open(OUT_BUILD_TSV, "w", encoding="utf-8") as f:
    f.write("# BUILD_KMAP_R9M1R2.tsv -- Build record of kmap-dbg drivers for P05-S4 R9 M1R2 (Rule U315)\n")
    f.write("driver_name\texe_path\tsha256\tcompile_command\twarning_count\tstatus\n")
    for r in build_tsv_rows:
        f.write("%s\t%s\t%s\t%s\t%d\t%s\n" % (r[0], r[1], r[2], r[3], r[4], r[5]))

print("build_kmap_r9m1r2.py: ALL 4 KMAP DRIVERS BUILT AND VERIFIED SUCCESSFULLY.")
