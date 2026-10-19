#!/usr/bin/env python3
# relr4_attrib.py -- section 5.3 attribution of REL-R4: for every U vs F4 unit whose category is
# DIFF_ATTRIBUTED, run the same unit on the intermediate tree M (b97f639 = original + Lua/Python frontend
# fixes, before the P04/D001/D002 adoption) and classify where the difference comes from:
#   U->M   : frontend fixes (93b1c90, 182480d, b97f639)
#   M->B   : commits 963ccf1 and 5cf534c (the latter adopts D001 zgebak / D002 RNP fixes from 44f4a09)
#   B->F4  : expected 0 (D003 is output-preserving on these paths); reported if it happens
# For units with an independent reference (T2) it also reports which tree is closer to the reference.
# If an M->B attribution is found, two more intermediate trees are built to name the source commit:
#   M2 = 963ccf1 (first S4/ change after M), M3 = 5cf534c (D001/D002 adoption).  Writes ATTRIB_RELR4.tsv.
import os, sys, subprocess, hashlib, importlib.util

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TAB = chr(9)
NL = chr(10)
M_COMMIT = "b97f63989c4d8192faee119e4dbcb70ef4a27219"
M2_COMMIT = "963ccf153855734de968e6cf71477f324e33329c"
M3_COMMIT = "5cf534ce5ec223a6388d29bbb2c58f981f070241"
TOL = 1e-12

# import the verdict engine's comparison helpers (same read-only code path, no duplicated rules)
spec = importlib.util.spec_from_file_location("relr4_verdict", os.path.join(REPO, "testing/d003/stage_relr4/relr4_verdict.py"))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
TREES = V.TREES


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(path):
    return V.read_tsv(path)


def run(cmd):
    p = subprocess.run(cmd, cwd=REPO)
    return p.returncode


def tree_facts(tree):
    t = TREES[tree]
    out = {}
    for k, args in (("HEAD", ["rev-parse", "HEAD"]), ("S4", ["rev-parse", "HEAD:S4"])):
        p = subprocess.run(["git", "-C", t] + args, capture_output=True, text=True)
        out[k] = p.stdout.strip() if p.returncode == 0 else "MISSING"
    out["build_S4_sha256"] = sha_f(os.path.join(t, "build", "S4")) if os.path.isfile(os.path.join(t, "build", "S4")) else "MISSING"
    out["clean"] = "yes" if subprocess.run(["git", "-C", t, "status", "--porcelain"], capture_output=True, text=True).stdout.strip() == "" else "no"
    return out


def need_tree(commit, name):
    t = TREES[name]
    if os.path.isdir(os.path.join(t, ".git")):
        return "exists"
    os.makedirs(os.path.dirname(t), exist_ok=True)
    p = subprocess.run(["git", "clone", "--quiet", "--revision", commit, REPO, t], capture_output=True, text=True)
    if p.returncode != 0:
        return "FAILED:" + (p.stderr or p.stdout).strip().splitlines()[-1][:200]
    env = dict(os.environ)
    env["CFLAGS"] = "-Wno-error=int-conversion"
    env["TMPDIR"] = os.path.join(EV, "tmp")
    with open(os.path.join(EV, "build_logs", "%s_lua_frontend.log" % name), "w", encoding="utf-8") as fh:
        q = subprocess.run(["make", "-j16", "build/S4"], cwd=t, env=env, stdout=fh, stderr=subprocess.STDOUT)
    return "cloned+build_rc=%d" % q.returncode


def cmp2(a, b, ta, tb, tol=TOL, pass_by_rc=False):
    return V.compare(a, b, ta, tb, tol, pass_by_rc=pass_by_rc)


