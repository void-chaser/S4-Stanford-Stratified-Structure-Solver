#!/usr/bin/env python3
# run_r6d_rnv1.py -- P05-S4 R6d-2 (new file): runner of the RNV1 injection (72 points = F 36 + B 36, two passes).
#
# Inputs: the pre-registration REGISTRY_S4_PRE_R6d_RNV1.tsv (sha256 and UTC in the sidecar files; checked here), the two
# drivers (F and B) with their recorded sha256.  Judgement uses judge_d003.classify (imported, not modified).
# Per point and pass: one run WITHOUT gdb (the judged run) and, for the first point of each (tree, mode) only, one run
# under gdb with the backtrace script r6d_rnv1_callers.gdb-like printing (backtrace of the injected malloc is written).
# Environment: FMM_MODE=<mode>, S4FMM_NG=<NG>, S4FMM_INJECT=rnv1:<M>; other FMM_/S4FMM_ variables removed.
#
# Output (never overwritten; U17): EVDIR/RESULTS_R6d_RNV1_pass<P>.tsv and EVDIR/rnv1/<tree>/<point>/pass<P>/{nogdb.out,gdb.log}
# Columns: point_id, tree, mode, NG, M, request, expected, baseline_rc, rc, rc1, rc2, hit, signal, class, verdict_vs_expected,
#          window_mallocs_seen, windows_seen, notes
#
# Usage: python3 -I -B testing/d003/stage_s4/run_r6d_rnv1.py PREREG EVDIR PASS
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402  (imported, not modified)

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 600
GDB_SCRIPT = os.path.join(HERE, "r6d_rnv1_crash.gdb")  # backtrace at the fatal signal (the callers are in section 4 of RNV1_SOURCE_R6d.md)
DRIVERS = {
    # driver sha256 as relinked after the HIT-protocol line (link v4).  The pre-registration file has no driver column,
    # so its sha256 is unchanged.  The earlier driver hashes (2349fa05..., 93743e5e...) belong to the discarded run 1.
    "F": ("checkpoints/p05/evidence/p05-s4r6d/drivers/r6d-rnv1/driver-r6d-rnv1", "e73ec071ddae575fb28968c475b3a80e247199b9e7af026f0d0f59c06f495f82"),
    "B": ("checkpoints/p05/evidence/p05-s4r6d/drivers/r6d-rnv1-B/driver-r6d-rnv1-B", "ecf00fa6b3c3b1bbd7465b22bb097d07dbc099d46e06b31f7d7d0c9d3588bc9c"),
}
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_WIN_OPEN = re.compile(r"^S4FMM R6D_WIN_OPEN", re.M)
RE_WIN_MALLOC = re.compile(r"^S4FMM R6D_WIN_MALLOC", re.M)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path):
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


def run(cmd, env, log_path):
    rc = None
    out = b""
    try:
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, (exc.stdout or b"")
    if rc is not None and rc < 0:
        rc = 128 - rc
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "wb") as fh:
        fh.write(out)
    return rc, out.decode("utf-8", errors="replace")


def facts(text):
    m1, m2 = RE_RC1.search(text), RE_RC2.search(text)
    hc = RE_HITC.search(text)
    hit = int(hc.group(1)) if hc else len(re.findall(r"^S4FMM HIT ", text, re.M))
    return {
        "rc1": int(m1.group(1)) if m1 else None,
        "rc2": int(m2.group(1)) if m2 else None,
        "hit": hit,
        "win_open": len(RE_WIN_OPEN.findall(text)),
        "win_malloc": len(RE_WIN_MALLOC.findall(text)),
    }


