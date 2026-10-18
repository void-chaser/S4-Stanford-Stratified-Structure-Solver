#!/usr/bin/env python3
# s5r4_prereg.py -- pre-registration of the independent re-judgement v2 (task brief section 5): the sha256
# of every input file is recorded BEFORE the first formal rejudge call, together with the expected counts
# (42 E2E points, 34 recorded D016 rows / 33 rejudged / 1 not judged, DIFFS=0) and status INFLUENCED.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
EV3 = os.path.join(P05, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
TABLES = ["PREREG_E2E_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "PREREG_D016_S5R3.tsv", "D016_PASS1_S5R3.json",
          "D016_PASS2_S5R3.json", "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv"]
EXPECTS = [("E2E_ROWS", "42"), ("E2E_DIFFS", "0"), ("D016_RECORDED_ROWS", "34"),
           ("D016_REJUDGED_ROWS", "33"), ("D016_NOT_JUDGED", "1"), ("D016_DIFFS", "0"), ("DIFFS", "0")]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sums_map(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        d[" ".join(parts[1:])] = parts[0]
    return d


def main():
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sums = sums_map(os.path.join(EV3, "SHA256SUMS.txt"))
    inputs = [(rel, os.path.join(EV3, rel)) for rel in TABLES]
    for pn in (1, 2):
        d = os.path.join(EV3, "e2e/pass%d/points" % pn)
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                inputs.append(("e2e/pass%d/points/%s" % (pn, f), os.path.join(d, f)))
    rows = ["row_kind" + TAB + "key" + TAB + "value" + TAB + "sha256" + TAB + "note"]
    bad = []
    for rel, p in inputs:
        s = sha_f(p)
        note = "matches_p05_s5r3_sha256sums" if sums.get(rel) == s else "MISMATCH"
        if sums.get(rel) != s:
            bad.append(rel)
        rows.append(TAB.join(["INPUT", rel, str(os.path.getsize(p)), s, note]))
    for k, v in EXPECTS:
        rows.append(TAB.join(["EXPECT", k, v, "-", "expected independent-rejudge count"]))
    rows.append(TAB.join(["STATUS", "INFLUENCED", "-", "-",
                          "the S5R3 tables were observed before this re-judgement; the rejudge only re-derives them"]))
    out = os.path.join(EV4, "PREREG_REJUDGE_S5R4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    sha = sha_f(out)
    rec = ["file" + TAB + "sha256" + TAB + "bytes" + TAB + "rows" + TAB + "status" + TAB + "utc_recorded",
           TAB.join(["PREREG_REJUDGE_S5R4.tsv", sha, str(os.path.getsize(out)), str(len(rows) - 1),
                     "INFLUENCED", utc])]
    open(out + ".sha256.txt", "w", encoding="utf-8").write(
        "# PREREG_REJUDGE_S5R4.tsv.sha256.txt -- sha256/UTC recorded before the first formal rejudge call" + NL + NL.join(rec) + NL)
    print("PREREG_INPUTS=%d EXPECT=%d sha=%s utc=%s" % (len(inputs), len(EXPECTS), sha, utc))
    print("INPUT_SHA_BAD=%d" % len(bad))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
