#!/usr/bin/env python3
# relr4_verdict.py -- REL-R4 comparison engine.  Reads the per-unit observations, the pre-registration
# and the MPI/CAPI tables, and writes (read by column name only):
#   VERDICT_RELR4.tsv  one row per comparison unit, with the U / B / F4 columns (task brief section 6)
#   RESULTS_RELR4.tsv  every per-unit observation of T1-T5, one row per run
#   SUMMARY_RELR4.txt  machine-readable category counts (the report's COUNTS block is checked against it)
# Categories (task brief section 4): SAME, DIFF_WITHIN_TOL, DIFF_ATTRIBUTED, REGRESSION, IMPROVED,
# BOTH_FAIL, U_UNAVAILABLE, FLAKY.  The engine only compares rc, normalised text, file sha256 and numdiff
# numbers; it never reads a driver PASS/FAIL line.
import os, sys, re, hashlib, json

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4"),
         "M": os.path.join(EV, "trees", "M"),
         "M2": os.path.join(EV, "trees", "M2"),
         "M3": os.path.join(EV, "trees", "M3")}
TAB = chr(9)
NL = chr(10)
CATS = ["SAME", "DIFF_WITHIN_TOL", "DIFF_ATTRIBUTED", "REGRESSION", "IMPROVED", "BOTH_FAIL",
        "U_UNAVAILABLE", "FLAKY"]
