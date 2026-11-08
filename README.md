# Assignment 3 — Algorithm Efficiency and Scalability

Ravi Shanker Thadishetti · MSCS-532-B01 · Michael Solomon

This project compares randomized and first-element-pivot Quicksort and implements a separate-chaining hash table. The report explains the algorithms, derives their costs, and interprets reproducible experiments.

## Run

Use Python 3.10 or newer; the included results were produced with CPython 3.12.14. Run commands from this repository's root. On systems that use `python` instead of `python3`, substitute that command.

```bash
python3 -m unittest discover -s tests -v
python3 demo.py
python3 benchmark.py
```

The implementation, tests, demo, and benchmark require only the Python standard library. `benchmark.py` regenerates CSV results and environment metadata in `results/`. Timings will vary by machine and current system load. A shorter exploratory run can use:

```bash
python3 benchmark.py --sizes 128 512 --trials 3 --output results_small
```

The full hash experiment still runs when using this shorter sort configuration. To regenerate the supplied figure, optionally install the plotting dependency:

```bash
python3 -m pip install -r requirements-plots.txt
python3 plot_results.py
```

The checked-in report describes the supplied full experiment. Regenerating results does not automatically rewrite the report.

## Files

| Path | Purpose |
| --- | --- |
| `algorithms/quicksort.py` | Two pivot policies sharing one partition implementation |
| `algorithms/hash_table.py` | Universal hashing, explicit chains, growth and shrinkage |
| `tests/test_algorithms.py` | Exhaustive small-input checks and model-based tests |
| `demo.py` | Small sorting and hash-table examples |
| `benchmark.py` | Paired sort timings, comparison counts, and load-factor study |
| `plot_results.py` | Optional figure generation |
| `results/` | Raw trials, summaries, figure, test log, and environment metadata |
| `report/Assignment3_Ravi_Shanker_Thadishetti.docx` | Formatted report |
| `report/report.md` | Same report text for reading on GitHub |

## Quicksort API and design

```python
from algorithms.quicksort import randomized_quicksort, deterministic_quicksort

values = [8, -3, 8, 4, 0, -3]
randomized_quicksort(values, seed=532)
assert values == [-3, -3, 0, 4, 8, 8]
deterministic_quicksort(values)
```

Both functions mutate a list and return `None`. Values must be mutually comparable with a consistent ordering; NaN and incompatible mixed types are outside the contract. Empty lists, singleton lists, negative values, duplicates, and ordered inputs are supported. The algorithms are unstable.

The random pivot is sampled uniformly from the current inclusive subarray. The deterministic pivot is always the **first element**, as required. Both use a two-pass three-way partition that excludes equal keys from further work. The larger side is deferred while the smaller side is processed immediately, bounding the explicit stack by O(log n). Neither implementation calls Python's sorting functions.

For distinct keys, randomized time is expected Θ(n log n) and worst-case Θ(n²). The deterministic version takes Θ(n²) on ascending and descending inputs. Both finish all-equal input in Θ(n). Randomized and deterministic methods share partition code so the comparison isolates pivot selection. A3's two-pass partition differs from A4's one-pass three-way comparison implementation; the reports analyze them separately.

## Hash table API and design

```python
from algorithms.hash_table import ChainedHashTable

table = ChainedHashTable(seed=532)
table.insert(101, "waiting")
table.insert(101, "complete")  # replace without increasing size
assert table.search(101) == "complete"
assert table.delete(101) == "complete"
```

Keys must be integers in `[0, 2**61 - 1)`; booleans are rejected. Values may be any Python object, including `None`. Missing searches or deletions raise `KeyError`; invalid keys raise `TypeError` or `ValueError`. Bucket order is unspecified. `len(table)`, `table.capacity`, `table.load_factor`, and `table.items()` expose basic diagnostics. Do not mutate while iterating.

Hashing uses `((a * key + b) % PRIME) % capacity`, with random nonzero `a` and random `b`. Buckets contain explicit lists of key–value pairs; no dictionary backs the implementation. Expected bounds assume keys independent of the sampled hash parameters. This is not a cryptographic hash or an adaptive-adversary guarantee.

The default table grows before projected load exceeds 0.75 and shrinks below 0.20, never below its initial capacity. Hash parameters are resampled during a rehash. With default bounded occupancy, search is expected O(1), and updates are expected amortized O(1). Individual operations can be linear because of collisions or resizing. Space is O(n + m) for n entries and m buckets. `resize=False` intentionally permits higher loads for experiments.

## Experiments and findings

- **280 timed sort runs:** four sizes (128, 512, 2,048, 4,096), five distributions, two methods, seven trials. Inputs are paired, order alternates, and each configuration has a warmup. Copying and checking are excluded; random-generator setup is included. Garbage collection is disabled only while timing.
- **40 comparison-count runs:** actual calls to the implementation's comparison operator, measured separately from timings.
- **100 hash trials:** capacity 1,024, loads 0.25 through 4.0, 20 seeds per load. All inserted keys and 1,024 absent keys are queried. Counts exclude hash computation and are not wall-clock timings.

At 4,096 ascending values, median time was **4.746 ms** for randomized Quicksort and **365.847 ms** for the first-pivot version. On random distinct inputs the first-pivot version was slightly faster in this experiment. Randomization protects against unfavorable input structure; it need not win every run.

At load 4, successful and unsuccessful hash searches examined about **3.002** and **3.984** keys, respectively. The report connects these measurements to load factor, collision assumptions, and resizing costs.

Seeds and individual measurements are retained in the CSV files. `environment.json` records Python/platform information and source hashes. Final docstring-only formatting changes are identified in its provenance note. Report figures use these recorded data rather than illustrative numbers.

## Correctness and rubric coverage

The **11 passing tests** contain substantially more than 11 input cases: 3,280 ternary arrays, 5,040 permutations of seven keys, long ordered/equal inputs, explicit partition invariants, forced hash collisions, replacement, missing keys, boundary values, resize cycles, and 10,000 operations checked against a dictionary model.

| Rubric item | Evidence |
| --- | --- |
| Randomized Quicksort implementation | Uniform subarray pivots, duplicate-aware partition, documented contract and tests |
| Quicksort analysis | Report recurrence, pairwise indicators, worst case, duplicates, and stack bound |
| Empirical comparison | Paired random/ordered/repeated trials, raw data, timing and count interpretation |
| Hash table implementation | Explicit chaining and insert/search/delete with resizing and validation |
| Hash table analysis | Universal family, simple-uniform-hashing model, load-factor study and amortization |
| Code quality | Separate algorithm modules, deterministic experiments, tests and API documentation |
| Report and documentation | DOCX, readable Markdown report, cited sources, limitations and reproduction steps |
| Repository organization | All implementation, test, report and result files organized in this folder |

The report cites the sources used for the theoretical background. Standard algorithm names and mathematical notation are retained for accuracy.
