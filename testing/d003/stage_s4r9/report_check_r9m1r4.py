#!/usr/bin/env python3
# report_check_r9m1r4.py -- Report verification and forbidden word audit (Step S-G). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys, re

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RPT_PATH = os.path.join(REPO, "checkpoints", "p05", "P05_S4R9_M1R4_REPORT.md")
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R4")

FORBIDDEN_WORDS = [
    "已修好",
    "静态可达",
    "是否签收",
]

def main():
    if not os.path.isfile(RPT_PATH):
        print(f"Report missing at {RPT_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(RPT_PATH, "r", encoding="utf-8") as f:
        rpt_text = f.read()

    # 1. Check forbidden words
    found_forbidden = []
    for w in FORBIDDEN_WORDS:
        if w in rpt_text:
            found_forbidden.append(w)

    assert not found_forbidden, f"Found forbidden words: {found_forbidden}"

    # 2. Check no commit hash self-citation in report
    # Report should not cite closeout commit hash
    if re.search(r"closeout commit:\s*[0-9a-f]{7,40}", rpt_text, re.IGNORECASE):
        print("Report contains closeout commit hash self-citation!", file=sys.stderr)
        sys.exit(1)

    # 3. Check key numbers consistency in report
    assert "1302" in rpt_text, "Report must cite grand total 1302"
    assert "651" in rpt_text, "Report must cite 651 points"
    assert "416" in rpt_text, "Report must cite 416 K points"
    assert "235" in rpt_text, "Report must cite 235 non-K points"
    assert "U323" in rpt_text, "Report must cite U323"
    assert "E9-29" in rpt_text, "Report must cite E9-29"

    print("Report check passed: no forbidden words, numbers consistent.")

if __name__ == "__main__":
    main()
