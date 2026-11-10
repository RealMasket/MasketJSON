# Auto v3: growth under copy pressure

## Hypothesis and fixed experiment

The dense-input diagnosis found expensive allocation schedules without JSON scanning or density prediction.
Phase 1 changes only the geometric floor when the existing copy-pressure predicate is active. Density thresholds, pressure thresholds,
4 MiB speed / 1 MiB memory speculative-byte budgets and remaining-byte final-capacity proof are unchanged.
Candidates use floor(capacity * 1.5), floor(capacity * 1.75) or capacity * 2 under pressure; checked arithmetic saturates at max_size.
Without pressure, the ordinary speed 1.5 / memory 1.25 minimum remains. Larger floors can exceed the soft byte ceiling, and every exception is logged.
A proved final-capacity reservation may bypass the geometric floor because all remaining tokens fit, requiring no subsequent expansion.

The [original plan](../auto-v3/plan.json), controllers and tooling were committed before measurements at `f4b9f04`.
Phase 1 showed zero speed pressure activations on dense-zeros-262144: increasing a pressure floor cannot change that schedule.
A [second pre-recorded plan](../auto-v3/selection-plan.json), committed at `f6604dc` before further measurement, adds projected pressure.
Projected pressure includes the inevitable relocation at the pending expansion. Integer comparisons cancel that n-token term:
speed uses moved > floor(n/2), memory moved > 2*n; no overflowing sum is formed. The historical predicate remains a control.
Both predicates are crossed with all three floors. Selection uses all six known-data candidates under the original joint gates.
All 91 previous synthetic inputs, including previous evaluation splits, are calibration data now. No old holdout is reused as an independent test.
The 1.5 control reproduces all 91 v2 heap/profile rows exactly for both goals and both production modes.
One exploratory round of 3 samples x 2 operations selects each goal using all joint CPU/heap gates first, geometric mean time second,
and lowest worst peak/oracle for candidates within 3% of the fastest. If no candidate passes, minimum normalized gate violation is explicitly unqualified.

| Candidate / goal | Pressure floor | Lookahead | GM time/Balanced | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| control/speed | 1.5 | 0 | 1.028 | 1.653 | 1.653 | 1.427 | 1.390 | False |
| control/memory | 1.5 | 0 | 1.116 | 2.076 | 2.076 | 1.357 | 1.357 | False |
| seven-fourths/speed | 1.75 | 0 | 1.054 | 1.749 | 1.749 | 1.427 | 1.390 | False |
| seven-fourths/memory | 1.75 | 0 | 1.199 | 2.568 | 2.568 | 1.382 | 1.382 | False |
| double/speed | 2 | 0 | 1.027 | 1.621 | 1.621 | 1.427 | 1.390 | False |
| double/memory | 2 | 0 | 1.127 | 1.896 | 1.896 | 1.382 | 1.382 | True |
| projected-control/speed | 1.5 | 1 | 1.028 | 1.529 | 1.529 | 1.427 | 1.390 | False |
| projected-control/memory | 1.5 | 1 | 1.091 | 1.905 | 1.905 | 1.350 | 1.350 | True |
| projected-seven-fourths/speed | 1.75 | 1 | 1.023 | 1.470 | 1.470 | 1.427 | 1.390 | True |
| projected-seven-fourths/memory | 1.75 | 1 | 1.133 | 1.881 | 1.881 | 1.350 | 1.350 | True |
| projected-double/speed | 2 | 1 | 1.018 | 1.451 | 1.451 | 1.427 | 1.390 | True |
| projected-double/memory | 2 | 1 | 1.135 | 2.270 | 2.270 | 1.350 | 1.350 | False |

Selected speed pressure floor: 1.75; memory: 1.5. Lookahead speed/memory: 1/1.
Policy sources, all comparison executables and the selected parameters were frozen at `2026-11-10T16:05:51.411550+00:00` after repeated known-set measurements.
Only then were 16 full new inputs generated with seed 20261110 and counts 197/4093: buried trailing padding, escaped/UTF-8 values,
late records, mixed-width floats, ragged objects, whitespace islands, leading padding and irregular stepped string/number regions.
No thresholds, budgets or coefficients were changed using that new evaluation.

## Measurement and unchanged gates

Machine: 12th Gen Intel(R) Core(TM) i5-12600KF; Windows-10-10.0.19045-SP0; MSVC 19.51 Release, static, /O2 /Ob2 /DNDEBUG; binary identities are frozen calibration artifacts.
Logical CPU 0; six cyclic rounds with every mode in every position once. Each round uses 5 samples x 3 operations and 5 warm-ups.
Tables show medians of round medians. Loading and exact checks are outside timing; result construction/destruction is included.
Timing uses ordinary builds without journals or allocation interception. Profile/trace builds run separately.
Captured heap peak counts simultaneous requested bytes from intercepted C++ new calls, including overlapping token buffers.
Caller input, stack/root Json, allocator rounding/metadata, direct malloc/CRT allocations and profiler bookkeeping are excluded; this is not RSS.
Copied bytes are logical live-token relocations, not retained memory. Recorded retained DOM accounting is identical across all six modes.

Pre-registered gates apply on Balanced parse >=1 ms; every smaller input is still reported:

- Speed: time/better fixed mode <=1.5, peak/better fixed mode <=2, peak/Balanced <=1.5.
- Memory: time/Balanced <=2, peak/better fixed mode <=1.5.
The better fixed mode (offline oracle) is chosen per document and metric. These are local empirical criteria, not runtime guarantees.