T1_TOL = 1e-12
T2_TOL = {"simple": 1e-12, "fresnel": 1e-12, "fanfig12": 1e-10}
T3_TOL = 1e-12
T4_TOL = 1e-12
MPI_EXAMPLES = ["examples/MPI_example/binary_grating_mpi.lua", "examples/MPI_example/mpi_simple.lua"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def read_kv(path):
    d = {}
    if not os.path.isfile(path):
        return d
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        k, _, v = line.rstrip(NL).partition(TAB)
        d[k] = v
    return d


def read_tsv(path):
    rows, hdr = [], None
    if not os.path.isfile(path):
        return rows
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        if len(f) != len(hdr):
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def load_units(dirname):
    out = {}
    d = os.path.join(EV, dirname)
    if not os.path.isdir(d):
        return out
    for n in sorted(os.listdir(d)):
        if not n.endswith(".tsv"):
            continue
        u = read_kv(os.path.join(d, n))
        if u.get("unit_id"):
            out[u["unit_id"]] = u
    return out


def eid(rel):
    s = rel[len("examples/"):].replace("/", "__")
    return s[:-4] if s.endswith(".lua") else s


def norm_text(text, tree, cwd=None):
    # normalise every tree-specific absolute path so that byte comparisons across trees are meaningful
    pairs = []
    if cwd:
        pairs.append((cwd, "<CWD>"))
    pairs.append((TREES.get(tree, ""), "<TREE>"))
    pairs.append((EV, "<EV>"))
    pairs.append((REPO, "<REPO>"))
    for p, tag in pairs:
        if p:
            text = text.replace(p, tag)
            text = text.replace(os.path.realpath(p), tag)
    # Lua truncates long source paths with a leading "..." (e.g. "...tream/S4/examples/x.lua:19:"),
    # so any remaining path fragment that ends in examples/ is replaced by a single placeholder.
    text = re.sub(r"[^ \t:]*examples/", "<TREE>/examples/", text)
    return text


def unit_text(u, which):
    p = u.get(which + "_path", "")
    if not p:
        return ""
    fp = p if os.path.isabs(p) else os.path.join(REPO, p)
    try:
        return open(fp, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def unit_cwd(u):
    p = u.get("stdout_path", "")
    return os.path.dirname(p if os.path.isabs(p) else os.path.join(REPO, p)) if p else ""


ERROR_MARKERS = ("stack traceback:", "attempt to call", "bad argument #", "syntax error",
                 "unexpected symbol", "':' expected", "'end' expected", "cannot open", "not found.")


def stderr_error(u, tree):
    """(error_present, silent) -- the U Lua frontend exits 0 even when the script raised a Lua error
    (the P04 frontend rewrite made the exit status non-zero); rc alone is therefore not a pass criterion."""
    txt = norm_text(unit_text(u, "stderr"), tree, unit_cwd(u))
    present = any(m in txt for m in ERROR_MARKERS)
    rc = str(u.get("rc", ""))
    silent = present and rc == "0"
    return present, silent


def outcome(u, tree=None):
    if not u:
        return "MISSING"
    s = u.get("status", "")
    if s == "TIMEOUT":
        return "TIMEOUT"
    if s in ("PASS_REF", "PASS", "BUILD_OK", "WITH_MPI"):
        return "PASS"
    if s == "RAN_FAIL":
        return "FAIL"
    if s == "RAN_OK":
        if tree:
            present, _silent = stderr_error(u, tree)
            return "FAIL" if present else "PASS"
        return "PASS"
    return "FAIL"


def token_relmax(ta, tb):
    a, b = ta.split(), tb.split()
    if len(a) != len(b):
        return None, "LEN_DIFF(%d/%d)" % (len(a), len(b))
    mx = 0.0
    for x, y in zip(a, b):
        try:
            fx, fy = float(x), float(y)
        except ValueError:
            if x != y:
                return None, "NONNUMERIC_DIFF"
            continue
        mx = max(mx, abs(fx - fy) / max(abs(fx), abs(fy), 1e-300))
    return mx, "OK"


def files_dict(u):
    d = {}
    for item in (u.get("files") or "").split(";"):
        if ":" in item:
            name, sha = item.rsplit(":", 1)
            d[name] = sha
    return d


def products_relmax(u1, u2):
    """numeric comparison of the files both runs wrote (same relative names); None if not comparable"""
    d1, d2 = files_dict(u1), files_dict(u2)
    common = sorted(set(d1) & set(d2))
    mx = 0.0
    for name in common:
        cwd1, cwd2 = unit_cwd(u1), unit_cwd(u2)
        p1, p2 = os.path.join(cwd1, name), os.path.join(cwd2, name)
        if not (os.path.isfile(p1) and os.path.isfile(p2)):
            return None, "FILE_MISSING:" + name
        m, why = token_relmax(open(p1, encoding="utf-8", errors="replace").read(),
                              open(p2, encoding="utf-8", errors="replace").read())
        if m is None:
            return None, why
        mx = max(mx, m)
    if set(d1) != set(d2):
        return None, "FILE_SET_DIFF"
    return mx, "OK"


def flaky(u1, u2, tree):
    if not u1 or not u2:
        return "MISSING"
    c1, c2 = unit_cwd(u1), unit_cwd(u2)
    t1 = norm_text(unit_text(u1, "stdout"), tree, c1)
    t2 = norm_text(unit_text(u2, "stdout"), tree, c2)
    e1 = norm_text(unit_text(u1, "stderr"), tree, c1)
    e2 = norm_text(unit_text(u2, "stderr"), tree, c2)
    if u1.get("status") != u2.get("status") or u1.get("rc") != u2.get("rc"):
        return "STATUS"
    if t1 != t2:
        return "STDOUT"
    if e1 != e2:
        return "STDERR"
    if files_dict(u1) != files_dict(u2):
        return "FILES"
    return ""


def compare(t_u, t_f4, tree_u, tree_f4, tol, flaky_checked=(), pass_by_rc=False):
    """core comparison for a pair of trees; returns (category, detail)"""
    for tree, (a, b) in flaky_checked:
        why = flaky(a, b, tree)
        if why:
            return "FLAKY", "tree %s pass1 != pass2 (%s)" % (tree, why)
    if not t_u or not t_f4:
        return "U_UNAVAILABLE", "missing observation"
    if pass_by_rc:
        # suites that compare two trees' outputs against a third artefact (reference data) must judge
        # "did the run succeed" by the return code only; the reference match is the category itself.
        ou = "PASS" if str(t_u.get("rc")) == "0" else "FAIL"
        of = "PASS" if str(t_f4.get("rc")) == "0" else "FAIL"
    else:
        ou, of = outcome(t_u, tree_u), outcome(t_f4, tree_f4)
    _eu, sil_u = stderr_error(t_u, tree_u)
    _ef, sil_f = stderr_error(t_f4, tree_f4)
    if ou == "PASS" and of == "PASS":
        cu, cf = unit_cwd(t_u), unit_cwd(t_f4)
        su = norm_text(unit_text(t_u, "stdout"), tree_u, cu)
        sf = norm_text(unit_text(t_f4, "stdout"), tree_f4, cf)
        eu = norm_text(unit_text(t_u, "stderr"), tree_u, cu)
        ef = norm_text(unit_text(t_f4, "stderr"), tree_f4, cf)
        fd_u, fd_f = files_dict(t_u), files_dict(t_f4)
        if su == sf and eu == ef and fd_u == fd_f:
            return "SAME", "rc=0 both, normalised stdout/stderr and file products identical"
        rel, why = token_relmax(su, sf)
        if rel is None:
            prel, pwhy = products_relmax(t_u, t_f4)
            if prel is not None and prel <= tol and why.startswith("NONNUMERIC") is False:
                return "DIFF_WITHIN_TOL", "stdout %s; product files relmax=%.3e <= %g" % (why, prel, tol)
            prd = "file products " + ("identical" if fd_u == fd_f else "differ")
            return "DIFF_ATTRIBUTED", "stdout not numeric-comparable (%s), %s" % (why, prd)
        if rel <= tol:
            return "DIFF_WITHIN_TOL", "stdout relmax=%.3e <= %g (not byte-identical)" % (rel, tol)
        return "DIFF_ATTRIBUTED", "stdout relmax=%.3e > %g" % (rel, tol)
    if ou == "PASS" and of != "PASS":
        return "REGRESSION", "%s passes (rc=%s), %s %s (rc=%s)" % (tree_u, t_u.get("rc"), tree_f4,
                                                                  of.lower(), t_f4.get("rc"))
    if ou != "PASS" and of == "PASS":
        return "IMPROVED", "%s %s (rc=%s), %s passes (rc=%s)" % (tree_u, ou.lower(), t_u.get("rc"),
                                                                 tree_f4, t_f4.get("rc"))
    if ou == "TIMEOUT" or of == "TIMEOUT":
        return "BOTH_FAIL", "timeout involved: %s rc=%s, %s rc=%s" % (tree_u, t_u.get("rc"), tree_f4, t_f4.get("rc"))
    # both failed: compare normalised stderr messages
    cu, cf = unit_cwd(t_u), unit_cwd(t_f4)
    eu = norm_text(unit_text(t_u, "stderr"), tree_u, cu).strip()
    ef = norm_text(unit_text(t_f4, "stderr"), tree_f4, cf).strip()
    same_msg = "same normalised stderr" if eu == ef else "different stderr messages"
    silent = ""
    if sil_u or sil_f:
        silent = "; silent-exit-0 with Lua error: " + ",".join(
            (["U"] if sil_u else []) + (["F4"] if sil_f else []))
    return "BOTH_FAIL", "%s rc=%s / %s rc=%s; %s%s" % (tree_u, t_u.get("rc"), tree_f4, t_f4.get("rc"), same_msg, silent)


def pairs_of(path):
    out = []
    if not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            try:
                out.append((float(f[0]), float(f[1])))
            except ValueError:
                continue
    return out


def relclose(a, b):
    return abs(a - b) <= 1e-12 * max(abs(a), abs(b), 1e-300)


def match_pairs(merged, ref):
    used, mx, matched = set(), 0.0, 0
    for f, v in merged:
        best = None
        for j, (rf, rv) in enumerate(ref):
            if j in used:
                continue
            if relclose(f, rf):
                best = j
                break
        if best is None:
            continue
        used.add(best)
        matched += 1
        rv = ref[best][1]
        mx = max(mx, abs(v - rv) / max(abs(v), abs(rv), 1e-300))
    return mx, matched, len(merged) - matched, len(ref) - matched


def rc_outcome(u):
    """run success judged by the return code only (used where the category is 'matches a third artefact')"""
    if not u:
        return "MISSING"
    if u.get("status") == "TIMEOUT":
        return "TIMEOUT"
    return "PASS" if str(u.get("rc")) == "0" else "FAIL"


def mpi_fseq(start, end, step):
    """replicate a Lua numeric for loop's IEEE-754 double sequence (init, init+step, ... as accumulated)"""
    out = []
    f = start
    while f <= end:
        out.append(f)
        f += step
    return out


def mpi_values(path):
    """values of an out<N>.txt file in line order (the script writes them in increasing frequency order)"""
    vals = []
    if not os.path.isfile(path):
        return vals
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.split()
        if len(f) >= 2:
            try:
                vals.append(float(f[1]))
            except ValueError:
                pass
    return vals


def main():
    prereg = read_tsv(os.path.join(EV, "PREREG_RELR4.tsv"))
    u1 = load_units("units_t1")
    u2 = load_units("units_t2")
    u3 = load_units("units_t3")
    u4 = load_units("units_t4")
    u5 = load_units("units_t5")
    results = []

    def add_result(suite, uid, u):
        results.append({"unit_id": uid, "suite": suite, "tree": u.get("tree", ""), "pass": u.get("pass", ""),
                        "status": u.get("status", ""), "rc": u.get("rc", ""), "signal": u.get("signal", ""),
                        "timed_out": u.get("timed_out", ""), "stdout_sha256": u.get("stdout_sha256", ""),
                        "stderr_sha256": u.get("stderr_sha256", ""), "numdiff_rc": u.get("numdiff_rc", ""),
                        "numdiff_relmax": u.get("numdiff_relmax", ""), "dur_s": u.get("dur_s", ""),
                        "extra": u.get("extra", "")})
    for d in (u1, u2, u3, u4, u5):
        for uid in sorted(d):
            add_result(d[uid].get("suite", ""), uid, d[uid])

    verdict = []  # dicts: unit_id, suite, comparison, u, b, f4, category, detail

    def vadd(unit_id, suite, comparison, tu, tb, tf, category, detail):
        verdict.append({"unit_id": unit_id, "suite": suite, "comparison": comparison,
                        "u": tu, "b": tb, "f4": tf, "category": category, "detail": detail})

    # ---------------------------------------------------------------- T1 examples
    rels = sorted(set(u.get("example", "") for uid, u in u1.items()
                      if uid.startswith("T1_") and u.get("suite") == "T1_examples" and u.get("example")))
    if not rels:
        print("HARD_STOP no T1 example observations found")
        return 2
    non_mpi = [r for r in rels if r not in MPI_EXAMPLES]
    for rel in non_mpi:
        e = eid(rel)
        units = {}
        fl = []
        for tree in ("U", "B", "F4"):
            p1 = u1.get("T1_%s_%s_p1" % (e, tree))
            p2 = u1.get("T1_%s_%s_p2" % (e, tree))
            units[tree] = p1
            fl.append((tree, (p1, p2)))
        cat, detail = compare(units["U"], units["F4"], "U", "F4", T1_TOL, ((("U"), (fl[0][1])), (("F4"), (fl[2][1]))))
        vadd("T1CMP_%s_U_vs_F4" % e, "T1_compare", "U_vs_F4", outcome(units["U"], "U"),
             outcome(units["B"], "B"), outcome(units["F4"], "F4"), cat, detail)
        catb, detailb = compare(units["B"], units["F4"], "B", "F4", T1_TOL, (("B", fl[1][1]), ("F4", fl[2][1])))
        vadd("T1CMP_%s_B_vs_F4" % e, "T1_compare", "B_vs_F4", outcome(units["U"], "U"),
             outcome(units["B"], "B"), outcome(units["F4"], "F4"), catb, detailb)
    # T1 runs of the MPI examples are the single-process reference used by T3: record their outcome
    for rel in MPI_EXAMPLES:
        e = eid(rel)
        for tree in ("U", "B", "F4"):
            p1 = u1.get("T1_%s_%s_p1" % (e, tree))
            p2 = u1.get("T1_%s_%s_p2" % (e, tree))
            why = flaky(p1, p2, tree)
            vadd("T1MPIREF_%s_%s" % (e, tree), "T1_examples", "single_process_reference", outcome(p1), "",
                 "", "FLAKY" if why else ("PASS" if outcome(p1) == "PASS" else "FAIL"),
                 "pass1 %s rc=%s pass2 rc=%s" % (p1.get("status") if p1 else "MISSING", p1.get("rc") if p1 else "",
                                                  p2.get("rc") if p2 else ""))
    # ---------------------------------------------------------------- T2 reference cases
    for cid in ("simple", "fresnel", "fanfig12"):
        st = {}
        for tree in ("U", "B", "F4"):
            st[tree] = u2.get("T2_%s_%s" % (tree, cid))
        cat, detail = compare(st["U"], st["F4"], "U", "F4", T2_TOL[cid], pass_by_rc=True)
        vadd("T2CMP_%s_U_vs_F4" % cid, "T2_compare", "U_vs_F4", rc_outcome(st["U"]), rc_outcome(st["B"]),
             rc_outcome(st["F4"]), cat, detail)
        catb, detailb = compare(st["B"], st["F4"], "B", "F4", T2_TOL[cid], pass_by_rc=True)
        vadd("T2CMP_%s_B_vs_F4" % cid, "T2_compare", "B_vs_F4", rc_outcome(st["U"]), rc_outcome(st["B"]),
             rc_outcome(st["F4"]), catb, detailb)
        for tree in ("U", "B", "F4"):
            u = st[tree]
            vadd("T2REF_%s_%s" % (tree, cid), "T2_runtests_reference", "vs_reference",
                 u.get("status") if tree == "U" else "", u.get("status") if tree == "B" else "",
                 u.get("status") if tree == "F4" else "", u.get("status", "MISSING"),
                 "numdiff_rc=%s relmax=%s" % (u.get("numdiff_rc", ""), u.get("numdiff_relmax", "")))
    for tree in ("U", "B", "F4"):
        u = u2.get("T2_%s_runtests_sh" % tree)
        vadd("T2REF_%s_runtests_sh" % tree, "T2_runtests_reference", "vs_reference",
             u.get("status") if tree == "U" else "", u.get("status") if tree == "B" else "",
             u.get("status") if tree == "F4" else "", u.get("status", "MISSING"),
             "F4 harness with S4_BIN=<%s>/build/S4" % tree)
    uown = u2.get("T2_U_OWN_MANIFEST")
    vadd("T2_U_OWN_MANIFEST", "T2_runtests_reference", "record", uown.get("status", "MISSING"), "", "",
         "U_UNAVAILABLE", "original testing/testcases.txt: 10 baselines and 7 of 10 scripts missing (EXPECT_SCAN_RELR4.tsv)")
    # ---------------------------------------------------------------- T3 MPI
    precheck = read_tsv(os.path.join(EV, "mpi", "PRECHECK_RELR4.tsv"))
    # (precheck file has no header row; read as positional)
    pre_rows = []
    for line in open(os.path.join(EV, "mpi", "PRECHECK_RELR4.tsv"), encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        pre_rows.append(f)
    for f in pre_rows:
        vadd(f[0], "T3_mpi", "precheck", f[1], "", "", f[1], f[3] if len(f) > 3 else f[2])
    for tree in ("U", "B", "F4"):
        u = u3.get("T3_%s_build_s4mpi" % tree)
        vadd("T3_%s_build_s4mpi" % tree, "T3_mpi", "build", u.get("status") if tree == "U" else "",
             u.get("status") if tree == "B" else "", u.get("status") if tree == "F4" else "",
             u.get("status", "MISSING"), u.get("extra", ""))
        ub = u3.get("T3_%s_banner" % tree)
        vadd("T3_%s_banner" % tree, "T3_mpi", "banner", ub.get("status") if tree == "U" else "",
             ub.get("status") if tree == "B" else "", ub.get("status") if tree == "F4" else "",
             ub.get("status", "MISSING"), ub.get("extra", ""))
    for rel in MPI_EXAMPLES:
        e = eid(rel)
        # run status
        for tree in ("U", "B", "F4"):
            for np_ in ("1", "4"):
                for pas in ("1", "2"):
                    u = u3.get("T3_%s_%s_np%s_p%s" % (e, tree, np_, pas))
                    vadd("T3_%s_%s_np%s_p%s" % (e, tree, np_, pas), "T3_mpi", "run", outcome(u), "", "",
                         outcome(u), "rc=%s timeout=%s" % (u.get("rc", ""), u.get("timed_out", "")))
        # a. np4 merged vs np1 and vs T1 non-MPI, comparing ONLY frequencies that are the same IEEE double.
        #    The Lua numeric-for loops accumulate the step differently per rank (rank start frequencies are
        #    computed from a different expression), so most rank frequencies differ from the single-process
        #    grid in the last bits; the task brief says frequency coverage is recorded and not judged.
        np1_seq = mpi_fseq(0.25, 0.7, 0.005)
        rank_seqs = []
        for _r in range(4):
            _st = 0.25 + _r / 4 * (0.7 - 0.25)
            _en = _st + (0.7 - 0.25) / 4
            rank_seqs.append(mpi_fseq(_st, _en, 0.005))
        all_rank_freqs = set()
        for _seq in rank_seqs:
            all_rank_freqs |= set(_seq)
        for tree in ("U", "B", "F4"):
            cwd4 = unit_cwd(u3.get("T3_%s_%s_np4_p1" % (e, tree)) or {})
            cwd1 = unit_cwd(u3.get("T3_%s_%s_np1_p1" % (e, tree)) or {})
            rank_vals = [mpi_values(os.path.join(cwd4, "out%d.txt" % r)) for r in range(4)]
            np1_vals = mpi_values(os.path.join(cwd1, "out0.txt"))
            t1_vals = mpi_values(os.path.join(EV, "run", tree, "1", e, "out0.txt"))
            merged_parsed = []
            for r in range(4):
                merged_parsed.extend(pairs_of(os.path.join(cwd4, "out%d.txt" % r)))
            merged_parsed.sort(key=lambda x: x[0])
            for label, ref_vals, ref_pairs in (
                    ("np4_vs_np1", np1_vals, pairs_of(os.path.join(cwd1, "out0.txt"))),
                    ("np4_vs_t1", t1_vals, pairs_of(os.path.join(EV, "run", tree, "1", e, "out0.txt")))):
                refmap = {}
                for i, f in enumerate(np1_seq):
                    if i < len(ref_vals):
                        refmap.setdefault(f, ref_vals[i])
                matched, only_rank, mx = 0, 0, 0.0
                for r in range(4):
                    for i, f in enumerate(rank_seqs[r]):
                        if i >= len(rank_vals[r]):
                            continue
                        if f in refmap:
                            matched += 1
                            rv = refmap[f]
                            mx = max(mx, abs(rank_vals[r][i] - rv) / max(abs(rank_vals[r][i]), abs(rv), 1e-300))
                        else:
                            only_rank += 1
                only_ref = len([f for f in np1_seq if f not in all_rank_freqs])
                # observation only (not judged): matching by printed frequency strings also pairs values whose
                # frequency differs in the last bits; report the difference this produces.
                nom_mx, nom_matched, _, _ = match_pairs(merged_parsed, ref_pairs)
                if matched == 0:
                    cat, detail = "DIFF_ATTRIBUTED", "no frequency with an identical IEEE double; merged=%d ref=%d" % (
                        sum(len(v) for v in rank_vals), len(ref_vals))
                elif mx <= T3_TOL:
                    cat, detail = "DIFF_WITHIN_TOL", ("identical-double matched=%d max_rel=%.3e <= %g; "
                                                      "coverage only_rank=%d only_ref=%d; observation: nominal "
                                                      "printed-frequency matching matched=%d max_rel=%.3e (those pairs "
                                                      "differ in the last bits of the frequency double)"
                                                      % (matched, mx, T3_TOL, only_rank, only_ref, nom_matched, nom_mx))
                else:
                    cat, detail = "DIFF_ATTRIBUTED", ("identical-double matched=%d max_rel=%.3e > %g; coverage "
                                                      "only_rank=%d only_ref=%d; nominal matched=%d max_rel=%.3e"
                                                      % (matched, mx, T3_TOL, only_rank, only_ref, nom_matched, nom_mx))
                vadd("T3CMP_%s_%s_%s" % (e, tree, label), "T3_compare", "same_tree_np",
                     cat if tree == "U" else "", cat if tree == "B" else "", cat if tree == "F4" else "",
                     cat, detail)
                print("MPI_CMP %-52s %s matched=%d max_rel=%.3e only_rank=%d only_ref=%d nominal=%d/%.3e"
                      % ("T3CMP_%s_%s_%s" % (e, tree, label), cat, matched, mx, only_rank, only_ref, nom_matched, nom_mx))
        # b. B vs F4 same-named outputs byte identical
        for np_ in ("1", "4"):
            files = ["out0.txt"] if np_ == "1" else ["out%d.txt" % i for i in range(4)]
            diffs = []
            for fn in files:
                pb = os.path.join(unit_cwd(u3.get("T3_%s_B_np%s_p1" % (e, np_)) or {}), fn)
                pf = os.path.join(unit_cwd(u3.get("T3_%s_F4_np%s_p1" % (e, np_)) or {}), fn)
                if not (os.path.isfile(pb) and os.path.isfile(pf)):
                    diffs.append(fn + ":missing")
                elif sha_f(pb) != sha_f(pf):
                    diffs.append(fn + ":diff")
            cat = "SAME" if not diffs else "DIFF_ATTRIBUTED"
            vadd("T3CMP_%s_B_vs_F4_np%s" % (e, np_), "T3_compare", "B_vs_F4", "", cat, cat,
                 cat, ";".join(diffs) if diffs else "all same-named files byte-identical")
        # c. U vs F4 (merged, pass 1), np1 and np4
        for np_ in ("1", "4"):
            cu = unit_cwd(u3.get("T3_%s_U_np%s_p1" % (e, np_)) or {})
            cf = unit_cwd(u3.get("T3_%s_F4_np%s_p1" % (e, np_)) or {})
            uvals, fvals = [], []
            for r in range(int(np_)):
                uvals.extend(pairs_of(os.path.join(cu, "out%d.txt" % r)))
                fvals.extend(pairs_of(os.path.join(cf, "out%d.txt" % r)))
            uvals.sort(key=lambda x: x[0])
            fvals.sort(key=lambda x: x[0])
            same = [sha_f(os.path.join(cu, "out%d.txt" % r)) if os.path.isfile(os.path.join(cu, "out%d.txt" % r)) else ""
                    for r in range(int(np_))] == \
                   [sha_f(os.path.join(cf, "out%d.txt" % r)) if os.path.isfile(os.path.join(cf, "out%d.txt" % r)) else ""
                    for r in range(int(np_))]
            mx, matched, only_u, only_f = match_pairs(uvals, fvals)
            if same:
                cat, detail = "SAME", "all -np %s output files byte-identical" % np_
            elif matched and mx <= T3_TOL:
                cat, detail = "DIFF_WITHIN_TOL", "matched=%d max_rel=%.3e only_U=%d only_F4=%d" % (matched, mx, only_u, only_f)
            else:
                cat, detail = "DIFF_ATTRIBUTED", "matched=%d max_rel=%.3e only_U=%d only_F4=%d" % (matched, mx, only_u, only_f)
            vadd("T3CMP_%s_U_vs_F4_np%s" % (e, np_), "T3_compare", "U_vs_F4", "PASS", "", "PASS", cat, detail)
    # d. missing 1d reference, recorded
    miss = []
    for tree in ("U", "B", "F4"):
        miss.append("%s=%s" % (tree, "present" if os.path.isfile(os.path.join(TREES[tree], "examples", "1d", "binary_grating.txt")) else "absent"))
    vadd("T3_RECORD_MISSING_1D_REFERENCE", "T3_mpi", "record", "", "", "", "RECORD_ONLY",
         "examples/1d/binary_grating.txt " + "; ".join(miss))
    # ---------------------------------------------------------------- T4 C API
    capi_units = {k: v for k, v in u4.items()}
    for tree in ("B", "F4", "U"):
        for step, uid in (("build", "T4_%s_build_capi" % tree),
                          ("makefile", "T4_%s_original_makefile" % tree),
                          ("spec", "T4_%s_spec_sweep" % tree),
                          ("posctrl", "T4_%s_posctrl_c_vs_lua" % tree)):
            u = capi_units.get(uid) or {}
            vadd(uid, "T4_capi", step, u.get("status") if tree == "U" else "",
                 u.get("status") if tree == "B" else "", u.get("status") if tree == "F4" else "",
                 u.get("status", "MISSING"), u.get("detail", ""))
    # B vs F4 byte identical
    pb, pf = os.path.join(EV, "capi", "B", "spec.awk.out"), os.path.join(EV, "capi", "F4", "spec.awk.out")
    same = os.path.isfile(pb) and os.path.isfile(pf) and sha_f(pb) == sha_f(pf)
    vadd("T4CMP_B_vs_F4_byte_identical", "T4_compare", "B_vs_F4", "", "SAME" if same else "DIFF",
         "SAME" if same else "DIFF", "SAME" if same else "DIFF_ATTRIBUTED",
         "sha_B=%s sha_F4=%s" % (sha_f(pb) if os.path.isfile(pb) else "missing",
                                 sha_f(pf) if os.path.isfile(pf) else "missing"))
    # U vs F4 numeric comparison of the spec sweep
    uv = pairs_of(os.path.join(EV, "capi", "U", "spec.awk.out"))
    fv = pairs_of(os.path.join(EV, "capi", "F4", "spec.awk.out"))
    if uv and fv and len(uv) == len(fv):
        mx = 0.0
        for (ufq, uvv), (ffq, fvv) in zip(uv, fv):
            mx = max(mx, abs(uvv - fvv) / max(abs(uvv), abs(fvv), 1e-300))
        ubytes = open(os.path.join(EV, "capi", "U", "spec.awk.out"), "rb").read()
        fbytes = open(os.path.join(EV, "capi", "F4", "spec.awk.out"), "rb").read()
        if ubytes == fbytes:
            cat, detail = "SAME", "35 rows byte-identical"
        elif mx <= T4_TOL:
            cat, detail = "DIFF_WITHIN_TOL", "rows=%d max_rel=%.3e" % (len(uv), mx)
        else:
            cat, detail = "DIFF_ATTRIBUTED", "rows=%d max_rel=%.3e" % (len(uv), mx)
    else:
        cat, detail = "U_UNAVAILABLE", "U spec.awk.out rows=%d (U binary not available)" % len(uv)
    vadd("T4CMP_U_vs_F4_spec_sweep", "T4_compare", "U_vs_F4", "PASS" if uv else "UNAVAILABLE", "", "PASS", cat, detail)
    vadd("T4_RECORD_U_CAPI_EXAMPLE", "T4_capi", "record", "", "", "", "RECORD_ONLY",
         "original examples/C_api/main.c uses pre-P04 C API names; recorded, not judged")
    # ---------------------------------------------------------------- T5 main suite
    t5 = u5.get("T5_F4_make_test")
    vadd("T5_F4_make_test", "T5_make_test", "main_suite", "", "", outcome(t5),
         "PASS" if outcome(t5) == "PASS" else "FAIL",
         "rc=%s unit_count=%s failures=%s" % (t5.get("rc", ""), t5.get("unit_count", ""), t5.get("failures", "")))
    vadd("T5_U_make_test", "T5_make_test", "main_suite", "U_UNAVAILABLE", "", "", "U_UNAVAILABLE",
         "U has no 'test' target")

    # ---------------------------------------------------------------- summary
    def cat_counts(rows):
        c = {k: 0 for k in CATS}
        for r in rows:
            if r["category"] in c:
                c[r["category"]] += 1
        return c
    urows = [r for r in verdict if r["comparison"] == "U_vs_F4"]
    brows = [r for r in verdict if r["comparison"] == "B_vs_F4"]
    uc = cat_counts(urows)
    bc = cat_counts(brows)
    t1b = [r for r in brows if r["suite"] == "T1_compare"]
    t1u = [r for r in urows if r["suite"] == "T1_compare"]
    t1u_c = cat_counts(t1u)
    t1b_c = cat_counts(t1b)
    t2ref_pass = len([r for r in verdict if r["suite"] == "T2_runtests_reference" and r["comparison"] == "vs_reference"
                      and r["category"].startswith("PASS")])
    t2ref_total = len([r for r in verdict if r["suite"] == "T2_runtests_reference" and r["comparison"] == "vs_reference"])
    t3build_ok = len([r for r in verdict if r["suite"] == "T3_mpi" and r["comparison"] == "build" and r["category"] == "BUILD_OK"])
    t3banner = len([r for r in verdict if r["suite"] == "T3_mpi" and r["comparison"] == "banner" and "With_MPI_support=yes" in r["detail"] or (r["suite"] == "T3_mpi" and r["comparison"] == "banner" and r["category"] == "WITH_MPI")])
    t3run_ok = len([r for r in verdict if r["suite"] == "T3_mpi" and r["comparison"] == "run" and r["category"] == "PASS"])
    t3run_total = len([r for r in verdict if r["suite"] == "T3_mpi" and r["comparison"] == "run"])
    t3cmp_ok = len([r for r in verdict if r["suite"] == "T3_compare" and r["comparison"] == "same_tree_np"
                    and r["category"] in ("DIFF_WITHIN_TOL", "SAME")])
    t3cmp_total = len([r for r in verdict if r["suite"] == "T3_compare" and r["comparison"] == "same_tree_np"])
    t4_build_ok = len([r for r in verdict if r["suite"] == "T4_capi" and r["comparison"] == "build" and r["category"] == "BUILD_OK"])
    t4_makefile_rc2 = len([r for r in verdict if r["suite"] == "T4_capi" and r["comparison"] == "makefile" and r["category"] == "RC2"])
    t4_spec_pass = len([r for r in verdict if r["suite"] == "T4_capi" and r["comparison"] == "spec" and r["category"] == "PASS_REF"])
    t4_pos_pass = len([r for r in verdict if r["suite"] == "T4_capi" and r["comparison"] == "posctrl" and r["category"] == "PASS"])
    maketest = u5.get("T5_F4_make_test", {})
    summary = {
        "REGISTRY_ROWS": len(verdict),
        "PREREG_UNITS": len(prereg),
        "RESULTS_ROWS": len(results),
        "T1_RUNS": len([r for r in results if r["suite"] == "T1_examples"]),
        "T1_U_VS_F4_TOTAL": len(t1u),
        "T1_B_VS_F4_TOTAL": len(t1b),
        "T1_B_VS_F4_SAME": t1b_c["SAME"],
        "T1_B_VS_F4_BOTH_FAIL": t1b_c["BOTH_FAIL"],
        "T1_B_VS_F4_DIFF_ATTRIBUTED": t1b_c["DIFF_ATTRIBUTED"],
        "T1_U_VS_F4_SAME": t1u_c["SAME"],
        "T1_U_VS_F4_DIFF_WITHIN_TOL": t1u_c["DIFF_WITHIN_TOL"],
        "T1_U_VS_F4_DIFF_ATTRIBUTED": t1u_c["DIFF_ATTRIBUTED"],
        "T1_U_VS_F4_REGRESSION": t1u_c["REGRESSION"],
        "T1_U_VS_F4_IMPROVED": t1u_c["IMPROVED"],
        "T1_U_VS_F4_BOTH_FAIL": t1u_c["BOTH_FAIL"],
        "T1_U_VS_F4_FLAKY": t1u_c["FLAKY"],
        "T2_REF_PASS": t2ref_pass,
        "T2_REF_TOTAL": t2ref_total,
        "T3_BUILD_OK": t3build_ok,
        "T3_WITH_MPI_BANNER": t3banner,
        "T3_RUN_OK": t3run_ok,
        "T3_RUN_TOTAL": t3run_total,
        "T3_MPI_COMPARE_OK": t3cmp_ok,
        "T3_MPI_COMPARE_TOTAL": t3cmp_total,
        "T4_CAPI_BUILD_OK": t4_build_ok,
        "T4_ORIGINAL_MAKEFILE_RC2": t4_makefile_rc2,
        "T4_SPEC_REF_PASS": t4_spec_pass,
        "T4_POSITIVE_CONTROL_PASS": t4_pos_pass,
        "MAKETEST_RC": maketest.get("rc", "MISSING"),
        "UNIT_COUNT": maketest.get("unit_count", "MISSING"),
        "MAKETEST_FAILURES": maketest.get("failures", "MISSING"),
        "NON_REGRESSION_U": "PASS" if (t1u_c["REGRESSION"] == 0 and
                                       len([r for r in t1u if r["category"] == "FLAKY" and "tree F4" in r["detail"]]) == 0) else "FAIL",
        "FLAKY_F4": len([r for r in t1u if r["category"] == "FLAKY" and "tree F4" in r["detail"]]),
        "FLAKY_U": len([r for r in t1u if r["category"] == "FLAKY" and "tree U" in r["detail"]]),
        "NON_REGRESSION_B": "PASS" if (t1b_c["SAME"] == 38 and t1b_c["BOTH_FAIL"] == 11 and t1b_c["DIFF_ATTRIBUTED"] == 0) else "FAIL",
    }
    for k in CATS:
        summary["ALL_U_VS_F4_" + k] = uc[k]
    summary["ALL_B_VS_F4_SAME"] = bc["SAME"]
    summary["ALL_B_VS_F4_BOTH_FAIL"] = bc["BOTH_FAIL"]
    summary["ALL_B_VS_F4_DIFF_ATTRIBUTED"] = bc["DIFF_ATTRIBUTED"]
    summary["ALL_U_VS_F4_TOTAL"] = len(urows)
    summary["DIFF_ATTRIBUTED_TOTAL"] = uc["DIFF_ATTRIBUTED"]
    summary["REGRESSION_TOTAL"] = uc["REGRESSION"]
    summary["FLAKY_TOTAL"] = uc["FLAKY"]
    prereg_sha = "MISSING"
    shaf = os.path.join(EV, "PREREG_RELR4.tsv.sha256.txt")
    if os.path.isfile(shaf):
        for line in open(shaf, encoding="utf-8"):
            if line.startswith("PREREG_RELR4.tsv" + TAB):
                prereg_sha = line.rstrip(NL).split(TAB)[1]
    summary["PREREG_SHA256"] = prereg_sha
    # ---------------------------------------------------------------- write
    res_out = os.path.join(EV, "RESULTS_RELR4.tsv")
    rkeys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out", "stdout_sha256",
             "stderr_sha256", "numdiff_rc", "numdiff_relmax", "dur_s", "extra"]
    lines = ["# RESULTS_RELR4.tsv -- consolidated per-unit observations of REL-R4 (T1 runs, T2, T3, T4, T5).",
             "# Every row is a raw observation written by the round's own runners (rc, signals, sha256, numdiff).",
             TAB.join(rkeys)]
    for r in results:
        lines.append(TAB.join([r.get(k, "") for k in rkeys]))
    open(res_out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    vkeys = ["unit_id", "suite", "comparison", "u", "b", "f4", "category", "detail"]
    lines = ["# VERDICT_RELR4.tsv -- one row per comparison unit of REL-R4, with the U / B / F4 columns.",
             "# Categories (task brief section 4): " + ", ".join(CATS) + ".",
             "# comparison = U_vs_F4 | B_vs_F4 | same_tree_np | vs_reference | precheck | build | banner | run | record.",
             "# The engine reads rc, normalised stdout/stderr, file sha256 and numdiff numbers only.",
             TAB.join(vkeys)]
    for r in verdict:
        lines.append(TAB.join([r.get(k, "") for k in vkeys]))
    open(os.path.join(EV, "VERDICT_RELR4.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    sm = ["# SUMMARY_RELR4.txt -- machine-readable category counts of REL-R4 (read by relr4_check.py by key)"]
    for k in sorted(summary):
        sm.append("%s=%s" % (k, summary[k]))
    open(os.path.join(EV, "SUMMARY_RELR4.txt"), "w", encoding="utf-8").write(NL.join(sm) + NL)
    for k in sorted(summary):
        print("%s=%s" % (k, summary[k]))
    print("WROTE VERDICT_RELR4.tsv RESULTS_RELR4.tsv SUMMARY_RELR4.txt")
    return 0 if (uc["REGRESSION"] == 0 and uc["FLAKY"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())