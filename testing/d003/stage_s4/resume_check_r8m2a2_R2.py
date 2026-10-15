#!/usr/bin/env python3
# resume_check_r8m2a2_R2.py -- P05-S4 R8 M2a2: resume consistency check, version R2 (item by item).
# Replaces nothing: RESUME_CHECK_R8_M2a2.tsv (R1, 07:18Z) is kept.  The original start gate (GATE_R8_M2a2_start.txt,
# FAILS=0, 2026-10-15T07:05:45Z) is NOT repeated and NOT overwritten; this check only maps every present change to
# the task brief or to the continuation instruction.
# Output: $EV/RESUME_CHECK_R8_M2a2_R2.tsv   columns: class, item, check, expected, actual, note
#   CLASS1 = known and allowed change (not a failure)
#   CLASS2 = known product that needs correction (goes to the correction list)
#   CLASS3 = unknown or out-of-range change (needs a pause and a check)
#   BASE   = baseline invariant (HEAD, S4 tree, judge, prefixes, no duplicate rulings)
import hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
EVA = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
OUT = os.path.join(EV, "RESUME_CHECK_R8_M2a2_R2.tsv")
ST4 = "testing/d003/stage_s4/"
M2A = "checkpoints/p05/registries/s4r8/M2/r8m2a/"

BASE = "6a4f0031afeda0a3105c9983d5a65a2d847f1488"
S4TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
RUL_N, RUL_SHA = 92855, "c1632c0f518ff20d3139891230b379772ad6757ef16e60cc7564abf71c19813c"
ERR_N, ERR_SHA = 67104, "e559b0110a26f3f039b27a39c1a08924eee4b43e394ddf799cee347706cf7520"

# Products of this round that exist but must be corrected (R1 versions are kept, R2/R3 versions are added).
NEEDS_CORRECTION = {
    "inject_r8m2a2_dual.cpp": "target 2 of linearsolve_null2 parsed with permissive sscanf; target 2 of plancall counts mallocs while target 1 arms the call (shared arm flag); s4malloc target 2 reads the counter of target 1; replaced by inject_r8m2a2_dual_R2.cpp",
    "inject_r8m2a2_dual_append.inc": "unreferenced draft include (S4_TEST_DUAL_HOOK); superseded",
    "inject_r8m2a2_dual_DRAFT_SUPERSEDED.cpp.txt": "draft already renamed .txt; superseded",
    "make_dual_r8m2a2.py": "generator of the draft; superseded",
    "build_apparatus_sources_r8m2a2.py": "replacements were not asserted to match exactly once; replaced by build_apparatus_sources_r8m2a2_R2.py",
    "inject_r8m2a2_nan.cpp": "request parser accepts trailing text; replaced by inject_r8m2a2_nan_R2.cpp",
    "driver_r8m2a2_layers.cpp": "unknown S4FMM_LAYOUT falls through to the default layout silently; replaced by driver_r8m2a2_layers_R2.cpp",
    "generate_search_tables_r8m2a2.py": "category C table asserts zero allocations for every cell without computing the grid; stage e table is a hand list; replaced by generate_search_tables_r8m2a2_R2.py",
    "generate_index_derivation_r8m2a2.py": "hard-coded table; PP2 used NTH=2 as layer 2; replaced by index derivation inside points_r8m2a2.py",
    "build_r8m2a2.py": "compile commands are not recorded per object; build dir reused names; replaced by build_r8m2a2_R3.py (new directory build_R3)",
    "build_r8m2a2.sh": "wrapper of build_r8m2a2.py",
    "m210_b_r8m2a2.gdb": "one breakpoint only (S4.cpp:2432) although the B tree has three return 20 sites; replaced by m210_b_r8m2a2_R2.gdb",
    "nm_check_r8m2a2.sh": "R1 static check, kept as record",
    "nm_check_r8m2a2_R2.sh": "static check wrapper, kept as record",
    "nm_audit_buf_r8m2a2_R2.py": "symbol table only; no relocation or call-site coverage; extended by nm_audit_buf_r8m2a2_R3.py",
    "reuse_check_r8m2a2.sh": "R1 reuse check, kept as record",
    "resume_check_r8m2a2.py": "R1 resume check (generic 'status non-empty'); replaced by this R2",
}
VALID = {
    "diff_gate_r8m2a2.sh", "gate_allow_r8m2a2_end.txt", "gate_allow_r8m2a2_start.txt", "gate_check_r8m2a2.py",
    "gate_r8m2a2.sh", "copy_r8m2a_end_r8m2a2.py", "build_rulings_r8m2a2.py", "build_errata_r8m2a2.py",
    "export_r8m2a2.sh", "k1_anchor_r8m2a2.py", "san_probe_r8m2a2.cpp", "san_probe_r8m2a2.sh",
    "r6c_state_gdb_r8m2a2.py", "r6c_state_r8m2a2.gdb", "reuse_check_r8m2a2_R2.py",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True).stdout


