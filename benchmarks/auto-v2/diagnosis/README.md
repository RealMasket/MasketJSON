# Dense-input diagnosis

This standalone tool follows the Auto v2 experiment at `fc03dae`. It does not
change a controller or the public parser. Eight existing inputs are diagnostics,
not a fresh holdout. Frozen binaries from the previous experiment are required
for paired full-parse/lexer measurements; their hashes are checked before use.

```powershell
cmake -S benchmarks/auto-v2/diagnosis -B out/auto-v2-diagnosis-build -DCMAKE_BUILD_TYPE=Release
cmake --build out/auto-v2-diagnosis-build --config Release --parallel 2
ctest --test-dir out/auto-v2-diagnosis-build -C Release --output-on-failure
python benchmarks/auto-v2/diagnosis/run_diagnosis.py --bin out/auto-v2-selected-bin --v1-bin out/auto-frozen-bin --replay out/auto-v2-diagnosis-build/Release/TokenRelocation.exe --inputs out/reservation-matrix-final/data out/lowmemory-holdout-inputs out/auto-heldout-inputs --output out/auto-v2-diagnosis-final --report out/auto-v2-diagnosis.md
```

Single-configuration generators omit `Release` from the executable path. Python 3
is required. Keep the machine idle; do not compile or run other benchmarks while
measuring. Output directories must be new. Inputs are verified against the
previous known-set hashes, not newly generated alternatives. If frozen binaries
are unavailable, rebuild and establish a new recorded control; do not bypass the
hash checks and call it a reproduction of these paired measurements.

The replay uses real `std::vector<Token>` with recorded capacity requests. It
checks every expansion and matches logical moved bytes, growth count and final
capacity to the independent lexer profile. Both v2 schedules are compared to
reserving the exact known token count once. Tokens have deterministic synthetic
metadata: this is a buffer experiment, without lexer scanning or DOM creation.
The exact-count plan assumes offline information, not a proposed public preset.
No timing subtraction assigns an exact percentage of parser cost to relocation.

All six original policies rotate through every timing position once. The three
replay policies rotate separately, twice through every position. Warm-ups, sample
and operation counts match the original v2 experiment. Heap profiles are untimed;
the runner requires the previous deterministic memory observations to match.

The raw result directory preserves exact bytes for cross-file SHA-256 references.
To audit recorded files and regenerate the report without original binaries:

```powershell
python benchmarks/auto-v2/diagnosis/run_diagnosis.py --output benchmarks/results/auto-v2-diagnosis-msvc1951 --report out/auto-v2-diagnosis-audit.md --report-only
```

CI builds the standalone replay on Windows and Linux and checks known relocation
accounting plus rejection of malformed, incomplete and unsupported schedules.
Timing is diagnostic evidence for the measured machine, not a CI speed assertion.

After moving the checkout, configure a fresh build directory. Existing CMake
caches contain the old absolute source/build paths; keep the frozen executable
snapshots for comparisons, and do not attempt to reuse those caches in place.
