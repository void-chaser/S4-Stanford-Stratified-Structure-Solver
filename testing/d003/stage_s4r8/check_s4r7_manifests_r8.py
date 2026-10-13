#!/usr/bin/env python3
"""P05-S4 R8 M0, restart 2: checks of the registries/s4r7 manifests (U128, U132(b)).  New file.

Called by gate2_r8.sh (which runs under safe_run):
  python3 -I -B testing/d003/stage_s4r8/check_s4r7_manifests_r8.py OUT_NAME
OUT_NAME: S4R7_MANIFEST_CHECK_R8_R2.tsv (opening gate) or S4R7_MANIFEST_CHECK_R8_R2_END.tsv (closing gate).

Reads only: the manifests in registries/s4r7, the files they list, and git objects through "git show".
Writes only: $EV/OUT_NAME, a new file (refused if it exists).  No temporary file is written: the filtered
manifest text goes to "sha256sum -c -" on standard input.  No shell is used.  The last line printed is "fails=<n>".
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
S4R7_REL = "checkpoints/p05/registries/s4r7"
S4R7 = os.path.join(REPO, S4R7_REL)
OUT_RE = re.compile(r"^S4R7_MANIFEST_CHECK_R8_R2(_END)?\.tsv$")

EXPECTED_SET = sorted([
    "SHA256SUMS.txt", "SHA256SUMS_M1.txt", "SHA256SUMS_M2a.txt", "SHA256SUMS_M2b_run6prep.txt",
    "SHA256SUMS_M2b_run7.txt", "SHA256SUMS_M2b_run7_std.txt", "SHA256SUMS_M2b_run7prep.txt",
    "SHA256SUMS_M2b_run7prep_std.txt", "SHA256SUMS_M2bprep.txt", "SHA256SUMS_M2pre.txt",
    "SHA256SUMS_M3.txt", "SHA256SUMS_M3_closeout.txt", "SHA256SUMS_M3_prep.txt",
])

# (a) manifests checked directly: every line must be OK
DIRECT = [
    "SHA256SUMS_M1.txt", "SHA256SUMS_M2bprep.txt", "SHA256SUMS_M2b_run6prep.txt",
    "SHA256SUMS_M2b_run7_std.txt", "SHA256SUMS_M2b_run7prep_std.txt",
    "SHA256SUMS_M3_prep.txt", "SHA256SUMS_M3.txt", "SHA256SUMS_M3_closeout.txt",
]

# (b) manifests with snapshot rows.  name: (own sha256, commit that wrote the manifest,
# number of non-snapshot rows, snapshot rows).  Snapshot kinds: "prefix" = append-only file, sha256 of its
# first N bytes; "state" = sha256 of the file at the write commit.
SNAP_MANIFESTS = {
    "SHA256SUMS.txt": (
        "0f8f06be5bdbbed833ba09199ec79ae4b0813ff32750d16d1d9af0ca45db0a36",
        "8a71b3f459b210119bbc12f71aab879f15c46c54", 10,
        {"ERRATA_7.txt": ("prefix", 5378)}),
    "SHA256SUMS_M2pre.txt": (
        "40380dd10223101e8b63adb9af5143e22ead818f629b14a640de4f8eda646fe1",
        "db9264887add276b68fa93e3c19f20efa5fe7262", 13,
        {"ERRATA_7.txt": ("prefix", 18030), "../RULINGS.tsv": ("prefix", 16066),
         "../../STATE.md": ("state", None)}),
    "SHA256SUMS_M2a.txt": (
        "f03268ee014db0a2ac064bc9a5e641584abeec4de50aa1581c5c96ba5c7525f3",
        "6319a3ca75cb73d30171d87d2b944540116cb018", 16,
        {"ERRATA_7.txt": ("prefix", 19434), "../RULINGS.tsv": ("prefix", 16066),
         "../../STATE.md": ("state", None)}),
}

# manifests whose extra "copied" column prevents sha256sum -c: name: (own sha256, standard copy, row count)
STD_MANIFESTS = {
    "SHA256SUMS_M2b_run7.txt": (
        "3e189f3820263c8f1c01d62aa57cb5bb43462be30d2d810b5a0cd7fd092bfe56",
        "SHA256SUMS_M2b_run7_std.txt", 13),
    "SHA256SUMS_M2b_run7prep.txt": (
        "29ea95057b5942358b4ee1704d6fd4adb61c44f9ea7301b81faf3390f715ad44",
        "SHA256SUMS_M2b_run7prep_std.txt", 3),
}

ROWS = []
FAILS = [0]
MISSING = "MISSING"


def rec(manifest, check, expected, actual):
    ok = (expected == actual) and (expected != MISSING)
    if not ok:
        FAILS[0] += 1
    ROWS.append([manifest, check, str(expected), str(actual), "PASS" if ok else "FAIL"])


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def git_show(commit, repo_path):
    p = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (commit, repo_path)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout if p.returncode == 0 else None


def sha256sum_check(args, data=None):
    p = subprocess.run(["sha256sum", "-c"] + args, cwd=S4R7, input=data,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace").splitlines()


def bad_lines(lines):
    return [ln for ln in lines if not ln.endswith(": OK")]


def manifest_lines(name):
    raw = read_bytes(os.path.join(S4R7, name))
    if raw is None:
        return None, None
    return raw, raw.decode("utf-8").splitlines()


def check_direct(name):
    rc, lines = sha256sum_check([name])
    rec(name, "sha256sum -c: rc=0 and every line OK", "rc=0;bad=0",
        "rc=%d;bad=%d" % (rc, len(bad_lines(lines))))


def check_snapshot(name):
    own, commit, count, snaps = SNAP_MANIFESTS[name]
    raw, lines = manifest_lines(name)
    if raw is None:
        rec(name, "manifest present", "present", MISSING)
        return
    rec(name, "own sha256 (manifest file unchanged)", own, sha_bytes(raw))
    found = {}
    keep = []
    for ln in lines:
        parts = ln.split(None, 1)
        if len(parts) == 2 and parts[1] in snaps:
            found[parts[1]] = parts[0]
        else:
            keep.append(ln)
    rec(name, "snapshot rows (file names)", ", ".join(sorted(snaps)), ", ".join(sorted(found)))
    rec(name, "non-snapshot row count", count, len(keep))
    for fname in sorted(snaps):
        kind, n = snaps[fname]
        repo_path = os.path.normpath(os.path.join(S4R7_REL, fname))
        recorded = found.get(fname, MISSING)
        wrote = git_show(commit, repo_path)
        wrote_sha = sha_bytes(wrote) if wrote is not None else MISSING
        if kind == "prefix":
            cur = read_bytes(os.path.join(REPO, repo_path))
            cur_sha = sha_bytes(cur[:n]) if (cur is not None and len(cur) >= n) else MISSING
            rec(name, "%s: recorded = sha256(current first %d bytes)" % (fname, n), recorded, cur_sha)
            rec(name, "%s: recorded = sha256(git show %s:%s)" % (fname, commit[:12], repo_path),
                recorded, wrote_sha)
            rec(name, "%s: byte length of git show version = %d" % (fname, n), n,
                len(wrote) if wrote is not None else MISSING)
        else:
            rec(name, "%s: recorded = sha256(git show %s:%s)" % (fname, commit[:12], repo_path),
                recorded, wrote_sha)
    data = ("\n".join(keep) + "\n").encode("utf-8")
    rc, out = sha256sum_check(["-"], data)
    rec(name, "non-snapshot rows: sha256sum -c rc=0 and every line OK", "rc=0;bad=0",
        "rc=%d;bad=%d" % (rc, len(bad_lines(out))))


def check_std(name):
    own, std_name, count = STD_MANIFESTS[name]
    raw, lines = manifest_lines(name)
    std_raw, std_lines = manifest_lines(std_name)
    if raw is None or std_raw is None:
        rec(name, "manifest and standard copy present", "present", MISSING)
        return
    rec(name, "own sha256 (manifest file unchanged)", own, sha_bytes(raw))
    rec(name, "row count", count, len(lines))
    rec(name, "row count of %s" % std_name, count, len(std_lines))
    equal = 0
    for ln, sl in zip(lines, std_lines):
        if ln.split()[:2] == sl.split()[:2]:
            equal += 1
    rec(name, "first two columns equal to %s, line by line" % std_name, count, equal)


def check_set():
    names = sorted(n for n in os.listdir(S4R7) if n.startswith("SHA256SUMS") and n.endswith(".txt"))
    rec("registries/s4r7", "SHA256SUMS*.txt set (exactly the 13 expected names)",
        ", ".join(EXPECTED_SET), ", ".join(names))


def main(argv):
    if len(argv) != 2 or not OUT_RE.match(argv[1]):
        raise SystemExit("usage: check_s4r7_manifests_r8.py S4R7_MANIFEST_CHECK_R8_R2[_END].tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    for name in DIRECT:
        check_direct(name)
    for name in sorted(SNAP_MANIFESTS):
        check_snapshot(name)
    for name in sorted(STD_MANIFESTS):
        check_std(name)
    check_set()
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R8 M0 restart 2 (RESTART section 2.2; U128, U132(b)).  Reads registries/s4r7 only.\n"
                 % argv[1])
        fh.write("manifest\tcheck\texpected\tactual\tresult\n")
        for row in ROWS:
            fh.write("\t".join(row) + "\n")
        fh.write("fails=%d\n" % FAILS[0])
    print("fails=%d" % FAILS[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