| Split / mode | GM time/Balanced, all | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| known/v2-speed | 1.072 | 1.700 | 1.700 | 1.427 | 1.390 | FAIL |
| known/v3-speed | 1.056 | 1.460 | 1.460 | 1.427 | 1.390 | PASS |
| known/v2-memory | 1.144 | 2.362 | 2.362 | 1.357 | 1.357 | FAIL |
| known/v3-memory | 1.136 | 1.911 | 1.911 | 1.350 | 1.350 | PASS |
| holdout/v2-speed | 1.076 | 1.314 | 1.314 | 1.261 | 1.048 | PASS |
| holdout/v3-speed | 1.051 | 1.294 | 1.294 | 1.261 | 1.048 | PASS |
| holdout/v2-memory | 1.255 | 1.642 | 1.642 | 1.382 | 1.382 | PASS |
| holdout/v3-memory | 1.233 | 1.494 | 1.494 | 1.382 | 1.382 | PASS |

Worst-case input names:

- known/v3-speed, worst time/oracle: wide-objects-16384.json, 1.460.
- known/v3-speed, worst time/Balanced: wide-objects-16384.json, 1.460.
- known/v3-speed, worst peak/oracle: auto-held-late-padding-2053.json, 1.427.
- known/v3-speed, worst peak/Balanced: v2-held-internal-gap-3079.json, 1.390.
- known/v3-memory, worst time/oracle: dense-zeros-262144.json, 1.911.
- known/v3-memory, worst time/Balanced: dense-zeros-262144.json, 1.911.
- known/v3-memory, worst peak/oracle: v2-held-duplicate-keys-3079.json, 1.350.
- known/v3-memory, worst peak/Balanced: v2-held-duplicate-keys-3079.json, 1.350.
- holdout/v3-speed, worst time/oracle: v3-held-late-records-4093.json, 1.294.
- holdout/v3-speed, worst time/Balanced: v3-held-late-records-4093.json, 1.294.
- holdout/v3-speed, worst peak/oracle: v3-held-buried-tail-4093.json, 1.261.
- holdout/v3-speed, worst peak/Balanced: v3-held-ragged-object-4093.json, 1.048.
- holdout/v3-memory, worst time/oracle: v3-held-float-values-4093.json, 1.494.
- holdout/v3-memory, worst time/Balanced: v3-held-float-values-4093.json, 1.494.
- holdout/v3-memory, worst peak/oracle: v3-held-float-values-4093.json, 1.382.
- holdout/v3-memory, worst peak/Balanced: v3-held-float-values-4093.json, 1.382.

These results preserve the original thresholds, including failed rows. Passing both splits is evidence for these inputs and this machine,
not proof of general automatic selection. V3 remains a private experiment; public Balanced/LowMemory and Json layout are unchanged.

## Dense and sparse-tail regressions

| Known input / mode | Parse ms | Lexer ms | Copied MiB | Whole-parse peak MiB | Final token buffer MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense-zeros-262144.json / balanced | 16.459 | 8.874 | 0.762 | 34.500 | 24.000 |
| dense-zeros-262144.json / low-memory | 28.289 | 21.210 | 47.988 | 51.500 | 27.000 |
| dense-zeros-262144.json / v2-speed | 27.982 | 18.994 | 42.122 | 42.435 | 24.000 |
| dense-zeros-262144.json / v3-speed | 23.429 | 14.944 | 26.154 | 38.424 | 24.000 |
| dense-zeros-262144.json / v2-memory | 38.880 | 29.633 | 82.808 | 45.073 | 24.000 |
| dense-zeros-262144.json / v3-memory | 31.456 | 23.284 | 59.031 | 43.460 | 24.000 |
| alternating-262144.json / balanced | 22.427 | 11.485 | 0.762 | 41.197 | 26.673 |
| alternating-262144.json / low-memory | 33.472 | 24.529 | 47.988 | 53.501 | 27.000 |
| alternating-262144.json / v2-speed | 33.477 | 22.669 | 43.337 | 47.523 | 27.013 |
| alternating-262144.json / v3-speed | 28.331 | 18.912 | 27.330 | 41.020 | 24.512 |
| alternating-262144.json / v2-memory | 43.395 | 32.568 | 82.808 | 53.932 | 30.859 |
| alternating-262144.json / v3-memory | 37.591 | 27.146 | 59.031 | 49.900 | 28.439 |
| held-tail-records-4099.json / balanced | 9.088 | 5.975 | 0.762 | 54.116 | 48.000 |
| held-tail-records-4099.json / low-memory | 9.971 | 6.940 | 5.988 | 12.219 | 6.000 |
| held-tail-records-4099.json / v2-speed | 10.024 | 7.543 | 4.274 | 15.132 | 7.957 |
| held-tail-records-4099.json / v3-speed | 10.143 | 6.766 | 4.274 | 15.132 | 7.957 |
| held-tail-records-4099.json / v2-memory | 10.503 | 7.908 | 8.894 | 11.207 | 4.494 |
| held-tail-records-4099.json / v3-memory | 10.649 | 7.685 | 8.894 | 11.207 | 4.494 |
| dense-zeros-32768.json / balanced | 1.930 | 1.047 | 0.762 | 4.313 | 3.000 |
| dense-zeros-32768.json / low-memory | 3.211 | 2.250 | 5.988 | 6.438 | 3.375 |
| dense-zeros-32768.json / v2-speed | 1.921 | 0.996 | 0.317 | 4.313 | 3.000 |
| dense-zeros-32768.json / v3-speed | 1.895 | 0.981 | 0.317 | 4.313 | 3.000 |
| dense-zeros-32768.json / v2-memory | 3.030 | 2.126 | 5.400 | 5.557 | 3.000 |
| dense-zeros-32768.json / v3-memory | 3.123 | 2.082 | 5.400 | 5.557 | 3.000 |

