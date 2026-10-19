#!/usr/bin/env python3
# s5r7_rulings.py -- P05-S5 R7 task brief section 2.2: append exactly one ruling row U391 to
# checkpoints/p05/registries/RULINGS.tsv (the user sign-off text given in the conversation).
# No existing row is rewritten.  The script asserts the base bytes/sha, appends one 5-field row,
# re-checks that the old prefix is byte-identical, and writes the evidence table RULINGS_APPEND_S5R7.tsv
# ("U391 row and the sha256 before/after").
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
TEXTFILE = os.path.join(REPO, "testing/d003/stage_s5r7/s5r7_signoff_text.txt")
RUL = os.path.join(P05, "registries/RULINGS.tsv")
TAB = chr(9)
NL = chr(10)

EXP_BASE_BYTES = 156852
EXP_BASE_SHA = "d5742e70c40ebb7a08585860d98557eabcd0aaebbdbabb4f47e9be950a38e9c3"
EXP_TEXT_SHA = "c7af2fb22c9cc9f9ec04d4bfb83cce73478b0a2019ce951f12b1c0804df3f65e"


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def build_row():
    text_sha = sha_b(open(TEXTFILE, "rb").read())
    if text_sha != EXP_TEXT_SHA:
        raise SystemExit("HARD_STOP sign-off anchor sha mismatch: " + text_sha)
    fields = [
        "U391",
        "用户对话签收原文（P05-S5 R7 任务书 §1）",
        "同意签收 P05-S5；范围声明 (a)–(f) 逐字见 checkpoints/p05/P05_S5_SIGNOFF.md §2，"
        "签收原文 sha256=" + text_sha + "；P05 随 S5 签收收口。",
        "P05-S5 R7 任务书 §1（用户签收原文）；checkpoints/p05/P05_S5_SIGNOFF.md §2；"
        "原文 sha256=" + text_sha,
        "生效",
    ]
    return (TAB.join(fields) + NL).encode("utf-8")


def main():
    base = open(RUL, "rb").read()
    if len(base) != EXP_BASE_BYTES or sha_b(base) != EXP_BASE_SHA:
        print("HARD_STOP RULINGS baseline mismatch bytes=%d sha=%s" % (len(base), sha_b(base)))
        return 2
    if not base.endswith(NL.encode("utf-8")):
        print("HARD_STOP RULINGS baseline does not end with a newline")
        return 2
    cur = base
    if "U391" in base.decode("utf-8"):
        print("HARD_STOP RULINGS already contains U391")
        return 2
    row = build_row()
    with open(RUL, "ab") as fh:
        fh.write(row)
    cur = open(RUL, "rb").read()
    if cur[:EXP_BASE_BYTES] != base or sha_b(cur[:EXP_BASE_BYTES]) != EXP_BASE_SHA:
        print("HARD_STOP RULINGS prefix changed")
        return 2
    appended = cur[len(base):]
    lines = [l for l in appended.decode("utf-8").split(NL) if l.strip()]
    if len(lines) != 1:
        print("HARD_STOP expected exactly one appended row, got %d" % len(lines))
        return 2
    fields = lines[0].split(TAB)
    if len(fields) != 5 or fields[0] != "U391" or fields[4] != "生效":
        print("HARD_STOP appended row shape is wrong")
        return 2
    body = ["# RULINGS_APPEND_S5R7.tsv -- P05-S5 R7 RULINGS.tsv append (U391, user sign-off text)",
            "# before_bytes=%d before_sha256=%s" % (EXP_BASE_BYTES, EXP_BASE_SHA),
            "# after_bytes=%d after_sha256=%s" % (len(cur), sha_b(cur)),
            "# prefix_bytes=%d prefix_sha256=%s prefix_unchanged=yes" % (EXP_BASE_BYTES, sha_b(cur[:EXP_BASE_BYTES])),
            "# rows_appended=1 new_row_id=U391 row_bytes=%d row_sha256=%s" % (len(row), sha_b(row)),
            "# signoff_text_sha256=%s" % EXP_TEXT_SHA,
            "id" + TAB + "given_in_round" + TAB + "fields" + TAB + "status",
            fields[0] + TAB + fields[1] + TAB + "5" + TAB + fields[4],
            "ROW_SHA256" + TAB + sha_b(row)]
    open(os.path.join(EV, "RULINGS_APPEND_S5R7.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("RULINGS before=%d/%s after=%d/%s row_sha=%s" % (EXP_BASE_BYTES, EXP_BASE_SHA,
                                                           len(cur), sha_b(cur), sha_b(row)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
