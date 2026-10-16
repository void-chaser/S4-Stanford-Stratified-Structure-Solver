#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# test_noinj_control_r8m2e.py -- Non-injection control run for init-F3-san-AL across 3 combos (S-C).
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.path.join(REPO, EV_REL)
DRV = os.path.join(EV, "build", "init-F3-san-AL")
PROBE_DIR = os.path.join(EV, "probe")
OUT_TXT = os.path.join(PROBE_DIR, "test_noinj_control_r8m2e.txt")

COMBOS = [
    ("closed2d-ng1", "closed2d", "1"),
    ("fft-ng5", "fft", "5"),
    ("kottke-ng5", "kottke", "5"),
]


def main():
    os.makedirs(PROBE_DIR, exist_ok=True)
    if not os.path.isfile(DRV):
        sys.stderr.write("REFUSED: driver not found: %s\n" % DRV)
        return 2

    lines = []
    lines.append("# test_noinj_control_r8m2e.txt -- S-C non-injection control run on init-F3-san-AL")
    lines.append("# Driver: %s" % DRV)

    all_ok = True
    hard_stop = False

    for cname, mode, ng in COMBOS:
        env = os.environ.copy()
        env["FMM_MODE"] = mode
        env["S4FMM_NG"] = ng
        env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
        env["UBSAN_OPTIONS"] = "abort_on_error=0"
        env.pop("S4FMM_INJECT", None)
        env.pop("S4_FAIL_ALLOC_AT", None)

        cmd = [DRV, "pattern", "both", "4", "3"]
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
        lines.extend(r.stdout.splitlines()[:10])
        lines.append("--- stderr head ---")
        lines.extend(r.stderr.splitlines()[:10])
        lines.append("")

        if r.returncode != 0 or has_asan:
            hard_stop = True
            all_ok = False
        if has_hit or has_hitcount_nz:
            all_ok = False

    with open(OUT_TXT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("test_noinj_control_r8m2e: wrote %s (all_ok=%s, hard_stop=%s)" % (OUT_TXT, all_ok, hard_stop))

    if hard_stop:
        sys.stderr.write("HARD STOP: ASAN report detected or rc != 0 in non-injection control\n")
        return 1
    if not all_ok:
        sys.stderr.write("CONTROL FAILED: unexpected hit or hitcount\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
