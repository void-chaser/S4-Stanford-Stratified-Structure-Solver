#!/usr/bin/env python3
# relr1_check.py -- REL-R1 gate.  ONE read-only code path for both invocations (--out only changes the file):
#   pre-run   : relr1_check.py --phase end --out GATE_RELR1_pre.txt   (before commit (i))
#   formal    : relr1_check.py --phase end --out GATE_RELR1_end.txt   (after commit (i))
# The gate only reads files and recomputes facts; it never changes any evidence.  If the formal run has
# FAILS>0 it is not fixed and not re-run (task brief section 8.5).
# Checks (at least, per task brief): S4/ zero changes, judge sha256, pre-registration sha against the
# recorded value, registry manifests all OK, every file changed this round inside the whitelist, the
# top-level temporary-directory snapshot identical before/after, STATE.md free of gate-result words,
# and the report's derived numbers equal to the source tables read BY COLUMN NAME.
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
P05 = os.path.join(REPO, "checkpoints/p05")
TAB = chr(9)
NL = chr(10)
EXP_BASE_HEAD = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_F4_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_UNIT_COUNT = "265"
CATEGORIES = ["SAME", "DIFF_WITHIN_TOL", "DIFF", "NEW_FAIL", "FIXED", "BOTH_FAIL", "TIMEOUT", "SKIP_DECLARED", "FLAKY"]
WHITELIST = ("testing/d003/stage_relr1/", "checkpoints/p05/STATE.md",
             "checkpoints/p05/P05_RELR1_REPORT.md", "checkpoints/p05/registries/rel-r1/")
REPORT = os.path.join(P05, "P05_RELR1_REPORT.md")
SKIP_DIRS = ("trees", "clone", "p04run", "tmp", "t4src")
BIN_EXT = (".so", ".a", ".o", ".pyc", ".tar", ".gz", ".zip", ".png", ".bin")
EXEMPT_EVIDENCE = ("SHA256SUMS.txt", "safe_run.log", "GATE_RELR1_pre.txt", "GATE_RELR1_end.txt")
CHECKS = []
CRASHED = []


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
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0] == "RECORD" and len(f) >= 3:
            k, _, v = f[2].partition("=")
            d[f[1]] = v
    return d


