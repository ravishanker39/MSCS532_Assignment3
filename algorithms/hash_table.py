"""Separate chaining with a universal family over bounded integer keys.

Keys must be integers in [0, 2**61 - 1); booleans are rejected. This explicit
universe avoids silently mapping different arbitrary-size keys to one field
element. Values may be any Python object, including None.
"""

import random
from typing import Any, Iterator

PRIME = 2**61 - 1


class ChainedHashTable:
    """Hash h(k)=((a*k+b) mod PRIME) mod capacity; buckets are Python lists.

    With bounded load and keys independent of the sampled hash parameters,
    search is expected O(1), and insert/delete are expected amortized O(1).
    Individual operations can take O(n) under collisions or resizing.
    No dict backs storage. Use resize=False for fixed-capacity experiments.
    """

    def __init__(self, capacity: int = 8, seed: int | None = None, resize: bool = True):
        if type(capacity) is not int or capacity < 1 or capacity >= PRIME:
            raise ValueError("capacity must be a positive integer below PRIME")
        if type(resize) is not bool:
            raise TypeError("resize must be a boolean")
        self._minimum = max(8, 1 << (capacity - 1).bit_length())
        self._buckets: list[list[tuple[int, Any]]] = [[] for _ in range(self._minimum)]
        self._size = 0
        self._rng = random.Random(seed)
        self._resize_enabled = resize
        self._choose_hash()

    def _choose_hash(self) -> None:
        self._a = self._rng.randrange(1, PRIME)
        self._b = self._rng.randrange(PRIME)

    def _validate(self, key: int) -> None:
        if type(key) is not int:
            raise TypeError("key must be an integer, not a boolean")
        if not 0 <= key < PRIME:
            raise ValueError("key must be in [0, PRIME)")

    def _index(self, key: int) -> int:
        return ((self._a * key + self._b) % PRIME) % self.capacity

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def load_factor(self) -> float:
        return self._size / self.capacity

    def __len__(self) -> int:
        return self._size

    def insert(self, key: int, value: Any) -> None:
        """Insert or replace a value. Replacing a key does not increase size."""
        self._validate(key)
        bucket = self._buckets[self._index(key)]
        for position, (stored, _) in enumerate(bucket):
            if stored == key:
                bucket[position] = (key, value)
                return
        if self._resize_enabled and (self._size + 1) / self.capacity > .75:
            self._rehash(self.capacity * 2)
            bucket = self._buckets[self._index(key)]
        bucket.append((key, value))
        self._size += 1

    def search(self, key: int) -> Any:
        """Return the value or raise KeyError; a stored None is a valid value."""
        self._validate(key)
        for stored, value in self._buckets[self._index(key)]:
            if stored == key:
                return value
        raise KeyError(key)

    def delete(self, key: int) -> Any:
        """Remove a pair and return its value; missing keys raise KeyError."""
        self._validate(key)
        bucket = self._buckets[self._index(key)]
        for position, (stored, value) in enumerate(bucket):
            if stored == key:
                bucket[position] = bucket[-1]
                bucket.pop()
                self._size -= 1
                if (self._resize_enabled and self.capacity > self._minimum
                        and self.load_factor < .20):
                    self._rehash(max(self._minimum, self.capacity // 2))
                return value
        raise KeyError(key)

    def _rehash(self, capacity: int) -> None:
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(capacity)]
        self._choose_hash()
        for bucket in old_buckets:
            for key, value in bucket:
                self._buckets[self._index(key)].append((key, value))

    def items(self) -> Iterator[tuple[int, Any]]:
        """Iterate pairs in unspecified order; do not mutate while iterating."""
        for bucket in self._buckets:
            yield from bucket

    def probes_for_search(self, key: int) -> int:
        """Count examined keys for diagnostics, excluding hash calculation."""
        self._validate(key)
        bucket = self._buckets[self._index(key)]
        for probes, (stored, _) in enumerate(bucket, 1):
            if stored == key:
                return probes
        return len(bucket)

    def check_invariants(self) -> None:
        """O(n + capacity) diagnostic; not called in measured operations."""
        pairs = list(self.items())
        assert len(pairs) == self._size
        assert len({key for key, _ in pairs}) == self._size
        for index, bucket in enumerate(self._buckets):
            assert all(self._index(key) == index for key, _ in bucket)
        if self._resize_enabled:
            assert self.load_factor <= .75
