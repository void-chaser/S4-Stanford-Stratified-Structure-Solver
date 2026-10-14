#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2): copy the small result tables to registries/s4r8/M1a.  New file.

Copies the round's small tables (listed in SOURCES below) from the evidence directory into checkpoints/p05/registries/s4r8/M1a/,
de-duplicated by target name, verifies every copy byte for byte (filecmp, shallow=False), and writes
SHA256SUMS_M1a4AUDIT2.txt into the same directory.  The copy target is refused if it already exists (U17).  Only the
registries/s4r8/M1a directory is written.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/copy_registries_r8m1a4audit2.py
"""
import filecmp
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
SUMS = os.path.join(DST, "SHA256SUMS_M1a4AUDIT2.txt")

# (source file name in the evidence directory, target file name in registries/s4r8/M1a, role)
SOURCES = [
    ("CONFIG_CHECK_R8_M1a4AUDIT2_RUN2.tsv", "CONFIG_CHECK_R8_M1a4AUDIT2.tsv", "config check (section 3, RUN2 after the C7 split)"),
    ("CONFIG_CHECK_R8_M1a4AUDIT2_RUN1.tsv", "CONFIG_CHECK_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv", "config check first run (superseded; kept)"),
    ("SEQCOMPARE_R8_M1a4AUDIT2_RUN1.tsv", "SEQCOMPARE_R8_M1a4AUDIT2.tsv", "F2-F3 event comparison (section 3)"),
    ("SEQCOMPARE_DIFF_R8_M1a4AUDIT2_RUN1.tsv", "SEQCOMPARE_DIFF_R8_M1a4AUDIT2.tsv", "F2-F3 difference table (header only: no DIFFERENT pair)"),
    ("REQUEST_RECON_R8_M1a4AUDIT2_RUN6.tsv", "REQUEST_RECON_R8_M1a4AUDIT2.tsv", "request reconstruction, 1128 rows (section 2)"),
    ("REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv", "REQUEST_TARGETS_R8_M1a4AUDIT2.tsv", "request targets and classification, 1128 rows (section 2)"),
    ("INVALID44_R8_M1a4AUDIT2_RUN3.tsv", "INVALID44_R8_M1a4AUDIT2.tsv", "the 44 INVALID_NOT_REACHED rows, line by line (section 2)"),
    ("DIFF_OLD_NEW_R8_M1a4AUDIT2_RUN3.tsv", "DIFF_OLD_NEW_R8_M1a4AUDIT2.tsv", "old _R3 versus new status, difference table (section 2)"),
    ("TRACER_AUDIT_R8_M1a4AUDIT2_RUN1.tsv", "TRACER_AUDIT_R8_M1a4AUDIT2.tsv", "offline tracer audit of the 198 logs (section 4)"),
    ("SYMQ_R8_M1a4AUDIT2_F2_d003plain.txt", "SYMQ_R8_M1a4AUDIT2_F2_d003plain.txt", "symbol query, F2 d003 driver (section 4)"),
    ("SYMQ_R8_M1a4AUDIT2_F2_r6dnv1.txt", "SYMQ_R8_M1a4AUDIT2_F2_r6dnv1.txt", "symbol query, F2 r6dnv1 driver (section 4)"),
    ("SYMQ_R8_M1a4AUDIT2_F3_r6dnv1.txt", "SYMQ_R8_M1a4AUDIT2_F3_r6dnv1.txt", "symbol query, F3 r6dnv1 driver, P0048 plan breakpoint (section 4)"),
    ("SYMQ_ADDR_R8_M1a4AUDIT2_F2_d003plain.txt", "SYMQ_ADDR_R8_M1a4AUDIT2_F2_d003plain.txt", "breakpoint address versus entry, F2 d003 (section 4)"),
    ("SYMQ_ADDR_R8_M1a4AUDIT2_F3_r6dnv1.txt", "SYMQ_ADDR_R8_M1a4AUDIT2_F3_r6dnv1.txt", "breakpoint address versus entry, F3 r6dnv1 (section 4)"),
    ("SYMQ_DBG_R8_M1a4AUDIT2_F2_d003plain.txt", "SYMQ_DBG_R8_M1a4AUDIT2_F2_d003plain.txt", "DWARF section count, F2 d003 (section 4)"),
    ("SYMQ_DBG_R8_M1a4AUDIT2_F3_r6dnv1.txt", "SYMQ_DBG_R8_M1a4AUDIT2_F3_r6dnv1.txt", "DWARF section count, F3 r6dnv1 (section 4)"),
    ("RERUN_SCOPE_R8_M1a4AUDIT2_RUN1.tsv", "RERUN_SCOPE_R8_M1a4AUDIT2.tsv", "rerun scope table, 99 pairs (section 4)"),
    ("RERUN_PREREG_R8_M1a4AUDIT2.txt", "RERUN_PREREG_R8_M1a4AUDIT2.txt", "rerun pre-registration and design note, not executed (section 4)"),
    ("K0_RULE_R8_M1a4AUDIT2.txt", "K0_RULE_R8_M1a4AUDIT2.txt", "frozen K0 rule, INFLUENCED (section 5)"),
    ("ADDITIONS_STRICT_R8_M1a4AUDIT2_RUN2.tsv", "ADDITIONS_STRICT_R8_M1a4AUDIT2.tsv", "strict additions recheck, field by field (section 5)"),
    ("ADDITIONS_STRICT_R8_M1a4AUDIT2_RUN1.tsv", "ADDITIONS_STRICT_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv", "strict additions recheck first run (superseded: no gdb_rc check; kept)"),
    ("ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv", "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2.tsv", "22-row strict mapping (section 5)"),
    ("ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN1.tsv", "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv", "22-row mapping first run (superseded: gdb_rc field missing; kept)"),
    ("SHA256SUMS_M1a4AUDIT2_R2.txt", "SHA256SUMS_M1a4AUDIT2_EVIDENCE_R2.txt", "evidence manifest copy (2090 lines; the registries copy is listed for reference)"),
    ("GATE_R8_M1a4_AUDIT2_START_A.txt", "GATE_R8_M1a4_AUDIT2_START_A.txt", "phase-A start gate (already copied by the phase-A commit; compared only)"),
    ("GATE_R8_M1a4_AUDIT2_END_A.txt", "GATE_R8_M1a4_AUDIT2_END_A.txt", "phase-A end gate"),
    ("GATE_R8_M1a4_AUDIT2_START_B.txt", "GATE_R8_M1a4_AUDIT2_START_B.txt", "phase-B start gate"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: copy_registries_r8m1a4audit2.py")
    if os.path.exists(SUMS):
        raise SystemExit("REFUSED: exists (U17): %s" % SUMS)
    seen_targets = set()
    lines = []
    copied = 0
    already_present = 0
    for src_name, dst_name, role in SOURCES:
        if dst_name in seen_targets:
            raise SystemExit("REFUSED: duplicate target in the copy list: %s" % dst_name)
        seen_targets.add(dst_name)
        # gate files are written by gate10 into the directory of the round's EV parent (p05-s4r8), not into m1a4audit2
        src_dir = EVR if src_name.startswith("GATE_R8_M1a4_AUDIT2_") else EV
        src = os.path.join(src_dir, src_name)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: source missing: %s" % src)
        # the two GATE copies that the phase-A commit already placed in registries are compared, not copied again
        dst = os.path.join(DST, dst_name)
        if os.path.exists(dst):
            # resumable: an existing target is accepted only if it is byte-identical to its source (never overwritten).
            # A target that differs is refused (U17).  Earlier attempt: the first run had copied the first 25 targets
            # before it stopped at the START_A source line (see the round report, table 2).
            if filecmp.cmp(src, dst, shallow=False):
                lines.append("%s  %s" % (sha256_file(dst), os.path.relpath(dst, REPO)))
                already_present += 1
                continue
            raise SystemExit("REFUSED: exists and differs from its source (U17): %s" % dst)
        shutil.copyfile(src, dst)
        if not filecmp.cmp(src, dst, shallow=False):
            raise SystemExit("FAIL: copy not byte-identical: %s" % dst)
        copied += 1
        lines.append("%s  %s" % (sha256_file(dst), os.path.relpath(dst, REPO)))
    with open(SUMS, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("copy registries: copied=%d already_identical=%d listed=%d -> %s" % (
        copied, already_present, len(lines), os.path.relpath(SUMS, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
