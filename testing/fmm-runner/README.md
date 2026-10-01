# Verified FMM runner checkpoint

This directory archives the runner and finite acceptance tools accepted by the
fix4 independent review. The 2 delivered scripts, 13 test helpers, before copies,
and input manifest are byte-identical to `/tmp/s4-fix4-AQA9Bd` and the independently
reviewed copies. See PROVENANCE.json and provenance/INDEPENDENT_REVIEW.md.

The before copies here are the frozen fix4 inputs and match the delivered scripts;
they are not the original deficient handoff inputs. `handoff/fmm-runner/inputs`
remains the original task input, not this verified delivery.

Only frozen-manifest path metadata was converted from absolute temporary paths
to relative paths. No runner or test implementation was edited for this checkpoint.
The remaining new files document provenance, checksums, and generated-output exclusions.

## Scope

Final PASS must be a complete line and occur exactly once. WITNESS and each HIT
must independently carry a complete matching branch field. Original classification,
per-attempt checks and baseline behavior are retained. Finite tests also cover
field splitting, real-entry failure propagation, evidence isolation, and manifest
output self-exclusion. This is fake-driver acceptance, not production FMM,
scientific validation, or native memory-safety acceptance.

Frozen SHA256:

- work/run-one.sh: 51e448a88b3d1df9da63a37cefbbac5e4d4dab14c8395514e0844f5d1b9c36f1
- work/fake.sh: f1a0912958d32335ee486dfccda64d8e08acaf85735679eec1260736b3cde6bd

## Reproduce in a new isolated directory

From this directory, verify `sha256sum -c SHA256SUMS`, then copy only the checkpoint
sources to a fresh temporary directory. For example:

```sh
checkpoint_root="$PWD"
runner_replay=$(mktemp -d /tmp/s4-runner-replay-XXXXXX)
cp -p "$checkpoint_root/inputs.sha256" "$checkpoint_root/delivered-frozen.sha256" "$runner_replay/"
cp -rp "$checkpoint_root/work" "$checkpoint_root/before" "$checkpoint_root/tests" "$runner_replay/"
cd "$runner_replay"
ulimit -c 0
bash tests/run-all.sh checkpoint-001
```

No native build or Python extension is used. The suite runs Bash/Python helpers,
fake drivers and 2-second timeout checks. Expected matrix exits are 1 for cases
01–15, 3/INAPPLICABLE for case16, and 0 for cases17–20. The other accepted suites
cover 28 fake variants, 10 regressions, 4 new observations, 3 isolated mutants,
and T1–T8 tool checks. Reusing a run ID must fail instead of replacing evidence.

Generated runs and their logs are deliberately excluded from Git. Original
acceptance/review evidence remains at the paths recorded in PROVENANCE.json.
Do not copy historical experimental trees or stage generated output directories.
