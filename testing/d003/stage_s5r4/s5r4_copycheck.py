#!/usr/bin/env python3
# s5r4_copycheck.py -- COPY_DIFF_S5R4.txt for the gate copy (task brief section 6): the S5R4 end gate is an
# evolutionary copy of gate_check_s5r3.py. Every diff hunk must fall into a DECLARED category:
#   CONSTANT  -- constants changed to the S5R4 round (EV4/EV3 roots, baseline, start-gate expectations, R4 names)
#   FIX1..FIX5 -- the five declared checker fixes (task brief section 6)
#   STAGING   -- the staging overrides (--ev-root/--ev3-root/--p05-root/--stage-repo/--post-i-from/--out/...)
#   NEW_CHECK -- the new S5R4 checks (rejudge v2, R3 recheck, R3 immutability, readiness, STATE, draft v2,
#                registry completion, errata/rulings, registry patch, report, shakedown, ...)
#   RENAME    -- an inherited check that had to be renamed because its subject moved to S5R4 (see RENAMES;
#                the semantic is preserved or strengthened, never relaxed)
# Any hunk that matches none of these is UNDECLARED and makes strict_unexpected>0.
# It also asserts that every R3 check name is either still present in the S5R4 gate or listed in RENAMES.
import os, sys, re, difflib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
SRC = os.path.join(REPO, "testing/d003/stage_s5r3/gate_check_s5r3.py")
DST = os.path.join(REPO, "testing/d003/stage_s5r4/gate_check_s5r4.py")
NL = chr(10)
CATS = [
    ("STAGING", ["--ev-root", "--ev3-root", "--p05-root", "--stage-repo", "--post-i-from", "--status-override",
                 "--commit-i", "--out", "staging", "STAGING", "post_from", "POST_I_FROM", "ev_root", "p05_root",
                 "STAGE", "stage_repo", "status_override", "start_records", "listed_map", "GATE_S5R4_start.txt",
                 "first_line", "min_epoch", "LOG", "srec", "recs3", "hdr[0]", "skip_first", "read_tsv"]),
    ("FIX1", ["RULINGS_LINES_5_FIELDS", "rulings_5_fields", "_r5", "RULINGS_DATA_ROWS", "5_fields", "5 tab fields"]),
    ("FIX2", ["FROZEN_POST_I_CALL_COUNTS_MATCH", "frozen_counts", "count_calls", "expected_calls", "mode", "FROZEN_ROWS"]),
    ("FIX3", ["MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "modified_ok", "porcelain", "status, path", "ln[:2]",
              "allow_files", "allow_untracked", "MODIFIED_TRACKED_LINES"]),
    ("FIX4", ["D016_VERDICT_ROWS_34", "d16rows", "MATCH=33,RECORD=1", "D016_VERDICT_COUNTS"]),
    ("FIX5", ["CALIB_DIFF_ZERO", "calib_zero", "SUMMARY", "DIFFS=0"]),
    ("NEW_CHECK", ["REJUDGE_", "R3_GATE_RECHECK", "READINESS_", "SIGNOFF_", "REGISTRY_", "REPORT_", "SHAKEDOWN_",
                   "CHAIN_FORMAL", "END_GATE_", "START_GATE_", "ACCEPTANCE_S5R4", "STATE_MARKERS_R4",
                   "RULINGS_U378", "R3_EVIDENCE", "R3_SCRIPTS", "R3_REPORT", "R3_DRAFT", "POST_I_FROM_LINE",
                   "COMMIT_I_IS_HEAD", "COMMIT_I_SUBJECT", "FROZEN_ROWS_POSITIVE", "EVIDENCE_ITEMS",
                   "FIXED_CHECK_NAMES", "R3_FAIL_NAMES", "CAUSE_CLASSES", "R3_DELIVERED_19", "S5R3_COMPLETION_7",
                   "P05_REAL", "EV4_REAL", "recs3", "RULINGS_MAX_U_385", "ERRATA_S5_LAST_IS_ES5_14",
                   "ERRATA_S5_HAS_ES5_9_TO_14", "STATE_CRITICAL_NUMBERS", "STATE_CHANGED_FROM_START",
                   "ERRATA_S5_GREW", "PREREG_D016_ROWS_36", "COPY_DIFF_S5R4", "ACCEPTANCE_S5R3_ALL_MET"]),
    ("CONSTANT", ["EXP_", "EV4", "EV3", "P05_REAL", "s5r4", "S5R4", "R4", "U385", "U378", "registries/",
                  "evidence/", "05-s5r4", "05-s5r3", "rejudge", "REJUDGE"]),
]
RENAMES = {
    "RULINGS_MAX_U_377": "RULINGS_MAX_U_385",
    "ERRATA_S5_LAST_IS_ES5_8": "ERRATA_S5_LAST_IS_ES5_14",
    "STATE_MARKERS": "STATE_MARKERS_R4",
    "PREREG_D016_ROWS": "PREREG_D016_ROWS_36",
    "REJUDGE_DIFFS_ZERO": "REJUDGE_S5R4_DIFFS_ZERO",
    "ACCEPTANCE_ALL_MET": "ACCEPTANCE_S5R3_ALL_MET",
    "REGISTRY_ISSUE_HAS_ES5_6": "REGISTRY_ISSUE_HAS_ES5_9",
    "REGISTRY_ROADMAP_HAS_ES5_6": "REGISTRY_ROADMAP_HAS_S5R4",
    "REPORT_SIGNOFF_DRAFT_REF": "REPORT_SIGNOFF_DRAFT_V2_REF",
    "REGISTRIES_SUMS_ALL_OK": "REGISTRY_EXPECTED_ALL_IN_SUMS",
}


