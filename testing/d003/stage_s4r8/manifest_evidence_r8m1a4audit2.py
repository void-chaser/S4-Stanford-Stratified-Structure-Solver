#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2): evidence manifest for the round.  New file.

Writes SHA256SUMS_M1a4AUDIT2.txt into the round evidence directory.  The manifest covers:
  - the 198 formal runs: events.tsv, summary.json, gdb.stdout.txt, gdb.stderr.txt of each unit directory
    (callseq_r8m1a4_r3/<unit>/);
  - the first and partial call-sequence runs, if present (callseq_r8m1a4/, callseq_r8m1a4_r2/);
  - the A and B raw logs of the nine F3 combinations (additions_r8m1a4/a1map_F3_*, b_map_F3_*): stderr, counts, gdb,
    gdb_rc, callers, base and call logs as present;
  - the expectation files, the source tables and the driver tables (registries/s4r7, s4r6c, s3r4c2, s3r4c3, s4r8/M1a);
  - the device scripts of testing/d003/stage_s4r8 that the round ran (hash only);
  - the PRERUN record and the two safe_run.log files, as LIVE entries (length and sha256 at the time of the record).
Trees, libraries and driver binaries are recorded as identity hashes only (their hash is taken, the file is not copied).
The manifest does NOT list itself and does NOT claim to cover the end or FINAL files, which do not exist yet.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/manifest_evidence_r8m1a4audit2.py
Refuses if SHA256SUMS_M1a4AUDIT2.txt exists (U17).
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
RAW = os.path.join(EVR, "callseq_r8m1a4_r3")
OUT = os.path.join(EV, "SHA256SUMS_M1a4AUDIT2_R2.txt")
# files that change after the record (every safe_run or prerun call appends to them): not checkable, recorded as LIVE
LIVE_FILES = ("PRERUN_CHECKS_R8_M1a4AUDIT2.txt", "safe_run.log")
DEVICE_DIR = os.path.join(REPO, "testing", "d003", "stage_s4r8")
REG_DIRS = [
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3"),
    os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a"),
]
UNIT_FILES = ("events.tsv", "summary.json", "gdb.stdout.txt", "gdb.stderr.txt")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return os.path.relpath(path, REPO)


def collect():
    entries = []  # (rel_path, sha256, kind)
    # 1. the 198 formal runs
    for uid in sorted(os.listdir(RAW)):
        ud = os.path.join(RAW, uid)
        if not os.path.isdir(ud):
            continue
        for f in UNIT_FILES:
            p = os.path.join(ud, f)
            if not os.path.isfile(p):
                raise SystemExit("REFUSED: formal run file missing: %s" % p)
            entries.append((rel(p), sha256_file(p), "FORMAL_RUN"))
    # 2. first and partial call-sequence runs (directories present in the evidence tree)
    for d in ("callseq_r8m1a4", "callseq_r8m1a4_r2"):
        base = os.path.join(EVR, d)
        if os.path.isdir(base):
            for root, _dirs, files in os.walk(base):
                for f in sorted(files):
                    if f in UNIT_FILES:
                        p = os.path.join(root, f)
                        entries.append((rel(p), sha256_file(p), "FIRST_OR_PARTIAL_RUN"))
    # 3. the A and B raw logs of the nine F3 combinations
    add = os.path.join(EVR, "additions_r8m1a4")
    for name in sorted(os.listdir(add)):
        if name.startswith("a1map_F3_") or name.startswith("b_map_F3_"):
            d = os.path.join(add, name)
            for f in sorted(os.listdir(d)):
                p = os.path.join(d, f)
                if os.path.isfile(p):
                    entries.append((rel(p), sha256_file(p), "AB_RAW_LOG"))
    # 4. expectation, source and driver tables (only the files of the registry directories named by the round)
    for d in REG_DIRS:
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isfile(p) and f.endswith((".tsv", ".txt")):
                entries.append((rel(p), sha256_file(p), "REGISTRY_OR_EXPECT"))
    # 5. device scripts of the round (hash only)
    for f in sorted(os.listdir(DEVICE_DIR)):
        p = os.path.join(DEVICE_DIR, f)
        if os.path.isfile(p) and "r8m1a4audit2" in f:
            entries.append((rel(p), sha256_file(p), "DEVICE_SCRIPT"))
    # 6. the round evidence directory: expectations, rules, outputs.  LIVE files (grown by every safe_run or prerun
    #    call) are excluded here and recorded in the LIVE file instead (see LIVE_FILES).
    for f in sorted(os.listdir(EV)):
        p = os.path.join(EV, f)
        if not os.path.isfile(p) or f in LIVE_FILES or f.startswith("SHA256SUMS") or f.startswith("LIVE_SNAPSHOT"):
            continue
        entries.append((rel(p), sha256_file(p), "ROUND_EVIDENCE"))
    return entries


def live_lines():
    """The two safe_run.log files are live: they change with every safe_run call.  They are NOT in the checkable manifest;
    their length and hash are written as LIVE records (a snapshot, not a permanent hash)."""
    out = []
    for p in (os.path.join(EVR, "safe_run.log"), os.path.join(EV, "safe_run.log"),
              os.path.join(EV, "PRERUN_CHECKS_R8_M1a4AUDIT2.txt")):
        if os.path.isfile(p):
            out.append("LIVE\t%s\tlength=%d\tsha256=%s" % (rel(p), os.path.getsize(p), sha256_file(p)))
    return out


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: manifest_evidence_r8m1a4audit2.py")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    entries = collect()
    seen = set()
    lines = []
    for p, h, kind in entries:
        if p in seen:
            continue
        seen.add(p)
        # standard "sha256  path" form, so that sha256sum -c can check every line
        lines.append("%s  %s" % (h, p))
    live_path = os.path.join(EV, "LIVE_SNAPSHOT_R8_M1a4AUDIT2_R2.txt")
    if os.path.exists(live_path):
        raise SystemExit("REFUSED: exists (U17): %s" % live_path)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(live_path, "x", encoding="utf-8") as fh:
        fh.write("\n".join(live_lines()) + "\n")
    print("manifest entries=%d -> %s; live records -> %s" % (
        len(lines), os.path.relpath(OUT, REPO), os.path.relpath(live_path, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
