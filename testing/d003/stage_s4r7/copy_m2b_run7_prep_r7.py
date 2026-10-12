#!/usr/bin/env python3
"""P05-S4 R7 cont8 ADD1 step 1 (U75c): copy the run7 prep files to registries/s4r7/ (new file).

Rule (U75c): if the destination exists, the copy succeeds only when its sha256 equals the source sha256; the outcome is logged as
"already present, sha256 equal".  A sha256 mismatch refuses.  A missing destination is copied, the copy is verified byte for byte,
and logged as "copied".  The log is written to the manifest SHA256SUMS_M2b_run7prep.txt (with UTC times).
The older copy scripts are not edited (their manifests are committed).

Usage (through safe_run, absolute EVDIR):  python3 -I -B testing/d003/stage_s4r7/copy_m2b_run7_prep_r7.py EVDIR
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
    "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv",
    "ADD_V3_VS_V2_DIFF.txt",
    "DRYRUN_R7_M2b_run7_final.txt",
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
        raise SystemExit("usage: copy_m2b_run7_prep_r7.py EVDIR")
    ev = argv[1]
    if not os.path.isabs(ev):
        raise SystemExit("REFUSED: EVDIR must be absolute")
    manifest = os.path.join(DEST, "SHA256SUMS_M2b_run7prep.txt")
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
