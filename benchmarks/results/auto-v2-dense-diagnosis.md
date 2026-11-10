# Auto v2: dense-input diagnosis

## Scope and method

This is a follow-up on eight already known synthetic inputs, not an independent evaluation or a retuned Auto policy.
Production code and the frozen v1/v2 controllers are unchanged. Six cyclic rounds compare the original frozen executables.
Measured on 12th Gen Intel(R) Core(TM) i5-12600KF, Windows-10-10.0.19045-SP0; MSVC 19.51 Release, /O2 /Ob2 /DNDEBUG; original frozen parsers and standalone replay; pinned to logical CPU 0.
Each sample contains 3 operations; 5 samples per round, plus 5 warm-ups. Reported times are medians of six round medians.
Parser/lexer time includes allocation and destruction; allocation profiles and journals are separate untimed runs.

The isolated replay appends the same number of 48-byte Token objects to std::vector and follows the exact v2 allocation schedule.
It performs no JSON scan, source copy, density prediction, token conversion or DOM construction. Every observed growth and copied-token count must match the journal/profile.
The exact-known-count control reserves all tokens once before appending; knowing this count for free is an offline experiment, not an implementable Auto mode.
Replay still includes token synthesis, vector checks, allocation and destruction. Timing differences between separate executables cannot be subtracted to assign exact parser percentages.

## Repeated full parse and lexer measurements

| Known input / mode | Parse ms | Lexer ms | Parse/Balanced | Lexer/Balanced | Parse/prior run |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense-zeros-4096.json / balanced | 0.188 | 0.060 | 1.000 | 1.000 | 1.054 |
| dense-zeros-4096.json / v1-speed | 0.348 | 0.228 | 1.851 | 3.810 | 1.393 |
| dense-zeros-4096.json / v2-speed | 0.348 | 0.226 | 1.853 | 3.776 | 1.473 |
| dense-zeros-4096.json / low-memory | 0.536 | 0.455 | 2.855 | 7.588 | 1.086 |
| dense-zeros-4096.json / v1-memory | 0.480 | 0.415 | 2.555 | 6.919 | 1.374 |
| dense-zeros-4096.json / v2-memory | 0.543 | 0.464 | 2.890 | 7.744 | 1.860 |
| dense-zeros-32768.json / balanced | 2.011 | 1.037 | 1.000 | 1.000 | 0.939 |
| dense-zeros-32768.json / v1-speed | 2.171 | 1.231 | 1.079 | 1.187 | 1.094 |
| dense-zeros-32768.json / v2-speed | 2.115 | 1.149 | 1.052 | 1.109 | 1.053 |
| dense-zeros-32768.json / low-memory | 3.400 | 2.454 | 1.691 | 2.367 | 0.965 |
| dense-zeros-32768.json / v1-memory | 3.657 | 2.554 | 1.818 | 2.464 | 1.095 |
| dense-zeros-32768.json / v2-memory | 3.561 | 2.532 | 1.771 | 2.442 | 1.093 |
| dense-zeros-262144.json / balanced | 19.411 | 9.898 | 1.000 | 1.000 | 1.146 |
| dense-zeros-262144.json / v1-speed | 19.759 | 10.224 | 1.018 | 1.033 | 1.041 |
| dense-zeros-262144.json / v2-speed | 31.999 | 21.977 | 1.648 | 2.220 | 1.097 |
| dense-zeros-262144.json / low-memory | 31.288 | 23.744 | 1.612 | 2.399 | 1.064 |
| dense-zeros-262144.json / v1-memory | 25.274 | 15.649 | 1.302 | 1.581 | 1.104 |
| dense-zeros-262144.json / v2-memory | 46.271 | 34.468 | 2.384 | 3.482 | 1.129 |
| alternating-4096.json / balanced | 0.340 | 0.098 | 1.000 | 1.000 | 0.903 |
| alternating-4096.json / v1-speed | 0.471 | 0.346 | 1.385 | 3.511 | 0.931 |
| alternating-4096.json / v2-speed | 0.523 | 0.334 | 1.540 | 3.392 | 1.019 |
| alternating-4096.json / low-memory | 0.670 | 0.578 | 1.971 | 5.871 | 0.944 |
| alternating-4096.json / v1-memory | 0.608 | 0.500 | 1.788 | 5.084 | 0.875 |
| alternating-4096.json / v2-memory | 0.598 | 0.486 | 1.758 | 4.942 | 0.875 |
| alternating-32768.json / balanced | 3.094 | 1.717 | 1.000 | 1.000 | 1.210 |
| alternating-32768.json / v1-speed | 3.010 | 1.859 | 0.973 | 1.083 | 0.982 |
| alternating-32768.json / v2-speed | 2.975 | 1.898 | 0.962 | 1.106 | 0.999 |
| alternating-32768.json / low-memory | 4.408 | 2.926 | 1.425 | 1.705 | 1.081 |
| alternating-32768.json / v1-memory | 4.324 | 2.976 | 1.398 | 1.733 | 1.042 |
| alternating-32768.json / v2-memory | 4.144 | 3.135 | 1.340 | 1.826 | 1.066 |
| alternating-262144.json / balanced | 25.730 | 13.080 | 1.000 | 1.000 | 1.134 |
| alternating-262144.json / v1-speed | 27.483 | 13.973 | 1.068 | 1.068 | 1.178 |
| alternating-262144.json / v2-speed | 35.352 | 25.914 | 1.374 | 1.981 | 1.053 |
| alternating-262144.json / low-memory | 36.373 | 25.610 | 1.414 | 1.958 | 1.009 |
| alternating-262144.json / v1-memory | 33.808 | 19.439 | 1.314 | 1.486 | 1.240 |
| alternating-262144.json / v2-memory | 46.892 | 35.939 | 1.822 | 2.748 | 1.122 |
| held-tail-records-4099.json / balanced | 10.624 | 6.450 | 1.000 | 1.000 | 1.156 |
| held-tail-records-4099.json / v1-speed | 10.623 | 6.995 | 1.000 | 1.084 | 1.079 |
| held-tail-records-4099.json / v2-speed | 11.161 | 7.181 | 1.051 | 1.113 | 1.135 |
| held-tail-records-4099.json / low-memory | 11.506 | 7.619 | 1.083 | 1.181 | 1.142 |
| held-tail-records-4099.json / v1-memory | 11.622 | 7.705 | 1.094 | 1.195 | 1.141 |
| held-tail-records-4099.json / v2-memory | 11.844 | 8.771 | 1.115 | 1.360 | 1.128 |
| whitespace-interleaved-16384.json / balanced | 3.322 | 3.093 | 1.000 | 1.000 | 1.019 |
| whitespace-interleaved-16384.json / v1-speed | 4.475 | 3.831 | 1.347 | 1.238 | 1.050 |
| whitespace-interleaved-16384.json / v2-speed | 4.335 | 3.875 | 1.305 | 1.253 | 1.038 |
| whitespace-interleaved-16384.json / low-memory | 4.231 | 3.943 | 1.274 | 1.275 | 1.152 |
| whitespace-interleaved-16384.json / v1-memory | 5.231 | 5.032 | 1.575 | 1.627 | 1.037 |
| whitespace-interleaved-16384.json / v2-memory | 5.982 | 5.287 | 1.801 | 1.709 | 1.270 |

