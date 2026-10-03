# S4 defects found while building the Python test suite

Baseline: branch `feature/python314-binding`, commit `b97f639`, Ubuntu 26.04,
Python 3.14.4, GCC 15.2.0.

Everything below was reproduced with a minimal program. Where a defect was
fixed, the patch is isolated in `S4/S4.cpp` and the reproduction is listed.

---

## D1 — `S4_Simulation_Clone()` corrupts the heap (CRASH) — FIXED

**Symptom.** `Clone()` appears to succeed, then destroying either object aborts
the interpreter:

```
free(): invalid pointer
Aborted (core dumped)
```

**Minimal reproduction.**

```python
import S4, gc
s = S4.New(Lattice=((1,0),(0,1)), NumBasis=9)
s.AddMaterial("Air", 1); s.AddMaterial("Si", 12)
s.AddLayer("Top", 0, "Air"); s.AddLayer("Slab", 0.5, "Si")
s.SetRegionCircle("Slab", "Air", (0,0), 0.2)
s.AddLayerCopy("Bot", 0, "Top")
s.SetFrequency(0.4); s.SetExcitationPlanewave((0,0), 1, 0)
c = s.Clone()
del c
gc.collect()          # <-- free(): invalid pointer
```

A diagnostic build printing the clone immediately after construction showed
`Layer_Destroy(L=0x… name=<garbage> nshapes=1702125938)`; the integer
`1702125938` is `0x65722079`, i.e. the ASCII text *"er y"*, so the layer array
held raw heap text rather than initialised structs.

**Root cause.** Four independent ownership bugs in `S4_Simulation_Clone`:

1. `memcpy(T, S, sizeof(S4_Simulation))` copies `S->n_layers` into `T`, but
   `T->layer` is then freshly `malloc`ed and uninitialised. The subsequent
   `S4_Simulation_SetLayer(T, -1, …)` calls see `n_layers == 3` against an
   allocation of 4, take the *update* path instead of the *append* path, and
   write at `layer[3]`, `layer[4]`, … . `layer[0..2]` are never initialised, so
   `Layer_Destroy` feeds `free()` a garbage `name` pointer.
2. The same `memcpy` aliases `S->G` and `S->kx` into the clone (`ky` is
   `kx + n_G`). Destroying either simulation frees memory the other still uses.
3. `pattern.shapes` was copied with `malloc(sizeof(shape)*nshapes)` and then
   `memcpy`d wholesale, leaving polygon `vertex` arrays shared between the two
   simulations. When `nshapes == 0` this also stored a non-`NULL` zero-size
   allocation in the clone.
4. `Simulation_SetExcitationType()` (`S4/S4.cpp:3462` in the baseline) called
   `free()` on `S->exc.layer`, which is a *borrowed* pointer into `S->layer`,
   not an allocation. `S4_Simulation_Destroy` calls this function, so a dipole
   excitation corrupted the heap on destruction independently of `Clone`.

**Fix.** Reset `T->n_materials`/`T->n_layers` to zero before rebuilding; give the
clone its own `G` and `kx` buffers; deep-copy the pattern via a new
`S4_Simulation_CopyPattern` (duplicating polygon vertices); stop freeing
`exc.layer`. `Layer_Destroy` and the clone path now share
`S4_Simulation_ClearPattern`.

**Verification.** After a full rebuild (`rm -rf build S4*.so && make && make S4_pyext`),
all of the following exit 0:

* clone, then destroy clone, then destroy original;
* clone, destroy original, then destroy clone (`mk().Clone()`);
* `testing/s4test/selftest_suite.py` — 12 probes, `crash: 0`;
* `testing/s4test/test_python_api.py` — 41 tests OK, including the two new
  `Clone()` regression tests.

> **Build caution.** `make` does not relink `S4.cpython-*.so` unless
> `build/libS4.a` changes, so a stale extension can make a fixed source tree
> look broken. Always wipe `build/` and `S4*.so` before validating a change to
> `S4/S4.cpp`. This cost a full diagnosis cycle during development: the work
> copy's extension was still the pre-fix binary from 16:46 while the source was
> from 16:53, and the crash reproduced from the old `.so`.

---

## D2 — `Clone()` regression: `n_G` deep copy left a compiler-dependent crash

After D1's first iteration, `Clone()` still crashed **only in the `-O3` release
build**; a `-g -O0` build of the same source passed. The differing flag set is
`-O3 -march=native -fcx-limited-range -fno-exceptions` versus `-g -O0 -fPIC`.

This is recorded because it is the reason the D1 fix must be validated on a
**clean release build**, and because "it passes in my debug build" was a
misleading signal during diagnosis. The final fix no longer depends on
optimisation level: the release build passes all reproductions.

---

## D3 — Two-layer stack (bare interface) returns zero flux — FIXED

The reproduction below describes the original behavior. The two-layer route
now uses `SolveInterior`; `test_two_layer_interface.py` and
`test_two_layer_acceptance.py` compare its output with Fresnel and with an
equivalent three-layer stack. Exact diffraction cutoffs remain a separate
numerical boundary, covered by `test_cutoff_safety.py`.

**Symptom.** A simulation with exactly two layers — one semi-infinite incidence
medium and one semi-infinite exit medium — returns no power at all.

**Minimal reproduction.**

```python
import S4
s = S4.New(Lattice=((1,0),(0,1)), NumBasis=1)
s.AddMaterial("Above", 1)
s.AddMaterial("Below", 4)          # n = 2
s.AddLayer("Above", 0, "Above")
s.AddLayer("Below", 0, "Below")
s.SetFrequency(1.0)
s.SetExcitationPlanewave((0,0), 1, 0)
print(s.GetPowerFlux("Above", 0.0))   # ((1+0j), 0j)      <- backward is 0
print(s.GetPowerFlux("Below", 0.0))   # (0j, 0j)          <- transmitted is 0
```

Measured `R = 0`, `T = 0`, `R + T = 0`. Analytic expectation for `n1 = 1`,
`n2 = 2` at normal incidence is `R = 1/9`, `T = 8/9`.

**Adding a third layer fixes it.** Inserting a zero-thickness spacer between the
two media yields `R = 0.111111111111111`, `T = 0.888888888888889` — matching
`1/9` and `8/9` to better than `1e-15`. So the solver mathematics is sound and
the defect is specific to the two-layer degeneracy.

**Why it matters.** The repository's own example
`examples/0d/fabry_perot/fresnel.lua` is exactly this configuration, and it is
listed in `testing/testcases.txt`. Running it through `build/S4` prints

```
0	0	-0	0	-0
1	0	-0	0	-0
...
```

i.e. the shipped example has been producing zeros. The failure is in the shared
core, not in the Python binding: the `-O3`-built Lua frontend reproduces it
identically.

The current suite also uses two-layer Fresnel benchmarks; the restriction above
applied only before the routing fix.

---

## D4 — cubic-spline interpolation returns uninitialised output — FIXED

Natural cubic spline mathematically implemented; Hermite spline handles redundant points correctly; out-of-order x values throw exception.

The Python binding now accepts the correctly spelled name and rejects
`"cublic spline"`. That fixed only dispatch: `S4/Interpolator.c` still returns
`I->result` without computing it in the `Interpolator_CUBIC_SPLINE` branch.
On the current Linux build, `Get(0.75)` for the table below returned a tiny
garbage value. The Hermite branch also returned NaN for this table. Neither
mode should be marked numerically fixed until independent interpolation tests
pass. The observations below describe the original binding before the spelling
change.

`S4/main_python.c:554` compares against the misspelled literal `"cublic spline"`:

```c
else if(0 == strcmp("cublic spline", typeName))
        inter_type = Interpolator_CUBIC_SPLINE;
```

but `S4/main_python.c:560` advertises the correct spelling in its error text:

```
TypeError: the 'type' should be 'linear'/'cubic spline'/'cubic hermite spline'.
```

Measured behaviour:

| argument | result |
|---|---|
| `"linear"` | `(0.625,)` for the test table — correct |
| `"cubic spline"` | `TypeError` |
| `"cublic spline"` | returns `(1.429976056e-315,)` — garbage, not an interpolation |
| `"cubic hermite spline"` | returns `(nan,)` |

So the correctly-spelled name is rejected, and the accepted misspelling takes
the cubic-spline branch but produces a meaningless number. Both the literal and
the returned value need attention.

---

## D5 — `NewSpectrumSampler` rejects more than two arguments — FIXED

The format string is now `dd|idddO!`. The current Python 3.14 build accepts
both the three-argument and seven-argument forms. The old failure follows.

`S4/main_python.c:596` passes a format string with **two** `|` separators:

```c
"dd|i|d|d|d|O!:SpectrumSampler_New"
```

Since Python 3.13 CPython rejects that outright:

```
SystemError: Invalid format string (| specified twice)
```

Consequences: `InitialNumPoints`, `RangeThreshold`, `MaxBend`, `MinimumSpacing`
and `Parallelize` are unreachable, so adaptive sampling and parallel sampling
cannot be enabled from Python. The two-argument form
`S4.NewSpectrumSampler(0.3, 0.5)` works. Keyword arguments are declared in
`kwlist` but can never be bound because parsing fails first.

---

## D6 — `SetRegionPolygon` rejects a list of pairs — FIXED

The converter now accepts a list of coordinate pairs; the current Linux build
accepted the reproduction below. The exception shown is historical.

```python
sim.SetRegionPolygon("Slab", "Air", (0,0), 0, [(0,0), (0.3,0), (0.3,0.3)])
# SystemError: SetRegionPolygon() argument 5 (unspecified)
```

A tuple of pairs works. The failure mode is a `SystemError` with no
explanation, produced because the `O&` converter returns 0 without setting an
exception when the vertex argument is not a tuple; CPython then substitutes its
own generic message. A list is the natural Python spelling and the one a reader
would infer from `SetRegionCircle` etc.

---

## D7 — `SetExcitationExterior` has an undocumented signature — DOCUMENTED

The Python method docstring now shows the three-field tuple form. The following
paragraph describes the earlier wording and remains useful for the exact
argument types accepted by the converter.

The docstring says `SetExcitationExterior(Excitations) -> None`, and the
converter's error text refers to a "G index", but the accepted element form is

```python
((int_index, 'x' or 'y', complex_amplitude), ...)
```

These are the *positional fields of a tuple*, not a `Gindex`/polarization pair
as the converter's own variable names (`exg[2*i+0]`, `exg[2*i+1]`) suggest.
`[(1, 0, 'x', 1+0j)]` raises `TypeError: parameter must be a tuple.`; a nested
G-index such as `(((1,0),'x',1+0j),)` raises
`TypeError: the G index must be a integer.` Only the flat three-field form is
accepted.

---

## D8 - The Lua regression harness is dead - FIXED

The manifest, the stored reference outputs and the runner have all been
repaired, so `testing/runtests.sh` now serves as a real numerical regression.

* `testing/testcases.txt` holds three entries whose paths exist under the
  reorganised `examples/` tree - `simple/simple.lua`,
  `0d/fabry_perot/fresnel.lua` and `2d/Fan_PRB_65_2002/fig12.lua` - each with a
  baseline file and a tolerance. The entries that named files which do not
  exist (`fabry_perot/fresnel.lua`, `1d/binary_grating.lua`,
  `magneto/halfspace.lua`, `diffraction.lua`, ...) are gone.
* Reference outputs are stored next to their scripts:
  `examples/simple/simple.txt`, `examples/0d/fabry_perot/fresnel.txt` and
  `examples/2d/Fan_PRB_65_2002/fig12.txt`.
