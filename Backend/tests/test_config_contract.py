import unittest


from config import (
    EXTERNAL_SEARCH_ENABLED,
    EXTERNAL_SEARCH_TOP_K,
    VECTOR_MATCH_DISTANCE_THRESHOLD,
)


class ConfigContractTests(unittest.TestCase):
    def test_external_search_settings_are_available(self):
        self.assertTrue(EXTERNAL_SEARCH_ENABLED)
        self.assertEqual(EXTERNAL_SEARCH_TOP_K, 5)
        self.assertEqual(VECTOR_MATCH_DISTANCE_THRESHOLD, 0.8)


if __name__ == "__main__":
    unittest.main()
