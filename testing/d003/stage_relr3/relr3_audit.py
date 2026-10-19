#!/usr/bin/env python3
# relr3_audit.py -- P05 delivery round REL-R3: pre-push read-only audit (task brief section 3).
#   (1) sensitive-information scan of the two REL-R2 commits (range c88bf30..4607e96) with exactly the
#       REL-R2 section 6.2 pattern table and the same counting rule; token/key hits must be 0 or HARD_STOP.
#   (2) volume recomputation over 5b72793..4607e96 (the archive branch): new blobs, total bytes, largest
#       blob, >=50 MB and >=100 MB counts; any blob >= 50 MB is a HARD_STOP.
#   (3) push plan: per pushed ref, git rev-list --count 5b72793..<ref> and, for tags, the tag object sha.
#   (4) read-only remote baseline (git ls-remote origin) compared with the REL-R2 record.
# Nothing is written outside $EV (checkpoints/p05/evidence/p05-rel-r3/).  No network write, no fetch.
import os, re, sys, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
TAB = chr(9)
NL = chr(10)
B = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
RELR2_TIP = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
A_TIP = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
P_TIP = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
TAG1, TAG2 = "p05-signed-20261019", "p05-rel-r1-20261019"
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
ARCHIVE_BRANCH = "archive/p05-d003-full-20261019"
MB = 1024.0 * 1024.0


def run(args, timeout=180):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)


def git(args):
    p = run(["git"] + args)
    if p.returncode != 0:
        raise SystemExit("git failed: " + " ".join(args) + NL + p.stderr[-1000:])
    return p.stdout


