#!/usr/bin/env python3
# verify_registries_r8m1c3.py -- P05-S4 R8 M1c3 registry verification (AGENTS.md 7.1). New file.
# Reads checkpoints/p05/registries/s4r8/M1c/r8m1c3/SHA256SUMS.txt and SHA256SUMS_END.txt; for each listed file, checks
# that it exists in that directory and that its sha256 equals the listed value.  Writes $EV/VERIFY_REGISTRIES_R8_M1c3.txt.
# The file-name paths are relative to the directory (the cause of the earlier failed inline check: wrong base directory).
# Usage: python3 -I -B verify_registries_r8m1c3.py
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3")
OUT = os.path.join(EV, "VERIFY_REGISTRIES_R8_M1c3.txt")
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)

lines = []
bad = 0
n = 0
for lst in ("SHA256SUMS.txt", "SHA256SUMS_END.txt"):
    p = os.path.join(DST, lst)
    if not os.path.isfile(p):
        lines.append("MISSING_LIST\t%s" % lst)
        bad += 1
        continue
    with open(p, encoding="utf-8") as fh:
        for l in fh:
            l = l.strip()
            if not l:
                continue
            sha, name = l.split(None, 1)
            n += 1
            fp = os.path.join(DST, name)
            if not os.path.isfile(fp):
                lines.append("MISSING\t%s\t%s" % (lst, name))
                bad += 1
                continue
            got = hashlib.sha256(open(fp, "rb").read()).hexdigest()
            ok = (got == sha)
            lines.append("%s\t%s\t%s" % ("OK" if ok else "BAD", lst, name))
            if not ok:
                bad += 1
lines.append("ENTRIES=%d BAD=%d" % (n, bad))
lines.append("RESULT=%s" % ("ALL_OK" if bad == 0 else "FAILED"))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("RESULT=%s ENTRIES=%d BAD=%d" % ("ALL_OK" if bad == 0 else "FAILED", n, bad))
sys.exit(0 if bad == 0 else 1)
