#!/usr/bin/env python3
# compact_state_r8m1a5.py -- compacts checkpoints/p05/STATE.md for CONT3b1 (brief section 4).  New file.
# It replaces three over-long lines by short link lines and keeps every other line unchanged.  The removed text is
# already archived verbatim in registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md (written by state_history_r8m1a5.sh).
# It refuses to run unless the archive contains each removed line (byte-for-byte), and it writes the new STATE
# only once, in place, after making a copy in the evidence directory (U17: the copy name must not exist).
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a5")
STATE = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
HIST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "STATE_HISTORY_R8_M1a5.md")
BACKUP = os.path.join(EV, "STATE_BEFORE_COMPACT_R8_M1a5.md")

with open(STATE, encoding="utf-8") as fh:
    lines = fh.read().split("\n")
with open(HIST, encoding="utf-8") as fh:
    hist = fh.read()

# (line index is 0-based; the expected text is matched by its first 40 characters, the full line must be in the archive)
REPLACE = {}
def find_idx(prefix):
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(hits) != 1:
        sys.exit("compact_state: prefix not unique (%d): %s" % (len(hits), prefix))
    return hits[0]

i35 = find_idx("| S4R8 M1a（F3，续3a 审核修正第二部分 r8m1a4audit2，技术停止）")
if lines[i35] not in hist:
    sys.exit("compact_state: archive does not contain line %d verbatim; stop" % (i35 + 1))

REPLACE[i35] = ("| S4R8 M1a（F3，续3a 审核修正第二部分 r8m1a4audit2，技术停止） | 细节见 `P05_S4R8_REPORT_M1a_CONT3a_AUDIT2.md`；原行存 `STATE_HISTORY_R8_M1a5.md`。 |")
# The evidence-location line (line i70) is rewritten only after the round's manifests exist (end of round), not here.

if os.path.exists(BACKUP):
    sys.exit("compact_state: backup exists (U17): " + BACKUP)
with open(BACKUP, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))

new_lines = list(lines)
for idx, txt in REPLACE.items():
    new_lines[idx] = txt
new_text = "\n".join(new_lines)
with open(STATE, "w", encoding="utf-8") as fh:
    fh.write(new_text)
print("compact_state_r8m1a5: replaced %d lines; STATE bytes %d; backup %s" % (
    len(REPLACE), len(new_text.encode("utf-8")), os.path.relpath(BACKUP, REPO)))