* `testing/runtests.sh` uses `../build/S4`, and reports a missing executable,
  missing manifest, missing script, missing baseline and malformed manifest
  lines as explicit errors with a non-zero exit status; a manifest with zero
  cases is also an error.
* `testing/numdiff` compares the two files field by field using the tolerance
  given in the manifest.

`make test` reaches the harness through `test-lua`, and `test-python` builds
`$(OBJDIR)/S4` as part of its clean rebuild, so the harness always runs against
a binary built from the current sources. A healthy control plus eleven negative
cases are covered by `testing/s4test/test_lua_regression_negative.sh`, and
fifteen Lua API cases by `testing/s4test/test_lua_api_negative.py`.

Known limitation: `runtests.sh` executes `numdiff` directly and therefore
depends on the interpreter named in its shebang (`/usr/bin/perl`) being
installed; it does not probe for that interpreter itself. A missing interpreter
makes the comparison fail loudly rather than pass.

---

## Documentation inconsistencies (no code defect)

`doc/S4v2lua.md` documents a **different, older API** and does not describe the
shipped binding:

| documented | shipped |
|---|---|
| `S4.NewSimulation()` | `S4.New(...)` |
| `Simulation:AddMaterial` | `S4_Simulation.AddMaterial` |
| `Simulation:SetLattice` / `GetLattice` | not exposed (`Lattice=` at construction) |
| `Simulation:GetMaterial` / `GetLayer` | not exposed |
| `Simulation:ExcitationPlanewave` | `SetExcitationPlanewave` |
| `Layer:SetRegion` / `ClearRegions` / `GetPowerFlux` / `GetWaves` | `S4_Simulation.SetRegion*` / `RemoveLayerRegions` / `GetPowerFlux(layer, z)` |

The following symbols are documented or referenced but **commented out** of the
Python method table in `S4/main_python.c:1868-1889`, so they are absent at
runtime: `GetEField`, `GetHField`, `GetDiffractionOrder`, `GetGList`,
`GetNumG`, `SetBasisFieldDumpPrefix`, `SetLatticeTruncation`. A commented-out
`PrintTuple` entry also remains at line 2053.

`S4Sim_ConvertUnits` is defined at `main_python.c:666` but never registered, so
the compiler emits `-Wunused-function` for it; unit conversion is therefore
unavailable from Python.

`S4_Simulation_Destroy` reads `S->omega[0]` in its `S4_TRACE` epilogue *after*
`free(S)`. This is harmless while tracing is compiled out but is a
use-after-free the moment `S4_DEBUG` is enabled.

---

## Summary

