#!/usr/bin/env python3
# relr2_audit.py -- P05 delivery round REL-R2: pre-publish audit, read-only (task brief section 5).
# Candidates: A = the current work branch (REL-R3 pushes it as archive/p05-d003-full-20261019);
#             P = the product branch p05/d003-fft-error-propagation.
# For A the committed range audited is 5b72793..c88bf30 (the branch tip before the REL-R2 bookkeeping
# commits); the REL-R2 round adds only text files under checkpoints/p05/ and testing/d003/stage_relr2/,
# which are audited separately in the same table (their sizes are read from disk, since they are not
# committed yet when this script runs).  Nothing is rewritten, nothing is compressed, nothing is fetched.
import os, sys, re, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
TAB = chr(9)
NL = chr(10)
B = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
A_TIP = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
P_TIP = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
A_NAME = "A_work_branch"
P_NAME = "P_product_branch"
MB = 1024.0 * 1024.0


def run(args, cwd=REPO, check=False):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(args):
    p = run(["git"] + args)
    if p.returncode != 0:
        raise SystemExit("git failed: " + " ".join(args) + "\n" + p.stderr[-1000:])
    return p.stdout


def git_ok(args):
    return run(["git"] + args).returncode == 0


def objects(range_spec):
    """[(sha, path, size, type)] for the objects introduced by range_spec, sizes from cat-file."""
    out = git(["rev-list", "--objects", range_spec])
    lines = [l for l in out.splitlines() if l.strip()]
    shas = [l.split(" ", 1)[0] for l in lines]
    paths = {}
    for l in lines:
        parts = l.split(" ", 1)
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
    total = sum(r["size"] for r in blobs)
    top = sorted(blobs, key=lambda r: (-r["size"], r["path"]))[:20]
    over50 = [r for r in blobs if r["size"] >= 50 * MB]
    over100 = [r for r in blobs if r["size"] >= 100 * MB]
    return {"candidate": name, "tip": tip, "range": spec, "blobs": len(blobs),
            "total_bytes": total, "largest": top, "over50": over50, "over100": over100,
            "all_types": sorted(set(r["type"] for r in rows))}


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
    ("HOSTNAME", None),  # filled in main()
]


def sensitive_committed(tip, cand):
    files = [l for l in git(["diff", "--name-only", B, tip]).splitlines() if l.strip()]
    hits = {name: [] for name, _rx in PATTERNS}
    for f in files:
        p = run(["git", "show", tip + ":" + f])
        if p.returncode != 0:
            continue
        text = p.stdout
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, rx in PATTERNS:
                if rx and re.search(rx, line):
                    hits[name].append((f, lineno, line.strip()[:240]))
    return files, hits


