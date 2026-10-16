#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# noinj_control_s3r5.py -- Non-injection control run for F4 drivers across 3 combos (S-G, U289(C)).
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
PROBE_DIR = os.path.join(EV, "probe")
OUT_TXT = os.path.join(PROBE_DIR, "noinj_control_s3r5.txt")

DRIVERS = [
    ("init-F4-dbg", os.path.join(EV, "build", "init-F4-dbg")),
    ("init-F4-san", os.path.join(EV, "build", "init-F4-san")),
    ("init-F4-san-AL", os.path.join(EV, "build", "init-F4-san-AL")),
]

COMBOS = [
    ("closed2d-ng1", "closed2d", "1"),
    ("fft-ng5", "fft", "5"),
    ("kottke-ng5", "kottke", "5"),
]

def main():
    os.makedirs(PROBE_DIR, exist_ok=True)
    lines = [
        "# noinj_control_s3r5.txt -- S-G non-injection control run for F4 drivers (U289(C))",
        "# Expectation: rc=0, san_reports=0, no injection hits",
    ]
    all_ok = True
    hard_stop = False
    for dname, drv_path in DRIVERS:
        if not os.path.isfile(drv_path):
            sys.stderr.write("REFUSED: driver not found: %s\n" % drv_path)
            return 2
        lines.append("==================================================")
        lines.append("Driver: %s (%s)" % (dname, drv_path))
        for cname, mode, ng in COMBOS:
            env = os.environ.copy()
            env["FMM_MODE"] = mode
            env["S4FMM_NG"] = ng
            env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
            env["UBSAN_OPTIONS"] = "abort_on_error=0"
            env.pop("S4FMM_INJECT", None)
            env.pop("S4_FAIL_ALLOC_AT", None)
            cmd = [drv_path, "pattern", "both", "4", "3"]
            r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
            has_hit = ("S4FMM HIT " in r.stderr) or ("S4FMM HIT " in r.stdout)
            has_hitcount_nz = ("S4FMM HITCOUNT" in r.stdout and "S4FMM HITCOUNT 0" not in r.stdout)
            has_asan = ("AddressSanitizer" in r.stderr) or ("AddressSanitizer" in r.stdout)
            lines.append("## Combo: %s (mode=%s, ng=%s)" % (cname, mode, ng))
            lines.append("exit_code: %d" % r.returncode)
            lines.append("stdout_lines: %d" % len(r.stdout.splitlines()))
            lines.append("stderr_lines: %d" % len(r.stderr.splitlines()))
            lines.append("has_hit: %s" % has_hit)
            lines.append("has_hitcount_nz: %s" % has_hitcount_nz)
            lines.append("has_asan: %s" % has_asan)
            lines.append("--- stdout head ---")
            lines.extend(r.stdout.splitlines()[:5])
            lines.append("--- stderr head ---")
            lines.extend(r.stderr.splitlines()[:5])
            lines.append("")
            if r.returncode != 0 or has_asan:
                hard_stop = True
                all_ok = False
            if has_hit or has_hitcount_nz:
                all_ok = False
            print("Driver %s Combo %s -> rc=%d, asan=%s, hit=%s" % (dname, cname, r.returncode, has_asan, has_hit))
    with open(OUT_TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("noinj_control_s3r5: wrote %s (all_ok=%s, hard_stop=%s)" % (OUT_TXT, all_ok, hard_stop))
    if hard_stop:
        sys.stderr.write("HARD STOP: ASAN report detected or rc != 0 in non-injection control\n")
        return 1
    if not all_ok:
        sys.stderr.write("CONTROL FAILED: unexpected hit or hitcount\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
