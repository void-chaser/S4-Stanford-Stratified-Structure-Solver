#!/usr/bin/env python3
# relr3_pr.py -- P05 delivery round REL-R3: open ONE Draft pull request in the fork (U395) and verify
# its fields read-only (task brief section 5 step 4).  Parameters are exactly U395's:
#   --repo void-chaser/S4-Stanford-Stratified-Structure-Solver --base master
#   --head p05/d003-fft-error-propagation --draft --body-file $EV/PR_BODY_RELR3.md
# No merge, no ready-for-review, no reviewer, no upstream PR.  Writes only $EV/PR_RELR3.tsv.
import os, sys, json, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
BODY = os.path.join(EV, "PR_BODY_RELR3.md")
OUT = os.path.join(EV, "PR_RELR3.tsv")
TAB = chr(9)
NL = chr(10)
FORK = "void-chaser/S4-Stanford-Stratified-Structure-Solver"
BASE = "master"
HEAD = "p05/d003-fft-error-propagation"
TITLE = "P05 D003: propagate FMM/FFT and pattern allocation failures to the public API"
JSON_FIELDS = "state,isDraft,baseRefName,headRefName,commits,changedFiles,mergedAt,url,number"


def run_merged(args, timeout=180):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=timeout)


def run(args, timeout=120):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)


def write_records(rec, utc):
    lines = ["# PR_RELR3.tsv -- P05 delivery round REL-R3 Draft PR creation and read-only verification (U395)",
             "# gh pr create used exactly: --repo " + FORK + " --base " + BASE + " --head " + HEAD + " --draft",
             "# --body-file $EV/PR_BODY_RELR3.md.  No merge / no ready-for-review / no reviewer / no upstream PR.",
             "# written " + utc,
             TAB.join(["key", "value"])]
    for k in sorted(rec):
        lines.append(TAB.join([k, rec[k]]))
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)


def main():
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not os.path.isfile(BODY):
        print("HARD_STOP PR body missing: " + BODY)
        return 2
    nlines = sum(1 for _ in open(BODY, encoding="utf-8"))
    if nlines > 120:
        print("HARD_STOP PR body longer than 120 lines: %d" % nlines)
        return 2
    rec = {"BODY_LINES": str(nlines), "BODY_SHA256": sha_f(BODY), "CREATE_UTC": utc,
           "TITLE": TITLE}
    p = run_merged(["gh", "pr", "create", "--repo", FORK, "--base", BASE, "--head", HEAD,
                    "--draft", "--title", TITLE, "--body-file", BODY], timeout=180)
    rec["CREATE_RC"] = str(p.returncode)
    rec["CREATE_OUTPUT"] = " || ".join(l.replace(TAB, " ") for l in p.stdout.rstrip(NL).splitlines()[-6:])
    print("gh pr create rc=%d" % p.returncode)
    if p.returncode != 0:
        write_records(rec, utc)
        print("HARD_STOP gh pr create failed; no retry")
        return 2
    url = None
    for line in p.stdout.splitlines():
        if line.strip().startswith("https://github.com/"):
            url = line.strip()
    if url is None:
        write_records(rec, utc)
        print("HARD_STOP cannot parse the PR URL from gh output")
        return 2
    rec["PR_URL"] = url
    m = url.rstrip("/").split("/")
    number = m[-1] if m else ""
    rec["PR_NUMBER"] = number
    print("PR URL=" + url)

    v = run(["gh", "pr", "view", number, "--repo", FORK, "--json", JSON_FIELDS], timeout=120)
    rec["VIEW_RC"] = str(v.returncode)
    rec["VIEW_RAW"] = v.stdout.strip().replace(TAB, " ")
    print("gh pr view rc=%d" % v.returncode)
    if v.returncode != 0:
        write_records(rec, utc)
        print("HARD_STOP gh pr view failed")
        return 2
    try:
        d = json.loads(v.stdout)
    except ValueError:
        write_records(rec, utc)
        print("HARD_STOP cannot parse gh pr view JSON")
        return 2
    rec["PR_STATE"] = str(d.get("state"))
    rec["PR_ISDRAFT"] = "true" if d.get("isDraft") is True else "false"
    rec["PR_BASE"] = str(d.get("baseRefName"))
    rec["PR_HEAD"] = str(d.get("headRefName"))
    rec["PR_COMMITS"] = str(len(d.get("commits") or []))
    rec["PR_CHANGED_FILES"] = str(d.get("changedFiles"))
    rec["PR_MERGED_AT"] = str(d.get("mergedAt"))
    rec["PR_VIEW_URL"] = str(d.get("url"))
    write_records(rec, utc)
    ok = (rec["PR_STATE"] == "OPEN" and rec["PR_ISDRAFT"] == "true" and rec["PR_BASE"] == BASE
          and rec["PR_HEAD"] == HEAD and rec["PR_COMMITS"] == "2" and rec["PR_CHANGED_FILES"] == "11")
    print("PR state=%s isDraft=%s base=%s head=%s commits=%s changedFiles=%s"
          % (rec["PR_STATE"], rec["PR_ISDRAFT"], rec["PR_BASE"], rec["PR_HEAD"],
             rec["PR_COMMITS"], rec["PR_CHANGED_FILES"]))
    print("R8 " + ("SAME" if ok else "MISMATCH"))
    return 0 if ok else 1


def sha_f(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
