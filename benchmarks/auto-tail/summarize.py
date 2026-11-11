"""Render the experiment report from the frozen measurements."""

import argparse
import csv
import json
import statistics
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

PLAN = Path(__file__).with_name("plan.json")


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    root = args.results
    metadata = json.loads((root / "metadata.json").read_text())
    freeze = json.loads((root / "freeze.json").read_text())
    plan = json.loads(PLAN.read_text())
    assert sha(PLAN) == freeze["plan_sha256"]
    assert sha(root / "freeze.json") == metadata["freeze_sha256"]
    for name, digest in metadata["files"].items():
        assert sha(root / name) == digest, name

    samples = defaultdict(dict)
    for row in read_rows(root / "timings.csv"):
        key = row["compiler"], row["dataset"], row["mode"], row["operation"]
        index = int(row["round"])
        assert index not in samples[key]
        samples[key][index] = float(row["median_us"])
    expected_rounds = set(range(1, plan["rounds"] + 1))
    for rounds in samples.values():
        assert set(rounds) == expected_rounds

    def time(compiler, name, mode, operation="parse"):
        return statistics.median(samples[compiler, name, mode, operation].values())

    peaks = {(r["compiler"], r["dataset"], r["mode"]): int(r["peak_live_bytes"])
             for r in read_rows(root / "memory.csv") if r["stage"] == "whole_parse"}
    compilers = ("msvc", "clang")
    probes = {}
    for compiler in compilers:
        for row in read_rows(root / f"{compiler}-tail-decisions.csv"):
            if row["stage"] == "lex_only" and row["probe_status"] != "not_run":
                probes[compiler, row["dataset"]] = row

    lines = [
        "# Bounded tail count before the final speed reservation", "",
        "The prototype reuses the production lexer to count a suffix of at most",
        "256 KiB when v3 raises the growth floor and reserves its remaining-byte",
        "bound. It restores the cursor before the main scan. When the suffix",
        "including EOF fits in the ordinary 1.5× allocation, the prototype",
        "requests that capacity. A token-limit stop or a lexical error keeps the",
        "v3 request. The main scan formats the original diagnostic.", "",
        f"The build was frozen at commit {freeze['source_revision'][:7]}.",
        f"Timing ran on {metadata['cpu']} under {metadata['os']} with logical CPU 0.",
        "MSVC 19.51 and Clang-cl 23.1.5 use Microsoft STL on this machine.",
        "Eight rotated rounds compare all eight compiler and mode pairs. Each",
        "round records five samples of three operations after five warm-ups.",
        "The table reports the median of the eight round medians.",
        "Parse time includes the count and destruction of the parsed value.",
        "Peak memory is captured requested C++ heap memory.", "",
        "The fresh geometry includes three generated inputs and two original",
        "Natural Earth files. The synthetic seed and the pinned external",
        "revisions were recorded before measurement. Exact comparisons against",
        "both production presets covered all eleven inputs.", "",
        "[Protocol](../auto-tail/plan.json) · [Raw data and build hashes](auto-tail-windows/)", "",
        "## Full parse and peak", "",
        "| Compiler | Input | V3 ms | Probe ms | Probe / v3 time | V3 peak MiB | Probe peak MiB |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    inputs = metadata["inputs"]
    for compiler in compilers:
        for entry in inputs:
            name = entry["name"]
            old_time = time(compiler, name, "v3-speed")
            new_time = time(compiler, name, "tail")
            old_peak = peaks[compiler, name, "v3-speed"]
            new_peak = peaks[compiler, name, "tail"]
            lines.append(
                f"| {compiler} | {name} | {old_time/1000:.3f} | {new_time/1000:.3f} | "
                f"{new_time/old_time:.3f} | {old_peak/1048576:.3f} | {new_peak/1048576:.3f} |"
            )
    lines += ["", "## Probe decisions", "",
              "| Compiler | Input | Outcome | Bytes scanned | V3 request | Request with probe |",
              "| --- | --- | --- | ---: | ---: | ---: |"]
    for (compiler, name), row in probes.items():
        lines.append(f"| {compiler} | {name} | {row['probe_status']} | {row['probe_bytes']} | "
                     f"{row['probe_original_request']} | {row['request']} |")
    lines += ["", "The raw timing rows also include lexer-only measurements. The decision",
              "journal records the token quota outcome and the confirmed suffix count.", "",
              "## Speed criteria", "",
              "The criteria apply to inputs with a Balanced median of at least 1 ms.",
              "Time may reach 1.5× the fastest fixed mode. Peak may reach 2× the",
              "lowest fixed peak and 1.5× the Balanced peak.", "",
              "| Compiler | Mode | Known inputs passed | Fresh geometry passed |",
              "| --- | --- | ---: | ---: |"]
    gates = plan["gates"]
    failures = []
    for compiler in compilers:
        for mode in ("v3-speed", "tail"):
            totals = {"known": 0, "new": 0}
            passed = totals.copy()
            for entry in inputs:
                name, split = entry["name"], entry["split"]
                balanced_time = time(compiler, name, "balanced")
                if balanced_time < gates["non_tiny_balanced_us"]:
                    continue
                totals[split] += 1
                fixed_time = min(balanced_time, time(compiler, name, "low-memory"))
                balanced_peak = peaks[compiler, name, "balanced"]
                fixed_peak = min(balanced_peak, peaks[compiler, name, "low-memory"])
                peak = peaks[compiler, name, mode]
                ratios = {
                    "time vs best fixed": (time(compiler, name, mode) / fixed_time, gates["time_vs_best_fixed"]),
                    "peak vs best fixed": (peak / fixed_peak, gates["peak_vs_best_fixed"]),
                    "peak vs Balanced": (peak / balanced_peak, gates["peak_vs_balanced"]),
                }
                failed = [f"{metric} {value:.3f}×" for metric, (value, limit) in ratios.items() if value > limit]
                if failed:
                    failures.append(f"- {compiler} / {mode} / {name} exceeded " + ", ".join(failed) + ".")
                else:
                    passed[split] += 1
            lines.append(f"| {compiler} | {mode} | {passed['known']}/{totals['known']} | "
                         f"{passed['new']}/{totals['new']} |")
    if failures:
        lines += ["", *failures]
    lines += ["", "Fresh external geometry comes from Natural Earth at 1:50m."]
    lines += [f"[{entry['name']}]({entry['source']})"
              for entry in inputs if entry["source"].startswith("https://")]
    args.report.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
