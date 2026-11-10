# Frozen Auto v3 on external JSON snapshots and two compilers

## Scope and frozen protocol

This evaluates the selected private Auto v3 from `838a26e`; no controller, pressure threshold, budget or coefficient is tuned using these files.
Five immutable public snapshots cover numeric geometry, an indented event catalog, historical CJK social text, country attributes/geometry and a dependency lockfile.
These are external transfer examples, not a random or representative sample of user workloads. The native benchmark snapshots are historical.
Original bytes are used without minification, content editing or synthetic repetition. Raw upstream JSON is downloaded into ignored output and is not redistributed here.

| Snapshot | Original bytes | Upstream revision | SHA-256 |
| --- | ---: | --- | --- |
| [canada.json](https://github.com/miloyip/nativejson-benchmark/blob/478d5727c2a4048e835a29c65adecc7d795360d5/data/canada.json) | 2251051 | `478d5727c2a4` | `f83b3b354030d5dd58740c68ac4fecef64cb730a0d12a90362a7f23077f50d78` |
| [citm_catalog.json](https://github.com/miloyip/nativejson-benchmark/blob/478d5727c2a4048e835a29c65adecc7d795360d5/data/citm_catalog.json) | 1727204 | `478d5727c2a4` | `a73e7a883f6ea8de113dff59702975e60119b4b58d451d518a929f31c92e2059` |
| [twitter.json](https://github.com/miloyip/nativejson-benchmark/blob/478d5727c2a4048e835a29c65adecc7d795360d5/data/twitter.json) | 631514 | `478d5727c2a4` | `a08b769f32b95f426cbc3abafcec65c1a19d3eb544d4ddf320eae142c99efc5d` |
| [natural-earth-countries.json](https://github.com/nvkelso/natural-earth-vector/blob/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_110m_admin_0_countries.geojson) | 838726 | `ca96624a56bd` | `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` |
| [typescript-package-lock.json](https://github.com/microsoft/TypeScript/blob/df43aada644be309fe8ceee3f1254b6eea25a549/package-lock.json) | 158517 | `df43aada644b` | `9ad3d45f3b8c590d96b64b791033dad1f10994db95bd3dc3f9671f9201599672` |

Compiler builds, sources and corpus were frozen at `2026-11-10T16:38:58.545900+00:00`; source revision `a8017e8d00910ada69be05644ed3a41c107c5474`.
Source snapshots are content-addressed and checked against the freeze; all timing/profile files have recorded hashes.
Upstream source context: [Native JSON Benchmark data](https://github.com/miloyip/nativejson-benchmark#json-data),
[Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/), [TypeScript](https://github.com/microsoft/TypeScript).
MasketJSON does not claim that its MIT license relicenses upstream datasets.

## Comparable builds and measurements

Machine: 12th Gen Intel(R) Core(TM) i5-12600KF; Windows-10-10.0.19045-SP0; logical CPU 0.
Both compilers target Windows x64 with Microsoft STL 14.51.36231 and Release CRT /MD. MSVC link.exe 14.51 links both builds.
Clang uses its normal resource wrappers around the same Microsoft STL headers. This isolates a compiler change while holding OS, STL and runtime allocator constant;
it does not measure Linux, libc++, libstdc++ or another allocator. The allocator used by the Clang compiler process is unrelated to measured applications.

| Build | Compiler version | Global flags | Release flags |
| --- | --- | --- | --- |
| msvc | MSVC 19.51.36257.0 | `/DWIN32 /D_WINDOWS /EHsc` | `/O2 /Ob2 /DNDEBUG` |
| clang | Clang 23.1.5 | `/DWIN32 /D_WINDOWS /EHsc` | `/O2 /Ob2 /DNDEBUG` |

C++17, static library, no LTO or fast-math. Eight compiler/preset pairs rotate over eight rounds: each occupies each absolute position once.
Within each compiler every preset occupies each position twice. Each measurement has 5 samples x 3 operations plus 5 warm-ups.
Tables use medians of eight round medians. Loading, shape checks and semantic validation are outside timing; parse includes result destruction.
Ordinary timing builds have no allocation interception or journal hooks. Profiles and traces run separately.
Captured peak counts simultaneous requested C++ new bytes, including old/new token-buffer overlap; it excludes caller input, stack/root Json, allocator rounding/metadata,
direct malloc/CRT internals and profiler bookkeeping. It is not RSS. Copied MiB are logical live-token relocations, not retained heap.

All five files pass every token/value/diagnostic comparison against both fixed parsers in both toolchains.
Canonical value/shape fingerprints also match across compilers. Journal token count, final capacity and moved bytes match independent allocation profiles.

## Unchanged empirical gates

Per compiler, gates apply when its Balanced median parse is >=1 ms; every smaller file remains in all tables.

- Speed: time/better fixed mode <=1.5, peak/better fixed mode <=2, peak/Balanced <=1.5.
- Memory: time/Balanced <=2 and peak/better fixed mode <=1.5.

The offline oracle is the better fixed mode per document and metric. These local criteria are not runtime guarantees.

| Compiler / goal | GM time/Balanced, all | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| msvc/speed | 1.110 | 1.244 | 1.244 | 1.582 | 1.582 | FAIL |
| msvc/memory | 1.339 | 1.476 | 1.476 | 1.357 | 1.357 | PASS |
| clang/speed | 1.119 | 1.269 | 1.269 | 1.582 | 1.582 | FAIL |
| clang/memory | 1.383 | 1.509 | 1.509 | 1.357 | 1.357 | PASS |

- msvc/speed, worst time/oracle: natural-earth-countries.json, 1.244.
- msvc/speed, worst time/Balanced: natural-earth-countries.json, 1.244.
- msvc/speed, worst peak/oracle: canada.json, 1.582.
- msvc/speed, worst peak/Balanced: canada.json, 1.582.
- msvc/memory, worst time/oracle: natural-earth-countries.json, 1.476.
- msvc/memory, worst time/Balanced: natural-earth-countries.json, 1.476.
- msvc/memory, worst peak/oracle: canada.json, 1.357.
- msvc/memory, worst peak/Balanced: canada.json, 1.357.
- clang/speed, worst time/oracle: canada.json, 1.269.
- clang/speed, worst time/Balanced: canada.json, 1.269.
- clang/speed, worst peak/oracle: canada.json, 1.582.
- clang/speed, worst peak/Balanced: canada.json, 1.582.
- clang/memory, worst time/oracle: natural-earth-countries.json, 1.509.
- clang/memory, worst time/Balanced: natural-earth-countries.json, 1.509.
- clang/memory, worst peak/oracle: canada.json, 1.357.
- clang/memory, worst peak/Balanced: canada.json, 1.357.

A failed external gate remains a failure. No presets, coefficients, inputs or acceptance rules were adjusted in response.
Passing these five snapshots would still not establish reliable automatic selection for arbitrary applications; Auto remains private.

## Full per-input results

| Compiler / input / preset | Parse ms | Lexer ms | Whole-parse peak MiB | Copied MiB | Token count | Final token capacity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| msvc / canada.json / balanced | 29.2712 | 7.6426 | 24.876 | 0.762 | 334374 | 336676 |
| msvc / canada.json / v3-speed | 36.0218 | 13.9064 | 39.360 | 26.154 | 334374 | 508758 |
| msvc / canada.json / low-memory | 34.7401 | 13.2503 | 29.461 | 23.988 | 334374 | 334534 |
| msvc / canada.json / v3-memory | 38.9418 | 16.6748 | 33.746 | 40.072 | 334374 | 414180 |
| clang / canada.json / balanced | 24.8210 | 6.5700 | 24.876 | 0.762 | 334374 | 336676 |
| clang / canada.json / v3-speed | 31.5030 | 12.8186 | 39.360 | 26.154 | 334374 | 508758 |
| clang / canada.json / low-memory | 30.7106 | 12.1844 | 29.461 | 23.988 | 334374 | 334534 |
| clang / canada.json / v3-memory | 34.4737 | 16.0364 | 33.746 | 40.072 | 334374 | 414180 |
| msvc / citm_catalog.json / balanced | 9.9836 | 3.9018 | 12.861 | 0.762 | 135991 | 150248 |
| msvc / citm_catalog.json / v3-speed | 11.1861 | 4.5990 | 12.652 | 4.274 | 135991 | 145673 |
| msvc / citm_catalog.json / low-memory | 12.7443 | 6.5076 | 14.397 | 11.988 | 135991 | 147456 |
| msvc / citm_catalog.json / v3-memory | 14.3836 | 7.9215 | 15.692 | 19.006 | 135991 | 184080 |
| clang / citm_catalog.json / balanced | 8.9002 | 2.8361 | 12.861 | 0.762 | 135991 | 150248 |
| clang / citm_catalog.json / v3-speed | 9.3577 | 3.5102 | 12.652 | 4.274 | 135991 | 145673 |
| clang / citm_catalog.json / low-memory | 11.3867 | 5.2814 | 14.397 | 11.988 | 135991 | 147456 |
| clang / citm_catalog.json / v3-memory | 12.9339 | 7.0613 | 15.692 | 19.006 | 135991 | 184080 |
| msvc / twitter.json / balanced | 4.9007 | 1.9331 | 4.952 | 0.762 | 55264 | 55472 |
| msvc / twitter.json / v3-speed | 4.6208 | 1.7560 | 5.197 | 0.317 | 55264 | 60815 |
| msvc / twitter.json / low-memory | 5.9482 | 2.8523 | 5.962 | 5.511 | 55264 | 61988 |
| msvc / twitter.json / v3-memory | 5.9158 | 2.7992 | 5.973 | 5.400 | 55264 | 62830 |
| clang / twitter.json / balanced | 4.6277 | 1.4567 | 4.952 | 0.762 | 55264 | 55472 |
| clang / twitter.json / v3-speed | 4.2454 | 1.4545 | 5.197 | 0.317 | 55264 | 60815 |
| clang / twitter.json / low-memory | 5.5713 | 2.5039 | 5.962 | 5.511 | 55264 | 61988 |
| clang / twitter.json / v3-memory | 5.7888 | 2.5409 | 5.973 | 5.400 | 55264 | 62830 |
| msvc / natural-earth-countries.json / balanced | 13.2274 | 3.7292 | 14.849 | 0.762 | 189786 | 205567 |
| msvc / natural-earth-countries.json / v3-speed | 16.4551 | 6.4204 | 20.091 | 12.230 | 189786 | 247610 |
| msvc / natural-earth-countries.json / low-memory | 15.5172 | 5.7438 | 15.557 | 11.988 | 189786 | 191298 |
| msvc / natural-earth-countries.json / v3-memory | 19.5284 | 10.1186 | 18.903 | 27.432 | 189786 | 211390 |
| clang / natural-earth-countries.json / balanced | 12.5526 | 3.1948 | 14.849 | 0.762 | 189786 | 205567 |
| clang / natural-earth-countries.json / v3-speed | 15.3506 | 6.0672 | 20.091 | 12.230 | 189786 | 247610 |
| clang / natural-earth-countries.json / low-memory | 14.4687 | 5.2889 | 15.557 | 11.988 | 189786 | 191298 |
| clang / natural-earth-countries.json / v3-memory | 18.9360 | 10.3293 | 18.903 | 27.432 | 189786 | 211390 |
| msvc / typescript-package-lock.json / balanced | 0.8026 | 0.2722 | 1.208 | 0.012 | 12022 | 13708 |
| msvc / typescript-package-lock.json / v3-speed | 0.8373 | 0.2946 | 1.159 | 0.317 | 12022 | 12622 |
| msvc / typescript-package-lock.json / low-memory | 0.8900 | 0.3156 | 1.311 | 1.284 | 12022 | 13414 |
| msvc / typescript-package-lock.json / v3-memory | 1.0104 | 0.3727 | 1.298 | 1.215 | 12022 | 13153 |
| clang / typescript-package-lock.json / balanced | 0.7538 | 0.2004 | 1.208 | 0.012 | 12022 | 13708 |
| clang / typescript-package-lock.json / v3-speed | 0.8838 | 0.2259 | 1.159 | 0.317 | 12022 | 12622 |
| clang / typescript-package-lock.json / low-memory | 0.8449 | 0.2520 | 1.311 | 1.284 | 12022 | 13414 |
| clang / typescript-package-lock.json / v3-memory | 1.0001 | 0.2877 | 1.298 | 1.215 | 12022 | 13153 |

## Compiler transfer

Clang/MSVC parse-time ratio below 1 means faster Clang for the same preset/input on this run.
Use these paired local results rather than interpreting the compiler as a universally faster choice.

| Input | Balanced | V3 speed | LowMemory | V3 memory |
| --- | ---: | ---: | ---: | ---: |
| canada.json | 0.848 | 0.875 | 0.884 | 0.885 |
| citm_catalog.json | 0.891 | 0.837 | 0.893 | 0.899 |
| twitter.json | 0.944 | 0.919 | 0.937 | 0.979 |
| natural-earth-countries.json | 0.949 | 0.933 | 0.932 | 0.970 |
| typescript-package-lock.json | 0.939 | 1.055 | 0.949 | 0.990 |
| Geometric mean | 0.914 | 0.921 | 0.919 | 0.944 |

## Reproduction and limits

Raw [freeze, upstream manifest, eight timing rounds, profiles, journals and source snapshots](real-corpus-windows/) accompany the report.
Use [the real-corpus instructions](../real-corpus/README.md). Regenerate with `python benchmarks/real-corpus/summarize.py benchmarks/results/real-corpus-windows REPORT.md`.
No noisy performance threshold runs in CI. Windows/Linux CI repeats exact results and journal/profile invariants on the original external files.
CPU frequency, thermal state, code layout and background load can still affect measurements. This is one machine and a small convenience sample,
with no pretense that the historical external corpus covers users actual file distributions. Representative opt-in workload data remains the next evidence needed.
