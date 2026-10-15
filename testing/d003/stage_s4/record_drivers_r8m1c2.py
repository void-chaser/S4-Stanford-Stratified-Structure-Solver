#!/usr/bin/env python3
# record_drivers_r8m1c2.py -- append one record line per driver (sha256) to DRIVER_RUN_RECORD_R8_M1c2.tsv.
# Called by run_m1c_r8m1c2.sh immediately before and after each runner/judge call.
# Usage: python3 -I -B record_drivers_r8m1c2.py TREE TAG    (TREE is F2 or F3; TAG names the call site)
import hashlib, os, sys, time

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
EVROOT = os.path.join(REPO, "checkpoints", "p05", "evidence")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

DRIVERS = {
    "F2": [
        ("r6bstate-F2-dbg", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bstate-F2-dbg", "driver")),
        ("r6bseam-seamF-F2", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bseam-seamF-F2", "driver")),
        ("r6bseam-fmmret-F2", os.path.join(EVROOT, "p05-s4r7", "drivers_r7", "r6bseam-fmmret-F2", "driver")),
    ],
    "F3": [
        ("r6bstate-F3-dbg", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bstate-F3-dbg", "driver")),
        ("r6bseam-seamF-F3", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bseam-seamF-F3", "driver")),
        ("r6bseam-fmmret-F3", os.path.join(EVROOT, "p05-s4r8", "drivers_r8m1", "r6bseam-fmmret-F3", "driver")),
    ],
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


tree, tag = sys.argv[1], sys.argv[2]
out = os.path.join(EV, "DRIVER_RUN_RECORD_R8_M1c2.tsv")
new = not os.path.isfile(out)
with open(out, "a", encoding="utf-8") as fh:
    if new:
        fh.write("utc\ttree\ttag\tdriver_name\tsha256\n")
    for name, path in DRIVERS[tree]:
        fh.write("%s\t%s\t%s\t%s\t%s\n" % (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), tree, tag, name,
            sha256_file(path) if os.path.isfile(path) else "MISSING"))
print("RECORDED %s %s" % (tree, tag))
