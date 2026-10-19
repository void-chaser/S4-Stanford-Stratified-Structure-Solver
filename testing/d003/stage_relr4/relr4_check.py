#!/usr/bin/env python3
# relr4_check.py -- P05 delivery round REL-R4 gate.  ONE read-only code path for both phases: the opening
# checks are shared by --phase start and --phase end; the closing checks are only run by --phase end.
# The gate only reads files and recomputes facts; it never modifies evidence.
#   --phase start : the opening baseline, re-derived from immutable git objects at c126619 plus the start
#                   gate file (run once; writes GATE_RELR4_check_start.txt).
#   --phase end   : opening checks + closing checks.  End is PRE-RUN once (--out GATE_RELR4_pre.txt) and
#                   the FORMAL run is executed exactly once (--out GATE_RELR4_end.txt); FAILS>0 is not
#                   fixed and not re-run.
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
P05 = os.path.join(REPO, "checkpoints/p05")
TAB = chr(9)
NL = chr(10)
EXP_BASE_HEAD = "c126619c77ec1f45511cdf30145431d3d6982c4e"
EXP_F4_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_B_COMMIT = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
EXP_B_S4 = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXP_F4_COMMIT = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_U_COMMIT = "7fd00a231610bff51f5c7de5f723e3956eab7453"
EXP_U_S4 = "06553f72e93aaef1a5c9294f358a7f5afbd42bb1"
EXP_M_COMMIT = "b97f63989c4d8192faee119e4dbcb70ef4a27219"
CATS = ["SAME", "DIFF_WITHIN_TOL", "DIFF_ATTRIBUTED", "REGRESSION", "IMPROVED", "BOTH_FAIL",
        "U_UNAVAILABLE", "FLAKY"]
WHITELIST = ("testing/d003/stage_relr4/", "checkpoints/p05/STATE.md",
             "checkpoints/p05/P05_RELR4_REPORT.md", "checkpoints/p05/registries/rel-r4/",
             "checkpoints/p05/registries/RULINGS.tsv")
REPORT = os.path.join(P05, "P05_RELR4_REPORT.md")
STATE = os.path.join(P05, "STATE.md")
RULINGS = os.path.join(P05, "registries/RULINGS.tsv")
REG = os.path.join(P05, "registries/rel-r4")
CHECKS = []
CRASHED = []
EXPECT_RULING_IDS = ["U399", "U400", "U401", "U402", "U403"]
NONCAT = ("PASS", "FAIL", "BUILD_OK", "BUILD_FAIL", "WITH_MPI", "NO_MPI", "RC2", "RC1", "PASS_REF",
          "FAIL_REF", "REF_DRIFT", "RECORD_ONLY", "UNAVAILABLE", "UNRUNNABLE", "RAN", "OBSERVED")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sh(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def check(name, fn, exp):
    try:
        actual = fn()
    except Exception as exc:
        CRASHED.append((name, repr(exc)[:200]))
        actual = "EXC:" + repr(exc)[:160]
    CHECKS.append((name, exp, actual, actual == exp))


def kv_file(path):
    d = {}
    if not os.path.isfile(path):
        return d
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0] == "RECORD" and len(f) >= 3:
            k, _, v = f[2].partition("=")
            d[f[1]] = v
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


def read_summary():
    d = {}
    p = os.path.join(EV, "SUMMARY_RELR4.txt")
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        line = line.rstrip(NL)
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            d[k] = v
    return d


def tmp_snapshot():
    names = sorted(os.listdir("/tmp"))
    return len(names), hashlib.sha256((NL.join(names) + NL).encode("utf-8")).hexdigest()


def verify_sums_dir(d):
    p = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(p):
        return None
    n, bad, listed = 0, [], set()
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            bad.append("MALFORMED")
            continue
        n += 1
        name = " ".join(parts[1:])
        listed.add(name)
        fp = os.path.join(d, name)
        if not os.path.isfile(fp):
            bad.append("MISSING:" + name)
        elif sha_f(fp) != parts[0]:
            bad.append("SHA:" + name)
    unlisted = sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x))
                      and x != "SHA256SUMS.txt" and x not in listed)
    return n, bad, unlisted