## Buffer accounting

MiB are requested bytes, not RSS. Copied bytes are cumulative logical live-token relocation, not retained heap.

| Input / mode | Tokens | Expansions | Copied MiB | Final token-buffer MiB | Lexer peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense-zeros-4096.json / balanced | 8194 | 1 | 0.012 | 0.375 | 0.395 |
| dense-zeros-4096.json / low-memory | 8194 | 6 | 0.738 | 0.422 | 0.805 |
| dense-zeros-4096.json / v2-speed | 8194 | 3 | 0.317 | 0.375 | 0.630 |
| dense-zeros-4096.json / v2-memory | 8194 | 5 | 0.670 | 0.375 | 0.748 |
| dense-zeros-32768.json / balanced | 65538 | 2 | 0.762 | 3.000 | 3.813 |
| dense-zeros-32768.json / low-memory | 65538 | 9 | 5.988 | 3.375 | 6.438 |
| dense-zeros-32768.json / v2-speed | 65538 | 3 | 0.317 | 3.000 | 3.309 |
| dense-zeros-32768.json / v2-memory | 65538 | 8 | 5.400 | 3.000 | 5.557 |
| dense-zeros-262144.json / balanced | 524290 | 2 | 0.762 | 24.000 | 25.250 |
| dense-zeros-262144.json / low-memory | 524290 | 12 | 47.988 | 27.000 | 51.500 |
| dense-zeros-262144.json / v2-speed | 524290 | 7 | 42.122 | 24.000 | 42.435 |
| dense-zeros-262144.json / v2-memory | 524290 | 16 | 82.808 | 24.000 | 45.073 |
| alternating-4096.json / balanced | 8202 | 1 | 0.012 | 0.750 | 0.801 |
| alternating-4096.json / low-memory | 8202 | 6 | 0.738 | 0.469 | 0.883 |
| alternating-4096.json / v2-speed | 8202 | 3 | 0.317 | 0.449 | 0.735 |
| alternating-4096.json / v2-memory | 8202 | 5 | 0.670 | 0.456 | 0.860 |
| alternating-32768.json / balanced | 65602 | 2 | 0.762 | 3.334 | 4.397 |
| alternating-32768.json / low-memory | 65602 | 9 | 5.988 | 3.375 | 6.688 |
| alternating-32768.json / v2-speed | 65602 | 4 | 1.315 | 3.351 | 4.662 |
| alternating-32768.json / v2-memory | 65602 | 8 | 5.400 | 3.118 | 5.924 |
| alternating-262144.json / balanced | 524802 | 2 | 0.762 | 26.673 | 29.924 |
| alternating-262144.json / low-memory | 524802 | 12 | 47.988 | 27.000 | 53.501 |
| alternating-262144.json / v2-speed | 524802 | 8 | 43.337 | 27.013 | 47.523 |
| alternating-262144.json / v2-memory | 524802 | 16 | 82.808 | 30.859 | 53.932 |
| held-tail-records-4099.json / balanced | 90180 | 2 | 0.762 | 48.000 | 51.969 |
| held-tail-records-4099.json / low-memory | 90180 | 9 | 5.988 | 6.000 | 12.219 |
| held-tail-records-4099.json / v2-speed | 90180 | 4 | 4.274 | 7.957 | 15.132 |
| held-tail-records-4099.json / v2-memory | 90180 | 9 | 8.894 | 4.494 | 11.207 |
| whitespace-interleaved-16384.json / balanced | 32770 | 2 | 0.762 | 1.500 | 4.328 |
| whitespace-interleaved-16384.json / low-memory | 32770 | 8 | 2.988 | 1.688 | 5.266 |
| whitespace-interleaved-16384.json / v2-speed | 32770 | 3 | 0.317 | 1.595 | 3.919 |
| whitespace-interleaved-16384.json / v2-memory | 32770 | 7 | 2.906 | 1.868 | 5.440 |

