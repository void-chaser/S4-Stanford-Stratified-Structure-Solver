#!/usr/bin/env python3
# relr3_check.py -- P05 delivery round REL-R3 gate (task brief sections 2 and 7).
# One script, two read-only phases that share the same helpers (only --out differs):
#   --phase start : the opening baseline, re-derived from immutable git objects at HEAD 4607e96 plus the
#                   start top-level temporary-directory snapshot, the REL-R2 remote record and PREREG_RELR3.
#   --phase end   : closing checks: opening items still hold; the round commit and its whitelist; RULINGS
#                   pure append U393-U398 with unchanged prefix; the two tags, the product branch ref and the
#                   archive branch ref; the FOUR remote refs read live with git ls-remote, the remote master
#                   and six pre-existing heads unchanged; the Draft PR read live with gh pr view (OPEN, draft,
#                   not merged); R1-R9 against PREREG_RELR3.tsv (read by column name); the report's derived
#                   COUNTS block against the source tables; STATE without projected gate results; the rel-r3
#                   registry and evidence SHA256SUMS; /tmp end snapshot equal to start; the script manifest;
#                   the push log (four pushes, no force flag); the supplementary sensitive/volume audit.
# Nothing in this script writes outside the gate file path passed with --out (under the round evidence
# directory); every table is read BY COLUMN NAME, and every directory-set sha uses Python sorted().
import os, re, sys, json, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r3")
REG1 = os.path.join(P05, "registries/rel-r1")
REG2 = os.path.join(P05, "registries/rel-r2")
REG3 = os.path.join(P05, "registries/rel-r3")
STAGE = os.path.join(REPO, "testing/d003/stage_relr3")
RULINGS = os.path.join(P05, "registries/RULINGS.tsv")
STATE = os.path.join(P05, "STATE.md")
REPORT = os.path.join(P05, "P05_RELR3_REPORT.md")
AGENTS = os.path.join(REPO, "AGENTS.md")
ROADMAP = os.path.join(REPO, "PROJECT_ROADMAP.md")
ISSUE = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
PREREG = os.path.join(EV, "PREREG_RELR3.tsv")
PREREG_SHA = os.path.join(EV, "PREREG_RELR3.tsv.sha256.txt")
VT = os.path.join(EV, "V_RELR3.tsv")
PUSHPLAN = os.path.join(EV, "PUSH_PLAN_RELR3.tsv")
PUSHLOG = os.path.join(EV, "PUSH_LOG_RELR3.tsv")
SENS = os.path.join(EV, "PUBLISH_AUDIT_RELR3.tsv")
VOL = os.path.join(EV, "PUBLISH_VOLUME_RELR3.tsv")
REMOTE_BEFORE = os.path.join(EV, "REMOTE_BEFORE_RELR3.tsv")
REMOTE_AFTER = os.path.join(EV, "REMOTE_AFTER_RELR3.tsv")
CLONE = os.path.join(EV, "REMOTE_CLONE_RELR3.tsv")
PRT = os.path.join(EV, "PR_RELR3.tsv")
BACKUP = os.path.join(EV, "EVIDENCE_BACKUP_PLAN_RELR3.md")
SNAP_START = os.path.join(EV, "TMP_SNAPSHOT_RELR3.tsv")
SNAP_END = os.path.join(EV, "TMP_SNAPSHOT_RELR3_end.tsv")
MANIFEST = os.path.join(STAGE, "relr3_scripts.txt")
CLONEDIR = os.path.join(EV, "remoteclone")

TAB = chr(9)
NL = chr(10)
ROUND = "P05 delivery round REL-R3 (rel-r3)"
BRANCH = "codex/p05-d003-fft-error-propagation"
BASE_HEAD = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
B_COMMIT = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RUL_OPEN_BYTES = 158104
EXP_RUL_OPEN_SHA = "ca9ab5721d9cd490ed4365b04230f1e16fa93c3e2615528c2e9f1fbe2cd773c7"
EXP_RUL_OPEN_ROWS = 396
EXP_TMP_COUNT = "0"
EXP_TMP_SHA = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
EXP_TAG1 = "p05-signed-20261019"
EXP_TAG2 = "p05-rel-r1-20261019"
EXP_TAG1_OBJ = "ef925cdea019a7cdf00acb66bc5b59d55f00d868"
EXP_TAG2_OBJ = "b42c4c16298ce644f39c3c33ae6c26ef18820a96"
EXP_TAG1_PEEL = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_TAG2_PEEL = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
EXP_PROD_HEAD = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
EXP_ARCHIVE = BASE_HEAD
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
ARCHIVE_BRANCH = "archive/p05-d003-full-20261019"
FORK = "void-chaser/S4-Stanford-Stratified-Structure-Solver"
PR_URL_PREFIX = "https://github.com/" + FORK + "/pull/"
REL1_REGISTRY_ITEMS = 18
REL2_REGISTRY_ITEMS = 15
EXP_PUSH_REFS = 4
PREGATE = ["GATE_RELR3_start.txt", "PREREG_RELR3.tsv", "PREREG_RELR3.tsv.sha256.txt",
           "PUSH_PLAN_RELR3.tsv", "PUSH_LOG_RELR3.tsv", "PUBLISH_AUDIT_RELR3.tsv",
           "PUBLISH_VOLUME_RELR3.tsv", "PUBLISH_REMOTE_RELR3.tsv", "REMOTE_BEFORE_RELR3.tsv",
           "REMOTE_AFTER_RELR3.tsv", "REMOTE_CLONE_RELR3.tsv", "PR_RELR3.tsv", "V_RELR3.tsv",
           "EVIDENCE_BACKUP_PLAN_RELR3.md", "RULINGS_APPEND_RELR3.tsv",
           "TMP_SNAPSHOT_RELR3.tsv", "TMP_SNAPSHOT_RELR3_end.tsv"]