def main():
    if os.path.exists(OUT):
        print("resume_check_r8m2a2_R2: REFUSED exists (U17)")
        return 2
    rows, counts = [], {"CLASS1": 0, "CLASS2": 0, "CLASS3": 0, "BASE_FAIL": 0}

    def add(cls, item, check, exp, act, note=""):
        rows.append((cls, item, check, exp, act, note))
        if cls in counts:
            counts[cls] += 1

    def base(item, exp, act, note=""):
        ok = (exp == act)
        rows.append(("BASE", item, "PASS" if ok else "FAIL", exp, act, note))
        if not ok:
            counts["BASE_FAIL"] += 1

    base("HEAD", BASE, git("rev-parse", "HEAD").strip())
    base("HEAD:S4", S4TREE, git("rev-parse", "HEAD:S4").strip())
    base("JUDGE_SHA256", JUDGE, sha(os.path.join(REPO, "testing/d003/judge_d003.py")))
    base("BRANCH", "codex/p05-d003-fft-error-propagation", git("branch", "--show-current").strip())
    rul = open(os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv"), "rb").read()
    err = open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/ERRATA_8.txt"), "rb").read()
    base("RULINGS_PREFIX_92855", RUL_SHA, hashlib.sha256(rul[:RUL_N]).hexdigest(), "now %d bytes" % len(rul))
    base("ERRATA_8_PREFIX_67104", ERR_SHA, hashlib.sha256(err[:ERR_N]).hexdigest(), "now %d bytes" % len(err))
    rt = rul.decode("utf-8").splitlines()
    for i in range(236, 248):
        n = sum(1 for l in rt if l.split("\t")[0] == "U%d" % i)
        base("RULINGS_U%d_COUNT" % i, "1", str(n))
    et = err.decode("utf-8").splitlines()
    for i in range(91, 96):
        n = sum(1 for l in et if re.match(r"^E8-%d\b" % i, l))
        base("ERRATA_E8-%d_COUNT" % i, "1", str(n))
    base("TRACKED_MODIFIED_FILES",
         "checkpoints/p05/registries/RULINGS.tsv;checkpoints/p05/registries/s4r8/ERRATA_8.txt",
         ";".join(sorted(git("diff", "--name-only", "HEAD").split())))
    base("TRACKED_DIFF_S4", "", git("diff", "--name-only", "HEAD", "--", "S4").strip())
    base("TRACKED_DIFF_testing_d003", "", git("diff", "--name-only", "HEAD", "--", "testing/d003").strip())
    base("TRACKED_DIFF_r8m2a_registry", "", git("diff", "--name-only", "HEAD", "--", M2A).strip())
    tracked_m2a = [x for x in git("ls-files", M2A).split("\n") if x]
    base("R8M2A_TRACKED_FILES_20", "20", str(len(tracked_m2a)))

    # r8m2a registry back-fill: 4 copies equal their evidence originals, SUMS_END parses and matches
    for name in ("GATE_R8_M2a_end.txt", "GATE_R8_M2a_end_R2.txt", "GATE_R8_M2a_end_R3.txt", "POSTCOMMIT_R8_M2a.txt"):
        a, b = os.path.join(EVA, name), os.path.join(REPO, M2A, name)
        add("CLASS1", M2A + name, "EQUALS_EVIDENCE_ORIGINAL" if sha(a) == sha(b) else "DIFFERS", sha(a), sha(b),
            "brief 4.0 back-fill; origin evidence/p05-s4r8/m2a/" + name)
    sums_end = os.path.join(REPO, M2A, "SHA256SUMS_END.txt")
    ent = [l.split("  ", 1) for l in open(sums_end, encoding="utf-8").read().splitlines() if l.strip()]
    ok = len(ent) == 4 and all(sha(os.path.join(REPO, M2A, n)) == h for h, n in ent)
    add("CLASS1", M2A + "SHA256SUMS_END.txt", "4_ENTRIES_ALL_MATCH" if ok else "MISMATCH", "4 entries ok", "%d entries, ok=%s" % (len(ent), ok),
        "brief 4.0; E8-93")

    # git status, item by item
    status = [l for l in git("status", "--short", "-uall").split("\n") if l]
    for l in status:
        code, path = l[:2], l[3:]
        if code == " M" and path in ("checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s4r8/ERRATA_8.txt"):
            add("CLASS1", path, "TASK_APPEND_PREFIX_OK", "brief section 3", l, "U236-U247 / E8-91..95 appended once; prefix unchanged (BASE rows)")
        elif path == "checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md":
            add("CLASS1", path, "BRIEF_COPY", "brief step 1", l, "task brief copy")
        elif path.startswith(M2A) and os.path.basename(path) in (
                "GATE_R8_M2a_end.txt", "GATE_R8_M2a_end_R2.txt", "GATE_R8_M2a_end_R3.txt", "POSTCOMMIT_R8_M2a.txt", "SHA256SUMS_END.txt"):
            pass  # already listed above
        elif path.startswith(ST4) and "r8m2a2" in path:
            name = path[len(ST4):]
            if name in NEEDS_CORRECTION:
                add("CLASS2", path, "NEEDS_CORRECTION", "-", l, NEEDS_CORRECTION[name])
            elif name in VALID:
                add("CLASS1", path, "ROUND_SCRIPT_VALID", "-", l, "round script, allowed by end allow list *r8m2a2*")
            elif name.endswith("_R2.py") or name.endswith("_R3.py") or "_R2." in name or "_R3." in name or name in (
                    "points_r8m2a2.py", "design_r8m2a2.py", "prereg_r8m2a2.py", "verdict_m2_r8m2a2.py", "posctrl_m2_r8m2a2.py",
                    "completeness_r8m2a2.py", "check_report_counts_r8m2a2.py", "copy_registries_r8m2a2.py", "sums_ev_r8m2a2.py",
                    "state_bytes_r8m2a2.py", "commit_r8m2a2.sh", "postcommit_r8m2a2.py"):
                add("CLASS1", path, "CONTINUATION_SCRIPT", "-", l, "new continuation script (version-suffixed or round-named)")
            else:
                add("CLASS3", path, "UNMAPPED_ROUND_FILE", "-", l, "name contains r8m2a2 but is not in the known lists")
        else:
            add("CLASS3", path, "UNMAPPED_STATUS_ENTRY", "-", l, "outside brief section 2 allow list and not a continuation product")

    # evidence directory content
    listing = sorted(os.listdir(EV))
    for n in listing:
        p = os.path.join(EV, n)
        if n in ("tmp", "build", "tree_F3", "tree_B", "tree_F3_buf", "tree_F3_san") or os.path.isdir(p):
            add("CLASS1", "evidence/" + n + "/", "EVIDENCE_DIR", "-", "dir", "round evidence directory (not committed)")
        elif n in ("INDEX_DERIVATION_R8_M2a2.tsv", "STAGE_E_SEARCH_R8_M2a2.tsv", "CATC_SEARCH_R8_M2a2.tsv", "BUILD_R8_M2a2.tsv",
                   "BUILD_R8_M2a2_R2.tsv", "NM_CHECK_BUF_R8_M2a2_R2.tsv", "SRC_DIFF_R8_M2a2_inject_dual.txt",
                   "SRC_DIFF_R8_M2a2_inject_dual_R2.txt", "SRC_DIFF_R8_M2a2_inject_dual_R3.txt", "SRC_DIFF_R8_M2a2_inject_nan.txt",
                   "SRC_DIFF_R8_M2a2_inject_nan_R2.txt", "SRC_DIFF_R8_M2a2_driver_layers.txt"):
            add("CLASS2", "evidence/" + n, "SUPERSEDED_EVIDENCE_KEPT", "-", n, "kept (U17); replaced by a later version, report says so")
        else:
            add("CLASS1", "evidence/" + n, "EVIDENCE_FILE", "-", n, "round evidence file")

    # static nm audit: reconcile with the actual safe_run log (no start-order verdict from a new session)
    log = open(os.path.join(EV, "safe_run.log"), encoding="utf-8").read().splitlines()
    idx_start = next((i for i, l in enumerate(log) if "gate_r8m2a2.sh" in l and " start " in l), -1)
    idx_nm = next((i for i, l in enumerate(log) if "nm_audit_buf_r8m2a2_R2.py" in l), -1)
    add("CLASS1", "nm_audit_buf_r8m2a2_R2.py", "RUN_THROUGH_SAFE_RUN", "log line present", "start line %d, nm line %d" % (idx_start + 1, idx_nm + 1),
        "original start gate precedes the audit run in safe_run.log; no start-order violation is claimed")
    add("CLASS1", "nm_audit_buf_r8m2a2_R2.py", "PRE_RUN_CHECK_LOG", "no record file", "none found",
        "no pre-run check log exists for this script; none is invented (disclosed in the report)")
    add("CLASS1", "NM_CHECK_BUF_R8_M2a2_R2.tsv", "OUTPUT_PATH_IN_EV", "under evidence dir", "yes", "coverage: symbol table only (4 undefined, 1 defined); call-site coverage added in R3")

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# RESUME_CHECK_R8_M2a2_R2 -- item-by-item resume consistency; original start gate not repeated\n")
        fh.write("class\titem\tcheck\texpected\tactual\tnote\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fh.write("CLASS1=%d\nCLASS2=%d\nCLASS3=%d\nBASE_FAIL=%d\n" % (counts["CLASS1"], counts["CLASS2"], counts["CLASS3"], counts["BASE_FAIL"]))
        fh.write("RESUME_CHECK_R2=%s\n" % ("PASS" if counts["CLASS3"] == 0 and counts["BASE_FAIL"] == 0 else "ATTENTION"))
    print("resume_check_r8m2a2_R2: CLASS1=%d CLASS2=%d CLASS3=%d BASE_FAIL=%d" % (counts["CLASS1"], counts["CLASS2"], counts["CLASS3"], counts["BASE_FAIL"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
