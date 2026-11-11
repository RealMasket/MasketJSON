"""Verify the probe's work limit, proof and lexer state on targeted cases."""

import argparse
import sys
from pathlib import Path

benchmarks = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(benchmarks / "reservation"))
from check_matrix import executable, run
sys.path.insert(0, str(benchmarks / "auto-v3"))
from journal import validate

from fixtures import focused


def check_trace(text, inputs):
    sizes = {path.name: path.stat().st_size for path in inputs}
    rows = validate(text, "speed", sizes)
    for name, size in sizes.items():
        for stage in ("parse", "lex_only"):
            events = [r for r in rows if r["dataset"] == name and r["stage"] == stage]
            probes = [r for r in events if r["probe_status"] != "not_run"]
            assert len(probes) <= 1, (name, stage, "multiple probes")
            if not probes:
                continue

            row = probes[0]
            capacity = int(row["old_capacity"])
            remaining = size - int(row["position"])
            floor = int(row["probe_ordinary_floor"])
            original = int(row["probe_original_request"])
            scanned = int(row["probe_bytes"])
            count = int(row["probe_tokens"])
            quota = floor - capacity - 1
            assert 0 <= scanned <= remaining <= 256 * 1024
            assert 0 <= count <= quota
            assert floor == capacity + capacity // 2
            assert original == capacity + remaining + 2 and original > floor
            assert row["pressure_raised_floor"] == row["tail_applied"] == "1"

            status = row["probe_status"]
            if status == "fits":
                assert scanned == remaining
                assert int(row["request"]) == floor
                assert events[-1]["reason"] == "finished"
                assert int(events[-1]["tokens"]) == capacity + 1 + count
            else:
                assert int(row["request"]) == original
                if status == "token_limit":
                    assert count == quota
                else:
                    assert status == "invalid" and events[-1]["reason"] == "aborted"
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument("--bin", type=Path)
    location.add_argument("--build", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--canada", type=Path)
    args = parser.parse_args()
    if args.build:
        args.bin = args.build / "benchmarks" / "auto-tail"
        if (args.bin / "Release").is_dir():
            args.bin /= "Release"
    fixtures = focused(args.output / "data")
    valid = [p for p in fixtures if "invalid" not in p.name]
    invalid = [p for p in fixtures if "invalid" in p.name]
    if args.canada:
        valid.append(args.canada)
    print(run(executable(args.bin, "AutoTailVerify"), *valid), end="")
    print(run(executable(args.bin, "AutoTailVerify"), "--invalid", *invalid), end="")
    text = run(executable(args.bin, "AutoTailTrace"), *valid, *invalid)
    rows = check_trace(text, valid + invalid)
    (args.output / "decisions.csv").write_bytes(text.encode())
    expected = {
        "probe-fits.json": "fits",
        "probe-limit.json": "token_limit",
        "probe-invalid-number.json": "invalid",
        "probe-invalid-utf8.json": "invalid",
    }
    if args.canada:
        expected[args.canada.name] = "fits"
    for name, status in expected.items():
        actual = [r["probe_status"] for r in rows
                  if r["dataset"] == name and r["probe_status"] != "not_run"]
        assert actual == [status, status], (name, status, actual)
    print("Probe fit, token limit and malformed suffix preserve both lexer paths")


if __name__ == "__main__":
    main()