def sensitive_delta():
    """The REL-R2 round's own new/modified text files (working tree; not committed when this runs).
    The audit report itself is excluded: it quotes the pattern strings by construction."""
    paths = []
    for root, dirs, fs in os.walk(os.path.join(REPO, "checkpoints/p05")):
        if "evidence" in root:
            dirs[:] = [d for d in dirs if False]
            continue
        for f in fs:
            paths.append(os.path.relpath(os.path.join(root, f), REPO))
    for root, dirs, fs in os.walk(os.path.join(REPO, "testing/d003/stage_relr2")):
        for f in fs:
            paths.append(os.path.relpath(os.path.join(root, f), REPO))
    # only files touched by this round: untracked or modified relative to git
    changed = set()
    st = git(["status", "--porcelain", "-uall"])
    for ln in st.splitlines():
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ")[-1]
        changed.add(p.strip())
    paths = sorted(set(p for p in paths if p in changed
                      and not p.endswith("P05_RELR2_REPORT.md")
                      and not p.endswith("relr2_audit.py")))
    hits = {name: [] for name, _rx in PATTERNS}
    for f in paths:
        fp = os.path.join(REPO, f)
        if not os.path.isfile(fp):
            continue
        try:
            text = open(fp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, rx in PATTERNS:
                if rx and re.search(rx, line):
                    hits[name].append((f, lineno, line.strip()[:240]))
    return paths, hits


def remote_state():
    p = run(["git", "ls-remote", "origin"], timeout if False else REPO) if False else None
    p = subprocess.run(["git", "ls-remote", "origin"], cwd=REPO, capture_output=True, text=True, timeout=120)
    text = p.stdout
    rows = [{"check": "ls_remote_rc", "expected": "0", "actual": str(p.returncode),
             "result": "SAME" if p.returncode == 0 else "MISMATCH"}]
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    rows.append({"check": "origin_is_void_chaser_fork",
                 "expected": "https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git",
                 "actual": url, "result": "SAME" if "void-chaser/S4-Stanford-Stratified-Structure-Solver" in url else "MISMATCH"})
    refs = []
    for l in text.splitlines():
        f = l.split(TAB)
        if len(f) == 2:
            refs.append(f[1])
    def exists(rx):
        return any(re.match(rx, r) for r in refs)
    for label, rx in (("remote_p05_branches", r"^refs/heads/p05/"),
                      ("remote_archive_branches", r"^refs/heads/archive/"),
                      ("remote_tag_p05_signed", r"^refs/tags/p05-signed-20261019$"),
                      ("remote_tag_p05_rel_r1", r"^refs/tags/p05-rel-r1-20261019$")):
        present = exists(rx)
        rows.append({"check": label, "expected": "absent", "actual": "present" if present else "absent",
                     "result": "SAME" if not present else "MISMATCH"})
    rows.append({"check": "remote_ref_count", "expected": "record", "actual": str(len(refs)), "result": "RECORDED"})
    heads = [r for r in refs if r.startswith("refs/heads/")]
    rows.append({"check": "remote_heads", "expected": "record", "actual": ",".join(sorted(heads)), "result": "RECORDED"})
    return rows


def evidence_inventory():
    ev = os.path.join(REPO, "checkpoints/p05/evidence")
    total = subprocess.run(["du", "-s", "--block-size=1", ev], capture_output=True, text=True).stdout.split()[0]
    subs = []
    for name in sorted(os.listdir(ev)):
        p = os.path.join(ev, name)
        if not os.path.isdir(p):
            continue
        out = subprocess.run(["du", "-s", "--block-size=1", p], capture_output=True, text=True).stdout.split()
        if out:
            subs.append((name, int(out[0])))
    subs.sort(key=lambda x: -x[1])
    return int(total), subs


def main():
    host = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
    PATTERNS[-1] = (PATTERNS[-1][0], r"\b" + re.escape(host) + r"\b" if host else r"(?!)")
    va = volume(B + ".." + A_TIP, A_TIP, A_NAME)
    vp = volume(B + ".." + P_TIP, P_TIP, P_NAME)
    files_a, hits_a = sensitive_committed(A_TIP, A_NAME)
    files_p, hits_p = sensitive_committed(P_TIP, P_NAME)
    delta_files, hits_d = sensitive_delta()

    # volume table
    lines = ["# PUBLISH_VOLUME_RELR2.tsv -- pre-publish volume audit (task brief section 5.1)",
             "# object sizes from: git rev-list --objects <range> | git cat-file --batch-check",
             "# A = current work branch tip c88bf30 (before the REL-R2 bookkeeping commits);",
             "# P = product branch HEAD " + P_TIP + ".",
             "# GitHub warning line 50 MB, rejection line 100 MB (binary MB = 1048576 bytes).",
             TAB.join(["candidate", "range", "tip", "new_blob_count", "total_bytes", "total_mib",
                       "blobs_ge_50mb", "blobs_ge_100mb"])]
    for v in (va, vp):
        lines.append(TAB.join([v["candidate"], v["range"], v["tip"], str(v["blobs"]),
                               str(v["total_bytes"]), "%.2f" % (v["total_bytes"] / MB),
                               str(len(v["over50"])), str(len(v["over100"]))]))
    lines += ["", "# largest 20 new blobs per candidate", TAB.join(["candidate", "rank", "bytes", "mib", "path"])]
    for v in (va, vp):
        for k, r in enumerate(v["largest"], 1):
            lines.append(TAB.join([v["candidate"], str(k), str(r["size"]), "%.2f" % (r["size"] / MB), r["path"]]))
    open(os.path.join(EV, "PUBLISH_VOLUME_RELR2.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    # sensitive table
    lines = ["# PUBLISH_AUDIT_RELR2.tsv -- pre-publish sensitive-information audit (task brief section 5.2)",
             "# Record only: nothing is rewritten, no history is changed.  Counts are occurrences over the files",
             "# added or modified in the audited range (git diff --name-only B..tip, content from git show tip:path).",
             "# D = the REL-R2 round's own text files still uncommitted at audit time (the report itself is",
             "# excluded because it quotes the pattern strings by construction).",
             "# Columns: candidate, pattern, hits, files_hit, samples(up to 3, path:line: text)"]
    for cand, files, hits in (("A", files_a, hits_a), ("P", files_p, hits_p), ("D", delta_files, hits_d)):
        for name, _rx in PATTERNS:
            h = hits[name]
            samples = " || ".join("%s:%d: %s" % (f, ln, t) for f, ln, t in h[:3])
            lines.append(TAB.join([cand, name, str(len(h)), str(len(set(f for f, _l, _t in h))),
                                   samples.replace(TAB, " ")]))
        lines.append(TAB.join([cand, "FILES_SCANNED", str(len(files)), "", ",".join(files[:8]) + ("..." if len(files) > 8 else "")]))
    open(os.path.join(EV, "PUBLISH_AUDIT_RELR2.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    # remote table
    rr = remote_state()
    lines = ["# PUBLISH_REMOTE_RELR2.tsv -- read-only remote state (task brief section 5.3)",
             TAB.join(["check", "expected", "actual", "result"])]
    lines += [TAB.join([r["check"], r["expected"], r["actual"], r["result"]]) for r in rr]
    open(os.path.join(EV, "PUBLISH_REMOTE_RELR2.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    # evidence inventory
    total, subs = evidence_inventory()
    lines = ["# EVIDENCE_BACKUP_RELR2.tsv -- offline backup inventory, record only (task brief section 5.4)",
             "# No backup, no compression, no copy is performed by this round.",
             "# total_bytes = du -s --block-size=1 (disk usage) of checkpoints/p05/evidence; top 20 entries.",
             TAB.join(["entry", "bytes", "gib"])]
    lines.append(TAB.join(["TOTAL", str(total), "%.2f" % (total / (1024.0 ** 3))]))
    for name, size in subs[:20]:
        lines.append(TAB.join([name, str(size), "%.2f" % (size / (1024.0 ** 3))]))
    lines.append("# subdirectory count: " + str(len(subs)))
    open(os.path.join(EV, "EVIDENCE_BACKUP_RELR2.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)

    print("A blobs=%d total=%.1f MiB over50=%d over100=%d" % (va["blobs"], va["total_bytes"] / MB,
                                                              len(va["over50"]), len(va["over100"])))
    print("P blobs=%d total=%.1f MiB over50=%d over100=%d" % (vp["blobs"], vp["total_bytes"] / MB,
                                                              len(vp["over50"]), len(vp["over100"])))
    print("A sensitive hits: " + ", ".join("%s=%d" % (n, len(h)) for n, _ in PATTERNS for h in [hits_a[n]]))
    print("P sensitive hits: " + ", ".join("%s=%d" % (n, len(h)) for n, _ in PATTERNS for h in [hits_p[n]]))
    print("D sensitive hits: " + ", ".join("%s=%d" % (n, len(h)) for n, _ in PATTERNS for h in [hits_d[n]]))
    print("remote rows=%d mismatches=%d" % (len(rr), sum(1 for r in rr if r["result"] == "MISMATCH")))
    print("evidence total=%.2f GiB subdirs=%d" % (total / (1024.0 ** 3), len(subs)))
    print("WROTE audit tables under " + os.path.relpath(EV, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
