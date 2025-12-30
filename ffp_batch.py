from fplapi.fpl_services import fetch_fpl_bootstrap, FPLError
from database.helpers import init_db, sync_teams, sync_players
from database.db import SessionLocal

try:
    print("init database")
    init_db()

    print("get bootstrap data")
    data = fetch_fpl_bootstrap()

    if data is None:
        raise FPLError("No data returned by FPL API")

    if "teams" not in data:
        raise FPLError("No teams in FPL bootstrap data")

    if "elements" not in data:
        raise FPLError("No players (elements) in FPL bootstrap data")

    print("create teams dict")
    teams = {}
    for team in data["teams"]:
        teams[team["code"]] = team

    print("save data to db")
    with SessionLocal() as db:
        sync_teams(db, data["teams"])
        sync_players(db, data["elements"])
        
except Exception as e:
    print(f"Failed with : {e}")
