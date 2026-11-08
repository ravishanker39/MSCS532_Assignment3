"""Small examples of both Quicksort policies and chained-hash operations."""

from algorithms.hash_table import ChainedHashTable
from algorithms.quicksort import deterministic_quicksort, randomized_quicksort


def main():
    original = [8, -3, 8, 4, 0, -3]
    for name, method in (("randomized", randomized_quicksort),
                         ("first pivot", deterministic_quicksort)):
        items = original.copy()
        method(items)
        print(name, items)
    table = ChainedHashTable(seed=532)
    table.insert(101, "queued")
    table.insert(109, "running")
    table.insert(101, "complete")
    print("101:", table.search(101))
    print("removed:", table.delete(109))
    print("size:", len(table), "capacity:", table.capacity,
          "load:", table.load_factor)


if __name__ == "__main__":
    main()