EV_SUMS_EXCLUDE = ("safe_run.log", "GATE_RELR3_pre.txt", "GATE_RELR3_end.txt", "SHA256SUMS.txt")
EV_EXTS = (".txt", ".tsv", ".log", ".md")
TOKEN_PATTERNS = ("TOKEN_GHP", "TOKEN_GITHUB_PAT", "TOKEN_AKIA", "PRIVATE_KEY_BEGIN", "PASSWORD_ASSIGN")
COUNTS_KEYS = ["PREREG_ROWS", "PREREG_SHA256", "V_ROWS", "V_SAME", "V_MISMATCH",
               "PUSH_REFS", "PUSH_SUCCESS", "PUSH_LS_REMOTE_MATCH",
               "PUSH_PRODUCT_SHA", "PUSH_ARCHIVE_SHA", "TAG1_OBJECT_SHA", "TAG2_OBJECT_SHA",
               "REMOTE_MASTER_SHA", "REMOTE_OLD_HEADS_CHANGED",
               "PR_NUMBER", "PR_STATE", "PR_ISDRAFT", "PR_BASE", "PR_HEAD", "PR_COMMITS",
               "PR_CHANGED_FILES",
               "R6_HEAD", "R6_HEAD_S4", "R7_RC", "R7_UNIT_COUNT", "R7_FAILING",
               "A_NEW_BLOBS", "A_TOTAL_BYTES", "A_LARGEST_BLOB_BYTES", "A_BLOBS_GE_50MB",
               "A_BLOBS_GE_100MB", "SENSITIVE_NEW_TOKENS",
               "RULINGS_APPENDED_ROWS", "RULINGS_BEFORE_BYTES", "RULINGS_AFTER_BYTES",
               "ARCHIVE_BRANCH_SHA", "ARCHIVE_BRANCH_S4"]

CHECKS = []
RECORDS = []
CRASHED = []


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    return open(p, encoding="utf-8", errors="replace").read()


def run(args, timeout=120):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)


def sh(args):
    return run(args).stdout.strip()


def git_bytes(spec):
    p = subprocess.run(["git", "show", spec], cwd=REPO, capture_output=True)
    return p.stdout


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


def read_table(path):
    header = None
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if header is None:
            header = f
            continue
        if len(f) != len(header):
            continue
        rows.append(dict(zip(header, f)))
    return header, rows


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) == 2 and f[0] != "key":
            d[f[0]] = f[1]
    return d


def gate_results(path):
    t = rd(path)
    m = re.search(r"^COUNTS" + TAB + r"pass=(\d+)" + TAB + r"fail=(\d+)" + TAB + r"total=(\d+)$", t, re.M)
    f = re.search(r"^FAILS=(\d+)$", t, re.M)
    if not (m and f):
        return "UNPARSABLE"
    return "%s/%s/%s/%s" % (m.group(1), m.group(2), m.group(3), f.group(1))


def verify_sums(d):
    p = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(p):
        return None
    listed = []
    bad = []
    for line in open(p, encoding="utf-8"):
        line = line.rstrip("\r\n")
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            bad.append("MALFORMED")
            continue
        rel = " ".join(parts[1:])
        listed.append(rel)
        fp = os.path.join(d, rel)
        if not os.path.isfile(fp):
            bad.append("MISSING:" + rel)
        elif sha_f(fp) != parts[0]:
            bad.append("SHA:" + rel)
    return sorted(listed), bad


def tmp_snapshot(path):
    kv = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            kv[f[0]] = f[1]
    return kv.get("TMP_COUNT", "NA"), kv.get("TMP_SHA256", "NA")


def stage_files():
    return sorted([f for f in os.listdir(STAGE) if os.path.isfile(os.path.join(STAGE, f))])


def changed_between(a, b):
    return [l for l in sh(["git", "diff", "--name-only", a, b]).splitlines() if l.strip()]


def live_remote():
    p = run(["git", "ls-remote", "origin"], timeout=120)
    refs = {}
    for l in p.stdout.splitlines():
        f = l.split(TAB)
        if len(f) != 2:
            continue
        if f[1].endswith("^{}"):
            continue
        refs[f[1]] = f[0]
    return p.returncode, refs


def live_pr(number):
    p = run(["gh", "pr", "view", str(number), "--repo", FORK,
             "--json", "state,isDraft,baseRefName,headRefName,commits,changedFiles,mergedAt,url,number"],
            timeout=120)
    if p.returncode != 0:
        raise RuntimeError("gh pr view rc=" + str(p.returncode) + " " + p.stderr[-200:])
    return json.loads(p.stdout)


