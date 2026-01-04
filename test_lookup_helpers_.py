import unittest
from database.lookup_helpers import get_current_gameweek


class TestLookupHelpers(unittest.TestCase):
    def test_get_gameweek(self):
        try:
            data = get_current_gameweek()
            print(f"gameweek : {data}")
        except Exception as e:
            print(f"Failed to get gameweek {e}")


if __name__ == "__main__":
    test = TestLookupHelpers()
    data = test.test_get_gameweek()
    print("main done")


