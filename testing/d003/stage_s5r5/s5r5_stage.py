#!/usr/bin/env python3
# s5r5_stage.py -- build the staging roots for the R5 end-gate rehearsal (U388: only root paths differ).
# Copies the round artifacts into $EV/shakedown/p05 (staged checkpoints/p05 root) and $EV/shakedown/ev
# (staged evidence root) with metadata preserved, and records sha256 of every staged file. Nothing outside
# the round evidence directory is written.
import os, sys, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
STAGE = os.path.join(EV, "shakedown")
STAGE_P05 = os.path.join(STAGE, "p05")
STAGE_EV = os.path.join(STAGE, "ev")
TAB = chr(9)
NL = chr(10)

P05_FILES = [
    "STATE.md",
    "P05_S5R5_REPORT.md",
    "P05_S5_SIGNOFF_DRAFT_v3.md",
    "P05_S5_SIGNOFF_DRAFT_v2.md",
    "P05_S5_SIGNOFF_DRAFT.md",
    "P05_S5R4_REPORT.md",
    "registries/RULINGS.tsv",
    "registries/s5r2/ERRATA_S5.txt",
]
EV_FILES = [
    "GATE_S5R5_start.txt",
    "TMP_SNAPSHOT_S5R5.tsv",
    "RULINGS_APPEND_S5R5.tsv",
    "ERRATA_APPEND_S5R5.tsv",
    "CHECKER_SWEEP_S5R5.tsv",
    "RECHECK_STAGING_S5R5.tsv",
    "POSCTRL_RECHECK_STAGING_S5R5.txt",
    "POSCTRL_GATE_S5R5.txt",
    "READINESS_S5R5.tsv",
    "FROZEN_SCRIPTS_S5R5.tsv",
]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    if sha_f(src) != sha_f(dst):
        raise SystemExit("HARD_STOP staged copy mismatch: " + os.path.relpath(dst, REPO))


def main():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE_P05)
    os.makedirs(STAGE_EV)
    rows = []
    for rel in P05_FILES:
        cp(os.path.join(P05, rel), os.path.join(STAGE_P05, rel))
        rows.append(("p05", rel, sha_f(os.path.join(P05, rel))))
    reg5 = os.path.join(P05, "registries/s5r5")
    for root, dirs, files in os.walk(reg5):
        for f in sorted(files):
            src = os.path.join(root, f)
            rel = os.path.relpath(src, P05)
            cp(src, os.path.join(STAGE_P05, rel))
            rows.append(("p05", rel, sha_f(src)))
    for rel in EV_FILES:
        src = os.path.join(EV, rel)
        if not os.path.isfile(src):
            if rel == "POSCTRL_GATE_S5R5.txt":
                # produced by the gate positive-control run, which itself needs a staging tree; the final
                # staging tree is rebuilt after the positive control (the gate never reads this file's absence
                # differently -- it is a normal check input in both runs once the final tree exists).
                print("NOTE staging source not yet produced: " + rel)
                continue
            print("HARD_STOP missing staging source: " + rel)
            return 2
        cp(src, os.path.join(STAGE_EV, rel))
        rows.append(("ev", rel, sha_f(src)))
    out = os.path.join(EV, "STAGED_FILES_S5R5.tsv")
    body = ["# STAGED_FILES_S5R5.tsv -- files copied into the staging roots for the R5 end-gate rehearsal",
            "# stage_p05=" + os.path.relpath(STAGE_P05, REPO),
            "# stage_ev=" + os.path.relpath(STAGE_EV, REPO),
            TAB.join(["root", "rel_path", "sha256"])]
    for r in rows:
        body.append(TAB.join(r))
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("STAGED p05=%d ev=%d total=%d" % (len([r for r in rows if r[0] == "p05"]),
                                            len([r for r in rows if r[0] == "ev"]), len(rows)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
