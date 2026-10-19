#!/usr/bin/env python3
# s5r6_check.py -- P05-S5 R6 gate (pure documentation sub-round; task brief sections 0 and 5).
# One script, two read-only phases:
#   --phase start : the opening baseline named in the task brief, the immutable S5R5 evidence/registry
#                   manifests, the S5R5 end gate sha + FAILS=0 line, frozen inputs, the /tmp top-level
#                   snapshot and the absence of R6 outputs.
#   --phase end   : the closing checks: S4/ untouched, R5 report first 95 lines sha unchanged,
#                   ERRATA_S5.txt pure append (ES5-17), RULINGS unchanged (no user sign-off text -> no U391),
#                   drafts v1/v2/v3 and P05_S3_S4_SIGNOFF.md sha unchanged, S5R5/S5R4/S5R5-evidence manifests
#                   all OK, modified files within the round whitelist, /tmp snapshot unchanged, no new
#                   __pycache__, registry s5r6 pre-gate shape.
# The start phase never reads any gate output except the sha and the FAILS=0 line of GATE_S5R5_end.txt.
# The end phase has a single code path for the pre-commit rehearsal and for the formal run; only --out differs.
import os, re, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r6")
EV5 = os.path.join(P05, "evidence/p05-s5r5")
REG5 = os.path.join(P05, "registries/s5r5")
REG4 = os.path.join(P05, "registries/s5r4")
REG6 = os.path.join(P05, "registries/s5r6")
TAB = chr(9)
NL = chr(10)
TODAY = "2026-10-19"

EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_BASE_HEAD = "8e55f6e534f95f6458e491423c09f624b4f1ae01"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_S5R5_GATE_SHA = "1fd857449a426651c8e03a1721bd606eb502ccf8a6374623066d65565be4458f"
EXP_REG5_SUMS_SHA = "b8be693b70f859c43d74764553c7dd57f11f0fcc0ae931796fcd1d33f9ec0ed9"
EXP_REG5_ITEMS = 12
EXP_EV5_SUMS_SHA = "ff06d0ff9b8e78cf6a4dd2cc9ac8765334368adbcb0d3e69460ca1f480b1262e"
EXP_EV5_ITEMS = 20
EXP_REG4_SUMS_SHA = "7f2b30eb026ccb28e9c686bba5ceaff3bdee1ca47a611e6856e8b68a3aaed9a3"
EXP_REG4_ITEMS = 15
EXP_RULINGS_BYTES = 156852
EXP_RULINGS_SHA = "d5742e70c40ebb7a08585860d98557eabcd0aaebbdbabb4f47e9be950a38e9c3"
EXP_RULINGS_MAX = "U390"
EXP_ERRATA_BYTES = 15805
EXP_ERRATA_SHA = "e1f02ee80605a8eb1240fdacdf22d9b4e2e38c5a764c1fd946e5d979af8dfa33"
EXP_STATE_SHA = "c713a1018a4cae6b79914669433e7aef2c669f8cc49458f5ecdc705e1b2fa89e"
EXP_R5REPORT_SHA = "9f90d6f7ad390cc5ab14b6bc08bb5a4fbb95fcd98e6231081549ca4d602d91c5"
EXP_R5REPORT_FIRST95_SHA = "8f7f96b4fc41500c616f6f931160fdd4ee7d46856ca3e4c1d0fdcb1fe138932c"
EXP_DRAFT_V1_SHA = "c08bac3f05fe1c2ee087d093cc0dcf9d9cf96e1666f2472c534fb6162e41da93"
EXP_DRAFT_V2_SHA = "67876cd420c1ab44a6bd300f36ba2ae6cd382bdc855538203747e528d5acb69e"
EXP_DRAFT_V3_SHA = "c7fc843d0d9f90c3b89d9154e4660749ae82c50b29b7b07dd2c0aa3b6afed500"
EXP_P3S4_SIGNOFF_SHA = "7b5b412a9fa363ad47958d58a7500abb47c2c003b0a7fc79e72ad0e578c8f4ae"
EXP_ROADMAP_SHA = "986dc3b6cd3bff0405b788dfc10e3a7887cf4d6a58ce4cb163041d15afc85b4a"
EXP_ISSUE_SHA = "2c96469ab557e8974736a6949959ef3dea0f3a0f4f6dd3d54773a90668c6da10"
EXP_PYCACHE_COUNT = 22
EXP_PYCACHE_SHA = "fd6481c0a59399af539e9da2777884c10a70fd36f57b425787ae906ff8f20fbd"
R5REPORT = os.path.join(P05, "P05_S5R5_REPORT.md")
ERRATA = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
RULINGS = os.path.join(P05, "registries/RULINGS.tsv")
STATE = os.path.join(P05, "STATE.md")
ROADMAP = os.path.join(REPO, "PROJECT_ROADMAP.md")
ISSUE = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
R6REPORT = os.path.join(P05, "P05_S5R6_REPORT.md")
SIGNOFF_S5 = os.path.join(P05, "P05_S5_SIGNOFF.md")
WHITELIST = ("checkpoints/p05/", "testing/d003/stage_s5r6/",
             "testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md")

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


