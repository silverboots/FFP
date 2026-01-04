from database.db import SessionLocal
from sqlalchemy import text


def get_current_gameweek():
    with SessionLocal() as db:
        result = db.execute(
            text("SELECT MAX(round) AS game_week FROM PlayerPastFixtures")
        )

        gameweek = result.scalar_one_or_none()
        return gameweek
    
