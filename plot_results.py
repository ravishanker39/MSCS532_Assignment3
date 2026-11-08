"""Create report figures from saved CSV files; requires matplotlib."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    root = Path(__file__).resolve().parent / "results"
    with (root / "quicksort_summary.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    with (root / "hash_load_summary.csv").open() as handle:
        loads = list(csv.DictReader(handle))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.3), constrained_layout=True)
    for method, label, color in [("randomized", "Random pivot", "#245A81"),
                                  ("first_pivot", "First pivot", "#B05A28")]:
        selected = [r for r in rows if r["distribution"] == "sorted" and r["method"] == method]
        axes[0].plot([int(r["size"]) for r in selected],
                     [float(r["median_ms"]) for r in selected], marker="o", color=color,
                     label=label)
    axes[0].set_xscale("log", base=2)
    axes[0].set_yscale("log")
    axes[0].set_xticks([128, 512, 2048, 4096], ["128", "512", "2,048", "4,096"])
    axes[0].set_title("Already sorted distinct keys", loc="left", fontweight="bold")
    axes[0].set_xlabel("Number of items")
    axes[0].set_ylabel("Median sort time (ms)")
    x = [float(r["load_factor"]) for r in loads]
    axes[1].plot(x, [float(r["mean_successful_probes"]) for r in loads], "o-",
                 color="#245A81", label="Successful search")
    axes[1].plot(x, [float(r["mean_unsuccessful_probes"]) for r in loads], "s-",
                 color="#B05A28", label="Unsuccessful search")
    axes[1].set_title("Fixed capacity with chaining", loc="left", fontweight="bold")
    axes[1].set_xlabel("Load factor n / m")
    axes[1].set_ylabel("Mean keys examined")
    axes[1].set_ylim(bottom=0)
    for axis in axes:
        axis.grid(alpha=.2)
        axis.legend(frameon=False)
        axis.spines[["top", "right"]].set_visible(False)
    fig.savefig(root / "efficiency_comparison.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
