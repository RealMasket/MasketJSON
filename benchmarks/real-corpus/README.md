# External corpus and compiler transfer

This study evaluates the frozen selected Auto v3 from `838a26e` on five original
public JSON snapshots, without retuning. `corpus.json` pins upstream repository,
commit, path, byte count, Git blob SHA-1 and SHA-256. Raw data is downloaded into
ignored output and not bundled or relicensed by MasketJSON. Native JSON Benchmark
provides historical Canada, event-catalog and CJK Twitter snapshots; Natural Earth
adds country geometry/attributes, and TypeScript supplies a real dependency lock.
These are convenience examples, not representative samples of users' workloads.

```powershell
python benchmarks/real-corpus/fetch.py out/real-corpus-inputs
```

Existing files are reused only if all checks match. The downloader refuses to
replace a mismatching local file. It never minifies, edits or repeats input data.
The upstream descriptions and source/terms links are in the manifest and report.

Build a static Release library with benchmarks, profiler and private Auto v3.
Selected flags are `AUTO_V3_SPEED_QUARTERS=7`, `AUTO_V3_MEMORY_QUARTERS=6`, both
`AUTO_V3_*_LOOKAHEAD=1`, and default speed/memory budgets 4194304/1048576 bytes.
Timing and heap interception are separate executables. Keep LTO and fast-math off.

The recorded compiler comparison uses MSVC 19.51.36257 and official Clang-cl
23.1.5 on the same Windows x64 machine. Both use Microsoft STL 14.51.36231,
Release CRT /MD and Microsoft link.exe 14.51. The Clang archive URL and SHA-256
are pinned in `plan.json`; no system-wide compiler installation is required.
Clang's resource yvals wrapper includes the same installed MSVC STL headers.
Its compiler-process allocator is unrelated to the benchmark application heap.

Configure Clang-cl from an x64 Visual Studio developer environment, using Ninja,
`CMAKE_CXX_COMPILER` pointing to clang-cl, `CMAKE_LINKER` to MSVC link.exe, and
`CMAKE_BUILD_TYPE=Release`. Both configurations use `/O2 /Ob2 /DNDEBUG` and C++17.
The freeze records exact build information, global flags, compiler-binary hashes,
standard-library header hash and every benchmark executable identity. This holds
OS/STL/runtime constant rather than measuring GCC/libstdc++ or Linux performance.

For a fresh checkout, run these from an x64 Visual Studio developer shell with
CMake and Ninja available. Point the Clang variable at the verified portable
compiler or an equivalent official installation. The recorded study requires the
exact compiler versions above; other versions should use a new pre-recorded plan.

```powershell
$clangExecutable = (Resolve-Path out/real-toolchain/llvm/bin/clang-cl.exe).Path
$linkExecutable = (Get-Command link.exe).Source
cmake -S . -B out/real-msvc-build -G "Visual Studio 18 2026" -A x64 -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DMASKETJSON_BUILD_BENCHMARKS=ON -DMASKETJSON_BUILD_PROFILER=ON -DMASKETJSON_BUILD_AUTO_V3_EXPERIMENT=ON -DAUTO_V3_SPEED_QUARTERS=7 -DAUTO_V3_MEMORY_QUARTERS=6 -DAUTO_V3_SPEED_LOOKAHEAD=1 -DAUTO_V3_MEMORY_LOOKAHEAD=1
cmake --build out/real-msvc-build --config Release --target AutoV3Tools --parallel 2
cmake -S . -B out/real-clang-build -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=$clangExecutable" "-DCMAKE_LINKER=$linkExecutable" -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DMASKETJSON_BUILD_BENCHMARKS=ON -DMASKETJSON_BUILD_PROFILER=ON -DMASKETJSON_BUILD_AUTO_V3_EXPERIMENT=ON -DAUTO_V3_SPEED_QUARTERS=7 -DAUTO_V3_MEMORY_QUARTERS=6 -DAUTO_V3_SPEED_LOOKAHEAD=1 -DAUTO_V3_MEMORY_LOOKAHEAD=1
cmake --build out/real-clang-build --target AutoV3Tools --parallel 2
```

Use `--msvc-build out/real-msvc-build` below for a fresh producer build. The recorded
run reused the unchanged MSVC producer from the preceding Auto v3 stage.

```powershell
python benchmarks/real-corpus/prepare.py --msvc-build out/auto-v3-build --clang-build out/real-clang-build --inputs out/real-corpus-inputs --output out/real-frozen-bin
python benchmarks/real-corpus/run.py --bin out/real-frozen-bin --inputs out/real-corpus-inputs --output out/real-corpus-final
```

Use fresh output directories and an idle machine. Do not compile while timing.
The plan is fixed before timing: eight cyclic rounds over all compiler/preset
pairs, five samples of three operations, plus five warm-ups. Every pair occupies
every absolute position once; each within-compiler preset position occurs twice.
The runner pins logical CPU 0, validates all input/source/executable hashes and
checks every token/value/diagnostic, retained DOM accounting and journal bound.
Canonical result fingerprints must also agree across compilers.

The current resource gates are evaluated separately per compiler, with its own
Balanced >=1 ms criterion. Report every input, including failed gates; do not
change the algorithm to pass this new corpus. Peak is simultaneous requested C++
allocation bytes, not RSS; copied bytes are logical token relocation. The profiler
excludes caller input, stack/root Json, allocator metadata/rounding, direct malloc
and its own bookkeeping. Result creation/destruction is included in ordinary time.

Gather both compiler result folders, metadata, freeze, corpus and plan into a
result root. Preserve each normalized freeze source under `sources/SHA256.txt`.

```powershell
python benchmarks/real-corpus/summarize.py benchmarks/results/real-corpus-windows out/real-corpus-report.md
```

The reporter verifies file/source hashes, complete timing rows, profiles and
journals before evaluating unchanged joint gates. Full rounds and sample spread
remain available. CI fetches the same originals on Windows/Linux and runs
`common.py --build BUILD --inputs DATA --output RESULTS --profiles`; omit profiles
with sanitizers. It checks correctness and accounting without timing assertions.

The Canada speed regression runs on the generated journal. It checks the final
token count and the largest simultaneous request for old and new token slots.
The recorded peak and replay are documented with the fixture.
[Canada expansion analysis](../results/canada-growth.md)

```powershell
python benchmarks/real-corpus/check_canada_growth.py RESULTS/speed-decisions.csv
```

Auto remains private pending representative workload data and wider evidence.
A passing five-file snapshot study is not a hard latency or memory guarantee.
