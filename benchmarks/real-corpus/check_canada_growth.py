"""Check the requested token-buffer overlap on the pinned Canada fixture."""

import argparse
import csv
from pathlib import Path

EXPECTED_TOKENS = 334_374
# The old and new buffers at the largest recorded v3 speed expansion.
MAX_OVERLAP_SLOTS = 812_936


def check_canada_growth(rows):
    for stage in ("parse", "lex_only"):
        events = [
            row for row in rows
            if row["dataset"] == "canada.json" and row["stage"] == stage
        ]
        if len(events) < 2 or events[0]["reason"] != "initial":
            raise ValueError(f"canada.json {stage}: incomplete allocation journal")

        finish = events[-1]
        if (finish["reason"] != "finished" or finish["status"] != "accepted"
                or int(finish["tokens"]) != EXPECTED_TOKENS):
            raise ValueError(f"canada.json {stage}: expected {EXPECTED_TOKENS} accepted tokens")

        peak_slots = 0
        for row in events[:-1]:
            slots = int(row["old_capacity"]) + int(row["request"])
            if int(row["overlap_bytes"]) != slots * int(row["token_size"]):
                raise ValueError(f"canada.json {stage}: inconsistent token-buffer overlap")
            peak_slots = max(peak_slots, slots)

        if peak_slots > MAX_OVERLAP_SLOTS:
            raise ValueError(
                f"canada.json {stage}: {peak_slots} simultaneous requested slots "
                f"exceed the recorded ceiling of {MAX_OVERLAP_SLOTS}"
            )
        print(f"canada.json {stage}: {peak_slots} simultaneous requested token slots")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("journal", type=Path, help="Auto v3 speed decision CSV")
    args = parser.parse_args()
    with args.journal.open(encoding="utf-8", newline="") as stream:
        check_canada_growth(list(csv.DictReader(stream)))


if __name__ == "__main__":
    main()
