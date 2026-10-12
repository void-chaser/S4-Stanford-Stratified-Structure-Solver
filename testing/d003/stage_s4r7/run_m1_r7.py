#!/usr/bin/env python3
"""P05-S4 R7 M1 runner (new file).  Runs the 108 M1 pre-registered points, one pass per call (no gdb).

Usage (through safe_run; the pass number and run label are arguments; each output file must not exist):
  python3 -I -B testing/d003/stage_s4r7/run_m1_r7.py PREREG EVDIR PASS RUN_LABEL
Example: ... PREREG EVDIR 1 run2   -> RESULTS_R7_M1_pass1_run2.tsv
Judgement: judge_d003.classify (imported, not modified), inj_call = 1.  Per point: one run, env FMM_MODE, S4FMM_NG,
S4FMM_INJECT (for injected points).  Control rows (request "none") run with no S4FMM_INJECT.
Columns: point_id, group, tree, mode, NG, M, request, expected, first_expected_class, expected_win1_rc, rc, rc1, rc2, hit,
         signal, class, verdict_vs_expected, win1_rc, window_mallocs_seen, notes
win1_rc = the value on the "R6D_WIN_CLOSE k=1 ... rc=<n>" line of the first window (the window of the first call).
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402  (imported, not modified)

EV_REL = "checkpoints/p05/evidence/p05-s4r7"
GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 600
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_WIN_CLOSE1 = re.compile(r"^S4FMM R6D_WIN_CLOSE k=1 .* rc=(-?\d+)\s*$", re.M)
RE_WIN_MALLOC = re.compile(r"^S4FMM R6D_WIN_MALLOC", re.M)

# driver per tree and point family.  The window (r6dnv1) driver is used for RNV1 points; the tri lattice driver for tri points.
DRIVER = {
    ("F", "rnv1"): os.path.join(EV_REL, "drivers_r7", "r6dnv1-F-plain", "driver"),
    ("F2", "rnv1"): os.path.join(EV_REL, "drivers_r7", "r6dnv1-F2-plain", "driver"),
    ("F", "tri"): os.path.join(EV_REL, "drivers_r7", "tri-F-dbg", "driver"),
    ("F2", "tri"): os.path.join(EV_REL, "drivers_r7", "tri-F2-dbg", "driver"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def table(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def clean_env(extra):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(extra)
    return env


def run(cmd, env):
    rc, out = None, b""
    try:
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, (exc.stdout or b"")
    if rc is not None and rc < 0:
        rc = 128 - rc
    return rc, out.decode("utf-8", errors="replace")


def facts(text):
    m1, m2 = RE_RC1.search(text), RE_RC2.search(text)
    hc = RE_HITC.search(text)
    hit = int(hc.group(1)) if hc else len(re.findall(r"^S4FMM HIT ", text, re.M))
    mw = RE_WIN_CLOSE1.search(text)
    return {
        "rc1": int(m1.group(1)) if m1 else None,
        "rc2": int(m2.group(1)) if m2 else None,
        "hit": hit,
        "win1": mw.group(1) if mw else "-",
        "nmalloc": len(RE_WIN_MALLOC.findall(text)),
    }


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: run_m1_r7.py PREREG EVDIR PASS RUN_LABEL")
    prereg, ev, pas, tag = argv[1:5]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if not re.match(r"^[a-z0-9]+$", tag):
        raise SystemExit("REFUSED: run label must be [a-z0-9]+")
    out_tsv = os.path.join(ev, "RESULTS_R7_M1_pass%s_%s.tsv" % (pas, tag))
    if os.path.exists(out_tsv):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out_tsv)
    want = open(os.path.join(ev, "REGISTRY_S4_PRE_R7_M1.sha256"), encoding="utf-8").read().split()[0]
    if sha256_file(prereg) != want:
        raise SystemExit("REFUSED: pre-registration sha256 differs from the recorded value")
    drv_sha = {}
    for k, rel in DRIVER.items():
        p = os.path.join(REPO, rel)
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver %s not executable: %s" % (k, rel))
        drv_sha[k] = sha256_file(p)
    pts = table(prereg)
    if len(pts) != 108:
        raise SystemExit("REFUSED: pre-registration rows %d != 108" % len(pts))

    rows = []
    for d in pts:
        tree, mode, ng, m, req = d["tree"], d["mode"], d["NG"], d["M"], d["request"]
        if d["group"] == "control":
            family = "rnv1"
            driver = os.path.join(REPO, DRIVER[(tree, family)])
            env = {"FMM_MODE": mode, "S4FMM_NG": ng}
        else:
            family = "tri" if d["point_id"].startswith("M1-42-tri") or d["point_id"].startswith("M1-G8") else "rnv1"
            driver = os.path.join(REPO, DRIVER[(tree, family)])
            env = {"FMM_MODE": mode, "S4FMM_NG": ng, "S4FMM_INJECT": req}
        pdir = os.path.join(ev, "m1_selfcheck", d["point_id"], "pass%s_%s" % (pas, tag))
        rc, txt = run([driver] + GRID, clean_env(env))
        os.makedirs(pdir, exist_ok=True)
        with open(os.path.join(pdir, "nogdb.out"), "w", encoding="utf-8") as fh:
            fh.write(txt)
        f = facts(txt)
        if d["group"] == "control":
            # a control is judged against the rc values read from run1 (encoded in expected_win1_rc as rc_first=..,rc_retry=..,run_rc=..)
            m_ = re.match(r"rc_first=(-?\d+),rc_retry=(-?\d+),run_rc=(-?\d+)$", d["expected_win1_rc"] or "")
            if m_ is None:
                cls, verdict, reason = "INVALID", "MISMATCH", "control expectation not defined in pre-registration"
            else:
                ok = (str(f["rc1"]) == m_.group(1) and str(f["rc2"]) == m_.group(2) and str(rc) == m_.group(3))
                cls = "CONTROL_OK" if ok else "INVALID"
                verdict = "MATCH" if (ok and d["expected_class"] == "CONTROL_OK") else "MISMATCH"
                reason = "no injection; observed rc1=%s rc2=%s run_rc=%s vs expected %s" % (f["rc1"], f["rc2"], rc, d["expected_win1_rc"])
        else:
            cls, label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=False, real=True, inj_call=1)
            verdict = "MATCH" if cls == d["expected_class"] else "MISMATCH"
        rows.append([d["point_id"], d["group"], tree, mode, ng, m, req, d["expected_class"], d["first_expected_class"],
                     d["expected_win1_rc"], str(rc), str(f["rc1"]), str(f["rc2"]), str(f["hit"]),
                     "" if rc is None or rc < 128 else str(rc - 128), cls, verdict, f["win1"], str(f["nmalloc"]),
                     reason])

    cols = ["point_id", "group", "tree", "mode", "NG", "M", "request", "expected_class", "first_expected_class",
            "expected_win1_rc", "rc", "rc1", "rc2", "hit", "signal", "class", "verdict_vs_expected", "win1_rc",
            "window_mallocs_seen", "notes"]
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R7 M1, pass %s run %s (judge: judge_d003.classify, imported).  Written by run_m1_r7.py.\n"
                 % (os.path.basename(out_tsv), pas, tag))
        fh.write("# driver sha256: " + "; ".join("%s/%s=%s" % (k[0], k[1], v) for k, v in sorted(drv_sha.items())) + "\n")
        fh.write("# prereg sha256: " + want + "\n")
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    mism = sum(1 for r in rows if r[16] == "MISMATCH")
    print("pass=%s run=%s rows=%d mismatches=%d -> %s" % (pas, tag, len(rows), mism, out_tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
