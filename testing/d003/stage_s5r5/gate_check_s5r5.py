#!/usr/bin/env python3
# gate_check_s5r5.py -- P05-S5 R5 end gate (task brief section 6; U388).
# Design rules (U388): the check logic is literally the same for the staging rehearsal and the formal run and
# depends only on the root path arguments (--ev-root / --p05-root / --out); there is NO branch on "is this a
# rehearsal" and NO branch on "is the output path this gate's own output"; the gate reads NO gate output file
# (neither the R5 staging output nor the R5 formal output nor any S5R4 gate output -- the R4 facts are consumed
# through the sweep/recheck tables produced before this gate). The staging output is verified outside the gate
# by s5r5_shakedown_verify.py.
# Every check is registered as (name, actual thunk, expected thunk) so --only evaluates exactly one check
# (used by the on-disk mutation positive controls); expected values may also be thunks.
# usage: gate_check_s5r5.py end [--ev-root DIR] [--p05-root DIR] [--out PATH] [--only NAME]
#          [--facts PATH] [--status-file PATH] [--judge-path PATH] [--s5r4-ev-root DIR] [--s5r4-reg-root DIR]
#          [--pycache-root DIR]
import os, sys, re, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV5_REAL = os.path.join(P05_REAL, "evidence/p05-s5r5")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
REG4_REAL = os.path.join(P05_REAL, "registries/s5r4")
TAB = chr(9)
NL = chr(10)

EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_BASE_HEAD = "1600ca1ba333e68988dc6d22211487b27e676191"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RULINGS_BYTES = 154825
EXP_RULINGS_SHA = "24e65c3223c94deafbfd58d74e613aec2e5749159b39dfe93014ee32dc86a2d3"
EXP_ERRATA_BYTES = 13848
EXP_ERRATA_SHA = "8aec8fd5e21c9fd2d3e5f3189d921eebe2fdde23524c5ea41087137fd641ba4f"
EXP_EV4_SUMS_SHA = "e996f364a38b8aa07a160f59b04e2ff0e9dd4f0497e8afca6fb14fc901758367"
EXP_EV4_ITEMS = 941
EXP_REG4_SUMS_SHA = "7f2b30eb026ccb28e9c686bba5ceaff3bdee1ca47a611e6856e8b68a3aaed9a3"
EXP_REG4_ITEMS = 15
EXP_START_UTC = "2026-10-18T22:09:21Z"
EXP_SWEEP_ROWS = 139
EXP_SWEEP_SELF_BRANCH = 2
EXP_R4_PASSES = 138
EXP_R4_FAILS = 1
EXP_R4_GATE_SHA = "20bb6ad031d50929e68631c166bab9aa4cb24c0a707c8fa1d07ecac7b7873065"
EXP_REG5_ITEMS = 11
EXP_REG5_EXPECTED_ROWS = 10
EXP_MAX_U = "U390"
EXP_TMP_COUNT_FILE = "TMP_SNAPSHOT_S5R5.tsv"
FORBIDDEN = [re.compile(r"FAILS=\d+"), re.compile(r"门禁.*(通过|PASS)"), re.compile(r"无可做")]

CHECKS = []
RECORDS = []
CRASHED = []


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sh(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO, stderr=subprocess.DEVNULL).strip()


def sh_raw(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO, stderr=subprocess.DEVNULL).rstrip("\n")


def rd(p):
    return open(p, encoding="utf-8").read()


def record(k, v):
    RECORDS.append((k, str(v)))


def add(name, actual, expected):
    CHECKS.append((name, actual, expected))


def verify_sums_dir(d):
    p = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(p):
        return None
    bad = []
    n = 0
    for line in open(p, encoding="utf-8"):
        line = line.rstrip(NL)
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        n += 1
        fp = os.path.join(d, " ".join(parts[1:]))
        if not os.path.isfile(fp) or sha_f(fp) != parts[0]:
            bad.append(os.path.basename(fp))
    return n, bad


