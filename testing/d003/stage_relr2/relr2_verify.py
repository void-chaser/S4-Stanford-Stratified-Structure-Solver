#!/usr/bin/env python3
# relr2_verify.py -- P05 delivery round REL-R2: product-branch verification V1-V6 (task brief section 4).
# Read-only for the main repository (the product branch ref and the tags are read); writes only under
# $EV/verify/, $EV/verifyclone/ and $EV/V_RELR2.tsv (+ the log files under $EV/).  Resumable: each heavy
# step is recorded with a '.done' marker so a re-invocation does not repeat a finished build or test.
# Rules are read from PREREG_RELR2.tsv by column name; nothing is hard-coded where the pre-registration
# already names it.
import os, sys, subprocess, hashlib, re, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
PROD = os.path.join(EV, "prod")
VCLONE = os.path.join(EV, "verifyclone")
LOGS = os.path.join(EV, "logs")
WORK = os.path.join(EV, "verify")
TAB = chr(9)
NL = chr(10)
BRANCH = "p05/d003-fft-error-propagation"
BASE = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
TAG1, TAG2 = "p05-signed-20261019", "p05-rel-r1-20261019"
EXP_TAG1_COMMIT = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_TAG2_COMMIT = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
EXP_DOC = "doc/P05_D003_SUMMARY.md"
REL_R1_S4_BIN = "fb375c726101ae2d935e929fece54b1867aa0435b24e9fe92bdeda77314396f2"
REL_R1_LIBS4 = "a28eaa5d6a0ed347870c9bf9f4c38d16cac23f340cfe17cf1725854f8c6d8b8d"
REG = os.path.join(REPO, "checkpoints/p05/registries")
UNITS_R1 = os.path.join(REG, "rel-r1/MAKETEST_UNITS_RELR1.tsv")
MAKETEST_PYTHON = ["make", "test", "PYTHON=python3"]
TIMEOUT = 5400

STAGES = [
    ("test_python_binding", "=== original smoke tests (testing/test_python_binding.py) ==="),
    ("s4test_unittest", "=== S4 test suite (testing/s4test) ==="),
    ("selftest_analytic", "=== analytic reference self-check ==="),
    ("lua_regression", "=== S4 Lua test suite ==="),
    ("lua_regression_negative", "=== S4 Lua test suite negative ==="),
    ("lua_api_negative", "=== S4 Lua API negative ==="),
]
UNIT_STAGES = ("test_python_binding", "s4test_unittest")
STAGE_UNITS = ("selftest_analytic", "lua_regression", "lua_regression_negative", "lua_api_negative")
FAIL_STATUS = ("FAIL", "ERROR", "unexpected success")
UNIT_RE = re.compile(r"^(test_[A-Za-z0-9_]+) \(([A-Za-z0-9_.]+)\)(.*)$")
STATUS_RE = re.compile(r"\.\.\.\s+(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sh(args, cwd=REPO, check=False, timeout=TIMEOUT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p


def git(args, cwd=REPO):
    return sh(["git"] + args, cwd=cwd).stdout.strip()


def read_tsv_by_name(path):
    rows = []
    header = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.rstrip(NL).split(TAB)
        if header is None:
            header = fields
            continue
        rows.append(dict(zip(header, fields)))
    return header, rows


def read_prereg():
    header, rows = read_tsv_by_name(os.path.join(EV, "PREREG_RELR2.tsv"))
    return {r["test_id"]: r for r in rows}


def run_step(name, argv, cwd, logname):
    """Run a command once and remember its rc and log path."""
    d = os.path.join(WORK, name + ".done")
    logp = os.path.join(LOGS, logname)
    if os.path.isfile(d):
        return {"rc": open(d, encoding="utf-8").read().strip(), "log": logp, "reused": True}
    os.makedirs(LOGS, exist_ok=True)
    t0 = datetime.datetime.now(datetime.timezone.utc)
    # merge stderr into stdout: Python unittest writes its verbose per-unit lines to stderr, so
    # capturing the two streams separately would destroy the order the make test parser needs.
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=TIMEOUT)
    data = ("% $ " + " ".join(argv) + NL
            + "# rc=" + str(p.returncode) + " utc=" + t0.strftime("%Y-%m-%dT%H:%M:%SZ") + NL
            + p.stdout)
    open(logp, "w", encoding="utf-8").write(data)
    os.makedirs(WORK, exist_ok=True)
    open(d, "w", encoding="utf-8").write(str(p.returncode))
    return {"rc": str(p.returncode), "log": logp, "reused": False}


