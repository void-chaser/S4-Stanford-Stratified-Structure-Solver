#!/usr/bin/env python3
# relr3_verify.py -- P05 delivery round REL-R3: R6 (fresh remote clone) and R7 (make test in that clone)
# (task brief section 5 step 5).  Everything runs inside $EV/remoteclone; the main repository is only
# read.  R6: git clone --branch p05/d003-fft-error-propagation <origin URL> $EV/remoteclone, then
# HEAD = 8e4c014 and HEAD:S4 = 589e15eb.  R7: make test PYTHON=python3 with stderr merged into stdout
# before parsing; unit set equal to REL-R2 V3 (MAKETEST_UNITS_RELR1.tsv column F4_p1), zero failures.
import os, re, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
CLONE = os.path.join(EV, "remoteclone")
LOGS = os.path.join(EV, "logs")
OUT = os.path.join(EV, "REMOTE_CLONE_RELR3.tsv")
TAB = chr(9)
NL = chr(10)
REMOTE_URL = "https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git"
BRANCH = "p05/d003-fft-error-propagation"
EXP_HEAD = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
UNITS_R1 = os.path.join(REPO, "checkpoints/p05/registries/rel-r1/MAKETEST_UNITS_RELR1.tsv")
MAKETEST = ["make", "test", "PYTHON=python3"]
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
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def git(args, cwd=REPO):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=300)
    return p.stdout.strip(), p.returncode


def read_tsv_by_name(path):
    rows = []
    header = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if header is None:
            header = f
            continue
        if len(f) == len(header):
            rows.append(dict(zip(header, f)))
    return rows


def rel_r2_v3_units():
    """REL-R2 V3 unit set = REL-R1 T1 F4 unit set (column F4_p1 != ABSENT)."""
    return set(r["unit"] for r in read_tsv_by_name(UNITS_R1) if r.get("F4_p1") != "ABSENT" and r["unit"])


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


def run_merged(argv, cwd, logname, timeout=TIMEOUT):
    os.makedirs(LOGS, exist_ok=True)
    t0 = datetime.datetime.now(datetime.timezone.utc)
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=timeout)
    data = ("% $ " + " ".join(argv) + NL + "# rc=" + str(p.returncode) + " utc="
            + t0.strftime("%Y-%m-%dT%H:%M:%SZ") + NL + p.stdout)
    open(os.path.join(LOGS, logname), "w", encoding="utf-8").write(data)
    return p.returncode, os.path.join(LOGS, logname)


def main():
    results = []
    rec = {}
    os.makedirs(EV, exist_ok=True)
    if os.path.exists(CLONE):
        print("HARD_STOP " + os.path.relpath(CLONE, REPO) + " already exists; refusing to reuse a clone")
        return 2
    rc, log = run_merged(["git", "clone", "--branch", BRANCH, REMOTE_URL, CLONE], EV, "clone_remote.log",
                         timeout=1200)
    rec["R6_CLONE_RC"] = str(rc)
    if rc != 0:
        write_table(results, rec)
        print("HARD_STOP remote clone failed rc=%d" % rc)
        return 2
    head, _ = git(["rev-parse", "HEAD"], cwd=CLONE)
    s4, _ = git(["rev-parse", "HEAD:S4"], cwd=CLONE)
    rec["R6_HEAD"] = head
    rec["R6_HEAD_S4"] = s4
    r6_ok = head == EXP_HEAD and s4 == EXP_S4
    results.append({"test_id": "R6", "item": "fresh remote clone of the product branch",
                    "expected": "HEAD=" + EXP_HEAD + "; HEAD:S4=" + EXP_S4,
                    "actual": "HEAD=" + head + "; HEAD:S4=" + s4,
                    "result": "SAME" if r6_ok else "MISMATCH"})
    print("R6 HEAD=%s S4=%s %s" % (head, s4, "SAME" if r6_ok else "MISMATCH"))
    if not r6_ok:
        write_table(results, rec)
        return 2

    mt_rc, mt_log = run_merged(MAKETEST, CLONE, "maketest_remote.log")
    rec["R7_RC"] = str(mt_rc)
    units, recon = parse_maketest(mt_log)
    all_units = set(units)
    fails = sorted(u for u, (st, _s) in units.items() if st in FAIL_STATUS)
    exp = rel_r2_v3_units()
    missing = sorted(exp - all_units)
    extra = sorted(all_units - exp)
    recon_ok = all(r["ok"] for r in recon.values())
    rec.update({"R7_UNIT_COUNT": str(len(all_units)), "R7_EXPECTED_UNITS": str(len(exp)),
                "R7_FAILING": ",".join(fails[:5]) if fails else "none",
                "R7_MISSING": ",".join(missing[:5]) if missing else "none",
                "R7_EXTRA": ",".join(extra[:5]) if extra else "none",
                "R7_RECON_OK": str(recon_ok), "R7_LOG": os.path.relpath(mt_log, REPO)})
    r7_ok = (mt_rc == 0 and not fails and not missing and not extra and recon_ok
             and len(all_units) == len(exp))
    results.append({"test_id": "R7", "item": "make test in the R6 clone",
                    "expected": "rc=0; units=%d; failing=none; missing=none; extra=none" % len(exp),
                    "actual": "rc=%d units=%d failing=%s missing=%s extra=%s recon=%s"
                              % (mt_rc, len(all_units), ",".join(fails[:3]) or "none",
                                 ",".join(missing[:3]) or "none", ",".join(extra[:3]) or "none", recon_ok),
                    "result": "SAME" if r7_ok else "MISMATCH"})
    write_table(results, rec)
    print("R7 rc=%d units=%d failing=%s %s" % (mt_rc, len(all_units), ",".join(fails[:3]) or "none",
                                               "SAME" if r7_ok else "MISMATCH"))
    return 0 if r7_ok else 1


def write_table(results, rec):
    lines = ["# REMOTE_CLONE_RELR3.tsv -- R6 remote clone and R7 make test (task brief section 4 and 5.5)",
             "# make test stderr was merged into stdout before parsing; expected unit set is the REL-R2 V3 set",
             "# (REL-R1 registry MAKETEST_UNITS_RELR1.tsv column F4_p1, 265 units).",
             "# Generated " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(["test_id", "item", "expected", "actual", "result"])]
    for r in results:
        lines.append(TAB.join([r["test_id"], r["item"], r["expected"], r["actual"], r["result"]]))
    lines.append("")
    lines.append("# records")
    lines.append(TAB.join(["key", "value"]))
    for k in sorted(rec):
        lines.append(TAB.join([k, str(rec[k])]))
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("WROTE " + os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    sys.exit(main())
