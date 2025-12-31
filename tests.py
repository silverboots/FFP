import unittest
from fplapi.fpl_services import fetch_fpl_entry, fetch_fpl_fixtures


class TestFplServices(unittest.TestCase):
    def test_fpl_entry(self):
        try:
            data = fetch_fpl_entry(2632271)
            print("complete")
        except Exception as e:
            print(f"Failed to get entry {e}")

    def test_fpl_fixtures(self):
        try:
            data = fetch_fpl_fixtures()
            print("complete")
        except Exception as e:
            print(f"Failed to get fixtures {e}")