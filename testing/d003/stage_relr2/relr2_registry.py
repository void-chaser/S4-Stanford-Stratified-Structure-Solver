#!/usr/bin/env python3
# relr2_registry.py -- copy the REL-R2 small tables from the round evidence directory to
# checkpoints/p05/registries/rel-r2/ and write the registry SHA256SUMS.txt (AGENTS.md section 7.1).
# Every copy is verified against the evidence original (sha256) after it is made.
# The formal end gate file GATE_RELR2_end.txt is added by a later invocation after the gate runs.
import os, sys, hashlib, shutil, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
REG = os.path.join(REPO, "checkpoints/p05/registries/rel-r2")
PREGATE = ["GATE_RELR2_start.txt", "PREREG_RELR2.tsv", "PREREG_RELR2.tsv.sha256.txt", "PROD_RELR2.tsv",
           "V_RELR2.tsv", "PUBLISH_VOLUME_RELR2.tsv", "PUBLISH_AUDIT_RELR2.tsv",
           "PUBLISH_REMOTE_RELR2.tsv", "EVIDENCE_BACKUP_RELR2.tsv", "NOREG_PROBE_RELR2.tsv",
           "NOREG_REPEAT_RELR2.tsv", "RULINGS_APPEND_RELR2.tsv", "TMP_SNAPSHOT_RELR2.tsv",
           "TMP_SNAPSHOT_RELR2_end.tsv"]
EXTRA_AFTER_GATE = ["GATE_RELR2_end.txt"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(REG, exist_ok=True)
    items = []
    for name in PREGATE + [x for x in EXTRA_AFTER_GATE if os.path.isfile(os.path.join(EV, x))]:
        src = os.path.join(EV, name)
        if not os.path.isfile(src):
            raise SystemExit("HARD_STOP missing evidence file: " + name)
        dst = os.path.join(REG, name)
        shutil.copyfile(src, dst)
        if sha_f(dst) != sha_f(src):
            raise SystemExit("HARD_STOP copy sha mismatch: " + name)
        items.append(name)
    lines = ["# SHA256SUMS.txt -- P05 delivery round REL-R2 registry (copies verified against the evidence originals)",
             "# Generated " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    for name in items:
        lines.append(sha_f(os.path.join(REG, name)) + "  " + name)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(chr(10).join(lines) + chr(10))
    print("WROTE registry items=%d" % len(items))
    for name in items:
        print("  " + name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