def tsv_rows(path):
    rows, hdr = [], None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def read_kv_rows(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        k, _, v = line.rstrip(NL).partition(TAB)
        rows.append((k, v))
    return rows


def tmp_snapshot():
    names = sorted(os.listdir("/tmp"))
    return len(names), hashlib.sha256((NL.join(names) + NL).encode("utf-8")).hexdigest()


def verify_sums_dir(d):
    p = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(p):
        return None
    n, bad = 0, []
    listed = set()
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
        outp = os.path.join(EV, "GATE_RELR1_%s.txt" % phase)
    rp = os.path.realpath(outp)
    if not rp.startswith(os.path.join(P05, "evidence", "p05-rel-r1") + os.sep):
        print("HARD_STOP --out must stay under the round evidence directory")
        return 2
    out_existed = os.path.exists(rp)
    formal = os.path.basename(rp) == "GATE_RELR1_end.txt"
    start_gate = os.path.join(EV, "GATE_RELR1_start.txt")

    def sg(key, default="MISSING"):
        try:
            return kv_file(start_gate).get(key, default)
        except OSError:
            return default

    # ---------- facts that must hold in both phases
    check("START_GATE_EXISTS", lambda: "present" if os.path.isfile(start_gate) else "absent", "present")
    check("START_GATE_FAILS_ZERO", lambda: [l for l in open(start_gate).read().splitlines() if l.startswith("FAILS=")][-1], "FAILS=0")
    check("START_GATE_HEAD_S4", lambda: sg("HEAD_S4"), EXP_F4_S4)
    check("START_GATE_JUDGE", lambda: sg("JUDGE_SHA256"), EXP_JUDGE)
    check("START_GATE_RULINGS_LAST_U391", lambda: sg("RULINGS_LAST_ID"), "U391")
    check("HEAD_S4_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]).stdout.strip(), EXP_F4_S4)
    check("JUDGE_SHA256", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    check("BASE_HEAD_IS_ANCESTOR", lambda: str(sh(["git", "merge-base", "--is-ancestor", EXP_BASE_HEAD, "HEAD"]).returncode), "0")

    def s4_zero():
        st = sh(["git", "status", "--porcelain", "-uall", "--", "S4"]).stdout.strip()
        dif = sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD", "--", "S4"]).stdout.strip()
        return "clean" if (st == "" and dif == "") else ("status=" + st[:80] + " diff=" + dif[:80])
    check("S4_ZERO_CHANGES", s4_zero, "clean")
    check("RULINGS_UNCHANGED", lambda: sha_f(os.path.join(P05, "registries/RULINGS.tsv")), sg("RULINGS_SHA256"))
    r = verify_sums_dir(os.path.join(P05, "registries/s5r7"))
    check("S5R7_REGISTRY_ALL_OK", lambda: "all %d OK" % r[0] if r and not r[1] and not r[2] else "BAD %s" % (r,), "all 4 OK")

    # ---------- pre-registration (written before the first formal run)
    shaf = os.path.join(EV, "PREREG_RELR1.tsv.sha256.txt")
    recorded = "MISSING"
    if os.path.isfile(shaf):
        for line in open(shaf, encoding="utf-8"):
            if line.startswith("PREREG_RELR1.tsv" + TAB):
                recorded = line.rstrip(NL).split(TAB)[1]
    check("PREREG_SHA_MATCHES_RECORD", lambda: sha_f(os.path.join(EV, "PREREG_RELR1.tsv")), recorded)

    # ---------- temporary-directory snapshot before/after
    t_n, t_sha = tmp_snapshot()
    check("TMP_SNAPSHOT_SAME_AS_START", lambda: "%d %s" % (t_n, t_sha),
          "%s %s" % (sg("TMP_COUNT"), sg("TMP_SHA256")))

    if phase == "end":
        # ---------- registry manifest of this round
        regr = verify_sums_dir(os.path.join(P05, "registries/rel-r1"))
        def reg_check():
            if not regr:
                return "MISSING"
            if regr[1] or regr[2]:
                return "bad=%s unlisted=%s" % (regr[1][:3], regr[2][:3])
            return "all %d OK unlisted=0" % regr[0]
        check("RELR1_REGISTRY_ALL_OK", reg_check,
              "all %d OK unlisted=0" % (regr[0] if regr else -1))
        # ---------- changed files whitelist
        def whitelist():
            paths = set()
            d = sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD"]).stdout.split()
            paths |= set(d)
            st = sh(["git", "status", "--porcelain", "-uall"]).stdout.splitlines()
            for line in st:
                p = line[3:].strip()
                if " -> " in p:
                    p = p.split(" -> ")[-1]
                paths.add(p)
            bad = sorted(p for p in paths if not any(p.startswith(w) for w in WHITELIST))
            return "clean" if not bad else "outside:" + ";".join(bad[:6])
        check("CHANGED_FILES_WHITELIST", whitelist, "clean")
        # ---------- STATE.md
        st_txt = open(os.path.join(P05, "STATE.md"), encoding="utf-8").read()
        def relr1_in_two_sections():
            if not ("## 1" in st_txt and "## 2" in st_txt and "## 3" in st_txt):
                return "no sections"
            sec1 = st_txt.split("## 1")[1].split("## 2")[0]
            sec2 = st_txt.split("## 2")[1].split("## 3")[0]
            ok = len([ln for ln in sec1.splitlines() if "REL-R1" in ln]) >= 1 and \
                 len([ln for ln in sec2.splitlines() if "REL-R1" in ln]) >= 1
            return "yes" if ok else "no"
        check("STATE_HAS_RELR1_IN_SEC1_AND_SEC2", relr1_in_two_sections, "yes")
        # Only the two NEW REL-R1 lines must be free of gate-result words (S1-S5 history legitimately records earlier
        # gate results and is untouched).  The new lines must point to appendix C instead of pre-writing a result.
        rel_lines = [ln for ln in st_txt.splitlines() if "REL-R1" in ln]
        bad_state = []
        for ln in rel_lines:
            for pat in ("FAILS=", "FINAL_STATUS", "GATE_RELR1", "COMPLETE", "INCOMPLETE", "PASS}", "FAIL}"):
                if pat in ln:
                    bad_state.append(pat)
        check("STATE_RELR1_LINES_NO_GATE_RESULT", lambda: "clean(%d lines)" % len(rel_lines) if not bad_state else "found:" + ",".join(bad_state), "clean(%d lines)" % len(rel_lines))
        # ---------- report counts block vs source tables
        report = open(REPORT, encoding="utf-8").read() if os.path.isfile(REPORT) else ""
        block = {}
        m = re.search(r"<!-- COUNTS:BEGIN -->(.*?)<!-- COUNTS:END -->", report, re.S)
        if m:
            for line in m.group(1).splitlines():
                mm = re.match(r"^([A-Za-z0-9_]+)=(.+)$", line.strip())
                if mm:
                    block[mm.group(1)] = mm.group(2).strip()
        check("REPORT_COUNTS_BLOCK_PRESENT", lambda: "present" if block else "absent", "present")
        summary = {}
        for line in open(os.path.join(EV, "SUMMARY_RELR1.txt"), encoding="utf-8"):
            line = line.rstrip(NL)
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                summary[k] = v
        mk = {}
        for r in tsv_rows(os.path.join(EV, "MAKETEST_VERDICT_RELR1.tsv")):
            mk[r["item"]] = r["value"]
        expected_block = dict(summary)
        expected_block["UNIT_COUNT"] = mk.get("unit_count", "MISSING")
        expected_block["PREREG_SHA256"] = recorded
        def report_match():
            problems = []
            for k in ("REGISTRY_ROWS", "PREREG_UNITS") + tuple(CATEGORIES) + ("NON_REGRESSION", "UNIT_COUNT", "PREREG_SHA256"):
                if k not in block:
                    problems.append("absent:" + k)
                elif k in expected_block and block[k] != expected_block[k]:
                    problems.append("%s:%s!=%s" % (k, block[k], expected_block[k]))
            return "all match" if not problems else ";".join(problems[:6])
        check("REPORT_DERIVED_TEXT_MATCHES_TABLES", report_match, "all match")
        # ---------- verdict / summary internal consistency (recompute by column name)
        vrows = tsv_rows(os.path.join(EV, "VERDICT_RELR1.tsv"))
        counts = {c: 0 for c in CATEGORIES}
        badcat = []
        covered = set()
        for r in vrows:
            if r["category"] not in counts:
                badcat.append(r["category"])
            else:
                counts[r["category"]] += 1
            for uid in (r.get("prereg_units") or "").split(";"):
                if uid:
                    covered.add(uid)
        prereg_ids = set(r["unit_id"] for r in tsv_rows(os.path.join(EV, "PREREG_RELR1.tsv")))
        def recompute():
            probs = []
            for c in CATEGORIES:
                if summary.get(c) != str(counts[c]):
                    probs.append("%s:%s!=%s" % (c, summary.get(c), counts[c]))
            if badcat:
                probs.append("unknown_category:" + ",".join(sorted(set(badcat))[:3]))
            if covered != prereg_ids:
                probs.append("coverage missing=%d extra=%d" % (len(prereg_ids - covered), len(covered - prereg_ids)))
            return "consistent" if not probs else ";".join(probs[:6])
        check("SUMMARY_CONSISTENT_WITH_VERDICT", recompute, "consistent")
        def nonreg_rule():
            ok = (counts["NEW_FAIL"] == 0 and counts["DIFF"] == 0 and counts["FLAKY"] == 0
                  and summary.get("TIMEOUT_BOTH_TREES_SAME") == "YES")
            want = "PASS" if ok else "FAIL"
            return "PASS" if summary.get("NON_REGRESSION") == want else "SUMMARY_SAYS_" + str(summary.get("NON_REGRESSION"))
        check("NON_REGRESSION_RULE", nonreg_rule, "PASS")
        # ---------- evidence checksum list covers all non-binary evidence
        sums_path = os.path.join(EV, "SHA256SUMS.txt")
        def evidence_cov():
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
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if f.endswith(BIN_EXT) or f in EXEMPT_EVIDENCE:
                        continue
                    need.add(os.path.relpath(os.path.join(root, f), EV))
            missing = sorted(need - set(listed))
            bad = [p for p in listed if os.path.isfile(os.path.join(EV, p)) and sha_f(os.path.join(EV, p)) != listed[p]]
            gone = [p for p in listed if not os.path.isfile(os.path.join(EV, p))]
            return "covered" if not missing and not bad and not gone else "missing=%s bad=%s gone=%s" % (missing[:3], bad[:3], gone[:3])
        check("EVIDENCE_SUMS_COVER_NONBINARY", evidence_cov, "covered")
        # ---------- formal-run first-write invariant
        check("FORMAL_OUT_ABSENT_BEFORE_RUN", lambda: "absent" if not out_existed else "present",
              "absent" if formal else ("present" if out_existed else "absent"))
    fails = [c for c in CHECKS if not c[3]]
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    lines = ["# GATE_RELR1_%s.txt -- P05 delivery round REL-R1 gate (%s)" % (phase, os.path.basename(rp)),
             "# One read-only code path: every check reads files/tables and recomputes the fact; nothing is modified.",
             "# phase=%s formal=%s out=%s" % (phase, "yes" if formal else "no", os.path.relpath(rp, REPO))]
    for name, exp, act, ok in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + name + TAB + "expected=" + str(exp) + TAB + "actual=" + str(act))
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    lines.append("FINAL_STATUS=" + ("COMPLETE" if not fails and not CRASHED else "INCOMPLETE"))
    open(rp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for l in lines:
        print(l)
    print("WROTE " + os.path.relpath(rp, REPO))
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
