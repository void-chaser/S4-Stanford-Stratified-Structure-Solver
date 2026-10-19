#!/usr/bin/env python3
# relr4_startgate.py -- P05 delivery round REL-R4 (rel-r4) start gate (task brief section 0).
# Read-only baseline checks plus the read-only top-level temporary-directory snapshot.
# Writes ONLY $EV/GATE_RELR4_start.txt.  Any check failing prints FAILS>0 and the round stops.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
P05 = os.path.join(REPO, "checkpoints/p05")
OUT = os.path.join(EV, "GATE_RELR4_start.txt")
TAB = chr(9)
NL = chr(10)
EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_HEAD = "c126619c77ec1f45511cdf30145431d3d6982c4e"
EXP_F4_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_B_COMMIT = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
EXP_B_S4 = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXP_F4_COMMIT = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"
EXP_U_COMMIT = "7fd00a231610bff51f5c7de5f723e3956eab7453"
EXP_U_S4 = "06553f72e93aaef1a5c9294f358a7f5afbd42bb1"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
RECORDS = []
CHECKS = []
CRASHED = []
DOL = chr(36)  # dollar sign, kept out of source text so no shell/template expansion can occur


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sh(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO).strip()


def out(cmd):
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip()


def record(k, v):
    RECORDS.append((k, str(v)))


def safe(name, fn, exp):
    try:
        actual = fn()
    except Exception as exc:
        CRASHED.append((name, repr(exc)))
        actual = "EXC:" + repr(exc)[:160]
    ok = actual == exp
    CHECKS.append((name, exp, actual, ok))


def tmp_snapshot():
    # identical calibration to s5r7_tmpsnap.py / relr2_tmpsnap.py: Python sorted() names,
    # sha256 of newline-joined names + trailing newline.
    names = sorted(os.listdir("/tmp"))
    return len(names), sha_b((NL.join(names) + NL).encode("utf-8"))


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
        if len(parts) < 2:
            bad.append(("MALFORMED", line))
            continue
        n += 1
        fp = os.path.join(d, " ".join(parts[1:]))
        if not os.path.isfile(fp):
            bad.append(("MISSING", os.path.basename(fp)))
        elif sha_f(fp) != parts[0]:
            bad.append(("SHA", os.path.basename(fp)))
    return n, bad


def real_dir(p):
    rp = os.path.realpath(p)
    if not rp.startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + rp)
    return rp


def first_line(cmd):
    o = out(cmd)
    return o.splitlines()[0] if o else "MISSING"