## Full parse time, ms

| Split / input | Balanced | LowMemory | V2 speed | V3 speed | V2 memory | V3 memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| known / alternating-262144.json | 22.4267 | 33.4718 | 33.4772 | 28.3309 | 43.3946 | 37.5914 |
| known / alternating-32768.json | 2.7889 | 3.9403 | 2.8044 | 2.8467 | 3.9887 | 3.8848 |
| known / alternating-4096.json | 0.3624 | 0.6647 | 0.4470 | 0.4681 | 0.6263 | 0.6460 |
| known / auto-held-bursts-2053.json | 4.5300 | 5.5654 | 4.6640 | 4.9756 | 5.2808 | 5.3733 |
| known / auto-held-bursts-73.json | 0.1693 | 0.1777 | 0.1772 | 0.1790 | 0.1765 | 0.1852 |
| known / auto-held-inner-padding-2053.json | 3.2959 | 6.1868 | 3.4222 | 3.4078 | 5.0480 | 5.0887 |
| known / auto-held-inner-padding-73.json | 0.1446 | 0.1989 | 0.1885 | 0.1864 | 0.1694 | 0.1695 |
| known / auto-held-late-padding-2053.json | 5.7296 | 6.0296 | 5.7052 | 5.8104 | 6.0164 | 5.9815 |
| known / auto-held-late-padding-73.json | 0.2277 | 0.2235 | 0.2114 | 0.2127 | 0.2221 | 0.2245 |
| known / auto-held-long-keys-2053.json | 2.2306 | 2.2769 | 2.1656 | 2.1710 | 2.2456 | 2.2039 |
| known / auto-held-long-keys-73.json | 0.0539 | 0.0555 | 0.0545 | 0.0540 | 0.0540 | 0.0533 |
| known / auto-held-phases-2053.json | 22.0327 | 25.5163 | 22.8695 | 22.7176 | 24.0728 | 23.7455 |
| known / auto-held-phases-73.json | 0.8629 | 0.9290 | 0.9192 | 0.9123 | 0.9240 | 0.9090 |
| known / auto-held-ragged-numbers-2053.json | 1.7692 | 2.1661 | 1.7874 | 1.7088 | 2.1884 | 2.1328 |
| known / auto-held-ragged-numbers-73.json | 0.0328 | 0.0507 | 0.0643 | 0.0616 | 0.0385 | 0.0376 |
| known / auto-held-spiky-strings-2053.json | 24.0233 | 24.2860 | 23.7853 | 22.9813 | 22.8518 | 24.1986 |
| known / auto-held-spiky-strings-73.json | 1.1251 | 1.0612 | 1.0877 | 1.0609 | 1.0872 | 1.1844 |
| known / auto-held-zigzag-2053.json | 1.6537 | 1.6176 | 1.6599 | 1.6500 | 1.6485 | 1.7351 |
| known / auto-held-zigzag-73.json | 0.1041 | 0.0925 | 0.0794 | 0.0761 | 0.0933 | 0.1081 |
| known / deep-128.json | 0.0109 | 0.0108 | 0.0111 | 0.0111 | 0.0110 | 0.0116 |
| known / deep-64.json | 0.0057 | 0.0059 | 0.0059 | 0.0058 | 0.0059 | 0.0060 |
| known / deep-8.json | 0.0007 | 0.0008 | 0.0008 | 0.0008 | 0.0008 | 0.0008 |
| known / dense-first-262144.json | 20.6937 | 34.5955 | 32.9128 | 29.4402 | 42.6427 | 36.7358 |
| known / dense-first-32768.json | 2.6734 | 4.0565 | 2.7879 | 2.5584 | 3.8159 | 3.8853 |
| known / dense-first-4096.json | 0.2016 | 0.5009 | 0.3876 | 0.3836 | 0.5772 | 0.5815 |
| known / dense-zeros-262144.json | 16.4591 | 28.2890 | 27.9820 | 23.4291 | 38.8799 | 31.4555 |
| known / dense-zeros-32768.json | 1.9299 | 3.2112 | 1.9214 | 1.8949 | 3.0296 | 3.1228 |
| known / dense-zeros-4096.json | 0.1705 | 0.4588 | 0.2659 | 0.2657 | 0.2709 | 0.2741 |
| known / escaped-4096.json | 12.8432 | 11.8502 | 12.2859 | 12.3169 | 11.9095 | 12.4497 |
| known / escaped-512.json | 1.4842 | 1.4299 | 1.2670 | 1.3266 | 1.3644 | 1.4200 |
| known / escaped-64.json | 0.1616 | 0.1456 | 0.1601 | 0.1637 | 0.1662 | 0.1626 |
| known / flat-object-16384.json | 5.2526 | 6.4947 | 5.3359 | 5.3391 | 6.3759 | 6.6069 |
| known / flat-object-2048.json | 0.4574 | 0.6910 | 0.5778 | 0.5520 | 0.5986 | 0.6084 |
| known / flat-object-256.json | 0.0493 | 0.0625 | 0.0486 | 0.0481 | 0.0495 | 0.0498 |
| known / held-empty-mix-257.json | 0.1200 | 0.1385 | 0.1603 | 0.1525 | 0.1031 | 0.1314 |
| known / held-empty-mix-4099.json | 1.7339 | 2.2926 | 1.8189 | 1.7501 | 2.1701 | 2.4451 |
| known / held-escape-transition-257.json | 0.0969 | 0.1144 | 0.1005 | 0.0981 | 0.0898 | 0.0945 |
| known / held-escape-transition-4099.json | 0.4727 | 0.5781 | 0.5188 | 0.3966 | 0.5093 | 0.4443 |
| known / held-front-nested-257.json | 0.6610 | 0.7075 | 0.7521 | 0.7863 | 0.6206 | 0.5805 |
| known / held-front-nested-4099.json | 11.3027 | 15.5593 | 11.3033 | 11.1228 | 11.9255 | 11.3326 |
| known / held-long-keys-257.json | 0.0295 | 0.0315 | 0.0295 | 0.0319 | 0.0295 | 0.0308 |
| known / held-long-keys-4099.json | 0.4944 | 0.5315 | 0.5220 | 0.5330 | 0.5250 | 0.5331 |
| known / held-sawtooth-257.json | 0.2600 | 0.2429 | 0.2449 | 0.2550 | 0.2339 | 0.2302 |
| known / held-sawtooth-4099.json | 4.3363 | 4.4856 | 4.4044 | 4.4897 | 4.2886 | 4.2269 |
| known / held-tail-records-257.json | 0.4166 | 0.4560 | 0.5700 | 0.5837 | 0.4676 | 0.5000 |
| known / held-tail-records-4099.json | 9.0880 | 9.9712 | 10.0245 | 10.1433 | 10.5031 | 10.6488 |
| known / large.json | 16.9577 | 21.0729 | 21.4619 | 19.0035 | 26.8424 | 25.8834 |
| known / long-ascii-4096.json | 9.2187 | 9.2534 | 9.6795 | 9.5715 | 9.3380 | 8.8340 |
| known / long-ascii-512.json | 1.0227 | 1.0417 | 1.0389 | 1.0288 | 1.0317 | 1.0210 |
| known / long-ascii-64.json | 0.1238 | 0.1226 | 0.1216 | 0.1213 | 0.1215 | 0.1190 |
| known / medium.json | 1.7061 | 2.1313 | 1.6486 | 1.6719 | 2.0957 | 2.2468 |
| known / nested.json | 0.0177 | 0.0187 | 0.0176 | 0.0178 | 0.0180 | 0.0180 |
| known / small.json | 0.0813 | 0.0913 | 0.0832 | 0.0825 | 0.0887 | 0.0876 |
| known / sparse-first-262144.json | 34.6719 | 62.1178 | 40.7391 | 32.5599 | 43.6519 | 35.7701 |
| known / sparse-first-32768.json | 3.5169 | 6.8927 | 3.3188 | 3.1926 | 3.9462 | 3.9025 |
| known / sparse-first-4096.json | 0.2143 | 0.2574 | 0.2079 | 0.1950 | 0.2412 | 0.2395 |
| known / tiny.json | 0.0011 | 0.0013 | 0.0011 | 0.0011 | 0.0012 | 0.0011 |
| known / unicode-4096.json | 10.8289 | 11.2084 | 11.1033 | 11.5233 | 11.2763 | 10.8502 |
| known / unicode-512.json | 1.2288 | 1.2287 | 1.2578 | 1.2535 | 1.2675 | 1.1671 |
| known / unicode-64.json | 0.1487 | 0.1501 | 0.1534 | 0.1541 | 0.1572 | 0.1424 |
| known / v2-held-chunks-149.json | 0.1702 | 0.1622 | 0.1594 | 0.1685 | 0.1583 | 0.1627 |
| known / v2-held-chunks-3079.json | 3.8663 | 3.7732 | 3.3716 | 3.3528 | 3.8622 | 3.6946 |
| known / v2-held-duplicate-keys-149.json | 0.0371 | 0.0392 | 0.0365 | 0.0368 | 0.0363 | 0.0363 |
| known / v2-held-duplicate-keys-3079.json | 1.1891 | 1.6221 | 1.1230 | 1.1275 | 1.6112 | 1.5803 |
| known / v2-held-front-cells-149.json | 0.2009 | 0.2106 | 0.1903 | 0.1920 | 0.2083 | 0.1997 |
| known / v2-held-front-cells-3079.json | 6.2976 | 9.2826 | 6.2337 | 5.9584 | 6.3027 | 6.0557 |
| known / v2-held-internal-gap-149.json | 0.1356 | 0.1448 | 0.1330 | 0.1421 | 0.1390 | 0.1373 |
| known / v2-held-internal-gap-3079.json | 3.9536 | 4.6879 | 3.5204 | 3.5056 | 4.4183 | 3.7980 |
| known / v2-held-ragged-width-149.json | 0.0362 | 0.0354 | 0.0365 | 0.0361 | 0.0357 | 0.0357 |
| known / v2-held-ragged-width-3079.json | 1.1564 | 1.1313 | 1.0473 | 1.0984 | 1.1526 | 1.1355 |
| known / v2-held-space-strings-149.json | 0.0515 | 0.0536 | 0.0502 | 0.0488 | 0.0512 | 0.0505 |
| known / v2-held-space-strings-3079.json | 1.1624 | 0.9654 | 0.9818 | 1.0008 | 0.9900 | 0.9928 |
| known / v2-held-tail-cells-149.json | 0.1895 | 0.1876 | 0.1871 | 0.1963 | 0.1932 | 0.1938 |
| known / v2-held-tail-cells-3079.json | 4.9458 | 5.3199 | 4.8928 | 5.0191 | 5.3451 | 5.6252 |
| known / v2-held-utf8-149.json | 0.0518 | 0.0527 | 0.0530 | 0.0529 | 0.0555 | 0.0505 |
| known / v2-held-utf8-3079.json | 1.0255 | 1.0768 | 1.0788 | 1.1206 | 1.0854 | 1.0301 |
| known / whitespace-interleaved-16384.json | 3.1906 | 3.5886 | 4.1311 | 4.1745 | 4.9045 | 4.5894 |
| known / whitespace-interleaved-2048.json | 0.2972 | 0.2945 | 0.4249 | 0.4191 | 0.4344 | 0.4607 |
| known / whitespace-interleaved-256.json | 0.0357 | 0.0365 | 0.0528 | 0.0521 | 0.0538 | 0.0524 |
| known / whitespace-leading-16384.json | 3.9226 | 5.3800 | 4.0809 | 3.9940 | 3.9897 | 4.1784 |
| known / whitespace-leading-2048.json | 0.3439 | 0.4261 | 0.3516 | 0.3478 | 0.3669 | 0.3654 |
| known / whitespace-leading-256.json | 0.0421 | 0.0429 | 0.0425 | 0.0432 | 0.0430 | 0.0432 |
| known / whitespace-trailing-16384.json | 3.6039 | 3.9396 | 3.5741 | 3.5476 | 3.9623 | 4.1193 |
| known / whitespace-trailing-2048.json | 0.3338 | 0.3641 | 0.3379 | 0.3296 | 0.3365 | 0.3434 |
| known / whitespace-trailing-256.json | 0.0416 | 0.0429 | 0.0415 | 0.0414 | 0.0415 | 0.0412 |
| known / wide-numbers-262144.json | 22.5171 | 35.2491 | 34.0818 | 29.1934 | 43.8457 | 37.8388 |
| known / wide-numbers-32768.json | 2.7157 | 3.9368 | 2.8557 | 2.5938 | 3.6356 | 3.8272 |
| known / wide-numbers-4096.json | 0.2193 | 0.2430 | 0.2479 | 0.2246 | 0.2334 | 0.2529 |
| known / wide-objects-16384.json | 32.2767 | 44.8387 | 42.0228 | 47.1157 | 51.6148 | 43.8204 |
| known / wide-objects-2048.json | 3.5859 | 4.4550 | 3.1962 | 3.4623 | 4.2854 | 4.2927 |
| known / wide-objects-256.json | 0.3209 | 0.3322 | 0.3644 | 0.3244 | 0.3282 | 0.3249 |
| holdout / v3-held-buried-tail-197.json | 0.4047 | 0.5592 | 0.4820 | 0.4569 | 0.5180 | 0.5328 |
| holdout / v3-held-buried-tail-4093.json | 8.7892 | 9.6501 | 9.5699 | 9.0019 | 11.3602 | 12.5194 |
| holdout / v3-held-escaped-values-197.json | 0.1651 | 0.1594 | 0.1844 | 0.1735 | 0.1725 | 0.1703 |
| holdout / v3-held-escaped-values-4093.json | 3.4823 | 3.4359 | 3.7344 | 3.5228 | 3.9863 | 3.8999 |
| holdout / v3-held-float-values-197.json | 0.1412 | 0.1922 | 0.1563 | 0.1479 | 0.1874 | 0.1791 |
| holdout / v3-held-float-values-4093.json | 2.7409 | 3.6601 | 2.9873 | 3.0624 | 4.1602 | 4.0948 |
| holdout / v3-held-late-records-197.json | 0.4402 | 0.7275 | 0.5792 | 0.5981 | 0.7085 | 0.7521 |
| holdout / v3-held-late-records-4093.json | 9.5932 | 12.6385 | 12.6022 | 12.4132 | 15.7500 | 13.4792 |
| holdout / v3-held-leading-blank-197.json | 0.3109 | 0.3812 | 0.2903 | 0.3151 | 0.3106 | 0.3276 |
| holdout / v3-held-leading-blank-4093.json | 6.5500 | 10.1288 | 6.3134 | 5.7710 | 6.9795 | 6.9134 |
| holdout / v3-held-ragged-object-197.json | 0.1791 | 0.2397 | 0.2018 | 0.1965 | 0.2493 | 0.2220 |
| holdout / v3-held-ragged-object-4093.json | 4.6971 | 5.6018 | 4.2860 | 4.2120 | 6.7994 | 6.4800 |
| holdout / v3-held-space-island-197.json | 0.2004 | 0.4002 | 0.2963 | 0.2893 | 0.3347 | 0.3157 |
| holdout / v3-held-space-island-4093.json | 6.1344 | 8.5505 | 4.5197 | 4.5224 | 6.7232 | 6.6333 |
| holdout / v3-held-step-regions-197.json | 0.1951 | 0.1623 | 0.2029 | 0.1992 | 0.1645 | 0.1639 |
| holdout / v3-held-step-regions-4093.json | 3.7540 | 3.5250 | 3.5930 | 3.4455 | 4.0712 | 3.9848 |

