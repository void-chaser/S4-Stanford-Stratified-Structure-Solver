#!/usr/bin/env python3
# s5r5_gate_posctrl.py -- on-disk mutation positive control for EVERY check of gate_check_s5r5.py (task brief
# section 6). Each case runs the FORMAL gate script in --only single-check mode: the clean staging data must
# PASS and a tampered copy on disk must FAIL. Nothing here lowers a check or touches the real artifacts.
# usage: s5r5_gate_posctrl.py posctrl
import os, sys, re, shutil, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
REG4 = os.path.join(P05, "registries/s5r4")
GATE = os.path.join(REPO, "testing/d003/stage_s5r5/gate_check_s5r5.py")
STAGE = os.path.join(EV, "shakedown")
STAGE_P05 = os.path.join(STAGE, "p05")
STAGE_EV = os.path.join(STAGE, "ev")
BASE = os.path.join(EV, "posctrl/gate")
RUNBASE = os.path.join(EV, "posctrl/gate_out")
TAB = chr(9)
NL = chr(10)


def rd(p):
    return open(p, encoding="utf-8").read()


def wr(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(t)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def gate_names():
    src = rd(GATE)
    return re.findall(r'add\("([A-Z0-9_]+)"', src)


def run_only(name, ev, p05, extra, tag):
    out = os.path.join(RUNBASE, name + "_" + tag + ".txt")
    os.makedirs(RUNBASE, exist_ok=True)
    cmd = [sys.executable, "-I", "-B", GATE, "end", "--only", name, "--ev-root", ev, "--p05-root", p05,
           "--out", out] + extra
    subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if not os.path.isfile(out):
        return "NO_OUTPUT"
    res = "NO_LINE"
    for line in rd(out).splitlines():
        f = line.split(TAB)
        if len(f) >= 2 and f[1] == name and f[0] in ("PASS", "FAIL"):
            res = f[0]
    return res


def cp_tree(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def tamper_p05(name, mut):
    dst = os.path.join(BASE, name, "p05")
    cp_tree(STAGE_P05, dst)
    mut(dst)
    return dst


def tamper_ev(name, mut):
    dst = os.path.join(BASE, name, "ev")
    cp_tree(STAGE_EV, dst)
    mut(dst)
    return dst


def edge(root, rel):
    return os.path.join(root, rel)


def edit_text(path, fn):
    wr(path, fn(rd(path)))


def main():
    names = gate_names()
    if os.path.isdir(BASE):
        shutil.rmtree(BASE)
    os.makedirs(BASE)
    if os.path.isdir(RUNBASE):
        shutil.rmtree(RUNBASE)
    os.makedirs(RUNBASE)
    clean_extra = []
    results = []

    def case(name, tamper, clean_ev=None, clean_extra=None, tamper_cleanup=None):
        rc = run_only(name, clean_ev or STAGE_EV, STAGE_P05, clean_extra or [], "clean")
        ev = STAGE_EV
        p05 = STAGE_P05
        extra = []
        try:
            got = tamper()
            if got:
                evo, p05o, extrao = got
                ev = evo or STAGE_EV
                p05 = p05o or STAGE_P05
                extra = extrao or []
            rt = run_only(name, ev, p05, extra, "tamper")
        finally:
            if tamper_cleanup:
                tamper_cleanup()
        ok = (rc == "PASS" and rt == "FAIL")
        results.append((name, ok, rc, rt))
        print(("PASS" if ok else "FAIL") + TAB + "posctrl_" + name + TAB + "clean=" + rc + " tampered=" + rt)

    # ---- git / repo facts (override through a facts file; the clean side uses the real work tree)
    def facts_case(name, key, bad):
        def mut():
            d = os.path.join(BASE, name)
            wr(os.path.join(d, "facts.txt"), key + "=" + bad + NL)
            return (None, None, ["--facts", os.path.join(d, "facts.txt")])
        return mut
    case("BRANCH_IS_EXPECTED", facts_case("BRANCH_IS_EXPECTED", "BRANCH", "other-branch"))
    case("HEAD_S4_TREE_EQ_F4", facts_case("HEAD_S4_TREE_EQ_F4", "HEAD_S4", "0" * 40))

    def mut_head_commits():
        d = os.path.join(BASE, "HEAD_R5_I_COMMITS_ONLY")
        wr(os.path.join(d, "facts.txt"), "BASE_ANCESTOR=yes" + NL + "COMMITS_POST_BASE=random commit subject" + NL)
        return (None, None, ["--facts", os.path.join(d, "facts.txt")])
    # clean side simulates the POST-commit-(i) git state (one "P05-S5 R5 (i)" commit) so the formal branch is
    # exercised before commit (i); the real pre-commit state (0 commits) is exercised by the full staging run.
    head_clean = os.path.join(BASE, "HEAD_R5_I_COMMITS_ONLY", "clean_facts.txt")
    wr(head_clean, "BASE_ANCESTOR=yes" + NL
       + "COMMITS_POST_BASE=P05-S5 R5 (i): rehearsal of the formal post-commit state" + NL)
    case("HEAD_R5_I_COMMITS_ONLY", mut_head_commits, clean_extra=["--facts", head_clean])

    def mut_judge():
        d = os.path.join(BASE, "JUDGE_SHA256")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "judge_d003.py")
        wr(p, rd(os.path.join(REPO, "testing/d003/judge_d003.py")) + "# tampered" + NL)
        return (None, None, ["--judge-path", p])
    case("JUDGE_SHA256", mut_judge)
    case("S4_DIR_ZERO_MODIFICATION", facts_case("S4_DIR_ZERO_MODIFICATION", "S4_DIFF", "S4/rcwa.cpp"))

    def mut_status():
        d = os.path.join(BASE, "MODIFIED_TRACKED_FILES_WITHIN_ALLOW_PREFIXES")
        p = os.path.join(d, "status.txt")
        wr(p, " M S4/rcwa.cpp" + NL)
        return (None, None, ["--status-file", p])
    # clean side uses the expected POST-commit-(i) status shape (committed round files + uncommitted report
    # artifacts), so the formal branch is exercised before commit (i); the real pre-commit status is exercised
    # by the full staging run.
    status_clean = os.path.join(BASE, "MODIFIED_TRACKED_FILES_WITHIN_ALLOW_PREFIXES", "clean_status.txt")
    wr(status_clean, NL.join([
        " M checkpoints/p05/STATE.md",
        " M checkpoints/p05/registries/RULINGS.tsv",
        " M checkpoints/p05/registries/s5r2/ERRATA_S5.txt",
        "?? checkpoints/p05/P05_S5R5_REPORT.md",
        "?? checkpoints/p05/P05_S5_SIGNOFF_DRAFT_v3.md",
        "?? checkpoints/p05/registries/s5r5/"]) + NL)
    case("MODIFIED_TRACKED_FILES_WITHIN_ALLOW_PREFIXES", mut_status, clean_extra=["--status-file", status_clean])

    pyc = os.path.join(BASE, "NO_PYCACHE", "fixture")

    def cleanup_pyc():
        if os.path.isdir(pyc):
            shutil.rmtree(pyc)

    def mut_pycache():
        os.makedirs(os.path.join(pyc, "__pycache__"), exist_ok=True)
        wr(os.path.join(pyc, "__pycache__", "x.pyc"), "tampered" + NL)
        return (None, None, ["--pycache-root", pyc])
    case("NO_PYCACHE", mut_pycache, tamper_cleanup=cleanup_pyc)

    def mut_tmp(d):
        edit_text(edge(d, "TMP_SNAPSHOT_S5R5.tsv"),
                  lambda t: re.sub(r"TMP_COUNT\t\d+", "TMP_COUNT" + TAB + "999", t))
    case("TMP_SNAPSHOT_UNCHANGED", lambda: (tamper_ev("TMP_SNAPSHOT_UNCHANGED", mut_tmp), None, None))

    def tamper_sums_dir(name, src, tag):
        d = os.path.join(BASE, name, tag)
        os.makedirs(d, exist_ok=True)
        lines = rd(os.path.join(src, "SHA256SUMS.txt")).splitlines()
        out = []
        for line in lines:
            if line.startswith("#") or not line.strip():
                out.append(line)
                continue
            parts = line.split()
            if line is lines[-1] or "  " in line:
                pass
            out.append(line)
        # flip one hex digit of the first data line's sha
        for i, line in enumerate(out):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            sha = parts[0]
            parts[0] = ("0" if sha[0] != "0" else "1") + sha[1:]
            out[i] = " ".join(parts)
            break
        wr(os.path.join(d, "SHA256SUMS.txt"), NL.join(out) + NL)
        return d
    case("S5R4_EVIDENCE_SUMS_ALL_OK_941",
         lambda: (None, None, ["--s5r4-ev-root", tamper_sums_dir("S5R4_EVIDENCE_SUMS_ALL_OK_941", EV4, "ev4")]))
    case("S5R4_REGISTRY_SUMS_ALL_OK_15",
         lambda: (None, None, ["--s5r4-reg-root", tamper_sums_dir("S5R4_REGISTRY_SUMS_ALL_OK_15", REG4, "reg4")]))

    def mut_summary(key, bad):
        def mut(d):
            edit_text(edge(d, "CHECKER_SWEEP_S5R5.tsv"),
                      lambda t: re.sub("SUMMARY" + TAB + key + TAB + "[^" + NL + "]*",
                                       "SUMMARY" + TAB + key + TAB + bad, t))
        return mut
    case("CHECKER_SWEEP_ROWS_SELF_BRANCH",
         lambda: (tamper_ev("CHECKER_SWEEP_ROWS_SELF_BRANCH", mut_summary("SWEEP_ROWS", "138")), None, None))
    case("CHECKER_SWEEP_R4_GATE_SUMMARY",
         lambda: (tamper_ev("CHECKER_SWEEP_R4_GATE_SUMMARY", mut_summary("R4_FORMAL_FAILS", "0")), None, None))
    case("CHECKER_SWEEP_VACUOUS_ZERO",
         lambda: (tamper_ev("CHECKER_SWEEP_VACUOUS_ZERO", mut_summary("VACUOUS", "1")), None, None))

    def mut_rulings(fn):
        def mut(d):
            edit_text(edge(d, "registries/RULINGS.tsv"), fn)
        return mut
    case("RULINGS_PREFIX_AND_NOT_TRUNCATED",
         lambda: (None, tamper_p05("RULINGS_PREFIX_AND_NOT_TRUNCATED",
                                   mut_rulings(lambda t: ("X" if t[0] != "X" else "Y") + t[1:])), None))
    case("RULINGS_MAX_U_390",
         lambda: (None, tamper_p05("RULINGS_MAX_U_390",
                                   mut_rulings(lambda t: t + "U391" + TAB + "x" + TAB + "y" + TAB + "z" + TAB + "w" + NL)), None))
    case("RULINGS_LINES_5_FIELDS",
         lambda: (None, tamper_p05("RULINGS_LINES_5_FIELDS",
                                   mut_rulings(lambda t: t + "U399" + TAB + "x" + TAB + "y" + NL)), None))
    case("RULINGS_U386_U390_ONCE",
         lambda: (None, tamper_p05("RULINGS_U386_U390_ONCE",
                                   mut_rulings(lambda t: NL.join(l for l in t.splitlines()
                                                                 if not l.startswith("U386" + TAB)) + NL)), None))

    def mut_errata(fn):
        def mut(d):
            edit_text(edge(d, "registries/s5r2/ERRATA_S5.txt"), fn)
        return mut
    case("ERRATA_PREFIX_AND_NOT_TRUNCATED",
         lambda: (None, tamper_p05("ERRATA_PREFIX_AND_NOT_TRUNCATED",
                                   mut_errata(lambda t: ("X" if t[0] != "X" else "Y") + t[1:])), None))
    case("ERRATA_S5_LAST_IS_ES5_16",
         lambda: (None, tamper_p05("ERRATA_S5_LAST_IS_ES5_16",
                                   mut_errata(lambda t: t[:t.index("ES5-16")])), None))
    case("ERRATA_S5_HAS_ES5_15_16",
         lambda: (None, tamper_p05("ERRATA_S5_HAS_ES5_15_16",
                                   mut_errata(lambda t: NL.join(l for l in t.splitlines()
                                                                if not l.startswith("ES5-15")) + NL)), None))

    def mut_snapshot(d):
        edit_text(edge(d, "registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt"), lambda t: t + "tampered" + NL)
    case("ERRATA_R4FINAL_SNAPSHOT_SHA",
         lambda: (None, tamper_p05("ERRATA_R4FINAL_SNAPSHOT_SHA", mut_snapshot), None))

    def mut_recheck(row, col, bad):
        def mut(d):
            def f(t):
                out = []
                for line in t.splitlines():
                    fds = line.split(TAB)
                    if fds and fds[0] == row:
                        if col == "actual":
                            fds[2] = bad
                        else:
                            fds[3] = bad
                        line = TAB.join(fds)
                    out.append(line)
                return NL.join(out) + NL
            edit_text(edge(d, "RECHECK_STAGING_S5R5.tsv"), f)
        return mut
    case("RECHECK_CORRECTED_PASS",
         lambda: (tamper_ev("RECHECK_CORRECTED_PASS", mut_recheck("CORRECTED_LOGIC", "actual", "FAIL")), None, None))
    case("RECHECK_R4_ORIGINAL_NOT_STAGING",
         lambda: (tamper_ev("RECHECK_R4_ORIGINAL_NOT_STAGING", mut_recheck("R4_ORIGINAL_LOGIC", "actual", "PASS")), None, None))
    case("RECHECK_INPUT_SHA_AND_SHAKEDOWN_ROOTS",
         lambda: (tamper_ev("RECHECK_INPUT_SHA_AND_SHAKEDOWN_ROOTS", mut_recheck("FAILS_ZERO", "actual", "1")), None, None))

    def mut_pcr(d):
        edit_text(edge(d, "POSCTRL_RECHECK_STAGING_S5R5.txt"), lambda t: t.replace("(4/4)", "(3/4)"))
    case("RECHECK_POSCTRL_4_OF_4",
         lambda: (tamper_ev("RECHECK_POSCTRL_4_OF_4", mut_pcr), None, None))

    def mut_readiness_gap(d):
        edit_text(edge(d, "READINESS_S5R5.tsv"),
                  lambda t: t + TAB.join(["SUMMARY", "FORCED_GAP", "GAP", "tampered", "posctrl"]) + NL)
    case("READINESS_GAP_ZERO",
         lambda: (tamper_ev("READINESS_GAP_ZERO", mut_readiness_gap), None, None))

    def mut_readiness_sha(d):
        edit_text(edge(d, "READINESS_S5R5.tsv"),
                  lambda t: re.sub(r"STATE_SHA256=[0-9a-f]{64}", "STATE_SHA256=" + "0" * 64, t))
    case("READINESS_STATE_SHA_MATCH",
         lambda: (tamper_ev("READINESS_STATE_SHA_MATCH", mut_readiness_sha), None, None))

    def mut_readiness_mtime(d):
        p = edge(d, "READINESS_S5R5.tsv")
        p05_state = edge(STAGE_P05, "STATE.md")
        old = os.path.getmtime(p05_state) - 100
        os.utime(p, (old, old))
    case("READINESS_AFTER_FINAL_STATE",
         lambda: (tamper_ev("READINESS_AFTER_FINAL_STATE", mut_readiness_mtime), None, None))

    def mut_state_phrase(d):
        edit_text(edge(d, "STATE.md"), lambda t: t + NL + "门禁检查 PASS" + NL)
    case("STATE_NO_GATE_RESULT_PHRASES",
         lambda: (None, tamper_p05("STATE_NO_GATE_RESULT_PHRASES", mut_state_phrase), None))

    def mut_state_row(d):
        edit_text(edge(d, "STATE.md"), lambda t: t.replace("ES5-15", "ES5-XX"))
    case("STATE_S5R4_ROW_INCOMPLETE_CONSISTENT",
         lambda: (None, tamper_p05("STATE_S5R4_ROW_INCOMPLETE_CONSISTENT", mut_state_row), None))

    def mut_draft(d):
        edit_text(edge(d, "P05_S5_SIGNOFF_DRAFT_v3.md"),
                  lambda t: t.replace("FINAL_STATUS≠COMPLETE", "FINAL_STATUS different"))
    case("DRAFT_V3_UNSIGNED_DEFERRED_NO_PHRASES",
         lambda: (None, tamper_p05("DRAFT_V3_UNSIGNED_DEFERRED_NO_PHRASES", mut_draft), None))

    def mut_report(d):
        def f(t):
            marker = "## 附录 A"
            i = t.index(marker)
            return t[:i] + "门禁检查通过" + NL + t[i:]
        edit_text(edge(d, "P05_S5R5_REPORT.md"), f)
    case("REPORT_BODY_NO_GATE_RESULT_PHRASES",
         lambda: (None, tamper_p05("REPORT_BODY_NO_GATE_RESULT_PHRASES", mut_report), None))

    def mut_reg_sums(d):
        edit_text(edge(d, "registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt"), lambda t: t + "tampered" + NL)
    case("REGISTRY_S5R5_SUMS_ALL_OK",
         lambda: (None, tamper_p05("REGISTRY_S5R5_SUMS_ALL_OK", mut_reg_sums), None))

    def mut_reg_expected(d):
        def f(t):
            out = []
            done = False
            for line in t.splitlines():
                if (not done and line.strip() and not line.startswith("#") and TAB in line
                        and line.split(TAB)[0] != "rel_path"):
                    fds = line.split(TAB)
                    fds[1] = ("0" if fds[1][0] != "0" else "1") + fds[1][1:]
                    line = TAB.join(fds)
                    done = True
                out.append(line)
            return NL.join(out) + NL
        edit_text(edge(d, "registries/s5r5/REGISTRY_EXPECTED_S5R5.txt"), f)
    case("REGISTRY_S5R5_EXPECTED_AND_NO_UNLISTED",
         lambda: (None, tamper_p05("REGISTRY_S5R5_EXPECTED_AND_NO_UNLISTED", mut_reg_expected), None))

    def mut_frozen(d):
        def f(t):
            out = []
            done = False
            for line in t.splitlines():
                if not done and line.strip() and not line.startswith("#") and TAB in line:
                    fds = line.split(TAB)
                    fds[1] = ("0" if fds[1][0] != "0" else "1") + fds[1][1:]
                    line = TAB.join(fds)
                    done = True
                out.append(line)
            return NL.join(out) + NL
        edit_text(edge(d, "FROZEN_SCRIPTS_S5R5.tsv"), f)
    case("FROZEN_SCRIPTS_SHA_UNCHANGED",
         lambda: (tamper_ev("FROZEN_SCRIPTS_SHA_UNCHANGED", mut_frozen), None, None))

    def mut_posctrl_fixture(bad):
        p = os.path.join(BASE, "POSCTRL_GATE_ALL_CHECKS_COVERED")
        ev = os.path.join(p, "ev")
        os.makedirs(ev, exist_ok=True)
        wr(os.path.join(ev, "POSCTRL_GATE_S5R5.txt"),
           "# synthetic fixture for the self-referential positive-control check" + NL
           + "OVERALL_POSITIVE_CONTROL: PASS (" + bad + ")" + NL)
        return ev

    clean_ev_fixture = mut_posctrl_fixture("%d/%d" % (len(names), len(names)))
    case("POSCTRL_GATE_ALL_CHECKS_COVERED",
         lambda: (mut_posctrl_fixture("35/%d" % len(names)), None, None),
         clean_ev=clean_ev_fixture)

    # ---- aggregate
    if set(r[0] for r in results) != set(names):
        missing = sorted(set(names) - set(r[0] for r in results))
        extra = sorted(set(r[0] for r in results) - set(names))
        print("HARD_STOP posctrl coverage mismatch: missing=%s extra=%s" % (missing, extra))
        return 2
    ok_all = all(r[1] for r in results)
    out = os.path.join(EV, "POSCTRL_GATE_S5R5.txt")
    body = ["# POSCTRL_GATE_S5R5.txt -- on-disk mutation positive control of every gate_check_s5r5.py check",
            "# each case runs the formal gate script in --only mode: clean staging data must PASS, a tampered",
            "# copy under checkpoints/p05/evidence/p05-s5r5/posctrl/gate/ must FAIL. Mutations are file edits or",
            "# narrow fact/sha overrides; no check is lowered. The POSCTRL_GATE check itself uses a synthetic",
            "# two-file fixture (self-reference); the real aggregate is the last line of this file.",
            "# gate_sha256=" + sha_f(GATE) + " checks=" + str(len(names))]
    for (name, ok, rc, rt) in results:
        body.append(("PASS" if ok else "FAIL") + TAB + "posctrl_" + name + TAB
                    + "clean=" + rc + TAB + "tampered=" + rt)
    npass = sum(1 for r in results if r[1])
    body.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if ok_all else "FAIL", npass, len(results)))
    wr(out, NL.join(body) + NL)
    print("OVERALL_POSITIVE_CONTROL %s %d/%d" % ("PASS" if ok_all else "FAIL", npass, len(results)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