## Isolated schedule replay

| Input | Exact-known-count ms | V2 speed schedule ms | Speed/exact | V2 memory schedule ms | Memory/exact |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense-zeros-4096.json | 0.044 | 0.209 | 4.722 | 0.325 | 7.340 |
| dense-zeros-32768.json | 0.873 | 0.912 | 1.045 | 2.299 | 2.633 |
| dense-zeros-262144.json | 8.965 | 20.422 | 2.278 | 32.496 | 3.625 |
| alternating-4096.json | 0.044 | 0.213 | 4.789 | 0.342 | 7.681 |
| alternating-32768.json | 0.883 | 1.164 | 1.318 | 2.582 | 2.923 |
| alternating-262144.json | 8.552 | 20.896 | 2.443 | 34.898 | 4.080 |
| held-tail-records-4099.json | 1.113 | 2.027 | 1.821 | 3.541 | 3.182 |
| whitespace-interleaved-16384.json | 0.428 | 0.447 | 1.045 | 1.401 | 3.277 |

## Interpretation and next experiment

Read full-parse and lexer ratios together with replay: costly recorded schedules can be slow even when density calculations and JSON parsing are absent.
The byte ceiling trades a large speculative allocation for repeated copies. In dense inputs, final capacity can be exact while old/new overlap and cumulative copying remain expensive.
A remaining-byte final reservation avoids only the last unnecessary expansion; it cannot recover copies already made earlier.
Changing thresholds based on these known inputs would be calibration. The previous holdout is also known now; a future candidate needs a fresh evaluation set.

The next targeted experiment should vary the growth floor after copy pressure, while retaining the byte ceiling and the sparse-suffix regressions.
Evaluate time, simultaneous peak and relocation together. A larger floor can reduce copies and increase both overlap and final slack, so no promotion follows from replay alone.
Keep Balanced/LowMemory as the public choices. Representative user workloads remain necessary; this synthetic diagnosis does not establish production frequency.

Raw CSVs, replay schedules, source/input/binary hashes and frozen-reference hashes are in [the result directory](auto-v2-diagnosis-msvc1951/).
Reproduce with [the diagnosis instructions](../auto-v2/diagnosis/README.md).