def main():
    verdict = read_tsv(os.path.join(EV, "VERDICT_RELR4.tsv"))
    prereg = read_tsv(os.path.join(EV, "PREREG_RELR4.tsv"))
    u1 = V.load_units("units_t1")
    u2 = V.load_units("units_t2")
    u3 = V.load_units("units_t3")
    u4 = V.load_units("units_t4")
    diff = [r for r in verdict if r["category"] == "DIFF_ATTRIBUTED" and r["comparison"] == "U_vs_F4"]
    rows = ["# ATTRIB_RELR4.tsv -- section 5.3 attribution of the REL-R4 DIFF_ATTRIBUTED units",
            "# M = b97f639 (original + Lua/Python frontend fixes; no P04/D001/D002 adoption).",
            "# M2 = 963ccf1 (first S4/ change after M), M3 = 5cf534c (adopts D001/D002 fixes from 44f4a09).",
            "# u_vs_m / m_vs_b / b_vs_f4 are the same section-4 categories computed by the verdict engine.",
            TAB.join(["unit_id", "suite", "u_vs_m", "m_vs_m2", "m2_vs_m3", "m3_vs_b", "b_vs_f4", "source",
                      "detail", "reference_comparison"])]
    for tree in ("M",):
        f = tree_facts(tree)
        rows.append(TAB.join(["M_TREE_FACTS", "build", "", "", "", "", "", "M=%s" % M_COMMIT,
                              "HEAD=%s S4=%s build/S4=%s clone_clean=%s" % (f["HEAD"], f["S4"], f["build_S4_sha256"], f["clean"]), ""]))
    if not diff:
        rows.append(TAB.join(["NONE", "", "", "", "", "no DIFF_ATTRIBUTED unit", "nothing to attribute", ""]))
        open(os.path.join(EV, "ATTRIB_RELR4.tsv"), "w", encoding="utf-8").write(NL.join(rows) + NL)
        print("NO_DIFF_ATTRIBUTED")
        return 0
    # ensure M exists and is built
    if not os.path.isfile(os.path.join(TREES["M"], "build", "S4")):
        print("HARD_STOP M tree not built")
        return 2
    # ---------------------------------------------------------- run M for every differing unit
    m2_needed = False
    todo_t2_cases = set()
    for r in diff:
        uid = r["unit_id"]
        if uid.startswith("T1CMP_"):
            e = uid[len("T1CMP_"):-len("_U_vs_F4")]
            rel = None
            for k, v in u1.items():
                if k.startswith("T1_" + e + "_U_p1") and v.get("example"):
                    rel = v["example"]
                    break
            if rel is None:
                raise SystemExit("HARD_STOP cannot map T1 unit " + uid)
            print("M run T1 %s" % rel)
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_examples.py", "run-unit",
                 "--example", rel, "--tree", "M", "--pass", "1"])
        elif uid.startswith("T2CMP_"):
            cid = uid[len("T2CMP_"):-len("_U_vs_F4")]
            todo_t2_cases.add(cid)
            print("M run T2 %s" % cid)
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_t2.py", "case", "--tree", "M", "--case", cid])
        elif uid.startswith("T3CMP_"):
            core = uid[len("T3CMP_"):]
            np_ = core[-1]
            core = core[:-len("_np" + np_)]
            e = core[:-len("_U_vs_F4")]
            rel = None
            for k, v in u3.items():
                if k.startswith("T3_" + e + "_U_np1_p1") and v.get("extra"):
                    rel = v.get("extra").split()[-1]
                    break
            if rel is None:
                raise SystemExit("HARD_STOP cannot map T3 unit " + uid)
            print("M run T3 %s np%s" % (rel, np_))
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_mpi.py", "run",
                 "--example", rel, "--tree", "M", "--np", np_, "--pass", "1"])
        elif uid.startswith("T4CMP_"):
            print("M run T4 C API")
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_capi.py", "build", "--tree", "M"])
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_capi.py", "spec", "--tree", "M"])
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_capi.py", "posctrl", "--tree", "M"])
        else:
            print("WARN cannot attribute unit " + uid)
    if todo_t2_cases:
        run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_t2.py", "sh", "--tree", "M"])
    u2 = V.load_units("units_t2")
    u3 = V.load_units("units_t3")
    u4 = V.load_units("units_t4")
    m1 = V.load_units("units_t1")
    # ---------------------------------------------------------- build M2/M3 and run them on the differing units
    r2 = need_tree(M2_COMMIT, "M2")
    r3 = need_tree(M3_COMMIT, "M3")
    print("M2=%s M3=%s" % (r2, r3))
    for r in diff:
        uid = r["unit_id"]
        kind = uid[1]
        if kind == "1":
            e = uid[len("T1CMP_"):-len("_U_vs_F4")]
            rel = None
            for k, v in u1.items():
                if k.startswith("T1_" + e + "_U_p1") and v.get("example"):
                    rel = v["example"]
                    break
            for t in ("M2", "M3"):
                run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_examples.py", "run-unit",
                     "--example", rel, "--tree", t, "--pass", "1"])
        elif kind == "2":
            cid = uid[len("T2CMP_"):-len("_U_vs_F4")]
            for t in ("M2", "M3"):
                run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_t2.py", "case", "--tree", t, "--case", cid])
        elif kind == "3":
            core = uid[len("T3CMP_"):]
            np_ = core[-1]
            e = core[:-len("_np" + np_ + "_U_vs_F4")]
            rel = None
            for k, v in u3.items():
                if k.startswith("T3_" + e + "_U_np1_p1"):
                    rel = v["extra"].split()[-1]
                    break
            for t in ("M2", "M3"):
                run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_mpi.py", "run",
                     "--example", rel, "--tree", t, "--np", np_, "--pass", "1"])
        elif kind == "4":
            for t in ("M2", "M3"):
                run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_capi.py", "build", "--tree", t])
                run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_capi.py", "spec", "--tree", t])
    for cid in sorted(set(r["unit_id"][len("T2CMP_"):-len("_U_vs_F4")] for r in diff
                          if r["unit_id"].startswith("T2CMP_"))):
        for t in ("M2", "M3"):
            run([sys.executable, "-B", "testing/d003/stage_relr4/relr4_t2.py", "sh", "--tree", t])
    # ---------------------------------------------------------- chain classification
    # For every DIFF_ATTRIBUTED unit the whole chain U -> M -> M2 -> M3 -> B -> F4 is compared with the
    # same section-4 categories; the FIRST step that is not SAME is the source of the difference.
    u1b = V.load_units("units_t1")
    u2b = V.load_units("units_t2")
    u3b = V.load_units("units_t3")
    rows.append(TAB.join(["M2_TREE", "build", "", "", "", "M2 = 963ccf1", "built for commit-level attribution", "",
                          "", ""]))
    rows.append(TAB.join(["M3_TREE", "build", "", "", "", "M3 = 5cf534c", "built for commit-level attribution", "",
                          "", ""]))
    for r in diff:
        uid = r["unit_id"]
        kind = uid[1]
        if kind == "1":
            e = uid[len("T1CMP_"):-len("_U_vs_F4")]
            get = lambda t: u1b.get("T1_%s_%s_p1" % (e, t))
            tol = TOL
            pbrc = False
            key = e
        elif kind == "2":
            cid = uid[len("T2CMP_"):-len("_U_vs_F4")]
            get = lambda t: u2b.get("T2_%s_%s" % (t, cid))
            tol = V.T2_TOL[cid]
            pbrc = True
            key = cid
        elif kind == "3":
            core = uid[len("T3CMP_"):]
            np_ = core[-1]
            e = core[:-len("_np" + np_ + "_U_vs_F4")]
            key = e

            def merged(t):
                cwd = V.unit_cwd(u3b.get("T3_%s_%s_np%s_p1" % (e, t, np_)) or {})
                vals = []
                for i in range(int(np_)):
                    vals.extend(V.pairs_of(os.path.join(cwd, "out%d.txt" % i)))
                vals.sort(key=lambda x: x[0])
                return vals
            chain = []
            trees = ("U", "M", "M2", "M3", "B", "F4")
            for a, b in zip(trees, trees[1:]):
                mx, matched, _, _ = V.match_pairs(merged(b), merged(a))
                chain.append("SAME" if mx == 0 else ("DIFF_WITHIN_TOL" if mx <= 1e-12 else "DIFF_ATTRIBUTED"))
            src = source_of(chain)
            rows.append(TAB.join([uid, "T3", chain[0], chain[1], chain[2], chain[3], chain[4], src,
                                  "np%s chain compared at identical frequencies; U vs F4 detail: %s" % (np_, r["detail"]),
                                  ""]))
            continue
        else:
            src = "not applicable"
            rows.append(TAB.join([uid, "T4", "", "", "", "", "", src, r["detail"], ""]))
            continue
        trees = ("U", "M", "M2", "M3", "B", "F4")
        units = {t: get(t) for t in trees}
        chain = []
        for a, b in zip(trees, trees[1:]):
            cat, _ = V.compare(units[a], units[b], a, b, tol, pass_by_rc=pbrc)
            chain.append(cat)
        src = source_of(chain)
        detail = "U vs F4: " + r["detail"]
        if kind == "2":
            refs = []
            for t in trees:
                u = units[t]
                refs.append("%s relmax=%s" % (t, u.get("numdiff_relmax", "MISSING") if u else "MISSING"))
            detail += " | vs reference: " + "; ".join(refs)
        rows.append(TAB.join([uid, "T" + kind, chain[0], chain[1], chain[2], chain[3], chain[4], src,
                              detail, ""]))
    # ---------------------------------------------------------- write
    out = os.path.join(EV, "ATTRIB_RELR4.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    for line in rows:
        if line.startswith(("T1CMP_", "T2CMP_", "T3CMP_", "T4CMP_")):
            print("ATTRIB " + line.replace(TAB, " | "))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


def source_of(chain):
    if chain[0] != "SAME":
        return "U->M: frontend fixes 93b1c90/182480d/b97f639"
    if chain[1] != "SAME":
        return "M->M2: commit 963ccf1 (first S4/ change after M; P04 core/API consolidation checkpoint)"
    if chain[2] != "SAME":
        return "M2->M3: commit 5cf534c (adopts D001/D002 fixes from 44f4a09)"
    if chain[3] != "SAME":
        return "M3->B: no S4/ change between 5cf534c and B; unexpected"
    if chain[4] != "SAME":
        return "B->F4 (unexpected: D003 was expected to preserve this output)"
    return "not reproduced by the U/M/M2/M3/B/F4 chain"


if __name__ == "__main__":
    sys.exit(main())