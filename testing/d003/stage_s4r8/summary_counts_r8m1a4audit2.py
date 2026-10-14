#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2): one summary of the key counts of the round, read from the files.  New file.

Read only.  Writes SUMMARY_COUNTS_R8_M1a4AUDIT2.txt into the round evidence directory.  The report quotes these counts; they
are read from the tables here, not typed by hand.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/summary_counts_r8m1a4audit2.py SUMMARY_COUNTS_R8_M1a4AUDIT2.txt
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
NAME_RE = re.compile(r"^SUMMARY_COUNTS_R8_M1a4AUDIT2\.txt$")


def col_counts(path, col_name, skip_comments=True):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    rows = [ln for ln in lines if ln and not ln.startswith("#")]
    hdr = rows[0].split("\t")
    idx = hdr.index(col_name)
    c = Counter()
    for ln in rows[1:]:
        cols = ln.split("\t")
        if len(cols) > idx:
            c[cols[idx]] += 1
    return c, len(rows) - 1


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: summary_counts_r8m1a4audit2.py SUMMARY_COUNTS_R8_M1a4AUDIT2.txt")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = []

    cfg, n_cfg = col_counts(os.path.join(EV, "CONFIG_CHECK_R8_M1a4AUDIT2_RUN2.tsv"), "status")
    lines.append("CONFIG_CHECK_RUN2 rows=%d %s" % (n_cfg, dict(sorted(cfg.items()))))

    seq, n_seq = col_counts(os.path.join(EV, "SEQCOMPARE_R8_M1a4AUDIT2_RUN1.tsv"), "status")
    lines.append("SEQCOMPARE_RUN1 pairs=%d %s" % (n_seq, dict(sorted(seq.items()))))

    tgt, n_tgt = col_counts(os.path.join(EV, "REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv"), "status")
    lines.append("REQUEST_TARGETS_RUN3 rows=%d %s" % (n_tgt, dict(sorted(tgt.items()))))

    old, n_old = col_counts(os.path.join(EV, "REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv"), "old_reach_status")
    lines.append("OLD_REACH_STATUS rows=%d %s" % (n_old, dict(sorted(old.items()))))

    rec, n_rec = col_counts(os.path.join(EV, "REQUEST_RECON_R8_M1a4AUDIT2_RUN6.tsv"), "recon_status")
    lines.append("RECON_RUN6 rows=%d %s" % (n_rec, dict(sorted(rec.items()))))

    tr, n_tr = col_counts(os.path.join(EV, "TRACER_AUDIT_R8_M1a4AUDIT2_RUN1.tsv"), "status")
    lines.append("TRACER_AUDIT_RUN1 rows=%d %s" % (n_tr, dict(sorted(tr.items()))))

    ad, n_ad = col_counts(os.path.join(EV, "ADDITIONS_STRICT_R8_M1a4AUDIT2_RUN2.tsv"), "status")
    lines.append("ADDITIONS_STRICT_RUN2 rows=%d %s" % (n_ad, dict(sorted(ad.items()))))

    mp, n_mp = col_counts(os.path.join(EV, "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv"), "status")
    lines.append("MAPPING22_STRICT_RUN2 rows=%d %s" % (n_mp, dict(sorted(mp.items()))))

    scope, n_scope = col_counts(os.path.join(EV, "RERUN_SCOPE_R8_M1a4AUDIT2_RUN1.tsv"), "status")
    lines.append("RERUN_SCOPE_RUN1 pairs=%d %s" % (n_scope, dict(sorted(scope.items()))))

    inv, n_inv = col_counts(os.path.join(EV, "INVALID44_R8_M1a4AUDIT2_RUN3.tsv"), "new_status")
    lines.append("INVALID44_RUN3 rows=%d %s" % (n_inv, dict(sorted(inv.items()))))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    for ln in lines:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