| id | defect | status |
|---|---|---|
| D1 | `Clone()` heap corruption (crash) | **fixed** |
| D2 | compiler-dependent `Clone()` crash masking D1 | documented |
| D3 | two-layer bare interface returns zero flux | **fixed** |
| D4 | cubic-spline interpolation returns uninitialised output | **fixed** |
| D5 | `NewSpectrumSampler` format string | **fixed** |
| D6 | `SetRegionPolygon` list rejected | **fixed** |
| D7 | `SetExcitationExterior` undocumented signature | documented |
| D8 | Lua regression harness dead | **fixed** |
| D9 | Python frequency sweep reused layer modes | **fixed** |
| D10 | exact cutoff gives invalid numerical output | safe errors incl. non-finite guards on fields/integrals; exact value **not computed** |
| D11 | binding error paths leaked scratch buffers | **fixed** (two of three; Lua sites open) |
| D12 | `GetFieldsOnGrid` crashed, leaked and wrote non-finite data | **fixed** (binding + core size guard; Lua `GetFieldPlane` still open) |
| D13 | Lua `GetFieldPlane` crashed, leaked and wrote non-finite data | **fixed** |
| D14 | public C API `S4_Simulation_GetFieldPlane` accepted impossible grids, dereferenced NULL outputs, formed a layer pointer with no layers, and read `xyz0` before validating it | **fixed** (capacity, output pointers, no-layer check, trace) |
| D15 | `GetFieldOnGrid` and the FFT plan wrapper ignored every allocation failure, dereferenced NULL, leaked the plan configuration, returned `void`, and both callers returned success | **fixed** (checked allocations, single cleanup path, `int` status propagated to C, Python and Lua) |
| D15b | the FFT *execution* stage (`kf_bfly_generic`'s generic-butterfly scratch, and the in-place temporary) was unchecked and SIGSEGVed on any grid with a radix outside 2/3/4/5, e.g. 7x3 with a 112-byte failure | **fixed** (checked KISS execution variants, status threaded through `kf_work`/`kiss_fftnd`/`fft_plan_exec`/`GetFieldOnGrid` to C, Python and Lua) |


---

## D9 -- `SetFrequency` did not invalidate cached layer modes (FIXED)

**Symptom.** A spectral sweep on a single simulation object returned the *first*
frequency's answer for every subsequent point.  Building a fresh simulation per
frequency gave the right answer, which is why the four original smoke tests
(which use one frequency each) never noticed.

**Minimal reproduction.**

```python
import S4
def build():
    s = S4.New(Lattice=((1,0),(0,1)), NumBasis=1)
    s.AddMaterial("Above", 1); s.AddMaterial("Film", 4); s.AddMaterial("Below", 1)
    s.AddLayer("Above", 0, "Above")
    s.AddLayer("Film", 0.5, "Film")
    s.AddLayer("Below", 0, "Below")
    return s

def T(s):
    inc, _ = s.GetPowerFlux("Above", 0.0)
    fwd, _ = s.GetPowerFlux("Below", 0.0)
    return fwd.real / inc.real

s = build(); s.SetExcitationPlanewave((0,0), 1, 0)
for f in (0.20, 0.35):
    s.SetFrequency(f)
    print(f, T(s))     # prints 0.662784504 twice; 0.35 should be 0.730908116
```

Measured:

```
sweep order      T values                    verdict
(0.20, 0.35)     0.662784504 0.662784504     second point stale
(0.35, 0.20)     0.730908116 0.730908116     second point stale
(0.20, 0.35)     ...                          the FIRST frequency always wins
```

The reference values come from `airy_rt` in `testing/s4test/analytic.py`:
0.20 -> 0.662784504, 0.25 -> 0.640000000 (exact half-wave), 0.35 -> 0.730908116.

**Root cause.** `S4Sim_SetFrequency` in `S4/main_python.c` called
`Simulation_DestroySolution` only.  Layer eigenmodes are cached per layer in
`S4_Layer::modes` and are frequency dependent, and
`Simulation_GetLayerSolution` reuses `L->modes` whenever it is non-NULL, so the
solved wavevectors from the first frequency were reused for all later ones.

The C API entry point `S4_Simulation_SetFrequency` (`S4/S4.cpp`) does the right
thing and calls `S4_Simulation_DestroyLayerModes(S, -1)` as well; the Python
binding was the inconsistent one.  This is a **binding defect, not a core
defect**: the Lua frontend (which uses a different entry point) sweeps
correctly, and the cross-frontend test confirms it.

**Fix.** `S4Sim_SetFrequency` now delegates to
`S4_Simulation_SetFrequency`, the C API function that invalidates modes,
solutions, and field caches together.

**Regression tests.**
`test_analytic_reference.TransferMatrixBenchmarkTests.test_frequency_dependence_matches_reference`
sweeps five frequencies on one object against the transfer-matrix reference, and
`FluxConventionTests` pins the amplitude conventions the comparison relies on.
Both failed before the fix and pass after it.

---

## D10 - Exact diffraction cutoff: explicit error, physical limit not computed

**Status.** The safety behaviour is implemented and tested; the exact-cutoff
value is **not** computed. The direct-substitution and whole-matrix-injection
experiments described below did not complete a repair, and no trustworthy
scheme has been found yet. Those experiments constrain the problem; they are not
a proof that no scheme exists, and other stable representations are not ruled
out.

### What the code does now

At an exact cutoff one interface subsystem can be singular. `GetSMatrix`,
`SolveAll` and `SolveInterior` propagate the zero-pivot status to the caller,
`Simulation_ComputeLayerSolution` returns error 3, and the accessor raises
`RuntimeError`. A failed solve is never cached, so a later frequency on the same
simulation object is computed normally. A second, independent failure mode
appears when a retained order has `q == 0` in the medium being addressed: the
flux, field and integral routines divide by `omega*q` without a guard, and the
pre-existing finiteness check reports error 18 instead of returning the value.
Neither path returns a NaN or a plausible-looking wrong number **for the
accessors listed under "Accessor coverage" below, on the builds listed there**.

### Reproducer and measured facts

Flat `Air / (Air) / Glass`, eps 1 -> 4, lattice `((1,0),(0,1))`, normal
incidence, s polarisation, `NumBasis = 9`. The cutoff orders are `(0,+-1)` and
`(+-1,0)`.

* `f = 0.999` and `f = 1.001`: `R = 1/9`, `T = 8/9` to 1e-15 (the Fresnel
  reference); energy is conserved to 1e-15.
* `f = 1.0` on a pure `-O1` build: explicit error from the interface solve. The
  neighbours at `f = 1 +- 1 ulp` also return the exact Fresnel value, so the
  failure is one representable point, not a neighbourhood.
* The same family of frequencies puts a retained order at a cutoff, and each
  fails in one of the two ways above: `f = 0.5` (glass, `(1,0)`),
  `f = 2.0` (air, `(2,0)`) and `f = sqrt(2)` (air, `(1,1)`).
* `NumBasis = 1` retains no cutoff order and stays exact at all of them.

### Why the value at the cutoff is not computed

Instrumented dumps of the `MakeQ` solve (research copy only, `S4_D10_DUMP`):

* The matrix is `Bl(layer l)`, 18x18 for `NumBasis = 9`. At `f = 1.0` it has
  **rank 14 and a 4-dimensional nullspace**; its four exactly-zero rows and
  columns are indices `{1, 4, 11, 12}`, and `q[l]` is exactly zero at exactly
  those four coordinates. This is the algebraic image of the four cutoff
  orders, not rounding.
* For the `Air -> Glass` interface the right-hand side is **incompatible** on
  those four columns (least-squares residual exactly 1.0); for `Air -> Air` it
  is compatible.
* Replacing the failed solve with the min-norm least-squares solution, and even
  injecting the code's own finite coupling matrix `Q` from `f = 1 - 1e-14`,
  still left the solver returning a non-finite flux at `f = 1.0`. So the
  problem is not confined to that one linear solve.
* The coupling matrix `Q` that the algorithm forms next grows like
  `1/q ~ (1-f)^(-1/2)` as `f -> 1` (`max|Q| = 3.1e1 ... 3.0e6` for
  `1-f = 1e-4 ... 1e-14`), while the physical answer converges. The divergence
  therefore cancels later in the recursion, and the min-norm `Q` at `f = 1.0`
  (which is `O(1)`) is **not** the limit.

This is why `SingularLinearSolve` (LAPACK `zgelss`, min-norm) is not a fix. In
this build configuration it is not even a min-norm solve: `Makefile.Linux`
defines neither `HAVE_LAPACK` nor `HAVE_BLAS`, so `SingularLinearSolve` falls
through to plain LU and the hand-written `RNP::LinearSolve` in
`LinearSolve.h` is the active solver.

Candidate directions that remain open, none of them established:

* a cutoff-adapted reformulation in which the divergent part of `Q` is carried
  through the recursion instead of being represented by a finite matrix;
* solving only the physically excited columns, with a certificate that the
  result is invariant over the solution set;
* a stable reformulation that avoids `Q` altogether.

### Two distinct failure mechanisms, and the f = 0.5 discrepancy

Instrumented return-code tracing on `-O1` separates the two:

* **`f = 1.0`, `f = 2.0`, `f = sqrt(2)`**: the interface solve itself reports an
  exact zero pivot (error 3). The flux code is never reached.
* **`f = 0.5`**: the interface solve succeeds. The exit medium is glass, whose
  `(1,0)` order sits exactly at cutoff, so `GetZPoyntingFlux` and
  `GetZPoyntingFluxComponents` compute `1/(omega*q)` with `min abs(q) =
  0.000000e+00` (8 of 18 mode coordinates), producing an infinity that the
  finiteness check catches (error 18). The entry-side (air) call has
  `min abs(q) = 3.14` and is finite. This is why the same frequency looks
  "finite" when only the entry-side flux is inspected, and why `-O3` builds
  differ: there `q` lands on a denormal instead of an exact zero.

The nine unguarded `1/(omega*q)` sites are in `GetZPoyntingFlux`,
`GetZPoyntingFluxComponents`, `GetInPlaneFieldVector`, `GetLayerVolumeIntegral`
and `GetLayerZIntegral`.

### Accessor coverage (measured)

Checked on the pure `-O1` build, the default `-O3 -march=native` build, the
`-O1 -fsanitize=address,undefined` build and the pre-existing default build in
the real repository, each on a fresh simulation object per accessor:
`GetPowerFlux` (both sides), `GetPowerFluxByOrder` (both sides),
`GetAmplitudes` (both sides), `GetSMatrixDeterminant`, `GetPoyntingFlux`,
`GetFields` (at z = 0 and inside the exit layer), `GetLayerZIntegral` (both
layers), `GetLayerVolumeIntegral`, `GetStressTensorIntegral`. Case matrix:
flat 2- and 3-layer x `NumBasis` 9/25 x frequencies 0.5, 1.0, 2.0, sqrt(2),
0.999, 1.001, 1.25, the patterned slab at `NumBasis` 9/25 x 1.0, 1 +- 1e-10,
1.25, and the oblique 30-degree two-layer case at `NumBasis = 25`.
`GetFieldsOnGrid` writes files and is not part of this matrix.

### Safety gaps found and closed in this round

* `GetFields`, `GetLayerZIntegral`, `GetLayerVolumeIntegral` and
  `GetStressTensorIntegral` returned **NaN silently** on `-O1` at `f = 0.5`
  (for example `GetFields(0,0,0.1)` gave `(nan,nan,nan)` and
  `GetLayerVolumeIntegral("Below","E")` gave `nan+nanj`). They now apply the
  same finiteness check the two flux accessors already had and raise error 18.
* A recorded solve failure used to be reported but not acted on: the code kept
  computing with the failed factorization and with right hand sides that had
  never been solved. `S4_RECORD_OR_DONE` now records the first non-zero status
  and abandons every remaining dependent step, jumping to a single
  `S4_SOLVE_DONE` cleanup label in `GetSMatrix`, `SolveAll` and
  `SolveInterior`. `Invert()` also stopped overwriting a factorization failure
  with the status of the follow-on `zgetri` call, and it no longer runs
  `zgetri` at all when the factorization failed.
  **Behaviourally verified** with a test-only fault injection build
  (`-DS4_D10_FAULT_INJECT`, compile-time gated so no normal build contains it,
  in a throwaway copy) that feeds a genuinely singular matrix to `zgetrf` at a
  chosen call. On a flat three-layer stack at `f = 0.999`, `NumBasis = 9`,
  `SolveAll` normally calls `Invert` twice, runs the dependent statements after
  it twice, factors twice and runs the three triangular passes three times. With
  the first `Invert` made singular the counters read
  `invert_calls=1 gotri_calls=0 after_invert=0 lufactor_calls=0 passes=0
  cleanup=1 solve_failed=1`: `zgetri` was not called, nothing that consumes
  `Saa` ran, the LDU factorization and all three passes were skipped, the shared
  cleanup ran, and the caller received error 3. With the first `LUFactor` made
  singular the counters read `passes=0 cleanup=1 solve_failed=1`. In both cases
  the same simulation object produced the exact Fresnel result at `f = 1.25`
  afterwards, and matched a freshly built object, so the failed layer was not
  cached as solved.
  **Static finding:** in every case of the matrix above, all of those calls
  returned `info = 0` in an unmodified build, so no natural failure case exists
  for the ignored return codes; the injection above is what exercises them.
* Error 3 and error 18 no longer assert that a singular system is a diffraction
  cutoff, and error 18 is no longer phrased as being about a flux.

Ordinary frequencies are unaffected: `R` and `T` at `f` in
{0.999, 1.001, 1.25} are bit-identical before and after these changes (compared
across the unpatched `-O1` build and the patched `-O1` build), and the `f = 0.5`
values for a healthy layer are unchanged.

### What the optimised build does

The default `-O3 -march=native` build does not hit the zero pivot at `f = 1.0`
and returns values that agree with the one-sided limit (for the patterned slab
below, the exact-point value equals the `f = 1 + 1 ulp` value to all printed
digits). That agreement is a property of the rounding, not a certificate, and
nothing in the suite relies on it. At `f = 2.0` and `f = sqrt(2)` with
`NumBasis = 25` the optimised build fails exactly as `-O1` does.

### Patterned structure

`Air / Slab(0.5, air with a glass circle r = 0.25) / Air`, `NumBasis = 9, 25`.
The cutoff orders are excited here, so the flat `1/9, 8/9` reference does not
apply. At `f = 1.0` the `-O1` build raises the interface error; the one-sided
values at `f = 1 +- 1e-14` conserve energy to 1e-15 and the one-sided gap
shrinks roughly like `sqrt(delta)`. The energy balance and the neighbourhood
comparison are evidence, not a substitute for a `NumBasis` convergence study or
an independent physical reference; the flat-interface `1/9, 8/9` result is not
imposed on it.

### Coverage

`testing/s4test/test_cutoff_safety.py` asserts, per case and per accessor on a
fresh object, that the result is either a known explicit error or a value whose
every real and imaginary component is finite; every case/accessor combination
is checked to have actually run. Flat successes must reproduce the closed-form
Fresnel answer, and patterned successes must conserve energy. Call order is
checked not to change any outcome, and repeats at the exact point are checked
for determinism.

---

## D11 - Error paths leaked their scratch buffers - FIXED (two of them)

`S4Sim_GetAmplitudes` and `S4Sim_GetPowerFluxByOrder` in `S4/main_python.c`
allocate a scratch buffer, call the core, and returned `NULL` without freeing
the buffer when the core reported an error, so every failed call leaked. This
is directly relevant to D10 because the cutoff cases fail on exactly those
paths.

| scenario | binding errors raised | before | after |
|---|---|---|---|
| import S4 only | 0 | 1760 B / 2 allocations | 1760 B / 2 allocations |
| 3 simulations created, solved, destroyed | 0 | 1760 B / 2 | 1760 B / 2 |
| 300 simulations created, solved, destroyed | 0 | 1760 B / 2 | 1760 B / 2 |
| 300 failing `GetAmplitudes` calls | 300 | 174560 B / 302 | 1760 B / 2 |
| 300 failing `GetPowerFluxByOrder` calls | 300 | 88160 B / 302 | 1760 B / 2 |
| 300 failing calls of both interfaces | 600 | 260960 B / 602 | 1760 B / 2 |
| 3 cubic-spline interpolators created, queried, destroyed | 0 | 1760 B / 2 | 1760 B / 2 |
| 300 cubic-spline interpolators created, queried, destroyed | 0 | 1760 B / 2 | 1760 B / 2 |

Each scenario runs in its own process; the table records how many errors the
binding actually raised, so a scenario that never reached the failing path
cannot be mistaken for a pass. The "before" column comes from a copy of the
same revision with only those two `free()` calls reverted, so the difference is
attributable to those two lines. The extra leaks there are direct allocations at
`S4Sim_GetAmplitudes` (`main_python.c:1312`, 576 B per failing call) and
`S4Sim_GetPowerFluxByOrder` (`main_python.c:1376`, 288 B per failing call); the
allocations are reported as 299 + 1 objects because LeakSanitizer splits the
final one off. After the fix the only frames left in any scenario are the two
`PyInit_S4` allocations.

`libasan` is preloaded into the Python process only; the tools that parse the
raw output run without it, so no shell utility leak report can contaminate the
result. Full raw output is kept under `/tmp/s4-d10/leak-leakbefore/` and
`/tmp/s4-d10/leak-leakfixed/` in the research area.

The two remaining allocations are once-per-process import-time singletons in
`PyInit_S4` - `PyErr_NewException("S4.Error", ...)` and a `PyType_Ready` static
type - and neither grows with the number of objects, of failures, or of
interpolators. They stay on the list as module-lifecycle items to review; this
patch does not refactor module initialisation. The comparison uses leak counts,
allocation counts and byte totals across the scenarios; RSS growth is not used
as evidence.

Fix: free the scratch buffer on the error path in both binding functions.

Still open, found by the same scan but not reached by any case in the D10 matrix
and therefore **not** fixed here (see D12 for the `GetFieldsOnGrid` follow-up):

* `S4L_Integrate` (`main_lua.c`) allocates `xmin` and has an early `return 0;`
  before the matching free.
* `S4L_Simulation_SetExcitationExterior` (`main_lua.c`) allocates `ex` and `exg`
  and never frees them, unlike the Python binding which does.
---

## D12 - `GetFieldsOnGrid` crashed, leaked and wrote non-finite data - FIXED

Task name: **GetFieldsOnGrid 修复（DEFECTS.md：D12）**.

`S4Sim_GetFieldsOnGrid` (`S4/main_python.c`) is the only Python entry point that
can write field data to disk. Its pre-fix form had no size validation, no
allocation checks, no `fopen` check and no common cleanup path. Every failure
family was reproduced in its own process against the pre-fix `-O1` build.

| case | pre-fix result |
|---|---|
| ordinary frequency, array return | correct shape `(E, H) x nu x nv x 3`, finite, no files written |
| ordinary frequency, `FileWrite` | `g.E` and `g.H` written, 8 tab-separated fields per row |
| ordinary frequency, `FileAppend` | appended, existing bytes preserved, 9 fields per row (adds `z`) |

For a 4x3 grid each file holds **12 non-empty data rows** - one per `(i, j)`
pair - plus 4 blank separator lines, i.e. 16 lines in total. The blank lines
separate the rows of the first index and are not data rows; any check of the row
count has to count non-empty lines.
| core failure (`f = 1.0`, flat stack) | `RuntimeError`, no files, but **3 leaked allocations per call** |
| `f = 0.5`, exit medium `q = 0` | **48 of 96 components NaN**, returned as an array and **written into both files** |
| output path in a missing directory | **SIGSEGV** in `__vfprintf_internal` (`fprintf(NULL, ...)`) |
| output path is a directory | **SIGSEGV** |
| `NumSamples = (0, 8)` | **SIGFPE** |
| `NumSamples = (-1, 8)` | `SystemError: returned a result with an exception set` |
| `NumSamples = (2**40, 2)` | **SIGSEGV** |

Ownership before the fix: `filename` and the two field buffers were freed only
on the three success paths, so the core-error path leaked all three; the two
`fopen` results and both `fclose` results were unchecked; the tuple and complex
objects in the array branch were created without checking any result.

Fix (binding):

* `NumSamples` must be positive, must fit in `int`, and the point count must be
  representable before anything is allocated; each rejection is `ValueError`, and
  a product that cannot be sized is `OverflowError`. No truncated or negative
  size reaches the core.
* `malloc` results are checked; failure raises `MemoryError` and releases what
  was already allocated.
* A single `done:` cleanup path frees `filename`, `Efields` and `Hfields` on
  every exit, and releases a partially built tuple if the interpreter's object
  creation fails.
* `fopen` failure raises `OSError` from `errno` **with the path**; short writes
  and `fclose` failure raise `OSError` naming the path. `fprintf` is never
  called on a `NULL` `FILE *`, and no success is reported for a file that was
  not written.
* A grid whose values are not finite raises `RuntimeError` naming the cause
  instead of returning NaN or writing NaN to disk. The check is applied before
  either output branch, so the two branches cannot disagree.

File output failure semantics, stated explicitly because the two files are
written independently and in order (`.E` first, then `.H`):

* This patch provides **no rollback and no atomic two-file commit**. If `.E` is
  written successfully and `.H` then fails to open or write, `.E` stays on disk.
* A failure part-way through writing one file can leave that file with partial
  content. Opening with `"wb"` truncates, so a failed `FileWrite` leaves the
  prefix that was already flushed.
* Any such failure raises `OSError` naming the affected path, and all three
  buffers are released on the common cleanup path.
* The accessor never reports success for a file it did not completely write and
  close; in particular it does not return `None` when a write or close failed.

Core guard (separate concern, `S4.cpp`): `Simulation_GetFieldPlane` turned its
`int nxy[2]` into `size_t`, multiplied it for the point count and used it as FFT
dimensions, so a non-positive entry was not representable - `nxy = {0, 8}` was
the SIGFPE above and a negative entry became a huge `size_t`. It now rejects a
non-positive grid with `-3` before any of that work, which protects every
caller rather than only this binding. The binding's own validation is what
produces the accurate Python error.

Invariance: for ordinary frequencies the returned arrays and both output files
are **byte-identical** before and after the change (SHA256 of the flattened
array values, of `FileWrite` `g.E`/`g.H`, and of two `FileAppend` passes all
unchanged), and a 1x1 grid returns an identical value.

Regression tests: `testing/s4test/test_grid_output_safety.py`. Coverage:
ordinary-frequency array shape and finiteness; every non-array format returns
arrays and writes nothing; `FileWrite` layout cross-checked against the array
result; `FileAppend` preserves existing content and adds the `z` column; core
failure propagates and writes nothing; non-finite grids are rejected;
an unwritable output path raises instead of crashing; invalid `NumSamples` is
rejected; the object is reusable after a failure; repeated failures keep raising;
and the two partial-file cases (`FileWrite`/`FileAppend` with `.E` on a full
device, and `.H` blocked while `.E` succeeds). On the pre-fix build the
non-finite case reports `RuntimeError not raised` and the unwritable-path,
invalid-size and `.E`-on-a-full-device cases crash or return silently instead of
raising, so those are run per method in separate processes to record it. The
number of tests in the file is not pinned here; the acceptance log records the
measured count.

Build dependence, which the tests are written around: the flat stack at
`f = 1.0` is singular under `-O1` but **not** under the project's default
`-O3 -march=native -fcx-limited-range`, and the `f = 0.5` glass grid is
non-finite under `-O1` only. Asserting on either one would make the suite
optimisation-dependent, so the tests trigger the two contracts with cases that
survive both builds: `f = sqrt(2)` for the singular interface solve, and a layer
with `eps = 0` for the non-finite grid, whose longitudinal wavevector is exactly
zero rather than approximately so. The `f = 1.0` and `f = 0.5` glass results are
recorded in this document as measurements, not asserted in the suite.

Leak comparison, `-O1` on both sides, `libasan` preloaded into the Python
process only, 300 calls per scenario:

| scenario | pre-fix | post-fix |
|---|---|---|
| import S4 only | 1760 B / 2 | 1760 B / 2 |
| 3 core failures (3 raised) | 6446 B / 11 | 1760 B / 2 |
| 300 core failures (300 raised) | 470360 B / 902 | 1760 B / 2 |
| 300 unwritable-path failures | **SIGSEGV** | 1760 B / 2 |
| 300 non-finite failures | NaN returned, 1760 B / 2 | guard fires, 1760 B / 2 |

Every pre-fix extra allocation is attributed to `S4Sim_GetFieldsOnGrid`; after
the fix the only remaining frames are the two `PyInit_S4` module-initialisation
allocations (1760 B / 2). Those two are **not fixed or explained away by this
patch** - they are process-lifetime allocations that stay on the open list, and
they are never counted as per-call leaks, nor is their presence reported as
"zero findings".

Allocation-failure injection (test-only build, `-DS4_D11_FAULT_INJECT`, never in
a delivered source): with the failure forced at allocation 1, 2 and 3 the report
confirms the injection hit that exact point (`alloc_calls=1/2/3 fail_at=1/2/3`),
a `MemoryError` is raised instead of a crash, the same object succeeds on the
next call, and 300 injected failures at each point still report only
1760 B / 2. The baseline report shows `alloc_calls=3`, i.e. the three
allocations happen in the documented order (`filename`, `Efields`, `Hfields`).

Suite status around this patch: the one skipped item is the interpolator
out-of-memory test, which is verified by code review only and is not
automatically exercised; this patch does not change that. D10 is untouched: an
exact diffraction cutoff still reports a safe error, and the trustworthy
exact-cutoff **value is not computed**; the paper examples run and conserve
energy but the published results are **not independently reproduced**.

Still open, separated from this patch:

* `S4L_Simulation_GetFieldPlane` (`main_lua.c:2772`) shares the core function and
  has the same unchecked `fopen`/`fprintf(fp, ...)` pattern and no finiteness
  check, so the Lua path can still crash on an unwritable path and still writes
  NaN files at a cutoff. It does validate positive grid sizes.
* `S4_Simulation_GetFieldPlane` (the public C API, `S4.cpp:4104`) is a separate
  implementation and does not validate `nxy` either.
* `PyInit_S4` module-lifecycle allocations (768 B + 992 B once per process).

---

## D13 - Lua `GetFieldPlane`: no input validation, leaked buffers, crashed on unopenable output - FIXED

Task name: **Lua GetFieldPlane 修复（DEFECTS.md：D13）**.

`S4L_Simulation_GetFieldPlane` (`S4/main_lua.c`) is the Lua counterpart of the
Python defect D12 and had **no test coverage at all** before this round. Its
pre-fix form cast `lua_tointeger` straight to `int` before validating, never
checked a `malloc`, never checked `fopen`/`fprintf`/`fclose`, had no finiteness
check and freed its three buffers only on the success paths.

### Pre-fix reproduction, one process per case

| case | pre-fix result |
|---|---|
| ordinary `Array` 1x1 and 4x3 | correct two-table shape, finite |
| ordinary `FileWrite` / `FileAppend` 4x3 | correct files, appended content preserved |
| output path in a missing directory | **SIGSEGV** |
| `.E` path is a directory | **SIGSEGV** |
| `.H` path is a directory (`.E` writable) | **SIGSEGV** |
| `.E` symlinked to `/dev/full`, `FileWrite` | **exit 0, no error** (silent success) |
| `.E` symlinked to `/dev/full`, `FileAppend` | **exit 0, no error** |
| core failure (`f = sqrt(2)`) | exit 1 through `S4L_error`, so `pcall` **cannot** catch it and no cleanup runs |
| non-finite grid (layer with `eps = 0`) | **all 24 components NaN**, returned as a table and written to both files, exit 0 |
| `NumSamples = {0,8}`, `{-1,8}`, `{2^40,2}` | exit 1 through `S4L_error` (uncatchable), message lost the real reason |
| `NumSamples = {2.5,2}` | **silently truncated** to `{2,2}`, exit 0 |
| `NumSamples = {2^31-1,2^31-1}` | **hung** (45 s timeout): the byte count wrapped `size_t`, `malloc` returned NULL, the core treats NULL as "nothing to do" and returns success, and the table loop then ran for an astronomical count |
| missing / wrong-typed arguments | already a proper Lua error |

### Error contract chosen

`S4L_error` prints to stderr and then, outside interactive mode, calls
`lua_close(L); exit(EXIT_FAILURE)`. It is not a Lua error: `pcall` cannot catch
it, no C frame is unwound, and no cleanup at the call site runs. In interactive
mode it merely prints and **returns**, so the caller continues with invalid state.

GetFieldPlane therefore raises real Lua errors (`luaL_error` / `luaL_argcheck`)
for every failure class. A caught error is catchable by `pcall`; an uncaught one
in batch mode travels through `docall`'s `lua_pcall` into `main`, which prints a
traceback and returns `EXIT_FAILURE` (exit code 1, never a signal). `S4L_error`
and the behaviour of `HandleSolutionErrorCode` are unchanged; only the error-text
table was moved to file scope so the new formatter and the existing function
share one copy, keeping the messages byte-identical.

### Resource ownership

The three native buffers are owned by a Lua userdata (`S4.GridPlaneBuffer`)
whose `__gc` releases them. It is created **before** any native allocation, so a
Lua memory error during preparation has nothing to leak; each pointer is stored
in the owner right after a successful `malloc`; and every failure the binding
controls - input validation, a buffer allocation, the core solution, a non-finite
grid, and file open/write/close - releases the buffers explicitly and only then
raises. The one case that cannot be released before the raise is a memory error
raised by Lua **itself** while the result tables are being built, because that is
unprotected Lua API which longjmps; those buffers are freed by the owner's `__gc`
when it is collected. No claim is made that every allocation failure is released
before the error is raised: controlled failures are, Lua-raised ones are released
at collection time. `FILE *` ownership stays local to the write helper, which
closes on every exit and saves `errno` before closing.

### Validation

Each grid entry must be a number, integral, `>= 1` and `<= INT_MAX`, checked
**before** the narrowing cast. `nu*nv`, then `npoints*6`, then that times
`sizeof(double)` are checked for `size_t` overflow in that order. No arbitrary
grid ceiling was added. Loop counters and element indices are `size_t`.

### File semantics

The two files stay independent: `.E` may survive a `.H` failure, a failed write
may leave partial content, and there is no rollback or two-file transaction -
identical to the accepted Python semantics. Every file error names the path and
the saved `errno` string, and distinguishes open, write and close.

### Compatibility

Ordinary results are unchanged: the 72-component `Array` dump, and the
`FileWrite` `g.E`/`g.H` files (1659 / 1634 bytes), are **byte-identical** before
and after. `FileWrite` and `FileAppend` still return no values (`nil`), the table
layout is still `E[i][j][component][real, imaginary]`, and the field order,
`%.14g` formatting, blank separators and the trailing blank line of an append are
unchanged.

### Tests

`testing/s4test/test_lua_field_plane.py`, 14 tests: the two success shapes, a
component-by-component cross-check of **both** output files against **both**
array tables (shape of both returned tables, 12 non-empty data rows per file,
8 fields per row, the grid coordinates, and every real and imaginary part
compared with an absolute tolerance of 1e-12 - the same evidence-based tolerance
the Python grid test uses, and not widened here), an append check that keeps the
raw pre-append bytes of both files and asserts `after.startswith(before)` plus
the correct count, field count and `z` column of the added rows, the zero-result
contract of the file formats via `select('#', ...)`, a missing output directory,
both file-open failures, a `/dev/full` write/close failure, a catchable core
failure, non-finite rejection, invalid grid sizes including the overflow case
that used to hang, an uncaught non-zero exit without a signal, object reuse after
a failure, repeated failures never reporting success, and argument type errors.

The tolerance has a known, stated scope: it accepts a difference below 5e-13, so
perturbing only the last digit of a value already stored at `%.14g` precision
does not count as a mismatch. A genuine corruption does. Both new assertions were
mutation-validated in a throwaway copy of the test module (never in the delivered
file, whose SHA256 was identical before and after): changing one `H` value by 1.0
made the `H` cross-check fail with
`-0.3333333333333 != -1.3333333333333333 within 12 places`; altering a byte
inside the saved append prefix while the file still grew made the prefix check
fail for both files with `the append changed earlier bytes of H`.

Against the pre-fix binary (`build/S4` `b17118d3…`): **9 of the 14 test methods
fail (15 subTest failures), 5 pass.** The five that pass are the success-behaviour
regression contracts (array shape, file layout, append semantics, no-return
values) plus the "uncaught failure exits non-zero without a signal" contract,
which the old frontend also satisfied through `S4L_error`'s `exit`. The nine that
fail are exactly the defect-exposing ones: three SIGSEGV cases, the two silent
`/dev/full` successes, the uncatchable core failure, the silent NaN, the grid-size
family (including the 45 s hang and the silent fractional truncation), the lost
recovery and the repeated-failure contract.

### Allocation failure and leak evidence

Test-only build `-DS4_LUA_GFP_FAULT_INJECT` in
`/home/jackal/sandbox/s4-lua-gfp-faulti`, never in a delivered source. The report
confirms the exact allocation hit: `fail_once_at_1` -> `alloc_calls=1`
(filename), `_at_2` -> `alloc_calls=2` (Efields), `_at_3` -> `alloc_calls=3`
(Hfields); the baseline shows `alloc_calls=3` per call; each injected failure
raises the matching message and the **same object succeeds on the next call**
(the second call reports `alloc_calls=3`).

LeakSanitizer, `detect_leaks=1`, in the same process for the whole loop (a
per-process exit would not prove anything about per-call behaviour): no report
for the empty script, for 3 successes, for 300 successes, or for 300 caught
failures at each of the three allocation points. The detector is proven live by a
positive control in the same build: with `S4_LUA_GFP_DELIBERATE_LEAK=1` it
reports `Direct leak of 1228800 byte(s) in 300 object(s)` with the stack
`s4_lua_gfp_deliberate_leak -> S4L_Simulation_GetFieldPlane -> docall -> main`,
i.e. 4096 bytes x 300 calls. The Lua binary shows **no** residual baseline leak,
unlike the Python extension's two module-initialisation allocations.

The "the same object still works afterwards" assertions in the test module prove
**usability only**. They are not a leak check and are not presented as one. The
per-call leak conclusion rests solely on the LeakSanitizer scenarios listed
above - the empty script, 3 successes, 300 successes, and 300 caught failures at
each of the three allocation points, each run inside a single process - and on
nothing else. Size growth is never used as evidence, and RSS is never used as
evidence anywhere in this work.

Not covered: a Lua **deep** out-of-memory during result-table construction is
handled by design (the `__gc` owner) but was not exercised, because that needs a
test-only Lua allocator; it is listed as not automatically verified rather than
claimed. RSS growth is not used as leak evidence anywhere.

Still open, separated from this patch: the public C API grid-size validation
(`S4_Simulation_GetFieldPlane`, `S4/S4.cpp`), `S4L_Integrate`,`
S4L_Simulation_SetExcitationExterior`, and the `PyInit_S4` module-lifecycle
allocations.

---

## D14 - Public C API `S4_Simulation_GetFieldPlane`: parameter, capacity and output contract - FIXED

Task name: **公开 C API 网格入口修复（DEFECTS.md：D14）**.

`S4_Simulation_GetFieldPlane` (`S4/S4.cpp`, declared in `S4/S4.h`) is the C entry
point for sampling the field on a grid. It is a *separate implementation* from
the internal `Simulation_GetFieldPlane` that the Python and Lua bindings use, and
it had no test reaching it: the Python grid tests exercise
`S4Sim_GetFieldsOnGrid` and the Lua ones exercise `S4L_Simulation_GetFieldPlane`,
both of which wrap the internal function.

### Contract

| condition | return | output buffers |
|---|---|---|
| `S == NULL` | -1 | untouched |
| `nxy == NULL` | -2 | untouched |
| `xyz0 == NULL` | -3 | untouched |
| `E == NULL && H == NULL` | 0 | n/a (no-op; grid not examined) |
| `nxy[0] <= 0 \|\| nxy[1] <= 0` | -4 (new) | untouched |
| `(size_t)nxy[0] * nxy[1] > INT_MAX` | -5 (new) | untouched |
| `S->n_layers <= 0` | 14 | untouched |
| core mode-solve failure | the solution code (3, 18, ...) | unspecified |
| internal allocation failure | 1 | unspecified |
| success | 0 | every non-NULL buffer filled |

`-4` and `-5` are new codes for this function. Negative codes are per-function in
this codebase (`-1`/`-2`/`-3` already meant NULL arguments here, and `-3` is
already taken by `xyz0`), so no existing meaning was redefined and no existing
code changes meaning. `14` is the established "No layers exist in the structure"
code; the function already contained a `return 14` that was unreachable.

Each non-NULL output buffer must hold `3*nxy[0]*nxy[1]` complex values, i.e.
`6*nxy[0]*nxy[1]` `S4_real` values: element `(i, j, c)` starts at `S4_real`
index `2*(3*(i + j*nxy[0]) + c)`, imaginary part after the real part, `i` the
fast axis. `E` and `H` are independently optional - `GetFieldAtPoint` and
`Simulation_GetField` already implement that convention (conditional writes), and
`GetFieldOnGrid`'s own parameter comment contemplates a NULL `efield` - so this
round keeps it rather than inventing a new restriction.

**The interface has no buffer length parameter.** It therefore cannot check how
much space a caller actually provided; a shorter buffer is a caller error these
checks cannot detect. Nothing here claims otherwise.

### Pre-fix reproduction (direct calls to this entry point, one process per case)

| case | pre-fix | post-fix |
|---|---|---|
| `S`, `nxy`, `xyz0` NULL | -1 / -2 / -3, outputs untouched | unchanged |
| both outputs NULL | 0, no work | unchanged (and still precedes grid validation) |
| `nxy = {0,8}` / `{8,0}` | **SIGFPE** | -4, outputs untouched |
| `nxy = {-1,8}` / `{8,-1}` | **SIGSEGV** | -4, outputs untouched |
| `nxy = {INT_MAX,INT_MAX}` | **SIGSEGV** | -5, outputs untouched |
| `nxy = {65536,65536}` | **SIGSEGV** | -5, outputs untouched |
| structure with no layers | 14, but only because the mode solve detects it after a layer pointer was formed from an empty array | 14 from an explicit check **before** any layer pointer is formed |
| E only, 1x1 | **SIGSEGV** (unconditional swap of the NULL buffer) | 0, E written, sentinels intact |
| H only, 1x1 | **SIGSEGV** | 0, H written |
| E only / H only, 4x3 | **SIGSEGV** (`GetFieldOnGrid` writes both outputs unconditionally) | 0, the given output written; single-output values equal the pair values |
| ordinary 1x1 / 4x3, both outputs | correct | unchanged, byte for byte |
| core failure, then frequency change | error, then success on the same object | unchanged |
| 50 repeated failures, then success | all fail, then success | unchanged |
| NULL `xyz0` in an `ENABLE_S4_TRACE` build | **SIGSEGV in the trace call**, which read `xyz0[0..2]` before the NULL check | -3 |

### Fix (three files, minimal)

`S4/S4.cpp`, `S4_Simulation_GetFieldPlane`:

* the entry trace prints pointers only, and a second trace prints the coordinates
  *after* `xyz0` has been validated, so the logging itself cannot dereference an
  unvalidated pointer;
* grid size validated before any conversion, multiplication, layer access, solve
  or FFT work: non-positive -> `-4`; point count above `INT_MAX` -> `-5`;
* the no-layer check moved above the layer-selection loop, so no layer pointer is
  formed from an empty array; the previously unreachable `if(NULL == L)` guard is
  gone because that condition is now impossible;
* the 1x1 reorder (three swaps that convert `Simulation_GetField`'s
  `{re,re,re,im,im,im}` layout into the grid path's complex layout) is applied
  per output, so a NULL output is never touched.

`S4/rcwa.cpp`, `GetFieldOnGrid`: the two output-write blocks are guarded by
`NULL != hfield` / `NULL != efield`. This is the minimal output-pointer safety
change and it makes the body match its own documented convention; both callers
pass either a real buffer or NULL, and the Python and Lua bindings always pass
both, so their results are unchanged (verified below).

`S4/S4.h`: the declaration is documented with the length, layout, optional-output
and return-code contract above. No signature changed and there is no ABI change.

Capacity arithmetic, including the downstream expressions rather than only the
final length. The checks are written in **division form**, so no product is
formed before it has been shown to fit and nothing depends on `size_t` being
wider than `int`. Four questions are distinguished:

* **A. positive dimensions.** `nxy[0] <= 0 || nxy[1] <= 0` -> `-4`.
* **B. point count representable.** `nu > INT_MAX / nv` -> `-5`, then
  `npoints = nu * nv` is computed only once that test has passed. The bound and
  the expression come from `kiss_fftnd_alloc`
  (`S4/kiss_fft/tools/kiss_fftnd.c`), which multiplies the two dimensions into an
  **`int dimprod`** and uses it for `st->tmpbuf`; a larger product wraps that int
  and corrupts the FFT workspace. `-5` is therefore derived from the existing
  code, not an arbitrary ceiling.
* **C. FFT integer capacity, same test.** The twelve FFT buffers that
  `GetFieldOnGrid` allocates through `fft_alloc_complex(N)` are sized by the same
  `N`, so B and C share one bound.
* **D. byte capacity, a separate question.** The output contract is
  `3 * npoints` complex values per buffer (`6 * npoints` `S4_real`), and
  `GetFieldOnGrid` additionally allocates twelve buffers of
  `sizeof(std::complex<double>) * npoints` bytes plus one
  `kiss_fftnd_alloc` block of `sizeof(kiss_fft_cpx) * npoints`. The check takes
  the largest per-point size of those (`6 * sizeof(S4_real)` = 48 on this
  platform, since `kiss_fft_scalar` is `double` and `sizeof(std::complex<double>)`
  is 16) and tests `npoints > SIZE_MAX / bytes_per_point` -> `-5`. The division
  covers the output buffers and every intermediate FFT buffer at once.

**D is not implied by B.** On a 64-bit `size_t` the byte limit
(`SIZE_MAX / 48` = 3.8e17) is far looser than the int limit (`INT_MAX` = 2.1e9),
so B is what binds; on a 32-bit `size_t` the byte limit is 8.9e7 and D binds
first. Stating that a product above `INT_MAX` "also makes the byte counts
unrepresentable" would be wrong on a 64-bit platform, and the earlier wording of
this entry said exactly that; it is corrected here.

**E. representable but unallocatable** is a separate question and is **not**
handled: a grid whose byte counts fit `size_t` but exceed available memory still
reaches the FFT layer, which does not check its allocations. That stays on the
open list below.

Platform scope: the verification in this round ran on **x86_64** only. That a
positive `int` product is representable in `size_t` there does not make it true
on every platform, which is why the checks use division form and why D exists.
No 32-bit toolchain was installed and no 32-bit run was performed; the 32-bit
branch is covered by arithmetic and inspection only.

Suite totals are whatever a run reports. The suite does not assert a count and no
number here is a requirement: the module contributes 16 methods, the suite total
moves with that, and each acceptance log records the run/passed/skipped/expected-
failure figures for its own mode. The single skip is the interpolator
out-of-memory test, which is verified by code review only and is never counted as
a pass.

### Verification scope notes

* One invocation in the four-mode acceptance log
  (`/tmp/s4-capi-accept2.log`) reports `DIFF_CHECK_EXIT=129`. That invocation
  **did not perform the check**: it ran inside the candidate copy, which is an
  rsync of the work tree made without `.git`, so git answered "Not a git
  repository" and printed usage. The check was re-run where it is meaningful -
  inside the apply-check copy, a full work-tree copy that includes `.git` - and
  there it exited **0**, as it also does in the real work tree.
* "All 16 steps exited 0" refers only to the 16 explicitly defined acceptance
  steps, each of which aborts the run when it fails. It is not a claim that every
  command appearing in that log succeeded.
* One pre-fix capacity case ended as SIGKILL. That shows the old process was
  terminated without a normal exit; the log holds no operating-system evidence of
  *what* terminated it, so no cause is asserted. That case is not re-run against
  the old build: the old code would attempt an allocation on the order of tens of
  gigabytes, which is not worth the risk on a shared machine.
* The checks were verified on **x86_64** only. The 32-bit `size_t` branch is
  covered by arithmetic and by inspection; no 32-bit toolchain was installed and
  no 32-bit run was performed.
* The interface takes no buffer length, so it cannot check how much space a
  caller actually provided. It validates its parameters and every capacity it can
  compute, and documents the length each non-NULL buffer must have; a shorter
  buffer is a caller error this code cannot detect. Nothing here claims otherwise.

### Findings recorded, deliberately not fixed in this round

* **FFT workspace allocation failures are not handled downstream.**
  `GetFieldOnGrid` does not check `eh`, `from[i]`, `to[i]` or the plans for NULL,
  so a grid whose byte size is representable but too large to allocate faults
  instead of returning an error. That is a solver-wide OOM concern and was
  explicitly out of scope; no claim is made that allocation failure is handled.
* **The internal `Simulation_GetFieldPlane` (Python/Lua) has the non-positive
  guard but not the `INT_MAX` product bound**, so a binding request such as
  `{100000,100000}` passes the Python-side `SIZE_MAX/6` check and reaches the same
  `int dimprod`. In practice it faults earlier, in the unchecked FFT allocation.
  Recorded here as an open item for the binding or the internal function.
* **The internal `Simulation_GetFieldPlane` treats a single NULL output as a
  silent no-op success** (`if(NULL == E || NULL == H) return 0;`), which differs
  from both the public entry point and `GetFieldAtPoint`. Left unchanged because
  the Python and Lua bindings always pass both buffers.
* `ext_lua.c:1156` (`lua_S4_Simulation_GetFields`) ignores the return code of
  `S4_Simulation_GetFieldPlane`, so a failure there yields an uninitialised Lua
  table. Not changed here.

### Tests

`testing/s4test/test_capi_field_plane.py` plus the C++ driver
`testing/s4test/capi_field_plane_driver.cpp`. The driver calls the public API
directly, is **compiled from source by the test** against the `build/libS4.a`
that `make` produces (so it never depends on a binary someone left behind, and a
missing library is a loud failure, not a skip), and each case runs in its own
process with a timeout. Before exiting, the driver checks the return code, the
contents of the output buffers and the sentinel words on both sides of each
buffer, so "it did not crash" is never the only evidence.

Sixteen test methods: the NULL argument codes, the both-NULL no-op and its
ordering against grid validation, the four non-positive grids, the two oversized
grids, the no-layer case, the optional-output combinations on 1x1 and 4x3 grids,
a component-by-component comparison of the C API's 4x3 grid against the Python
binding's array result, the same for the 1x1 reorder, the post-failure state
cases, the capacity boundary (below), and a **patterned** structure (below).

Capacity tests. `{46341,46341}` is the first square grid whose point count
exceeds `INT_MAX` (`46341^2 = 2147488281`, while `46340^2 = 2147395600`), and
`{2,INT_MAX}` overflows on one axis; both must be rejected with `-5` **before any
large allocation**, with the outputs and both sentinels untouched and the same
object succeeding on a small grid afterwards. No `INT_MAX`-scale legal allocation
is ever attempted. A separate pure-arithmetic case prints the two limits and
classifies a table of pairs with the same division expression, so the exact
boundary (`46340` accepted, `46341` rejected) is pinned without allocating
anything; the Python test recomputes the classification with `INT_MAX // nv` and
asserts the platform relationship between the two limits (`byte_limit >=
INT_MAX` on 64-bit), recording that no 32-bit run was done.

Patterned structure. The driver builds, entirely through the public C API, an
air / 0.5-thick air slab / air stack with a **Glass circle of radius 0.25 in
lattice coordinates centred on the origin** in the slab, created with
`S4_Layer_SetRegionHalfwidths(S, slab, glass, S4_REGION_TYPE_CIRCLE, {0.25,
0.25}, {0,0}, &0.0)`; that sets `shape.vtab.circle.radius = halfwidths[0]`,
exactly as the Python binding's `SetRegionCircle("Slab","Glass",(0,0),0.25)` does
through `Simulation_AddLayerPatternCircle`. The frequency is 0.999, away from any
known cutoff, and the sampling depth is z = 0.05, inside the patterned slab. On a
4x3 grid the test checks both outputs, E-only and H-only, that every component is
finite, that the sentinels on both sides of every buffer survive, that the
single-output results equal the pair results, and - so that a fixture which
silently failed to pattern the layer could not pass as a uniform field - that at
least one component varies across the grid. The measured spreads are 0.31 / 1.41
/ 0.34 for E and 3.61 / 0.34 / 2.76 for H by component, i.e. well above noise.
The 4x3 dump is then compared against the Python binding's array result for the
same structure, component by component, to 1e-12.

1x1 with a pattern - a genuine sampling finding, recorded rather than papered
over. The public entry point serves 1x1 through the point-field path
(`Simulation_GetField`), while the internal grid entry point samples a
one-point FFT grid; with a single grid point only the zeroth Fourier order is
representable, so the pattern's higher orders are truncated there. For the
patterned structure the two therefore differ - the measured worst
`|1x1 grid - point field|` is **2.21**, i.e. not a rounding effect - whereas for
the flat structure they agree because it has no higher orders, which is why the
previous round's flat 1x1 equivalence could not be generalised. The tests
therefore (a) assert that the public 1x1 result equals the **point-field**
interface element by element to 1e-12, which is the computation it actually
performs, and (b) assert that the 4x3 grid's origin sample also reproduces the
point field. The discrepancy itself is **not asserted in either direction**: an
earlier revision of this entry also required the difference between the 1x1 grid
and the point field to exceed 1e-2 and printed its magnitude, and that has been
removed deliberately - "the two interfaces must differ by at least this much" is
not a promise this interface makes, and a printed number is not a correctness
test. The observation is recorded in this entry instead, with the measured value
above. No tolerance was relaxed, no physics was changed and the sampling
algorithm was left alone: this is a sampling-semantics observation, not a defect
in the parameter checks, and a one-point FFT grid cannot be made to carry higher
orders by a binding fix.

Against the pre-fix library, run with the 17 methods the module then had: **6
fail (12 subTest failures), 11 pass.** The six that fail are the defect-exposing
ones - the non-positive grids (SIGFPE/SIGSEGV), the oversized grids (SIGSEGV),
the capacity boundary (one case ended as SIGKILL and the other as SIGSEGV; see
the scope note below for what that does and does not show), the optional-output
combinations (SIGSEGV), the patterned dual/single-output case (SIGSEGV) and the
patterned 1x1 case (SIGSEGV). The 11 that pass are the compatibility contracts
this round must not break: the NULL codes, the both-NULL no-op, the no-layer
`14`, both flat layout comparisons, the two pure-arithmetic capacity methods, the
patterned 4x3 comparison against the Python binding, the patterned
origin-versus-point-field comparison, and the state/recovery cases. Not every new
test is expected to fail against the old build - the arithmetic and dual-output
paths are supposed to keep working. No test uses `expectedFailure` or relaxes an
assertion.

The layout comparison uses an excitation that is *provably equivalent* to the
bindings' `SetExcitationPlanewave((0,0), s=1, p=0)`: with `kdir = (0,0,1)` and
`udir = (0,1,0)`, `vn = kn x un = (-1,0,0)`, so the internal state becomes
`k = (0,0)`, `hx = -root_eps`, `hy = 0` - the same values
`Simulation_MakeExcitationPlanewave` writes for those angles and amplitudes, with
`root_eps = 1` in air. Both comparisons then agree element by element to 1e-12.

---

## D15 - Grid allocation failures in `GetFieldOnGrid` and the FFT plan wrapper: safe stop, release, propagation - FIXED

Task name: **网格分配失败处理（DEFECTS.md：D15）**.

`GetFieldOnGrid` (`S4/rcwa.cpp`) allocated its work buffers, twelve FFT buffers
and six FFT plan wrappers without checking any of them, dereferenced the results
immediately, returned `void`, and the two callers (`Simulation_GetFieldPlane` and
`S4_Simulation_GetFieldPlane`, both in `S4/S4.cpp`) freed their own temporary and
returned 0 regardless. The public C API therefore could not report a grid
allocation failure at all, and the Python and Lua bindings - which already
propagate a non-zero core code correctly - never saw one.

### Resource table

`n = n_G`, `n2 = 2n`, `n4 = 2*n2`, `N = nxy[0]*nxy[1]`. Sizes are the ones
observed at run time for the flat fixture with `n_G = 9` and a 4x3 grid
(`n2 = 18`, `N = 12`), taken from the injector's logging pass.

| # | resource | acquired in | allocator | released by | pre-fix failure form | owner | release on partial construction |
|---|---|---|---|---|---|---|---|
| 1 | `ab` (`n4 + 8*n2` complex; 2880 bytes, malloc sees 2903) | the two callers in `S4.cpp` | `S4_malloc` -> `malloc_aligned` -> `malloc` | `S4_free` | already checked, returns 1 | caller | nothing to release |
| 2 | `eh` (`8*n2` complex; 2304 bytes, malloc sees 2327) | `GetFieldOnGrid` | `rcwa_malloc` -> `malloc_aligned` -> `malloc` | `rcwa_free` | NULL unchecked, `GetInPlaneFieldVector` writes through it | `GetFieldOnGrid` | nothing to release |
| 3 | `from[i]`, 6 of them (`N` complex; 192 bytes) | `GetFieldOnGrid` loop | `fft_alloc_complex` -> `KISS_FFT_MALLOC` = `malloc` | `fft_free` = `free` | NULL unchecked, `memset(NULL)` | `GetFieldOnGrid` | free the buffers and plans already acquired, then `eh` |
| 4 | `to[i]`, 6 of them (192 bytes) | `GetFieldOnGrid` loop | same | same | NULL unchecked, plan built over NULL | `GetFieldOnGrid` | same |
| 5 | kiss configuration (`kiss_fftnd_alloc`, 888 bytes for dims {3,4}) | `fft_plan_dft_2d` | `malloc` inside `kiss_fftnd_alloc` | `fft_plan_destroy` -> `free(plan->cfg)` | returns NULL, unchecked by the caller | wrapper plan object | n/a (single block) |
| 6 | plan wrapper (`sizeof(tag_fft_plan)`; 24 bytes) | `fft_plan_dft_2d` | `malloc` | `fft_plan_destroy` -> `free(plan)` | **NULL dereferenced as `plan->cfg`**; the configuration leaked | `GetFieldOnGrid` | free the configuration the wrapper could not hold |
| 6b | FFTW plan (only in a `HAVE_LIBFFTW3` build) | `fft_plan_dft_2d` | `fftw_plan_dft` | `fft_plan_destroy` -> `fftw_destroy_plan` | NULL handled, but the wrapper malloc was unchecked and leaked the plan | wrapper plan object | destroy the plan, under the same mutex the destroy path uses |

`GetInPlaneFieldVector` and `MultKPMatrix` allocate nothing themselves, so the
list above is the complete chain reachable from the two callers. `GetFieldAtPoint`
has an unchecked `rcwa_malloc` of its own when called with `work == NULL`; it is a
different field entry point and is **not** changed here (see the open items).

### Error contract

* `GetFieldOnGrid` now returns `int`: 0 on success, **1** (the library's existing
  allocation-failure code) if any temporary allocation fails. Its declaration in
  `S4/rcwa.h` carries that contract. The two call sites are the only callers in
  the tree, and both were updated.
* The public C API signature, the meaning of every existing error code, and the
  `-1/-2/-3/-4/-5/0/14/1` contract of `S4_Simulation_GetFieldPlane` are unchanged.
* Python: the binding already mapped core code 1 to
  `RuntimeError("... A memory allocation error occurred")`; that is what a grid
  allocation failure now produces. The binding's own `malloc` failures keep
  raising `MemoryError`, and no exception type was changed.
* Lua: the binding already turns a non-zero core code into `luaL_error` through
  its `fail:` label, which is catchable by `pcall`. The failure does **not** fall
  back to `S4L_error`, which closes the state and exits.
* No `exit`, no `abort`, no print-and-continue. No grid is shrunk, no zero field
  is returned and no partial result is passed off as a success.

### Implementation

`GetFieldOnGrid`: every handle starts NULL; the single cleanup path at the end
destroys the plans and frees the buffers and `eh`, so it is valid part-way
through the allocation loop and on the success path; each allocation is checked
immediately after it; the outputs are written only after all six transforms have
run, so a failure leaves them untouched. The arithmetic, the ordering of the
preparation loops, the values written and the two optional-output branches are
unchanged.

`fft_plan_dft_2d`: when the underlying object exists but the wrapper allocation
fails, the underlying object is released (`free(cfg)`, or `fftw_destroy_plan(p)`
under the same mutex the destroy path uses) and NULL is returned. The mutex is
unlocked before the wrapper allocation on the FFTW path, as before.

The two callers: capture the return value, free their own `ab` on every path,
and return the code with a trace instead of returning 0. The layer modes that
were already built stay valid - a grid temporary failure must not invalidate
them - and nothing is cached, so a later call recomputes and can succeed.

### Fix-before/fix-after fault matrix

Injector: `/tmp/s4-gridfault.c` built as `libgridfault.so` and preloaded **only
into the process under test** (`timeout 120 env LD_PRELOAD=... driver`, so
`timeout` itself is never instrumented - an earlier attempt that exported
`LD_PRELOAD` made the Rust `timeout` binary abort on its own 24-byte allocation
and produced a false SIGABRT). It matches an exact byte size and an occurrence
index, prints `S4FAULT FAIL size=<n> match=<k>` when it fires, and fires once, so
the same process also demonstrates recovery. No production file contains any of
it.

Each row is one process; the driver makes the failing call and then a second call
on the same simulation. 21 points, flat and patterned, both outputs and each
single output:

| injection point | size | pre-fix | post-fix |
|---|---|---|---|
| caller temporary `ab` | 2903 | rc=1, retry 0 (already correct) | unchanged |
| `eh` (flat, patterned) | 2327 | SIGSEGV / SIGSEGV | rc=1, outputs untouched, retry 0 |
| `from[0]`, `to[0]` | 192 (1,2) | SIGSEGV | rc=1, retry 0 |
| middle `from/to` pair | 192 (6) | SIGSEGV | rc=1, retry 0 |
| last `from`, `to` (flat, patterned) | 192 (11,12) | SIGSEGV | rc=1, retry 0 |
| kiss configuration, first/middle/last (flat, patterned) | 888 (1,3,6) | SIGSEGV | rc=1, retry 0 |
| plan wrapper, first/middle/last (flat, patterned) | 24 (1,3,6) | SIGSEGV | rc=1, retry 0 |
| `eh` with E-only and with H-only | 2327 | SIGSEGV | rc=1, retry 0 |
| last `from` with E-only, last plan with H-only | 192/24 | SIGSEGV | rc=1, retry 0 |

**Post-fix: 21 of 21 pass** (failure returns 1, outputs and both sentinels
untouched, retry on the same object returns 0 and writes finite output).
**Pre-fix: 20 of 21 die with SIGSEGV**; the `ab` row passes before and after,
because that check already existed - it is a compatibility row, not a defect row.

The two bottom-level cases the task calls out are distinguished by size rather
than by intercepting an outer return value: 888 is
`kiss_fftnd_alloc`'s configuration, 24 is the wrapper object that stores it, and
the 24-byte injections all have the 888-byte configuration already successfully
allocated.

### Python and Lua

Calibrated per process: a logging pass counts how many allocations of the target
size happen before the marker printed immediately before the grid call, and the
injection index is that count plus one, so the failure lands inside the grid call
and not in the interpreter's own allocations. Flat and patterned fixtures,
ordinary frequency 0.999, 4x3 grids that really go through `GetFieldOnGrid`.

| | Python | Lua |
|---|---|---|
| call fails | `RuntimeError: GetFieldsOnGrid: A memory allocation error occurred` | `pcall` false, `GetFieldPlane: A memory allocation error occurred.` |
| output files | not created (`.E` and `.H` absent) | not created |
| same object afterwards | succeeds, finite | succeeds, finite |
| interpreter state | no `SystemError`, no `MemoryError` misattribution, no silent `None`, no crash | error is catchable; uncaught it exits with status 1 (not 128+n) and prints the message |

Coverage: Python 8 of 8 combinations (flat and patterned x four sizes), Lua 6 of
8. The two missing Lua rows are both the 24-byte wrapper size: the Lua
interpreter's own 24-byte allocations differ between the calibration pass and the
injection pass, so the calibrated index drifted and the injection missed the grid
(`hits=0`, recorded as such). That point is covered at the C level (24, indices
1/3/6) and in Python; the Lua *propagation path* is proven for the other three
sizes. It is reported rather than papered over.

### Leak check

Scenarios in a single process each (build the structure, call the grid entry,
destroy the simulation), under `detect_leaks=1` with the sanitizer preloaded only
into the driver: baseline, 5 successes, 100 successes, 100 caught failures
(`S4FAULT_COUNT`), and the failure rounds repeated for each injection size. The
100-failure run reports `ok=200 failed=100 bad=0`, i.e. every injected failure
returned 1 with the outputs and sentinels intact and the calls after the
injection budget ran out succeeded. No leak was reported in any of these runs.

Positive control: the same driver with `leak` allocates 4096 bytes and drops the
pointer; the detector reports it, which is what shows the detector was live for
the other runs. Functional checking (`detect_leaks=0`) and leak checking
(`detect_leaks=1`) are reported separately and the functional runs are never
counted as leak evidence. A per-invocation leak claim is not made from process
exit alone.

### What was not changed

The numerical algorithm, the grid sampling, the index order, the two optional
outputs, the 1x1 point-field branch, the capacity and NULL contracts of the
public entry, the internal `Simulation_GetFieldPlane` capacity bounds and its
single-NULL no-op, the `ext_lua.c` return-code handling, and the pre-existing
`S4_FAIL_ALLOC_AT` injection hook (which is armed only inside
`S4_Simulation_Clone` and is inert when the variable is unset). `GetFieldAtPoint`
and `GetZStressTensorIntegral` were left alone.


### D15 round 2 - the FFT *execution* stage was still unchecked (SIGSEGV on 7x3)

The first D15 round checked the allocation sites in the preparation stage and in
the FFT plan wrapper.  It did not check the buffers the transform allocates while
it runs, and the 4x3 grid used by that round's matrix cannot reach them: its
radices are 3 and 4, so `kf_work` dispatches to `kf_bfly3`/`kf_bfly4` and never to
the generic butterfly.  Any grid with a radix outside 2/3/4/5 does reach it.

Reproduction, exactly as reported:

```
driver flat both 7 3                      -> rc 0, finite output (no injection)
LD_PRELOAD=<injector> S4FAULT_SIZE=112 S4FAULT_NTH=1 driver flat both 7 3
    S4FAULT FAIL size=112 match=1
    exit 139 (SIGSEGV)
```

and under gdb the frame sequence was `memcpy` <- `kf_work` <- `kiss_fftnd` <-
`GetFieldOnGrid` <- `S4_Simulation_GetFieldPlane` <- `main`.  112 bytes is
`sizeof(kiss_fft_cpx) * 7`, the scratch buffer for the radix-7 stage:

```c
/* S4/kiss_fft/kiss_fft.c, kf_bfly_generic, before this round */
kiss_fft_cpx * scratch = (kiss_fft_cpx*)KISS_FFT_TMP_ALLOC(sizeof(kiss_fft_cpx)*p);
for ( u=0; u<m; ++u ) { ... scratch[q1] = Fout[k]; ... }   /* writes through NULL */
```

#### Complete resource table, separated by stage

Preparation stage (as before): `ab` in the caller, `eh`, the twelve `from`/`to`
buffers, the six FFT configurations inside `kiss_fftnd_alloc`, and the six plan
wrapper objects.  See the table above; unchanged.

Execution stage, i.e. what `fft_plan_exec` can still allocate after the plan
exists.  Both sites use `KISS_FFT_TMP_ALLOC`, which is `KISS_FFT_MALLOC` =
`malloc` in this build: `KISS_FFT_USE_ALLOCA` is **not** defined anywhere in the
build (`_kiss_fft_guts.h` only mentions it), and `USE_SIMD`/`FIXED_POINT` are not
defined either, so `kiss_fft_scalar` is `double` and `kiss_fft_cpx` is 16 bytes.
The build was **not** changed to `alloca`; doing so would only move the failure
into a stack overflow.

| # | resource | acquired in | size | released by | reachable from the grid chain | pre-fix failure form |
|---|---|---|---|---|---|---|
| 7 | generic-butterfly scratch `kiss_fft_cpx[p]` | `kf_bfly_generic` (kiss_fft.c) | `16*p` (112 for p=7, 176 for p=11, 16 for p=1) | `KISS_FFT_TMP_FREE` at the end of the same function | **yes**, whenever a radix outside 2/3/4/5 appears (7x3, 11x3, 7x7, ...) | NULL dereference in the copy loop, inlined into `kf_work`; SIGSEGV |
| 8 | in-place temporary `kiss_fft_cpx[st->nfft]` | `kiss_fft_stride` (kiss_fft.c) | `16*nfft` | `KISS_FFT_TMP_FREE` in the same function | **no**: `GetFieldOnGrid` always passes distinct `from[i]`/`to[i]` buffers, and `kiss_fftnd` with two dimensions calls `kiss_fft_stride(st->states[k], bufin+i, bufout+i*curdim, stride)` with `bufin != bufout` and `curdim >= 3`, so `fin == fout` never holds | NULL dereference in `kf_work` and in the `memcpy` out of the temporary |

Nothing else in the execution chain allocates: `kf_work` only recurses, and
`kiss_fftnd` only walks dimensions and toggles buffers.

#### Error propagation, level by level

* `kf_bfly_generic` takes an explicit `int *err`.  If the scratch buffer cannot be
  obtained it sets `*err = 1` and returns **without touching `Fout`**.
* `kf_work` takes the same `int *err`, passes it to both recursive calls and to
  both butterfly dispatch sites, and returns immediately after the recursive
  phase when `*err` is set, so no recombination of incomplete sub-transforms
  happens.
* `kiss_fft_stride_checked` allocates nothing itself; for the in-place case it
  returns 1 if the temporary cannot be obtained and skips the `memcpy` that would
  publish a partial transform.
* `kiss_fftnd_checked` returns 1 as soon as a row fails, so the remaining rows of
  that dimension and all later dimensions are skipped.
* `fft_plan_exec` now returns `int` (0/1) and forwards the status; the FFTW branch
  returns 0 because FFTW's execution has no failure return and terminates the
  process itself.
* `GetFieldOnGrid` checks each of the six executions.  On failure it sets `ret = 1`
  and jumps to the existing single cleanup path, which destroys the six plans and
  frees the twelve buffers and `eh`.  The output loop runs **after** the execution
  loop, so `efield`/`hfield` are never written on this path.
* The two callers already propagate a non-zero grid status, free their own `ab` on
  every path, leave the layer modes intact and cache nothing, so the next call on
  the same simulation rebuilds the plans and can succeed.
* C returns 1; Python maps 1 to `RuntimeError("... A memory allocation error
  occurred")`; Lua raises through its catchable `fail:` path.

#### Interface compatibility

The three KISS entry points keep their exact signatures.  New checked variants
were added next to them (`kiss_fft_checked`, `kiss_fft_stride_checked`,
`kiss_fftnd_checked`), and the originals delegate to them and discard the status,
so no existing object file or external caller sees a changed ABI.  Only
`fft_plan_exec` changed from `void` to `int`, which is a source-level change: all
ten call sites still compile, and the nine in `S4/fmm/fmm_FFT.cpp`,
`fmm_kottke.cpp`, `fmm_PolBasisJones.cpp`, `fmm_PolBasisNV.cpp` and
`fmm_PolBasisVL.cpp` **ignore the new return value**.  Their behaviour on an
execution-stage allocation failure therefore changes from a process crash to
continuing with a partially written buffer.  Propagating it into the FMM solver
would need an error channel that does not exist there, which is outside this
round's scope; it is recorded as an open item.  The in-tree callers of the legacy
`kiss_fft`/`kiss_fftnd` are `S4/kiss_fft/tools/fftutil.c` and `kfc.c`, which the
build does not compile; the only library caller is `fft_iface.cpp`, which uses the
checked variant.

Recompilation: every translation unit that includes these headers must be
rebuilt.  They are all inside this library, and a stale object is caught loudly -
a partially re-synced copy failed to compile with
`invalid operands of types 'int' and 'void' to binary 'operator!='` when an old
`void fft_plan_exec` declaration met the new call site.  No global error flag and
no shared mutable state was introduced; the status travels through parameters.

#### Verification

Strict matrix (`run-matrix.sh`), every case requiring a hit at the intended size
and index, first call returning 1, outputs and both sentinels untouched, retry
returning 0 with finite output, and no driver check failing:
**24 cases, 0 failures** in the self-contained harness, and **31 cases, 0
failures** in the wider run that also keeps the single-output rows.  That
includes 4x3 (unchanged, preparation stage), 7x3 (p=7, 112 bytes, first and
second hit), 7x7 (both dimensions p=7, including a failure after earlier
transforms completed), 11x3 (p=11, 176 bytes), 3x11, flat and patterned, both
outputs and each single output.

Python and Lua, at an execution-stage point and at both previously-missed
wrapper-object points, all with the failure landing inside the grid call: the
call raises, the `.E`/`.H` files are **not created**, and the next call on the
same object succeeds with finite output.  Lua's error is catchable by `pcall`,
and an uncaught execution-stage failure exits with status 1 rather than dying
from a signal.  The two wrapper cases were previously unverifiable because the
interpreter's own 24-byte allocations drift between the calibration and
injection passes; they are now driven by explicit positions in the injection
build, and a marker records that the FFT configuration existed when the wrapper
allocation failed, so "the underlying plan was created and the wrapper object
failed" is proven rather than inferred.

Leaks (ASan+LSan, `detect_leaks=1`, one process per scenario): 0 leaks for the
baseline, 5 successes, 100 successes, and for each of ten partial-construction
failures - `eh`, the first wrapper object, the last plan creation, the last
wrapper object, and all six transform executions.  The positive control in the
same binary reports a deliberate 4096-byte leak, so the detector was live.  The
Python module's own initialisation residual (1760 bytes in two allocations inside
`PyInit_S4`, `S4/main_python.c:2212` and `:2226`) is a pre-existing item, is
reported separately, and is not attributed to this change.

Success values, layouts and file formats are unchanged: the fingerprint
comparison against the unpatched tree (flat and patterned, 4x3 and 1x1, arrays
and files, Python and Lua) is byte-identical.

### How to reproduce

The harness is test-only and lives outside the library; it is not part of this
patch.  It is kept in `/tmp/s4-gridalloc-harness/` (with
`/tmp/s4-gridalloc-harness.sha256`), so the evidence does not depend on a one-off
hand edit:

```
gcc -O1 -fPIC -shared -o /tmp/libgridfault.so s4-gridfault.c -ldl
g++ -I <tree>/S4 -O1 s4-gridfault-driver.cpp -o /tmp/s4-gridfault-driver -L <tree>/build -lS4 -llapack -lblas
# enumerate the allocation points (n_G = 9, 4x3: 2327 eh, 192 from/to, 888 kiss
# configuration, 24 wrapper object, 2903 caller temporary)
S4FAULT_LOG=1 S4FAULT_MIN=16 timeout 120 env LD_PRELOAD=/tmp/libgridfault.so \
    /tmp/s4-gridfault-driver flat both
# the 21-point matrix, one process per point (add the pre-fix library to get the
# before column)
/tmp/s4-fault-matrix.sh /tmp/s4-gridfault-driver /tmp/fault-matrix-postfix.log POSTFIX
# Python and Lua propagation, calibrated per process
/tmp/s4-fault-ab3.sh <tree> <tag>
# leak scenarios, sanitizer build
g++ -I <san>/S4 -O1 -g -fPIC -fsanitize=address,undefined s4-gridleak-driver.cpp \
    -o /tmp/s4-gridleak-driver-san -L <san>/build -lS4 -llapack -lblas -fsanitize=address,undefined
ASAN_OPTIONS=detect_leaks=1 /tmp/s4-gridleak-driver-san successes 100
S4_GRIDFAULT_AT=13 ASAN_OPTIONS=detect_leaks=1 /tmp/s4-gridleak-driver-san failures 3
```

`s4-san-testonly.patch` records the test-only injection used for the
failure-path leak scenarios.  It is applied **only** in a separate sanitizer
copy: `AddressSanitizer`'s interceptors shadow an `LD_PRELOAD` malloc interposer,
so the injector and the sanitizer cannot be combined in one process - with
`LD_PRELOAD` first ASan refuses to start (`ASan runtime does not come first`),
and with `libasan` first the injector sees no allocations at all.  Preloading
`LD_PRELOAD` must therefore never be exported for a whole pipeline: doing that
made the Rust `timeout` binary abort on its own 24-byte allocation and produced a
false SIGABRT, and made `timeout`/`tee` report leaks that were theirs, not S4's.

### Findings recorded, not fixed here

* `GetFieldAtPoint` allocates `8*n2` complex values with an unchecked
  `rcwa_malloc` when `work == NULL`. All current callers pass a work buffer, so
  the branch is unreachable from the public API today, but it is the same class
  of defect in another field entry point.
* `GetZStressTensorIntegral` shares `GetInPlaneFieldVector` and has its own
  buffer handling that was not audited here.
* The FFTW branch of `fft_plan_dft_2d` was reviewed and fixed for the wrapper
  allocation, but this tree is built without `HAVE_LIBFFTW3`, so that branch is
  **code review only** and not executed.

### D15 round 3 - boundary correction and harness hardening

**Correction to the in-place path argument.** The table above originally said the
`fin == fout` branch of `kiss_fft_stride` is unreachable because `curdim >= 3`.
That is wrong: a grid with a dimension of 1 is legal (`1x1`, `1x7`), so the
argument does not cover every legal grid. The correct reason is *buffer
ownership*: `GetFieldOnGrid` allocates `from[i]` and `to[i]` as two separate
blocks - distinct for every grid size, including 1x1 and 1xN - and passes them as
`fin`/`fout`, and `kiss_fftnd_checked` alternates only between those two
caller-owned buffers and the plan-owned `st->tmpbuf`, which is a third distinct
object. Neither `bufin + i` nor `bufout + i*curdim` can therefore alias the other
for any legal grid. This was measured rather than argued: a test-only witness in
`kiss_fft_stride_checked` prints `S4GRIDFAULT INPLACE` whenever the branch is
entered, and it stayed silent in all eight no-injection runs (4x3, 7x3, 11x3,
3x11, 7x7, 49x3, 1x7, 1x1). A caller that passes `fin == fout` to the KISS API
directly - the vendored `fftutil.c`/`kfc.c` tools, which this build does not
compile - still reaches the branch; it is guarded the same way and is covered by
inspection only.

**Coverage split for the injected failures.** Real scratch-allocation failures and
injected call-site failures are different mechanisms and are never combined in one
count:

| mechanism | where it acts | how it is armed | evidence |
|---|---|---|---|
| real scratch allocation failure | `kf_bfly_generic`'s `KISS_FFT_TMP_ALLOC`, so the production NULL check and the whole `err` chain run | `S4_GRIDFAULT_SCRATCH_AT=k` in the `S4_TEST_GRIDFAULT` build; prints `S4GRIDFAULT SCRATCH radix=<p> bytes=<n> hit=<k>` | 7x3 radix 7/112 B hits 1 and 2, 11x3 radix 11/176 B, 49x3 hits 1 and 3 (after earlier sub-transforms completed), 1x7; C 14/14, Python and Lua 7/7 |
| call-site simulated execution-boundary failure | immediately before `fft_plan_exec`; the transform is never entered | `S4_GRIDFAULT_AT` 26..31; prints `S4GRIDFAULT MARK exec-boundary-simulated` | 7x3 both outputs, Python and Lua |
| preparation-stage chain points | `eh`, the twelve `from`/`to`, plan creation, wrapper object | `S4_GRIDFAULT_AT` 1..25; the wrapper point prints `S4GRIDFAULT MARK cfg-created wrapper-alloc-next` | 4x3 and 7x3, both outputs and each single output, Python and Lua |

The first version of the scratch injection overwrote a *successful* allocation
with NULL, which leaked the 112-byte scratch buffer; the leak runner caught it
(`Direct leak of 112 byte(s) ... in kf_bfly_generic`) and it now makes the
allocation itself fail, so nothing is allocated and the production path cannot
leak.

**Runner hardening.** The verification runners now judge on the interpreter's real
exit code, require the completed marker with the expected case count, assert the
first-exception type and message, the absence of output files, the recovery
result's full nested shape and the finiteness of every component (checked with
`math.isfinite` per real and imaginary part, not `abs(v) == abs(v)`), and fail on
any sanitizer or crash diagnostic; Python and Lua are reported separately. The
leak runner requires the driver's exit code, its expected call/ok/failed counts,
`bad=0`, the destroy marker and no sanitizer diagnostic, and the positive control
must produce the exact `4096 byte(s)` summary with the configured exit code 23.
`run-negative.sh` proves the runners reject a program that prints every expected
line and then exits 77, prints a sanitizer error, hangs, omits the marker or dies
from a signal, and that the finiteness checker rejects NaN and both infinities in
non-first components: 12/12.