## Full captured heap peak, MiB

| Split / input | Balanced | LowMemory | V2 speed | V3 speed | V2 memory | V3 memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| known / alternating-262144.json | 41.197 | 53.501 | 47.523 | 41.020 | 53.932 | 49.900 |
| known / alternating-32768.json | 5.150 | 6.688 | 5.166 | 5.166 | 5.924 | 5.924 |
| known / alternating-4096.json | 0.977 | 0.883 | 0.735 | 0.735 | 0.860 | 0.860 |
| known / auto-held-bursts-2053.json | 4.504 | 4.492 | 4.420 | 4.420 | 4.609 | 4.609 |
| known / auto-held-bursts-73.json | 0.183 | 0.178 | 0.186 | 0.186 | 0.175 | 0.175 |
| known / auto-held-inner-padding-2053.json | 50.154 | 6.163 | 6.110 | 6.110 | 6.023 | 6.023 |
| known / auto-held-inner-padding-73.json | 0.827 | 0.217 | 0.219 | 0.219 | 0.214 | 0.214 |
| known / auto-held-late-padding-2053.json | 51.785 | 5.285 | 7.540 | 7.540 | 5.270 | 5.270 |
| known / auto-held-late-padding-73.json | 0.878 | 0.178 | 0.186 | 0.186 | 0.226 | 0.226 |
| known / auto-held-long-keys-2053.json | 2.032 | 1.893 | 1.870 | 1.870 | 1.927 | 1.927 |
| known / auto-held-long-keys-73.json | 0.073 | 0.069 | 0.073 | 0.073 | 0.070 | 0.070 |
| known / auto-held-phases-2053.json | 26.711 | 20.884 | 23.179 | 23.179 | 20.813 | 20.813 |
| known / auto-held-phases-73.json | 0.752 | 0.742 | 0.740 | 0.740 | 0.740 | 0.740 |
| known / auto-held-ragged-numbers-2053.json | 2.455 | 2.455 | 2.337 | 2.337 | 2.446 | 2.446 |
| known / auto-held-ragged-numbers-73.json | 0.081 | 0.084 | 0.084 | 0.084 | 0.108 | 0.108 |
| known / auto-held-spiky-strings-2053.json | 18.631 | 18.577 | 18.566 | 18.566 | 18.586 | 18.586 |
| known / auto-held-spiky-strings-73.json | 0.827 | 0.827 | 0.827 | 0.827 | 0.827 | 0.827 |
| known / auto-held-zigzag-2053.json | 1.070 | 1.076 | 1.065 | 1.065 | 1.069 | 1.076 |
| known / auto-held-zigzag-73.json | 0.103 | 0.109 | 0.098 | 0.098 | 0.102 | 0.109 |
| known / deep-128.json | 0.017 | 0.017 | 0.017 | 0.017 | 0.017 | 0.017 |
| known / deep-64.json | 0.009 | 0.009 | 0.009 | 0.009 | 0.009 | 0.009 |
| known / deep-8.json | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| known / dense-first-262144.json | 62.500 | 74.500 | 47.338 | 40.792 | 53.931 | 49.899 |
| known / dense-first-32768.json | 16.813 | 9.313 | 5.769 | 5.769 | 6.301 | 6.301 |
| known / dense-first-4096.json | 0.977 | 1.164 | 2.161 | 2.161 | 1.145 | 1.145 |
| known / dense-zeros-262144.json | 34.500 | 51.500 | 42.435 | 38.424 | 45.073 | 43.460 |
| known / dense-zeros-32768.json | 4.313 | 6.438 | 4.313 | 4.313 | 5.557 | 5.557 |
| known / dense-zeros-4096.json | 0.539 | 0.805 | 0.630 | 0.630 | 0.748 | 0.748 |
| known / escaped-4096.json | 8.752 | 8.797 | 8.774 | 8.774 | 8.831 | 8.831 |
| known / escaped-512.json | 1.094 | 1.100 | 1.097 | 1.097 | 1.094 | 1.094 |
| known / escaped-64.json | 0.143 | 0.143 | 0.143 | 0.143 | 0.143 | 0.143 |
| known / flat-object-16384.json | 5.116 | 6.635 | 5.582 | 5.582 | 5.872 | 5.872 |
| known / flat-object-2048.json | 0.712 | 0.826 | 0.690 | 0.690 | 0.800 | 0.800 |
| known / flat-object-256.json | 0.082 | 0.103 | 0.085 | 0.085 | 0.086 | 0.086 |
| known / held-empty-mix-257.json | 0.227 | 0.241 | 0.235 | 0.235 | 0.229 | 0.229 |
| known / held-empty-mix-4099.json | 3.609 | 3.838 | 3.750 | 3.750 | 3.832 | 3.832 |
| known / held-escape-transition-257.json | 0.112 | 0.112 | 0.112 | 0.115 | 0.110 | 0.110 |
| known / held-escape-transition-4099.json | 0.807 | 0.841 | 0.781 | 0.676 | 0.767 | 0.815 |
| known / held-front-nested-257.json | 0.702 | 0.728 | 0.663 | 0.739 | 0.725 | 0.738 |
| known / held-front-nested-4099.json | 11.771 | 11.121 | 11.110 | 11.797 | 11.660 | 11.705 |
| known / held-long-keys-257.json | 0.043 | 0.043 | 0.043 | 0.043 | 0.043 | 0.043 |
| known / held-long-keys-4099.json | 0.548 | 0.547 | 0.550 | 0.550 | 0.547 | 0.547 |
| known / held-sawtooth-257.json | 0.277 | 0.268 | 0.266 | 0.266 | 0.265 | 0.265 |
| known / held-sawtooth-4099.json | 4.281 | 4.159 | 4.136 | 4.136 | 4.193 | 4.193 |
| known / held-tail-records-257.json | 1.133 | 0.764 | 4.405 | 4.405 | 0.747 | 0.747 |
| known / held-tail-records-4099.json | 54.116 | 12.219 | 15.132 | 15.132 | 11.207 | 11.207 |
| known / large.json | 21.915 | 26.584 | 28.241 | 22.965 | 28.514 | 26.815 |
| known / long-ascii-4096.json | 8.615 | 8.660 | 8.637 | 8.637 | 8.694 | 8.694 |
| known / long-ascii-512.json | 1.077 | 1.083 | 1.080 | 1.080 | 1.077 | 1.077 |
| known / long-ascii-64.json | 0.141 | 0.141 | 0.141 | 0.141 | 0.141 | 0.141 |
| known / medium.json | 2.709 | 3.321 | 2.820 | 2.820 | 3.495 | 3.495 |
| known / nested.json | 0.038 | 0.038 | 0.034 | 0.034 | 0.036 | 0.036 |
| known / small.json | 0.172 | 0.208 | 0.176 | 0.176 | 0.194 | 0.194 |
| known / sparse-first-262144.json | 45.792 | 48.224 | 50.469 | 45.460 | 47.732 | 45.579 |
| known / sparse-first-32768.json | 6.014 | 6.270 | 5.417 | 5.334 | 5.355 | 5.814 |
| known / sparse-first-4096.json | 0.790 | 0.825 | 0.692 | 0.630 | 0.782 | 0.740 |
| known / tiny.json | 0.003 | 0.002 | 0.002 | 0.002 | 0.002 | 0.002 |
| known / unicode-4096.json | 8.638 | 8.684 | 8.660 | 8.660 | 8.718 | 8.718 |
| known / unicode-512.json | 1.080 | 1.086 | 1.083 | 1.083 | 1.080 | 1.080 |
| known / unicode-64.json | 0.141 | 0.141 | 0.141 | 0.141 | 0.141 | 0.141 |
| known / v2-held-chunks-149.json | 0.245 | 0.221 | 0.221 | 0.221 | 0.223 | 0.223 |
| known / v2-held-chunks-3079.json | 5.223 | 4.404 | 4.518 | 4.518 | 4.570 | 4.570 |
| known / v2-held-duplicate-keys-149.json | 0.107 | 0.135 | 0.151 | 0.151 | 0.122 | 0.122 |
| known / v2-held-duplicate-keys-3079.json | 2.558 | 3.285 | 2.266 | 2.266 | 3.453 | 3.453 |
| known / v2-held-front-cells-149.json | 0.300 | 0.309 | 0.286 | 0.286 | 0.311 | 0.311 |
| known / v2-held-front-cells-3079.json | 7.311 | 6.543 | 6.445 | 6.457 | 6.457 | 5.827 |
| known / v2-held-internal-gap-149.json | 0.858 | 0.222 | 0.226 | 0.226 | 0.218 | 0.218 |
| known / v2-held-internal-gap-3079.json | 4.439 | 4.537 | 6.171 | 6.171 | 4.491 | 4.297 |
| known / v2-held-ragged-width-149.json | 0.104 | 0.122 | 0.153 | 0.153 | 0.110 | 0.110 |
| known / v2-held-ragged-width-3079.json | 2.283 | 2.283 | 2.208 | 2.208 | 2.275 | 2.275 |
| known / v2-held-space-strings-149.json | 0.112 | 0.095 | 0.097 | 0.097 | 0.096 | 0.095 |
| known / v2-held-space-strings-3079.json | 2.224 | 1.853 | 1.855 | 1.855 | 1.918 | 1.918 |
| known / v2-held-tail-cells-149.json | 0.913 | 0.359 | 0.410 | 0.410 | 0.339 | 0.339 |
| known / v2-held-tail-cells-3079.json | 40.469 | 6.356 | 7.313 | 7.313 | 5.850 | 5.850 |
| known / v2-held-utf8-149.json | 0.065 | 0.061 | 0.065 | 0.065 | 0.062 | 0.062 |
| known / v2-held-utf8-3079.json | 1.316 | 1.231 | 1.286 | 1.286 | 1.199 | 1.199 |
| known / whitespace-interleaved-16384.json | 4.328 | 5.266 | 4.298 | 4.298 | 5.440 | 5.440 |
| known / whitespace-interleaved-2048.json | 0.528 | 0.658 | 0.538 | 0.538 | 0.657 | 0.657 |
| known / whitespace-interleaved-256.json | 0.068 | 0.082 | 0.069 | 0.069 | 0.068 | 0.068 |
| known / whitespace-leading-16384.json | 4.565 | 5.111 | 4.934 | 4.687 | 4.609 | 4.630 |
| known / whitespace-leading-2048.json | 0.588 | 0.624 | 0.626 | 0.565 | 0.599 | 0.586 |
| known / whitespace-leading-256.json | 0.076 | 0.077 | 0.073 | 0.073 | 0.078 | 0.078 |
| known / whitespace-trailing-16384.json | 50.781 | 6.531 | 6.613 | 6.613 | 6.020 | 6.020 |
| known / whitespace-trailing-2048.json | 1.082 | 0.817 | 0.579 | 0.579 | 0.795 | 0.795 |
| known / whitespace-trailing-256.json | 0.794 | 0.102 | 0.102 | 0.102 | 0.079 | 0.079 |
| known / wide-numbers-262144.json | 39.161 | 52.697 | 46.535 | 39.989 | 53.128 | 49.096 |
| known / wide-numbers-32768.json | 4.650 | 6.573 | 4.932 | 4.932 | 5.810 | 5.810 |
| known / wide-numbers-4096.json | 0.615 | 0.820 | 0.673 | 0.673 | 0.784 | 0.784 |
| known / wide-objects-16384.json | 43.923 | 53.182 | 47.020 | 55.615 | 53.613 | 49.581 |
| known / wide-objects-2048.json | 5.449 | 6.644 | 5.674 | 5.674 | 5.952 | 5.952 |
| known / wide-objects-256.json | 0.692 | 0.830 | 0.705 | 0.705 | 0.854 | 0.854 |
| holdout / v3-held-buried-tail-197.json | 0.979 | 0.645 | 0.476 | 0.476 | 0.624 | 0.624 |
| holdout / v3-held-buried-tail-4093.json | 43.471 | 10.806 | 13.631 | 13.631 | 11.830 | 11.830 |
| holdout / v3-held-escaped-values-197.json | 0.146 | 0.134 | 0.136 | 0.136 | 0.138 | 0.138 |
| holdout / v3-held-escaped-values-4093.json | 2.978 | 2.727 | 2.776 | 2.776 | 2.904 | 2.904 |
| holdout / v3-held-float-values-197.json | 0.138 | 0.201 | 0.164 | 0.164 | 0.195 | 0.195 |
| holdout / v3-held-float-values-4093.json | 2.859 | 3.577 | 2.975 | 2.975 | 3.950 | 3.950 |
| holdout / v3-held-late-records-197.json | 1.012 | 0.819 | 0.689 | 0.689 | 0.815 | 0.815 |
| holdout / v3-held-late-records-4093.json | 18.073 | 14.710 | 16.571 | 16.571 | 16.289 | 14.534 |
| holdout / v3-held-leading-blank-197.json | 0.305 | 0.343 | 0.344 | 0.344 | 0.345 | 0.324 |
| holdout / v3-held-leading-blank-4093.json | 7.418 | 6.822 | 6.977 | 7.276 | 6.769 | 7.224 |
| holdout / v3-held-ragged-object-197.json | 0.279 | 0.275 | 0.287 | 0.287 | 0.276 | 0.276 |
| holdout / v3-held-ragged-object-4093.json | 5.847 | 6.570 | 6.125 | 6.125 | 7.008 | 7.008 |
| holdout / v3-held-space-island-197.json | 0.886 | 0.341 | 0.306 | 0.325 | 0.324 | 0.341 |
| holdout / v3-held-space-island-4093.json | 8.045 | 6.892 | 6.767 | 6.767 | 6.805 | 6.997 |
| holdout / v3-held-step-regions-197.json | 0.200 | 0.192 | 0.204 | 0.204 | 0.190 | 0.190 |
| holdout / v3-held-step-regions-4093.json | 3.744 | 3.744 | 3.811 | 3.811 | 3.739 | 3.739 |

