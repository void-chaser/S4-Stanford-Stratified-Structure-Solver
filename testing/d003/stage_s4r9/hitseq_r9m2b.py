#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# hitseq_r9m2b.py -- HIT line equivalence between F3 and F4 for 173 regression points (Step S-C).
import hashlib, os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "HITSEQ_F3_F4_R9M2b.tsv")
PREREG_TSV = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M0", "PREREG_REGRESS_F4_R9.tsv")

F3_SEARCH_BASES = [
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2e", "formal", "run"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2c", "run"),
    os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b", "run"),
]

def get_hit_lines(d):
    lines = []
    for fname in ["stdout.txt", "stderr.txt"]:
        p = os.path.join(d, fname)
        if os.path.isfile(p):
            with open(p, "r", errors="replace", encoding="utf-8") as f:
                for line in f:
                    if "S4FMM HIT" in line:
                        clean = re.sub(r"caller=0x[0-9a-fA-F]+", "", line.strip())
                        lines.append(clean)
    return sorted(lines)

def sha_lines(lines):
    text = "\n".join(lines) + ("\n" if lines else "")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

with open(PREREG_TSV, encoding="utf-8") as f:
    raw_lines = [l.strip().split("\t") for l in f if not l.startswith("#") and l.strip()]

header = raw_lines[0]
rows = raw_lines[1:]

results = []
pass1_matches = 0
pass2_matches = 0

for r in rows:
    p_id = r[0]
    f3_id = p_id.replace("-F4", "-F3")
    for ps in [1, 2]:
        pstr = f"pass{ps}"
        f4_dir = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2", "formal", "run", pstr, p_id)
        f3_dir = None
        for b in F3_SEARCH_BASES:
            cand = os.path.join(b, pstr, f3_id)
            if os.path.isdir(cand):
                f3_dir = cand
                break

        if not os.path.isdir(f4_dir):
            sys.exit(f"Error: F4 directory missing: {f4_dir}")
        if not f3_dir:
            sys.exit(f"Error: F3 directory missing for {f3_id} in {pstr}")

        h4 = get_hit_lines(f4_dir)
        h3 = get_hit_lines(f3_dir)
        s4 = sha_lines(h4)
        s3 = sha_lines(h3)

        eq = "IDENTICAL" if s4 == s3 else "DIFFERENT"
        if eq == "IDENTICAL":
            if ps == 1:
                pass1_matches += 1
            else:
                pass2_matches += 1

        rel_f4 = os.path.relpath(f4_dir, REPO)
        rel_f3 = os.path.relpath(f3_dir, REPO)
        results.append((p_id, str(ps), rel_f4, rel_f3, s4, s3, eq))

with open(OUT_TSV, "w", encoding="utf-8") as out:
    out.write("# HITSEQ_F3_F4_R9M2b.tsv -- S4FMM HIT line equivalence between F4 and F3 (Step S-C)\n")
    out.write("point_id\tpass\tf4_dir\tf3_dir\tf4_hit_sha256\tf3_hit_sha256\tequivalence\n")
    for row in results:
        out.write("\t".join(row) + "\n")

total_rows = len(results)
print(f"Total checked rows: {total_rows}")
print(f"Pass 1 identical: {pass1_matches}/173")
print(f"Pass 2 identical: {pass2_matches}/173")

assert total_rows == 346, f"Expected 346 rows, got {total_rows}"
assert pass1_matches == 173, f"Pass 1 had mismatches: {pass1_matches}/173"
assert pass2_matches == 173, f"Pass 2 had mismatches: {pass2_matches}/173"

print(f"ALL_IDENTICAL: 173/173 points match across both passes (346/346). Output written to {OUT_TSV}")
