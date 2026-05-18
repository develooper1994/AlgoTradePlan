from __future__ import annotations

import unittest

from src.algotradeplan.core.ids import make_stable_id


class CoreIdsTest(unittest.TestCase):
    def test_make_stable_id_is_deterministic(self) -> None:
        self.assertEqual(make_stable_id("abc"), make_stable_id("abc"))
        self.assertNotEqual(make_stable_id("abc"), make_stable_id("def"))


if __name__ == "__main__":
    unittest.main()