# ---- make test parsing (same unit grammar as relr1_judge_maketest.py, re-implemented here) ----
def split_blocks(lines):
    marks = []
    for name, banner in STAGES:
        for i, l in enumerate(lines):
            if l.strip() == banner:
                marks.append((i, name))
                break
    marks.sort()
    blocks = {}
    for k, (start, name) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        blocks[name] = lines[start:end]
    return blocks


def parse_unittest_block(block):
    units = []
    i, n = 0, len(block)
    while i < n:
        m = UNIT_RE.match(block[i].strip())
        if not m:
            i += 1
            continue
        uid = m.group(2)
        st = STATUS_RE.search(m.group(3))
        status = st.group(1) if st else None
        j = i + 1
        while status is None and j < n:
            nxt = block[j].strip()
            if UNIT_RE.match(nxt):
                break
            st = STATUS_RE.search(nxt)
            status = st.group(1) if st else None
            j += 1
        units.append((uid, status if status else "UNRECOGNISED"))
        i = j if j > i else i + 1
    return units


def parse_maketest(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    blocks = split_blocks(lines)
    units = {}
    recon = {}
    for name in UNIT_STAGES:
        block = blocks.get(name, [])
        seen = {}
        for uid, st in parse_unittest_block(block):
            seen[uid] = "DUPLICATE" if uid in seen else st
        for uid, st in seen.items():
            units[uid] = (st, name)
        ran = None
        skipped = None
        for l in block:
            m = re.search(r"^Ran (\d+) tests?", l.strip())
            if m:
                ran = int(m.group(1))
            m2 = re.search(r"skipped=(\d+)", l)
            if m2:
                skipped = int(m2.group(1))
        if skipped is None and any(l.strip() == "OK" for l in block):
            skipped = 0
        got_skipped = sum(1 for st in seen.values() if st == "skipped")
        recon[name] = {"units": len(seen), "ran": ran, "skipped_expected": skipped,
                       "skipped_got": got_skipped,
                       "ok": (ran is not None and len(seen) == ran and skipped is not None
                              and got_skipped == skipped)}
    for name in STAGE_UNITS:
        block = blocks.get(name, [])
        failed = any(l.startswith("make: ***") and "Error" in l for l in block)
        units[name] = ("FAIL" if failed else ("ok" if block else "MISSING"), name)
        recon[name] = {"units": 1 if block else 0, "ran": None, "skipped_expected": None,
                       "skipped_got": None, "ok": bool(block) and not failed}
    return units, recon


def rel_r1_f4_units():
    header, rows = read_tsv_by_name(UNITS_R1)
    col = "F4_p1"
    return set(r["unit"] for r in rows if r.get(col) != "ABSENT" and r["unit"])


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    prereg = read_prereg()
    results = []
    rec = {}

    def add(test_id, item, expected, actual, result):
        results.append({"test_id": test_id, "item": item, "expected": expected, "actual": actual,
                        "result": result})

    # ---------- V1
    v1 = git(["-C", PROD, "rev-parse", "HEAD:S4"])
    rec["V1_HEAD_S4"] = v1
    add("V1", "product branch HEAD:S4", prereg["V1"]["expected"], v1,
        "SAME" if v1 == prereg["V1"]["expected"] else "MISMATCH")

    # ---------- V2: changed paths vs B, whitelist
    changed = [l.split(TAB) for l in git(["-C", PROD, "diff", "--name-status", BASE + "..HEAD"]).splitlines() if l]
    non_s4 = [c for c in changed if not c[-1].startswith("S4/")]
    non_s4_paths = [c[-1] for c in non_s4]
    allowed = {EXP_DOC}
    test_files = [p for p in non_s4_paths if re.match(r"^testing/s4test/test_p05_[A-Za-z0-9_]+\.py$", p)]
    bad = [p for p in non_s4_paths if p not in allowed and p not in test_files]
    doc_lines = 0
    docp = os.path.join(PROD, EXP_DOC)
    if os.path.isfile(docp):
        doc_lines = sum(1 for _ in open(docp, encoding="utf-8"))
    v2_ok = (not bad) and len(test_files) <= 1 and doc_lines <= 200 and EXP_DOC in non_s4_paths
    if not test_files:
        rec["V2_TEST_FILE"] = "none"
    else:
        rec["V2_TEST_FILE"] = test_files[0]
    rec["V2_NON_S4_PATHS"] = ",".join(non_s4_paths)
    rec["V2_DOC_LINES"] = doc_lines
    add("V2", "product branch non-S4 additions vs B", prereg["V2"]["expected"],
        "paths=" + ",".join(non_s4_paths) + "; doc_lines=%d; unexpected=%s" % (doc_lines, ",".join(bad) or "none"),
        "SAME" if v2_ok else "MISMATCH")

    # ---------- V6 part 1: tags and main-repo ref
    t1_type = git(["cat-file", "-t", TAG1])
    t2_type = git(["cat-file", "-t", TAG2])
    t1_commit = git(["rev-parse", TAG1 + "^{commit}"])
    t2_commit = git(["rev-parse", TAG2 + "^{commit}"])
    ref = git(["rev-parse", "refs/heads/" + BRANCH])
    prod_head = git(["-C", PROD, "rev-parse", "HEAD"])
    v6_ok = (t1_type == "tag" and t2_type == "tag" and t1_commit == EXP_TAG1_COMMIT
             and t2_commit == EXP_TAG2_COMMIT and ref == prod_head)
    rec.update({"TAG1_TYPE": t1_type, "TAG1_COMMIT": t1_commit, "TAG2_TYPE": t2_type,
                "TAG2_COMMIT": t2_commit, "MAIN_REF": ref, "PROD_HEAD": prod_head})
    add("V6", "annotated tags and main-repo product branch ref",
        prereg["V6"]["expected"],
        "tag1=%s->%s tag2=%s->%s ref=%s prod_head=%s" % (t1_type, t1_commit[:7], t2_type, t2_commit[:7],
                                                         ref[:7], prod_head[:7]),
        "SAME" if v6_ok else "MISMATCH")

    # ---------- fresh clone of the product branch
    if not os.path.isdir(VCLONE):
        p = sh(["git", "clone", "--branch", BRANCH, REPO, VCLONE], cwd=EV)
        open(os.path.join(LOGS, "clone_verifyclone.log"), "w", encoding="utf-8").write(
            ("%% $ git clone --branch %s REPO %s\n# rc=%d\n" % (BRANCH, VCLONE, p.returncode))
            + p.stdout + NL + p.stderr)
        if p.returncode != 0:
            raise SystemExit("HARD_STOP verify clone failed")
    clone_head = git(["-C", VCLONE, "rev-parse", "HEAD"])
    clone_s4 = git(["-C", VCLONE, "rev-parse", "HEAD:S4"])
    rec["VCLONE_HEAD"] = clone_head
    rec["VCLONE_HEAD_S4"] = clone_s4
    if clone_head != prod_head or clone_s4 != EXP_S4:
        add("V1", "fresh clone HEAD", prod_head, clone_head + " S4=" + clone_s4, "MISMATCH")

    # ---------- V5: build with the REL-R1 commands, then hash the artifacts (record only)
    b1 = run_step("build_lua", ["make", "-j16", "build/S4"], VCLONE, "build_lua.log")
    b2 = run_step("build_pyext", ["make", "S4_pyext", "PYTHON=python3"], VCLONE, "build_pyext.log")
    so = [f for f in os.listdir(VCLONE) if f.startswith("S4.") and f.endswith(".so")]
    art = {}
    for name, rel in (("build/S4", "build/S4"), ("build/libS4.a", "build/libS4.a")):
        p = os.path.join(VCLONE, rel)
        art[name] = sha_f(p) if os.path.isfile(p) else "MISSING"
    rec.update({"V5_BUILD_S4_SHA256": art["build/S4"], "V5_LIBS4_SHA256": art["build/libS4.a"],
                "V5_PYEXT": ",".join(sorted(so)), "V5_BUILD_RC": b1["rc"] + "/" + b2["rc"]})
    rel_r1 = {"build/S4": REL_R1_S4_BIN, "build/libS4.a": REL_R1_LIBS4}
    v5 = []
    for name in ("build/S4", "build/libS4.a"):
        v5.append("%s=%s" % (name, "SAME" if art[name] == rel_r1[name] else "DIFFERENT"))
    add("V5", "build artifact sha256 vs REL-R1 F4 (record only)", prereg["V5"]["expected"],
        "; ".join(v5) + "; build_rc=" + b1["rc"] + "/" + b2["rc"], "RECORDED")

    # ---------- V3: make test
    rc_path = os.path.join(WORK, "maketest.done")
    mt = run_step("maketest", MAKETEST_PYTHON, VCLONE, "maketest.log")
    units, recon = parse_maketest(mt["log"])
    test_units = {u: st for u, (st, stage) in units.items() if stage in UNIT_STAGES}
    all_units = set(units)
    fails = sorted(u for u, (st, _s) in units.items() if st in FAIL_STATUS)
    exp = rel_r1_f4_units()
    missing = sorted(exp - all_units)
    extra = sorted(all_units - exp)
    recon_ok = all(r["ok"] for r in recon.values())
    v3_ok = (mt["rc"] == "0" and not fails and not missing and not extra and recon_ok
             and len(all_units) == len(exp))
    rec.update({"V3_RC": mt["rc"], "V3_UNIT_COUNT": len(all_units), "V3_EXPECTED_UNITS": len(exp),
                "V3_FAILING": ",".join(fails[:5]) if fails else "none",
                "V3_MISSING": ",".join(missing[:5]) if missing else "none",
                "V3_EXTRA": ",".join(extra[:5]) if extra else "none",
                "V3_RECON_OK": recon_ok})
    add("V3", "make test in a fresh clone of the product branch", prereg["V3"]["expected"],
        "rc=%s units=%d failing=%s missing=%s extra=%s recon=%s"
        % (mt["rc"], len(all_units), ",".join(fails[:3]) or "none", ",".join(missing[:3]) or "none",
           ",".join(extra[:3]) or "none", recon_ok),
        "SAME" if v3_ok else "MISMATCH")

    # ---------- V4: runtests.sh (3 independent references)
    rt = run_step("runtests", ["./runtests.sh"], os.path.join(VCLONE, "testing"), "runtests.log")
    text = open(rt["log"], encoding="utf-8", errors="replace").read()
    ran = len(re.findall(r"^Running ", text, re.M))
    passed = "Lua regression tests PASSED." in text
    v4_ok = rt["rc"] == "0" and passed and ran == 3
    rec.update({"V4_RC": rt["rc"], "V4_CASES": ran, "V4_PASSED_LINE": passed})
    add("V4", "testing/runtests.sh independent references", prereg["V4"]["expected"],
        "rc=%s cases=%d passed_line=%s" % (rt["rc"], ran, passed), "SAME" if v4_ok else "MISMATCH")

    # ---------- write V table
    out = os.path.join(EV, "V_RELR2.tsv")
    lines = ["# V_RELR2.tsv -- REL-R2 product-branch verification V1-V6 (task brief section 4)",
             "# expected values are copied from PREREG_RELR2.tsv (by column name) where they are typed there;",
             "# V5 is record-only.  Generated " + datetime.datetime.now(datetime.timezone.utc)
             .strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(["test_id", "item", "expected", "actual", "result"])]
    for r in results:
        lines.append(TAB.join([r["test_id"], r["item"], r["expected"], r["actual"], r["result"]]))
    lines.append("")
    lines.append("# records")
    lines.append(TAB.join(["key", "value"]))
    for k in sorted(rec):
        lines.append(TAB.join([k, str(rec[k])]))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for r in results:
        print("%-4s %-10s %s" % (r["test_id"], r["result"], r["actual"][:160]))
    print("WROTE", os.path.relpath(out, REPO))
    bad = [r for r in results if r["result"] == "MISMATCH"]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
