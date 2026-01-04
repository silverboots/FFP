import unittest
from fplapi.fpl_services import fetch_fpl_entry, fetch_fpl_fixtures, fetch_fpl_player_summary, fetch_fpl_team


class TestFplServices(unittest.TestCase):
    def test_fpl_entry(self):
        try:
            data = fetch_fpl_entry(2632271)
            print("complete")
            return data
        except Exception as e:
            print(f"Failed to get entry {e}")

    def test_fpl_fixtures(self):
        try:
            data = fetch_fpl_fixtures()
            print("complete")
            return data
        except Exception as e:
            print(f"Failed to get fixtures {e}")

    def test_fpl_player_summary(self):
        try:
            data = fetch_fpl_player_summary(5)
            print("complete")
            return data
        except Exception as e:
            print(f"Failed to get fixtures {e}")

    def test_fpl_team_lookup(self):
        try:
            data = fetch_fpl_team(2632271, gameweek=20)
            print("complete")
            return data
        except Exception as e:
            print(f"Failed to get fixtures {e}")


if __name__ == "__main__":
    test = TestFplServices()
    data = test.test_fpl_team_lookup()
    print("main done")