def names(path):
    t = open(path, encoding="utf-8").read()
    return re.findall(r'safe\("([A-Za-z0-9_]+)"', t)


def classify(lines):
    for cat, keys in CATS:
        for ln in lines:
            for k in keys:
                if k in ln:
                    return cat
    return None


def main():
    a = open(SRC, encoding="utf-8").read().splitlines()
    b = open(DST, encoding="utf-8").read().splitlines()
    diff = list(difflib.unified_diff(a, b, fromfile="testing/d003/stage_s5r3/gate_check_s5r3.py",
                                     tofile="testing/d003/stage_s5r4/gate_check_s5r4.py", lineterm="", n=3))
    hunks = []
    cur = None
    for line in diff:
        if line.startswith("@@"):
            cur = [line]
            hunks.append(cur)
        elif cur is not None:
            cur.append(line)
    out = ["# COPY_DIFF_S5R4.txt -- line diff of the S5R4 end gate against the S5R3 end gate (task brief section 6)",
           "# left  = testing/d003/stage_s5r3/gate_check_s5r3.py",
           "# right = testing/d003/stage_s5r4/gate_check_s5r4.py",
           "# every hunk is classified into a DECLARED category; strict_unexpected counts undeclared hunks.",
           "# categories: CONSTANT FIX1 FIX2 FIX3 FIX4 FIX5 STAGING NEW_CHECK RENAME",
           "# unchanged lines: %d of the S5R3 gate are carried over verbatim (checked below)" % sum(
               1 for l in diff if l.startswith(" "))]
    unexpected = 0
    counts = {}
    for i, h in enumerate(hunks):
        body = [l for l in h if l[:1] in ("+", "-") and not l.startswith(("+++", "---"))]
        cat = classify(body)
        if cat is None:
            unexpected += 1
            out.append("UNDECLARED hunk%d %s" % (i + 1, h[0]))
            for l in body[:8]:
                out.append("    " + l[:200])
        else:
            counts[cat] = counts.get(cat, 0) + 1
            out.append("DECLARED %-10s hunk%d %s (%d changed lines)" % (cat, i + 1, h[0], len(body)))
    out.append("# HUNKS=%d" % len(hunks))
    out.append("# HUNKS_BY_CATEGORY=" + ";".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    n3, n4 = names(SRC), names(DST)
    missing = [(x, RENAMES.get(x)) for x in n3 if x not in n4]
    unresolved = [(x, y) for (x, y) in missing if not y or y not in n4]
    out.append("# R3_CHECKS_STATIC=%d PRESENT=%d RENAMED=%d UNRESOLVED=%d" % (
        len(n3), len([x for x in n3 if x in n4]), len(missing) - len(unresolved), len(unresolved)))
    for (x, y) in missing:
        out.append("# RENAME %s -> %s" % (x, y))
    for (x, y) in unresolved:
        out.append("UNRESOLVED_R3_CHECK %s -> %s" % (x, y))
    out.append("strict_unexpected=%d" % unexpected)
    path = os.path.join(EV4, "COPY_DIFF_S5R4.txt")
    open(path, "w", encoding="utf-8").write(NL.join(out) + NL)
    print("HUNKS=%d BY_CAT=%s" % (len(hunks), ";".join("%s=%d" % (k, counts[k]) for k in sorted(counts))))
    print("R3_CHECKS_STATIC=%d UNRESOLVED=%d" % (len(n3), len(unresolved)))
    print("STRICT_UNEXPECTED=%d" % unexpected)
    print("WROTE " + os.path.relpath(path, REPO))
    return 0 if unexpected == 0 and not unresolved else 1


if __name__ == "__main__":
    sys.exit(main())
