"""Compare pivot policies while keeping partitioning and stack management equal.

Inputs are lists of mutually comparable values; experiments use finite integers.
Both variants modify the supplied list and return None. Neither is stable.
"""

import random
from typing import TypeVar

T = TypeVar("T")


def _partition(items: list[T], left: int, right: int, pivot_index: int) -> tuple[int, int]:
    """Return inclusive boundaries of the equal block using two linear passes.

    The first pass gathers values below the pivot. The second gathers values
    equal to it. All equal keys leave further work together. With a first-
    element pivot, an ascending input retains an ascending remainder.
    """
    pivot = items[pivot_index]
    items[pivot_index], items[right] = items[right], items[pivot_index]
    lower = left
    for scan in range(left, right):
        if items[scan] < pivot:
            items[lower], items[scan] = items[scan], items[lower]
            lower += 1
    equal_end = lower
    for scan in range(lower, right):
        # Every value remaining here is >= pivot; one comparison detects equality.
        if not pivot < items[scan]:
            items[equal_end], items[scan] = items[scan], items[equal_end]
            equal_end += 1
    items[equal_end], items[right] = items[right], items[equal_end]
    return lower, equal_end


def _sort(items: list[T], rng: random.Random | None) -> None:
    pending = [(0, len(items) - 1)]
    while pending:
        left, right = pending.pop()
        while left < right:
            pivot_index = left if rng is None else rng.randrange(left, right + 1)
            equal_start, equal_end = _partition(items, left, right, pivot_index)
            # Defer the larger side; nested active ranges at least halve in size.
            if equal_start - left < right - equal_end:
                if equal_end + 1 < right:
                    pending.append((equal_end + 1, right))
                right = equal_start - 1
            else:
                if left < equal_start - 1:
                    pending.append((left, equal_start - 1))
                left = equal_end + 1


def randomized_quicksort(items: list[T], seed: int | None = None) -> None:
    """Choose each pivot uniformly from the current subarray's indices.

    Expected time O(n log n), worst time O(n**2), and O(log n) auxiliary stack.
    A seed makes experiments repeatable; None uses default initialization.
    The expectation concerns random pivot choices for any fixed input.
    """
    _sort(items, random.Random(seed))


def deterministic_quicksort(items: list[T]) -> None:
    """Always select the first element of each subarray as its pivot.

    Sorted/reverse distinct inputs take Theta(n**2). Iteration avoids Python
    recursion failures without changing the quadratic work.
    """
    _sort(items, None)
