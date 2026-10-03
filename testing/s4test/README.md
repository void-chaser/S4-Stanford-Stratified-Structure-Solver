# S4 Python binding — test suite

This directory holds the layered test suite for the S4 Python extension.  It is
deliberately separate from `testing/test_python_binding.py` (the four original
smoke tests, which are still valid and still run).

## Quick start

From a clean checkout on Linux:

```sh
make S4_pyext PYTHON=python3                       # build the extension in-place
PYTHONPATH="$PWD:$PWD/testing/s4test" \
    python3 -m unittest discover -s testing/s4test -p 'test_*.py' -v
```

`make test` wraps both the original smoke tests and this suite (see the
`test` target in the top-level `Makefile`).

## Design

### Isolation for crash-prone calls

Parts of the binding can **abort the process** (SIGABRT from `free()`) rather
than raising a Python exception.  A normal `unittest` run cannot survive that:
the interpreter dies and every remaining test result is lost.

`common.run_isolated(case)` therefore runs a probe from `isolation_cases.py` in
a **separate interpreter** and classifies the outcome as one of:

| verdict | meaning |
|---|---|
| `ok` | probe returned normally |
| `exception` | probe raised a Python exception (recoverable, expected for invalid input) |
| `crash` | child died from a signal — a native fault in the extension |
| `timeout` | child exceeded the time budget |

This is what makes a native memory bug a *test failure* instead of a lost run.

### Independent analytic reference

`analytic.py` implements Fresnel coefficients and a characteristic-matrix
(transfer-matrix) solver using only `math`/`cmath`.  It never imports S4, so
agreement between it and S4 is meaningful rather than circular.

`analytic.py` is self-validating: with zero-thickness layers the TMM must
reproduce the closed-form Fresnel result exactly, and `R + T == 1` for lossless
media.  Run that check with:

```sh
PYTHONPATH=testing/s4test python3 testing/s4test/selftest_analytic.py
```

Current worst-case agreement: `|TMM - Fresnel| < 6e-16`, `|R + T - 1| < 5e-16`.

### Sign conventions

These were established empirically and are relied on by every test:

* `GetPowerFlux(layer, z)` returns `(forward, backward)`, both **signed** fluxes
  along `+z`.  In the incidence layer `backward` is negative.
* Therefore `R = -backward.real / forward.real` and, in the exit layer,
  `T = forward.real / incident.real`.
* `GetAmplitudes(layer, z)` returns `(forward_coeffs, backward_coeffs)`; each is
  of length `2 * n_G` because the x and y coefficients are interleaved per
  order.  The `[0]`-th entry of the backward tuple in the incidence layer equals
  Fresnel's amplitude `r` — asserted in
  `test_python_api.OutputApiTests.test_reflected_amplitude_matches_fresnel`.
* `GetReciprocalLattice()` returns the rows of the inverse of the lattice
  matrix, in units of `1/a` and **not** multiplied by `2*pi`.

### Tolerances

| bound | used for |
|---|---|
| `1e-12` | identities that hold exactly in arithmetic (power conservation, analytic amplitude comparisons) |
| `1e-6` | comparisons that cross numerical routes or involve discretisation |

## Files

| file | purpose |
|---|---|
| `analytic.py` | Fresnel + transfer-matrix reference, no S4 import |
| `selftest_analytic.py` | proves `analytic.py` itself is correct |
| `common.py` | stack builder, `(R, T)` extraction, subprocess isolation helper |
| `isolation_cases.py` | the probes executed under isolation |
| `test_python_api.py` | build/import, modelling API, outputs, invalid input, isolated robustness |

## Current numerical boundary

At an exact diffraction cutoff, the retained interface system can become
singular. The solver reports a `RuntimeError` when it detects a zero pivot.
Some cutoff cases reach flux evaluation without a zero pivot; a non-finite flux
is now reported as a distinct error. 安全报错，精确截止点物理解未完成。 `test_cutoff_safety.py` checks that the result
is either the independent Fresnel value or an explicit error, and that changing
frequency after a failed solve works. General basis-size comparisons use a
frequency away from the cutoffs; they do not stand in for the cutoff tests.

D4 (Interpolator) and D8 (Lua Regression Harness) have been fully fixed and verified.

## Fixed defects guarded by this suite

