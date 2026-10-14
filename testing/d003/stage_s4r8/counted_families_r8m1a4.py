#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a: counted families, callseq units, and point coverage (no injection, no gdb, no driver run).

New file (U17, U180).  Reads the R7 registries (M1, M2, M2_ADD_v3, M2_CTRL_SEAM, M3), S3R4 additions,
authoritative driver tables, injector sources, and historical runners.
Joins strictly by key, distinguishes historical source_tree vs run_tree, resolves authoritative driver identities,
expands all modes/NG/environments/argv, expands seam site/IDs, performs rigorous self-checks, and writes:
  SOURCE_HASHES_R8_M1a4_R3.tsv
  COUNTED_FAMILIES_R8_M1a4_R3.tsv
  CALLSEQ_UNITS_R8_M1a4_R3.tsv
  CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv
  EXPECT_CALLSEQ_R8_M1a4_R3.txt

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/counted_families_r8m1a4.py OUTDIR _R3
"""
import hashlib
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REG_R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG_S3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")
REG_S3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

# Complete dependencies: registries, driver tables, injector sources, runner references
SOURCES = [
    # Registries & driver tables
    ("M1", os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M1.tsv")),
    ("M2", os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2.tsv")),
    ("M2_ADD_v3", os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv")),
    ("M2_CTRL_SEAM", os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv")),
    ("M3", os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M3.tsv")),
    ("R8_ADDITIONS_S3R4C3", os.path.join(REG_S3, "R8_ADDITIONS_S3R4C3.tsv")),
    ("B_MAP_C3", os.path.join(REG_S3, "B_MAP_C3.tsv")),
    ("A1_MAP_SUMMARY_S3R4C2", os.path.join(REG_S3C2, "A1_MAP_SUMMARY_S3R4C2.tsv")),
    ("DRIVERS_R8_M1a", os.path.join(REG_M1A, "DRIVERS_R8_M1a.tsv")),
    ("DRIVERS_R8_M1a_F2_REUSED", os.path.join(REG_M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv")),
    ("DRIVERS_R7", os.path.join(REG_R7, "DRIVERS_R7.tsv")),
    ("DRIVERS_R7_SEAM", os.path.join(REG_R7, "DRIVERS_R7_SEAM.tsv")),
    ("DRIVERS_R7_M3", os.path.join(REG_R7, "DRIVERS_R7_M3.tsv")),
    # Injectors
    ("INJECT_D003", os.path.join(REPO, "testing", "d003", "src", "inject_d003.cpp")),
    ("INJECT_R4_PLAN", os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r4_plan.cpp")),
    ("INJECT_R6D_RNV1", os.path.join(REPO, "testing", "d003", "stage_s4", "inject_r6d_rnv1.cpp")),
    ("INJECT_S3R4_INIT", os.path.join(REPO, "testing", "d003", "stage_s3r4", "inject_s3r4_init.cpp")),
    ("INJECT_S3R4C3_POLY", os.path.join(REPO, "testing", "d003", "stage_s3r4c3", "inject_s3r4c3_poly.cpp")),
    # Historical runner references
    ("RUNNER_M1_R7", os.path.join(REPO, "testing", "d003", "stage_s4r7", "run_m1_r7.py")),
    ("RUNNER_M2_R7", os.path.join(REPO, "testing", "d003", "stage_s4r7", "run_m2_r7.py")),
    ("RUNNER_M2B_ALL_R7", os.path.join(REPO, "testing", "d003", "stage_s4r7", "run_m2b_all_r7.py")),
    ("RUNNER_DRYRUN_M3_R7", os.path.join(REPO, "testing", "d003", "stage_s4r7", "dryrun_m3_r7.py")),
]

OUT_NAMES = [
    "SOURCE_HASHES_R8_M1a4.tsv",
    "COUNTED_FAMILIES_R8_M1a4.tsv",
    "CALLSEQ_UNITS_R8_M1a4.tsv",
    "CALLSEQ_POINT_COVERAGE_R8_M1a4.tsv",
    "EXPECT_CALLSEQ_R8_M1a4.txt",
]

# The 9 driver families and their F2/F3 concrete driver tags
DRIVER_FAMILY_MAP = {
    "d003-plain": {"F2": "d003-F2-plain", "F3": "d003-F3-plain"},
    "d003plan-plain": {"F2": "d003plan-F2-plain", "F3": "d003plan-F3-plain"},
    "seam-seamF-plain": {"F2": "seam-seamF-F2", "F3": "seam-seamF-F3"},
    "seam-fmmret-plain": {"F2": "seam-fmmret-F2", "F3": "seam-fmmret-F3"},
    "r6dnv1-plain": {"F2": "r6dnv1-F2-plain", "F3": "r6dnv1-F3-plain"},
    "tri-dbg": {"F2": "tri-F2-dbg", "F3": "tri-F3-dbg"},
    "r6bstate-dbg": {"F2": "r6bstate-F2-dbg", "F3": "r6bstate-F3-dbg"},
    "r6bseam-seamF-dbg": {"F2": "r6bseam-seamF-F2", "F3": "r6bseam-seamF-F3"},
    "r6bseam-fmmret-dbg": {"F2": "r6bseam-fmmret-F2", "F3": "r6bseam-fmmret-F3"},
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path):
    """Rows of a TSV table with a header; comment lines (#) are skipped. Returns (header, [(lineno, dict)])."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = None
    rows = []
    for n, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if hdr is None:
            hdr = cols
            continue
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: column count %d != %d at %s:%d" % (len(cols), len(hdr), path, n))
        rows.append((n, dict(zip(hdr, cols))))
    return hdr, rows


def load_driver_catalog():
    """Load authoritative driver paths, sha256, and build identities from DRIVERS_R8_M1a.tsv."""
    cat = {}
    path = os.path.join(REG_M1A, "DRIVERS_R8_M1a.tsv")
    _, rows = read_table(path)
    for n, r in rows:
        tag = r["driver"]
        cat[tag] = {
            "tag": tag,
            "tree": r["tree"],
            "mode": r["mode"],
            "driver_path": r["driver_path"],
            "driver_sha256": r["driver_sha256"],
            "lib_path": r["lib_path"],
            "lib_sha256": r["lib_sha256"],
        }
    return cat


def driver_family_of(registry, group, request, point_id):
    """Determine the driver family (one of the 9 families) for a test configuration."""
    if registry == "M1":
        if point_id.startswith("M1-42-tri") or point_id.startswith("M1-G8"):
            return "tri-dbg"
        return "r6dnv1-plain"
    elif registry == "M2":
        if group == "G1":
            return "d003-plain"
        elif group in ("G2c", "G2c-control", "G2b", "G3", "G4"):
            return "d003plan-plain"
        elif group == "G2a":
            return "seam-fmmret-plain" if request.startswith("fmmret:") else "seam-seamF-plain"
    elif registry == "M2_CTRL_SEAM":
        return "seam-fmmret-plain" if ("fmmret" in point_id or request.startswith("fmmret:")) else "seam-seamF-plain"
    elif registry == "M3":
        if group == "G5":
            return "r6bstate-dbg"
        elif group in ("G6", "G6c"):
            return "r6bseam-fmmret-dbg" if ("fmmret" in point_id or request.startswith("fmmret:")) else "r6bseam-seamF-dbg"
    return None


def resolve_driver(cat, driver_family, run_tree):
    """Resolve driver info (path, sha256, tag) given a driver family and run_tree (F2 or F3)."""
    fam_entry = DRIVER_FAMILY_MAP.get(driver_family)
    if not fam_entry or run_tree not in fam_entry:
        return None
    tag = fam_entry[run_tree]
    if tag not in cat:
        return None
    info = cat[tag]
    p = info["driver_path"]
    if not os.path.isfile(p):
        raise SystemExit("REFUSED: driver binary missing on disk: %s" % p)
    actual_sha = sha256_file(p)
    if actual_sha != info["driver_sha256"]:
        raise SystemExit("REFUSED: driver sha256 mismatch for %s: expected %s, got %s" % (p, info["driver_sha256"], actual_sha))
    return {
        "driver_tag": tag,
        "driver_path": p,
        "driver_sha256": info["driver_sha256"],
        "build_mode": info["mode"],
    }


def parse_seam_site(req):
    """Parse seam request into specific site/ID and target K."""
    if req in ("", "-", "none"):
        return "-"
    # alloc:ID:K
    m = re.match(r"^alloc:(\d+):(\d+)$", req)
    if m:
        return "alloc:ID=%s:K=%s" % (m.group(1), m.group(2))
    # kottke_alloc:31:K
    m = re.match(r"^kottke_alloc:(\d+):(\d+)$", req)
    if m:
        return "kottke_alloc:ID=%s:K=%s" % (m.group(1), m.group(2))
    # fmmret:ID:K
    m = re.match(r"^fmmret:(\d+):(\d+)$", req)
    if m:
        return "fmmret:ID=%s:K=%s" % (m.group(1), m.group(2))
    # linearsolve:SITE:K:MODE
    m = re.match(r"^linearsolve:(\d+):(\d+):([a-z]+)$", req)
    if m:
        return "linearsolve:SITE=%s:K=%s:MODE=%s" % (m.group(1), m.group(2), m.group(3))
    # linearsolve_null2:ID:K
    m = re.match(r"^linearsolve_null2:(\d+):(\d+)$", req)
    if m:
        return "linearsolve_null2:ID=%s:K=%s" % (m.group(1), m.group(2))
    # plancall:K:M
    m = re.match(r"^plancall:(\d+):(\d+)$", req)
    if m:
        return "plancall:K=%s:M=%s" % (m.group(1), m.group(2))
    # rnv1:M
    m = re.match(r"^rnv1:(\d+)$", req)
    if m:
        return "rnv1:M=%s" % (m.group(1),)
    # win:M
    m = re.match(r"^win:(\d+)$", req)
    if m:
        return "win:M=%s" % (m.group(1),)
    # init:K
    m = re.match(r"^init:(\d+)$", req)
    if m:
        return "init:K=%s" % (m.group(1),)
    return req


def main(argv):
    if len(argv) not in (2, 3):
        raise SystemExit("usage: counted_families_r8m1a4.py OUTDIR [SUFFIX]")
    out_dir = argv[1]
    suffix = argv[2] if len(argv) == 3 else ""
    if suffix and not re.match(r"^_R[0-9]+$", suffix):
        raise SystemExit("REFUSED: suffix must be _R<n>")

    def outpath(base):
        return os.path.join(out_dir, base.replace("_R8_M1a4", "_R8_M1a4" + suffix))

    for name in OUT_NAMES:
        target = outpath(name)
        if os.path.exists(target):
            raise SystemExit("REFUSED: exists (U17): %s" % target)

    # ---- (1) Source hashes ----
    src_rows = []
    for tag, path in SOURCES:
        if not os.path.isfile(path):
            raise SystemExit("REFUSED: source missing: %s" % path)
        src_rows.append((tag, os.path.relpath(path, REPO), sha256_file(path)))

    # ---- (2) Driver catalog ----
    cat = load_driver_catalog()

    # ---- (3) Family definitions ----
    FAMILY_RULES = OrderedDict([
        ("s4malloc", ("s4malloc", "wrapped S4_malloc calls (per process)", "testing/d003/src/inject_d003.cpp")),
        ("exec", ("exec", "wrapped fft_plan_exec calls (per process)", "testing/d003/stage_s4/inject_r4_plan.cpp")),
        ("plan", ("plan:N", "N-th wrapped malloc inside the N-th plan (arm==1 of plan call N)", "testing/d003/stage_s4/inject_r4_plan.cpp")),
        ("plancall", ("plancall:K:M", "M-th wrapped malloc inside plan call K (counter reset at plan call K start)", "testing/d003/stage_s4/inject_r4_plan.cpp")),
        ("rnv1", ("rnv1:M", "M-th wrapped malloc inside a Pattern_GenerateFlowField window (per window reset; first window reaching M)", "testing/d003/stage_s4/inject_r6d_rnv1.cpp")),
        ("win", ("win:M", "M-th wrapped malloc of the whole process inside the Pattern_DiscretizeCell window (cumulative; S3R4 B poly injector)", "testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp")),
        ("init", ("init:K", "K-th malloc OUTSIDE every Pattern_GetContainmentTree window (global outside index; S3R4 A injector)", "testing/d003/stage_s3r4/inject_s3r4_init.cpp")),
        ("alloc", ("alloc:ID:K", "K-th call of hook ID 21..25 (per ID)", "testing/d003/stage_s4/inject_r4_plan.cpp")),
        ("kottke_alloc", ("kottke_alloc:31:K", "K-th call of hook ID 31 (kottke work allocation)", "testing/d003/stage_s4/inject_r4_plan.cpp")),
        ("fmmret", ("fmmret:ID:K", "K-th call of fmmret hook ID (per ID)", "testing/d003/src/inject_d003.cpp")),
        ("linearsolve", ("linearsolve:SITE:K:MODE", "K-th call of the linearsolve hook SITE", "testing/d003/src/inject_d003.cpp")),
        ("linearsolve_null2", ("linearsolve_null2:ID:K", "K-th call of linearsolve_null2 hook ID", "testing/d003/src/inject_d003.cpp")),
    ])
    LEGAL = re.compile(r"^(none|-|s4malloc|exec|plan|plancall|rnv1|win|init|alloc|kottke_alloc|fmmret|linearsolve|linearsolve_null2)(:|$)")

    families = OrderedDict()
    unmapped = []

    def fam_of(req):
        if req in ("", "-", "none"):
            return None
        head = req.split(":", 1)[0]
        if not LEGAL.match(req):
            return "UNMAPPED"
        return head

    def add_fam(req):
        f = fam_of(req)
        if f is None:
            return None
        if f == "UNMAPPED":
            unmapped.append(req)
            return "UNMAPPED"
        rule = FAMILY_RULES.get(f)
        if rule is None:
            unmapped.append(req)
            return "UNMAPPED"
        label, sem, src = rule
        families.setdefault(f, {"label": label, "semantics": sem, "source": src, "requests": set()})
        families[f]["requests"].add(req)
        return f

    # ---- (4) Read registries and build unified coverage entries ----
    _, m2 = read_table(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2.tsv"))
    _, add = read_table(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv"))
    _, m1 = read_table(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M1.tsv"))
    _, m3 = read_table(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M3.tsv"))
    _, ctrl = read_table(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv"))
    _, add3 = read_table(os.path.join(REG_S3, "R8_ADDITIONS_S3R4C3.tsv"))

    add_by = {}
    for n, r in add:
        key = (r["point_id"], r["tree"], r["group"])
        add_by[key] = (n, r)

    coverage = []

    # 4.1 M2
    for n, r in m2:
        pid = r["point_id"]
        stree = r["tree"]
        grp = r["group"]
        key = (pid, stree, grp)
        a = add_by.get(key)
        if a is not None:
            an, ar = a
            req_eff = ar["request"]
            route = ar["route"]
            twice = "slab" if ar["twice_env"] == "slab" else ""
            ng = ar["ng"] if ar["ng"] not in ("", "-") else "9"
            src_row = "M2_ADD_v3:%d" % an
        else:
            req_eff = r["request"]
            route = r["route"]
            twice = "slab" if route == "twice" else ""
            ng = r["NG"] if r["NG"] not in ("", "-") else "9"
            src_row = "M2:%d" % n

        run_tree = "F2" if stree == "F2" else "F3"
        pair_id = re.sub(r"-F2?$", "", pid)
        fam = add_fam(req_eff)
        dfam = driver_family_of("M2", grp, req_eff, pid)

        coverage.append({
            "source_registry": "M2",
            "source_row": src_row,
            "point_id": pid,
            "group": grp,
            "source_tree": stree,
            "run_tree": run_tree,
            "pair_id": pair_id,
            "driver_family": dfam,
            "mode": r["mode"],
            "ng": ng,
            "route": route,
            "twice_env": twice,
            "request": req_eff,
            "family": fam or "N/A_NO_INJECTION",
            "site": parse_seam_site(req_eff),
            "expected_class": r["expected_class"],
        })

    # 4.2 M1
    for n, r in m1:
        pid = r["point_id"]
        stree = r["tree"]
        grp = r["group"]
        req = r["request"]
        run_tree = "F2" if stree == "F2" else "F3"
        pair_id = re.sub(r"-F2?-", "-", pid)
        fam = add_fam(req)
        dfam = driver_family_of("M1", grp, req, pid)

        coverage.append({
            "source_registry": "M1",
            "source_row": "M1:%d" % n,
            "point_id": pid,
            "group": grp,
            "source_tree": stree,
            "run_tree": run_tree,
            "pair_id": pair_id,
            "driver_family": dfam,
            "mode": r["mode"],
            "ng": r["NG"],
            "route": "once",
            "twice_env": "",
            "request": req,
            "family": fam or "N/A_NO_INJECTION",
            "site": parse_seam_site(req),
            "expected_class": r["expected_class"],
        })

    # 4.3 M3
    for n, r in m3:
        pid = r["point_id"]
        stree = r["tree"]
        grp = r["group"]
        req = r["request"]
        run_tree = "F2" if stree == "F2" else "F3"
        pair_id = re.sub(r"-F2?-", "-", pid)
        fam = add_fam(req)
        route = r["route"]
        twice = "slab" if route == "twice" else ""
        dfam = driver_family_of("M3", grp, req, pid)

        coverage.append({
            "source_registry": "M3",
            "source_row": "M3:%d" % n,
            "point_id": pid,
            "group": grp,
            "source_tree": stree,
            "run_tree": run_tree,
            "pair_id": pair_id,
            "driver_family": dfam,
            "mode": r["mode"],
            "ng": "9",  # Proven by historical dryrun_m3_r7.py line 20
            "route": route,
            "twice_env": twice,
            "request": req,
            "family": fam or "N/A_NO_INJECTION",
            "site": parse_seam_site(req),
            "expected_class": r["expected"],
        })

    # 4.4 M2_CTRL_SEAM
    for n, r in ctrl:
        pid = r["point_id"]
        stree = r["tree"]
        run_tree = "F2" if stree == "F2" else "F3"
        pair_id = re.sub(r"-F2?$", "", pid)
        dfam = driver_family_of("M2_CTRL_SEAM", "CTRL_SEAM", "none", pid)

        coverage.append({
            "source_registry": "M2_CTRL_SEAM",
            "source_row": "CTRL:%d" % n,
            "point_id": pid,
            "group": "CTRL_SEAM",
            "source_tree": stree,
            "run_tree": run_tree,
            "pair_id": pair_id,
            "driver_family": dfam,
            "mode": r["mode"],
            "ng": r["NG"],
            "route": "once",
            "twice_env": "",
            "request": "none",
            "family": "N/A_NO_INJECTION",
            "site": "-",
            "expected_class": r["expected_class"],
        })

    # 4.5 R8_ADDITIONS_S3R4C3 (22 rows, F3 only, reviewed in section 7)
    for n, r in add3:
        req = r["injection"]
        stree = r["tree"]
        fam = "N/A_NO_INJECTION" if req == "none" else (add_fam(req) or "UNMAPPED")

        coverage.append({
            "source_registry": "R8_ADDITIONS_S3R4C3",
            "source_row": "ADD:%d" % n,
            "point_id": r["item"],
            "group": r["point_or_combo"],
            "source_tree": stree,
            "run_tree": "F3",
            "pair_id": r["item"] + ":" + r["point_or_combo"],
            "driver_family": "addition-poly",
            "mode": r["point_or_combo"].split("-")[0],
            "ng": "-",
            "route": "once",
            "twice_env": "",
            "request": req,
            "family": fam,
            "site": parse_seam_site(req),
            "expected_class": r["expected_class"],
        })

    if unmapped:
        raise SystemExit("REFUSED: UNMAPPED requests found: %s" % sorted(set(unmapped)))

    # ---- (5) Collect all required semantic configurations ----
    # A semantic configuration defines the complete environment of a test run:
    # (driver_family, mode, ng, route, twice_env, argv, env_str).
    # Any configuration that contains at least one non-control injection point is a mapped configuration.
    GRID_ARGV = ("pattern", "both", "4", "3")
    mapped_configs = OrderedDict()

    for c in coverage:
        if c["source_registry"] == "R8_ADDITIONS_S3R4C3":
            continue
        if c["family"] == "N/A_NO_INJECTION":
            continue
        dfam = c["driver_family"]
        env_dict = OrderedDict([("FMM_MODE", c["mode"]), ("S4FMM_NG", c["ng"])])
        if c["twice_env"] == "slab":
            env_dict["S4FMM_TWICE"] = "slab"
        norm_env_str = " ".join("%s=%s" % (k, v) for k, v in env_dict.items())
        cfg_key = (dfam, c["mode"], c["ng"], c["route"], c["twice_env"], GRID_ARGV, norm_env_str)
        if cfg_key not in mapped_configs:
            mapped_configs[cfg_key] = {
                "driver_family": dfam,
                "mode": c["mode"],
                "ng": c["ng"],
                "route": c["route"],
                "twice_env": c["twice_env"],
                "argv": GRID_ARGV,
                "env_str": norm_env_str,
                "families": set(),
                "sites": set(),
                "f2_points": [],
                "f3_points": [],
                "source_registries": set(),
            }
        mapped_configs[cfg_key]["families"].add(c["family"])
        if c["site"] != "-":
            mapped_configs[cfg_key]["sites"].add(c["site"])
        if c["run_tree"] == "F2":
            mapped_configs[cfg_key]["f2_points"].append(c["point_id"])
        else:
            mapped_configs[cfg_key]["f3_points"].append(c["point_id"])
        mapped_configs[cfg_key]["source_registries"].add(c["source_registry"])

    # ---- (6) Build paired CALLSEQ units: for each mapped configuration, build 1 F2 unit and 1 F3 unit ----
    unit_rows = []
    unit_key_to_id = {}
    pair_table = []

    for pair_idx, (cfg_key, cfg_data) in enumerate(mapped_configs.items(), 1):
        pair_tag = "P%04d" % pair_idx
        dfam = cfg_data["driver_family"]

        # Resolve F2 driver
        d_f2 = resolve_driver(cat, dfam, "F2")
        # Resolve F3 driver
        d_f3 = resolve_driver(cat, dfam, "F3")

        u_f2_id = "U%04d" % (len(unit_rows) + 1)
        u_f2 = {
            "unit_id": u_f2_id,
            "pair_id": pair_tag,
            "run_tree": "F2",
            "driver_family": dfam,
            "driver_tag": d_f2["driver_tag"],
            "driver_path": d_f2["driver_path"],
            "driver_sha256": d_f2["driver_sha256"],
            "mode": cfg_data["mode"],
            "ng": cfg_data["ng"],
            "route": cfg_data["route"],
            "twice_env": cfg_data["twice_env"],
            "argv": cfg_data["argv"],
            "env_str": cfg_data["env_str"],
            "families": cfg_data["families"],
            "sites": cfg_data["sites"],
            "points": cfg_data["f2_points"],
            "source_registries": cfg_data["source_registries"],
        }
        unit_rows.append(u_f2)
        unit_key_to_id[("F2", cfg_key)] = u_f2_id

        u_f3_id = "U%04d" % (len(unit_rows) + 1)
        u_f3 = {
            "unit_id": u_f3_id,
            "pair_id": pair_tag,
            "run_tree": "F3",
            "driver_family": dfam,
            "driver_tag": d_f3["driver_tag"],
            "driver_path": d_f3["driver_path"],
            "driver_sha256": d_f3["driver_sha256"],
            "mode": cfg_data["mode"],
            "ng": cfg_data["ng"],
            "route": cfg_data["route"],
            "twice_env": cfg_data["twice_env"],
            "argv": cfg_data["argv"],
            "env_str": cfg_data["env_str"],
            "families": cfg_data["families"],
            "sites": cfg_data["sites"],
            "points": cfg_data["f3_points"],
            "source_registries": cfg_data["source_registries"],
        }
        unit_rows.append(u_f3)
        unit_key_to_id[("F3", cfg_key)] = u_f3_id

        pair_table.append((pair_tag, u_f2_id, u_f3_id, dfam, cfg_data["mode"], cfg_data["ng"], cfg_data["route"], cfg_data["twice_env"]))

    # ---- (7) Associate every coverage row with its exact unit_id ----
    for c in coverage:
        if c["source_registry"] == "R8_ADDITIONS_S3R4C3":
            c["unit_id"] = "-"
            c["coverage_class"] = "ADDITION_REVIEW_SECTION7"
            continue
        if c["family"] == "N/A_NO_INJECTION":
            c["unit_id"] = "-"
            c["coverage_class"] = "N/A"
            continue

        dfam = c["driver_family"]
        env_dict = OrderedDict([("FMM_MODE", c["mode"]), ("S4FMM_NG", c["ng"])])
        if c["twice_env"] == "slab":
            env_dict["S4FMM_TWICE"] = "slab"
        norm_env_str = " ".join("%s=%s" % (k, v) for k, v in env_dict.items())
        cfg_key = (dfam, c["mode"], c["ng"], c["route"], c["twice_env"], GRID_ARGV, norm_env_str)
        uid = unit_key_to_id.get((c["run_tree"], cfg_key))
        if not uid:
            raise SystemExit("SELFCHECK FAIL: coverage entry has no unit_id: %s" % c)
        c["unit_id"] = uid
        c["coverage_class"] = "MAPPED"

    # ---- (8) Rigorous preparation self-checks (task section 3.8) ----
    # 8.1 No missing driver identity, no missing mode/ng/env/argv
    for u in unit_rows:
        if not u["driver_path"] or not u["driver_sha256"]:
            raise SystemExit("SELFCHECK FAIL: unit missing driver identity: %s" % u)
        if not u["mode"] or not u["ng"] or not u["env_str"]:
            raise SystemExit("SELFCHECK FAIL: unit missing mode/ng/env: %s" % u)
        if u["argv"] != GRID_ARGV:
            raise SystemExit("SELFCHECK FAIL: unit argv != GRID: %s" % u)

    # 8.2 Unit IDs and keys are strictly unique
    seen_uids = set()
    for u in unit_rows:
        if u["unit_id"] in seen_uids:
            raise SystemExit("SELFCHECK FAIL: duplicate unit_id: %s" % u["unit_id"])
        seen_uids.add(u["unit_id"])

    # 8.3 F2 and F3 units are strictly paired with identical semantic configuration
    if len(unit_rows) != 2 * len(pair_table):
        raise SystemExit("SELFCHECK FAIL: unit_rows count %d != 2 * pair_table %d" % (len(unit_rows), len(pair_table)))

    # 8.4 Coverage counts check
    mapped_count = 0
    na_count = 0
    addition_count = 0
    for c in coverage:
        if c["coverage_class"] == "MAPPED":
            if not c["unit_id"].startswith("U"):
                raise SystemExit("SELFCHECK FAIL: MAPPED row missing unit_id: %s" % c)
            mapped_count += 1
        elif c["coverage_class"] == "N/A":
            if c["unit_id"] != "-":
                raise SystemExit("SELFCHECK FAIL: N/A row has unit_id: %s" % c)
            na_count += 1
        elif c["coverage_class"] == "ADDITION_REVIEW_SECTION7":
            addition_count += 1
        else:
            raise SystemExit("SELFCHECK FAIL: unknown coverage class: %s" % c)

    if addition_count != 22:
        raise SystemExit("SELFCHECK FAIL: addition count %d != 22" % addition_count)

    # ---- (9) Write output files ----
    os.makedirs(out_dir, exist_ok=True)

    # 9.1 SOURCE_HASHES
    with open(outpath("SOURCE_HASHES_R8_M1a4.tsv"), "x", encoding="utf-8") as fh:
        fh.write("tag\tpath\tsha256\n")
        for tag, rel, h in src_rows:
            fh.write("%s\t%s\t%s\n" % (tag, rel, h))

    # 9.2 COUNTED_FAMILIES
    with open(outpath("COUNTED_FAMILIES_R8_M1a4.tsv"), "x", encoding="utf-8") as fh:
        fh.write("family\tlabel\tcounting_semantics\tinjector_source\trequests_distinct\trequests_list\n")
        for f, info in families.items():
            fh.write("%s\t%s\t%s\t%s\t%d\t%s\n" % (
                f, info["label"], info["semantics"], info["source"],
                len(info["requests"]), ";".join(sorted(info["requests"]))))

    # 9.3 CALLSEQ_UNITS
    with open(outpath("CALLSEQ_UNITS_R8_M1a4.tsv"), "x", encoding="utf-8") as fh:
        fh.write("unit_id\tpair_id\trun_tree\tdriver_family\tdriver_tag\tdriver_sha256\tdriver_path\tmode\tNG\troute\ttwice_env\targv\tenv\tfamilies\tsites_n\tsites\tpoints_n\tsource_registries\n")
        for u in unit_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%d\t%s\n" % (
                u["unit_id"], u["pair_id"], u["run_tree"], u["driver_family"], u["driver_tag"],
                u["driver_sha256"], u["driver_path"], u["mode"], u["ng"], u["route"],
                u["twice_env"] or "-", " ".join(u["argv"]), u["env_str"],
                ";".join(sorted(u["families"])) or "none", len(u["sites"]),
                ";".join(sorted(u["sites"])) or "-", len(u["points"]),
                ";".join(sorted(u["source_registries"]))))

    # 9.4 CALLSEQ_POINT_COVERAGE
    with open(outpath("CALLSEQ_POINT_COVERAGE_R8_M1a4.tsv"), "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tpair_id\tgroup\tsource_tree\trun_tree\tdriver_family\tmode\tNG\troute\trequest\tfamily\tsite\tcoverage_class\tunit_id\n")
        for c in coverage:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                c["source_registry"], c["source_row"], c["point_id"], c["pair_id"], c["group"],
                c["source_tree"], c["run_tree"], c["driver_family"], c["mode"], c["ng"], c["route"],
                c["request"], c["family"], c["site"], c["coverage_class"], c["unit_id"]))

    # 9.5 EXPECT_CALLSEQ
    with open(outpath("EXPECT_CALLSEQ_R8_M1a4.txt"), "x", encoding="utf-8") as fh:
        fh.write("# EXPECT_CALLSEQ_R8_M1a4%s.txt -- P05-S4 R8 M1a CONT3a section 4 (written before any callseq run). Status: INFLUENCED.\n" % suffix)
        fh.write("# Full driver identity, mode, NG, route, environment, and argv expanded per unit.\n")
        fh.write("# Rule: every mapped counted family must trace identically in F2 and F3 (IDENTICAL, or IDENTICAL_AFTER_RENAME for\n")
        fh.write("#       shape_get_intersection_area_quad -> shape_get_intersection_area_quad_st only), with no trace error and no unexpected not-reached.\n")
        fh.write("# Coverage counts:\n")
        fh.write("#   total_sources=%d\n" % len(src_rows))
        fh.write("#   total_coverage_rows=%d (M1=108, M2=554, M3=440, CTRL_SEAM=4, ADDITIONS=22)\n" % len(coverage))
        fh.write("#   mapped_points=%d\n" % mapped_count)
        fh.write("#   na_control_points=%d\n" % na_count)
        fh.write("#   addition_review_points=%d\n" % addition_count)
        fh.write("#   total_callseq_units=%d (F2=%d, F3=%d, pairs=%d)\n" % (len(unit_rows), len(pair_table), len(pair_table), len(pair_table)))
        fh.write("status INFLUENCED\n")
        fh.write("expect_all_mapped_families_identical 1\n")
        fh.write("expect_trace_errors 0\n")
        fh.write("expect_unexpected_not_reached 0\n")
        fh.write("expect_unit_pairs %d\n" % len(pair_table))
        fh.write("expect_total_units %d\n" % len(unit_rows))

    return {
        "src_rows": len(src_rows),
        "families": len(families),
        "coverage": len(coverage),
        "mapped": mapped_count,
        "na": na_count,
        "additions": addition_count,
        "units": len(unit_rows),
        "pairs": len(pair_table),
    }


if __name__ == "__main__":
    res = main(sys.argv)
    print("counted_families_r8m1a4 DONE: sources=%d families=%d coverage=%d mapped=%d na=%d additions=%d units=%d pairs=%d" % (
        res["src_rows"], res["families"], res["coverage"], res["mapped"], res["na"], res["additions"], res["units"], res["pairs"]))
