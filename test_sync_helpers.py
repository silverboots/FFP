import unittest
from database.sync_helpers import get_users
from database.db import SessionLocal


class TestSyncHelpers(unittest.TestCase):
    def test_get_users(self):
        try:
            with SessionLocal() as db:
                data = get_users(db)
                print(f"complete")
                return data
        except Exception as e:
            print(f"Failed to get gameweek {e}")


if __name__ == "__main__":
    test = TestSyncHelpers()
    data = test.test_get_users()
    print("main done")