**`Clone()` used to abort the interpreter** with `free(): invalid pointer`.
`S4_Simulation_Clone` aliased heap blocks between the original and the clone:
`memcpy` copied `n_layers`/`n_layers_alloc` while `layer` was reallocated, `G`
and `kx` (with `ky == kx + n_G`) were shared, pattern polygon vertices were
shared, and `Simulation_SetExcitationType` freed the borrowed `exc.layer`
pointer. Two regression tests now guard it:
`test_python_api.IsolatedRobustnessTests.test_clone_and_destroy_both_objects` and
`..._test_clone_outliving_the_original`.

> When validating a change to `S4/S4.cpp`, rebuild the extension from scratch
> (`rm -rf build S4*.so && make && make S4_pyext`). During development a stale
> `S4.cpython-*.so` made a fixed build appear broken; `make` does not relink the
> extension unless the archive changes.

## Not covered yet

* A physical limiting solution at an exact diffraction cutoff.
* `SolveInParallel` under an actual MPI build.
* The `GetLayerZIntegral` / `GetStressTensorIntegral` physical interpretation.

## Lua Regression Harness

The Lua regression harness (`testing/runtests.sh` and `testing/numdiff`) has been fixed and is fully operational. It now properly detects missing files, non-numeric outputs, row/column mismatches, and numerical drift. The negative test behaviors have been verified.

**Note**: The three `.txt` reference files (e.g., `examples/simple/simple.txt`) used by the Lua harness are just repeatability snapshots of the current solver, not independent physical benchmarks.


---

## Status in this repository

Single entry point::

    make test          # rebuild core + extension + Lua frontend, run everything
    make test-fast     # analytic reference self-check only (no build, <1 s)
    make test-all      # `make test`, then rebuild build/S4 and run the suite again

Measured on this checkout (Ubuntu 26.04, Python 3.14.4, GCC 15.2.0, 16 cores):

| stage | result | time |
|---|---|---|
| rebuild from source (`rm -rf build`, `make S4_pyext`, `make build/S4`) | ok | ~8 s |
| original smoke tests (`testing/test_python_binding.py`) | 4 tests, OK | <0.1 s |
| this suite (`testing/s4test`) | 122 tests, OK | ~13 s |
| analytic reference self-check | 8 checks, PASS | <0.1 s |

### `make test-python` rebuilds from source on purpose

`make S4_pyext` links against an existing `$(OBJDIR)/libS4.a`, and
`setup.py build_ext` will reuse its own stale object file if timestamps look
plausible. Together those let an edit to `S4.cpp` appear to have no effect, which
is the one failure mode a test runner must not have. `test-python` therefore
removes `$(OBJDIR)` and any `S4*.so` before building.

That this actually works was verified behaviourally, not by timestamps:

| step | two-layer R | interpretation |
|---|---|---|
| edit `S4.cpp` to disable the two-layer route, do **not** rebuild | 0.111111111111 | stale extension still loaded |
| `make test-python` | **-0.000000000000** | edit took effect; suite reported 42 failures |
| revert and rebuild | 0.111111111111 | 122/122 OK again |

### Regenerating the regression baseline

`testing/s4test/regression_data.json` is a hand-reviewable 10-row baseline. It is
**never** updated automatically: a baseline that rewrites itself cannot detect a
regression.

To regenerate it deliberately, from the repository root::

    PYTHONPATH="$PWD" python3 testing/s4test/gen_regression_data.py

which rewrites the JSON from the analytic implementation plus one measured
S4-only row. Then confirm the suite still agrees::

    PYTHONPATH="$PWD:$PWD/testing/s4test" \
        S4_TEST_REPO_ROOT="$PWD" \
        python3 -m unittest test_regression_baseline -v

`test_regression_baseline.py` checks two separate things: that every row replays
against the current build, and that the analytic reference it names really does
produce the stored value. The second check is what stops a row from being
recorded off a buggy build and then passing forever.

### Lua-dependent tests

`test_lua_python_cross.py` and `test_two_layer_interface.TwoLayerLuaFrontendTests`
need the Lua frontend at `build/S4`. `make test-python` now builds it, so they
run as part of `make test`. They fail loudly rather than skipping when it is
missing, because a silently skipped cross-check is indistinguishable from a
passing one.
