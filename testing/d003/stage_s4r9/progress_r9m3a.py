#!/usr/bin/env python3
# progress_r9m3a.py -- append one progress line to the round evidence directory. New file (r9m3a).
import os, sys, datetime
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m3a")
os.makedirs(EV, exist_ok=True)
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
line = "%s\t%s\n" % (ts, " ".join(sys.argv[1:]))
with open(os.path.join(EV, "PROGRESS_R9M3A.txt"), "a", encoding="utf-8") as fh:
    fh.write(line)
print("PROGRESS " + line.strip())
