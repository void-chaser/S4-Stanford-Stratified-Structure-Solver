#!/usr/bin/env python3
# deviations_r8m2a2.py -- P05-S4 R8 M2a2 CONT1 section 2: deviation table and harness nm check.
# (1) Parses safe_run.log of this round and lists every record whose command after 'cmd=' is not a round script
#     (a file testing/d003/stage_s4/*r8m2a2* run by python3 -I -B or sh).  Nothing is copied by hand.
# (2) Writes HARNESS_NM_R8_M2a2.tsv: nm of the synthetic dual harness binaries, checking that no S4 symbol is present.
# Output: $EV/DEVIATIONS_R8_M2a2.tsv and $EV/HARNESS_NM_R8_M2a2.tsv
import os
import re
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
LOG = os.path.join(EV, "safe_run.log")
OUT_DEV = os.path.join(EV, "DEVIATIONS_R8_M2a2.tsv")
OUT_NM = os.path.join(EV, "HARNESS_NM_R8_M2a2.tsv")
SCRIPT_RE = re.compile(r"^(python3 -I -B|sh) (testing/d003/stage_s4/[^\s]*r8m2a2[^\s]*)(\s|$)")
# Symbols that exist only in libS4 (the S4 library and its C++ names); the harness-only s4fmm_* stubs are not S4 symbols.
S4_SYM_RE = re.compile(r"(Simulation_|S4_Simulation_|S4_New|ComputeLayerModes|LinearSolve|GetFieldOnGrid|FMMGetEpsilon_)")


def classify(cmd):
    """Return (is_round_script, reason)."""
    m = SCRIPT_RE.match(cmd)
    if m:
        return True, "round script %s" % m.group(2)
    if cmd.startswith("python3 -I -B -c"):
        return False, "inline python3 -c (not a round script)"
    first = cmd.split()[0] if cmd.split() else ""
    if first in ("mv", "mkdir"):
        return False, "%s run inline (not allowed by the brief)" % first
    if cmd.startswith("checkpoints/") or cmd.startswith("./"):
        return False, "direct execution of a built binary (not a round script)"
    if cmd.startswith("sh testing/d003/stage_s4/") and "r8m2a2" not in cmd:
        return False, "sh script without the round name"
    return False, "not a round script"


def parse_log():
    rows = []
    with open(LOG, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()]
    for n, line in enumerate(lines, 1):
        parts = line.split("\t")
        ts = parts[0]
        cmd_field = next((p for p in parts if p.startswith("cmd=")), "cmd=")
        cmd = cmd_field[len("cmd="):].strip()
        is_script, reason = classify(cmd)
        if not is_script:
            # repository target of the command: the first path-like token that lies under the repository
            targets = [t for t in cmd.split() if t.startswith("checkpoints/") or t.startswith("testing/")]
            rows.append([str(n), ts, cmd[:120], reason, "YES" if targets else "NO", ";".join(targets[:2]) or "-"])
    return rows, len(lines)


def nm_check():
    """nm of every harness binary in the round build directory: S4 symbols must be absent."""
    bins = []
    for root, _dirs, files in os.walk(os.path.join(EV, "build")):
        for f in files:
            if f.startswith("dual_harness_r8m2a2") and not f.endswith((".o", ".c", ".cpp")):
                bins.append(os.path.join(root, f))
    bins.sort()
    rows = []
    for b in bins:
        try:
            out = subprocess.run(["nm", "-C", b], capture_output=True, text=True).stdout
        except OSError as e:
            out = ""
            rows.append([os.path.relpath(b, EV), "NM_FAILED", str(e), "-"])
            continue
        hits = sorted(set(l.split()[-1] for l in out.splitlines() if S4_SYM_RE.search(l)))
        rows.append([os.path.relpath(b, EV), str(len(out.splitlines())), ";".join(hits[:5]) or "NONE",
                     "PASS_NO_S4_SYMBOL" if not hits else "FAIL_S4_SYMBOL"])
    return rows


def main():
    if os.path.exists(OUT_DEV) or os.path.exists(OUT_NM):
        print("deviations_r8m2a2: REFUSED exists (U17)")
        return 2
    rows, total = parse_log()
    with open(OUT_DEV, "x", encoding="utf-8") as fh:
        fh.write("# DEVIATIONS_R8_M2a2 -- safe_run records that are not round scripts (CONT1 section 2)\n")
        fh.write("# safe_run.log lines in this round: %d ; deviations: %d\n" % (total, len(rows)))
        fh.write("log_line\tutc\tcommand_prefix_120\treason\trepo_target\ttargets\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# DEVIATIONS=%d\n" % len(rows))
    nm = nm_check()
    fails = sum(1 for r in nm if r[-1] != "PASS_NO_S4_SYMBOL")
    with open(OUT_NM, "x", encoding="utf-8") as fh:
        fh.write("# HARNESS_NM_R8_M2a2 -- nm of the synthetic dual harness (dual_stubs_r8m2a2.cpp, no libS4)\n")
        fh.write("binary\tnm_lines\tS4_symbols_found\tresult\n")
        for r in nm:
            fh.write("\t".join(r) + "\n")
        fh.write("# BINARIES=%d FAILS=%d\n" % (len(nm), fails))
    print("deviations_r8m2a2: log_lines=%d deviations=%d harness_bins=%d nm_fails=%d" % (total, len(rows), len(nm), fails))
    return 0


if __name__ == "__main__":
    sys.exit(main())
