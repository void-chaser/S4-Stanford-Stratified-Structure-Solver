#!/usr/bin/env python3
# P05-S4 R8 M2a2: archive/member and final-driver symbol audit for buf hook.
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
LIB = os.path.join(EV, "build", "seam_buf", "build", "libS4.a")
DRIVER = os.path.join(EV, "build", "nan-F3")
OUT = os.path.join(EV, "NM_CHECK_BUF_R8_M2a2_R2.tsv")
SYMBOL = "S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_nm(args):
    p = subprocess.run(["nm"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, check=False)
    return p.returncode, p.stdout, p.stderr


def records(text):
    out = []
    for line in text.splitlines():
        if SYMBOL not in line:
            continue
        # nm -A -C output carries archive(member): followed by either " U name"
        # or "<address> <type> name". Keep full original line to preserve name/member.
        m = re.search(r"\s([A-Za-z?])\s+(.+)$", line)
        if m:
            out.append((m.group(1), m.group(2), line))
        else:
            out.append(("?", "UNPARSED", line))
    return out


def main():
    if os.path.exists(OUT):
        print("REFUSED exists (preserve evidence): %s" % OUT, file=sys.stderr)
        return 2
    rows = [
        "# NM_CHECK_BUF_R8_M2a2_R2 -- static symbol evidence only; no driver execution",
        "# columns: object\tobject_sha256\tkind\tmember\ttype\tfull_symbol_or_nm_line\tcount",
    ]
    for path, label, kinds in ((LIB, "F3-buf-seam archive", ("--undefined-only", "--defined-only")),
                               (DRIVER, "nan-F3 final executable", ("--defined-only",))):
        if not os.path.isfile(path):
            rows.append("MISSING\t%s\t%s" % (label, path))
            continue
        objsha = sha(path)
        for kind in kinds:
            rc, text, err = run_nm(["-A", "-C", kind, path])
            if rc:
                rows.append("ERROR\t%s\t%s\t%s\t%s" % (label, objsha, kind, err.replace("\n", " ")))
                continue
            found = records(text)
            for typ, name, line in found:
                # archive member is the prefix through the colon before nm payload
                member = line.split(":", 1)[0] if ":" in line else "UNKNOWN_MEMBER"
                rows.append("\t".join((label, objsha, kind, member, typ, line, "1")))
            if not found:
                rows.append("\t".join((label, objsha, kind, "-", "ABSENT", SYMBOL, "0")))
    # Explicit totals: undefined archive references vs archive definitions, plus final-driver definitions.
    totals = {}
    for line in rows[2:]:
        cols = line.split("\t")
        if len(cols) >= 7 and cols[0] in ("F3-buf-seam archive", "nan-F3 final executable"):
            key = (cols[0], cols[2])
            totals[key] = totals.get(key, 0) + int(cols[6])
    rows.append("# totals: archive_U=%d archive_defined=%d nan_driver_defined=%d" % (
        totals.get(("F3-buf-seam archive", "--undefined-only"), 0),
        totals.get(("F3-buf-seam archive", "--defined-only"), 0),
        totals.get(("nan-F3 final executable", "--defined-only"), 0)))
    with open(OUT, "x", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
