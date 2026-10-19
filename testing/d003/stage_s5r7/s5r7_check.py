#!/usr/bin/env python3
# s5r7_check.py -- P05-S5 R7 gate (pure documentation sub-round; task brief sections 0, 2 and 4).
# One script, two read-only phases (the pre-run and the formal end run share one code path; only --out differs):
#   --phase start : the opening baseline named in the task brief, the immutable S5R4/S5R5/S5R6
#                   evidence/registry manifests, the S5R5/S5R6 end-gate files, frozen inputs, the
#                   snapshots taken by s5r7_tmpsnap.py and the absence of R7 outputs.
#   --phase end   : closing checks: S4/ untouched; RULINGS pure append with exactly one new U391 row and
#                   unchanged prefix; ERRATA unchanged; P05_S5_SIGNOFF.md present with section 2 byte-equal to
#                   the task-brief section 1 text; drafts v1/v2/v3, P05_S3_S4_SIGNOFF.md and historical reports
#                   unchanged; ROADMAP only P05 append / P06 status-cell change; ISSUE_REGISTRY exactly one
#                   inserted line; manifests s5r4/s5r5/s5r6 and evidence p05-s5r5 all OK; changed files inside
#                   the whitelist; top-level temporary snapshot unchanged; no new __pycache__; STATE free of
#                   projected gate-result phrases; R7 registry pre-gate shape.
# This script never touches the system temporary directory itself: the only snapshot command of the round is
# s5r7_tmpsnap.py, and this script only reads the snapshot file it wrote under the evidence directory.
import os, re, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
EV5 = os.path.join(P05, "evidence/p05-s5r5")
REG4 = os.path.join(P05, "registries/s5r4")
REG5 = os.path.join(P05, "registries/s5r5")
REG6 = os.path.join(P05, "registries/s5r6")
REG7 = os.path.join(P05, "registries/s5r7")
STAGE = os.path.join(REPO, "testing/d003/stage_s5r7")
TEXTFILE = os.path.join(STAGE, "s5r7_signoff_text.txt")
TAB = chr(9)
NL = chr(10)
TODAY = "2026-10-19"

EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_BASE_HEAD = "0358a06ee41f0b78984834bfdb758dd1a793296c"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_REG5_SUMS_SHA = "b8be693b70f859c43d74764553c7dd57f11f0fcc0ae931796fcd1d33f9ec0ed9"
EXP_REG5_ITEMS = 12
EXP_REG4_SUMS_SHA = "7f2b30eb026ccb28e9c686bba5ceaff3bdee1ca47a611e6856e8b68a3aaed9a3"
EXP_REG4_ITEMS = 15
EXP_REG6_SUMS_SHA = "cbcfa69fd3c19cc9eac1bcf74a3deb3071fbb99e5694d11e34e210c2b5cd6f1f"
EXP_REG6_ITEMS = 4
EXP_EV5_SUMS_SHA = "ff06d0ff9b8e78cf6a4dd2cc9ac8765334368adbcb0d3e69460ca1f480b1262e"
EXP_EV5_ITEMS = 20
EXP_S5R5_GATE_SHA = "1fd857449a426651c8e03a1721bd606eb502ccf8a6374623066d65565be4458f"
EXP_S5R6_GATE_SHA = "58676104fa8c02eaf2f6a4cf238a9e745ed0e12b40aa250074d242cf00212fd0"
EXP_RULINGS_BASE_BYTES = 156852
EXP_RULINGS_BASE_SHA = "d5742e70c40ebb7a08585860d98557eabcd0aaebbdbabb4f47e9be950a38e9c3"
EXP_RULINGS_MAX = "U391"
EXP_ERRATA_BYTES = 17630
EXP_ERRATA_SHA = "4af120527c73e5ef8189c1c09f1d055750b01f6e9bc8f5f9aed88d1a47ba9d6c"
EXP_STATE_BASE_SHA = "303faf5d1066421ada37424d835ad5f2e4bbde1f3a21ff96e03cd305dc2932fc"
EXP_ROADMAP_BASE_SHA = "6bb1cfb25b0016f3452b1985f5229a66f3bd48075331bee5613bd16d261b3e2b"
EXP_ISSUE_BASE_SHA = "85cd329fdfa57cfb0bc5ab7eeee447e711b5a322c9337300e123f2039817b9de"
EXP_DRAFT_V1_SHA = "c08bac3f05fe1c2ee087d093cc0dcf9d9cf96e1666f2472c534fb6162e41da93"
EXP_DRAFT_V2_SHA = "67876cd420c1ab44a6bd300f36ba2ae6cd382bdc855538203747e528d5acb69e"
EXP_DRAFT_V3_SHA = "c7fc843d0d9f90c3b89d9154e4660749ae82c50b29b7b07dd2c0aa3b6afed500"
EXP_P3S4_SIGNOFF_SHA = "7b5b412a9fa363ad47958d58a7500abb47c2c003b0a7fc79e72ad0e578c8f4ae"
EXP_R3REPORT_SHA = "30a0f1d2d8ec073c124642279cee149ef17d9e437329a467ce5df220c26fe0bb"
EXP_R4REPORT_SHA = "2ceba6d197c8f026a4480432cf58bacff5021d999107630dd286d17d66fd47c6"
EXP_R5REPORT_SHA = "fe230b9d5a75f5d9ff125c8afb2493f65453ecbcdb61dd800b35ca1acaba8c9b"
EXP_R6REPORT_SHA = "e5d85315d27006e6c24fb75ebf228d1e7c904d304688a682309a135b14382842"
EXP_SIGNOFF_TEXT_BYTES = 1063
EXP_SIGNOFF_TEXT_SHA = "c7af2fb22c9cc9f9ec04d4bfb83cce73478b0a2019ce951f12b1c0804df3f65e"
EXP_PYCACHE_COUNT = 22
EXP_PYCACHE_SHA = "fd6481c0a59399af539e9da2777884c10a70fd36f57b425787ae906ff8f20fbd"

