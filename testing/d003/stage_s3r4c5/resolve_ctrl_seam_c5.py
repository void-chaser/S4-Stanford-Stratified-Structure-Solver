#!/usr/bin/env python3
"""P05-S3R4 CONT5 section 3.2: offline resolution of the CTRL_SEAM driver names (U118, ES3R4-29).

Read only.  Runs NO driver and NO check other than the sha256 read of check_driver (inside driver_for).
Imports run_m2b_all_r7 (its module-level code only computes constants; no file is written, no process started; checked
in CONT5 section 3.2).  Prints one TSV table to stdout; the caller (resolve_ctrl_seam_c5.sh) writes it to $EV.

Usage: python3 -I -B testing/d003/stage_s3r4c5/resolve_ctrl_seam_c5.py
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV_R7 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
sys.path.insert(0, os.path.join(REPO, "testing", "d003", "stage_s4r7"))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))

import run_m2b_all_r7 as B  # noqa: E402  imported, not modified; module-level code checked (CONT5 3.2)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    seam = B.load_seam_drivers(EV_R7)
    pts = B.ctrl_seam_points(EV_R7)
    rows = []
    for p in pts:
        registered = p["driver"]
        # the runner's own selection: driver_for(group, request, tree, rec, seam) for CTRL_SEAM (run_m2b_all_r7.py:124-131).
        # driver_for returns (path, expected sha256); the name is recovered from the path it selected, not re-derived.
        drv_path, drv_sha = B.driver_for("CTRL_SEAM", p["request"], p["tree"], {}, seam)
        resolved = os.path.basename(os.path.dirname(drv_path))  # drivers_r7/seam-<name>/driver -> seam-<name>
        resolved = resolved[len("seam-"):] if resolved.startswith("seam-") else resolved
        actual_sha = sha256_file(drv_path) if os.path.isfile(drv_path) else "MISSING"
        sha_ok = "yes" if actual_sha == drv_sha else "no"
        verdict = "AGREE" if registered == resolved else "DISAGREE"
        rows.append([p["point_id"], registered, p["tree"], p["request"], resolved,
                     drv_path, drv_sha, actual_sha, sha_ok, verdict])
    print("\t".join(["point_id", "registered_driver", "tree", "request", "resolved_driver",
                     "driver_path", "recorded_sha256", "actual_sha256", "sha256_match", "registered_vs_resolved"]))
    for r in rows:
        print("\t".join(r))


if __name__ == "__main__":
    main()