# ------------------------------------------------------------------ phase start
def phase_start():
    record("ROUND", ROUND)
    record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    record("BRANCH", sh(["git", "branch", "--show-current"]))
    record("HEAD", sh(["git", "rev-parse", "HEAD"]))
    record("HEAD_S4", sh(["git", "rev-parse", "HEAD:S4"]))
    record("JUDGE_SHA256", sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")))

    base = git_bytes(BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv")
    record("RULINGS_OPENING_BYTES", len(base))
    record("RULINGS_OPENING_SHA256", sha_b(base))
    rul_lines = [l for l in base.decode("utf-8").splitlines() if l.strip() and not l.startswith("#")]
    record("RULINGS_OPENING_ROWS", len(rul_lines))
    record("RULINGS_OPENING_LAST_ID", rul_lines[-1].split(TAB)[0] if rul_lines else "none")

    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), BRANCH)
    safe("HEAD_IS_RELR2_II", lambda: sh(["git", "rev-parse", "HEAD"]), BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("S4_DIR_ZERO_MODIFICATION",
         lambda: (sh(["git", "diff", "--name-only", BASE_HEAD, "--", "S4"]) or "unmodified"), "unmodified")
    safe("RULINGS_OPENING_BYTES", lambda: len(base), EXP_RUL_OPEN_BYTES)
    safe("RULINGS_OPENING_SHA256", lambda: sha_b(base), EXP_RUL_OPEN_SHA)
    safe("RULINGS_OPENING_LAST_IS_U392", lambda: rul_lines[-1].split(TAB)[0], "U392")
    safe("RULINGS_OPENING_DATA_ROWS_396", lambda: len(rul_lines), EXP_RUL_OPEN_ROWS)
    safe("RULINGS_OPENING_5_FIELDS",
         lambda: "ok" if all(len(l.split(TAB)) == 5 for l in rul_lines) else "bad", "ok")

    for name, reg, n in (("RELR1", REG1, REL1_REGISTRY_ITEMS), ("RELR2", REG2, REL2_REGISTRY_ITEMS)):
        v = verify_sums(reg)
        record(name + "_REGISTRY_ITEMS", len(v[0]) if v else "MISSING")
        record(name + "_REGISTRY_SUMS_SHA256", sha_f(os.path.join(reg, "SHA256SUMS.txt")))
        safe(name + "_REGISTRY_SUMS_ALL_OK_" + str(n),
             lambda v=v, n=n: "%d/%s" % (n, "OK" if v and not v[1] else
                                         "BAD:" + ",".join((v[1] if v else [])[:3])),
             "%d/OK" % n)

    cnt, tsha = tmp_snapshot(SNAP_START)
    record("TMP_COUNT", cnt)
    record("TMP_SHA256", tsha)
    safe("TMP_START_PRESENT", lambda: "present" if os.path.isfile(SNAP_START) else "absent", "present")
    safe("TMP_START_COUNT_ZERO", lambda: cnt, EXP_TMP_COUNT)
    safe("TMP_START_SHA256", lambda: tsha, EXP_TMP_SHA)

    safe("PREREG_PRESENT", lambda: "present" if os.path.isfile(PREREG) else "absent", "present")
    rec_sha = None
    for line in rd(PREREG_SHA).splitlines():
        if line.startswith("PREREG_RELR3.tsv" + TAB):
            rec_sha = line.split(TAB)[1]
    record("PREREG_RECORD_SHA256", rec_sha)
    safe("PREREG_SHA_MATCHES_RECORD", lambda: sha_f(PREREG), rec_sha)
    _, preg = read_table(PREREG)
    safe("PREREG_ROWS_9", lambda: len(preg), 9)
    safe("PREREG_HAS_R1_R9", lambda: ",".join(r["test_id"] for r in preg),
         "R1,R2,R3,R4,R5,R6,R7,R8,R9")
    safe("PREREG_STATUS_INFLUENCED",
         lambda: "ok" if preg and all(r.get("status") == "INFLUENCED" for r in preg) else "bad", "ok")

    before = read_table(REMOTE_BEFORE)[1]
    bt = {r["ref"]: r["sha"] for r in before}
    rc, live = live_remote()
    record("REMOTE_BEFORE_REF_COUNT", len(before))
    safe("REMOTE_BASELINE_MATCHES_RELR2",
         lambda: "ok" if rc == 0 and live.get("refs/heads/master") == B_COMMIT
         and not any(r.startswith("refs/heads/p05/") or r.startswith("refs/heads/archive/")
                     for r in live)
         and not any(r in live for r in ("refs/tags/" + EXP_TAG1, "refs/tags/" + EXP_TAG2))
         and bt.get("refs/heads/master") == B_COMMIT else "bad", "ok")
    safe("LOCAL_ARCHIVE_BRANCH_ABSENT",
         lambda: "absent" if run(["git", "show-ref", "--verify", "--quiet",
                                  "refs/heads/" + ARCHIVE_BRANCH]).returncode != 0 else "present", "absent")
    safe("PRODUCT_BRANCH_LOCAL_SHA", lambda: sh(["git", "rev-parse", "refs/heads/" + PRODUCT_BRANCH]),
         EXP_PROD_HEAD)
    safe("PRODUCT_BRANCH_LOCAL_S4", lambda: sh(["git", "rev-parse", "refs/heads/" + PRODUCT_BRANCH + ":S4"]),
         EXP_S4)
    safe("TAG1_ANNOTATED_OBJECT", lambda: sh(["git", "rev-parse", EXP_TAG1]), EXP_TAG1_OBJ)
    safe("TAG2_ANNOTATED_OBJECT", lambda: sh(["git", "rev-parse", EXP_TAG2]), EXP_TAG2_OBJ)
    safe("TAG1_PEEL", lambda: sh(["git", "rev-parse", EXP_TAG1 + "^{commit}"]), EXP_TAG1_PEEL)
    safe("TAG2_PEEL", lambda: sh(["git", "rev-parse", EXP_TAG2 + "^{commit}"]), EXP_TAG2_PEEL)

    def status_only_round():
        st = [l for l in run(["git", "status", "--porcelain=v1", "-uall"]).stdout.splitlines() if l.strip()]
        bad = [l for l in st if not (l[3:].startswith("checkpoints/p05/") or
                                     l[3:].startswith("testing/d003/stage_relr3/"))]
        return "clean" if not bad else "unexpected:" + ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_ROUND_FILES", status_only_round, "clean")

    def manifest_ok():
        want = set(stage_files())
        got = set(l.strip() for l in rd(MANIFEST).splitlines() if l.strip() and not l.startswith("#"))
        return "ok" if got == want else "diff:" + ",".join(sorted(got ^ want)[:5])
    safe("SCRIPT_MANIFEST_MATCHES_STAGE_DIR", manifest_ok, "ok")
    record("STAGE_SCRIPT_COUNT", len(stage_files()))
    record("STAGE_MANIFEST_SHA256", sha_f(MANIFEST))


# ------------------------------------------------------------------ actual counts
def actual_counts():
    d = {}
    _, preg = read_table(PREREG)
    d["PREREG_ROWS"] = str(len(preg))
    d["PREREG_SHA256"] = sha_f(PREREG)
    _, vt = read_table(VT)
    d["V_ROWS"] = str(len(vt))
    d["V_SAME"] = str(sum(1 for r in vt if r.get("result") == "SAME"))
    d["V_MISMATCH"] = str(sum(1 for r in vt if r.get("result") == "MISMATCH"))
    _, push = read_table(PUSHLOG)
    pushes = [r for r in push if r.get("action") == "push"]
    lsrs = [r for r in push if r.get("action") == "ls_remote"]
    d["PUSH_REFS"] = str(len(pushes))
    d["PUSH_SUCCESS"] = str(sum(1 for r in pushes if r.get("rc") == "0"))
    d["PUSH_LS_REMOTE_MATCH"] = str(sum(1 for r in lsrs if r.get("match") == "YES"))
    _, plan = read_table(PUSHPLAN)
    byref = {r["ref"]: r for r in plan}
    d["PUSH_PRODUCT_SHA"] = byref.get("refs/heads/" + PRODUCT_BRANCH, {}).get("local_sha", "NA")
    d["PUSH_ARCHIVE_SHA"] = byref.get("refs/heads/" + ARCHIVE_BRANCH, {}).get("local_sha", "NA")
    d["TAG1_OBJECT_SHA"] = byref.get("refs/tags/" + EXP_TAG1, {}).get("local_sha", "NA")
    d["TAG2_OBJECT_SHA"] = byref.get("refs/tags/" + EXP_TAG2, {}).get("local_sha", "NA")
    _, after = read_table(REMOTE_AFTER)
    amap = {r["ref"]: r["sha"] for r in after}
    _, before = read_table(REMOTE_BEFORE)
    bmap = {r["ref"]: r["sha"] for r in before}
    d["REMOTE_MASTER_SHA"] = amap.get("refs/heads/master", "NA")
    d["REMOTE_OLD_HEADS_CHANGED"] = str(sum(1 for r, s in bmap.items()
                                            if r.startswith("refs/heads/") and amap.get(r) != s))
    pr = read_kv(PRT)
    for k, src in (("PR_NUMBER", "PR_NUMBER"), ("PR_STATE", "PR_STATE"), ("PR_ISDRAFT", "PR_ISDRAFT"),
                   ("PR_BASE", "PR_BASE"), ("PR_HEAD", "PR_HEAD"), ("PR_COMMITS", "PR_COMMITS"),
                   ("PR_CHANGED_FILES", "PR_CHANGED_FILES")):
        d[k] = pr.get(src, "NA")
    clone = read_kv(CLONE)
    for k in ("R6_HEAD", "R6_HEAD_S4", "R7_RC", "R7_UNIT_COUNT", "R7_FAILING"):
        d[k] = clone.get(k, "NA")
    vol = {}
    for line in rd(VOL).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) == 10 and f[0] in ("A_archive_branch", "P_product_branch"):
            vol[f[0]] = {"blobs": f[3], "bytes": f[4], "largest": f[6], "ge50": f[8], "ge100": f[9]}
    a = vol.get("A_archive_branch", {})
    d["A_NEW_BLOBS"] = a.get("blobs", "NA")
    d["A_TOTAL_BYTES"] = a.get("bytes", "NA")
    d["A_LARGEST_BLOB_BYTES"] = a.get("largest", "NA")
    d["A_BLOBS_GE_50MB"] = a.get("ge50", "NA")
    d["A_BLOBS_GE_100MB"] = a.get("ge100", "NA")
    token_secret = "NA"
    for line in rd(SENS).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 3 and f[1] == "TOKEN_SECRETS_TOTAL":
            token_secret = f[2]
    d["SENSITIVE_NEW_TOKENS"] = token_secret
    base = git_bytes(BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv")
    cur = open(RULINGS, "rb").read()
    d["RULINGS_BEFORE_BYTES"] = str(len(base))
    d["RULINGS_AFTER_BYTES"] = str(len(cur))
    d["RULINGS_APPENDED_ROWS"] = str(len([l for l in cur[len(base):].decode("utf-8").split(NL) if l.strip()])
                                      if cur.startswith(base) else -1)
    d["ARCHIVE_BRANCH_SHA"] = sh(["git", "rev-parse", "refs/heads/" + ARCHIVE_BRANCH])
    d["ARCHIVE_BRANCH_S4"] = sh(["git", "rev-parse", "refs/heads/" + ARCHIVE_BRANCH + ":S4"])
    return d


def report_counts():
    t = rd(REPORT)
    m = re.search(r"<!-- COUNTS:BEGIN -->(.*?)<!-- COUNTS:END -->", t, re.S)
    if not m:
        return None
    d = {}
    for line in m.group(1).splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = v
    return d


# ------------------------------------------------------------------ phase end
def phase_end():
    record("ROUND", ROUND)
    record("END_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    base_rul = git_bytes(BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv")
    base_state = git_bytes(BASE_HEAD + ":checkpoints/p05/STATE.md")
    base_agents = git_bytes(BASE_HEAD + ":AGENTS.md")
    base_roadmap = git_bytes(BASE_HEAD + ":PROJECT_ROADMAP.md")
    base_issue = git_bytes(BASE_HEAD + ":testing/s4test/ISSUE_REGISTRY.md")
    record("RULINGS_OPENING_BYTES", len(base_rul))
    record("RULINGS_OPENING_SHA256", sha_b(base_rul))

    # ---- A opening items still hold
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), BRANCH)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA256_UNCHANGED", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("BASE_COMMIT_PRESENT", lambda: sh(["git", "rev-parse", "--verify", BASE_HEAD + "^{commit}"]), BASE_HEAD)
    safe("S4_DIR_ZERO_MODIFICATION",
         lambda: "unmodified" if not sh(["git", "diff", "--name-only", BASE_HEAD, "HEAD", "--", "S4"])
         and not sh(["git", "status", "--porcelain=v1", "-uall", "--", "S4"]) else "modified", "unmodified")
    safe("AGENTS_MD_UNCHANGED", lambda: sha_b(open(AGENTS, "rb").read()) == sha_b(base_agents), 1)
    safe("ROADMAP_UNCHANGED", lambda: sha_b(open(ROADMAP, "rb").read()) == sha_b(base_roadmap), 1)
    safe("ISSUE_REGISTRY_UNCHANGED", lambda: sha_b(open(ISSUE, "rb").read()) == sha_b(base_issue), 1)
    for name, reg, n in (("RELR1", REG1, REL1_REGISTRY_ITEMS), ("RELR2", REG2, REL2_REGISTRY_ITEMS),
                         ("RELR3", REG3, None)):
        v = verify_sums(reg)
        safe(name + "_REGISTRY_SUMS_ALL_OK",
             lambda v=v: "OK" if v and not v[1] else "BAD:" + ",".join((v[1] if v else [])[:3]), "OK")
        record(name + "_REGISTRY_ITEMS", len(v[0]) if v else "MISSING")

    # ---- B the round commit and whitelist
    n_commits = sh(["git", "rev-list", "--count", BASE_HEAD + "..HEAD"])
    record("ROUND_COMMITS", n_commits)
    safe("ROUND_COMMITS_EXACTLY_1", lambda: n_commits, "1")

    def round_changed():
        parts = set(changed_between(BASE_HEAD, "HEAD"))
        for line in run(["git", "status", "--porcelain=v1", "-uall"]).stdout.splitlines():
            if not line.strip():
                continue
            p = line[3:]
            if " -> " in p:
                p = p.split(" -> ")[-1]
            parts.add(p.strip())
        return sorted(parts)
    changed = round_changed()
    record("ROUND_CHANGED_FILES", len(changed))
    safe("ROUND_CHANGED_WITHIN_WHITELIST",
         lambda: "ok" if all(p.startswith("checkpoints/p05/") or p.startswith("testing/d003/stage_relr3/")
                             for p in changed) else "outside", "ok")
    safe("ROUND_NO_DELETIONS",
         lambda: sh(["git", "diff", "--name-status", "--diff-filter=DR", BASE_HEAD, "HEAD"]) or "none", "none")
    safe("STATUS_CLEAN_AFTER_COMMIT",
         lambda: "clean" if not run(["git", "status", "--porcelain=v1", "-uall"]).stdout.strip() else "dirty",
         "clean")
    safe("HEAD_DESCENDS_FROM_BASE",
         lambda: "yes" if (sh(["git", "rev-parse", "HEAD"]) == BASE_HEAD or
                           run(["git", "merge-base", "--is-ancestor", BASE_HEAD, "HEAD"]).returncode == 0)
         else "no", "yes")

    # ---- C RULINGS pure append U393-U398
    cur_rul = open(RULINGS, "rb").read()
    record("RULINGS_BYTES", len(cur_rul))
    record("RULINGS_SHA256", sha_b(cur_rul))
    safe("RULINGS_PURE_APPEND", lambda: "ok" if cur_rul.startswith(base_rul) else "prefix_changed", "ok")
    safe("RULINGS_PREFIX_SHA_UNCHANGED", lambda: sha_b(cur_rul[:len(base_rul)]), EXP_RUL_OPEN_SHA)
    add = cur_rul[len(base_rul):] if cur_rul.startswith(base_rul) else b""
    add_lines = [l for l in add.decode("utf-8").split(NL) if l.strip()]
    safe("RULINGS_EXACTLY_SIX_NEW_ROWS", lambda: len(add_lines), 6)
    ids = [l.split(TAB)[0] for l in add_lines]
    safe("RULINGS_NEW_ROWS_U393_U398", lambda: ",".join(ids),
         "U393,U394,U395,U396,U397,U398")
    safe("RULINGS_NEW_ROWS_5_FIELDS",
         lambda: "ok" if add_lines and all(len(l.split(TAB)) == 5 for l in add_lines) else "bad", "ok")
    safe("RULINGS_NEW_ROWS_STATUS_ACTIVE",
         lambda: "ok" if add_lines and all(l.split(TAB)[4] == "生效" for l in add_lines) else "bad", "ok")
    joined = add.decode("utf-8")
    for tag, needle in (("PUSH", "git push origin refs/heads/p05/d003-fft-error-propagation"),
                        ("FORCE_BAN", "一律不加 -f"),
                        ("ARCHIVE", "archive/p05-d003-full-20261019"),
                        ("PR", "--draft"),
                        ("ROADMAP", "ROADMAP"),
                        ("TOKEN0", "token/密钥类仍为 0"),
                        ("BACKUP", "证据离线备份由用户手工执行")):
        safe("RULINGS_HAS_" + tag, lambda n=needle: int(n in joined), 1)
    safe("RULINGS_NO_P05_S6", lambda: int(("P05-" + "S6") in joined), 0)

    # ---- D tags and local refs
    safe("TAG1_ANNOTATED", lambda: sh(["git", "cat-file", "-t", EXP_TAG1]), "tag")
    safe("TAG2_ANNOTATED", lambda: sh(["git", "cat-file", "-t", EXP_TAG2]), "tag")
    safe("TAG1_OBJECT_SHA", lambda: sh(["git", "rev-parse", EXP_TAG1]), EXP_TAG1_OBJ)
    safe("TAG2_OBJECT_SHA", lambda: sh(["git", "rev-parse", EXP_TAG2]), EXP_TAG2_OBJ)
    safe("TAG1_PEELS_TO_F4", lambda: sh(["git", "rev-parse", EXP_TAG1 + "^{commit}"]), EXP_TAG1_PEEL)
    safe("TAG2_PEELS_TO_RELR1_II", lambda: sh(["git", "rev-parse", EXP_TAG2 + "^{commit}"]), EXP_TAG2_PEEL)
    safe("PRODUCT_BRANCH_LOCAL_SHA", lambda: sh(["git", "rev-parse", "refs/heads/" + PRODUCT_BRANCH]),
         EXP_PROD_HEAD)
    safe("ARCHIVE_BRANCH_LOCAL_SHA", lambda: sh(["git", "rev-parse", "refs/heads/" + ARCHIVE_BRANCH]),
         EXP_ARCHIVE)
    safe("ARCHIVE_BRANCH_S4", lambda: sh(["git", "rev-parse", "refs/heads/" + ARCHIVE_BRANCH + ":S4"]),
         EXP_S4)
    safe("ARCHIVE_REFS_LOCAL_EXACTLY_ONE",
         lambda: ",".join(sorted(sh(["git", "for-each-ref", "--format=%(refname)", "refs/heads/archive/"]).splitlines())) if
         sh(["git", "for-each-ref", "--format=%(refname)", "refs/heads/archive/"]) else "none",
         "refs/heads/" + ARCHIVE_BRANCH)

    # ---- E remote live state: the four refs, master and the six old heads
    rc, live = live_remote()
    record("REMOTE_REF_COUNT", len(live))
    safe("REMOTE_LS_RC_ZERO", lambda: rc, 0)
    safe("REMOTE_PRODUCT_BRANCH_SHA", lambda: live.get("refs/heads/" + PRODUCT_BRANCH), EXP_PROD_HEAD)
    safe("REMOTE_ARCHIVE_BRANCH_SHA", lambda: live.get("refs/heads/" + ARCHIVE_BRANCH), EXP_ARCHIVE)
    safe("REMOTE_TAG1_OBJECT_SHA", lambda: live.get("refs/tags/" + EXP_TAG1), EXP_TAG1_OBJ)
    safe("REMOTE_TAG2_OBJECT_SHA", lambda: live.get("refs/tags/" + EXP_TAG2), EXP_TAG2_OBJ)
    safe("REMOTE_MASTER_UNCHANGED", lambda: live.get("refs/heads/master"), B_COMMIT)
    _, before = read_table(REMOTE_BEFORE)
    bmap = {r["ref"]: r["sha"] for r in before}
    old_heads = sorted(r for r in bmap if r.startswith("refs/heads/"))
    safe("REMOTE_OLD_HEADS_COUNT_6", lambda: len(old_heads), 6)
    changed_heads = [r for r in old_heads if live.get(r) != bmap[r]]
    safe("REMOTE_OLD_HEADS_UNCHANGED", lambda: ",".join(changed_heads) if changed_heads else "none", "none")
    # refs/pull/* are created by GitHub when the Draft PR is opened; they are not pushed by this round.
    new_refs = sorted(r for r in set(live) - set(bmap) if not r.startswith("refs/pull/"))
    expected_new = sorted(["refs/heads/" + PRODUCT_BRANCH, "refs/heads/" + ARCHIVE_BRANCH,
                           "refs/tags/" + EXP_TAG1, "refs/tags/" + EXP_TAG2])
    safe("REMOTE_ONLY_FOUR_NEW_REFS", lambda: ",".join(new_refs), ",".join(expected_new))
    record("REMOTE_PULL_REFS", ",".join(sorted(r for r in live if r.startswith("refs/pull/"))))
    safe("REMOTE_NO_OTHER_P05_OR_ARCHIVE",
         lambda: "none" if not [r for r in live
                                if (r.startswith("refs/heads/p05/") and r != "refs/heads/" + PRODUCT_BRANCH)
                                or (r.startswith("refs/heads/archive/") and r != "refs/heads/" + ARCHIVE_BRANCH)]
         else "present", "none")
    safe("REMOTES_ONLY_ORIGIN",
         lambda: ",".join(sorted(l.split()[0] for l in sh(["git", "remote"]).splitlines())), "origin")

    # ---- F Draft PR read live
    pr = read_kv(PRT)
    number = pr.get("PR_NUMBER", "")
    record("PR_NUMBER", number)
    record("PR_URL", pr.get("PR_URL", "NA"))
    live_pr_data = None
    live_pr_err = ""
    try:
        live_pr_data = live_pr(number)
    except Exception as exc:
        live_pr_err = repr(exc)[:200]
    record("PR_LIVE_ERROR", live_pr_err or "none")
    safe("PR_URL_IS_FORK_PR", lambda: int(pr.get("PR_URL", "").startswith(PR_URL_PREFIX)), 1)
    if live_pr_data is not None:
        rec = live_pr_data
        safe("PR_LIVE_STATE_OPEN", lambda: rec.get("state"), "OPEN")
        safe("PR_LIVE_IS_DRAFT", lambda: "true" if rec.get("isDraft") is True else "false", "true")
        safe("PR_LIVE_BASE_MASTER", lambda: rec.get("baseRefName"), "master")
        safe("PR_LIVE_HEAD_PRODUCT", lambda: rec.get("headRefName"), PRODUCT_BRANCH)
        safe("PR_LIVE_COMMITS_2", lambda: len(rec.get("commits") or []), 2)
        safe("PR_LIVE_CHANGED_FILES_11", lambda: rec.get("changedFiles"), 11)
        safe("PR_LIVE_NOT_MERGED",
             lambda: "not_merged" if rec.get("state") != "MERGED" and not rec.get("mergedAt") else "merged",
             "not_merged")
    else:
        safe("PR_LIVE_VIEW_OK", lambda: "error", "ok")
    safe("PR_TABLE_STATE_OPEN", lambda: pr.get("PR_STATE"), "OPEN")
    safe("PR_TABLE_ISDRAFT", lambda: pr.get("PR_ISDRAFT"), "true")
    safe("PR_TABLE_COMMITS", lambda: pr.get("PR_COMMITS"), "2")
    safe("PR_TABLE_CHANGED_FILES", lambda: pr.get("PR_CHANGED_FILES"), "11")

    # ---- G R6 / R7 measurements
    clone = read_kv(CLONE)
    _, crow = read_table(CLONE)
    safe("R6_CLONE_RC_ZERO", lambda: clone.get("R6_CLONE_RC"), "0")
    safe("R6_CLONE_HEAD", lambda: clone.get("R6_HEAD"), EXP_PROD_HEAD)
    safe("R6_CLONE_HEAD_S4", lambda: clone.get("R6_HEAD_S4"), EXP_S4)
    safe("R7_MAKE_TEST_RC_ZERO", lambda: clone.get("R7_RC"), "0")
    safe("R7_UNIT_COUNT_265", lambda: clone.get("R7_UNIT_COUNT"), "265")
    safe("R7_UNIT_SET_EQ_RELR2_V3",
         lambda: "ok" if clone.get("R7_UNIT_COUNT") == clone.get("R7_EXPECTED_UNITS") else "diff", "ok")
    safe("R7_NO_FAILURES", lambda: clone.get("R7_FAILING"), "none")
    safe("R7_NO_MISSING", lambda: clone.get("R7_MISSING"), "none")
    safe("R7_NO_EXTRA", lambda: clone.get("R7_EXTRA"), "none")
    safe("CLONE_DIR_PRESENT", lambda: "present" if os.path.isdir(CLONEDIR) else "absent", "present")

    # ---- H V table against PREREG (by column name)
    _, preg = read_table(PREREG)
    _, vt = read_table(VT)
    pmap = {r["test_id"]: r for r in preg}
    vmap = {r["test_id"]: r for r in vt}
    safe("V_TABLE_ROWS_9", lambda: len(vt), 9)
    safe("V_TABLE_IDS", lambda: ",".join(sorted(vmap)), ",".join(sorted(pmap)))
    safe("V_EXPECTED_MATCH_PREREG",
         lambda: "ok" if all(vmap[k]["expected"] == pmap[k]["expected"] for k in pmap if k in vmap) else "diff",
         "ok")
    safe("V_ALL_SAME",
         lambda: ",".join("%s=%s" % (k, vmap[k]["result"]) for k in sorted(vmap)),
         ",".join("%s=SAME" % k for k in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9")))
    safe("V_NO_MISMATCH", lambda: sum(1 for r in vt if r.get("result") == "MISMATCH"), 0)

    # ---- I report: derived COUNTS block against the source tables
    rc_counts = report_counts()
    actual = actual_counts()
    record("REPORT_COUNTS_KEYS", len(rc_counts) if rc_counts else "MISSING")

    def counts_all():
        if rc_counts is None:
            return "missing_block"
        missing = [k for k in COUNTS_KEYS if k not in rc_counts]
        extra = [k for k in rc_counts if k not in COUNTS_KEYS]
        if missing or extra:
            return "missing=" + ",".join(missing[:3]) + ";extra=" + ",".join(extra[:3])
        bad = [k for k in COUNTS_KEYS if rc_counts[k] != actual[k]]
        return "ok" if not bad else "mismatch:" + ",".join("%s=%s/%s" % (k, rc_counts[k], actual[k])
                                                           for k in bad[:4])
    safe("REPORT_COUNTS_MATCH_SOURCE_TABLES", counts_all, "ok")

    # ---- J report content requirements
    rep = rd(REPORT)
    safe("REPORT_HAS_APPENDIX_C_PLACEHOLDER", lambda: int("## 附录 C 正式 end 门禁结果" in rep), 1)
    for sec in ("## 1 范围与开工门禁", "## 2 推送前补审", "## 3 预注册与推送计划", "## 4 推送执行",
                "## 5 Draft PR", "## 6 R6 远端克隆与 R7", "## 7 证据离线备份", "## 8 违规披露",
                "## 9 待用户裁决", "## 10 两阶段提交与门禁", "## 附录 A", "## 附录 B"):
        safe("REPORT_SECTION_" + re.sub(r"[^0-9A-Za-z]+", "_", sec.split(" ", 1)[1]).strip("_"),
             lambda sec=sec: int(sec in rep), 1)
    for phrase in ("https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver/pull/",
                   "8e4c01491b6edec9eb4eaa617265ce9ca53bd548",
                   "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b",
                   "ef925cdea019a7cdf00acb66bc5b59d55f00d868",
                   "b42c4c16298ce644f39c3c33ae6c26ef18820a96",
                   "pending the REL-R3 push", "故障注入装置", "archive/p05-d003-full-20261019",
                   "p05-signed-20261019", "p05-rel-r1-20261019", "表一", "表二", "越界写入尝试",
                   "工具/脚本事件", "gh", "push", "备份", "ready", "归档分支", "git log -1",
                   "git status --short", "预注册", "SAME"):
        safe("REPORT_PHRASE_" + re.sub(r"[^A-Za-z0-9]+", "_", phrase)[:36], lambda p=phrase: int(p in rep), 1)
    safe("REPORT_NO_P05_S6", lambda: int(("P05-" + "S6") in rep), 0)
    safe("REPORT_NO_FIXED_CLAIM",
         lambda: int(("修复完成" in rep) or ("已验证可达" in rep) or ("REL-R3 已签收" in rep)), 0)
    safe("REPORT_APPENDIX_C_PLACEHOLDER_TEXT", lambda: int("照实写 INCOMPLETE" in rep), 1)
    appc = rd(os.path.join(STAGE, "relr3_appendix_c.py"))
    safe("APPENDIX_C_WRITES_CLOSING_SENTENCE",
         lambda: int("本轮已完成 REL-R3 范围，等待用户审核" in appc
                     and "本轮未完成 REL-R3 范围" in appc), 1)

    # ---- K STATE.md
    stt = rd(STATE)
    record("STATE_BYTES", len(stt.encode("utf-8")))
    record("STATE_SHA256", sha_b(stt.encode("utf-8")))
    safe("STATE_CURRENT_ROUND_RELR3", lambda: int("当前轮次 | P05 交付轮 REL-R3" in stt), 1)
    safe("STATE_HAS_RELR3_ROW", lambda: int("| REL-R3 | P05 交付轮（rel-r3）" in stt), 1)
    safe("STATE_HAS_RELR2_ROW", lambda: int("| REL-R2 | P05 交付轮（rel-r2）" in stt), 1)
    safe("STATE_S1_S5_SIGNED_TEXT_KEPT", lambda: int("S1–S5 已由用户签收" in stt), 1)
    safe("STATE_UNDER_12KB", lambda: int(len(stt.encode("utf-8")) <= 12288), 1)

    def state_gate_phrases():
        return sum(len(re.findall(p, stt)) for p in (r"FAILS=\d+", r"门禁.*(?:通过|PASS)"))
    safe("STATE_NO_GATE_RESULT_PHRASES", state_gate_phrases, 0)
    safe("STATE_NO_P05_S6", lambda: int(("P05-" + "S6") in stt), 0)

    # ---- L registries/rel-r3 and evidence SHA256SUMS
    reg3 = verify_sums(REG3)
    record("RELR3_REGISTRY_ITEMS", len(reg3[0]) if reg3 else "MISSING")
    record("RELR3_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG3, "SHA256SUMS.txt")))
    safe("RELR3_REGISTRY_SUMS_ALL_OK",
         lambda: "OK" if reg3 and not reg3[1] else "BAD:" + ",".join((reg3[1] if reg3 else [])[:3]), "OK")
    safe("RELR3_REGISTRY_COVERS_PREGATE",
         lambda: "ok" if reg3 and all(f in reg3[0] for f in PREGATE) else "missing", "ok")
    safe("RELR3_REGISTRY_EXTRAS_ONLY_GATE_END",
         lambda: "ok" if reg3 and not [f for f in reg3[0] if f not in PREGATE and f != "GATE_RELR3_end.txt"]
         else "extra", "ok")

    def registry_copies_match():
        for f in PREGATE:
            a, b = os.path.join(REG3, f), os.path.join(EV, f)
            if not (os.path.isfile(a) and os.path.isfile(b) and sha_f(a) == sha_f(b)):
                return "mismatch:" + f
        return "ok"
    safe("RELR3_REGISTRY_COPIES_MATCH_EVIDENCE", registry_copies_match, "ok")

    def ev_expected():
        names = []
        for name in sorted(os.listdir(EV)):
            p = os.path.join(EV, name)
            if not os.path.isfile(p) or name in EV_SUMS_EXCLUDE:
                continue
            if name.endswith(EV_EXTS):
                names.append(name)
        logd = os.path.join(EV, "logs")
        if os.path.isdir(logd):
            for name in sorted(os.listdir(logd)):
                if os.path.isfile(os.path.join(logd, name)) and name.endswith(EV_EXTS):
                    names.append("logs/" + name)
        return sorted(names)
    ev = verify_sums(EV)
    record("EVIDENCE_SUMS_ITEMS", len(ev[0]) if ev else "MISSING")
    safe("EVIDENCE_SUMS_ALL_OK",
         lambda: "OK" if ev and not ev[1] else "BAD:" + ",".join((ev[1] if ev else [])[:3]), "OK")
    safe("EVIDENCE_SUMS_COVERS_ALL_NONBINARY",
         lambda: "ok" if ev and sorted(ev[0]) == ev_expected() else
         "diff:" + ",".join(sorted(set((ev[0] if ev else [])) ^ set(ev_expected()))[:4]), "ok")

    # ---- M /tmp snapshots and script manifest
    sc, ss = tmp_snapshot(SNAP_START)
    ec, es = tmp_snapshot(SNAP_END)
    record("TMP_SNAPSHOT_START", sc + "/" + ss)
    record("TMP_SNAPSHOT_END", ec + "/" + es)
    safe("TMP_END_SNAPSHOT_PRESENT", lambda: "present" if os.path.isfile(SNAP_END) else "absent", "present")
    safe("TMP_SNAPSHOT_UNCHANGED", lambda: "same" if ec == sc and es == ss else "changed", "same")
    safe("TMP_START_COUNT_ZERO", lambda: sc, EXP_TMP_COUNT)

    def manifest_ok():
        want = set(stage_files())
        got = set(l.strip() for l in rd(MANIFEST).splitlines() if l.strip() and not l.startswith("#"))
        return "ok" if got == want else "diff:" + ",".join(sorted(got ^ want)[:5])
    safe("SCRIPT_MANIFEST_MATCHES_STAGE_DIR", manifest_ok, "ok")

    # ---- N push log shape: four pushes, no force flag, exact U393 commands
    _, push = read_table(PUSHLOG)
    actions = [r.get("action") for r in push]
    safe("PUSH_LOG_HAS_ONE_BRANCH_CREATE", lambda: actions.count("branch_create"), 1)
    safe("PUSH_LOG_FOUR_PUSHES", lambda: actions.count("push"), 4)
    safe("PUSH_LOG_FOUR_LS_REMOTE", lambda: actions.count("ls_remote"), 4)
    safe("PUSH_LOG_ALL_PUSH_RC_ZERO",
         lambda: sum(1 for r in push if r["action"] == "push" and r.get("rc") == "0"), 4)
    safe("PUSH_LOG_ALL_LS_REMOTE_MATCH",
         lambda: sum(1 for r in push if r["action"] == "ls_remote" and r.get("match") == "YES"), 4)
    cmds = [r.get("command", "") for r in push if r["action"] == "push"]
    safe("PUSH_ORDER_A_B_C_D", lambda: ",".join(r.get("order_spec", "") for r in push
                                                if r["action"] == "push"), "(a),(b),(c),(d)")
    safe("PUSH_COMMANDS_EXACT", lambda: " | ".join(cmds),
         "git push origin refs/heads/" + PRODUCT_BRANCH + ":refs/heads/" + PRODUCT_BRANCH
         + " | git push origin refs/heads/" + ARCHIVE_BRANCH + ":refs/heads/" + ARCHIVE_BRANCH
         + " | git push origin refs/tags/" + EXP_TAG1 + " | git push origin refs/tags/" + EXP_TAG2)
    banned = ["-f ", "--force", "--mirror", "--all", "--tags", "--delete"]
    safe("PUSH_NO_FORCE_FLAG",
         lambda: "none" if not any(b in c + " " for c in cmds for b in banned) else "present", "none")

    # ---- O supplementary audit / volume hard-stop conditions
    _, sens_rows = read_table(SENS)
    sens_map = {r["pattern"]: r for r in sens_rows if r.get("pattern")}
    tok = int(sens_map.get("TOKEN_SECRETS_TOTAL", {}).get("hits", "-1"))
    quotes = int(sens_map.get("TOKEN_PATTERN_QUOTES_TOTAL", {}).get("hits", "-1"))
    record("SENSITIVE_NEW_TOKEN_SECRETS", tok)
    record("SENSITIVE_NEW_TOKEN_PATTERN_QUOTES", quotes)
    safe("SENSITIVE_NEW_TOKENS_ZERO", lambda: tok, 0)
    safe("SENSITIVE_PATTERN_QUOTES_CLASSIFIED",
         lambda: "ok" if quotes >= 0 and sens_map.get("TOKEN_PATTERN_QUOTES_TOTAL", {}).get("classification")
         == "NOT_A_SECRET" else "bad", "ok")
    safe("SENSITIVE_NO_CREDENTIAL_ROWS",
         lambda: "none" if not [r for r in sens_rows
                                if r.get("classification") == "CREDENTIAL"] else "present", "none")
    _, vol_rows = read_table(VOL)
    byvol = {r["candidate"]: r for r in vol_rows}
    safe("VOLUME_A_NO_50MB", lambda: byvol.get("A_archive_branch", {}).get("blobs_ge_50mb"), "0")
    safe("VOLUME_A_NO_100MB", lambda: byvol.get("A_archive_branch", {}).get("blobs_ge_100mb"), "0")
    safe("VOLUME_A_LARGEST_UNDER_50MB",
         lambda: int(byvol.get("A_archive_branch", {}).get("largest_blob_bytes", "0")) < 50 * 1024 * 1024, 1)

    # ---- P backup plan and PR body content
    safe("BACKUP_PLAN_PRESENT", lambda: "present" if os.path.isfile(BACKUP) else "absent", "present")
    bp = rd(BACKUP)
    safe("BACKUP_PLAN_HAS_RSYNC_AND_TAR", lambda: int("rsync " in bp and "tar " in bp), 1)
    safe("BACKUP_PLAN_SAYS_NOT_EXECUTED", lambda: int("不执行" in bp or "not executed" in bp), 1)
    prbody = rd(os.path.join(EV, "PR_BODY_RELR3.md"))
    safe("PR_BODY_LINE_COUNT_LE_120", lambda: int(sum(1 for _ in open(os.path.join(EV, "PR_BODY_RELR3.md"),
                                                                      encoding="utf-8")) <= 120), 1)
    safe("PR_BODY_ENGLISH_NO_CJK", lambda: int(not re.search(r"[\u4e00-\u9fff]", prbody)), 1)
    for phrase in ("fault-injection harness", "D003-specific", "archive/p05-d003-full-20261019",
                   "p05-signed-20261019", "p05-rel-r1-20261019", "pending the REL-R3 push"):
        safe("PR_BODY_PHRASE_" + re.sub(r"[^A-Za-z0-9]+", "_", phrase)[:36],
             lambda p=phrase: int(p in prbody), 1)
    safe("PR_BODY_NO_FIXED_CLAIM",
         lambda: int(("fixed" in prbody.lower() and "not" not in prbody.lower())
                     or ("verified reachable" in prbody.lower())), 0)

    # ---- Q opening gate passed
    gs = os.path.join(REG3, "GATE_RELR3_start.txt")
    safe("GATE_START_PRESENT", lambda: "present" if os.path.isfile(gs) else "absent", "present")
    safe("GATE_START_FAILS_ZERO",
         lambda: "fails=0" if str(gate_results(gs)).split("/")[-1] == "0" else str(gate_results(gs)), "fails=0")


def write_gate(phase, out_name):
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# REL-R3 " + phase + " gate " + out_name + " (" +
             datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + ")",
             "# RECORD<TAB>KEY<TAB>value=V lines carry facts; PASS/FAIL lines carry the checks.",
             "# Every table is read by column name; directory-set sha uses Python sorted()."]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails)
                 + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    outp = os.path.join(EV, out_name)
    if not os.path.realpath(outp).startswith(os.path.realpath(EV) + os.sep):
        print("HARD_STOP --out must stay under the round evidence directory")
        return 2
    os.makedirs(EV, exist_ok=True)
    open(outp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print(lines[-3])
    print(lines[-2])
    for n, e, a, ok in CHECKS:
        if not ok:
            print("FAIL" + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    for n, x in CRASHED:
        print("CRASHED" + TAB + n + TAB + x)
    print("WROTE", os.path.relpath(outp, REPO))
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
        out = "GATE_RELR3_" + phase + ".txt"
    if not re.match(r"^GATE_RELR3_[A-Za-z0-9_]+\.txt$", out):
        print("HARD_STOP --out must be GATE_RELR3_<name>.txt")
        return 2
    if phase == "start":
        phase_start()
    else:
        phase_end()
    return write_gate(phase, out)


if __name__ == "__main__":
    sys.exit(main())
