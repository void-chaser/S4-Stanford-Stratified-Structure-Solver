#!/usr/bin/env python3
# reuse_check_r8m2a2_R2.py -- P05-S4 R8 M2a2: Revision 2 of reuse check (Part C1).
# Completely replaces R1: reads recorded sha256 from actual registry files with exact line numbers.
# Output: checkpoints/p05/evidence/p05-s4r8/m2a2/REUSE_CHECK_R8_M2a2_R2.tsv
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "REUSE_CHECK_R8_M2a2_R2.tsv")

ITEMS = [
    # (artifact, path, recorded_sha, source_file, source_line)
    ("F3-dbg-lib",
     "checkpoints/p05/evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a",
     "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a",
     "checkpoints/p05/registries/s4r8/BUILD_R8.tsv", 4),
    ("F3-plain-lib",
     "checkpoints/p05/evidence/p05-s4r8/build_r8/F3-plain/build/libS4.a",
     "abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de",
     "checkpoints/p05/registries/s4r8/BUILD_R8.tsv", 3),
    ("driver-init-F3",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/init-F3/driver",
     "ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68",
     "checkpoints/p05/registries/s4r8/M1a/DRIVERS_R8_M1a.tsv", 17),
    ("driver-polyinj-F3",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/polyinj-F3/driver",
     "419cfb727932cc8d9417fd3a873c578f2f1f597f57e501041d9dd3b221ad30a9",
     "checkpoints/p05/registries/s4r8/M1a/DRIVERS_R8_M1a.tsv", 18),
    ("driver-r6bstate-F3-dbg",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver",
     "8b269be6e21f7c74fa40a268ed6226e91e481e06000523e8cf0f9942b6e06cdd",
     "checkpoints/p05/registries/s4r8/M1a/DRIVERS_R8_M1a.tsv", 13),
    ("driver-d003-F3-plain",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003-F3-plain/driver",
     "afd4adb303acf06ddb0d34ed5e8a8de211f54d81a2c649ce946bba5c4ff7cb5c",
     "checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv", 2),
    ("driver-d003plan-F3-plain",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003plan-F3-plain/driver",
     "be478d9063e5c49a6d703110bd89875499287f8a5d1a2de97def2ec3df5f2faf",
     "checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv", 3),
    ("driver-seam-seamF-F3",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8/seam-seamF-F3/driver",
     "c691acd71db3d4aabdc08f999058033228513f7049e19c3715720aab55df4ae6",
     "checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv", 6),
    ("driver-seam-fmmret-F3",
     "checkpoints/p05/evidence/p05-s4r8/drivers_r8/seam-fmmret-F3/driver",
     "f7d445cc2a48ef9d7fae2118c3cd3c715bffaff2de89ab795dd74613f2ea585c",
     "checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv", 7),
    ("driver-seam-fmmret-F2",
     "checkpoints/p05/evidence/p05-s4r7/drivers_r7/seam-fmmret-F2/driver",
     "a4061e4c429df6f969993eab72c06a9afdaa2cbcab46535e9ca43851cca05fa6",
     "checkpoints/p05/registries/s4r7/DRIVERS_R7_SEAM.tsv", 4),
]

def sha256_file(p):
    if not os.path.isfile(p):
        return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    if os.path.exists(OUT):
        print("reuse_check_r8m2a2_R2: REFUSED exists (U17): %s" % OUT)
        return 2

    n_total = len(ITEMS)
    n_same = 0
    n_diff = 0
    lines = []
    lines.append("# REUSE_CHECK_R8_M2a2_R2 -- P05-S4 R8 M2a2 section 4.1 & Part C1 revision")
    lines.append("# columns: artifact\tpath\trecorded_sha256\tactual_sha256\tverdict\tsource_file\tsource_line")

    for art, rel_p, rec_sha, src_f, src_line in ITEMS:
        full_p = os.path.join(REPO, rel_p)
        act_sha = sha256_file(full_p)
        if rec_sha == "":
            verdict = "UNRESOLVED"
            n_diff += 1
        elif act_sha == rec_sha:
            verdict = "SAME"
            n_same += 1
        else:
            verdict = "DIFFERENT" if act_sha != "MISSING" else "MISSING"
            n_diff += 1
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%d" % (art, full_p, rec_sha, act_sha, verdict, src_f, src_line))

    lines.append("# SUMMARY: TOTAL=%d SAME=%d DIFFERENT_OR_UNRESOLVED=%d" % (n_total, n_same, n_diff))

    os.makedirs(EV, exist_ok=True)
    with open(OUT, "x", encoding="utf-8") as fh:
        for l in lines:
            fh.write(l + "\n")

    print("reuse_check_r8m2a2_R2: wrote %s; TOTAL=%d SAME=%d DIFF=%d" % (OUT, n_total, n_same, n_diff))
    return 0 if n_diff == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
