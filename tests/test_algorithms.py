"""Correctness oracles, boundary cases, collisions, and resize transitions."""

import itertools
import random
import unittest

from algorithms.hash_table import ChainedHashTable, PRIME
from algorithms.quicksort import deterministic_quicksort, randomized_quicksort, _partition


class SortingTests(unittest.TestCase):
    def check_sorts(self, data):
        for method in (deterministic_quicksort, randomized_quicksort):
            actual = list(data)
            self.assertIsNone(method(actual))
            self.assertEqual(actual, sorted(data))

    def test_empty_singleton_and_negative_values(self):
        for data in ([], [1], [2, 1], [1, 2], [2, 2], [-5, 7, -5, 0]):
            self.check_sorts(data)

    def test_exhaustive_short_arrays(self):
        for length in range(8):
            for data in itertools.product((-1, 0, 1), repeat=length):
                self.check_sorts(data)

    def test_all_seven_element_permutations(self):
        for data in itertools.permutations(range(7)):
            self.check_sorts(data)

    def test_partition_invariant_for_every_pivot(self):
        original = [8, 3, 3, -1, 5, 3, 9]
        for pivot_index in range(len(original)):
            data = original.copy()
            pivot = data[pivot_index]
            lower, upper = _partition(data, 0, len(data) - 1, pivot_index)
            self.assertTrue(all(x < pivot for x in data[:lower]))
            self.assertTrue(all(x == pivot for x in data[lower:upper + 1]))
            self.assertTrue(all(x > pivot for x in data[upper + 1:]))
            self.assertEqual(sorted(data), sorted(original))

    def test_large_ordered_and_repeated_inputs(self):
        for data in (list(range(1500)), list(range(1499, -1, -1)), [4] * 15000):
            self.check_sorts(data)

    def test_seeded_random_arrays(self):
        for seed in range(20):
            rng = random.Random(seed)
            data = [rng.randrange(-100, 101) for _ in range(513)]
            actual = data.copy()
            randomized_quicksort(actual, seed)
            self.assertEqual(actual, sorted(data))


class HashTests(unittest.TestCase):
    def test_insert_search_update_delete_and_none(self):
        table = ChainedHashTable(seed=1)
        table.insert(0, None)
        self.assertIsNone(table.search(0))
        table.insert(0, "new")
        self.assertEqual(len(table), 1)
        self.assertEqual(table.delete(0), "new")
        for method in (table.search, table.delete):
            with self.assertRaises(KeyError):
                method(0)
        table.check_invariants()

    def test_collision_chain_head_middle_tail(self):
        table = ChainedHashTable(seed=5, resize=False)
        keys = [key for key in range(1000) if table._index(key) == 0][:9]
        self.assertEqual(len(keys), 9)
        for key in keys:
            table.insert(key, key * 3)
        for key in (keys[0], keys[4], keys[-1]):
            self.assertEqual(table.delete(key), key * 3)
        for key in set(keys) - {keys[0], keys[4], keys[-1]}:
            self.assertEqual(table.search(key), key * 3)
        table.check_invariants()

    def test_growth_shrink_and_boundary_keys(self):
        table = ChainedHashTable(seed=2)
        keys = list(range(1000)) + [PRIME - 1]
        for key in keys:
            table.insert(key, -key)
            self.assertLessEqual(table.load_factor, .75)
        self.assertGreater(table.capacity, 8)
        for key in keys:
            self.assertEqual(table.search(key), -key)
        for key in keys:
            self.assertEqual(table.delete(key), -key)
        self.assertEqual(table.capacity, 8)
        table.check_invariants()

    def test_invalid_keys_leave_state_intact(self):
        table = ChainedHashTable(seed=3)
        table.insert(7, "seven")
        for key in (-1, PRIME, True, 1.5, "7", None):
            error = ValueError if type(key) is int else TypeError
            for method in (lambda key: table.insert(key, "bad"), table.search, table.delete):
                with self.assertRaises(error):
                    method(key)
        self.assertEqual(list(table.items()), [(7, "seven")])
        with self.assertRaises(ValueError):
            ChainedHashTable(capacity=0)

    def test_ten_thousand_model_operations(self):
        for seed in range(10):
            rng = random.Random(seed)
            table = ChainedHashTable(seed=seed)
            model = {}
            for step in range(1000):
                key = rng.randrange(300)
                action = rng.randrange(3)
                if action == 0:
                    value = (seed, step)
                    table.insert(key, value)
                    model[key] = value
                elif key in model:
                    if action == 1:
                        self.assertEqual(table.search(key), model[key])
                    else:
                        self.assertEqual(table.delete(key), model.pop(key))
                else:
                    with self.assertRaises(KeyError):
                        (table.search if action == 1 else table.delete)(key)
                self.assertEqual(dict(table.items()), model)
                table.check_invariants()


if __name__ == "__main__":
    unittest.main()
