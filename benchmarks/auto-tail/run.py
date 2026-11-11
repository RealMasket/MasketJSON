"""Record a frozen MSVC/Clang comparison of the bounded tail probe."""

import argparse
import csv
import io
import json
import platform
import random
import shutil
import subprocess
import urllib.request
from hashlib import sha1, sha256
from pathlib import Path

from check import check_trace, executable, run
from check_matrix import validate_memory
from fixtures import focused
from run_matrix import cpu_name, pin

HERE = Path(__file__).resolve().parent
BENCHMARKS = HERE.parent
REPO = BENCHMARKS.parent
PLAN = HERE / "plan.json"


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.write_bytes((json.dumps(data, indent=2) + "\n").encode())


def directory(build, part):
    path = build / "benchmarks" / part
    return path / "Release" if (path / "Release").is_dir() else path


def programs(build, mode):
    if mode == "tail":
        folder, prefix, suffix = directory(build, "auto-tail"), "AutoTail", ""
    elif mode == "v3-speed":
        folder, prefix, suffix = directory(build, "auto-v3"), "AutoV3", "-speed"
    else:
        folder, prefix, suffix = directory(build, "auto"), "Auto", "-" + mode
    roles = ["Time", "Profile", "Inspect"]
    if mode in ("v3-speed", "tail"):
        roles += ["Trace", "Verify"]
    return {role: executable(folder, prefix + role + suffix) for role in roles}


