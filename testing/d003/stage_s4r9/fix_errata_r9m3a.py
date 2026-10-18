#!/usr/bin/env python3
# fix_errata_r9m3a.py -- correct one line reference inside the errata block appended by append_errata_r9m3a.py.
# usage: python3 -I -B testing/d003/stage_s4r9/fix_errata_r9m3a.py ERRATA_9.txt
# Guard: the file must equal the post-append sha256 and the old text must occur exactly once.
import sys, hashlib

EXPECT_SHA = "13c090fe9174d3b9bdf7a7f49390b437c060b0a7e8ee6b1de1bfbb36a47e0512"
EXPECT_BYTES = 38070
OLD = "L155,L156,L157,L158,L160,L169"
NEW = "L155,L156,L157,L158,L160"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/p05/registries/s4r9/ERRATA_9.txt"
    old = open(p, "rb").read()
    if len(old) != EXPECT_BYTES or sha256_bytes(old) != EXPECT_SHA:
        print("HARD_STOP: unexpected current file bytes=%d sha=%s" % (len(old), sha256_bytes(old)))
        return 2
    text = old.decode("utf-8")
    if text.count(OLD) != 1:
        print("HARD_STOP: anchor count %d != 1" % text.count(OLD))
        return 2
    new_text = text.replace(OLD, NEW)
    new_b = new_text.encode("utf-8")
    with open(p, "wb") as fh:
        fh.write(new_b)
    print("FIXED one line reference: %s -> %s" % (OLD, NEW))
    print("BEFORE bytes=%d sha=%s" % (len(old), sha256_bytes(old)))
    print("AFTER  bytes=%d sha=%s" % (len(new_b), sha256_bytes(new_b)))
    print("PREFIX_PRESERVED=%s" % (new_b.startswith(old[:len(old) - 200]),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
