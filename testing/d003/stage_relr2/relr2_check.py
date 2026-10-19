#!/usr/bin/env python3
# relr2_check.py -- P05 delivery round REL-R2 gate (task brief sections 1 and 7).
# One script, two read-only phases that share the same helpers (only --out differs):
#   --phase start : the opening baseline, re-derived from immutable git objects at HEAD c88bf30 plus the
#                   start top-level temporary-directory snapshot that relr2_tmpsnap.py took before any run.
#   --phase end   : closing checks: opening items still hold; the round commits and their whitelist;
#                   RULINGS pure append with exactly one new U392 row and unchanged prefix; the two
#                   annotated tags and the main-repo product-branch ref; the product branch content and
#                   the V1-V6 rows against PREREG_RELR2.tsv (read by column name); the report's derived
#                   COUNTS block against the source tables; STATE without projected gate results; the
#                   rel-r2 registry and evidence SHA256SUMS; /tmp end snapshot equal to start; the script
#                   manifest; historical entry files unchanged.
# Nothing in this script writes outside the gate file path passed with --out (under the round evidence
# directory); every table is read BY COLUMN NAME, and every directory-set sha uses Python sorted().
import os, re, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r2")
REG1 = os.path.join(P05, "registries/rel-r1")
REG2 = os.path.join(P05, "registries/rel-r2")
STAGE = os.path.join(REPO, "testing/d003/stage_relr2")
RULINGS = os.path.join(P05, "registries/RULINGS.tsv")
STATE = os.path.join(P05, "STATE.md")
REPORT = os.path.join(P05, "P05_RELR2_REPORT.md")
AGENTS = os.path.join(REPO, "AGENTS.md")
ROADMAP = os.path.join(REPO, "PROJECT_ROADMAP.md")
ISSUE = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
PREREG = os.path.join(EV, "PREREG_RELR2.tsv")
PREREG_SHA = os.path.join(EV, "PREREG_RELR2.tsv.sha256.txt")
VT = os.path.join(EV, "V_RELR2.tsv")
PROD = os.path.join(EV, "PROD_RELR2.tsv")
VOL = os.path.join(EV, "PUBLISH_VOLUME_RELR2.tsv")
SENS = os.path.join(EV, "PUBLISH_AUDIT_RELR2.tsv")
REMOTE = os.path.join(EV, "PUBLISH_REMOTE_RELR2.tsv")
BACKUP = os.path.join(EV, "EVIDENCE_BACKUP_RELR2.tsv")
NOREG = os.path.join(EV, "NOREG_PROBE_RELR2.tsv")
SNAP_START = os.path.join(EV, "TMP_SNAPSHOT_RELR2.tsv")
SNAP_END = os.path.join(EV, "TMP_SNAPSHOT_RELR2_end.tsv")
MANIFEST = os.path.join(STAGE, "relr2_scripts.txt")
PRODCLONE = os.path.join(EV, "prod")
VCLONE = os.path.join(EV, "verifyclone")

TAB = chr(9)
NL = chr(10)
ROUND = "P05 delivery round REL-R2 (rel-r2)"
BRANCH = "codex/p05-d003-fft-error-propagation"
BASE_HEAD = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
B_COMMIT = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
F4_COMMIT = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RUL_OPEN_BYTES = 157296
EXP_RUL_OPEN_SHA = "1c0aad12e7a08dc775c14aa08b756f7a1d53d959642f813647b74b957d19f545"
EXP_TMP_COUNT = "0"
EXP_TMP_SHA = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
EXP_TAG1 = "p05-signed-20261019"
EXP_TAG2 = "p05-rel-r1-20261019"
EXP_DOC = "doc/P05_D003_SUMMARY.md"
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
REL1_REGISTRY_ITEMS = 18
PREGATE = ["GATE_RELR2_start.txt", "PREREG_RELR2.tsv", "PREREG_RELR2.tsv.sha256.txt", "PROD_RELR2.tsv",
           "V_RELR2.tsv", "PUBLISH_VOLUME_RELR2.tsv", "PUBLISH_AUDIT_RELR2.tsv",
           "PUBLISH_REMOTE_RELR2.tsv", "EVIDENCE_BACKUP_RELR2.tsv", "NOREG_PROBE_RELR2.tsv",
           "NOREG_REPEAT_RELR2.tsv", "RULINGS_APPEND_RELR2.tsv", "TMP_SNAPSHOT_RELR2.tsv",
           "TMP_SNAPSHOT_RELR2_end.tsv"]
