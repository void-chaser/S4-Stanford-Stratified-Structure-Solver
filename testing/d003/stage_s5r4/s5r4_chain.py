#!/usr/bin/env python3
# s5r4_chain.py -- the S5R4 formal chain (task brief section 10). One invocation runs the whole POST_I
# sequence and finally the end gate, each step as its own safe_run-logged subprocess, so the frozen call
# counts in the end gate are exact. The same code is used for the staging shakedown rehearsal (U381) by
# overriding --ev-root/--p05-root/--stage-repo; the rehearsal writes nothing to the formal paths.
# Order: rejudge v2 -> final STATE -> readiness (after STATE, U382) -> R3 gate recheck (measured against the
# final R4 artifacts) -> acceptance map -> sign-off draft v2 -> registry patch -> report -> report_check ->
# registry completion -> events -> sha_sums -> end gate.
# usage: s5r4_chain.py formal [--ev-root DIR] [--p05-root DIR] [--stage-repo DIR]
import os, sys, shutil, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
NL = chr(10)
TAB = chr(9)
STEPS = [
    ("rejudge_s5r4.py", ["formal"]),
    ("s5r4_state.py", ["formal"]),
    ("s5r4_readiness.py", ["formal"]),
    ("s5r4_r3recheck.py", ["formal"]),
    ("s5r4_acceptance.py", ["formal"]),
    ("s5r4_signoff.py", ["formal"]),
    ("s5r4_apply_patch.py", ["formal"]),
    ("s5r4_report.py", ["formal"]),
    ("s5r4_report_check.py", ["formal"]),
    ("s5r4_registry.py", ["formal"]),
    ("s5r4_events.py", ["formal"]),
    ("s5r4_sha_sums.py", ["formal"]),
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_chain.py formal [--ev-root DIR] [--p05-root DIR] [--stage-repo DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    STAGE = arg("--stage-repo", REPO)
    staging = os.path.realpath(EV) != os.path.realpath(EV4_REAL) or os.path.realpath(P05) != os.path.realpath(P05_REAL)
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # own log line = anchor of the POST_I window
    logp = os.path.join(EV4_REAL, "safe_run.log")
    ls = open(logp, encoding="utf-8").read().splitlines()
    H = 0
    for i in range(len(ls), 0, -1):
        if "s5r4_chain.py formal" in ls[i - 1]:
            H = i
            break
    if H <= 0:
        print("HARD_STOP cannot find own safe_run.log line")
        return 2
    # ---------- staging setup (never touches the formal paths)
    if staging:
        for d in (EV, P05, STAGE):
            if os.path.isdir(d):
                shutil.rmtree(d)
        os.makedirs(EV)
        for f in sorted(os.listdir(EV4_REAL)):
            if f in ("safe_run.log", "SHA256SUMS.txt", "gate", "tmp", "shakedown"):
                continue
            src = os.path.join(EV4_REAL, f)
            dst = os.path.join(EV, f)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copyfile(src, dst)
        os.makedirs(P05, exist_ok=True)
        for f in sorted(os.listdir(P05_REAL)):
            if f == "evidence":
                continue
            src = os.path.join(P05_REAL, f)
            dst = os.path.join(P05, f)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copyfile(src, dst)
        os.makedirs(STAGE, exist_ok=True)
        for f in ("testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md"):
            dst = os.path.join(STAGE, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(REPO, f), dst)
        print("STAGING_EV_ROOT=" + EV)
        print("STAGING_P05_ROOT=" + P05)
        print("STAGING_REPO_ROOT=" + STAGE)
    # ---------- chain marker (before the steps, so it is inside the sha_sums manifest)
    marker = os.path.join(EV, "FORMAL_CHAIN_RAN.txt")
    open(marker, "w", encoding="utf-8").write(NL.join([
        "# FORMAL_CHAIN_RAN.txt -- written by s5r4_chain.py formal at the start of the chain",
        "LOG_LINE=%d" % H, "UTC=%s" % utc, "MODE=formal", "STAGING=%s" % ("yes" if staging else "no"),
        "EV_ROOT=%s" % os.path.relpath(EV, REPO), "P05_ROOT=%s" % os.path.relpath(P05, REPO)]) + NL)
    common = ["--ev-root", EV, "--p05-root", P05, "--stage-repo", STAGE]
    def run(cmd):
        p = subprocess.run(["sh", "testing/d003/safe_run.sh", "p05-s5r4", "--"] + cmd, cwd=REPO,
                           text=True, capture_output=True)
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        return p.returncode
    n = 0
    for script, args in STEPS:
        cmd = ["python3", "-I", "-B", "testing/d003/stage_s5r4/" + script] + args + common
        if script == "rejudge_s5r4.py":
            cmd += ["--ev3-root", EV3, "--out", os.path.join(EV, "REJUDGE_S5R4.tsv")]
        if script in ("s5r4_r3recheck.py", "s5r4_apply_patch.py", "s5r4_report.py",
                      "s5r4_report_check.py", "s5r4_registry.py"):
            cmd += ["--ev3-root", EV3]
        rc = run(cmd)
        n += 1
        print("STEP %d %s rc=%d" % (n, script, rc))
        if rc != 0:
            print("HARD_STOP step %s rc=%d (no end gate run)" % (script, rc))
            return 3
    # ---------- shakedown rehearsal record (read by the end gate)
    if staging:
        rec = os.path.join(EV4_REAL, "shakedown/SHAKEDOWN_REHEARSAL.txt")
        os.makedirs(os.path.dirname(rec), exist_ok=True)
        open(rec, "w", encoding="utf-8").write(NL.join([
            "# SHAKEDOWN_REHEARSAL.txt -- full staging rehearsal of the S5R4 POST_I chain (U381)",
            "UTC=%s" % utc, "STAGING_EV_ROOT=%s" % os.path.relpath(EV, REPO),
            "STAGING_P05_ROOT=%s" % os.path.relpath(P05, REPO), "POST_I_FROM=%d" % H,
            "STAGED_STEPS=%d" % n, "MODE=formal-staging"]) + NL)
    gate_out = (os.path.join(EV4_REAL, "shakedown/gate/GATE_S5R4_end.txt") if staging
                else os.path.join(EV, "gate/GATE_S5R4_end.txt"))
    os.makedirs(os.path.dirname(gate_out), exist_ok=True)
    gcmd = ["sh", "testing/d003/stage_s5r4/gate_s5r4.sh", "end", "--post-i-from", str(H),
            "--ev-root", EV, "--ev3-root", EV3, "--p05-root", P05, "--stage-repo", STAGE, "--out", gate_out]
    if staging:
        gcmd += ["--commit-i", "HEAD"]
    rc = run(gcmd)
    txt = open(gate_out, encoding="utf-8").read()
    import re
    mf = re.search(r"FAILS=(\d+)", txt)
    mc = re.search(r"CHECK_CRASHED=(\d+)", txt)
    print("GATE_OUT=%s FAILS=%s CHECK_CRASHED=%s" % (os.path.relpath(gate_out, REPO),
                                                    mf.group(1) if mf else "?", mc.group(1) if mc else "?"))
    if os.path.join(EV4_REAL, "shakedown") in gate_out:
        print("SHAKEDOWN_%s" % ("PASS" if mf and mf.group(1) == "0" and mc and mc.group(1) == "0" else "FAIL"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
