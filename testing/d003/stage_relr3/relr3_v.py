#!/usr/bin/env python3
# relr3_v.py -- P05 delivery round REL-R3: write V_RELR3.tsv (R1-R9) from the measured record files
# (task brief section 5 step 7).  Every row is judged only from measured values read back from
# PUSH_LOG_RELR3.tsv, REMOTE_BEFORE/REMOTE_AFTER_RELR3.tsv, REMOTE_CLONE_RELR3.tsv and PR_RELR3.tsv;
# the expected strings are copied from PREREG_RELR3.tsv by column name.  R9 is split as pre-registered:
# the final empty working tree is re-measured by the end gate after commit (i); this table records the
# V-generation-time measurement (HEAD not rewritten, round bookkeeping files only).
import os, sys, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
OUT = os.path.join(EV, "V_RELR3.tsv")
TAB = chr(9)
NL = chr(10)
BASE = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
PROD_HEAD = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
MASTER = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
TAG1, TAG2 = "p05-signed-20261019", "p05-rel-r1-20261019"
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
ARCHIVE_BRANCH = "archive/p05-d003-full-20261019"


def read_table(path):
    header = None
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if header is None:
            header = f
            continue
        if len(f) == len(header):
            rows.append(dict(zip(header, f)))
    return rows


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if len(f) == 2 and f[0] != "key":
            d[f[0]] = f[1]
    return d


def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=120)


def git(args):
    return run(["git"] + args).stdout.strip()


