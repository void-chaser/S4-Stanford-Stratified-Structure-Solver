#!/usr/bin/env python3
# s5r7_entry.py -- P05-S5 R7 task brief section 2.5/2.6: two entry-document updates.
#   (1) PROJECT_ROADMAP.md: append one clause at the end of the P05 row (append only, no old text removed) and
#       change ONLY the status cell of the P06 row to "待启动（前置 P05 已签收）"; every other line is unchanged.
#   (2) testing/s4test/ISSUE_REGISTRY.md: insert exactly one status line (P05 signed by the user, transferred
#       items point to P05_S5_OPEN_ITEMS.tsv); no existing OPEN row is changed.
# The script asserts the pre-change files equal HEAD, then verifies the post-change invariants and writes
# ENTRY_SYNC_S5R7.tsv.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
ROADMAP = os.path.join(REPO, "PROJECT_ROADMAP.md")
ISSUE = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
TAB = chr(9)
NL = chr(10)

P05_APPEND = "；P05-S5 已由用户签收（U391，见 checkpoints/p05/P05_S5_SIGNOFF.md），P05 有限范围收口"
P06_STATUS = "待启动（前置 P05 已签收）"
ISSUE_ANCHOR = "> 2026-10-19 P05-S5 R5/R6 状态"
ISSUE_NEW = ("> 2026-10-19 P05 签收入账（U391，P05-S5 已由用户签收）：P05-S5 签收原文见 "
             "checkpoints/p05/P05_S5_SIGNOFF.md §2；P05 随 S5 有限范围收口，P06 可启动；"
             "转出项清单 checkpoints/p05/P05_S5_OPEN_ITEMS.tsv（D017、R-P05-01/02/03、F10/F8、"
             "反事实通量、allzero、S1 报告 11.2 五哈希保持 OPEN/未验证，不在 P05 修、不阻塞 P06）；"
             "本行只记状态，不改任何 OPEN 项。")


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def head_file(rel):
    return subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=REPO)