EV_SUMS_EXCLUDE = ("safe_run.log", "GATE_RELR2_pre.txt", "GATE_RELR2_end.txt")
COUNTS_KEYS = ["PREREG_ROWS", "PREREG_SHA256", "V_ROWS", "V_SAME", "V_RECORDED", "V_MISMATCH",
               "PROD_COMMITS_ABOVE_B", "PROD_HEAD", "PROD_HEAD_S4", "PROD_DOC_LINES",
               "V3_UNIT_COUNT", "V3_FAILING", "V3_MISSING", "V3_EXTRA", "V4_CASES",
               "V5_BUILD_S4_SHA256", "V5_LIBS4_SHA256", "A_NEW_BLOBS", "A_TOTAL_BYTES",
               "A_LARGEST_BLOB_BYTES", "A_BLOBS_GE_50MB", "A_BLOBS_GE_100MB", "P_NEW_BLOBS",
               "P_TOTAL_BYTES", "P_BLOBS_GE_50MB", "P_BLOBS_GE_100MB", "SENSITIVE_TOKENS_A",
               "SENSITIVE_TOKENS_P", "SENSITIVE_ABS_SRV_A", "SENSITIVE_ABS_HOME_A",
               "SENSITIVE_USERNAME_A", "SENSITIVE_EMAIL_A", "SENSITIVE_EMAIL_P", "SENSITIVE_HOSTNAME",
               "EVIDENCE_TOTAL_BYTES", "EVIDENCE_SUBDIRS", "NOREG_PROBE_CASES", "NOREG_PROBE_ROWS",
               "NOREG_FOUND", "RULINGS_APPENDED_ROWS", "RULINGS_BEFORE_BYTES", "RULINGS_AFTER_BYTES",
               "TAGS_CREATED"]

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


def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


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


def read_gate_kv(path):
    d = {}
    if not os.path.isfile(path):
        return d
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 3 and f[0] == "RECORD" and f[2].startswith("value="):
            d[f[1]] = f[2][len("value="):]
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