def main():
    prereg = {r["test_id"]: r for r in read_table(os.path.join(EV, "PREREG_RELR3.tsv"))}
    plan = {r["ref"]: r for r in read_table(os.path.join(EV, "PUSH_PLAN_RELR3.tsv"))}
    push = read_table(os.path.join(EV, "PUSH_LOG_RELR3.tsv"))
    lsr = {r["ref"]: r for r in push if r["action"] == "ls_remote"}
    pushes = [r for r in push if r["action"] == "push"]
    before = {r["ref"]: r["sha"] for r in read_table(os.path.join(EV, "REMOTE_BEFORE_RELR3.tsv"))}
    after = {r["ref"]: r["sha"] for r in read_table(os.path.join(EV, "REMOTE_AFTER_RELR3.tsv"))}
    clone_rec = read_kv(os.path.join(EV, "REMOTE_CLONE_RELR3.tsv"))
    pr = read_kv(os.path.join(EV, "PR_RELR3.tsv"))
    results = []
    rec = {}

    def add(rid, item, expected, actual, ok):
        results.append({"test_id": rid, "item": item, "expected": expected, "actual": actual,
                        "result": "SAME" if ok else "MISMATCH"})

    # ---- R1-R4: the four pushed refs as observed by ls-remote immediately after each push
    refs = {"R1": "refs/heads/" + PRODUCT_BRANCH, "R2": "refs/heads/" + ARCHIVE_BRANCH,
            "R3": "refs/tags/" + TAG1, "R4": "refs/tags/" + TAG2}
    for rid, ref in refs.items():
        row = lsr.get(ref, {})
        remote_shas = (row.get("remote_sha", "") or "").split(",")
        want = plan.get(ref, {}).get("local_sha", "")
        ok = (row.get("rc") == "0" and row.get("match") == "YES" and want in remote_shas)
        add(rid, "remote " + ref + " sha", prereg[rid]["expected"],
            "ls_remote_sha=" + ",".join(remote_shas) + "; push_rc=" + row.get("rc", "NA")
            + "; match=" + row.get("match", "NA"), ok)
        rec[rid + "_REMOTE_SHA"] = ",".join(remote_shas)

    # ---- R5: master and the six pre-existing heads unchanged; only the four new refs appeared
    old_heads = sorted(r for r in before if r.startswith("refs/heads/"))
    changed = [r for r in old_heads if after.get(r) != before.get(r)]
    new_refs = sorted(set(after) - set(before))
    expected_new = sorted(["refs/heads/" + PRODUCT_BRANCH, "refs/heads/" + ARCHIVE_BRANCH,
                           "refs/tags/" + TAG1, "refs/tags/" + TAG2])
    r5_ok = (not changed) and after.get("refs/heads/master") == MASTER \
        and before.get("refs/heads/master") == MASTER and new_refs == expected_new \
        and set(before) - set(after) == set()
    setrec = []
    for r in old_heads:
        setrec.append("%s=%s" % (r.split("/")[-1], "SAME" if after.get(r) == before.get(r) else "CHANGED"))
    rec["R5_NEW_REFS"] = ",".join(new_refs)
    rec["R5_OLD_HEADS"] = ",".join(setrec)
    add("R5", "remote master and six pre-existing heads", prereg["R5"]["expected"],
        "master=" + str(after.get("refs/heads/master")) + "; old_heads_changed=" + (",".join(changed) or "none")
        + "; new_refs=" + ",".join(new_refs), r5_ok)

    # ---- R6
    r6_ok = (clone_rec.get("R6_HEAD") == PROD_HEAD
             and clone_rec.get("R6_HEAD_S4") == "589e15eb11fcb04e031b524f25a443e7921946cf"
             and clone_rec.get("R6_CLONE_RC") == "0")
    add("R6", "fresh remote clone of the product branch", prereg["R6"]["expected"],
        "clone_rc=" + clone_rec.get("R6_CLONE_RC", "NA") + "; HEAD=" + clone_rec.get("R6_HEAD", "NA")
        + "; HEAD:S4=" + clone_rec.get("R6_HEAD_S4", "NA"), r6_ok)

    # ---- R7
    r7_ok = (clone_rec.get("R7_RC") == "0" and clone_rec.get("R7_FAILING") == "none"
             and clone_rec.get("R7_MISSING") == "none" and clone_rec.get("R7_EXTRA") == "none"
             and clone_rec.get("R7_UNIT_COUNT") == clone_rec.get("R7_EXPECTED_UNITS")
             and clone_rec.get("R7_UNIT_COUNT") == "265")
    add("R7", "make test in the R6 clone", prereg["R7"]["expected"],
        "rc=" + clone_rec.get("R7_RC", "NA") + "; units=" + clone_rec.get("R7_UNIT_COUNT", "NA")
        + "; failing=" + clone_rec.get("R7_FAILING", "NA") + "; missing=" + clone_rec.get("R7_MISSING", "NA")
        + "; extra=" + clone_rec.get("R7_EXTRA", "NA"), r7_ok)

    # ---- R8
    r8_ok = (pr.get("PR_STATE") == "OPEN" and pr.get("PR_ISDRAFT") == "true"
             and pr.get("PR_BASE") == "master" and pr.get("PR_HEAD") == PRODUCT_BRANCH
             and pr.get("PR_COMMITS") == "2" and pr.get("PR_CHANGED_FILES") == "11")
    rec["R8_PR_NUMBER"] = pr.get("PR_NUMBER", "NA")
    rec["R8_PR_URL"] = pr.get("PR_URL", "NA")
    add("R8", "Draft PR in the fork", prereg["R8"]["expected"],
        "state=" + pr.get("PR_STATE", "NA") + "; isDraft=" + pr.get("PR_ISDRAFT", "NA")
        + "; base=" + pr.get("PR_BASE", "NA") + "; head=" + pr.get("PR_HEAD", "NA")
        + "; commits=" + pr.get("PR_COMMITS", "NA") + "; changedFiles=" + pr.get("PR_CHANGED_FILES", "NA"),
        r8_ok)

    # ---- R9 (V-generation-time part; final empty status re-measured by the end gate)
    head = git(["rev-parse", "HEAD"])
    head_ok = (head == BASE) or (run(["git", "merge-base", "--is-ancestor", BASE, head]).returncode == 0)
    refs_ok = (git(["rev-parse", "refs/heads/" + PRODUCT_BRANCH]) == PROD_HEAD
               and git(["rev-parse", TAG1]) == "ef925cdea019a7cdf00acb66bc5b59d55f00d868"
               and git(["rev-parse", TAG2]) == "b42c4c16298ce644f39c3c33ae6c26ef18820a96")
    st = run(["git", "status", "--porcelain=v1", "-uall"]).stdout
    paths = []
    for line in st.splitlines():
        if not line.strip():
            continue
        p = line[3:]
        if " -> " in p:
            p = p.split(" -> ")[-1].strip()
        paths.append(p)
    whitelisted = all(p.startswith("checkpoints/p05/") or p.startswith("testing/d003/stage_relr3/")
                      for p in paths)
    r9_ok = head_ok and refs_ok and whitelisted
    rec["R9_GEN_HEAD"] = head
    rec["R9_GEN_STATUS_PATHS"] = str(len(paths))
    rec["R9_GEN_STATUS_SCOPE"] = "round-bookkeeping-only" if whitelisted else "OUTSIDE_WHITELIST"
    add("R9", "main repository final state (V-generation-time part)", prereg["R9"]["expected"],
        "HEAD=" + head + " (unrewritten=" + str(head_ok) + "); refs_ok=" + str(refs_ok)
        + "; status_paths=" + str(len(paths)) + " scope="
        + ("round-bookkeeping-only" if whitelisted else "OUTSIDE_WHITELIST")
        + "; final empty status re-measured by end gate", r9_ok)

    # ---- write V table
    lines = ["# V_RELR3.tsv -- P05 delivery round REL-R3 comparison table R1-R9 (task brief section 5 step 7)",
             "# expected strings are copied from PREREG_RELR3.tsv by column name; every row is judged only",
             "# from measured values recorded in PUSH_LOG / REMOTE_BEFORE / REMOTE_AFTER / REMOTE_CLONE / PR.",
             "# R9 is split as pre-registered: the final empty git status --short after commit (i) is",
             "# re-measured by the end gate (RECORD STATUS_CLEAN_AFTER_COMMIT).",
             "# Generated " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(["test_id", "item", "expected", "actual", "result"])]
    for r in results:
        lines.append(TAB.join([r["test_id"], r["item"], r["expected"], r["actual"], r["result"]]))
    lines.append("")
    lines.append("# records")
    lines.append(TAB.join(["key", "value"]))
    for k in sorted(rec):
        lines.append(TAB.join([k, str(rec[k])]))
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for r in results:
        print("%-3s %-9s %s" % (r["test_id"], r["result"], r["actual"][:170]))
    print("WROTE " + os.path.relpath(OUT, REPO))
    bad = [r for r in results if r["result"] == "MISMATCH"]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