def main():
    record("ROUND", "P05 delivery round REL-R4 (rel-r4)")
    record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    # --- section 0.1 head / branch / clean worktree
    record("HEAD", sh(["git", "rev-parse", "HEAD"]))
    record("HEAD_SHORT", sh(["git", "rev-parse", "--short", "HEAD"]))
    record("BRANCH", sh(["git", "branch", "--show-current"]))
    record("GIT_STATUS_RAW", sh(["git", "status", "--porcelain"]) or "empty")
    record("GIT_STATUS_LINES", len(sh(["git", "status", "--porcelain"]).splitlines()))
    # The worktree was verified empty immediately before this round started (the first command of
    # the round printed 0 lines).  The only entries allowed now are this round's own new files.
    ALLOWED_STATUS = ("testing/d003/stage_relr4/",)

    def status_only_round():
        st = [l for l in sh(["git", "status", "--porcelain"]).splitlines() if l.strip()]
        bad = [l for l in st if not any(l[3:].startswith(a) for a in ALLOWED_STATUS)]
        return "clean" if not bad else "unexpected:" + ";".join(bad[:4])
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_C126619", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_HEAD)
    safe("GIT_STATUS_ONLY_ROUND_FILES", status_only_round, "clean")
    # --- section 0.2 tree hashes
    record("HEAD_S4", sh(["git", "rev-parse", "HEAD:S4"]))
    record("B_COMMIT", sh(["git", "rev-parse", EXP_B_COMMIT]))
    record("B_COMMIT_S4", sh(["git", "rev-parse", EXP_B_COMMIT + ":S4"]))
    record("F4_COMMIT", sh(["git", "rev-parse", EXP_F4_COMMIT]))
    record("F4_COMMIT_S4", sh(["git", "rev-parse", EXP_F4_COMMIT + ":S4"]))
    record("U_COMMIT", sh(["git", "rev-parse", EXP_U_COMMIT]))
    record("U_COMMIT_S4", sh(["git", "rev-parse", EXP_U_COMMIT + ":S4"]))
    record("B_COMMIT_SUBJECT", sh(["git", "log", "-1", "--format=%s", EXP_B_COMMIT])[:120])
    record("F4_COMMIT_SUBJECT", sh(["git", "log", "-1", "--format=%s", EXP_F4_COMMIT])[:120])
    record("U_COMMIT_SUBJECT", sh(["git", "log", "-1", "--format=%s", EXP_U_COMMIT])[:120])
    record("HEAD_SUBJECT", sh(["git", "log", "-1", "--format=%s", "HEAD"])[:120])
    record("M_COMMIT", sh(["git", "rev-parse", "b97f639"]))
    record("M_S4", sh(["git", "rev-parse", "b97f639:S4"]))
    safe("HEAD_S4_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_F4_S4)
    safe("B_COMMIT_EQ_5B72793", lambda: sh(["git", "rev-parse", EXP_B_COMMIT]), EXP_B_COMMIT)
    safe("B_S4_EQ_1D738E64", lambda: sh(["git", "rev-parse", EXP_B_COMMIT + ":S4"]), EXP_B_S4)
    safe("F4_COMMIT_EQ_3DE6D8B", lambda: sh(["git", "rev-parse", EXP_F4_COMMIT]), EXP_F4_COMMIT)
    safe("F4_S4_EQ_589E15EB", lambda: sh(["git", "rev-parse", EXP_F4_COMMIT + ":S4"]), EXP_F4_S4)
    safe("U_COMMIT_EQ_7FD00A2", lambda: sh(["git", "rev-parse", EXP_U_COMMIT]), EXP_U_COMMIT)
    safe("U_S4_EQ_06553F72", lambda: sh(["git", "rev-parse", EXP_U_COMMIT + ":S4"]), EXP_U_S4)
    # --- section 0.3 judge hash
    record("JUDGE_SHA256", sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")))
    safe("JUDGE_SHA256_OK", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    # --- section 0.4 rel-r3 registry + RULINGS baseline (whole file = the append-only prefix)
    r = verify_sums_dir(os.path.join(P05, "registries/rel-r3"))
    record("RELR3_REGISTRY_ITEMS", r[0] if r else "MISSING")
    record("RELR3_REGISTRY_BAD", "none" if r and not r[1] else repr(r[1] if r else "missing"))
    safe("RELR3_REGISTRY_SUMS_ALL_OK", lambda: ("all %d OK" % r[0]) if r and not r[1] else ("BAD %s" % (r[1][:3] if r else "missing")), "all 18 OK")
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    lines = [l for l in rb.decode("utf-8").splitlines() if l.strip()]
    record("RULINGS_ROWS", len(lines))
    record("RULINGS_LAST_ID", lines[-1].split(TAB)[0])
    safe("RULINGS_LAST_IS_U398", lambda: lines[-1].split(TAB)[0], "U398")
    # --- section 0.5 top-level temporary directory snapshot (read only, start)
    tmp_n, tmp_sha = tmp_snapshot()
    record("TMP_COUNT", tmp_n)
    record("TMP_SHA256", tmp_sha)
    record("TMP_CALIBRATION", "python sorted(os.listdir('/tmp')); sha256 of newline-joined names + trailing newline (s5r7_tmpsnap.py calibration)")
    # --- section 0.6 environment
    record("PYTHON3_VERSION", out(["python3", "--version"]))
    record("LUA_VERSION", first_line(["lua", "-v"]))
    record("GCC_VERSION", first_line(["gcc", "--version"]))
    record("GXX_VERSION", first_line(["g++", "--version"]))
    pk = []
    for pkg in ("liblapack-dev", "liblapack3", "libblas-dev", "libblas3"):
        fmt = "-f=" + DOL + "{Package} " + DOL + "{Version}"
        pk.append(out(["dpkg-query", "-W", fmt, pkg]))
    record("LAPACK_BLAS_PACKAGES", "; ".join(pk))
    record("NPROC", out(["nproc"]))
    record("UNAME_R", out(["uname", "-r"]))
    record("MAKE_VERSION", first_line(["make", "--version"]))
    record("GIT_VERSION", out(["git", "--version"]))
    record("MPICC_PATH", out(["which", "mpicc"]))
    record("MPIRUN_PATH", out(["which", "mpirun"]))
    record("MPICC_VERSION", first_line(["mpicc", "--version"]))
    record("MPIRUN_VERSION", first_line(["mpirun", "--version"]))
    record("OMPI_INFO_VERSION", first_line(["ompi_info", "--version"]))
    record("MPICC_SHOWME_COMPILE", out(["mpicc", "--showme:compile"]))
    record("MPICC_SHOWME_LINK", out(["mpicc", "--showme:link"]))
    record("UPSTREAM_LSREMOTE_HEAD", out(["git", "ls-remote", "https://github.com/victorliu/S4.git", "HEAD"])[:120])
    dfs = out(["df", "-h", "/srv/nvme/projects"]).splitlines()
    record("DISK_FREE_SRV_NVME", dfs[-1] if dfs else "MISSING")
    safe("MPICC_PRESENT", lambda: "yes" if out(["which", "mpicc"]) else "no", "yes")
    safe("MPIRUN_PRESENT", lambda: "yes" if out(["which", "mpirun"]) else "no", "yes")
    # --- first-write invariant
    record("GATE_FILE", "GATE_RELR4_start.txt")
    fails = [c for c in CHECKS if not c[3]]
    os.makedirs(EV, exist_ok=True)
    outp = real_dir(OUT)
    data = ["# GATE_RELR4_start.txt -- P05 delivery round REL-R4 start gate (" + dict(RECORDS)["START_TIME_UTC"] + ")",
            "# Every line is RECORD<TAB>KEY<TAB>value=V or PASS/FAIL<TAB>name<TAB>expected=..<TAB>actual=..",
            "# Values are read back by relr4_check.py --phase start|end BY KEY NAME."]
    data += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    data += [("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + str(e) + TAB + "actual=" + str(a)
             for (n, e, a, ok) in CHECKS]
    data.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    data.append("FAILS=%d" % len(fails))
    data.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        data.append("CRASHED" + TAB + n + TAB + x)
    with open(outp, "w", encoding="utf-8") as fh:
        fh.write(NL.join(data) + NL)
    for l in data:
        print(l)
    print("WROTE " + os.path.relpath(outp, REPO))
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