# ------------------------------------------------------------------ phase start
def phase_start():
    record("ROUND", ROUND)
    record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    record("OPENING_BASELINE_SOURCE",
           "HEAD c88bf30 git objects (RULINGS blob) + TMP_SNAPSHOT_RELR2.tsv, both created before any run")
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
    record("OPENING_TAGS_AND_BRANCH_ABSENT",
           "verified at round opening before any write: p05-signed-20261019, p05-rel-r1-20261019, refs/heads/p05/* absent")
    record("OPENING_GIT_STATUS", "empty (round opening, first read-only command; see report section 1)")

    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), BRANCH)
    safe("HEAD_IS_RELR1_II", lambda: sh(["git", "rev-parse", "HEAD"]), BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("S4_DIR_ZERO_MODIFICATION",
         lambda: (sh(["git", "diff", "--name-only", BASE_HEAD, "--", "S4"]) or "unmodified"), "unmodified")
    safe("RULINGS_OPENING_BYTES", lambda: len(base), EXP_RUL_OPEN_BYTES)
    safe("RULINGS_OPENING_SHA256", lambda: sha_b(base), EXP_RUL_OPEN_SHA)
    safe("RULINGS_OPENING_LAST_IS_U391", lambda: rul_lines[-1].split(TAB)[0], "U391")
    safe("RULINGS_OPENING_DATA_ROWS_395", lambda: len(rul_lines), 395)
    safe("RULINGS_OPENING_5_FIELDS",
         lambda: "ok" if all(len(l.split(TAB)) == 5 for l in rul_lines) else "bad", "ok")

    reg1 = verify_sums(REG1)
    record("RELR1_REGISTRY_ITEMS", reg1[0].__len__() if reg1 else "MISSING")
    record("RELR1_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG1, "SHA256SUMS.txt")))
    safe("RELR1_REGISTRY_SUMS_ALL_OK_18",
         lambda: "18/%s" % ("OK" if reg1 and not reg1[1] else "BAD:" + ",".join((reg1[1] if reg1 else [])[:3])),
         "18/OK")

    cnt, tsha = tmp_snapshot(SNAP_START)
    record("TMP_COUNT", cnt)
    record("TMP_SHA256", tsha)
    safe("TMP_START_COUNT_ZERO", lambda: cnt, EXP_TMP_COUNT)
    safe("TMP_START_SHA256", lambda: tsha, EXP_TMP_SHA)

    safe("PREREG_PRESENT", lambda: "present" if os.path.isfile(PREREG) else "absent", "present")
    # the sha256 record is the pre-registration's own sha256 file (by column/format, not by index)
    rec_sha = None
    for line in rd(PREREG_SHA).splitlines():
        if line.startswith("PREREG_RELR2.tsv" + TAB):
            rec_sha = line.split(TAB)[1]
    record("PREREG_RECORD_SHA256", rec_sha)
    safe("PREREG_SHA_MATCHES_RECORD", lambda: sha_f(PREREG), rec_sha)
    _, preg = read_table(PREREG)
    safe("PREREG_ROWS_6", lambda: len(preg), 6)
    safe("PREREG_HAS_V1_V6", lambda: ",".join(r["test_id"] for r in preg),
         "V1,V2,V3,V4,V5,V6")

    def status_only_round():
        # use the raw stdout: sh() strips surrounding whitespace and would eat the leading status column
        st = [l for l in run(["git", "status", "--porcelain=v1", "-uall"]).stdout.splitlines() if l.strip()]
        bad = [l for l in st if not (l[3:].startswith("checkpoints/p05/") or
                                     l[3:].startswith("testing/d003/stage_relr2/"))]
        return "clean" if not bad else "unexpected:" + ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_ROUND_FILES", status_only_round, "clean")

    def manifest_ok():
        want = set(stage_files())
        got = set(l.strip() for l in rd(MANIFEST).splitlines() if l.strip() and not l.startswith("#"))
        return "ok" if got == want else "diff:" + ",".join(sorted(got ^ want)[:5])
    safe("SCRIPT_MANIFEST_MATCHES_STAGE_DIR", manifest_ok, "ok")
    record("STAGE_SCRIPT_COUNT", len(stage_files()))
    record("STAGE_MANIFEST_SHA256", sha_f(MANIFEST))


# ------------------------------------------------------------------ phase end
def actual_counts():
    d = {}
    _, preg = read_table(PREREG)
    d["PREREG_ROWS"] = str(len(preg))
    d["PREREG_SHA256"] = sha_f(PREREG)
    _, vt = read_table(VT)
    d["V_ROWS"] = str(len(vt))
    d["V_SAME"] = str(sum(1 for r in vt if r.get("result") == "SAME"))
    d["V_RECORDED"] = str(sum(1 for r in vt if r.get("result") == "RECORDED"))
    d["V_MISMATCH"] = str(sum(1 for r in vt if r.get("result") == "MISMATCH"))
    prod = read_kv(PROD)
    d["PROD_COMMITS_ABOVE_B"] = prod.get("COMMITS_ABOVE_B", "NA")
    d["PROD_HEAD"] = prod.get("PROD_HEAD", "NA")
    d["PROD_HEAD_S4"] = prod.get("PROD_HEAD_S4", "NA")
    d["PROD_DOC_LINES"] = prod.get("DOC_LINES", "NA")
    vrec = read_kv(VT)
    d["V3_UNIT_COUNT"] = vrec.get("V3_UNIT_COUNT", "NA")
    d["V3_FAILING"] = "0" if vrec.get("V3_FAILING") == "none" else "NONZERO"
    d["V3_MISSING"] = "0" if vrec.get("V3_MISSING") == "none" else "NONZERO"
    d["V3_EXTRA"] = "0" if vrec.get("V3_EXTRA") == "none" else "NONZERO"
    d["V4_CASES"] = vrec.get("V4_CASES", "NA")
    d["V5_BUILD_S4_SHA256"] = vrec.get("V5_BUILD_S4_SHA256", "NA")
    d["V5_LIBS4_SHA256"] = vrec.get("V5_LIBS4_SHA256", "NA")
    vol = {}
    largest = {}
    for line in rd(VOL).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) == 8 and f[0] in ("A_work_branch", "P_product_branch"):
            vol[f[0]] = {"blobs": f[3], "bytes": f[4], "ge50": f[6], "ge100": f[7]}
        elif len(f) == 5 and f[0] in ("A_work_branch", "P_product_branch"):
            largest.setdefault(f[0], []).append(int(f[2]))
    d["A_NEW_BLOBS"] = vol.get("A_work_branch", {}).get("blobs", "NA")
    d["A_TOTAL_BYTES"] = vol.get("A_work_branch", {}).get("bytes", "NA")
    d["A_LARGEST_BLOB_BYTES"] = str(max(largest.get("A_work_branch", [0])))
    d["A_BLOBS_GE_50MB"] = vol.get("A_work_branch", {}).get("ge50", "NA")
    d["A_BLOBS_GE_100MB"] = vol.get("A_work_branch", {}).get("ge100", "NA")
    d["P_NEW_BLOBS"] = vol.get("P_product_branch", {}).get("blobs", "NA")
    d["P_TOTAL_BYTES"] = vol.get("P_product_branch", {}).get("bytes", "NA")
    d["P_BLOBS_GE_50MB"] = vol.get("P_product_branch", {}).get("ge50", "NA")
    d["P_BLOBS_GE_100MB"] = vol.get("P_product_branch", {}).get("ge100", "NA")
    sens = {}
    for line in rd(SENS).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 4 and f[0] in ("A", "P", "D") and f[1] != "FILES_SCANNED":
            sens[(f[0], f[1])] = int(f[2])
    tok = ("TOKEN_GHP", "TOKEN_GITHUB_PAT", "TOKEN_AKIA", "PRIVATE_KEY_BEGIN", "PASSWORD_ASSIGN")
    d["SENSITIVE_TOKENS_A"] = str(sum(sens.get(("A", k), 0) for k in tok))
    d["SENSITIVE_TOKENS_P"] = str(sum(sens.get(("P", k), 0) for k in tok))
    d["SENSITIVE_ABS_SRV_A"] = str(sens.get(("A", "ABS_PATH_SRV"), 0))
    d["SENSITIVE_ABS_HOME_A"] = str(sens.get(("A", "ABS_PATH_HOME"), 0))
    d["SENSITIVE_USERNAME_A"] = str(sens.get(("A", "USERNAME"), 0))
    d["SENSITIVE_EMAIL_A"] = str(sens.get(("A", "EMAIL"), 0))
    d["SENSITIVE_EMAIL_P"] = str(sens.get(("P", "EMAIL"), 0))
    d["SENSITIVE_HOSTNAME"] = str(sens.get(("A", "HOSTNAME"), 0) + sens.get(("P", "HOSTNAME"), 0))
    btot = "NA"
    for line in rd(BACKUP).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if f[0] == "TOTAL":
            btot = f[1]
    d["EVIDENCE_TOTAL_BYTES"] = btot
    m = re.search(r"# subdirectory count: (\d+)", rd(BACKUP))
    d["EVIDENCE_SUBDIRS"] = m.group(1) if m else "NA"
    nrows = []
    cases = set()
    for line in rd(NOREG).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) < 6 or f[0] == "case":
            continue
        nrows.append({"case": f[0], "tree": f[1], "rc": f[2], "status": f[3],
                      "finite": f[4], "same": f[5]})
        cases.add(f[0])
    d["NOREG_PROBE_ROWS"] = str(len(nrows))
    d["NOREG_PROBE_CASES"] = str(len(cases))
    found = 0
    by = {}
    for r in nrows:
        by.setdefault(r["case"], {})[r["tree"]] = r
    for case, dd in by.items():
        b, f4 = dd.get("B"), dd.get("F4")
        if not (b and f4):
            continue
        b_failed = (b["rc"] != "0" or b["status"] != "RETURNED" or b["finite"] != "True")
        f_visible = (f4["status"] == "EXCEPTION" or f4["rc"] != "0")
        if b_failed and f_visible and b["same"] != "YES":
            found += 1
    d["NOREG_FOUND"] = str(found)
    base = git_bytes(BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv")
    cur = open(RULINGS, "rb").read()
    d["RULINGS_BEFORE_BYTES"] = str(len(base))
    d["RULINGS_AFTER_BYTES"] = str(len(cur))
    d["RULINGS_APPENDED_ROWS"] = str(len([l for l in cur[len(base):].decode("utf-8").split(NL) if l.strip()])
                                     if cur.startswith(base) else -1)
    d["TAGS_CREATED"] = str(int(sh(["git", "cat-file", "-t", EXP_TAG1]) == "tag")
                            + int(sh(["git", "cat-file", "-t", EXP_TAG2]) == "tag"))
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


def phase_end():
    record("ROUND", ROUND)
    record("END_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    record("OPENING_BASELINE_SOURCE",
           "HEAD c88bf30 git objects (RULINGS blob) + TMP_SNAPSHOT_RELR2.tsv, both created before any run")
    base_rul = git_bytes(BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv")
    base_state = git_bytes(BASE_HEAD + ":checkpoints/p05/STATE.md")
    base_agents = git_bytes(BASE_HEAD + ":AGENTS.md")
    base_roadmap = git_bytes(BASE_HEAD + ":PROJECT_ROADMAP.md")
    base_issue = git_bytes(BASE_HEAD + ":testing/s4test/ISSUE_REGISTRY.md")
    record("RULINGS_OPENING_BYTES", len(base_rul))
    record("RULINGS_OPENING_SHA256", sha_b(base_rul))

    # ---- opening items still hold
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
    reg1 = verify_sums(REG1)
    safe("RELR1_REGISTRY_SUMS_ALL_OK_18",
         lambda: "18/%s" % ("OK" if reg1 and not reg1[1] else "BAD:" + ",".join((reg1[1] if reg1 else [])[:3])),
         "18/OK")

    # ---- round commits and whitelist
    n_commits = sh(["git", "rev-list", "--count", BASE_HEAD + "..HEAD"])
    record("ROUND_COMMITS", n_commits)
    # 0 = pre-run before commit (i), 1 = formal end gate after commit (i); commit (ii) is the gate's
    # own appendix commit and cannot exist before the gate runs.
    safe("ROUND_COMMITS_0_OR_1", lambda: "ok" if n_commits in ("0", "1") else "unexpected:" + n_commits, "ok")

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
         lambda: "ok" if all(p.startswith("checkpoints/p05/") or p.startswith("testing/d003/stage_relr2/")
                             for p in changed) else "outside", "ok")
    safe("ROUND_NO_DELETIONS",
         lambda: sh(["git", "diff", "--name-status", "--diff-filter=DR", BASE_HEAD, "HEAD"]) or "none", "none")

    # ---- RULINGS pure append U392
    cur_rul = open(RULINGS, "rb").read()
    record("RULINGS_BYTES", len(cur_rul))
    record("RULINGS_SHA256", sha_b(cur_rul))
    safe("RULINGS_PURE_APPEND", lambda: "ok" if cur_rul.startswith(base_rul) else "prefix_changed", "ok")
    safe("RULINGS_PREFIX_SHA_UNCHANGED", lambda: sha_b(cur_rul[:len(base_rul)]), EXP_RUL_OPEN_SHA)
    add = cur_rul[len(base_rul):] if cur_rul.startswith(base_rul) else b""
    add_lines = [l for l in add.decode("utf-8").split(NL) if l.strip()]
    safe("RULINGS_EXACTLY_ONE_NEW_ROW", lambda: len(add_lines), 1)
    addf = add_lines[0].split(TAB) if add_lines else []
    safe("RULINGS_NEW_ROW_U392", lambda: addf[0] if addf else "none", "U392")
    safe("RULINGS_NEW_ROW_5_FIELDS", lambda: len(addf), 5)
    safe("RULINGS_NEW_ROW_STATUS_ACTIVE", lambda: addf[4] if len(addf) == 5 else "none", "生效")
    safe("RULINGS_NEW_ROW_HAS_AUTHORISATION_WORDING",
         lambda: "ok" if len(addf) == 5 and "用户对话授权" in addf[1] and "p05/d003-fft-error-propagation" in addf[2]
         else "missing", "ok")

    # ---- tags and product branch ref
    safe("TAG1_ANNOTATED", lambda: sh(["git", "cat-file", "-t", EXP_TAG1]), "tag")
    safe("TAG2_ANNOTATED", lambda: sh(["git", "cat-file", "-t", EXP_TAG2]), "tag")
    safe("TAG1_PEELS_TO_F4", lambda: sh(["git", "rev-parse", EXP_TAG1 + "^{commit}"]), F4_COMMIT)
    safe("TAG2_PEELS_TO_RELR1_II", lambda: sh(["git", "rev-parse", EXP_TAG2 + "^{commit}"]), BASE_HEAD)
    prod_head = sh(["git", "-C", PRODCLONE, "rev-parse", "HEAD"])
    main_ref = sh(["git", "rev-parse", "refs/heads/" + PRODUCT_BRANCH])
    record("PROD_CLONE_HEAD", prod_head)
    record("MAIN_PRODUCT_REF", main_ref)
    safe("MAIN_REF_EQ_PROD_CLONE_HEAD", lambda: main_ref, prod_head)
    safe("PROD_CLONE_HEAD_S4", lambda: sh(["git", "-C", PRODCLONE, "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("PROD_COMMITS_ABOVE_B", lambda: sh(["git", "-C", PRODCLONE, "rev-list", "--count", B_COMMIT + "..HEAD"]), 2)
    changed_prod = [l for l in sh(["git", "-C", PRODCLONE, "diff", "--name-only", B_COMMIT + "..HEAD"]).splitlines()
                    if l.strip()]
    non_s4 = [p for p in changed_prod if not p.startswith("S4/")]
    record("PROD_NON_S4_CHANGED", ",".join(non_s4))
    safe("PROD_NON_S4_ONLY_DOC", lambda: ",".join(non_s4), EXP_DOC)
    safe("PROD_FORBIDDEN_ADDED",
         lambda: "none" if not [p for p in changed_prod
                                if p.startswith("checkpoints/") or p.startswith("testing/d003/")
                                or p == "AGENTS.md"] else "present", "none")
    safe("PROD_DOC_LINES_LE_200",
         lambda: sum(1 for _ in open(os.path.join(PRODCLONE, EXP_DOC), encoding="utf-8")), 95)
    safe("PROD_WORKTREE_CLEAN", lambda: sh(["git", "-C", PRODCLONE, "status", "--porcelain"]) or "clean", "clean")
    capi_ok = True
    for spec in ("Makefile", "Makefile.Linux", "Makefile.common"):
        a = git_bytes(B_COMMIT + ":" + spec)
        b = git_bytes(prod_head + ":" + spec) if True else b""
        if a != b:
            capi_ok = False
    safe("PROD_BUILD_INPUTS_MAKEFILES_EQ_B", lambda: int(capi_ok), 1)
    ex_ok = sh(["git", "-C", PRODCLONE, "diff", "--name-only", B_COMMIT + "..HEAD", "--", "examples"]) or "none"
    safe("PROD_BUILD_INPUTS_EXAMPLES_EQ_B", lambda: ex_ok, "none")

    # ---- V table against PREREG (by column name)
    _, preg = read_table(PREREG)
    _, vt = read_table(VT)
    pmap = {r["test_id"]: r for r in preg}
    vmap = {r["test_id"]: r for r in vt}
    safe("V_TABLE_ROWS_6", lambda: len(vt), 6)
    safe("V_TABLE_IDS", lambda: ",".join(sorted(vmap)), ",".join(sorted(pmap)))
    safe("V_EXPECTED_MATCH_PREREG",
         lambda: "ok" if all(vmap[k]["expected"] == pmap[k]["expected"] for k in pmap if k in vmap) else "diff",
         "ok")
    safe("V_RESULT_NO_MISMATCH",
         lambda: ",".join("%s=%s" % (k, vmap[k]["result"]) for k in sorted(vmap)), "V1=SAME,V2=SAME,V3=SAME,V4=SAME,V5=RECORDED,V6=SAME")
    safe("V5_IS_RECORD_ONLY", lambda: vmap.get("V5", {}).get("result"), "RECORDED")

    # ---- report: derived COUNTS block against the source tables
    rc = report_counts()
    record("REPORT_COUNTS_KEYS", len(rc) if rc else "MISSING")
    actual = actual_counts()

    def counts_all():
        if rc is None:
            return "missing_block"
        missing = [k for k in COUNTS_KEYS if k not in rc]
        extra = [k for k in rc if k not in COUNTS_KEYS]
        if missing or extra:
            return "missing=" + ",".join(missing[:3]) + ";extra=" + ",".join(extra[:3])
        bad = [k for k in COUNTS_KEYS if rc[k] != actual[k]]
        return "ok" if not bad else "mismatch:" + ",".join("%s=%s/%s" % (k, rc[k], actual[k]) for k in bad[:4])
    safe("REPORT_COUNTS_MATCH_SOURCE_TABLES", counts_all, "ok")
    for k in ("V_ROWS", "V_SAME", "V_MISMATCH", "A_NEW_BLOBS", "A_LARGEST_BLOB_BYTES",
              "SENSITIVE_ABS_SRV_A", "EVIDENCE_TOTAL_BYTES", "NOREG_FOUND", "RULINGS_APPENDED_ROWS"):
        safe("REPORT_COUNT_" + k, lambda k=k: rc.get(k, "MISSING") if rc else "MISSING", actual[k])

    # ---- report content requirements
    rep = rd(REPORT)
    safe("REPORT_HAS_P05_RELR2_APPENDIX_C_PLACEHOLDER", lambda: int("## 附录 C 正式 end 门禁结果" in rep), 1)
    for sec in ("## 1 范围与开工门禁", "## 2 产品分支构建", "## 3 免注入可达路径调研",
                "## 4 产品分支验证", "## 5 主仓库引用写入", "## 6 上传前审查", "## 7 ROADMAP",
                "## 8 违规披露", "## 9 待用户裁决", "## 10 两阶段提交", "## 附录 A", "## 附录 B"):
        safe("REPORT_SECTION_" + re.sub(r"[^0-9A-Za-z]+", "_", sec.split(" ", 1)[1]).strip("_"),
             lambda sec=sec: int(sec in rep), 1)
    for phrase in ("未找到免注入可达路径，产品分支不含 D003 专用测试", "越界写入尝试", "工具/脚本事件",
                   "Draft PR", "PROJECT_ROADMAP.md", "敏感信息", "证据离线备份", "git log -1",
                   "git status --short", "预注册", "SAME", "RECORDED"):
        safe("REPORT_PHRASE_" + re.sub(r"[^A-Za-z0-9]+", "_", phrase)[:40], lambda p=phrase: int(p in rep), 1)
    # the closing sentence is written by relr2_appendix_c.py in appendix C after the formal gate, so the
    # pre-gate body cannot contain it; assert that the appendix script will write it.
    appc = rd(os.path.join(STAGE, "relr2_appendix_c.py"))
    safe("APPENDIX_C_WRITES_CLOSING_SENTENCE",
         lambda: int("本轮已完成 REL-R2 范围，等待用户审核" in appc
                     and "本轮未完成 REL-R2 范围" in appc), 1)
    safe("REPORT_NO_P05_S6", lambda: int(("P05-" + "S6") in rep), 0)
    safe("REPORT_NO_PUBLISHED_CLAIM", lambda: int(("已发布" in rep) or ("REL-R2 已签收" in rep)), 0)
    safe("REPORT_APPENDIX_C_PLACEHOLDER_TEXT",
         lambda: int("照实写 INCOMPLETE" in rep), 1)

    # ---- STATE.md
    stt = rd(STATE)
    record("STATE_BYTES", len(stt.encode("utf-8")))
    record("STATE_SHA256", sha_b(stt.encode("utf-8")))
    safe("STATE_CURRENT_ROUND_RELR2", lambda: int("当前轮次 | P05 交付轮 REL-R2" in stt), 1)
    safe("STATE_RELR1_ROW_HAS_COUNTS",
         lambda: int(all(k in stt for k in ("SAME=317", "BOTH_FAIL=12", "SKIP_DECLARED=5", "NEW_FAIL=0",
                                           "DIFF=0", "FLAKY=0", "unit_count=265"))), 1)
    safe("STATE_HAS_RELR2_ROW", lambda: int("| REL-R2 | P05 交付轮（rel-r2）" in stt), 1)
    safe("STATE_UNDER_8KB", lambda: int(len(stt.encode("utf-8")) <= 8192), 1)

    def state_gate_phrases():
        return sum(len(re.findall(p, stt)) for p in (r"FAILS=\d+", r"门禁.*(?:通过|PASS)"))
    safe("STATE_NO_GATE_RESULT_PHRASES", state_gate_phrases, 0)
    safe("STATE_NO_P05_S6", lambda: int(("P05-" + "S6") in stt), 0)
    safe("STATE_S1_S5_SIGNED_TEXT_KEPT", lambda: int("S1–S5 已由用户签收" in stt), 1)

    # ---- registries/rel-r2 and evidence SHA256SUMS
    reg2 = verify_sums(REG2)
    record("RELR2_REGISTRY_ITEMS", len(reg2[0]) if reg2 else "MISSING")
    record("RELR2_REGISTRY_SUMS_SHA256", sha_f(os.path.join(REG2, "SHA256SUMS.txt")))
    safe("RELR2_REGISTRY_SUMS_ALL_OK",
         lambda: "OK" if reg2 and not reg2[1] else "BAD:" + ",".join((reg2[1] if reg2 else [])[:3]), "OK")
    safe("RELR2_REGISTRY_COVERS_PREGATE",
         lambda: "ok" if reg2 and all(f in reg2[0] for f in PREGATE) else "missing", "ok")
    safe("RELR2_REGISTRY_EXTRAS_ONLY_GATE_END",
         lambda: "ok" if reg2 and not [f for f in reg2[0] if f not in PREGATE and f != "GATE_RELR2_end.txt"]
         else "extra", "ok")

    def registry_copies_match():
        for f in PREGATE:
            a, b = os.path.join(REG2, f), os.path.join(EV, f)
            if not (os.path.isfile(a) and os.path.isfile(b) and sha_f(a) == sha_f(b)):
                return "mismatch:" + f
        return "ok"
    safe("RELR2_REGISTRY_COPIES_MATCH_EVIDENCE", registry_copies_match, "ok")

    def ev_expected():
        names = []
        for name in sorted(os.listdir(EV)):
            p = os.path.join(EV, name)
            if not os.path.isfile(p) or name in EV_SUMS_EXCLUDE:
                continue
            if name == "SHA256SUMS.txt":
                continue
            if name.endswith((".txt", ".tsv", ".log")):
                names.append(name)
        logd = os.path.join(EV, "logs")
        if os.path.isdir(logd):
            for name in sorted(os.listdir(logd)):
                if os.path.isfile(os.path.join(logd, name)) and name.endswith((".txt", ".tsv", ".log")):
                    names.append("logs/" + name)
        return sorted(names)
    ev = verify_sums(EV)
    record("EVIDENCE_SUMS_ITEMS", len(ev[0]) if ev else "MISSING")
    safe("EVIDENCE_SUMS_ALL_OK",
         lambda: "OK" if ev and not ev[1] else "BAD:" + ",".join((ev[1] if ev else [])[:3]), "OK")
    safe("EVIDENCE_SUMS_COVERS_ALL_NONBINARY",
         lambda: "ok" if ev and sorted(ev[0]) == ev_expected() else
         "diff:" + ",".join(sorted(set((ev[0] if ev else [])) ^ set(ev_expected()))[:4]), "ok")

    # ---- /tmp snapshots and script manifest
    sc, ss = tmp_snapshot(SNAP_START)
    ec, es = tmp_snapshot(SNAP_END)
    record("TMP_SNAPSHOT_START", sc + "/" + ss)
    record("TMP_SNAPSHOT_END", ec + "/" + es)
    safe("TMP_END_SNAPSHOT_PRESENT", lambda: "present" if os.path.isfile(SNAP_END) else "absent", "present")
    safe("TMP_SNAPSHOT_UNCHANGED", lambda: "same" if ec == sc and es == ss else "changed", "same")

    def manifest_ok():
        want = set(stage_files())
        got = set(l.strip() for l in rd(MANIFEST).splitlines() if l.strip() and not l.startswith("#"))
        return "ok" if got == want else "diff:" + ",".join(sorted(got ^ want)[:5])
    safe("SCRIPT_MANIFEST_MATCHES_STAGE_DIR", manifest_ok, "ok")

    # ---- opening gate passed
    gs = os.path.join(REG2, "GATE_RELR2_start.txt")
    safe("GATE_START_PRESENT", lambda: "present" if os.path.isfile(gs) else "absent", "present")
    safe("GATE_START_FAILS_ZERO",
         lambda: "fails=0" if str(gate_results(gs)).split("/")[-1] == "0" else str(gate_results(gs)), "fails=0")

    # ---- product verification sanity (heads recorded by V table)
    vrec = read_kv(VT)
    record("VCLONE_HEAD", vrec.get("VCLONE_HEAD", "NA"))
    safe("VERIFY_CLONE_HEAD_EQ_PROD_HEAD", lambda: vrec.get("VCLONE_HEAD"), prod_head)
    safe("VERIFY_CLONE_HEAD_S4", lambda: vrec.get("VCLONE_HEAD_S4"), EXP_S4)
    remote_rows = read_table(REMOTE)[1]
    safe("REMOTE_NO_PUBLISHED_P05_OR_TAGS",
         lambda: "ok" if all(r["result"] in ("SAME", "RECORDED") for r in remote_rows) and
         not any(r["check"].startswith("remote_") and r["actual"] == "present" for r in remote_rows) else "bad", "ok")
    safe("NOREG_TEST_ABSENT_FROM_PRODUCT",
         lambda: "none" if not [p for p in changed_prod if p.startswith("testing/s4test/test_p05_")] else "present",
         "none")


def write_gate(phase, out_name):
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# REL-R2 " + phase + " gate " + out_name + " (" +
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
        out = "GATE_RELR2_" + phase + ".txt"
    if not re.match(r"^GATE_RELR2_[A-Za-z0-9_]+\.txt$", out):
        print("HARD_STOP --out must be GATE_RELR2_<name>.txt")
        return 2
    if phase == "start":
        phase_start()
    else:
        phase_end()
    return write_gate(phase, out)


if __name__ == "__main__":
    sys.exit(main())