def evaluation(directory, settings):
    directory.mkdir()
    rng = random.Random(settings["seed"])

    def point():
        return [rng.randrange(-1_700_000_000, 1_700_000_001) / 10_000_000,
                rng.randrange(-800_000_000, 800_000_001) / 10_000_000]

    def ring(index):
        # Disjoint, closed rectangular rings with varied decimal coordinates.
        x = index % 26 * 4 - 52 + rng.randrange(1, 1_000_000) / 10_000_000
        y = index // 26 * 4 - 48 + rng.randrange(1, 1_000_000) / 10_000_000
        step = rng.randrange(100_000, 250_001) / 10_000_000
        width = step * 21
        vertices = ([(x + i * step, y) for i in range(21)]
                    + [(x + width, y + i * step) for i in range(21)]
                    + [(x + width - i * step, y + width) for i in range(21)]
                    + [(x, y + width - i * step) for i in range(21)])
        rounded = [[round(lon, 7), round(lat, 7)] for lon, lat in vertices]
        return rounded + [rounded[0]]

    geometries = {
        "new-line.json": {"type": "LineString", "coordinates": [point() for _ in range(55_000)]},
        "new-rings.json": {"type": "MultiPolygon", "coordinates": [[ring(i)] for i in range(650)]},
        "new-dense-coordinates.json": {
            "type": "LineString",
            "coordinates": [point() for _ in range(29_000)]
                + [[rng.randrange(10), rng.randrange(10)] for _ in range(18_000)],
        },
    }
    assert list(geometries) == settings["synthetic"]
    origins = {}
    for name, geometry in geometries.items():
        (directory / name).write_bytes(json.dumps(geometry, separators=(",", ":")).encode())
        origins[name] = f"Generated geometry, seed {settings['seed']}"
    for name, entry in settings["external"].items():
        revision = settings["natural_earth_revision"]
        url = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{revision}/{entry['path']}"
        with urllib.request.urlopen(url, timeout=60) as response:
            body = response.read(entry["bytes"] + 1)
        assert len(body) == entry["bytes"]
        assert sha1(f"blob {len(body)}\0".encode() + body).hexdigest() == entry["blob_sha1"]
        (directory / name).write_bytes(body)
        origins[name] = f"https://github.com/nvkelso/natural-earth-vector/blob/{revision}/{entry['path']}"
    return origins


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--msvc", required=True, type=Path)
    parser.add_argument("--clang", required=True, type=Path)
    parser.add_argument("--known", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    builds = {"msvc": args.msvc, "clang": args.clang}
    pairs = [(compiler, mode) for mode in plan["modes"] for compiler in builds]
    binaries = {(compiler, mode): programs(builds[compiler], mode) for compiler, mode in pairs}
    hashes = {f"{c}/{m}/{role}": sha(path)
              for (c, m), roles in binaries.items() for role, path in roles.items()}
    info = {}
    for compiler, build in builds.items():
        info[compiler] = (directory(build, "auto-v3") / "build-info-Release.txt").read_text()
        assert all(flag in info[compiler] for flag in (
            "configuration=Release", "speed_quarters=7", "speed_lookahead=1",
            "speed_budget_bytes=4194304"))
    git = ["git", "-c", f"safe.directory={REPO.as_posix()}"]
    revision = subprocess.check_output(git + ["rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    generated = ("tail.cpp", "AutoReservationWithTail.hpp", "trace.cpp")
    freeze = {
        "source_revision": revision,
        "plan_sha256": sha(PLAN),
        "binary_sha256": hashes,
        "build_info": info,
        "generated_sha256": {
            compiler: {name: sha(build / "benchmarks" / "auto-tail" / "generated" / name)
                       for name in generated}
            for compiler, build in builds.items()
        },
    }
    args.output.mkdir(parents=True)
    save_json(args.output / "freeze.json", freeze)

    known = args.output / "known"
    focused(known)
    historical = json.loads((BENCHMARKS / "results/auto-v3-msvc1951/known/metadata.json").read_text())
    digests = {entry["name"]: entry["sha256"] for entry in historical["inputs"]}
    corpus = json.loads((BENCHMARKS / "real-corpus/corpus.json").read_text())
    digests.update({entry["name"]: entry["sha256"] for entry in corpus["entries"]})
    for name in plan["known"]:
        if not (known / name).is_file():
            source = next(path / name for path in args.known if (path / name).is_file())
            assert sha(source) == digests[name], name
            shutil.copyfile(source, known / name)
    new = args.output / "new"
    origins = evaluation(new, plan["evaluation"])
    inputs = [known / name for name in plan["known"]] + [new / name for name in origins]
    sizes = {p.name: p.stat().st_size for p in inputs}

    restore = pin(plan["logical_cpu"])
    try:
        shapes = None
        memory = []
        for pair, tools in binaries.items():
            compiler, mode = pair
            observed = run(tools["Inspect"], *inputs)
            if shapes is None:
                shapes = observed
                (args.output / "shapes.csv").write_bytes(shapes.encode())
            assert observed == shapes, pair
            if "Verify" in tools:
                run(tools["Verify"], *inputs)
            profile = run(tools["Profile"], *inputs)
            indexed = validate_memory(profile, sizes)
            memory.extend(dict(compiler=compiler, mode=mode, **row) for row in indexed.values())
            if "Trace" in tools:
                trace = run(tools["Trace"], *inputs)
                if mode == "tail":
                    check_trace(trace, inputs)
                (args.output / f"{compiler}-{mode}-decisions.csv").write_bytes(trace.encode())
            print(f"{compiler}/{mode} exact/profile checks passed", flush=True)
        write_csv(args.output / "memory.csv", memory)

        timings = []
        order = []
        for index in range(plan["rounds"]):
            rotated = pairs[index:] + pairs[:index]
            order.append(rotated)
            for compiler, mode in rotated:
                text = run(binaries[compiler, mode]["Time"], plan["iterations"], plan["samples"], *inputs)
                rows = list(csv.DictReader(io.StringIO(text)))
                assert len(rows) == 2 * len(inputs)
                assert {(r["dataset"], r["operation"]) for r in rows} == {
                    (p.name, operation) for p in inputs for operation in ("parse", "lex_only")}
                for row in rows:
                    assert row["configuration"] == "Release"
                    assert int(row["bytes"]) == sizes[row["dataset"]]
                    assert int(row["samples"]) == plan["samples"]
                    assert int(row["iterations"]) == plan["iterations"]
                    assert 0 < float(row["min_us"]) <= float(row["median_us"]) <= float(row["max_us"])
                    timings.append(dict(compiler=compiler, mode=mode, round=index + 1, **row))
            print(f"Round {index + 1}/{plan['rounds']} complete", flush=True)
        write_csv(args.output / "timings.csv", timings)
    finally:
        restore()

    for (compiler, mode), tools in binaries.items():
        for role, path in tools.items():
            assert sha(path) == hashes[f"{compiler}/{mode}/{role}"]
    metadata = {
        "cpu": cpu_name(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "freeze_sha256": sha(args.output / "freeze.json"),
        "inputs": [
            {"name": p.name, "split": p.parent.name, "bytes": sizes[p.name],
             "sha256": sha(p), "source": origins.get(p.name, "Previously measured or focused fixture")}
            for p in inputs
        ],
        "round_order": order,
        "files": {p.name: sha(p) for p in args.output.glob("*.csv")},
    }
    save_json(args.output / "metadata.json", metadata)


if __name__ == "__main__":
    main()
