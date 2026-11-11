# Bounded tail count experiment

Auto v3 speed sometimes increases its geometric floor at the final growth.
The Canada profile measures 39.360 MiB at that expansion. The prototype
checks whether the ordinary 1.5× allocation can accommodate the entire
suffix, including EOF. [Canada diagnosis](../results/canada-growth.md)

The probe runs at a v3 remaining-byte reservation with a raised floor and a
suffix of at most 256 KiB. It walks the production token loop and stops when
the ordinary allocation's token quota is exhausted. It restores the cursor,
line, column and token coordinates on every exit. A confirmed fit lets the
ordinary allocation cover the suffix. A token-limit stop or lexer error keeps
v3's byte-bound request, which already covers the suffix. Both paths therefore
allow one probe per tokenization.

## Build and verify

Use a static Release build with both experiments enabled and these CMake
settings.

    -DMASKETJSON_BUILD_BENCHMARKS=ON
    -DMASKETJSON_BUILD_PROFILER=ON
    -DMASKETJSON_BUILD_AUTO_V3_EXPERIMENT=ON
    -DMASKETJSON_BUILD_TAIL_EXPERIMENT=ON
    -DAUTO_V3_SPEED_QUARTERS=7
    -DAUTO_V3_SPEED_LOOKAHEAD=1
    -DAUTO_V3_SPEED_BUDGET=4194304

Build the AutoTailTools target in separate MSVC and Clang-cl directories.
The external corpus instructions give the Windows compiler configuration.
[Compiler setup](../real-corpus/README.md)

Run the targeted correctness check with the original Canada snapshot. CI
runs this check on Windows and Linux and under ASan/UBSan. Profiling is enabled
for the measurement build and omitted for the sanitizer build.

    python benchmarks/auto-tail/check.py --build out/auto-tail-msvc --output out/auto-tail-check --canada out/real-corpus-inputs/canada.json

The script checks a fit, a token-limit stop and malformed numeric and UTF-8
suffixes. It compares tokens, values and diagnostic positions with both
production presets and verifies the observed probe decisions.

## Measure

The runner uses Canada from the pinned external corpus, three previously
generated synthetic fixtures and two focused valid fixtures. These commands
retrieve or regenerate the known inputs for a fresh checkout.

    python benchmarks/real-corpus/fetch.py out/real-corpus-inputs
    python benchmarks/reservation/generate_inputs.py out/auto-tail-known-shapes
    python benchmarks/reservation/generate_holdout.py out/auto-tail-known-holdout

The run command records build and binary identities before it creates fresh
geometries and fetches the two pinned Natural Earth files. Use a fresh output
directory. The runner includes the probe's work in ordinary parse and lexer
timings and records heap profiles separately. [Measurement plan](plan.json)

    python benchmarks/auto-tail/run.py --msvc out/auto-tail-msvc --clang out/auto-tail-clang --known out/real-corpus-inputs out/auto-tail-known-shapes out/auto-tail-known-holdout --output out/auto-tail-final
    python benchmarks/auto-tail/summarize.py out/auto-tail-final out/auto-tail-report.md

The committed report includes the full parse time, peak and probe decision
for each input. [Experiment report](../results/auto-tail.md)
