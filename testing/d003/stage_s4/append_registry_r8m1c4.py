#!/usr/bin/env python3
# append_registry_r8m1c4.py -- P05-S4 R8 M1c4 append helper (brief section 3). New file (copied from append_registry_r8m1c3.py; only EV changed to m1c4).
# Appends a built text file to a living registry file, with prefix verification:
#   1. the current file must start with the recorded start bytes (length and sha256 given on the command line);
#   2. the appended text is written after them; the output must still start with the start bytes.
# Refuses (exit 2) if the file is not at the recorded start state, or if the append text is missing/empty.
# Usage: python3 -I -B append_registry_r8m1c4.py TARGET_REL APPEND_FILE START_BYTES START_SHA256
#   TARGET_REL is relative to the repository root.  Appending is the only write; nothing is removed or rewritten.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

if len(sys.argv) != 5:
    raise SystemExit("usage: append_registry_r8m1c4.py TARGET_REL APPEND_FILE START_BYTES START_SHA256")
target = os.path.join(REPO, sys.argv[1])
append_file = sys.argv[2]
start_bytes = int(sys.argv[3])
start_sha = sys.argv[4]

if not os.path.isfile(target):
    raise SystemExit("REFUSED target missing: %s" % target)
if not os.path.isfile(append_file):
    raise SystemExit("REFUSED append file missing: %s" % append_file)
with open(target, "rb") as fh:
    cur = fh.read()
if len(cur) != start_bytes or hashlib.sha256(cur).hexdigest() != start_sha:
    raise SystemExit("REFUSED target is not at recorded start state (bytes=%d)" % len(cur))
with open(append_file, "rb") as fh:
    add = fh.read()
if not add:
    raise SystemExit("REFUSED append text empty")
new = cur + add
if not new.startswith(cur):
    raise SystemExit("INTERNAL prefix check failed")
with open(target, "ab") as fh:
    fh.write(add)
with open(target, "rb") as fh:
    after = fh.read()
ok = after.startswith(cur) and after == new
print("APPENDED target=%s start_bytes=%d added_bytes=%d new_bytes=%d prefix_ok=%s" % (
    sys.argv[1], start_bytes, len(add), len(after), ok))
if not ok:
    raise SystemExit("PREFIX_VERIFY_FAILED")
