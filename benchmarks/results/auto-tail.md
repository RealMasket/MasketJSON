# Bounded tail count before the final speed reservation

The prototype reuses the production lexer to count a suffix of at most
256 KiB when v3 raises the growth floor and reserves its remaining-byte
bound. It restores the cursor before the main scan. When the suffix
including EOF fits in the ordinary 1.5× allocation, the prototype
requests that capacity. A token-limit stop or a lexical error keeps the
v3 request. The main scan formats the original diagnostic.

The build was frozen at commit 45349b3.
Timing ran on 12th Gen Intel(R) Core(TM) i5-12600KF under Windows-10-10.0.19045-SP0 with logical CPU 0.
MSVC 19.51 and Clang-cl 23.1.5 use Microsoft STL on this machine.
Eight rotated rounds compare all eight compiler and mode pairs. Each
round records five samples of three operations after five warm-ups.
The table reports the median of the eight round medians.
Parse time includes the count and destruction of the parsed value.
Peak memory is captured requested C++ heap memory.

The fresh geometry includes three generated inputs and two original
Natural Earth files. The synthetic seed and the pinned external
revisions were recorded before measurement. Exact comparisons against
both production presets covered all eleven inputs.

[Protocol](../auto-tail/plan.json) · [Raw data and build hashes](auto-tail-windows/)

## Full parse and peak

| Compiler | Input | V3 ms | Probe ms | Probe / v3 time | V3 peak MiB | Probe peak MiB |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| msvc | canada.json | 35.453 | 36.027 | 1.016 | 39.360 | 36.957 |
| msvc | dense-zeros-262144.json | 24.270 | 24.506 | 1.010 | 38.424 | 38.424 |
| msvc | alternating-262144.json | 30.463 | 29.810 | 0.979 | 41.020 | 41.020 |
| msvc | held-tail-records-4099.json | 10.268 | 10.204 | 0.994 | 15.132 | 15.132 |
| msvc | probe-fits.json | 9.021 | 9.384 | 1.040 | 20.387 | 20.145 |
| msvc | probe-limit.json | 11.842 | 12.207 | 1.031 | 20.574 | 20.574 |
| msvc | new-line.json | 29.808 | 30.228 | 1.014 | 34.088 | 34.088 |
| msvc | new-rings.json | 28.730 | 28.999 | 1.009 | 34.590 | 34.590 |
| msvc | new-dense-coordinates.json | 19.975 | 20.577 | 1.030 | 21.689 | 21.689 |
| msvc | new-countries.json | 66.386 | 66.743 | 1.005 | 69.951 | 69.951 |
| msvc | new-lakes.json | 16.348 | 16.136 | 0.987 | 21.530 | 20.727 |
| clang | canada.json | 31.591 | 31.451 | 0.996 | 39.360 | 36.957 |
| clang | dense-zeros-262144.json | 23.249 | 23.403 | 1.007 | 38.424 | 38.424 |
| clang | alternating-262144.json | 28.357 | 29.035 | 1.024 | 41.020 | 41.020 |
| clang | held-tail-records-4099.json | 8.189 | 8.134 | 0.993 | 15.132 | 15.132 |
| clang | probe-fits.json | 8.727 | 8.777 | 1.006 | 20.387 | 20.145 |
| clang | probe-limit.json | 11.245 | 11.606 | 1.032 | 20.574 | 20.574 |
| clang | new-line.json | 26.720 | 26.422 | 0.989 | 34.088 | 34.088 |
| clang | new-rings.json | 25.810 | 25.358 | 0.983 | 34.590 | 34.590 |
| clang | new-dense-coordinates.json | 17.777 | 17.967 | 1.011 | 21.689 | 21.689 |
| clang | new-countries.json | 59.679 | 60.677 | 1.017 | 69.951 | 69.951 |
| clang | new-lakes.json | 14.156 | 14.847 | 1.049 | 21.530 | 20.727 |

## Probe decisions

| Compiler | Input | Outcome | Bytes scanned | V3 request | Request with probe |
| --- | --- | --- | ---: | ---: | ---: |
| msvc | canada.json | fits | 204578 | 508758 | 456267 |
| msvc | dense-zeros-262144.json | token_limit | 152088 | 524290 | 524290 |
| msvc | probe-fits.json | fits | 92190 | 266008 | 260724 |
| msvc | probe-limit.json | token_limit | 86907 | 270002 | 270002 |
| msvc | new-dense-coordinates.json | token_limit | 87517 | 282620 | 282620 |
| msvc | new-lakes.json | fits | 104436 | 278254 | 260724 |
| clang | canada.json | fits | 204578 | 508758 | 456267 |
| clang | dense-zeros-262144.json | token_limit | 152088 | 524290 | 524290 |
| clang | probe-fits.json | fits | 92190 | 266008 | 260724 |
| clang | probe-limit.json | token_limit | 86907 | 270002 | 270002 |
| clang | new-dense-coordinates.json | token_limit | 87517 | 282620 | 282620 |
| clang | new-lakes.json | fits | 104436 | 278254 | 260724 |

The raw timing rows also include lexer-only measurements. The decision
journal records the token quota outcome and the confirmed suffix count.

## Speed criteria

The criteria apply to inputs with a Balanced median of at least 1 ms.
Time may reach 1.5× the fastest fixed mode. Peak may reach 2× the
lowest fixed peak and 1.5× the Balanced peak.

| Compiler | Mode | Known inputs passed | Fresh geometry passed |
| --- | --- | ---: | ---: |
| msvc | v3-speed | 5/6 | 5/5 |
| msvc | tail | 5/6 | 5/5 |
| clang | v3-speed | 4/6 | 5/5 |
| clang | tail | 5/6 | 5/5 |

- msvc / v3-speed / canada.json exceeded peak vs Balanced 1.582×.
- msvc / tail / probe-fits.json exceeded time vs best fixed 1.550×.
- clang / v3-speed / canada.json exceeded peak vs Balanced 1.582×.
- clang / v3-speed / probe-fits.json exceeded time vs best fixed 1.550×.
- clang / tail / probe-fits.json exceeded time vs best fixed 1.559×.

Fresh external geometry comes from Natural Earth at 1:50m.
[new-countries.json](https://github.com/nvkelso/natural-earth-vector/blob/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_50m_admin_0_countries.geojson)
[new-lakes.json](https://github.com/nvkelso/natural-earth-vector/blob/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_50m_lakes.geojson)