def main(argv):
    if len(argv) not in (4, 5):
        raise SystemExit("usage: run_r6d_rnv1.py PREREG EVDIR PASS [RUN_LABEL]")
    prereg, ev, pas = argv[1:4]
    tag = argv[4] if len(argv) == 5 else ""  # run label, e.g. "run2": keeps earlier result files untouched (U17)
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if tag and not re.match(r"^[a-z0-9]+$", tag):
        raise SystemExit("REFUSED: run label must be [a-z0-9]+")
    out_tsv = os.path.join(ev, "RESULTS_R6d_RNV1_pass%s%s.tsv" % (pas, ("_" + tag) if tag else ""))
    if os.path.exists(out_tsv):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out_tsv)
    pre_sha = sha256_file(prereg)
    with open(os.path.join(ev, "REGISTRY_S4_PRE_R6d_RNV1.sha256"), encoding="utf-8") as fh:
        want = fh.read().split()[0]
    if pre_sha != want:
        raise SystemExit("REFUSED: pre-registration sha256 %s != recorded %s" % (pre_sha, want))
    pts = read_table(prereg)
    if len(pts) != 72:
        raise SystemExit("REFUSED: pre-registration rows %d != 72" % len(pts))
    drv = {}
    for t, (rel, sha) in DRIVERS.items():
        p = os.path.join(REPO, rel)
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver %s not executable" % t)
        if sha256_file(p) != sha:
            raise SystemExit("REFUSED: driver %s sha256 differs from the recorded value" % t)
        drv[t] = p

    rows = []
    gdb_done = set()
    for d in pts:
        t, mode, ng, m = d["tree"], d["mode"], d["NG"], d["M"]
        env = {"FMM_MODE": mode, "S4FMM_NG": ng, "S4FMM_INJECT": d["request"]}
        pdir = os.path.join(ev, "rnv1" + (("_" + tag) if tag else ""), t, d["point_id"], "pass" + pas)
        rc_n, txt_n = run([drv[t]] + GRID, clean_env(env), os.path.join(pdir, "nogdb.out"))
        f = facts(txt_n)
        notes = []
        key = (t, mode)
        if key not in gdb_done:
            gdb_done.add(key)
            env_g = clean_env(env)
            rc_g, txt_g = run(["gdb", "-batch", "-x", GDB_SCRIPT, "--args", drv[t]] + GRID, env_g,
                              os.path.join(pdir, "gdb.log"))
            fg = facts(txt_g)
            notes.append("gdb backtrace written (first point of %s/%s); gdb rc=%s win_malloc=%s" % (t, mode, rc_g, fg["win_malloc"]))
            # gdb exits with its own status (0 after "quit"), not with the driver's signal status.  So the comparison is
            # on the driver facts (rc1, rc2, hit) and on whether gdb also reported the fatal signal ("received signal").
            g_sig = "received signal" in txt_g
            n_sig = rc_n >= 128
            if (g_sig != n_sig) or (fg["rc1"], fg["rc2"], fg["hit"]) != (f["rc1"], f["rc2"], f["hit"]):
                notes.append("GDB_DIVERGENT for this point (gdb rc %s vs %s, facts %s vs %s)" % (rc_g, rc_n, fg, f))
        baseline = d["baseline_rc"]
        cls, label, reason = J.classify(rc_n, f["rc1"], f["rc2"], f["hit"], control=False, real=True, inj_call=1)
        verdict = "MATCH" if cls == d["expected"] else "MISMATCH"
        rows.append([d["point_id"], t, mode, ng, m, d["request"], d["expected"], baseline, str(rc_n),
                     str(f["rc1"]), str(f["rc2"]), str(f["hit"]), "" if rc_n < 128 else str(rc_n - 128),
                     cls, verdict, str(f["win_malloc"]), str(f["win_open"]), "; ".join([reason] + notes)])

    cols = ["point_id", "tree", "mode", "NG", "M", "request", "expected", "baseline_rc", "rc", "rc1", "rc2", "hit",
            "signal", "class", "verdict_vs_expected", "window_mallocs_seen", "windows_seen", "notes"]
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R6d-2 RNV1 injection, pass %s (judge: judge_d003.classify, imported).  Written by run_r6d_rnv1.py.\n"
                 % (os.path.basename(out_tsv), pas))
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    counts = {}
    for r in rows:
        counts[(r[1], r[13])] = counts.get((r[1], r[13]), 0) + 1
    print("pass=%s rows=%d class_counts=%s mismatches=%d -> %s" % (
        pas, len(rows), counts, sum(1 for r in rows if r[14] == "MISMATCH"), out_tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