RULINGS = os.path.join(P05, "registries/RULINGS.tsv")
ERRATA = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
STATE = os.path.join(P05, "STATE.md")
ROADMAP = os.path.join(REPO, "PROJECT_ROADMAP.md")
ISSUE = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
SIGNOFF_S5 = os.path.join(P05, "P05_S5_SIGNOFF.md")
R7REPORT = os.path.join(P05, "P05_S5R7_REPORT.md")
R6REPORT = os.path.join(P05, "P05_S5R6_REPORT.md")
R5REPORT = os.path.join(P05, "P05_S5R5_REPORT.md")
R4REPORT = os.path.join(P05, "P05_S5R4_REPORT.md")
R3REPORT = os.path.join(P05, "P05_S5R3_REPORT.md")
WHITELIST = ("checkpoints/p05/", "testing/d003/stage_s5r7/",
             "testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md")

SEC2_HEAD = "## 2 范围声明（签收原文，逐字照录）" + NL + NL
NEXT3_HEAD = NL + "## 3 "
TMP_NEEDLE = re.compile((b"(?<![A-Za-z0-9_])" + b"/" + b"tmp" + b"(?![A-Za-z0-9_])").decode("latin-1"))

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


def read_gate_kv(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 3 and f[0] == "RECORD" and f[2].startswith("value="):
            d[f[1]] = f[2][len("value="):]
    return d


def tmp_snapshot(label_out):
    snap = read_kv(label_out)
    return snap["TMP_COUNT"], snap["TMP_SHA256"]


def stage_files_with_tmp_token():
    hits = []
    if not os.path.isdir(STAGE):
        return ["missing_stage_dir"]
    for name in sorted(os.listdir(STAGE)):
        p = os.path.join(STAGE, name)
        if not os.path.isfile(p):
            continue
        data = open(p, "rb").read().decode("latin-1")
        if TMP_NEEDLE.search(data):
            hits.append(name)
    return hits


def signoff_section2():
    data = rd_b(SIGNOFF_S5)
    head = SEC2_HEAD.encode("utf-8")
    nxt = NEXT3_HEAD.encode("utf-8")
    if head not in data:
        return "missing_section2_head"
    rest = data.split(head, 1)[1]
    if nxt not in rest:
        return "missing_section3_head"
    return rest.split(nxt, 1)[0]


def gate_reported_results(p):
    t = rd(p)
    counts = re.search(r"^COUNTS\tpass=(\d+)\tfail=(\d+)\ttotal=(\d+)$", t, re.M)
    fails = re.search(r"^FAILS=(\d+)$", t, re.M)
    crashed = re.search(r"^CHECK_CRASHED=(\d+)$", t, re.M)
    if not (counts and fails and crashed):
        return "unparsable"
    return "%s/%s/%s/%s" % (counts.group(1), counts.group(2), counts.group(3), fails.group(1))


# ------------------------------------------------------------------ phase start
def phase_start():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("START_TIME_UTC", started)
    record("BASE_HEAD", EXP_BASE_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    record("ROUND", "P05-S5 R7 (s5r7, pure documentation sub-round: P05-S5 sign-off entry)")
    record("SIGNOFF_TEXT_ANCHOR", os.path.relpath(TEXTFILE, REPO))
    record("SIGNOFF_TEXT_BYTES", EXP_SIGNOFF_TEXT_BYTES)
    record("SIGNOFF_TEXT_SHA256", EXP_SIGNOFF_TEXT_SHA)
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_R6_II", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("BASE_COMMIT_PRESENT",
         lambda: sh(["git", "rev-parse", "--verify", EXP_BASE_HEAD + "^{commit}"]), EXP_BASE_HEAD)
    safe("S4_DIR_ZERO_MODIFICATION",
         lambda: sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "--", "S4"]) or "unmodified", "unmodified")

    def status_only_stage():
        st = sh(["git", "status", "--porcelain=v1", "-uall"])
        bad = [ln for ln in st.splitlines() if ln.strip()
               and not re.match(r"^\?\? testing/d003/stage_s5r7/[^/]+$", ln.strip())]
        return "only_stage_s5r7" if not bad else ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_STAGE_S5R7", status_only_stage, "only_stage_s5r7")

    rb = rd_b(RULINGS)
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    safe("RULINGS_START_BYTES", lambda: len(rb), EXP_RULINGS_BASE_BYTES)
    safe("RULINGS_START_SHA256", lambda: sha_b(rb), EXP_RULINGS_BASE_SHA)

    def rulings_max_u():
        mu = 0
        for line in rb.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    safe("RULINGS_START_MAX_U390", rulings_max_u, "U390")
    safe("RULINGS_START_LINES_5_FIELDS",
         lambda: "ok" if all(len(l.split(TAB)) == 5 for l in rb.decode("utf-8").splitlines()
                             if l.strip() and not l.startswith("#")) else "bad", "ok")

    def rulings_matches_s5r6_record():
        rec = read_gate_kv(os.path.join(REG6, "GATE_S5R6_end.txt"))
        return "ok" if rec.get("RULINGS_SHA256") == sha_b(rb) else "record=" + str(rec.get("RULINGS_SHA256"))
    safe("RULINGS_SHA_MATCHES_S5R6_RECORD", rulings_matches_s5r6_record, "ok")

    eb = rd_b(ERRATA)
    record("ERRATA_S5_BYTES", len(eb))
    record("ERRATA_S5_SHA256", sha_b(eb))
    safe("ERRATA_START_BYTES", lambda: len(eb), EXP_ERRATA_BYTES)
    safe("ERRATA_START_SHA256", lambda: sha_b(eb), EXP_ERRATA_SHA)
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_START_LAST_IS_ES5_17", lambda: last_e[-1] if last_e else "none", "ES5-17")
    safe("ERRATA_START_ES5_17_ONCE", lambda: last_e.count("ES5-17"), 1)

    st = rd_b(STATE)
    record("STATE_BYTES", len(st))
    record("STATE_SHA256", sha_b(st))
    safe("STATE_START_SHA", lambda: sha_b(st), EXP_STATE_BASE_SHA)
    safe("STATE_START_NO_S5R7", lambda: "present" if "S5R7" in st.decode("utf-8") else "absent", "absent")

    safe("DRAFT_V1_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")), EXP_DRAFT_V2_SHA)
    safe("DRAFT_V3_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")), EXP_DRAFT_V3_SHA)
    safe("P05_S3_S4_SIGNOFF_SHA",
         lambda: sha_f(os.path.join(P05, "P05_S3_S4_SIGNOFF.md")), EXP_P3S4_SIGNOFF_SHA)
    safe("SIGNOFF_S5_ABSENT", lambda: "absent" if not os.path.exists(SIGNOFF_S5) else "present", "absent")
    safe("ROADMAP_START_SHA", lambda: sha_f(ROADMAP), EXP_ROADMAP_BASE_SHA)
    safe("ISSUE_REGISTRY_START_SHA", lambda: sha_f(ISSUE), EXP_ISSUE_BASE_SHA)
    safe("R7_REPORT_ABSENT", lambda: "absent" if not os.path.exists(R7REPORT) else "present", "absent")
    safe("REG7_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(REG7) else "present", "absent")
    safe("TEXT_ANCHOR_BYTES", lambda: len(rd_b(TEXTFILE)), EXP_SIGNOFF_TEXT_BYTES)
    safe("TEXT_ANCHOR_SHA", lambda: sha_f(TEXTFILE), EXP_SIGNOFF_TEXT_SHA)

    def ev_precontent():
        if not os.path.isdir(EV):
            return "absent"
        allowed = {"tmp", "safe_run.log", "TMP_SNAPSHOT_S5R7.tsv"}
        extra = sorted(set(os.listdir(EV)) - allowed)
        if extra:
            return "extra=" + ",".join(extra[:4])
        logp = os.path.join(EV, "safe_run.log")
        if os.path.isfile(logp):
            bad = [l for l in rd(logp).splitlines()
                   if "s5r7_tmpsnap.py" not in l and "s5r7_check.py" not in l]
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
    reg4 = verify_sums_dir(REG4)
    record("S5R4_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG4, "SHA256SUMS.txt")))
    safe("S5R4_REGISTRY_SUMS_SHA", lambda: sha_f(os.path.join(REG4, "SHA256SUMS.txt")), EXP_REG4_SUMS_SHA)
    safe("S5R4_REGISTRY_SUMS_ALL_OK_15",
         lambda: "%d/%s" % (reg4[0], "OK" if not reg4[1] else "BAD:" + ",".join(reg4[1][:3])),
         "%d/OK" % EXP_REG4_ITEMS)
    reg6 = verify_sums_dir(REG6)
    record("S5R6_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG6, "SHA256SUMS.txt")))
    safe("S5R6_REGISTRY_SUMS_SHA", lambda: sha_f(os.path.join(REG6, "SHA256SUMS.txt")), EXP_REG6_SUMS_SHA)
    safe("S5R6_REGISTRY_SUMS_ALL_OK_4",
         lambda: "%d/%s" % (reg6[0], "OK" if not reg6[1] else "BAD:" + ",".join(reg6[1][:3])),
         "%d/OK" % EXP_REG6_ITEMS)
    ev5 = verify_sums_dir(EV5)
    record("S5R5_EVIDENCE_SUMS_SHA256", sha_f(os.path.join(EV5, "SHA256SUMS.txt")))
    safe("S5R5_EVIDENCE_SUMS_SHA", lambda: sha_f(os.path.join(EV5, "SHA256SUMS.txt")), EXP_EV5_SUMS_SHA)
    safe("S5R5_EVIDENCE_SUMS_ALL_OK_20",
         lambda: "%d/%s" % (ev5[0], "OK" if not ev5[1] else "BAD:" + ",".join(ev5[1][:3])),
         "%d/OK" % EXP_EV5_ITEMS)

    g5 = os.path.join(EV5, "gate/GATE_S5R5_end.txt")
    record("S5R5_GATE_END_SHA256", sha_f(g5))
    safe("S5R5_GATE_END_SHA", lambda: sha_f(g5), EXP_S5R5_GATE_SHA)
    safe("S5R5_GATE_END_FAILS_ZERO",
         lambda: re.search(r"FAILS=(\d+)", rd(g5)).group(1), "0")

    g6 = os.path.join(REG6, "GATE_S5R6_end.txt")
    record("S5R6_GATE_END_SHA256", sha_f(g6))
    safe("S5R6_GATE_END_SHA", lambda: sha_f(g6), EXP_S5R6_GATE_SHA)
    safe("S5R6_GATE_END_COUNTS_53_0_53",
         lambda: "53/0/53/0" if gate_reported_results(g6) == "53/0/53/0" else gate_reported_results(g6),
         "53/0/53/0")
    safe("S5R6_GATE_END_FAILS_ZERO",
         lambda: re.search(r"FAILS=(\d+)", rd(g6)).group(1), "0")
    # The task brief says the S5R6 gate file contains FINAL_STATUS=COMPLETE.  The file itself carries
    # COUNTS/FAILS; the FINAL_STATUS=COMPLETE line lives in P05_S5R6_REPORT.md appendix C.  Check the
    # combination and record the actual location (no fix: the underlying condition is the same).
    r6t = rd(R6REPORT)
    app_c = r6t.split("## 附录 C", 1)[-1]
    record("S5R6_FINAL_STATUS_LOCATION", "P05_S5R6_REPORT.md appendix C (brief wording says gate file)")
    safe("S5R6_FINAL_STATUS_COMPLETE",
         lambda: "complete" if ("FINAL_STATUS=COMPLETE" in app_c) else "missing", "complete")

    snaps = os.path.join(EV, "TMP_SNAPSHOT_S5R7.tsv")
    record("TMP_SNAPSHOT_FILE", os.path.relpath(snaps, REPO))
    if not os.path.isfile(snaps):
        record("TMP_SNAPSHOT_START_STATE", "absent")
        safe("TMP_SNAPSHOT_START_PARSED", lambda: "absent", "present")
        record("TMP_COUNT", "NA")
        record("TMP_SHA256", "NA")
    else:
        cnt, tsha = tmp_snapshot(snaps)
        record("TMP_COUNT", cnt)
        record("TMP_SHA256", tsha)
        safe("TMP_SNAPSHOT_START_PARSED",
             lambda: "ok" if re.match(r"^\d+$", cnt) and re.match(r"^[0-9a-f]{64}$", tsha) else "bad", "ok")

    pyc = pycache_now()
    record("PYCACHE_COUNT", len(pyc))
    record("PYCACHE_SET_SHA256", sha_b((NL.join(pyc) + NL).encode("utf-8")))
    safe("PYCACHE_BASELINE_22", lambda: len(pyc), EXP_PYCACHE_COUNT)
    safe("PYCACHE_BASELINE_SHA", lambda: sha_b((NL.join(pyc) + NL).encode("utf-8")), EXP_PYCACHE_SHA)
    safe("TMP_TOKEN_ONLY_IN_TMSNAP",
         lambda: ",".join(stage_files_with_tmp_token()), "s5r7_tmpsnap.py")


# ------------------------------------------------------------------ phase end
def phase_end():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("END_TIME_UTC", started)
    record("BASE_HEAD", EXP_BASE_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    record("ROUND", "P05-S5 R7 (s5r7, pure documentation sub-round: P05-S5 sign-off entry)")
    record("SIGNOFF_TEXT_BYTES", EXP_SIGNOFF_TEXT_BYTES)
    record("SIGNOFF_TEXT_SHA256", EXP_SIGNOFF_TEXT_SHA)

    base_err = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/registries/s5r2/ERRATA_S5.txt"])
    base_rul = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv"])
    base_rm = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":PROJECT_ROADMAP.md"])
    base_is = subprocess.check_output(["git", "show", EXP_BASE_HEAD + ":testing/s4test/ISSUE_REGISTRY.md"])
    record("BASE_RULINGS_BYTES", len(base_rul))
    record("BASE_RULINGS_SHA256", sha_b(base_rul))

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
        for line in sh(["git", "diff", "--name-only", EXP_BASE_HEAD, "HEAD"]).splitlines():
            if line.strip():
                parts.add(line.strip())
        for line in sh_raw(["git", "status", "--porcelain=v1", "-uall"]).splitlines():
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

    # ---- RULINGS: pure append, exactly one new row U391, prefix sha unchanged
    cur_rul = rd_b(RULINGS)
    record("RULINGS_BYTES", len(cur_rul))
    record("RULINGS_SHA256", sha_b(cur_rul))
    safe("RULINGS_PURE_APPEND", lambda: "ok" if cur_rul.startswith(base_rul) else "prefix_changed", "ok")
    safe("RULINGS_PREFIX_SHA_UNCHANGED", lambda: sha_b(cur_rul[:len(base_rul)]), EXP_RULINGS_BASE_SHA)
    add_rul = cur_rul[len(base_rul):] if cur_rul.startswith(base_rul) else b""
    record("RULINGS_APPENDED_BYTES", len(add_rul))
    add_lines = [l for l in add_rul.decode("utf-8").split(NL) if l.strip()]
    safe("RULINGS_EXACTLY_ONE_NEW_ROW", lambda: len(add_lines), 1)
    safe("RULINGS_NEW_ROW_U391",
         lambda: add_lines[0].split(TAB)[0] if add_lines else "none", "U391")
    safe("RULINGS_NEW_ROW_5_FIELDS",
         lambda: len(add_lines[0].split(TAB)) if add_lines else 0, 5)
    safe("RULINGS_NEW_ROW_STATUS_ACTIVE",
         lambda: add_lines[0].split(TAB)[4] if add_lines and len(add_lines[0].split(TAB)) == 5 else "none", "生效")
    safe("RULINGS_NEW_ROW_SOURCE_S5R7",
         lambda: "ok" if add_lines and "用户对话签收原文（P05-S5 R7 任务书 §1）" in add_lines[0] else "missing", "ok")
    safe("RULINGS_NEW_ROW_HAS_TEXT_SHA",
         lambda: "ok" if add_lines and EXP_SIGNOFF_TEXT_SHA in add_lines[0] else "missing", "ok")

    def rulings_max_u():
        mu = 0
        for line in cur_rul.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    safe("RULINGS_MAX_IS_U391", rulings_max_u, EXP_RULINGS_MAX)

    # ---- ERRATA: unchanged this round
    cur_err = rd_b(ERRATA)
    record("ERRATA_S5_BYTES", len(cur_err))
    record("ERRATA_S5_SHA256", sha_b(cur_err))
    safe("ERRATA_UNCHANGED", lambda: sha_b(cur_err), EXP_ERRATA_SHA)

    # ---- sign-off file
    safe("SIGNOFF_S5_EXISTS", lambda: "present" if os.path.isfile(SIGNOFF_S5) else "absent", "present")
    sec2 = signoff_section2()
    record("SIGNOFF_S5_SECTION2_SHA256", sha_b(sec2) if isinstance(sec2, bytes) else "unparsable")
    safe("SIGNOFF_S5_SECTION2_BYTES_EQUAL_TASK_BRIEF_SECTION1",
         lambda: "equal" if sec2 == rd_b(TEXTFILE) else "different", "equal")
    safe("SIGNOFF_S5_SECTION2_SHA",
         lambda: sha_b(sec2) if isinstance(sec2, bytes) else "bad", EXP_SIGNOFF_TEXT_SHA)
    sgt = rd(SIGNOFF_S5)

    def signoff_table():
        rows = [l for l in sgt.split(NL) if l.startswith("| P05-S")]
        if len(rows) != 5:
            return "rows=%d" % len(rows)
        for k in range(1, 6):
            r = [x for x in rows if x.startswith("| P05-S%d |" % k)]
            if not r or "已由用户签收" not in r[0]:
                return "bad_S%d" % k
        s5r = [x for x in rows if x.startswith("| P05-S5 |")][0]
        return "ok" if TODAY in s5r else "s5_date"
    safe("SIGNOFF_S5_TABLE_5_STAGES_SIGNED", signoff_table, "ok")
    safe("SIGNOFF_S5_SECTIONS_1_2_3_4",
         lambda: "ok" if all(("## %d " % k) in sgt for k in (1, 2, 3, 4)) else "missing", "ok")
    safe("SIGNOFF_S5_IMPLIES_P06",
         lambda: "ok" if ("P06" in sgt and "可启动" in sgt) else "missing", "ok")
    safe("SIGNOFF_S5_TRANSFERRED_ITEMS",
         lambda: "ok" if all(k in sgt for k in ("D017", "R-P05-01", "F10", "F8", "allzero",
                                                "P05_S5_OPEN_ITEMS.tsv")) else "missing", "ok")
    safe("SIGNOFF_S5_HISTORICAL_NOTE",
         lambda: "ok" if ("历史说明" in sgt and "写于 S5 开始前" in sgt and "P05_S3_S4_SIGNOFF.md" in sgt)
         else "missing", "ok")
    safe("SIGNOFF_S5_DECLARATION",
         lambda: "ok" if "本记录由执行者依据用户授权写入，执行者未自行宣布任何阶段完成" in sgt else "missing", "ok")

    # ---- frozen drafts / historical sign-off file / reports
    safe("DRAFT_V1_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")), EXP_DRAFT_V2_SHA)
    safe("DRAFT_V3_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")), EXP_DRAFT_V3_SHA)
    safe("P05_S3_S4_SIGNOFF_SHA_UNCHANGED",
         lambda: sha_f(os.path.join(P05, "P05_S3_S4_SIGNOFF.md")), EXP_P3S4_SIGNOFF_SHA)
    safe("P05_S5R3_REPORT_SHA_UNCHANGED", lambda: sha_f(R3REPORT), EXP_R3REPORT_SHA)
    safe("P05_S5R4_REPORT_SHA_UNCHANGED", lambda: sha_f(R4REPORT), EXP_R4REPORT_SHA)
    safe("P05_S5R5_REPORT_SHA_UNCHANGED", lambda: sha_f(R5REPORT), EXP_R5REPORT_SHA)
    safe("P05_S5R6_REPORT_SHA_UNCHANGED", lambda: sha_f(R6REPORT), EXP_R6REPORT_SHA)

    # ---- STATE.md: S5 signed, U391 recorded, no projected gate result
    stt = rd(STATE)
    record("STATE_BYTES", len(stt.encode("utf-8")))
    record("STATE_SHA256", sha_b(stt.encode("utf-8")))
    safe("STATE_HAS_S5R7_ROW", lambda: int("S5R7" in stt), 1)
    safe("STATE_STAGE_ALL_FIVE_SIGNED", lambda: int("S1–S5 已由用户签收" in stt), 1)
    safe("STATE_S5_SIGNOFF_ROW_U391", lambda: int("已签收（U391）" in stt), 1)
    safe("STATE_POINTS_TO_APPENDIX_C", lambda: int("附录 C" in stt), 1)
    safe("STATE_UNDER_8KB", lambda: int(len(stt.encode("utf-8")) <= 8192), 1)

    def state_gate_phrases():
        pats = [r"FAILS=\d+", r"门禁.*(?:通过|PASS)"]
        return sum(len(re.findall(p, stt)) for p in pats)
    safe("STATE_NO_GATE_RESULT_PHRASES", state_gate_phrases, 0)

    # ---- PROJECT_ROADMAP.md: P05 append only, P06 status cell only, other lines unchanged
    cur_rm = rd(ROADMAP)
    record("ROADMAP_BYTES", len(cur_rm.encode("utf-8")))
    record("ROADMAP_SHA256", sha_b(cur_rm.encode("utf-8")))
    bl = base_rm.decode("utf-8").split(NL)
    cl = cur_rm.split(NL)

    def roadmap_lines():
        if len(cl) != len(bl):
            return "line_count=%d/%d" % (len(cl), len(bl))
        diff = [i for i in range(len(bl)) if bl[i] != cl[i]]
        if diff != [50, 51]:
            return "diff_lines=" + ",".join(str(i + 1) for i in diff[:5])
        return "ok"
    safe("ROADMAP_ONLY_P05_ROW_APPENDED_AND_P06_STATUS", roadmap_lines, "ok")

    def roadmap_p05():
        if len(cl) != len(bl):
            return "line_count"
        if not (cl[50].endswith(" |") and bl[50].endswith(" |")):
            return "no_cell_delimiter"
        old_body, new_body = bl[50][:-2], cl[50][:-2]
        return "ok" if new_body.startswith(old_body) else "not_prefix_append"
    safe("ROADMAP_P05_ROW_PREFIX_APPEND", roadmap_p05, "ok")
    safe("ROADMAP_P05_ROW_HAS_SIGNOFF_CLAUSE",
         lambda: int(all(k in rd(ROADMAP) for k in ("P05-S5 已由用户签收（U391", "P05 有限范围收口",
                                                   "checkpoints/p05/P05_S5_SIGNOFF.md"))), 1)

    def roadmap_p06():
        if len(cl) != len(bl):
            return "line_count"
        a = bl[51].split("|")
        b = cl[51].split("|")
        if len(a) != len(b) or len(a) < 3:
            return "cell_count"
        if a[:-2] != b[:-2]:
            return "non_status_cell_changed"
        if a[-2].strip() != "待执行" or b[-2].strip() != "待启动（前置 P05 已签收）":
            return "status=" + b[-2].strip()
        return "ok"
    safe("ROADMAP_P06_ROW_ONLY_STATUS_CELL_CHANGED", roadmap_p06, "ok")

    def roadmap_other_lines_sha():
        keep = [bl[i] for i in range(len(bl)) if i not in (50, 51)]
        keep2 = [cl[i] for i in range(len(cl)) if i not in (50, 51)]
        return "ok" if sha_b((NL.join(keep) + NL).encode("utf-8")) == sha_b((NL.join(keep2) + NL).encode("utf-8")) else "changed"
    safe("ROADMAP_OTHER_LINES_SHA_UNCHANGED", roadmap_other_lines_sha, "ok")

    # ---- ISSUE_REGISTRY.md: exactly one inserted line, no OPEN row changed
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
                if ("已由用户签收" in line and "P05_S5_OPEN_ITEMS.tsv" in line
                        and "U391" in line and "OPEN" in line):
                    return "ok_line_%d" % (k + 1)
                return "bad_inserted_line"
        return "not_single_insert"
    safe("ISSUE_REGISTRY_ONE_LINE_INSERTED", issue_one_insert, "ok_line_37")
    safe("ISSUE_REGISTRY_OPEN_ROWS_UNCHANGED",
         lambda: "ok" if all(l in cil for l in bil) else "removed_or_changed", "ok")

    # ---- R7 report body (committed in (i); appendix C is added after the formal gate)
    r7 = rd(R7REPORT)
    record("R7REPORT_BYTES", len(r7.encode("utf-8")))
    record("R7REPORT_SHA256", sha_b(r7.encode("utf-8")))
    safe("R7_REPORT_CLOSING_SENTENCE",
         lambda: int("本轮已完成 P05-S5 R7 范围，等待用户审核" in r7), 1)
    safe("R7_REPORT_NO_P05_S6", lambda: int(("P05-" + "S6") in r7), 0)
    safe("R7_REPORT_NO_SELF_ANNOUNCE",
         lambda: int(("执行者宣布" in r7) or ("由执行者签收" in r7)), 0)
    safe("R7_REPORT_STATES_SIGNOFF_SOURCE",
         lambda: int(("用户在对话中给出" in r7) and ("签收原文" in r7)), 1)
    safe("R7_REPORT_POINTS_TO_APPENDIX_C", lambda: int("附录 C" in r7), 1)
    safe("R7_REPORT_EVENT_TABLES",
         lambda: int(("越界写入尝试" in r7) and ("工具/脚本事件" in r7) and ("dsh-spill" in r7)), 1)
    safe("R7_REPORT_GIT_SECTION",
         lambda: int(("git log -1" in r7) and ("git status --short" in r7)), 1)

    # ---- manifests (read only)
    reg4 = verify_sums_dir(REG4)
    safe("S5R4_REGISTRY_SUMS_ALL_OK_15",
         lambda: "%d/%s" % (reg4[0], "OK" if not reg4[1] else "BAD:" + ",".join(reg4[1][:3])),
         "%d/OK" % EXP_REG4_ITEMS)
    reg5 = verify_sums_dir(REG5)
    safe("S5R5_REGISTRY_SUMS_ALL_OK_12",
         lambda: "%d/%s" % (reg5[0], "OK" if not reg5[1] else "BAD:" + ",".join(reg5[1][:3])),
         "%d/OK" % EXP_REG5_ITEMS)
    reg6 = verify_sums_dir(REG6)
    safe("S5R6_REGISTRY_SUMS_ALL_OK_4",
         lambda: "%d/%s" % (reg6[0], "OK" if not reg6[1] else "BAD:" + ",".join(reg6[1][:3])),
         "%d/OK" % EXP_REG6_ITEMS)
    ev5 = verify_sums_dir(EV5)
    safe("S5R5_EVIDENCE_SUMS_ALL_OK_20",
         lambda: "%d/%s" % (ev5[0], "OK" if not ev5[1] else "BAD:" + ",".join(ev5[1][:3])),
         "%d/OK" % EXP_EV5_ITEMS)
    safe("S5R5_GATE_END_SHA_UNCHANGED",
         lambda: sha_f(os.path.join(EV5, "gate/GATE_S5R5_end.txt")), EXP_S5R5_GATE_SHA)
    safe("S5R6_GATE_END_SHA_UNCHANGED",
         lambda: sha_f(os.path.join(REG6, "GATE_S5R6_end.txt")), EXP_S5R6_GATE_SHA)

    # ---- registries/s5r7 pre-gate shape and copies
    PREGATE = ["GATE_S5R7_start.txt", "RULINGS_APPEND_S5R7.tsv", "TMP_SNAPSHOT_S5R7.tsv"]

    def reg7_shape():
        if not os.path.isdir(REG7):
            return "absent"
        got = sorted(os.listdir(REG7))
        want = sorted(PREGATE + ["SHA256SUMS.txt"])
        return "ok" if got == want else "files=" + ",".join(got[:8])
    safe("REGISTRY_S5R7_PREGATE_SHAPE", reg7_shape, "ok")

    def reg7_sums():
        if not os.path.isfile(os.path.join(REG7, "SHA256SUMS.txt")):
            return "absent"
        listed, bad = [], []
        for line in rd(os.path.join(REG7, "SHA256SUMS.txt")).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            h, rel = line.split("  ", 1)
            listed.append(rel)
            if not os.path.isfile(os.path.join(REG7, rel)) or sha_f(os.path.join(REG7, rel)) != h:
                bad.append(rel)
        return "ok" if (sorted(listed) == sorted(PREGATE) and not bad) else "bad"
    safe("REGISTRY_S5R7_SUMS_PREGATE_ALL_OK", reg7_sums, "ok")

    def reg7_matches_evidence():
        pairs = [(rel, os.path.join(EV, rel)) for rel in PREGATE]
        for rel, src in pairs:
            if not os.path.isfile(os.path.join(REG7, rel)) or sha_f(os.path.join(REG7, rel)) != sha_f(src):
                return "mismatch:" + rel
        return "ok"
    safe("REGISTRY_S5R7_COPIES_MATCH_EVIDENCE", reg7_matches_evidence, "ok")

    # ---- snapshot unchanged + no new __pycache__
    start_snap = read_kv(os.path.join(EV, "TMP_SNAPSHOT_S5R7.tsv"))
    end_snap_p = os.path.join(EV, "TMP_SNAPSHOT_S5R7_end.tsv")
    record("TMP_SNAPSHOT_START", "%s/%s" % (start_snap.get("TMP_COUNT"), start_snap.get("TMP_SHA256")))
    if os.path.isfile(end_snap_p):
        esc, esh = tmp_snapshot(end_snap_p)
        record("TMP_SNAPSHOT_END", "%s/%s" % (esc, esh))
        safe("TMP_SNAPSHOT_UNCHANGED",
             lambda: "same" if (esc == start_snap.get("TMP_COUNT") and esh == start_snap.get("TMP_SHA256"))
             else "changed", "same")
    else:
        record("TMP_SNAPSHOT_END", "absent")
        safe("TMP_SNAPSHOT_UNCHANGED", lambda: "absent", "same")

    pyc = pycache_now()
    record("PYCACHE_COUNT", len(pyc))
    record("PYCACHE_SET_SHA256", sha_b((NL.join(pyc) + NL).encode("utf-8")))
    safe("NO_NEW_PYCACHE", lambda: sha_b((NL.join(pyc) + NL).encode("utf-8")), EXP_PYCACHE_SHA)
    safe("TMP_TOKEN_ONLY_IN_TMSNAP",
         lambda: ",".join(stage_files_with_tmp_token()), "s5r7_tmpsnap.py")


def write_gate(phase, out_name):
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R7 %s gate %s (%s)" % (phase, out_name, datetime.datetime.now(datetime.timezone.utc)
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
        out = "GATE_S5R7_%s.txt" % phase
    if not re.match(r"^GATE_S5R7_[A-Za-z0-9_]+\.txt$", out):
        print("HARD_STOP --out must be GATE_S5R7_<name>.txt")
        return 2
    if phase == "start":
        phase_start()
    else:
        phase_end()
    return write_gate(phase, out)


if __name__ == "__main__":
    sys.exit(main())