## Growth decisions and correctness

| Split / goal | Expansions | Pressure active | Pressure raised floor | Byte floor overrides | Proven final capacity |
| --- | ---: | ---: | ---: | ---: | ---: |
| known/speed | 275 | 73 | 73 | 15 | 24 |
| known/memory | 535 | 120 | 120 | 36 | 31 |
| holdout/speed | 53 | 11 | 11 | 0 | 3 |
| holdout/memory | 109 | 22 | 22 | 3 | 5 |

Exact comparators check every token field, canonical integer/double/negative-zero representation, results and full error diagnostics against both production modes.
Independent journal checks recompute the pressure floor, verify unchanged ordinary floors, justify each byte exception and reject growth after a proved final-capacity reserve.
Token count/capacity/movement matches allocation profiles; retained categories partition memory and all tracked live bytes/blocks return to zero.
Arithmetic tests cover rational rounding, tiny capacities, saturation near size_t/max_size and near-EOF final capacity. Corpus replay and coverage fuzzers compare independent production parsing.

CPU frequency, code layout, allocator state and background load can affect times. Full sample spread, six rounds, hashes and frozen artifact identities are retained.
The 107 known/new synthetic documents are not representative user workloads; future promotion also needs real workload and other-toolchain measurements.

Raw [calibration, selection, freeze, measurements and journals](auto-v3-msvc1951/) accompany [reproduction instructions](../README.md#auto-v3-growth-under-copy-pressure).
Regenerate with `python benchmarks/auto-v3/summarize.py benchmarks/results/auto-v3-msvc1951 REPORT.md`.