def objects(range_spec):
    out = git(["rev-list", "--objects", range_spec])
    lines = [l for l in out.splitlines() if l.strip()]
    shas = []
    paths = {}
    for l in lines:
        parts = l.split(" ", 1)
        shas.append(parts[0])
        if len(parts) == 2:
            paths[parts[0]] = parts[1]
    p = subprocess.run(["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
                       cwd=REPO, input=NL.join(shas) + NL, capture_output=True, text=True)
    rows = []
    for l in p.stdout.splitlines():
        f = l.split(" ")
        if len(f) < 3:
            continue
        rows.append({"sha": f[0], "type": f[1], "size": int(f[2]), "path": paths.get(f[0], "")})
    return rows


def volume(spec, tip, name):
    rows = objects(spec)
    blobs = [r for r in rows if r["type"] == "blob"]
    blobs.sort(key=lambda r: (-r["size"], r["path"]))
    over50 = [r for r in blobs if r["size"] >= 50 * MB]
    over100 = [r for r in blobs if r["size"] >= 100 * MB]
    return {"candidate": name, "range": spec, "tip": tip, "blobs": len(blobs),
            "total_bytes": sum(r["size"] for r in blobs),
            "largest": blobs[0] if blobs else {"size": 0, "path": ""},
            "over50": over50, "over100": over100}


PATTERNS = [
    ("TOKEN_GHP", r"ghp_[A-Za-z0-9]{20,}"),
    ("TOKEN_GITHUB_PAT", r"github_pat_[A-Za-z0-9_]{20,}"),
    ("TOKEN_AKIA", r"AKIA[0-9A-Z]{16}"),
    ("PRIVATE_KEY_BEGIN", r"BEGIN [A-Z ]*PRIVATE KEY"),
    ("PASSWORD_ASSIGN", r"(?i)password\s*="),
    ("ABS_PATH_HOME", r"/home/"),
    ("ABS_PATH_SRV", r"/srv/nvme/"),
    ("USERNAME", r"\bjackal\b|\bvoid-chaser\b|\bZiyang Li\b"),
    ("EMAIL", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("HOSTNAME", None),
]
TOKEN_PATTERNS = ("TOKEN_GHP", "TOKEN_GITHUB_PAT", "TOKEN_AKIA", "PRIVATE_KEY_BEGIN", "PASSWORD_ASSIGN")


def sensitive_committed(a, b):
    files = [l for l in git(["diff", "--name-only", a, b]).splitlines() if l.strip()]
    hits = {name: [] for name, _rx in PATTERNS}
    for f in files:
        p = run(["git", "show", b + ":" + f])
        if p.returncode != 0:
            continue
        for lineno, line in enumerate(p.stdout.splitlines(), 1):
            for name, rx in PATTERNS:
                if rx and re.search(rx, line):
                    hits[name].append((f, lineno, line.strip()[:240]))
    return files, hits


def relr2_remote_record():
    path = os.path.join(REPO, "checkpoints/p05/registries/rel-r2/PUBLISH_REMOTE_RELR2.tsv")
    rows = {}
    header = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if header is None:
            header = f
            continue
        if len(f) != len(header):
            continue
        d = dict(zip(header, f))
        rows[d["check"]] = d
    return rows


def remote_before(expected):
    p = run(["git", "ls-remote", "origin"], timeout=120)
    refs = []
    for l in p.stdout.splitlines():
        f = l.split(TAB)
        if len(f) == 2:
            refs.append((f[1], f[0]))
    by = dict(refs)
    url = run(["git", "remote", "get-url", "origin"]).stdout.strip()
    rows = []
    rows.append({"check": "ls_remote_rc", "expected": "0", "actual": str(p.returncode),
                 "result": "SAME" if p.returncode == 0 else "MISMATCH"})
    rows.append({"check": "origin_is_void_chaser_fork",
                 "expected": expected.get("origin_is_void_chaser_fork", {}).get("expected", ""),
                 "actual": url,
                 "result": "SAME" if "void-chaser/S4-Stanford-Stratified-Structure-Solver" in url else "MISMATCH"})
    for label, rx in (("remote_p05_branches", r"^refs/heads/p05/"),
                      ("remote_archive_branches", r"^refs/heads/archive/"),
                      ("remote_tag_p05_signed", r"^refs/tags/p05-signed-20261019$"),
                      ("remote_tag_p05_rel_r1", r"^refs/tags/p05-rel-r1-20261019$")):
        present = any(re.match(rx, r) for r, _s in refs)
        rows.append({"check": label, "expected": "absent", "actual": "present" if present else "absent",
                     "result": "SAME" if not present else "MISMATCH"})
    exp_count = expected.get("remote_ref_count", {}).get("actual", "9")
    rows.append({"check": "remote_ref_count", "expected": exp_count, "actual": str(len(refs)),
                 "result": "SAME" if str(len(refs)) == exp_count else "MISMATCH"})
    heads = sorted(r for r, _s in refs if r.startswith("refs/heads/"))
    exp_heads = expected.get("remote_heads", {}).get("actual", "").split(",")
    rows.append({"check": "remote_heads", "expected": ",".join(exp_heads), "actual": ",".join(heads),
                 "result": "SAME" if heads == exp_heads else "MISMATCH"})
    rows.append({"check": "remote_master_sha", "expected": B, "actual": by.get("refs/heads/master", "absent"),
                 "result": "SAME" if by.get("refs/heads/master") == B else "MISMATCH"})
    return rows, refs


def main():
    host = run(["hostname"]).stdout.strip()
    PATTERNS[-1] = ("HOSTNAME", r"\b" + re.escape(host) + r"\b" if host else r"(?!)")
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(EV, exist_ok=True)

    files, hits = sensitive_committed(RELR2_TIP, A_TIP)
    lines = ["# PUBLISH_AUDIT_RELR3.tsv -- pre-push sensitive-information supplementary audit (task brief section 3)",
             "# Range: c88bf30..4607e96 (the two REL-R2 bookkeeping commits; the REL-R2 audit covered 5b72793..c88bf30",
             "# for A and 5b72793..8e4c014 for P and found 0 token/key hits).  Pattern table and counting rule are",
             "# exactly the REL-R2 report section 6.2 ones.  Record only: nothing is rewritten, no history is changed.",
             "# Counts are occurrences over the files added or modified in the range (git diff --name-only; content",
             "# from git show 4607e96:path).  Any token/key hit is a HARD_STOP (no push).",
             "# Columns: candidate, pattern, hits, files_hit, samples(up to 3, path:line: text), classification",
             "# classification: NONE (no hit); RECORD_ONLY (non-token pattern); PATTERN_QUOTE_NOT_SECRET",
             "# (a token regex matching the audit's own pattern name quoted in a report -- REL-R2 section 6.2",
             "# already excludes the report/audit script from the stop count for exactly this reason);",
             "# CREDENTIAL (a real token/key hit -> HARD_STOP).",
             TAB.join(["candidate", "pattern", "hits", "files_hit", "samples", "classification"])]

    def classify(name, f, text):
        if name not in TOKEN_PATTERNS:
            return "RECORD_ONLY"
        if f.endswith("P05_RELR2_REPORT.md") and "token/密钥类" in text:
            return "PATTERN_QUOTE_NOT_SECRET"
        return "CREDENTIAL"

    token_secret = 0
    token_quote = 0
    for name, _rx in PATTERNS:
        h = hits[name]
        samples = " || ".join("%s:%d: %s" % (f, ln, t) for f, ln, t in h[:3])
        classes = [classify(name, f, t) for f, _l, t in h]
        if name in TOKEN_PATTERNS:
            token_secret += sum(1 for c in classes if c == "CREDENTIAL")
            token_quote += sum(1 for c in classes if c == "PATTERN_QUOTE_NOT_SECRET")
            cls = ("CREDENTIAL" if token_secret else
                   ("PATTERN_QUOTE_NOT_SECRET" if token_quote else "NONE"))
        else:
            cls = "RECORD_ONLY" if h else "NONE"
        lines.append(TAB.join(["NEW_RELR2_COMMITS", name, str(len(h)),
                               str(len(set(f for f, _l, _t in h))), samples.replace(TAB, " "), cls]))
    lines.append(TAB.join(["NEW_RELR2_COMMITS", "FILES_SCANNED", str(len(files)), "",
                           ",".join(files[:8]) + ("..." if len(files) > 8 else ""), "RECORD_ONLY"]))
    lines.append(TAB.join(["NEW_RELR2_COMMITS", "TOKEN_SECRETS_TOTAL", str(token_secret), "",
                           "real credential hits; HARD_STOP if non-zero",
                           "PASS" if token_secret == 0 else "HARD_STOP"]))
    lines.append(TAB.join(["NEW_RELR2_COMMITS", "TOKEN_PATTERN_QUOTES_TOTAL", str(token_quote), "",
                           "token regex matching the audit pattern name quoted by a report (not a secret)",
                           "NOT_A_SECRET"]))
    lines.append("# token/key credential hits over the new range: " + str(token_secret)
                 + " (pattern-name quotes: " + str(token_quote) + ")"
                 + (" -- PASS: no HARD_STOP" if token_secret == 0 else " -- HARD_STOP: do not push"))
    lines.append("# written " + utc)
    open(os.path.join(EV, "PUBLISH_AUDIT_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    va = volume(B + ".." + A_TIP, A_TIP, "A_archive_branch")
    vp = volume(B + ".." + P_TIP, P_TIP, "P_product_branch")
    lines = ["# PUBLISH_VOLUME_RELR3.tsv -- pre-push volume recomputation (task brief section 3)",
             "# object sizes from: git rev-list --objects <range> | git cat-file --batch-check",
             "# A_archive_branch = 5b72793..4607e96 (the range pushed as archive/p05-d003-full-20261019);",
             "# P_product_branch = 5b72793..8e4c014 (recorded for context; unchanged from REL-R2).",
             "# GitHub warning line 50 MB, rejection line 100 MB (binary MB = 1048576 bytes).  Any blob >= 50 MB is",
             "# a HARD_STOP (no push).",
             TAB.join(["candidate", "range", "tip", "new_blob_count", "total_bytes", "total_mib",
                       "largest_blob_bytes", "largest_blob_path", "blobs_ge_50mb", "blobs_ge_100mb"])]
    for v in (va, vp):
        lines.append(TAB.join([v["candidate"], v["range"], v["tip"], str(v["blobs"]), str(v["total_bytes"]),
                               "%.2f" % (v["total_bytes"] / MB), str(v["largest"]["size"]),
                               v["largest"]["path"], str(len(v["over50"])), str(len(v["over100"]))]))
    lines.append("# >=50 MB blobs: A=%d P=%d (any non-zero A count is a HARD_STOP)" % (len(va["over50"]), len(vp["over50"])))
    lines.append("# written " + utc)
    open(os.path.join(EV, "PUBLISH_VOLUME_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    tag1_obj = git(["rev-parse", TAG1]).strip()
    tag2_obj = git(["rev-parse", TAG2]).strip()
    tag1_peel = git(["rev-parse", TAG1 + "^{commit}"]).strip()
    tag2_peel = git(["rev-parse", TAG2 + "^{commit}"]).strip()
    plan = [
        {"seq": "1", "kind": "branch", "ref": "refs/heads/" + PRODUCT_BRANCH, "local_sha": P_TIP,
         "peel_commit": "", "push_src": "refs/heads/" + PRODUCT_BRANCH, "push_dst": "refs/heads/" + PRODUCT_BRANCH,
         "order_spec": "(a)"},
        {"seq": "2", "kind": "branch", "ref": "refs/heads/" + ARCHIVE_BRANCH, "local_sha": A_TIP,
         "peel_commit": "", "push_src": "refs/heads/" + ARCHIVE_BRANCH, "push_dst": "refs/heads/" + ARCHIVE_BRANCH,
         "order_spec": "(b)"},
        {"seq": "3", "kind": "tag", "ref": "refs/tags/" + TAG1, "local_sha": tag1_obj,
         "peel_commit": tag1_peel, "push_src": "refs/tags/" + TAG1, "push_dst": "",
         "order_spec": "(c)"},
        {"seq": "4", "kind": "tag", "ref": "refs/tags/" + TAG2, "local_sha": tag2_obj,
         "peel_commit": tag2_peel, "push_src": "refs/tags/" + TAG2, "push_dst": "",
         "order_spec": "(d)"},
    ]
    lines = ["# PUSH_PLAN_RELR3.tsv -- the four refs to push, in U393 order (task brief section 3)",
             "# commits_above_b = git rev-list --count 5b72793..<ref>; tag rows: local_sha is the annotated tag",
             "# object sha and peel_commit is its peeled commit.  No ref outside these four is pushed.",
             TAB.join(["seq", "order_spec", "kind", "ref", "local_sha", "peel_commit", "commits_above_b",
                       "push_src", "push_dst", "remote_absent_before"])]
    expected_abs = {"refs/heads/" + PRODUCT_BRANCH: "absent", "refs/heads/" + ARCHIVE_BRANCH: "absent",
                    "refs/tags/" + TAG1: "absent", "refs/tags/" + TAG2: "absent"}
    for r in plan:
        tip = r["peel_commit"] if r["kind"] == "tag" else r["local_sha"]
        cnt = git(["rev-list", "--count", B + ".." + tip]).strip()
        r["commits_above_b"] = cnt
        lines.append(TAB.join([r["seq"], r["order_spec"], r["kind"], r["ref"], r["local_sha"],
                               r["peel_commit"], cnt, r["push_src"], r["push_dst"],
                               expected_abs[r["ref"]]]))
    lines.append("# written " + utc)
    open(os.path.join(EV, "PUSH_PLAN_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    relr2 = relr2_remote_record()
    rows, refs = remote_before(relr2)
    lines = ["# PUBLISH_REMOTE_RELR3.tsv -- read-only remote baseline before any push (task brief section 2)",
             "# Compared with REL-R2 checkpoints/p05/registries/rel-r2/PUBLISH_REMOTE_RELR2.tsv by column name.",
             TAB.join(["check", "expected", "actual", "result"])]
    lines += [TAB.join([r["check"], r["expected"], r["actual"], r["result"]]) for r in rows]
    lines.append("")
    lines.append("# all remote refs observed before any push")
    lines.append(TAB.join(["ref", "sha"]))
    for r, s in sorted(refs):
        lines.append(TAB.join([r, s]))
    lines.append("# written " + utc)
    open(os.path.join(EV, "PUBLISH_REMOTE_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    lines = ["# REMOTE_BEFORE_RELR3.tsv -- all remote refs (name, sha) captured read-only before any push",
             "# Used by R5: master and the six pre-existing heads must keep these shas after the four pushes.",
             "# written " + utc,
             TAB.join(["ref", "sha"])]
    for r, s in sorted(refs):
        lines.append(TAB.join([r, s]))
    open(os.path.join(EV, "REMOTE_BEFORE_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    print("sensitive NEW range files=%d token_secrets=%d token_pattern_quotes=%d"
          % (len(files), token_secret, token_quote))
    for name in ("ABS_PATH_SRV", "ABS_PATH_HOME", "USERNAME", "EMAIL", "HOSTNAME"):
        print("  %s=%d" % (name, len(hits[name])))
    print("volume A blobs=%d total=%.2f MiB largest=%d >=50MB=%d >=100MB=%d"
          % (va["blobs"], va["total_bytes"] / MB, va["largest"]["size"], len(va["over50"]), len(va["over100"])))
    print("volume P blobs=%d total=%.2f MiB" % (vp["blobs"], vp["total_bytes"] / MB))
    print("push plan rows=%d" % len(plan))
    for r in plan:
        print("  %s %s %s commits=%s" % (r["order_spec"], r["ref"], r["local_sha"][:12], r["commits_above_b"]))
    bad_remote = [r for r in rows if r["result"] == "MISMATCH"]
    print("remote baseline rows=%d mismatches=%d" % (len(rows), len(bad_remote)))
    if token_secret != 0:
        print("HARD_STOP real token/key hits != 0 -- do not push")
        return 1
    if len(va["over50"]) != 0:
        print("HARD_STOP blob >= 50 MB in the archive range -- do not push")
        return 1
    if bad_remote:
        print("HARD_STOP remote baseline differs from the REL-R2 record -- stop")
        return 1
    print("WROTE audit tables under " + os.path.relpath(EV, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
