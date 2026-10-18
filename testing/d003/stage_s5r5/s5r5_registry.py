#!/usr/bin/env python3
# s5r5_registry.py -- assemble checkpoints/p05/registries/s5r5/ (task brief section 7 / AGENTS.md section 7).
# Copies the round's small result tables from the evidence directory, writes REGISTRY_EXPECTED_S5R5.txt and
# SHA256SUMS.txt, and verifies every copied sha. The formal end-gate file is appended after the gate (by the
# appendix script) and the manifest is updated then.
import os, sys, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
REG = os.path.join(P05, "registries/s5r5")
TAB = chr(9)
NL = chr(10)

# rel_path in the registry -> source path
SOURCES = {
    "GATE_S5R5_start.txt": os.path.join(EV, "GATE_S5R5_start.txt"),
    "TMP_SNAPSHOT_S5R5.tsv": os.path.join(EV, "TMP_SNAPSHOT_S5R5.tsv"),
    "RULINGS_APPEND_S5R5.tsv": os.path.join(EV, "RULINGS_APPEND_S5R5.tsv"),
    "ERRATA_APPEND_S5R5.tsv": os.path.join(EV, "ERRATA_APPEND_S5R5.tsv"),
    "r4_final/ERRATA_S5_R4FINAL.txt": os.path.join(REG, "r4_final/ERRATA_S5_R4FINAL.txt"),
    "CHECKER_SWEEP_S5R5.tsv": os.path.join(EV, "CHECKER_SWEEP_S5R5.tsv"),
    "RECHECK_STAGING_S5R5.tsv": os.path.join(EV, "RECHECK_STAGING_S5R5.tsv"),
    "POSCTRL_RECHECK_STAGING_S5R5.txt": os.path.join(EV, "POSCTRL_RECHECK_STAGING_S5R5.txt"),
    "READINESS_S5R5.tsv": os.path.join(EV, "READINESS_S5R5.tsv"),
    "FROZEN_SCRIPTS_S5R5.tsv": os.path.join(EV, "FROZEN_SCRIPTS_S5R5.tsv"),
}
LISTED = [k for k in SOURCES if not k.startswith("r4_final/")] + [k for k in SOURCES if k.startswith("r4_final/")]
LISTED = list(SOURCES.keys())


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(REG, exist_ok=True)
    os.makedirs(os.path.join(REG, "r4_final"), exist_ok=True)
    rows = []
    for rel in LISTED:
        src = SOURCES[rel]
        dst = os.path.join(REG, rel)
        if os.path.realpath(src) != os.path.realpath(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        if not os.path.isfile(dst) or sha_f(src) != sha_f(dst):
            print("HARD_STOP registry copy mismatch: " + rel)
            return 2
        rows.append((rel, sha_f(dst)))
    # REGISTRY_EXPECTED lists every registry file except itself and the manifest
    exp = os.path.join(REG, "REGISTRY_EXPECTED_S5R5.txt")
    body = ["# REGISTRY_EXPECTED_S5R5.txt -- expected registry files and their sha256 (pre-gate set)",
            "# the formal end-gate file is appended after the gate and is listed in SHA256SUMS.txt only",
            TAB.join(["rel_path", "sha256"])]
    for (rel, sha) in rows:
        body.append(TAB.join([rel, sha]))
    open(exp, "w", encoding="utf-8").write(NL.join(body) + NL)
    files = [rel for (rel, _sha) in rows] + ["REGISTRY_EXPECTED_S5R5.txt"]
    sums = ["# SHA256SUMS.txt -- P05-S5 R5 registry (r4_final/ is the frozen R4 errata snapshot)",
            "# the formal end-gate file GATE_S5R5_end.txt is appended after the gate and added below"]
    for rel in files:
        sums.append(sha_f(os.path.join(REG, rel)) + "  " + rel)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(sums) + NL)
    for rel in files:
        if rel in ("SHA256SUMS.txt",):
            continue
    print("REGISTRY files=%d listed=%d expected_rows=%d" % (len(files) + 1, len(files), len(rows)))
    print("WROTE " + os.path.relpath(os.path.join(REG, "SHA256SUMS.txt"), REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
