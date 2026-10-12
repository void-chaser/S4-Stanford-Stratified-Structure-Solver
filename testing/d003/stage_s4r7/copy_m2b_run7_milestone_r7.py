#!/usr/bin/env python3
"""P05-S4 R7 cont8 milestone (AGENTS 7; U75c): copy the M2b run7 small tables to registries/s4r7/ (new file).

Same rule as copy_m2b_run7_prep_r7.py (U75c): an existing destination counts as copied only when its sha256 equals the source;
otherwise refuse.  The manifest SHA256SUMS_M2b_run7.txt lists every file with its sha256 and UTC time.
Usage (through safe_run, absolute EVDIR):  python3 -I -B testing/d003/stage_s4r7/copy_m2b_run7_milestone_r7.py EVDIR
"""
import datetime
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
FILES = [
    "RESULTS_R7_CTRL_SEAM_pass1_run7.tsv",
    "RESULTS_R7_CTRL_SEAM_pass2_run7.tsv",
    "RESULTS_R7_G2c_pass1_run7.tsv",
    "RESULTS_R7_G2c_pass2_run7.tsv",
    "RESULTS_R7_G1_pass1_run7.tsv",
    "RESULTS_R7_G1_pass2_run7.tsv",
    "RESULTS_R7_G2a_pass1_run7.tsv",
    "RESULTS_R7_G2a_pass2_run7.tsv",
    "REGRESS_R7_M2b_run7.tsv",
    "M2B_SUMMARY_R7_run7.txt",
    "VALUES_VS_HISTORY_run7.tsv",
    "ENV_DRIFT_R7_M2b_run7.tsv",
    "REPORT_COUNTS_CHECK_FINAL_run7_v2.txt",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: copy_m2b_run7_milestone_r7.py EVDIR")
    ev = argv[1]
    if not os.path.isabs(ev):
        raise SystemExit("REFUSED: EVDIR must be absolute")
    manifest = os.path.join(DEST, "SHA256SUMS_M2b_run7.txt")
    if os.path.exists(manifest):
        raise SystemExit("REFUSED: exists (U17): %s" % manifest)
    log = []
    for name in FILES:
        src = os.path.join(ev, name)
        dst = os.path.join(DEST, name)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: missing source %s" % src)
        src_sha = sha256(src)
        if os.path.exists(dst):
            if sha256(dst) != src_sha:
                raise SystemExit("REFUSED: %s already present with a different sha256 (U75c)" % name)
            log.append("%s  %s  already present, sha256 equal  %s" % (src_sha, name, utc_now()))
            continue
        shutil.copyfile(src, dst)
        if sha256(dst) != src_sha:
            raise SystemExit("REFUSED: copy mismatch %s" % name)
        log.append("%s  %s  copied  %s" % (src_sha, name, utc_now()))
    with open(manifest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
