#!/usr/bin/env python3
# run_s3r3_selfcheck.py -- P05-S3R3-2 self-check runner (new file; modelled on testing/d003/stage_s4/run_r6d_rnv1.py).
#
# Runs the injection points of the S3R3 pre-registration (SECTION A: RNV1 on F2; SECTION C2: tri points on F and F2)
# and writes RESULTS_S3R3_SELFCHECK_pass<P>.tsv.  Judgement: judge_d003.classify (imported, not modified).
# The expected value of every point is read from the pre-registration file (never changed here).
#
# Usage (inside safe_run, output in EVDIR):
#   python3 -I -B testing/d003/stage_s3r3/run_s3r3_selfcheck.py PREREG EVDIR PASS RUN_LABEL
# The driver of each tree is looked up in EVDIR/drivers/ and its sha256 is recorded in the output header.
# Output (never overwritten, U17): EVDIR/RESULTS_S3R3_SELFCHECK_pass<P>[_<label>].tsv and EVDIR/selfcheck/<point>/pass<P>/...
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
GDB_CRASH = os.path.join(HERE, "..", "stage_s4", "r6d_rnv1_crash.gdb")
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_WIN_MALLOC = re.compile(r"^S4FMM R6D_WIN_MALLOC", re.M)
RE_WIN_OPEN = re.compile(r"^S4FMM R6D_WIN_OPEN", re.M)


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
    if len(argv) != 5:
        raise SystemExit("usage: run_s3r3_selfcheck.py PREREG EVDIR PASS RUN_LABEL")
    prereg, ev, pas, tag = argv[1:5]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if not re.match(r"^[a-z0-9]+$", tag):
        raise SystemExit("REFUSED: run label must be [a-z0-9]+")
    out_tsv = os.path.join(ev, "RESULTS_S3R3_SELFCHECK_pass%s_%s.tsv" % (pas, tag))
    if os.path.exists(out_tsv):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out_tsv)
    pre_sha = sha256_file(prereg)
    with open(os.path.join(ev, "REGISTRY_S3R3_SELFCHECK.sha256"), encoding="utf-8") as fh:
        want = fh.read().split()[0]
    if pre_sha != want:
        raise SystemExit("REFUSED: pre-registration sha256 %s != recorded %s" % (pre_sha, want))

    pts = [p for p in read_table(prereg) if p["section"] in ("A", "C2")]
    if len(pts) != 42:
        raise SystemExit("REFUSED: section A + C2 rows %d != 42" % len(pts))

    # drivers: F2 RNV1 (section A), F and F2 tri (section C2); the sha256 of each is recorded in the header
    drv = {
        ("rnv1", "F2"): os.path.join(ev, "drivers", "s3r3-rnv1-F2", "driver"),
        ("tri", "F"): os.path.join(ev, "drivers", "s3r3-tri-F", "driver"),
        ("tri", "F2"): os.path.join(ev, "drivers", "s3r3-tri-F2", "driver"),
    }
    drv_sha = {}
    for k, p in drv.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver %s not executable" % (k,))
        drv_sha[k] = sha256_file(p)

    rows = []
    gdb_done = set()
    for d in pts:
        tree = d["tree"]
        kind = "rnv1" if d["section"] == "A" else "tri"
        dkey = ("rnv1", "F2") if kind == "rnv1" else ("tri", tree)
        driver = drv[dkey]
        mode, ng, m = d["mode"], d["NG"], d["M"]
        env = {"FMM_MODE": mode, "S4FMM_NG": ng, "S4FMM_INJECT": d["request"]}
        pdir = os.path.join(ev, "selfcheck", d["point_id"], "pass" + pas + "_" + tag)
        rc_n, txt_n = run([driver] + GRID, clean_env(env), os.path.join(pdir, "nogdb.out"))
        f = facts(txt_n)
        notes = []
        key = (dkey, mode)
        if key not in gdb_done:
            gdb_done.add(key)
            rc_g, txt_g = run(["gdb", "-batch", "-x", GDB_CRASH, "--args", driver] + GRID, clean_env(env),
                              os.path.join(pdir, "gdb.log"))
            fg = facts(txt_g)
            g_sig = "received signal" in txt_g
            n_sig = rc_n >= 128
            notes.append("gdb log written (first point of %s/%s); gdb rc=%s" % (dkey, mode, rc_g))
            if (g_sig != n_sig) or (fg["rc1"], fg["rc2"], fg["hit"]) != (f["rc1"], f["rc2"], f["hit"]):
                notes.append("GDB_DIVERGENT for this point (gdb rc %s vs %s, facts %s vs %s)" % (rc_g, rc_n, fg, f))
        cls, label, reason = J.classify(rc_n, f["rc1"], f["rc2"], f["hit"], control=False, real=True, inj_call=1)
        verdict = "MATCH" if cls == d["expected"] else "MISMATCH"
        rows.append([d["point_id"], d["section"], tree, mode, ng, m, d["request"], d["expected"], str(rc_n),
                     str(f["rc1"]), str(f["rc2"]), str(f["hit"]), "" if rc_n < 128 else str(rc_n - 128),
                     cls, verdict, str(f["win_malloc"]), str(f["win_open"]), "; ".join([reason] + notes)])

    cols = ["point_id", "section", "tree", "mode", "NG", "M", "request", "expected", "rc", "rc1", "rc2", "hit",
            "signal", "class", "verdict_vs_expected", "window_mallocs_seen", "windows_seen", "notes"]
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S3R3-2 self-check, pass %s run %s (judge: judge_d003.classify, imported).  Written by run_s3r3_selfcheck.py.\n"
                 % (os.path.basename(out_tsv), pas, tag))
        fh.write("# driver sha256: " + "; ".join("%s/%s=%s" % (k[0], k[1], v) for k, v in sorted(drv_sha.items())) + "\n")
        fh.write("# prereg sha256: " + pre_sha + "\n")
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    counts = {}
    for r in rows:
        counts[(r[1], r[2], r[13])] = counts.get((r[1], r[2], r[13]), 0) + 1
    print("pass=%s run=%s rows=%d class_counts=%s mismatches=%d -> %s" % (
        pas, tag, len(rows), counts, sum(1 for r in rows if r[14] == "MISMATCH"), out_tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