def rd_b(p):
    return open(p, "rb").read()


def rd(p):
    return open(p, encoding="utf-8").read()


def sh(args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()


def sh_raw(args):
    # keep leading/trailing whitespace: porcelain status lines start with a space in many cases
    return subprocess.check_output(args, text=True, cwd=REPO)


def record(k, v):
    RECORDS.append((k, str(v)))


def safe(name, fn, exp):
    try:
        actual = fn()
        if isinstance(actual, bool):
            actual = int(actual)
    except Exception as exc:
        CRASHED.append((name, repr(exc)[:200]))
        actual = "EXC:" + repr(exc)[:160]
    CHECKS.append((name, str(exp), str(actual), str(actual) == str(exp)))


def first_n_lines_sha(data, n):
    parts = data.split(b"\n")
    if len(parts) < n:
        return "too_short"
    return sha_b(b"\n".join(parts[:n]) + b"\n")


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


def tmp_live():
    names = sorted(os.listdir("/tmp"))
    return len(names), sha_b((NL.join(names) + NL).encode("utf-8")), names


def pycache_now():
    out = []
    for root, dirs, _fs in os.walk(REPO):
        if ".git" in dirs:
            dirs.remove(".git")
        for d in list(dirs):
            if d == "__pycache__":
                out.append(os.path.relpath(os.path.join(root, d), REPO))
                dirs.remove(d)
    out.sort()
    return out


def read_kv(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


# ------------------------------------------------------------------ phase start
def phase_start():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("START_TIME_UTC", started)
    record("BASE_HEAD", EXP_BASE_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    record("ROUND", "P05-S5 R6 (s5r6, pure documentation sub-round)")
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_R5_II", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("BASE_COMMIT_PRESENT",
         lambda: sh(["git", "rev-parse", "--verify", EXP_BASE_HEAD + "^{commit}"]), EXP_BASE_HEAD)
    safe("S4_DIR_ZERO_MODIFICATION",
         lambda: sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "--", "S4"]) or "unmodified", "unmodified")

    def status_only_stage():
        st = sh(["git", "status", "--porcelain=v1", "-uall"])
        bad = [ln for ln in st.splitlines() if ln.rstrip() != "?? testing/d003/stage_s5r6/s5r6_check.py"]
        return "only_stage_s5r6_check" if not bad else ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_STAGE_S5R6", status_only_stage, "only_stage_s5r6_check")

    rb = rd_b(RULINGS)
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    safe("RULINGS_START_BYTES", lambda: len(rb), EXP_RULINGS_BYTES)
    safe("RULINGS_START_SHA256", lambda: sha_b(rb), EXP_RULINGS_SHA)

    def rulings_max_u():
        mu = 0
        for line in rb.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    safe("RULINGS_START_MAX_U390", rulings_max_u, EXP_RULINGS_MAX)
    safe("RULINGS_START_LINES_5_FIELDS",
         lambda: "ok" if all(len(l.split(TAB)) == 5 for l in rb.decode("utf-8").splitlines()
                             if l.strip() and not l.startswith("#")) else "bad", "ok")

    eb = rd_b(ERRATA)
    record("ERRATA_S5_BYTES", len(eb))
    record("ERRATA_S5_SHA256", sha_b(eb))
    safe("ERRATA_START_BYTES", lambda: len(eb), EXP_ERRATA_BYTES)
    safe("ERRATA_START_SHA256", lambda: sha_b(eb), EXP_ERRATA_SHA)
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_START_LAST_IS_ES5_16", lambda: last_e[-1] if last_e else "none", "ES5-16")

    st = rd_b(STATE)
    record("STATE_BYTES", len(st))
    record("STATE_SHA256", sha_b(st))
    safe("STATE_START_SHA", lambda: sha_b(st), EXP_STATE_SHA)
    r5 = rd_b(R5REPORT)
    record("R5REPORT_BYTES", len(r5))
    record("R5REPORT_SHA256", sha_b(r5))
    record("R5REPORT_FIRST95_SHA256", first_n_lines_sha(r5, 95))
    safe("R5REPORT_START_SHA", lambda: sha_b(r5), EXP_R5REPORT_SHA)
    safe("R5REPORT_FIRST95_SHA", lambda: first_n_lines_sha(r5, 95), EXP_R5REPORT_FIRST95_SHA)
    safe("R5REPORT_HAS_96_LINES", lambda: r5.count(b"\n"), 96)
    safe("DRAFT_V1_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")), EXP_DRAFT_V2_SHA)
    safe("DRAFT_V3_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")), EXP_DRAFT_V3_SHA)
    safe("P05_S3_S4_SIGNOFF_SHA",
         lambda: sha_f(os.path.join(P05, "P05_S3_S4_SIGNOFF.md")), EXP_P3S4_SIGNOFF_SHA)
    safe("SIGNOFF_S5_ABSENT", lambda: "absent" if not os.path.exists(SIGNOFF_S5) else "present", "absent")
    safe("ROADMAP_START_SHA", lambda: sha_f(ROADMAP), EXP_ROADMAP_SHA)
    safe("ISSUE_REGISTRY_START_SHA", lambda: sha_f(ISSUE), EXP_ISSUE_SHA)
    safe("S5R6_REPORT_ABSENT", lambda: "absent" if not os.path.exists(R6REPORT) else "present", "absent")
    safe("REG6_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(REG6) else "present", "absent")

    def ev_precontent():
        if not os.path.isdir(EV):
            return "absent"
        allowed = {"tmp", "safe_run.log", "GATE_S5R6_start.txt", "TMP_SNAPSHOT_S5R6.tsv"}
        extra = sorted(set(os.listdir(EV)) - allowed)
        if extra:
            return "extra=" + ",".join(extra[:4])
        logp = os.path.join(EV, "safe_run.log")
        if os.path.isfile(logp):
            bad = [l for l in rd(logp).splitlines()
                   if "s5r6_check.py" not in l and "cmd=mkdir " not in l
                   and "GATE_S5R6_start.txt" not in l and "TMP_SNAPSHOT_S5R6.tsv" not in l]
            if bad:
                return "foreign_log_lines=%d" % len(bad)
        return "clean"
    safe("EV_PRECONTENT_ONLY_WRAPPER", ev_precontent, "clean")

    reg5 = verify_sums_dir(REG5)
    record("S5R5_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG5, "SHA256SUMS.txt")))
    safe("S5R5_REGISTRY_SUMS_SHA", lambda: sha_f(os.path.join(REG5, "SHA256SUMS.txt")), EXP_REG5_SUMS_SHA)
    safe("S5R5_REGISTRY_SUMS_ALL_OK_12",
         lambda: "%d/%s" % (reg5[0], "OK" if not reg5[1] else "BAD:" + ",".join(reg5[1][:3])),
         "%d/OK" % EXP_REG5_ITEMS)
    ev5 = verify_sums_dir(EV5)
    record("S5R5_EVIDENCE_SUMS_SHA256", sha_f(os.path.join(EV5, "SHA256SUMS.txt")))
    safe("S5R5_EVIDENCE_SUMS_SHA", lambda: sha_f(os.path.join(EV5, "SHA256SUMS.txt")), EXP_EV5_SUMS_SHA)
    safe("S5R5_EVIDENCE_SUMS_ALL_OK_20",
         lambda: "%d/%s" % (ev5[0], "OK" if not ev5[1] else "BAD:" + ",".join(ev5[1][:3])),
         "%d/OK" % EXP_EV5_ITEMS)
    reg4 = verify_sums_dir(REG4)
    record("S5R4_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG4, "SHA256SUMS.txt")))
    safe("S5R4_REGISTRY_SUMS_SHA", lambda: sha_f(os.path.join(REG4, "SHA256SUMS.txt")), EXP_REG4_SUMS_SHA)
    safe("S5R4_REGISTRY_SUMS_ALL_OK_15",
         lambda: "%d/%s" % (reg4[0], "OK" if not reg4[1] else "BAD:" + ",".join(reg4[1][:3])),
         "%d/OK" % EXP_REG4_ITEMS)

    g5 = os.path.join(EV5, "gate/GATE_S5R5_end.txt")
    record("S5R5_GATE_END_SHA256", sha_f(g5))
    safe("S5R5_GATE_END_SHA", lambda: sha_f(g5), EXP_S5R5_GATE_SHA)
    safe("S5R5_GATE_END_FAILS_ZERO",
         lambda: re.search(r"FAILS=(\d+)", rd(g5)).group(1), "0")

    cnt, tsha, _names = tmp_live()
    record("TMP_COUNT", cnt)
    record("TMP_SHA256", tsha)
    snaps = os.path.join(EV, "TMP_SNAPSHOT_S5R6.tsv")
    body = ["# TMP_SNAPSHOT_S5R6.tsv -- /tmp top-level snapshot at P05-S5 R6 start (read only)",
            "# captured by s5r6_check.py --phase start; --phase end compares the live /tmp list against this record",
            "key" + TAB + "value",
            "TMP_COUNT" + TAB + str(cnt),
            "TMP_SHA256" + TAB + tsha]
    os.makedirs(EV, exist_ok=True)
    open(snaps, "w", encoding="utf-8").write(NL.join(body) + NL)
    record("TMP_SNAPSHOT_FILE", os.path.relpath(snaps, REPO))
    safe("TMP_SNAPSHOT_EMPTY_AT_START", lambda: "%d/%s" % (cnt, tsha),
         "0/01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b")

    pyc = pycache_now()
    record("PYCACHE_COUNT", len(pyc))
    record("PYCACHE_SET_SHA256", sha_b((NL.join(pyc) + NL).encode("utf-8")))
    safe("PYCACHE_BASELINE_22", lambda: len(pyc), EXP_PYCACHE_COUNT)
    safe("PYCACHE_BASELINE_SHA", lambda: sha_b((NL.join(pyc) + NL).encode("utf-8")), EXP_PYCACHE_SHA)


# ------------------------------------------------------------------ phase end
def phase_end():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("END_TIME_UTC", started)
    record("BASE_HEAD", EXP_BASE_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    record("ROUND", "P05-S5 R6 (s5r6, pure documentation sub-round)")

    base_err = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/registries/s5r2/ERRATA_S5.txt"])
    base_rul = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv"])
    base_r5 = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/P05_S5R5_REPORT.md"])
    base_rm = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":PROJECT_ROADMAP.md"])
    base_is = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":testing/s4test/ISSUE_REGISTRY.md"])
    record("BASE_ERRATA_BYTES", len(base_err))
    record("BASE_ERRATA_SHA256", sha_b(base_err))
    record("BASE_RULINGS_BYTES", len(base_rul))
    record("BASE_RULINGS_SHA256", sha_b(base_rul))
    record("BASE_R5REPORT_BYTES", len(base_r5))
    record("BASE_R5REPORT_SHA256", sha_b(base_r5))
    record("BASE_R5REPORT_FIRST95_SHA256", first_n_lines_sha(base_r5, 95))

    # ---- frozen tree / commits
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("BASE_COMMIT_PRESENT",
         lambda: sh(["git", "rev-parse", "--verify", EXP_BASE_HEAD + "^{commit}"]), EXP_BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA256_UNCHANGED",
         lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    def s4_clean():
        d = sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD", "--", "S4"])
        s = sh(["git", "status", "--porcelain=v1", "-uall", "--", "S4"])
        return "unmodified" if not d and not s else "diff=" + d + ";status=" + s
    safe("S4_DIR_ZERO_MODIFICATION", s4_clean, "unmodified")
    safe("ROUND_COMMITS_0_OR_1",
         lambda: "ok" if int(sh(["git", "rev-list", "--count", EXP_BASE_HEAD + "..HEAD"])) <= 1 else "too_many",
         "ok")

    def changed_paths():
        parts = set()
        d = sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD"])
        s = sh_raw(["git", "status", "--porcelain=v1", "-uall"])
        for line in d.splitlines():
            if line.strip():
                parts.add(line.strip())
        for line in s.splitlines():
            if not line.strip():
                continue
            p = line[3:]
            if " -> " in p:
                p = p.split(" -> ")[-1]
            parts.add(p.strip())
        return sorted(parts)
    record("ROUND_CHANGED_FILES", ",".join(changed_paths()) if changed_paths() else "none")
    def changed_ok():
        paths = changed_paths()
        good = all(p.startswith(WHITELIST) for p in paths) and any(
            p.startswith("checkpoints/p05/") for p in paths)
        return "ok" if good else "outside_whitelist"
    safe("ROUND_CHANGED_FILES_WITHIN_WHITELIST", changed_ok, "ok")
    safe("NO_DELETED_OR_RENAMED_ROUND_FILES",
         lambda: sh(["git", "diff", "--name-status", "--diff-filter=DR", EXP_BASE_HEAD]) or "none", "none")

    # ---- R5 report: first 95 lines unchanged, pure append (appendix D)
    cur_r5 = rd_b(R5REPORT)
    record("R5REPORT_BYTES", len(cur_r5))
    record("R5REPORT_SHA256", sha_b(cur_r5))
    record("R5REPORT_FIRST95_SHA256", first_n_lines_sha(cur_r5, 95))
    safe("R5REPORT_FIRST95_SHA_UNCHANGED", lambda: first_n_lines_sha(cur_r5, 95), EXP_R5REPORT_FIRST95_SHA)
    safe("R5REPORT_PURE_APPEND", lambda: "ok" if cur_r5.startswith(base_r5) else "prefix_changed", "ok")
    add5 = cur_r5[len(base_r5):].decode("utf-8") if cur_r5.startswith(base_r5) else ""
    record("R5REPORT_APPENDED_BYTES", len(cur_r5) - len(base_r5))

    def app5_has(frag):
        return frag in add5
    safe("R5REPORT_APPD_HEADING", lambda: int(app5_has("附录 D")), 1)
    safe("R5REPORT_APPD_ES5_17", lambda: int(app5_has("ES5-17")), 1)
    safe("R5REPORT_APPD_ESCAPED_PIPE", lambda: int(app5_has("\\| tee /dev/stderr \\| wc -l")), 1)
    safe("R5REPORT_APPD_POSCTRL_EVIDENCE", lambda: int(app5_has("evidence/p05-s5r5/POSCTRL_GATE_S5R5.txt")), 1)
    safe("R5REPORT_APPD_COUNTS", lambda: int(app5_has("COUNTS\\tpass=36\\tfail=0\\ttotal=36")), 1)

    # ---- ERRATA: pure append ES5-17
    cur_err = rd_b(ERRATA)
    record("ERRATA_S5_BYTES", len(cur_err))
    record("ERRATA_S5_SHA256", sha_b(cur_err))
    safe("ERRATA_PURE_APPEND", lambda: "ok" if cur_err.startswith(base_err) else "prefix_changed", "ok")
    add_err = cur_err[len(base_err):].decode("utf-8") if cur_err.startswith(base_err) else ""
    record("ERRATA_APPENDED_BYTES", len(cur_err) - len(base_err))
    ids = [l for l in cur_err.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_LAST_IS_ES5_17", lambda: ids[-1] if ids else "none", "ES5-17")
    safe("ERRATA_ES5_17_ONCE", lambda: ids.count("ES5-17"), 1)
    safe("ERRATA_ES5_17_ITEMS_ABC",
         lambda: "ok" if all(k in add_err for k in ("(a)", "(b)", "(c)", "- 事实", "- 影响", "- 证据", "- 处理方式"))
         else "missing", "ok")

    # ---- RULINGS: no user sign-off text -> unchanged, no U391
    cur_rul = rd_b(RULINGS)
    record("RULINGS_BYTES", len(cur_rul))
    record("RULINGS_SHA256", sha_b(cur_rul))
    safe("RULINGS_UNCHANGED_NO_SIGNOFF", lambda: sha_b(cur_rul), EXP_RULINGS_SHA)
    safe("RULINGS_HAS_NO_U391", lambda: "ok" if "U391" not in cur_rul.decode("utf-8") else "found", "ok")

    # ---- drafts / historical sign-off file unchanged
    safe("DRAFT_V1_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")), EXP_DRAFT_V2_SHA)
    safe("DRAFT_V3_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")), EXP_DRAFT_V3_SHA)
    safe("P05_S3_S4_SIGNOFF_SHA_UNCHANGED",
         lambda: sha_f(os.path.join(P05, "P05_S3_S4_SIGNOFF.md")), EXP_P3S4_SIGNOFF_SHA)

    # ---- sign-off: the user gave no P05-S5 sign-off text, so no file and no U391 (task brief section 2)
    safe("SIGNOFF_S5_ABSENT_NO_USER_TEXT",
         lambda: "absent" if not os.path.exists(SIGNOFF_S5) else "present", "absent")

    # ---- STATE.md: S5R6 version, waiting for the user, no "no work left"
    stt = rd(STATE)
    record("STATE_BYTES", len(stt.encode("utf-8")))
    record("STATE_SHA256", sha_b(stt.encode("utf-8")))
    safe("STATE_HAS_S5R6_ROW", lambda: int("S5R6" in stt), 1)
    safe("STATE_S5_PENDING_SIGNOFF", lambda: int("等待用户签收" in stt), 1)
    safe("STATE_NO_WUKEZUO", lambda: int("无可做" in stt), 0)
    safe("STATE_POINTS_TO_APPENDIX_C", lambda: int("附录 C" in stt), 1)
    safe("STATE_HAS_S5R5_COMPLETE", lambda: int("36/36" in stt and "COMPLETE" in stt), 1)
    safe("STATE_UNDER_8KB", lambda: int(len(stt.encode("utf-8")) <= 8192), 1)

    # ---- PROJECT_ROADMAP.md: exactly one changed line (P05 row, pure append inside the cell)
    cur_rm = rd(ROADMAP)
    record("ROADMAP_BYTES", len(cur_rm.encode("utf-8")))
    record("ROADMAP_SHA256", sha_b(cur_rm.encode("utf-8")))
    bl = base_rm.decode("utf-8").split(NL)
    cl = cur_rm.split(NL)

    def roadmap_one_append():
        if len(cl) != len(bl):
            return "line_count=%d/%d" % (len(cl), len(bl))
        diff = [i for i in range(len(bl)) if bl[i] != cl[i]]
        if diff != [50]:
            return "diff_lines=" + ",".join(str(i + 1) for i in diff[:5])
        if not (cl[50].endswith(" |") and bl[50].endswith(" |")):
            return "no_cell_delimiter"
        old_body, new_body = bl[50][:-2], cl[50][:-2]
        return "ok" if new_body.startswith(old_body) else "not_prefix_append"
    safe("ROADMAP_ONLY_P05_ROW_APPENDED", roadmap_one_append, "ok")
    safe("ROADMAP_HAS_ES5_15_16_SENTENCE",
         lambda: int(all(k in cur_rm for k in ("ES5-15/16", "FINAL_STATUS=INCOMPLETE", "36/36 FINAL_STATUS=COMPLETE",
                                               "P05_S5R5_REPORT.md 附录 C"))), 1)
    safe("ROADMAP_HAS_S5_PENDING", lambda: int("P05-S5 等待用户签收" in cur_rm), 1)
    p06 = [l for l in cl if l.startswith("| P06 |")]
    safe("ROADMAP_P06_ROW_UNCHANGED",
         lambda: "ok" if p06 and p06[0] == [l for l in bl if l.startswith("| P06 |")][0] else "changed", "ok")

    # ---- ISSUE_REGISTRY.md: exactly one inserted line, no OPEN status changed
    cur_is = rd(ISSUE)
    record("ISSUE_REGISTRY_BYTES", len(cur_is.encode("utf-8")))
    record("ISSUE_REGISTRY_SHA256", sha_b(cur_is.encode("utf-8")))
    bil = base_is.decode("utf-8").split(NL)
    cil = cur_is.split(NL)

    def issue_one_insert():
        if len(cil) != len(bil) + 1:
            return "line_count=%d/%d" % (len(cil), len(bil))
        for k in range(len(cil)):
            if cil[:k] + cil[k + 1:] == bil:
                line = cil[k]
                if line.startswith("> ") and "P05-S5" in line and "S5R5" in line and "S5R6" in line:
                    return "ok_line_%d" % (k + 1)
                return "bad_inserted_line"
        return "not_single_insert"
    # the expected insertion point is after the D003 status block (old line 35 -> new line 36)
    safe("ISSUE_REGISTRY_ONE_LINE_INSERTED", issue_one_insert, "ok_line_36")
    safe("ISSUE_REGISTRY_OPEN_ROWS_UNCHANGED",
         lambda: "ok" if all(l in cil for l in bil) else "removed_or_changed", "ok")

    # ---- R6 report
    r6 = rd(R6REPORT)
    record("R6REPORT_BYTES", len(r6.encode("utf-8")))
    record("R6REPORT_SHA256", sha_b(r6.encode("utf-8")))
    safe("R6_REPORT_CLOSING_SENTENCE",
         lambda: int("本轮已完成 P05-S5 R6 范围，等待用户审核" in r6), 1)
    safe("R6_REPORT_NO_P05_S6", lambda: int("P05-S6" in r6), 0)
    safe("R6_REPORT_NO_SELF_SIGNOFF",
         lambda: int(("P05-S5 已由用户签收" in r6) or ("已签收 P05-S5" in r6)), 0)
    safe("R6_REPORT_HAS_ES5_17", lambda: int("ES5-17" in r6), 1)
    safe("R6_REPORT_EVENT_TABLES",
         lambda: int(("越界写入尝试" in r6) and ("工具/脚本事件" in r6) and ("dsh-spill" in r6)), 1)
    safe("R6_REPORT_GIT_SECTION",
         lambda: int(("git log -1" in r6) and ("git status --short" in r6)), 1)

    # ---- manifests (read only)
    reg5 = verify_sums_dir(REG5)
    safe("S5R5_REGISTRY_SUMS_ALL_OK_12",
         lambda: "%d/%s" % (reg5[0], "OK" if not reg5[1] else "BAD:" + ",".join(reg5[1][:3])),
         "%d/OK" % EXP_REG5_ITEMS)
    reg4 = verify_sums_dir(REG4)
    safe("S5R4_REGISTRY_SUMS_ALL_OK_15",
         lambda: "%d/%s" % (reg4[0], "OK" if not reg4[1] else "BAD:" + ",".join(reg4[1][:3])),
         "%d/OK" % EXP_REG4_ITEMS)
    ev5 = verify_sums_dir(EV5)
    safe("S5R5_EVIDENCE_SUMS_ALL_OK_20",
         lambda: "%d/%s" % (ev5[0], "OK" if not ev5[1] else "BAD:" + ",".join(ev5[1][:3])),
         "%d/OK" % EXP_EV5_ITEMS)
    safe("S5R5_GATE_END_SHA_UNCHANGED",
         lambda: sha_f(os.path.join(EV5, "gate/GATE_S5R5_end.txt")), EXP_S5R5_GATE_SHA)

    # ---- registries/s5r6 pre-gate shape (the formal end-gate file is copied after the gate)
    PREGATE = ["ERRATA_APPEND_S5R6.tsv", "GATE_S5R6_start.txt", "TMP_SNAPSHOT_S5R6.tsv"]

    def reg6_shape():
        if not os.path.isdir(REG6):
            return "absent"
        got = sorted(os.listdir(REG6))
        want = sorted(PREGATE + ["SHA256SUMS.txt"])
        return "ok" if got == want else "files=" + ",".join(got[:6])
    safe("REGISTRY_S5R6_PREGATE_SHAPE", reg6_shape, "ok")

    def reg6_sums():
        if not os.path.isfile(os.path.join(REG6, "SHA256SUMS.txt")):
            return "absent"
        listed, bad = [], []
        for line in rd(os.path.join(REG6, "SHA256SUMS.txt")).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            h, rel = line.split("  ", 1)
            listed.append(rel)
            if not os.path.isfile(os.path.join(REG6, rel)) or sha_f(os.path.join(REG6, rel)) != h:
                bad.append(rel)
        return "ok" if (sorted(listed) == sorted(PREGATE) and not bad) else "bad"
    safe("REGISTRY_S5R6_SUMS_PREGATE_ALL_OK", reg6_sums, "ok")

    def reg6_matches_evidence():
        pairs = [("GATE_S5R6_start.txt", os.path.join(EV, "GATE_S5R6_start.txt")),
                 ("ERRATA_APPEND_S5R6.tsv", os.path.join(EV, "ERRATA_APPEND_S5R6.tsv")),
                 ("TMP_SNAPSHOT_S5R6.tsv", os.path.join(EV, "TMP_SNAPSHOT_S5R6.tsv"))]
        for rel, src in pairs:
            if not os.path.isfile(os.path.join(REG6, rel)) or sha_f(os.path.join(REG6, rel)) != sha_f(src):
                return "mismatch:" + rel
        return "ok"
    safe("REGISTRY_S5R6_COPIES_MATCH_EVIDENCE", reg6_matches_evidence, "ok")

    # ---- /tmp snapshot unchanged + no new __pycache__
    snap = read_kv(os.path.join(EV, "TMP_SNAPSHOT_S5R6.tsv"))
    cnt, tsha, _names = tmp_live()
    record("TMP_COUNT", cnt)
    record("TMP_SHA256", tsha)
    safe("TMP_SNAPSHOT_UNCHANGED", lambda: "%s/%s" % (cnt, tsha),
         "%s/%s" % (snap["TMP_COUNT"], snap["TMP_SHA256"]))
    pyc = pycache_now()
    record("PYCACHE_COUNT", len(pyc))
    record("PYCACHE_SET_SHA256", sha_b((NL.join(pyc) + NL).encode("utf-8")))
    safe("NO_NEW_PYCACHE", lambda: sha_b((NL.join(pyc) + NL).encode("utf-8")), EXP_PYCACHE_SHA)