def main():
    args = sys.argv[1:]
    phase = "end"
    outp = None
    if "--phase" in args:
        phase = args[args.index("--phase") + 1]
    if "--out" in args:
        outp = args[args.index("--out") + 1]
    if phase not in ("start", "end"):
        print("HARD_STOP --phase must be start or end")
        return 2
    if outp is None:
        outp = os.path.join(EV, "GATE_RELR4_check_start.txt" if phase == "start" else "GATE_RELR4_end.txt")
    rp = os.path.realpath(outp)
    if not rp.startswith(os.path.join(P05, "evidence", "p05-rel-r4") + os.sep):
        print("HARD_STOP --out must stay under the round evidence directory")
        return 2
    out_existed = os.path.exists(rp)
    formal = os.path.basename(rp) == "GATE_RELR4_end.txt"
    start_gate = os.path.join(EV, "GATE_RELR4_start.txt")
    sg = kv_file(start_gate)
    summary = read_summary()
    prereg = read_tsv(os.path.join(EV, "PREREG_RELR4.tsv"))

    # ================================================================ opening checks (both phases)
    check("START_GATE_EXISTS", lambda: "present" if os.path.isfile(start_gate) else "absent", "present")
    check("START_GATE_FAILS_ZERO",
          lambda: [l for l in open(start_gate, encoding="utf-8").read().splitlines() if l.startswith("FAILS=")][-1],
          "FAILS=0")
    check("START_GATE_HEAD", lambda: sg.get("HEAD"), EXP_BASE_HEAD)
    check("START_GATE_HEAD_S4", lambda: sg.get("HEAD_S4"), EXP_F4_S4)
    check("START_GATE_JUDGE", lambda: sg.get("JUDGE_SHA256"), EXP_JUDGE)
    check("START_GATE_RULINGS_LAST", lambda: sg.get("RULINGS_LAST_ID"), "U398")
    check("JUDGE_SHA256", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    check("BASE_HEAD_IS_ANCESTOR",
          lambda: str(sh(["git", "merge-base", "--is-ancestor", EXP_BASE_HEAD, "HEAD"]).returncode), "0")
    for name, commit, s4 in (("B", EXP_B_COMMIT, EXP_B_S4), ("F4", EXP_F4_COMMIT, EXP_F4_S4),
                             ("U", EXP_U_COMMIT, EXP_U_S4), ("M", EXP_M_COMMIT, None)):
        check("COMMIT_%s_LOCAL" % name, lambda c=commit: str(sh(["git", "cat-file", "-t", c]).returncode), "0")
        if s4:
            check("COMMIT_%s_S4" % name, lambda c=commit: sh(["git", "rev-parse", c + ":S4"]).stdout.strip(), s4)

    def zero_changes(paths):
        d = sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD", "--"] + paths).stdout.strip()
        st = sh(["git", "status", "--porcelain", "-uall", "--"] + paths).stdout.strip()
        return "clean" if (d == "" and st == "") else ("diff=" + d[:100] + " status=" + st[:100])
    check("S4_ZERO_CHANGES", lambda: zero_changes(["S4"]), "clean")
    check("EXAMPLES_AND_MAKEFILE_ZERO_CHANGES", lambda: zero_changes(["examples", "Makefile"]), "clean")

    def clone_facts(path):
        p = os.path.join(EV, *path)
        return (sh(["git", "-C", p, "rev-parse", "HEAD"]).stdout.strip(),
                sh(["git", "-C", p, "rev-parse", "HEAD:S4"]).stdout.strip())
    check("CLONE_U_HEAD", lambda: clone_facts(("upstream", "S4"))[0], EXP_U_COMMIT)
    check("CLONE_U_S4", lambda: clone_facts(("upstream", "S4"))[1], EXP_U_S4)
    check("CLONE_B_HEAD", lambda: clone_facts(("trees", "B"))[0], EXP_B_COMMIT)
    check("CLONE_B_S4", lambda: clone_facts(("trees", "B"))[1], EXP_B_S4)
    check("CLONE_F4_HEAD", lambda: clone_facts(("trees", "F4"))[0], EXP_F4_COMMIT)
    check("CLONE_F4_S4", lambda: clone_facts(("trees", "F4"))[1], EXP_F4_S4)
    check("CLONE_M_HEAD", lambda: clone_facts(("trees", "M"))[0], EXP_M_COMMIT)
    trees = read_tsv(os.path.join(EV, "TREES_RELR4.tsv"))
    check("TREES_TSV_ROWS", lambda: str(len(trees)), "3")
    check("TREES_ALL_MATCH", lambda: ",".join(sorted(r["tree"] + "=" + r["match"] for r in trees)),
          "B=YES,F4=YES,U=YES")

    shaf = os.path.join(EV, "PREREG_RELR4.tsv.sha256.txt")
    recorded = "MISSING"
    if os.path.isfile(shaf):
        for line in open(shaf, encoding="utf-8"):
            if line.startswith("PREREG_RELR4.tsv" + TAB):
                recorded = line.rstrip(NL).split(TAB)[1]
    check("PREREG_SHA_MATCHES_RECORD", lambda: sha_f(os.path.join(EV, "PREREG_RELR4.tsv")), recorded)
    check("PREREG_ROWS", lambda: str(len(prereg)), "493")
    check("PREREG_T1_RUN_UNITS",
          lambda: str(len([r for r in prereg if r["suite"] == "T1_examples"])), "306")

    rb = open(RULINGS, "rb").read() if os.path.isfile(RULINGS) else b""
    base_sha = sg.get("RULINGS_SHA256", "MISSING")
    base_bytes = int(sg.get("RULINGS_BYTES", "-1"))
    check("RULINGS_OLD_PREFIX_UNCHANGED", lambda: hashlib.sha256(rb[:base_bytes]).hexdigest(), base_sha)

    t_n, t_sha = tmp_snapshot()
    check("TMP_SNAPSHOT_SAME_AS_START", lambda: "%d %s" % (t_n, t_sha),
          "%s %s" % (sg.get("TMP_COUNT"), sg.get("TMP_SHA256")))

    # ================================================================ closing checks (--phase end only)
    if phase == "end":
        rlines = [l for l in rb.decode("utf-8").splitlines() if l.strip()]
        check("RULINGS_ROWS", lambda: str(len(rlines)), str(int(sg.get("RULINGS_ROWS", "-5")) + 5))
        check("RULINGS_LAST_ID", lambda: rlines[-1].split(TAB)[0], "U403")
        check("RULINGS_APPENDED_IDS", lambda: ",".join(l.split(TAB)[0] for l in rlines[-5:]), ",".join(EXPECT_RULING_IDS))
        check("RULINGS_APPENDED_WELL_FORMED",
              lambda: "ok" if all(len(l.split(TAB)) == 5 and l.split(TAB)[4] == "生效" for l in rlines[-5:]) else "bad", "ok")
        check("RULINGS_APPEND_TSV", lambda: "present" if os.path.isfile(os.path.join(EV, "RULINGS_APPEND_RELR4.tsv")) else "absent", "present")

        snap_end = os.path.join(EV, "TMP_SNAPSHOT_RELR4_end.tsv")
        def snap_end_ok():
            if not os.path.isfile(snap_end):
                return "absent"
            d = {}
            for line in open(snap_end, encoding="utf-8"):
                if line.strip() and not line.startswith("#"):
                    k, _t, val = line.rstrip(NL).partition(TAB)
                    d[k] = val
            return "same" if (d.get("TMP_COUNT") == sg.get("TMP_COUNT") and d.get("TMP_SHA256") == sg.get("TMP_SHA256")) else "differs"
        check("TMP_END_SNAPSHOT_FILE_MATCHES_START", snap_end_ok, "same")

        verdict = read_tsv(os.path.join(EV, "VERDICT_RELR4.tsv"))
        results = read_tsv(os.path.join(EV, "RESULTS_RELR4.tsv"))
        counts = {c: 0 for c in CATS}
        badcat = []
        for r in verdict:
            if r["category"] in counts:
                counts[r["category"]] += 1
            elif r["category"] not in NONCAT:
                badcat.append(r["category"])
        urows = [r for r in verdict if r["comparison"] == "U_vs_F4"]
        brows = [r for r in verdict if r["comparison"] == "B_vs_F4"]
        t1u = [r for r in urows if r["suite"] == "T1_compare"]
        t1b = [r for r in brows if r["suite"] == "T1_compare"]

        def catc(rows, c):
            return len([r for r in rows if r["category"] == c])
        check("VERDICT_NO_UNKNOWN_CATEGORY", lambda: "none" if not badcat else ",".join(sorted(set(badcat))[:4]), "none")
        check("VERDICT_REGISTRY_ROWS", lambda: str(len(verdict)), summary.get("REGISTRY_ROWS", "MISSING"))
        check("VERDICT_U_VS_F4_TOTAL", lambda: str(len(urows)), summary.get("ALL_U_VS_F4_TOTAL", "MISSING"))
        for c in CATS:
            check("VERDICT_ALL_U_VS_F4_" + c, lambda c=c: str(catc(urows, c)), summary.get("ALL_U_VS_F4_" + c, "MISSING"))
        check("SUMMARY_T1_U_SAME", lambda: str(catc(t1u, "SAME")), summary.get("T1_U_VS_F4_SAME", "MISSING"))
        check("SUMMARY_T1_U_DIFF_WITHIN_TOL", lambda: str(catc(t1u, "DIFF_WITHIN_TOL")), summary.get("T1_U_VS_F4_DIFF_WITHIN_TOL", "MISSING"))
        check("SUMMARY_T1_U_DIFF_ATTRIBUTED", lambda: str(catc(t1u, "DIFF_ATTRIBUTED")), summary.get("T1_U_VS_F4_DIFF_ATTRIBUTED", "MISSING"))
        check("SUMMARY_T1_U_BOTH_FAIL", lambda: str(catc(t1u, "BOTH_FAIL")), summary.get("T1_U_VS_F4_BOTH_FAIL", "MISSING"))
        check("SUMMARY_T1_U_IMPROVED", lambda: str(catc(t1u, "IMPROVED")), summary.get("T1_U_VS_F4_IMPROVED", "MISSING"))
        check("SUMMARY_T1_U_REGRESSION_ZERO", lambda: str(catc(t1u, "REGRESSION")), "0")
        check("REL_R1_REPRODUCTION_SAME", lambda: str(catc(t1b, "SAME")), "38")
        check("REL_R1_REPRODUCTION_BOTH_FAIL", lambda: str(catc(t1b, "BOTH_FAIL")), "11")
        check("REL_R1_REPRODUCTION_DIFF_ZERO",
              lambda: str(len(t1b) - catc(t1b, "SAME") - catc(t1b, "BOTH_FAIL")), "0")

        def category_consistent():
            bad = []
            for r in urows:
                c, u, f4 = r["category"], r["u"], r["f4"]
                ok = True
                if c in ("SAME", "DIFF_WITHIN_TOL"):
                    ok = (u == "PASS" and f4 == "PASS")
                elif c == "DIFF_ATTRIBUTED":
                    ok = (u == "PASS" and f4 == "PASS")
                elif c == "REGRESSION":
                    ok = (u == "PASS" and f4 == "FAIL")
                elif c == "IMPROVED":
                    ok = (u in ("FAIL", "TIMEOUT") and f4 == "PASS")
                elif c == "BOTH_FAIL":
                    ok = (u != "PASS" and f4 != "PASS")
                if not ok:
                    bad.append(r["unit_id"] + ":" + c + "/" + u + "/" + f4)
            return "consistent" if not bad else ";".join(bad[:4])
        check("VERDICT_CATEGORY_PASS_FAIL_CONSISTENT", category_consistent, "consistent")

        mpi = read_tsv(os.path.join(EV, "MPI_RELR4.tsv"))
        check("MPI_TSV_EXISTS", lambda: "present" if os.path.isfile(os.path.join(EV, "MPI_RELR4.tsv")) else "absent", "present")
        check("MPI_COMPARE_ALL_OK",
              lambda: "%d/%d" % (len([r for r in mpi if r["comparison"].startswith("np4_merged_vs") and r["result"] == "PASS"]),
                                 len([r for r in mpi if r["comparison"].startswith("np4_merged_vs")])), "12/12")
        check("MPI_BUILDS_OK", lambda: str(len([r for r in results if r["suite"] == "T3_mpi" and r["status"] == "BUILD_OK"])), "3")
        check("MPI_BANNERS",
              lambda: str(len([r for r in verdict if r["suite"] == "T3_mpi" and r["comparison"] == "banner"
                               and r["category"] == "WITH_MPI"])), "3")
        check("T5_UNIT_COUNT", lambda: summary.get("UNIT_COUNT"), "265")
        check("T5_RC_ZERO", lambda: summary.get("MAKETEST_RC"), "0")
        check("T5_NO_FAILURES", lambda: summary.get("MAKETEST_FAILURES"), "0")
        check("CAPI_BUILDS_OK", lambda: str(len([r for r in results if r["suite"] == "T4_capi" and r["status"] == "BUILD_OK"])), "3")
        check("CAPI_SPEC_REF_PASS", lambda: summary.get("T4_SPEC_REF_PASS"), "3")
        check("CAPI_POSCTRL_PASS", lambda: summary.get("T4_POSITIVE_CONTROL_PASS"), "3")
        check("CAPI_ORIGINAL_MAKEFILE_RC2", lambda: summary.get("T4_ORIGINAL_MAKEFILE_RC2"), "3")
        check("ATTR_TABLE_PRESENT", lambda: "present" if os.path.isfile(os.path.join(EV, "ATTRIB_RELR4.tsv")) else "absent", "present")
        check("DIFF_ATTRIBUTED_ALL_ATTRIBUTED",
              lambda: "%d" % len([r for r in read_tsv(os.path.join(EV, "ATTRIB_RELR4.tsv"))
                                  if r["unit_id"] != "NONE" and r["unit_id"].endswith(("_U_vs_F4",))]),
              summary.get("DIFF_ATTRIBUTED_TOTAL", "MISSING"))

        report = open(REPORT, encoding="utf-8").read() if os.path.isfile(REPORT) else ""
        block = {}
        m = re.search(r"<!-- COUNTS:BEGIN -->(.*?)<!-- COUNTS:END -->", report, re.S)
        if m:
            for line in m.group(1).splitlines():
                mm = re.match(r"^([A-Za-z0-9_]+)=(.+)$", line.strip())
                if mm:
                    block[mm.group(1)] = mm.group(2).strip()

        def report_match():
            need = ["REGISTRY_ROWS", "PREREG_UNITS", "T1_U_VS_F4_SAME", "T1_U_VS_F4_DIFF_WITHIN_TOL",
                    "T1_U_VS_F4_DIFF_ATTRIBUTED", "T1_U_VS_F4_REGRESSION", "T1_U_VS_F4_IMPROVED",
                    "T1_U_VS_F4_BOTH_FAIL", "T1_U_VS_F4_FLAKY", "T1_B_VS_F4_SAME", "T1_B_VS_F4_BOTH_FAIL",
                    "ALL_U_VS_F4_SAME", "ALL_U_VS_F4_DIFF_WITHIN_TOL", "ALL_U_VS_F4_DIFF_ATTRIBUTED",
                    "ALL_U_VS_F4_REGRESSION", "ALL_U_VS_F4_IMPROVED", "ALL_U_VS_F4_BOTH_FAIL",
                    "ALL_U_VS_F4_FLAKY", "UNIT_COUNT", "PREREG_SHA256", "NON_REGRESSION_U", "NON_REGRESSION_B"]
            probs = []
            for k in need:
                if k not in block:
                    probs.append("absent:" + k)
                elif summary.get(k) is not None and block[k] != summary[k]:
                    probs.append("%s:%s!=%s" % (k, block[k], summary[k]))
            return "all match" if not probs else ";".join(probs[:6])
        check("REPORT_COUNTS_MATCH_SUMMARY", report_match, "all match")

        def report_answers():
            need = ["原版能跑通的", "REGRESSION", "IMPROVED", "BOTH_FAIL", "GetAmplitudes", "Python",
                    "MPI", "S4mpi", "With MPI support", "spec.awk.out", "REF_DRIFT", "P13",
                    "越界写入", "工具/脚本事件", "等待用户审核", "git log -1", "git status --short"]
            missing = [x for x in need if x not in report]
            return "all present" if not missing else "missing:" + ",".join(missing)
        check("REPORT_REQUIRED_CONTENT", report_answers, "all present")
        check("REPORT_NO_P05_S6", lambda: "P05-S6" if "P05-S6" in report else "absent", "absent")

        st = open(STATE, encoding="utf-8").read() if os.path.isfile(STATE) else ""

        def state_sections():
            if "## 1" not in st or "## 2" not in st or "## 3" not in st:
                return "no sections"
            sec1 = st.split("## 1")[1].split("## 2")[0]
            sec2 = st.split("## 2")[1].split("## 3")[0]
            ok = any("REL-R4" in l for l in sec1.splitlines()) and any("REL-R4" in l for l in sec2.splitlines())
            return "yes" if ok else "no"
        check("STATE_RELR4_IN_SEC1_AND_SEC2", state_sections, "yes")
        rel_lines = [l for l in st.splitlines() if "REL-R4" in l]
        bad_state = [p for l in rel_lines for p in ("FAILS=", "FINAL_STATUS", "GATE_RELR4", "COMPLETE", "INCOMPLETE") if p in l]
        check("STATE_RELR4_LINES_NO_GATE_RESULT",
              lambda: "clean(%d lines)" % len(rel_lines) if not bad_state else "found:" + ",".join(bad_state),
              "clean(%d lines)" % len(rel_lines))
        check("STATE_NO_P05_S6", lambda: "P05-S6" if "P05-S6" in st else "absent", "absent")





        def whitelist():
            paths = set(sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD"]).stdout.split())
            for line in sh(["git", "status", "--porcelain", "-uall"]).stdout.splitlines():
                p = line[3:].strip()
                if " -> " in p:
                    p = p.split(" -> ")[-1]
                paths.add(p)
            bad = sorted(p for p in paths if not any(p.startswith(w) for w in WHITELIST))
            return "clean(%d files)" % len(paths) + ("" if not bad else ";outside:" + ";".join(bad[:6]))
        check("CHANGED_FILES_WHITELIST_NO_OUTSIDE", whitelist, "clean(0 files)") if False else None
        _wl = whitelist()
        check("CHANGED_FILES_WHITELIST_NO_OUTSIDE_REAL",
              lambda: "clean" if ";outside:" not in _wl else _wl.split(";outside:")[1], "clean")
        SKIP_TOP = ("upstream", "trees", "run", "tmp")
        BIN_NAMES = ("fig12", "mpi_probe_relr4", "main_lua_no_override.o")
        BIN_EXT = (".so", ".a", ".o", ".pyc", ".tar", ".gz", ".zip", ".png", ".bin")
        EXEMPT = ("SHA256SUMS.txt", "safe_run.log", "GATE_RELR4_pre.txt", "GATE_RELR4_end.txt",
                  "GATE_RELR4_check_start.txt", "GATE_RELR4_pre_firstrun.txt")

        def evidence_cov():
            sums_path = os.path.join(EV, "SHA256SUMS.txt")
            if not os.path.isfile(sums_path):
                return "SHA256SUMS.txt absent"
            listed = {}
            for line in open(sums_path, encoding="utf-8"):
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    listed[" ".join(parts[1:])] = parts[0]
            need = set()
            for root, dirs, files in os.walk(EV):
                relroot = os.path.relpath(root, EV)
                parts = [] if relroot == "." else relroot.split(os.sep)
                if parts and parts[0] in SKIP_TOP:
                    dirs[:] = []
                    continue
                if parts and parts[0] == "mpi":
                    dirs[:] = []
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), EV)
                    if rel in EXEMPT or f in BIN_NAMES or f.endswith(BIN_EXT):
                        continue
                    need.add(rel)
            missing = sorted(need - set(listed))
            bad = [p for p in listed if os.path.isfile(os.path.join(EV, p)) and sha_f(os.path.join(EV, p)) != listed[p]]
            gone = [p for p in listed if not os.path.isfile(os.path.join(EV, p))]
            return "covered" if not missing and not bad and not gone else "missing=%s bad=%s gone=%s" % (missing[:3], bad[:3], gone[:3])
        check("EVIDENCE_SUMS_COVER_NONBINARY", evidence_cov, "covered")

        # ---------- registry manifest of this round
        regr = verify_sums_dir(REG)

        def reg_check():
            if not regr:
                return "MISSING"
            if regr[1] or regr[2]:
                return "bad=%s unlisted=%s" % (regr[1][:3], regr[2][:3])
            return "all %d OK unlisted=0" % regr[0]
        check("RELR4_REGISTRY_ALL_OK", reg_check, "all %d OK unlisted=0" % (regr[0] if regr else -1))

        # ---------- the gate runs between commit (i) and commit (ii): verify commit (i) only
        def commits():
            out = sh(["git", "log", "--format=%H%x09%s", EXP_BASE_HEAD + "..HEAD"]).stdout.strip().splitlines()
            return out if out else []

        def commit_i():
            cs = commits()
            if len(cs) != 1:
                return "count=%d" % len(cs)
            subj = cs[0].split(TAB)[1].rstrip()
            if "(i)" not in subj:
                return "subject:" + subj[:80]
            if not subj.endswith("awaiting user review"):
                return "message"
            return "ok"
        check("ROUND_COMMIT_I_AWAITING_REVIEW", commit_i, "ok")

        def commit_scope():
            probs = []
            for c in commits():
                files = sh(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", c.split(TAB)[0]]).stdout.split()
                bad = [p for p in files if not any(p.startswith(w) for w in WHITELIST)]
                if bad:
                    probs.append(c.split(TAB)[0][:10] + ":" + ";".join(bad[:3]))
            return "clean" if not probs else "outside:" + ",".join(probs)
        check("COMMIT_SCOPE_WHITELIST", commit_scope, "clean")

        def worktree_clean():
            stt = sh(["git", "status", "--porcelain"]).stdout.strip()
            return "clean" if stt == "" else "dirty:" + stt[:150]
        check("WORKTREE_CLEAN_AT_FORMAL_GATE", worktree_clean, "clean")

        # appendix C is appended AFTER the formal gate (task brief section 8), so at gate time it must be absent
        check("REPORT_APPENDIX_C_ABSENT_AT_GATE",
              lambda: "absent" if "## 附录 C" not in report else "present", "absent")
        check("FORMAL_OUT_ABSENT_BEFORE_RUN", lambda: "absent" if not out_existed else "present",
              "absent" if formal else ("present" if out_existed else "absent"))
        # at the FORMAL run the pre-run gate file must already exist; the pre-run itself cannot see its own output
        if formal:
            check("GATE_PRE_FILE_PRESENT", lambda: "present" if os.path.isfile(os.path.join(EV, "GATE_RELR4_pre.txt")) else "absent", "present")

    fails = [c for c in CHECKS if not c[3]]
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    lines = ["# GATE_RELR4_%s.txt -- P05 delivery round REL-R4 gate (%s)" % (phase, os.path.basename(rp)),
             "# One script, one read-only code path: opening checks are shared, closing checks are --phase end only.",
             "# phase=%s formal=%s out=%s" % (phase, "yes" if formal else "no", os.path.relpath(rp, REPO))]
    for name, exp, act, ok in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + name + TAB + "expected=" + str(exp) + TAB + "actual=" + str(act))
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    lines.append("FINAL_STATUS=" + ("COMPLETE" if not fails and not CRASHED else "INCOMPLETE"))
    lines.append("TMP_COUNT=" + str(t_n))
    lines.append("TMP_SHA256=" + t_sha)
    open(rp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for l in lines:
        print(l)
    print("WROTE " + os.path.relpath(rp, REPO))
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())