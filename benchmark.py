"""Paired Quicksort trials and a separate chained-hash load-factor experiment.

Run python3 benchmark.py from this repository. CSV data and environment details
are written to results/. No third-party package is required.
"""

import argparse
import csv
import gc
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path

from algorithms.hash_table import ChainedHashTable, PRIME
from algorithms.quicksort import deterministic_quicksort, randomized_quicksort

DISTRIBUTIONS = ("random", "sorted", "reverse", "repeated", "equal")
METHODS = ("randomized", "first_pivot")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def dataset(size, distribution, seed):
    rng = random.Random(seed)
    data = list(range(size))
    if distribution == "random":
        rng.shuffle(data)
    elif distribution == "reverse":
        data.reverse()
    elif distribution == "repeated":
        data = [rng.randrange(8) for _ in range(size)]
    elif distribution == "equal":
        data = [7] * size
    return data


def run_sort(method, data, seed):
    if method == "randomized":
        randomized_quicksort(data, seed)
    else:
        deterministic_quicksort(data)


class Counted:
    comparisons = 0

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        type(self).comparisons += 1
        return self.value < other.value


def hash_experiment(output):
    rows = []
    capacity = 1024
    for size in (256, 512, 1024, 2048, 4096):
        for seed in range(20):
            rng = random.Random(532 + seed)
            sampled = rng.sample(range(PRIME), size + 1024)
            present, absent = sampled[:size], sampled[size:]
            table = ChainedHashTable(capacity, seed=seed, resize=False)
            for key in present:
                table.insert(key, key)
            assert all(table.search(key) == key for key in present)
            rows.append({
                "size": size, "capacity": capacity, "load_factor": size / capacity,
                "seed": seed,
                "successful_probes": statistics.mean(table.probes_for_search(k) for k in present),
                "unsuccessful_probes": statistics.mean(table.probes_for_search(k) for k in absent),
                "max_chain": max(len(bucket) for bucket in table._buckets),
                "suh_success_reference": 1 + (size - 1) / (2 * capacity),
                "suh_failure_reference": size / capacity,
            })
    write_csv(output / "hash_load_raw.csv", rows)
    summary = []
    for size in (256, 512, 1024, 2048, 4096):
        chosen = [row for row in rows if row["size"] == size]
        summary.append({"size": size, "capacity": capacity, "load_factor": size / capacity,
                        "trials": len(chosen),
                        "mean_successful_probes": statistics.mean(r["successful_probes"] for r in chosen),
                        "mean_unsuccessful_probes": statistics.mean(r["unsuccessful_probes"] for r in chosen),
                        "largest_chain_seen": max(r["max_chain"] for r in chosen)})
    write_csv(output / "hash_load_summary.csv", summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[128, 512, 2048, 4096])
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.trials < 3 or any(size < 2 for size in args.sizes):
        parser.error("use at least three trials and sizes of at least two")
    args.output.mkdir(parents=True, exist_ok=True)
    raw, summary, counts = [], [], []
    for size in args.sizes:
        for dist_index, distribution in enumerate(DISTRIBUTIONS):
            base = 532 + size * 101 + dist_index * 100003
            original = dataset(size, distribution, base)
            for method in METHODS:
                work = original.copy()
                run_sort(method, work, base)
                assert work == sorted(original)
            for trial in range(args.trials):
                seed = base + trial + 1
                original = dataset(size, distribution, seed)
                expected = sorted(original)
                order = METHODS if trial % 2 == 0 else METHODS[::-1]
                for method in order:
                    work = original.copy()
                    enabled = gc.isenabled()
                    gc.disable()
                    try:
                        start = time.perf_counter_ns()
                        run_sort(method, work, seed + 2000003)
                        elapsed = time.perf_counter_ns() - start
                    finally:
                        if enabled:
                            gc.enable()
                    assert work == expected
                    raw.append({"size": size, "distribution": distribution,
                                "method": method, "trial": trial,
                                "data_seed": seed, "pivot_seed": seed + 2000003,
                                "elapsed_ns": elapsed})
            for method in METHODS:
                values = [row["elapsed_ns"] / 1e6 for row in raw
                          if row["size"] == size and row["distribution"] == distribution
                          and row["method"] == method]
                quartiles = statistics.quantiles(values, method="inclusive")
                summary.append({"size": size, "distribution": distribution,
                                "method": method, "trials": args.trials,
                                "median_ms": statistics.median(values),
                                "min_ms": min(values), "max_ms": max(values),
                                "q1_ms": quartiles[0], "q3_ms": quartiles[2]})
                original = dataset(size, distribution, base)
                work = [Counted(value) for value in original]
                Counted.comparisons = 0
                run_sort(method, work, base)
                comparison_count = Counted.comparisons
                assert [item.value for item in work] == sorted(original)
                counts.append({"size": size, "distribution": distribution,
                               "method": method, "comparisons": comparison_count,
                               "comparisons_per_nlog2n": comparison_count / (size * math.log2(size)),
                               "comparisons_per_n_squared": comparison_count / size**2})
            print(f"Measured n={size}, {distribution}", flush=True)
    write_csv(args.output / "quicksort_raw.csv", raw)
    write_csv(args.output / "quicksort_summary.csv", summary)
    write_csv(args.output / "quicksort_comparisons.csv", counts)
    hash_experiment(args.output)
    environment = {
        "python": sys.version, "implementation": platform.python_implementation(),
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "sizes": args.sizes, "trials": args.trials,
        "timer": "perf_counter_ns", "timer_resolution_seconds":
        time.get_clock_info("perf_counter").resolution,
        "method": "same partition code; paired inputs; alternating order; one warmup/configuration; "
                  "GC disabled during timing; input copying and validation excluded",
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted(Path("algorithms").glob("*.py"))},
        "hash_experiment": "20 independently seeded tables per load factor; capacity 1024; "
                           "resizing disabled; 1024 absent queries; every inserted key queried",
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    print(f"Saved {len(raw)} timed runs, {len(counts)} count runs, and 100 hash trials.")


if __name__ == "__main__":
    main()
