#!/usr/bin/env python3
# relr3_registry.py -- copy the REL-R3 small tables from the round evidence directory to
# checkpoints/p05/registries/rel-r3/ and write the registry SHA256SUMS.txt (AGENTS.md section 7.1).
# Every copy is verified against the evidence original (sha256) after it is made.  The formal end gate
# file GATE_RELR3_end.txt is added by a later invocation after the gate runs (commit (ii)).
import os, sys, hashlib, shutil, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
REG = os.path.join(REPO, "checkpoints/p05/registries/rel-r3")
PREGATE = ["GATE_RELR3_start.txt", "PREREG_RELR3.tsv", "PREREG_RELR3.tsv.sha256.txt",
           "PUSH_PLAN_RELR3.tsv", "PUSH_LOG_RELR3.tsv", "PUBLISH_AUDIT_RELR3.tsv",
           "PUBLISH_VOLUME_RELR3.tsv", "PUBLISH_REMOTE_RELR3.tsv", "REMOTE_BEFORE_RELR3.tsv",
           "REMOTE_AFTER_RELR3.tsv", "REMOTE_CLONE_RELR3.tsv", "PR_RELR3.tsv", "V_RELR3.tsv",
           "EVIDENCE_BACKUP_PLAN_RELR3.md", "RULINGS_APPEND_RELR3.tsv",
           "TMP_SNAPSHOT_RELR3.tsv", "TMP_SNAPSHOT_RELR3_end.tsv"]
OPTIONAL = ["ERRATA_RELR3.txt"]
EXTRA_AFTER_GATE = ["GATE_RELR3_end.txt"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(REG, exist_ok=True)
    items = []
    names = [n for n in PREGATE if os.path.isfile(os.path.join(EV, n))]
    missing = [n for n in PREGATE if n not in names]
    if missing:
        raise SystemExit("HARD_STOP missing evidence file(s): " + ",".join(missing))
    for n in OPTIONAL:
        if os.path.isfile(os.path.join(EV, n)):
            names.append(n)
    for n in EXTRA_AFTER_GATE:
        if os.path.isfile(os.path.join(EV, n)):
            names.append(n)
    for name in names:
        src = os.path.join(EV, name)
        dst = os.path.join(REG, name)
        shutil.copyfile(src, dst)
        if sha_f(dst) != sha_f(src):
            raise SystemExit("HARD_STOP copy sha mismatch: " + name)
        items.append(name)
    lines = ["# SHA256SUMS.txt -- P05 delivery round REL-R3 registry (copies verified against the evidence originals)",
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
