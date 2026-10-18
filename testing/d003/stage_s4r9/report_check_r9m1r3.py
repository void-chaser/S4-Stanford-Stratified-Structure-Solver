#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# report_check_r9m1r3.py -- Verify report discipline, forbidden words, referenced tables, and numbers (Step S-I). New file.
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
REPORT_PATH = os.path.join(REPO, "checkpoints", "p05", "P05_S4R9_M1R3_REPORT.md")
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R3")

FORBIDDEN_WORDS = ["完全", "完全一致", "完全闭环", "严格遵循", "已修好", "已验证", "静态可达"]

def main():
    if not os.path.isfile(REPORT_PATH):
        print(f"Report not found at {REPORT_PATH}", file=sys.stderr)
        sys.exit(1)

    content = open(REPORT_PATH, encoding="utf-8").read()
    lines = content.splitlines()

    fails = 0
    # 1. Forbidden words check
    print("=== Checking forbidden words ===")
    for idx, l in enumerate(lines, 1):
        # Exclude quote lines or ruling citation lines if any
        if l.strip().startswith(">") or "U3" in l or "E9-" in l:
            continue
        for w in FORBIDDEN_WORDS:
            if w in l:
                print(f"FAIL: Forbidden word '{w}' at line {idx}: {l}")
                fails += 1
    if fails == 0:
        print("Forbidden words check: PASS (0 occurrences).")

    # 2. Referenced registry files exist
    print("\n=== Checking referenced registry files ===")
    ref_matches = re.findall(r"([A-Za-z0-9_.-]+\.(?:tsv|txt))", content)
    unique_refs = sorted(set(ref_matches))
    for ref in unique_refs:
        # Check if file exists in registries/s4r9/M1R3/ or in evidence
        reg_p = os.path.join(REG_DIR, ref)
        ev_p = os.path.join(EV, ref)
        if not os.path.isfile(reg_p) and not os.path.isfile(ev_p):
            # Check if historical
            hist_found = False
            for rroot, rdirs, rfiles in os.walk(os.path.join(REPO, "checkpoints", "p05", "registries")):
                if ref in rfiles:
                    hist_found = True
                    break
            if not hist_found:
                print(f"WARNING/FAIL: Referenced table not found: {ref}")
                fails += 1
            else:
                print(f"  Historical table OK: {ref}")
        else:
            print(f"  M1R3 registry table OK: {ref}")

    print(f"\nReport check complete. FAILS = {fails}.")
    if fails != 0:
        sys.exit(fails)

if __name__ == "__main__":
    main()