def main():
    # ---------------- roadmap
    base = head_file("PROJECT_ROADMAP.md")
    cur = open(ROADMAP, "rb").read()
    if P05_APPEND in cur.decode("utf-8"):
        print("roadmap already has the sign-off clause; verifying only")
        new = cur
    else:
        if cur != base:
            print("HARD_STOP PROJECT_ROADMAP.md differs from HEAD before the change")
            return 2
        lines = base.decode("utf-8").split(NL)
        p05 = [i for i, l in enumerate(lines) if l.startswith("| P05 |")]
        p06 = [i for i, l in enumerate(lines) if l.startswith("| P06 |")]
        if len(p05) != 1 or len(p06) != 1:
            print("HARD_STOP roadmap P05/P06 row not unique")
            return 2
        i, j = p05[0], p06[0]
        if not lines[i].endswith(" |"):
            print("HARD_STOP roadmap P05 row cell delimiter missing")
            return 2
        lines[i] = lines[i][:-2] + P05_APPEND + " |"
        cells = lines[j].split("|")
        if len(cells) < 3 or cells[-2].strip() != "待执行":
            print("HARD_STOP roadmap P06 status cell is not 待执行")
            return 2
        cells[-2] = " " + P06_STATUS + " "
        lines[j] = "|".join(cells)
        new = NL.join(lines).encode("utf-8")
        with open(ROADMAP, "wb") as fh:
            fh.write(new)
        print("roadmap P05 line=%d P06 line=%d written" % (i + 1, j + 1))
    # verify roadmap invariants against HEAD
    bl = base.decode("utf-8").split(NL)
    cl = new.decode("utf-8").split(NL)
    i = [k for k, l in enumerate(bl) if l.startswith("| P05 |")][0]
    j = [k for k, l in enumerate(bl) if l.startswith("| P06 |")][0]
    if len(bl) != len(cl):
        print("HARD_STOP roadmap line count changed")
        return 2
    diff = [k for k in range(len(bl)) if bl[k] != cl[k]]
    if diff != [i, j]:
        print("HARD_STOP roadmap changed lines are not exactly P05/P06: " + repr(diff))
        return 2
    if not cl[i].endswith(" |") or not cl[i][:-2].startswith(bl[i][:-2]):
        print("HARD_STOP roadmap P05 row is not a pure append")
        return 2
    a, b = bl[j].split("|"), cl[j].split("|")
    if a[:-2] != b[:-2] or b[-2].strip() != P06_STATUS:
        print("HARD_STOP roadmap P06 row changed more than the status cell")
        return 2
    keep_b = [bl[k] for k in range(len(bl)) if k not in (i, j)]
    keep_c = [cl[k] for k in range(len(cl)) if k not in (i, j)]
    if sha_b((NL.join(keep_b) + NL).encode("utf-8")) != sha_b((NL.join(keep_c) + NL).encode("utf-8")):
        print("HARD_STOP roadmap other lines changed")
        return 2

    # ---------------- issue registry
    ibase = head_file("testing/s4test/ISSUE_REGISTRY.md")
    icur = open(ISSUE, "rb").read()
    if ISSUE_NEW in icur.decode("utf-8"):
        print("issue registry already has the status line; verifying only")
        inew = icur
    else:
        if icur != ibase:
            print("HARD_STOP ISSUE_REGISTRY.md differs from HEAD before the change")
            return 2
        ilines = ibase.decode("utf-8").split(NL)
        anchors = [k for k, l in enumerate(ilines) if l.startswith(ISSUE_ANCHOR)]
        if len(anchors) != 1:
            print("HARD_STOP issue registry anchor line not unique")
            return 2
        k = anchors[0]
        ilines2 = ilines[:k + 1] + [ISSUE_NEW] + ilines[k + 1:]
        inew = NL.join(ilines2).encode("utf-8")
        with open(ISSUE, "wb") as fh:
            fh.write(inew)
        print("issue registry inserted at new line=%d" % (k + 2))
    bil = ibase.decode("utf-8").split(NL)
    cil = inew.decode("utf-8").split(NL)
    if len(cil) != len(bil) + 1:
        print("HARD_STOP issue registry line count is not +1")
        return 2
    found = None
    for kk in range(len(cil)):
        if cil[:kk] + cil[kk + 1:] == bil:
            found = kk
            break
    if found is None:
        print("HARD_STOP issue registry is not a single-line insertion")
        return 2
    if not all(x in cil[found] for x in ("已由用户签收", "P05_S5_OPEN_ITEMS.tsv", "U391", "OPEN")):
        print("HARD_STOP inserted issue-registry line lacks the required content")
        return 2
    if not all(l in cil for l in bil):
        print("HARD_STOP an existing issue-registry line was removed or changed")
        return 2

    body = ["# ENTRY_SYNC_S5R7.tsv -- P05-S5 R7 entry-document sync (roadmap P05 append + P06 status, issue registry +1 line)",
            "# roadmap_before_sha256=%s roadmap_after_sha256=%s" % (sha_b(base), sha_b(new)),
            "# roadmap_changed_lines=P05(row %d,append only),P06(row %d,status cell only)" % (i + 1, j + 1),
            "# issue_before_sha256=%s issue_after_sha256=%s" % (sha_b(ibase), sha_b(inew)),
            "# issue_inserted_line_number=%d issue_open_rows_changed=0" % (found + 1),
            "key" + TAB + "value",
            "ROADMAP_AFTER_SHA256" + TAB + sha_b(rd0(ROADMAP)),
            "ROADMAP_CHANGED_LINES" + TAB + "P05,P06",
            "ISSUE_AFTER_SHA256" + TAB + sha_b(rd0(ISSUE)),
            "ISSUE_INSERTED_LINE" + TAB + str(found + 1),
            "P06_STATUS" + TAB + P06_STATUS]
    open(os.path.join(EV, "ENTRY_SYNC_S5R7.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("ROADMAP before=%s after=%s" % (sha_b(base), sha_b(rd0(ROADMAP))))
    print("ISSUE   before=%s after=%s inserted_line=%d" % (sha_b(ibase), sha_b(rd0(ISSUE)), found + 1))
    return 0


def rd0(p):
    return open(p, "rb").read()


if __name__ == "__main__":
    sys.exit(main())
