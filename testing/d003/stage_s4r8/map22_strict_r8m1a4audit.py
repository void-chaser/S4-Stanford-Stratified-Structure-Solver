#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit), task section 5: strict re-association of the 22 additions to the nine combinations.

New file.  The old mapping ADDITIONS_MAPPING_22_R8_M1a4.tsv is read only and is not modified.  Its status column was
written from the old summarizer (hard-coded n_values, E8-64) and is therefore NOT used as evidence here.

For each of the 22 rows, the mapped combination(s) are read from the old table's mapped_combo column (the mapping
itself is kept; only the verdict is re-derived).  The verdict comes from the strict recheck output
ADDITIONS_STRICT_R8_M1a4AUDIT.tsv (task section 5 rule: combination missing, unknown, or MISMATCH never gives
MAPPING_VERIFIED).  A row maps to every combination named in its mapped_combo column; the row is verified only if
every named combination is MATCH in the strict output.

Output: ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv in the evidence directory argument.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
OLD_MAP = os.path.join(EVB, "ADDITIONS_MAPPING_22_R8_M1a4.tsv")
STRICT = os.path.join(EVB, "m1a4audit", "additions_strict_r2", "ADDITIONS_STRICT_R8_M1a4AUDIT.tsv")

# The nine combinations, in the notation of the strict output: section + combo
KNOWN_COMBOS = {("A", "closed2d-ng1"), ("A", "fft-ng5"), ("A", "kottke-ng5"),
                ("B", "fft-ng1"), ("B", "fft-ng5"), ("B", "fft-ng9"),
                ("B", "kottke-ng1"), ("B", "kottke-ng5"), ("B", "kottke-ng9")}


def read_rows(path):
    hdr = None
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if hdr is None:
                hdr = cols
                continue
            if len(cols) != len(hdr):
                raise SystemExit("REFUSED: column count %d != %d at %s:%d" % (len(cols), len(hdr), path, n))
            out.append((n, dict(zip(hdr, cols))))
    return out


def expand_combos(mapped):
    """Return the list of (section, combo) named by a mapped_combo string.

    A single name ('fft-ng5') is resolved to its section by membership in KNOWN_COMBOS (A names are the three
    closed2d/fft/kottke A combos, B names are the six fft/kottke B combos).  A row that names several combinations
    separated by '|' is split.  A string that is not a known combination (for example 'fft/kottke x NG1,5,9'
    style text) is expanded only through the explicit list below; any other text is refused.
    """
    named = []
    for part in mapped.split("|"):
        p = part.strip()
        if p in ("closed2d-ng1", "fft-ng1", "fft-ng5", "fft-ng9", "kottke-ng1", "kottke-ng5", "kottke-ng9"):
            # the section (A or B) is supplied by the row's section column; fft-ng5 and kottke-ng5 exist in both
            named.append(p)
        elif p == "fft/kottke x NG1,5,9":
            named.extend(["fft-ng1", "fft-ng5", "fft-ng9", "kottke-ng1", "kottke-ng5", "kottke-ng9"])
        else:
            raise SystemExit("REFUSED: unrecognised combination text: %r" % p)
    return named


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: map22_strict_r8m1a4audit.py OUTDIR")
    out_dir = argv[1]
    out_path = os.path.join(out_dir, "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv")
    if os.path.exists(out_path):
        raise SystemExit("REFUSED: exists (U17): %s" % out_path)

    old = read_rows(OLD_MAP)
    if len(old) != 22:
        raise SystemExit("REFUSED: old mapping has %d rows, expected 22" % len(old))
    strict = read_rows(STRICT)
    verdict = {}
    for n, r in strict:
        key = (r["section"], r["combo"])
        if key in verdict:
            raise SystemExit("REFUSED: duplicate strict key %s" % (key,))
        verdict[key] = r["verdict"]
    if set(verdict) != KNOWN_COMBOS:
        raise SystemExit("REFUSED: strict output does not cover the nine combinations: %s" % sorted(verdict))

    out_rows = []
    counts = {}
    for n, r in old:
        section = r["section"]
        names = expand_combos(r["mapped_combo"])
        # every named combination must exist in the strict output under the row's own section.
        # The 'section' column of the old row names the section ('A-...' or 'B-...' label family).
        row_section = "A" if section.startswith("A") or r["item"].startswith("A-") else "B"
        results = []
        for name in names:
            key = (row_section, name)
            if key not in verdict:
                results.append("MISSING:%s/%s" % (row_section, name))
            else:
                results.append("%s/%s=%s" % (row_section, name, verdict[key]))
        all_match = all(x.endswith("=MATCH") for x in results) and not any(x.startswith("MISSING") for x in results)
        status = "MAPPING_VERIFIED_STRICT" if all_match else "NOT_VERIFIED"
        counts[status] = counts.get(status, 0) + 1
        out_rows.append((r["item"], r["tree"], r["point_or_combo"], r["injection"], r["mapped_combo"],
                          row_section, ";".join(results), status, "old_status=%s" % r["status"]))

    with open(out_path, "x", encoding="utf-8") as fh:
        fh.write("item\ttree\tpoint_or_combo\tinjection\tmapped_combo\tsection_used\tstrict_verdicts\tstatus_strict\told_status_not_used\n")
        for row in out_rows:
            fh.write("\t".join(str(x) for x in row) + "\n")

    print("MAPPING22_STRICT rows=%d counts=%s" % (len(out_rows), sorted(counts.items())))
    return 0 if counts.get("MAPPING_VERIFIED_STRICT", 0) == len(out_rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
