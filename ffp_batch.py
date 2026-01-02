from fplapi.fpl_services import fetch_fpl_bootstrap, FPLError, fetch_fpl_player_summary, fetch_fpl_fixtures
from database.helpers import (
    init_db, 
    sync_teams, 
    sync_players, 
    sync_player_past_fixtures, 
    sync_player_upcoming_fixtures, 
    sync_player_past_seasons,
    sync_team_metrics
)
from database.db import SessionLocal
"""
    This file represents the batch process for the FFP system.  
    - Data is collected from the FPL apis
    - Data is processed and calculated data derived
    - All data is saved to the database for use by the streamlit user web application
    - This batch should be run daily to keep the database up to date
"""
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

    print("get team fixture data to calculate strength home and away")
    team_metrics_lookup = {} # used for quick lookup in player calcs
    team_metrics_db = [] # stored in db
    fixture_data = fetch_fpl_fixtures()
    for i, fixture in enumerate(reversed(fixture_data)):
        print(f"calculate team metrics ({i+1}/{len(fixture_data)})")
        if not fixture["finished"]:
            continue
        
        if fixture["team_a"] not in team_metrics_lookup:
            team_metric = {
                "team_id": fixture["team_a"],
                "no_games_a": 1,
                "no_games_h": 0,
                "no_goals_scored_a": fixture["team_a_score"],
                "no_goals_conceded_a": fixture["team_h_score"],
                "no_goals_scored_h": 0,
                "no_goals_conceded_h": 0
            }

            team_metrics_lookup[fixture["team_a"]] = team_metric
        else:
            if team_metrics_lookup[fixture["team_a"]]["no_games_a"] < 3:
                team_metrics_lookup[fixture["team_a"]]["no_games_a"] += 1
                team_metrics_lookup[fixture["team_a"]]["no_goals_scored_a"] += fixture["team_a_score"]
                team_metrics_lookup[fixture["team_a"]]["no_goals_conceded_a"] += fixture["team_h_score"]

        if fixture["team_h"] not in team_metrics_lookup:
            team_metric = {
                "team_id": fixture["team_h"],
                "no_games_a": 0,
                "no_games_h": 1,
                "no_goals_scored_a": 0,
                "no_goals_conceded_a": 0,
                "no_goals_scored_h": fixture["team_h_score"],
                "no_goals_conceded_h": fixture["team_a_score"]
            }
            team_metrics_lookup[fixture["team_h"]] = team_metric
        else:
            if team_metrics_lookup[fixture["team_h"]]["no_games_h"] < 3:
                team_metrics_lookup[fixture["team_h"]]["no_games_h"] += 1
                team_metrics_lookup[fixture["team_h"]]["no_goals_scored_h"] += fixture["team_h_score"]
                team_metrics_lookup[fixture["team_h"]]["no_goals_conceded_h"] += fixture["team_a_score"]




    print("create teams dict")
    for i, team in enumerate(data["teams"]):
        print(f"processing team ({i+1}/{len(data['teams'])}) {team['name']}")

        # calculate team metrics where we have games for the team available (wont be there for start of season)
        if team["id"] in team_metrics_lookup:
            team_metrics_lookup[team["id"]]["home_strength_defence"] = 20 - (team_metrics_lookup[team["id"]]["no_goals_conceded_h"]/team_metrics_lookup[team["id"]]["no_games_h"]) if team_metrics_lookup[team["id"]]["no_games_h"] > 0 else 0
            team_metrics_lookup[team["id"]]["away_strength_defence"] = 20 - (team_metrics_lookup[team["id"]]["no_goals_conceded_a"]/team_metrics_lookup[team["id"]]["no_games_a"]) if team_metrics_lookup[team["id"]]["no_games_a"] > 0 else 0
            team_metrics_lookup[team["id"]]["home_strength_attack"] = team_metrics_lookup[team["id"]]["no_goals_scored_h"]/team_metrics_lookup[team["id"]]["no_games_h"] if team_metrics_lookup[team["id"]]["no_games_h"] > 0 else 0
            team_metrics_lookup[team["id"]]["away_strength_attack"] = team_metrics_lookup[team["id"]]["no_goals_scored_a"]/team_metrics_lookup[team["id"]]["no_games_a"] if team_metrics_lookup[team["id"]]["no_games_a"] > 0 else 0

            team_metrics_db.append(team_metrics_lookup[team["id"]])

    # initialise lists for full player details
    past_fixtures = []
    upcoming_fixtures = []
    past_seasons = []
    for i, player in enumerate(data["elements"]):
        print(f"processing player ({i+1}/{len(data['elements'])}) {player['first_name']} {player['second_name']}")
        # call api to get player summary
        player_data = fetch_fpl_player_summary(player['id'])

        # add player_id to lists where we dont have it
        for item in player_data["fixtures"]:
            item["player_id"] = player['id']

        for item in player_data["history_past"]:
            item["player_id"] = player['id']

        # append player data to full player lists for saving to db
        past_fixtures.extend(player_data["history"])
        upcoming_fixtures.extend(player_data["fixtures"])
        past_seasons.extend(player_data["history_past"])

        # calculate player metrics

        if i >= 0:
            break


    print("save data to db")
    with SessionLocal() as db:
        # sync_teams(db, data["teams"])
        # sync_players(db, data["elements"])
        # sync_player_past_fixtures(db, past_fixtures)
        # sync_player_upcoming_fixtures(db, upcoming_fixtures)
        # sync_player_past_seasons(db, past_seasons)
        sync_team_metrics(db, team_metrics_db)
        pass
        
except Exception as e:
    print(f"Failed with : {e}")