def write_gate(phase, out_name):
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R6 %s gate %s (%s)" % (phase, out_name, datetime.datetime.now(datetime.timezone.utc)
                                             .strftime("%Y-%m-%dT%H:%M:%SZ"))]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails)
                 + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    os.makedirs(EV, exist_ok=True)
    with open(os.path.join(EV, out_name), "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print(lines[-3])
    print(lines[-2])
    for n, e, a, ok in CHECKS:
        if not ok:
            print("FAIL\t%s\texpected=%s\tactual=%s" % (n, e, a))
    for n, x in CRASHED:
        print("CRASHED\t%s\t%s" % (n, x))
    print("WROTE " + os.path.relpath(os.path.join(EV, out_name), REPO))
    return 0 if not fails and not CRASHED else 1


def main():
    args = sys.argv[1:]
    phase = "start"
    out = None
    i = 0
    while i < len(args):
        if args[i] == "--phase":
            phase = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        else:
            print("HARD_STOP unknown argument: " + args[i])
            return 2
    if phase not in ("start", "end"):
        print("HARD_STOP --phase must be start or end")
        return 2
    if out is None:
        out = "GATE_S5R6_%s.txt" % phase
    if not re.match(r"^GATE_S5R6_[A-Za-z0-9_]+\.txt$", out):
        print("HARD_STOP --out must be GATE_S5R6_<name>.txt")
        return 2
    if phase == "start":
        phase_start()
    else:
        phase_end()
    return write_gate(phase, out)


if __name__ == "__main__":
    sys.exit(main())