def read_kv(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def read_tsv(p):
    rows = []
    hdr = None
    if not os.path.isfile(p):
        return rows
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def read_summary(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in rd(p).splitlines():
        if line.startswith("SUMMARY" + TAB):
            f = line.split(TAB)
            if len(f) >= 3:
                d[f[1]] = f[2]
    return d


def listed_map(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        d[" ".join(parts[1:])] = parts[0]
    return d


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] != "end":
        print("usage: gate_check_s5r5.py end [--ev-root DIR] [--p05-root DIR] [--out PATH] [--only NAME] "
              "[--facts PATH] [--status-file PATH] [--judge-path PATH] [--s5r4-ev-root DIR] [--s5r4-reg-root DIR] "
              "[--pycache-root DIR]")
        return 2

    def arg(name, default=None):
        return os.path.abspath(argv[argv.index(name) + 1]) if name in argv else default
    EV = arg("--ev-root", EV5_REAL)
    P05 = arg("--p05-root", P05_REAL)
    outp = arg("--out", os.path.join(EV, "gate/GATE_S5R5_end.txt"))
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    facts_path = arg("--facts")
    status_file = arg("--status-file")
    judge_path = arg("--judge-path", os.path.join(REPO, "testing/d003/judge_d003.py"))
    s5r4_ev = arg("--s5r4-ev-root", EV4_REAL)
    s5r4_reg = arg("--s5r4-reg-root", REG4_REAL)
    pycache_root = arg("--pycache-root", REPO)

    # ---------- git facts (real git by default; the positive control may pass a facts file)
    facts = {}
    if facts_path and os.path.isfile(facts_path):
        for line in rd(facts_path).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            facts[k] = v
    else:
        facts["BRANCH"] = sh(["git", "branch", "--show-current"])
        facts["HEAD"] = sh(["git", "rev-parse", "HEAD"])
        facts["HEAD_S4"] = sh(["git", "rev-parse", "HEAD:S4"])
        facts["S4_DIFF"] = sh_raw(["git", "diff", "--name-only", "HEAD", "--", "S4"]).strip()
        try:
            subprocess.check_call(["git", "merge-base", "--is-ancestor", EXP_BASE_HEAD, "HEAD"],
                                  cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            facts["BASE_ANCESTOR"] = "yes"
        except subprocess.CalledProcessError:
            facts["BASE_ANCESTOR"] = "no"
        facts["COMMITS_POST_BASE"] = sh(["git", "log", "--format=%s", EXP_BASE_HEAD + "..HEAD"])

    def status_lines():
        if status_file:
            return [l.rstrip() for l in rd(status_file).splitlines() if l.strip()]
        return [l.rstrip() for l in sh_raw(["git", "status", "--porcelain=v1"]).splitlines() if l.strip()]

    # ---------- per-root inputs
    state_p = os.path.join(P05, "STATE.md")
    draft3_p = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")
    report_p = os.path.join(P05, "P05_S5R5_REPORT.md")
    r4report_p = os.path.join(P05, "P05_S5R4_REPORT.md")
    rulings_p = os.path.join(P05, "registries/RULINGS.tsv")
    errata_p = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    reg5 = os.path.join(P05, "registries/s5r5")
    snap_p = os.path.join(reg5, "r4_final/ERRATA_S5_R4FINAL.txt")
    sweep_p = os.path.join(EV, "CHECKER_SWEEP_S5R5.tsv")
    recheck_p = os.path.join(EV, "RECHECK_STAGING_S5R5.tsv")
    pcr_p = os.path.join(EV, "POSCTRL_RECHECK_STAGING_S5R5.txt")
    readiness_p = os.path.join(EV, "READINESS_S5R5.tsv")
    frozen_p = os.path.join(EV, "FROZEN_SCRIPTS_S5R5.tsv")
    pcg_p = os.path.join(EV, "POSCTRL_GATE_S5R5.txt")
    tmp_p = os.path.join(EV, EXP_TMP_COUNT_FILE)

    def body_of_report():
        if not os.path.isfile(report_p):
            return ""
        data = open(report_p, "rb").read().decode("utf-8")
        return data.split("## 附录 A")[0]

    def phrase_hits(txt):
        hits = []
        for i, line in enumerate(txt.splitlines(), 1):
            for rx in FORBIDDEN:
                if rx.search(line):
                    hits.append("line%d" % i)
        return hits

    # ---------- checks
    add("BRANCH_IS_EXPECTED", lambda: facts.get("BRANCH", "?"), lambda: EXP_BRANCH)
    add("HEAD_S4_TREE_EQ_F4", lambda: facts.get("HEAD_S4", "?"), lambda: EXP_S4)

    def head_commits():
        if facts.get("BASE_ANCESTOR") != "yes":
            return "base_not_ancestor"
        subs = [s for s in facts.get("COMMITS_POST_BASE", "").splitlines() if s.strip()]
        bad = [s for s in subs if "P05-S5 R5 (i)" not in s]
        return "ok" if not bad else "bad:" + bad[0][:60]
    add("HEAD_R5_I_COMMITS_ONLY", head_commits, lambda: "ok")
    add("JUDGE_SHA256", lambda: sha_f(judge_path), lambda: EXP_JUDGE)
    add("S4_DIR_ZERO_MODIFICATION", lambda: facts.get("S4_DIFF", "") or "unmodified", lambda: "unmodified")

    def modified_ok():
        lines = status_lines()
        bad = []
        for ln in lines:
            status, path = ln[:2], ln[3:]
            if path.startswith("checkpoints/p05/") or path.startswith("testing/d003/stage_s5r5"):
                continue
            bad.append(ln)
        return "ok" if not bad else ";".join(bad[:3])
    add("MODIFIED_TRACKED_FILES_WITHIN_ALLOW_PREFIXES", modified_ok, lambda: "ok")

    def pycache_hits():
        """No __pycache__ created by this round: count __pycache__ dirs whose mtime is not older than the round
        start. Pre-existing historical __pycache__ trees (Oct 11, gitignored) are older and are not R5 output."""
        start = int(datetime.datetime.strptime(EXP_START_UTC, "%Y-%m-%dT%H:%M:%SZ")
                    .replace(tzinfo=datetime.timezone.utc).timestamp())
        n = 0
        for root, dirs, files in os.walk(pycache_root):
            dirs[:] = [d for d in dirs if d != ".git"]
            if os.path.basename(root) == "__pycache__":
                try:
                    if os.path.getmtime(root) >= start:
                        n += 1
                except OSError:
                    pass
        return n
    add("NO_PYCACHE", pycache_hits, lambda: 0)

    def tmp_snap():
        names = sorted(os.listdir("/tmp"))
        return "%d/%s" % (len(names), sha_b((NL.join(names) + NL).encode("utf-8")))
    add("TMP_SNAPSHOT_UNCHANGED", tmp_snap,
        lambda: "%s/%s" % (read_kv(tmp_p).get("TMP_COUNT", "?"), read_kv(tmp_p).get("TMP_SHA256", "?")))

    def sums_ok(d, items, sha_exp):
        v = verify_sums_dir(d)
        if not v:
            return "MISSING"
        return "%d/%s/%s" % (v[0], "OK" if not v[1] else "BAD",
                             "yes" if sha_f(os.path.join(d, "SHA256SUMS.txt")) == sha_exp else "no")
    add("S5R4_EVIDENCE_SUMS_ALL_OK_941", lambda: sums_ok(s5r4_ev, EXP_EV4_ITEMS, EXP_EV4_SUMS_SHA),
        lambda: "%d/OK/yes" % EXP_EV4_ITEMS)
    add("S5R4_REGISTRY_SUMS_ALL_OK_15", lambda: sums_ok(s5r4_reg, EXP_REG4_ITEMS, EXP_REG4_SUMS_SHA),
        lambda: "%d/OK/yes" % EXP_REG4_ITEMS)

    def sw(name):
        return read_summary(sweep_p).get(name, "MISSING")
    add("CHECKER_SWEEP_ROWS_SELF_BRANCH", lambda: "%s/%s" % (sw("SWEEP_ROWS"), sw("SELF_BRANCH_ROWS")),
        lambda: "%d/%d" % (EXP_SWEEP_ROWS, EXP_SWEEP_SELF_BRANCH))
    add("CHECKER_SWEEP_R4_GATE_SUMMARY",
        lambda: "%s/%s/%s" % (sw("R4_FORMAL_PASSES"), sw("R4_FORMAL_FAILS"), sw("R4_GATE_SHA256")),
        lambda: "%d/%d/%s" % (EXP_R4_PASSES, EXP_R4_FAILS, EXP_R4_GATE_SHA))
    add("CHECKER_SWEEP_VACUOUS_ZERO", lambda: sw("VACUOUS"), lambda: "0")

    def rulings_bytes():
        return open(rulings_p, "rb").read()
    add("RULINGS_PREFIX_AND_NOT_TRUNCATED",
        lambda: "ok" if (len(rulings_bytes()) >= EXP_RULINGS_BYTES
                         and sha_b(rulings_bytes()[:EXP_RULINGS_BYTES]) == EXP_RULINGS_SHA) else "bad", lambda: "ok")

    def rulings_max():
        mu = 0
        for line in rulings_bytes().decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    add("RULINGS_MAX_U_390", rulings_max, lambda: EXP_MAX_U)

    def rulings5():
        n = 0
        for line in rulings_bytes().decode("utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            n += 1
            if len(line.split(TAB)) != 5:
                return "row%d=%dfields" % (n, len(line.split(TAB)))
        return "ok"
    add("RULINGS_LINES_5_FIELDS", rulings5, lambda: "ok")

    def rulings_once():
        ids = [l.split(TAB)[0] for l in rulings_bytes().decode("utf-8").splitlines()
               if l.strip() and not l.startswith("#")]
        bad = [u for u in ("U386", "U387", "U388", "U389", "U390") if ids.count(u) != 1]
        return "ok" if not bad else ",".join(bad)
    add("RULINGS_U386_U390_ONCE", rulings_once, lambda: "ok")

    def errata_bytes():
        return open(errata_p, "rb").read()
    add("ERRATA_PREFIX_AND_NOT_TRUNCATED",
        lambda: "ok" if (len(errata_bytes()) >= EXP_ERRATA_BYTES
                         and sha_b(errata_bytes()[:EXP_ERRATA_BYTES]) == EXP_ERRATA_SHA) else "bad", lambda: "ok")

    def errata_ids():
        return [l for l in errata_bytes().decode("utf-8").splitlines() if l.startswith("ES5-")]
    add("ERRATA_S5_LAST_IS_ES5_16", lambda: errata_ids()[-1] if errata_ids() else "none", lambda: "ES5-16")
    add("ERRATA_S5_HAS_ES5_15_16",
        lambda: ",".join(x for x in errata_ids() if x in ("ES5-15", "ES5-16")), lambda: "ES5-15,ES5-16")
    add("ERRATA_R4FINAL_SNAPSHOT_SHA",
        lambda: sha_f(snap_p) if os.path.isfile(snap_p) else "MISSING", lambda: EXP_ERRATA_SHA)

    def recheck_rows():
        return {r.get("check"): r for r in read_tsv(recheck_p)}
    add("RECHECK_CORRECTED_PASS", lambda: recheck_rows().get("CORRECTED_LOGIC", {}).get("actual", "MISSING"),
        lambda: "PASS")
    add("RECHECK_R4_ORIGINAL_NOT_STAGING",
        lambda: recheck_rows().get("R4_ORIGINAL_LOGIC", {}).get("actual", "MISSING"), lambda: "not_staging")

    def recheck_input():
        rows = recheck_rows()
        want = rows.get("INPUT_SHA256", {})
        excl = rows.get("INPUT_NOT_IN_S5R4_SUMS_DECLARED_EXCLUSION", {}).get("status", "MISSING")
        evr = rows.get("EV_ROOT_IS_SHAKEDOWN_PATH", {})
        p05r = rows.get("P05_ROOT_IS_SHAKEDOWN_PATH", {})
        f0 = rows.get("FAILS_ZERO", {})
        c0 = rows.get("CHECK_CRASHED_ZERO", {})
        got_sha = sha_f(os.path.join(EV4_REAL, "shakedown/gate/GATE_S5R4_end.txt"))
        ok = (want.get("actual") == got_sha and want.get("expected") == got_sha
              and excl == "PASS" and evr.get("status") == "PASS" and p05r.get("status") == "PASS"
              and f0.get("actual") == "0" and c0.get("actual") == "0")
        return "ok" if ok else "bad"
    add("RECHECK_INPUT_SHA_AND_SHAKEDOWN_ROOTS", recheck_input, lambda: "ok")
    add("RECHECK_POSCTRL_4_OF_4",
        lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pcr_p)).groups()
                 if os.path.isfile(pcr_p) else ("MISSING", "0", "0")), lambda: ("PASS", "4", "4"))

    def readiness_rows():
        return read_tsv(readiness_p)

    def rd_meta():
        d = {}
        if not os.path.isfile(readiness_p):
            return d
        for line in rd(readiness_p).splitlines():
            if line.startswith("# META" + TAB):
                for x in line.split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    d[k] = v
        return d
    add("READINESS_GAP_ZERO",
        lambda: sum(1 for r in readiness_rows() if r.get("status") == "GAP"), lambda: 0)
    add("READINESS_STATE_SHA_MATCH",
        lambda: rd_meta().get("STATE_SHA256", "MISSING"),
        lambda: sha_f(state_p) if os.path.isfile(state_p) else "NO_STATE")
    add("READINESS_AFTER_FINAL_STATE",
        lambda: 1 if (os.path.isfile(readiness_p) and os.path.isfile(state_p)
                      and os.path.getmtime(readiness_p) > os.path.getmtime(state_p)) else 0, lambda: 1)

    add("STATE_NO_GATE_RESULT_PHRASES",
        lambda: len(phrase_hits(rd(state_p) if os.path.isfile(state_p) else "")), lambda: 0)

    def state_r4_row():
        if not os.path.isfile(state_p):
            return "NO_STATE"
        t = rd(state_p)
        miss = [k for k in ("ES5-15", "INCOMPLETE", "RECHECK_STAGING_S5R5.tsv") if k not in t]
        if miss:
            return "missing:" + ",".join(miss)
        if not os.path.isfile(r4report_p):
            return "NO_R4_REPORT"
        hits = re.findall(r"FINAL_STATUS=(\w+)", rd(r4report_p))
        return "ok" if hits and hits[-1] == "INCOMPLETE" else "r4_report_final=%s" % (hits[-1] if hits else "MISSING")
    add("STATE_S5R4_ROW_INCOMPLETE_CONSISTENT", state_r4_row, lambda: "ok")

    def draft3_check():
        if not os.path.isfile(draft3_p):
            return "NO_DRAFT"
        t = rd(draft3_p)
        miss = [k for k in ("未签收", "见 P05_S5R5_REPORT.md 附录 C", "FINAL_STATUS≠COMPLETE") if k not in t]
        if miss:
            return "missing:" + ",".join(miss)
        h = phrase_hits(t)
        return "ok" if not h else "phrases:" + ",".join(h[:3])
    add("DRAFT_V3_UNSIGNED_DEFERRED_NO_PHRASES", draft3_check, lambda: "ok")
    add("REPORT_BODY_NO_GATE_RESULT_PHRASES", lambda: len(phrase_hits(body_of_report())), lambda: 0)

    def reg_sums():
        v = verify_sums_dir(reg5)
        if not v:
            return "MISSING"
        return "%d/%s" % (v[0], "OK" if not v[1] else "BAD")
    add("REGISTRY_S5R5_SUMS_ALL_OK", reg_sums, lambda: "%d/OK" % EXP_REG5_ITEMS)

    def reg_expected():
        exp = os.path.join(reg5, "REGISTRY_EXPECTED_S5R5.txt")
        if not os.path.isfile(exp):
            return "NO_EXPECTED"
        sums = listed_map(os.path.join(reg5, "SHA256SUMS.txt"))
        bad = []
        n = 0
        for line in rd(exp).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split(TAB) if TAB in line else line.split()
            if f[0] == "rel_path":
                continue
            n += 1
            rel, want = f[0], f[1]
            p = os.path.join(reg5, rel)
            if not os.path.isfile(p) or sha_f(p) != want or sums.get(rel) != want:
                bad.append(rel)
        files = set()
        for root, dirs, fs in os.walk(reg5):
            for f in fs:
                rel = os.path.relpath(os.path.join(root, f), reg5)
                if rel in ("SHA256SUMS.txt", "GATE_S5R5_end.txt"):
                    continue
                files.add(rel)
        miss = sorted(files - set(sums))
        extra = sorted(set(sums) - files)
        if bad or miss or extra:
            return "bad=%s miss=%s extra=%s" % (bad[:2], miss[:2], extra[:2])
        return "%d/ok" % n
    add("REGISTRY_S5R5_EXPECTED_AND_NO_UNLISTED", reg_expected,
        lambda: "%d/ok" % EXP_REG5_EXPECTED_ROWS)

    def frozen_ok():
        rows = read_tsv(frozen_p)
        if not rows:
            return "NO_LIST"
        bad = []
        for r in rows:
            p = os.path.join(REPO, r.get("path", ""))
            if not os.path.isfile(p) or sha_f(p) != r.get("sha256", ""):
                bad.append(os.path.basename(r.get("path", "")))
        return "ok_%d" % len(rows) if not bad else "bad:" + ",".join(bad[:3])
    add("FROZEN_SCRIPTS_SHA_UNCHANGED", frozen_ok, lambda: "ok_%d" % len(read_tsv(frozen_p)))

    def posctrl_gate():
        if not os.path.isfile(pcg_p):
            return "MISSING"
        m = re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pcg_p))
        if not m:
            return "UNPARSED"
        return "%s/%s" % (m.group(1), m.group(2))
    add("POSCTRL_GATE_ALL_CHECKS_COVERED", posctrl_gate, lambda: "PASS/%d" % TOTAL_CHECKS)

    # ---------- run
    TOTAL_CHECKS = len(CHECKS)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("END_TIME_UTC", started)
    record("GATE_SCRIPT", "testing/d003/stage_s5r5/gate_check_s5r5.py")
    record("GATE_SCRIPT_SHA256", sha_f(os.path.abspath(__file__)))
    record("EV_ROOT", os.path.relpath(EV, REPO))
    record("P05_ROOT", os.path.relpath(P05, REPO))
    record("GATE_CHECKS", TOTAL_CHECKS)
    if only:
        picks = [c for c in CHECKS if c[0] == only]
        if not picks:
            print("FAIL\t--only: unknown check %s" % only)
            return 2
        CHECKS[:] = picks
        record("ONLY_CHECK", only)
    results = []
    for (name, fn_a, fn_e) in CHECKS:
        try:
            exp = fn_e()
            act = fn_a()
            if isinstance(act, bool):
                act = int(act)
            if isinstance(exp, bool):
                exp = int(exp)
            ok = str(act) == str(exp)
        except Exception as exc:
            CRASHED.append((name, repr(exc)[:200]))
            exp, act, ok = "?", "EXC:" + repr(exc)[:160], False
        results.append((name, str(exp), str(act), ok))
    fails = [c for c in results if not c[3]]
    lines = ["# P05-S5 R5 end gate GATE_S5R5_end.txt (" + started + ")"]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in results:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + str(e) + TAB + "actual=" + str(a))
    lines.append("COUNTS" + TAB + "pass=%d" % (len(results) - len(fails)) + TAB + "fail=%d" % len(fails)
                 + TAB + "total=%d" % len(results))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print(NL.join(lines))
    print("WROTE " + outp)
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
