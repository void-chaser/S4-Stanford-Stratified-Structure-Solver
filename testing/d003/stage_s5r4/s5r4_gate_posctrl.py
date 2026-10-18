#!/usr/bin/env python3
# s5r4_gate_posctrl.py -- positive control of the five fixed end-gate checks and of the git-status parser
# (task brief section 6): every case writes a tampered copy ON DISK and invokes the FORMAL gate script in
# single-check mode; a clean copy must PASS and the tampered copy must FAIL. Nothing here lowers a check.
# usage: s5r4_gate_posctrl.py posctrl [--ev-root DIR] [--p05-root DIR] [--ev3-root DIR]
import os, sys, shutil, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
GATE = os.path.join(REPO, "testing/d003/stage_s5r4/gate_check_s5r4.py")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "posctrl":
        print("usage: s5r4_gate_posctrl.py posctrl [--ev-root DIR] [--p05-root DIR] [--ev3-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    base = os.path.join(EV, "posctrl/gate")
    if os.path.isdir(base):
        shutil.rmtree(base)
    os.makedirs(base)
    logp = os.path.join(EV4_REAL, "safe_run.log")
    ls = open(logp, encoding="utf-8").read().splitlines()
    anchor = 0
    for i in range(len(ls), 0, -1):
        if "s5r4_gate_posctrl.py posctrl" in ls[i - 1]:
            anchor = i
            break
    if anchor <= 0:
        print("HARD_STOP cannot find own log line")
        return 2
    results = []

    def run_gate(only, out, extra):
        cmd = [sys.executable, "-I", "-B", GATE, "end", "--only", only, "--out", out,
               "--post-i-from", str(anchor), "--commit-i", "HEAD", "--precommit-i"] + extra
        p = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True)
        t = open(out, encoding="utf-8").read() if os.path.isfile(out) else ""
        m = None
        for line in t.splitlines():
            if line.startswith(("PASS" + TAB + only, "FAIL" + TAB + only)):
                m = line.split(TAB)[0]
        return (m or "NO_LINE"), (p.stdout + p.stderr)

    def case(name, only, clean_extra, tamper_extra):
        outc = os.path.join(base, name + "_clean.txt")
        outt = os.path.join(base, name + "_tamper.txt")
        rc, _ = run_gate(only, outc, clean_extra)
        rt, txt = run_gate(only, outt, tamper_extra)
        ok = (rc == "PASS" and rt == "FAIL")
        results.append((name, ok, rc, rt))
        print(("PASS" if ok else "FAIL") + TAB + "posctrl_" + name + TAB + "clean=%s tampered=%s" % (rc, rt))
        return ok, txt

    # ---- FIX2: FROZEN call counts (synthetic frozen list in a staged ev root; the posctrl line itself is the
    # only POST_I line in the window and carries the 'posctrl' mode token)
    def frozen_root(d, expected):
        os.makedirs(d, exist_ok=True)
        shutil.copyfile(os.path.join(EV, "GATE_S5R4_start.txt"), os.path.join(d, "GATE_S5R4_start.txt"))
        p = os.path.join(REPO, "testing/d003/stage_s5r4/s5r4_gate_posctrl.py")
        open(os.path.join(d, "FROZEN_SCRIPTS_S5R4.tsv"), "w", encoding="utf-8").write(
            "path" + TAB + "sha256" + TAB + "expected_calls" + TAB + "mode" + NL +
            TAB.join(["testing/d003/stage_s5r4/s5r4_gate_posctrl.py", sha_f(p), str(expected), "posctrl"]) + NL)
        return d
    fc = frozen_root(os.path.join(base, "ev_frozen_clean"), 1)
    ft = frozen_root(os.path.join(base, "ev_frozen_tamper"), 2)
    case("FROZEN_POST_I_CALL_COUNTS_MATCH", "FROZEN_POST_I_CALL_COUNTS_MATCH",
         ["--ev-root", fc], ["--ev-root", ft])
    # ---- FIX1: RULINGS 5 fields (p05 root with a 3-field data line)
    tc = os.path.join(base, "p05_rulings_tamper")
    os.makedirs(os.path.join(tc, "registries"))
    lines = open(os.path.join(P05, "registries/RULINGS.tsv"), encoding="utf-8").read().splitlines()
    lines.append("U999" + TAB + "x" + TAB + "y")     # 3 fields -> must FAIL FIX1
    open(os.path.join(tc, "registries/RULINGS.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    case("RULINGS_LINES_5_FIELDS", "RULINGS_LINES_5_FIELDS", ["--p05-root", P05], ["--p05-root", tc])
    # ---- FIX4: D016 verdict rows (a duplicated data row -> 35)
    tc = os.path.join(base, "ev3_d016_tamper")
    os.makedirs(tc)
    v = open(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"), encoding="utf-8").read().splitlines()
    data = [i for i, l in enumerate(v) if l and not l.startswith("#") and not l.startswith("SUMMARY")
            and not l.startswith("point_id")]
    v.insert(data[0], v[data[0]])
    open(os.path.join(tc, "D016_VERDICT_S5R3.tsv"), "w", encoding="utf-8").write(NL.join(v) + NL)
    case("D016_VERDICT_ROWS_34", "D016_VERDICT_ROWS_34", ["--ev3-root", EV3], ["--ev3-root", tc])
    # ---- FIX5: CALIB diff (one non-SAME data row)
    tc = os.path.join(base, "ev3_calib_tamper")
    os.makedirs(tc)
    c = open(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv"), encoding="utf-8").read().splitlines()
    for i, l in enumerate(c):
        if l.startswith("TARGET" + TAB):
            f = l.split(TAB)
            f[4] = "DIFF"
            c[i] = TAB.join(f)
            break
    open(os.path.join(tc, "CALIB_DIFF_S5R3.tsv"), "w", encoding="utf-8").write(NL.join(c) + NL)
    case("CALIB_DIFF_ZERO", "CALIB_DIFF_ZERO", ["--ev3-root", EV3], ["--ev3-root", tc])
    # ---- FIX3: git status parser, two real-format strings + the real status
    sc = os.path.join(base, "status_allowed.txt")
    open(sc, "w", encoding="utf-8").write(NL.join([
        " M checkpoints/p05/STATE.md",
        "?? testing/d003/stage_s5r4/",
        "?? checkpoints/p05/registries/s5r4/"]) + NL)
    st = os.path.join(base, "status_disallowed.txt")
    open(st, "w", encoding="utf-8").write(" M S4/rcwa.cpp" + NL)
    case("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST",
         ["--status-override", sc], ["--status-override", st])
    # the real work-tree status must pass the same check
    rc, _ = run_gate("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", os.path.join(base, "status_real.txt"), [])
    results.append(("MODIFIED_TRACKED_REAL_STATUS", rc == "PASS", rc, "n/a"))
    print(("PASS" if rc == "PASS" else "FAIL") + TAB + "posctrl_MODIFIED_TRACKED_REAL_STATUS" + TAB + "real=%s" % rc)
    ok = all(r[1] for r in results)
    out = os.path.join(EV, "POSCTRL_GATE_S5R4.txt")
    body = ["# POSCTRL_GATE_S5R4.txt -- positive control of the five fixed end-gate checks (U378)",
            "# every tampered copy is on disk under " + os.path.relpath(base, REPO) + "/ and the FORMAL gate script",
            "# was invoked in --only single-check mode; clean copy must PASS, tampered copy must FAIL.",
            "# git status: allowed/disallowed real-format strings plus the real work-tree status."]
    for (name, o, rc, rt) in results:
        body.append("%s: %s (clean=%s tampered=%s)" % (name, "PASS" if o else "FAIL", rc, rt))
    body.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if ok else "FAIL", sum(1 for r in results if r[1]), len(results)))
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("OVERALL_POSITIVE_CONTROL %s %d/%d" % ("PASS" if ok else "FAIL", sum(1 for r in results if r[1]), len(results)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
