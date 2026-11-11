# Final token-buffer expansion on Canada GeoJSON

The original 2,251,051-byte fixture ends with 334,374 tokens including EOF.
MSVC and Clang record the same last expansion and whole-parse peak.
[External-corpus measurements](real-corpus.md)

## What the last expansion did

The lexer has 304,178 stored tokens and has consumed 2,046,473 bytes when it
scans the pending token. It has already relocated 267,174 tokens. Speed v3
activates projected copy pressure when that counter exceeds half the current
token count, which is 152,089 here.

| Quantity | Slots |
| --- | ---: |
| Density estimate before the 6.25% speed margin | 334,588 |
| Forecast including the speed margin | 355,499 |
| Ordinary geometric floor at 1.5× | 456,267 |
| Geometric floor with copy pressure at 1.75× | 532,311 |
| Ceiling for the 4 MiB speculative reserve | 391,560 |
| Remaining-byte bound and actual request | 508,758 |
| Final token count | 334,374 |

The forecast before the margin is within about 214 tokens of the actual total.
The ordinary floor alone already exceeds the byte ceiling. Copy pressure
raises the floor further and the byte bound brings the request back down.
The bound counts at most one token for each of the remaining 204,578 bytes,
plus the pending token and EOF. The suffix actually yields 30,194 tokens
after the pending token and before EOF. The new buffer finishes with 174,384
unused slots. [MSVC speed decision journal](real-corpus-windows/msvc/speed-decisions.csv)

The two buffers account for 39,020,928 bytes at the expansion. Add 2,251,095
bytes for the lexer source copy and 78 bytes requested by the Microsoft STL
to align the two large allocations. The sum is exactly the observed peak of
41,272,101 bytes or 39.360 MiB. Balanced peaks at 24.876 MiB.
[Speed profile](real-corpus-windows/msvc/v3-speed-memory.csv) · [Balanced profile](real-corpus-windows/msvc/balanced-memory.csv)

## Replay of the last request

TokenRelocation replayed 334,374 token insertions from initial capacity 256. The first five requests
were 1,282, 5,386, 86,434, 173,816 and 304,178 slots in each run. The final
request varied as shown below. Each run completed with six expansions and
571,352 relocated tokens. [TokenRelocation instructions](../auto-v2/diagnosis/README.md)

| Last request | Slots | Simultaneous token bytes | Calculated expansion peak, MiB |
| --- | ---: | ---: | ---: |
| Recorded | 508,758 | 39,020,928 | 39.360 |
| Ordinary 1.5× floor | 456,267 | 36,501,360 | 36.957 |
| 4 MiB byte ceiling | 391,560 | 33,395,424 | 33.995 |

The calculated peak adds the recorded source allocation and alignment bytes
to the buffer sizes. The replay supplies the observed token count and
measures capacity and relocation in isolation. On this input the ordinary
floor would put the last expansion below 1.5× the recorded Balanced peak.
The byte-ceiling request also fits the observed suffix and would require a
separate growth rule because it falls below the ordinary geometric floor.

## Regression check

CI verifies the pinned input through the external corpus manifest and checks
both speed journals for an accepted 334,374-token result. The check recalculates
the simultaneous requested slots and requires a peak at or below the recorded
812,936 slots. This lets a later improvement lower the overlap. The benchmark
report separately evaluates the 1.5× whole-parse limit. [Corpus instructions](../real-corpus/README.md)
