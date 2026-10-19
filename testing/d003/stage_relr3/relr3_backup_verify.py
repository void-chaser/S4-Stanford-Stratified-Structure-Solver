#!/usr/bin/env python3
# relr3_backup_verify.py -- P05 delivery round REL-R3: READ-ONLY verification of an offline evidence
# backup (task brief section 5 step 6; U398 says the backup itself is executed by the user by hand).
#
# The script is NOT run by the round against any repository-external path.  The user runs it after making
# a backup, e.g.:
#   python3 testing/d003/stage_relr3/relr3_backup_verify.py --media /media/user/P05_BACKUP
#
# It reads every SHA256SUMS.txt under the given media path (the per-round evidence and registry lists),
# re-hashes every item listed there and compares.  It never writes to the media path: all media access is
# open(..., "rb").  It writes only the TSV report, which MUST stay under $EV
# (checkpoints/p05/evidence/p05-rel-r3/) and refuses any other --out path.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
TAB = chr(9)
NL = chr(10)


def sha_f(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def parse_sums(path):
    items = []
    bad = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\r\n")
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            bad.append("MALFORMED")
            continue
        items.append((parts[0], " ".join(parts[1:])))
    return items, bad


def main():
    args = sys.argv[1:]
    media = None
    out = os.path.join(EV, "BACKUP_VERIFY_RELR3.tsv")
    repo = REPO
    i = 0
    while i < len(args):
        if args[i] == "--media":
            media = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        elif args[i] == "--repo":
            repo = args[i + 1]
            i += 2
        else:
            print("HARD_STOP unknown argument: " + args[i])
            return 2
    if not media:
        print("usage: relr3_backup_verify.py --media <backup-root> [--out <$EV/report.tsv>] [--repo <repo-root>]")
        return 2
    media = os.path.realpath(media)
    real_ev = os.path.realpath(EV)
    real_out = os.path.realpath(out)
    if not real_out.startswith(real_ev + os.sep):
        print("HARD_STOP --out must stay under the round evidence directory: " + real_ev)
        return 2
    if not os.path.isdir(media):
        print("HARD_STOP media path is not a directory: " + media)
        return 2

    sums_files = []
    for root, dirs, files in os.walk(media):
        dirs.sort()
        for f in sorted(files):
            if f == "SHA256SUMS.txt":
                sums_files.append(os.path.join(root, f))
    rows = []
    total_items = total_ok = total_missing = total_bad = 0
    for sf in sorted(sums_files):
        rel_sf = os.path.relpath(sf, media)
        items, malformed = parse_sums(sf)
        checked = ok = 0
        missing = []
        mismatch = []
        for want, rel in items:
            target = os.path.join(os.path.dirname(sf), rel)
            checked += 1
            if not os.path.isfile(target):
                missing.append(rel)
                continue
            if sha_f(target) == want:
                ok += 1
            else:
                mismatch.append(rel)
        repo_copy = os.path.join(repo, rel_sf)
        list_match = ""
        if os.path.isfile(repo_copy):
            list_match = "YES" if sha_f(repo_copy) == sha_f(sf) else "NO"
        else:
            list_match = "NOT_IN_REPO"
        rows.append({"sums_file": rel_sf, "checked": checked, "ok": ok,
                     "missing": len(missing), "mismatch": len(mismatch),
                     "malformed": len(malformed), "list_matches_repo": list_match,
                     "missing_names": ",".join(missing[:5]), "mismatch_names": ",".join(mismatch[:5])})
        total_items += checked
        total_ok += ok
        total_missing += len(missing)
        total_bad += len(mismatch) + len(malformed)
    lines = ["# BACKUP_VERIFY_RELR3.tsv -- READ-ONLY offline evidence backup verification (task brief section 5 step 6)",
             "# The media path is read only (open(..., 'rb')); nothing is written there.  This report is written",
             "# under $EV only.  One row per SHA256SUMS.txt found under the media path.",
             "# generated " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(["sums_file", "checked", "ok", "missing", "mismatch", "malformed",
                       "list_matches_repo", "missing_names", "mismatch_names"])]
    for r in rows:
        lines.append(TAB.join([r["sums_file"], str(r["checked"]), str(r["ok"]), str(r["missing"]),
                               str(r["mismatch"]), str(r["malformed"]), r["list_matches_repo"],
                               r["missing_names"], r["mismatch_names"]]))
    lines.append("")
    lines.append(TAB.join(["TOTAL_SUMS_FILES", str(len(rows))]))
    lines.append(TAB.join(["TOTAL_ITEMS", str(total_items)]))
    lines.append(TAB.join(["TOTAL_OK", str(total_ok)]))
    lines.append(TAB.join(["TOTAL_MISSING", str(total_missing)]))
    lines.append(TAB.join(["TOTAL_BAD", str(total_bad)]))
    lines.append(TAB.join(["VERDICT", "PASS" if total_bad == 0 and total_missing == 0 and rows else "FAIL"]))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("sums_files=%d items=%d ok=%d missing=%d bad=%d verdict=%s"
          % (len(rows), total_items, total_ok, total_missing, total_bad,
             "PASS" if total_bad == 0 and total_missing == 0 and rows else "FAIL"))
    print("WROTE " + out)
    return 0 if total_bad == 0 and total_missing == 0 and rows else 1


if __name__ == "__main__":
    sys.exit(main())
